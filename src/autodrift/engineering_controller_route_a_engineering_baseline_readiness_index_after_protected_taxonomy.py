"""Materialize Route A baseline readiness after protected taxonomy.

This runner reanalyzes existing Route A engineering artifacts. It does not
execute environments, policies, replay, validation, training, ranking, or
promotion.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2667-engineering-controller-route-a-engineering-baseline-readiness-index-"
    "after-protected-taxonomy-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2668-engineering-controller-route-a-engineering-baseline-readiness-index-"
    "after-protected-taxonomy-materialization-result-audit"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2667_engineering_controller_route_a_engineering_baseline_readiness_index_after_protected_taxonomy"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2667-engineering-controller-route-a-engineering-baseline-readiness-index-"
    "after-protected-taxonomy-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2668-engineering-controller-route-a-engineering-baseline-"
    "readiness-index-after-protected-taxonomy-materialization-result-audit.json"
)

M2666_DOC = Path(
    "docs/m2666-engineering-controller-route-a-protected-mitigation-fresh-panel-"
    "failure-taxonomy-branch-synthesis.md"
)
M2665_DOC = Path(
    "docs/m2665-engineering-controller-route-a-protected-mitigation-fresh-panel-"
    "failure-taxonomy-materialization-result-audit.md"
)
M2664_SUMMARY = Path("runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy/summary.json")
M2664_SUBJECT_ROWS = Path(
    "runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy/"
    "subject_failure_taxonomy_rows.csv"
)
M2664_AXIS_ROWS = Path(
    "runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy/"
    "axis_failure_taxonomy_rows.csv"
)
M2664_METRIC_ROWS = Path(
    "runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy/"
    "metric_failure_taxonomy_rows.csv"
)
M2664_COMBINED_ROWS = Path(
    "runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy/"
    "combined_failure_taxonomy_rows.csv"
)
M2541_SUMMARY = Path("runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/summary.json")
M2541_BASELINE_CHECKPOINTS = Path(
    "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/baseline_checkpoint_list.csv"
)
M2541_ACTOR_CONTRACT = Path(
    "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/actor_io_contract_snapshot.json"
)
M2541_ARTIFACT_MAP = Path(
    "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/route_a_artifact_map.csv"
)
M2505_SUMMARY = Path("public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505/summary.json")
M2505_ARTIFACT_MANIFEST = Path(
    "public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505/artifact_manifest.csv"
)
M2508_SUMMARY = Path("runs/m2508_engineering_controller_runtime_inference_cost_report/summary.json")
M2508_RUNTIME_ROWS = Path("runs/m2508_engineering_controller_runtime_inference_cost_report/runtime_measurements.csv")
M2509_DOC = Path("docs/m2509-engineering-controller-runtime-inference-cost-report-result-audit.md")
M2657_SUMMARY = Path("runs/m2657_engineering_controller_route_a_source_only_target_protected_tradeoff_report/summary.json")
M2657_SCENARIO_ROLE_REPORT = Path(
    "runs/m2657_engineering_controller_route_a_source_only_target_protected_tradeoff_report/"
    "scenario_role_metric_report.csv"
)
M2657_TRADEOFF_ROWS = Path(
    "runs/m2657_engineering_controller_route_a_source_only_target_protected_tradeoff_report/"
    "target_protected_tradeoff_rows.csv"
)
M2657_PROTECTED_FOCUS = Path(
    "runs/m2657_engineering_controller_route_a_source_only_target_protected_tradeoff_report/"
    "protected_regression_focus_rows.csv"
)
M2659_SUMMARY = Path(
    "runs/m2659_engineering_controller_route_a_baseline_evidence_index_after_target_protected_report_refresh/"
    "summary.json"
)
M2659_EVIDENCE_INDEX = Path(
    "runs/m2659_engineering_controller_route_a_baseline_evidence_index_after_target_protected_report_refresh/"
    "evidence_index.csv"
)
M2659_GAP_MATRIX = Path(
    "runs/m2659_engineering_controller_route_a_baseline_evidence_index_after_target_protected_report_refresh/"
    "gap_matrix.csv"
)
ROUTE_PLAN = Path("docs/post-m2470-route-plan.md")

CLAIM_SCOPE = (
    "Route A engineering baseline readiness index after protected taxonomy only; "
    "no reset, rollout, replay, validation, training, ranking, winner selection, "
    "promotion, success-rate verdict, driver-performance, paper, finite-window-vs-GRU, "
    "current-sim, high-fidelity validation, full ideal driver, or self-ID claim"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness, validation result, "
    "controller ranking, winner selection, checkpoint promotion, success-rate verdict, "
    "paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, "
    "high-fidelity validation result, full ideal driver completion, or self-ID evidence"
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
    "validation_readiness_claim_made": False,
    "verdict_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "level3_self_id_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
    "full_ideal_driver_gate_passed": False,
}

CHECKPOINT_FIELDNAMES = [
    "checkpoint_id",
    "checkpoint_path",
    "source_milestone",
    "source_exists",
    "actor_contract_shape_72_action_3",
    "action_shape_3",
    "checkpoint_admitted",
    "behavior_changed_from_parent",
    "subject_taxonomy_id",
    "protected_blocking_gate_row_count",
    "protected_regressed_row_count",
    "target_evidence_present",
    "protected_blocker_present",
    "readiness_status",
    "readiness_reason",
    "allowed_use",
    "forbidden_interpretation",
]
ARTIFACT_FIELDNAMES = [
    "artifact_id",
    "source_milestone",
    "artifact_path",
    "route_a_requirement",
    "route_a_required",
    "source_exists",
    "status_pass_or_present",
    "row_count",
    "coverage_status",
    "readiness_use",
    "claim_scope",
    "forbidden_interpretation",
]
FAILURE_FIELDNAMES = [
    "boundary_id",
    "source_milestone",
    "failure_family",
    "taxonomy_axis",
    "subject_or_axis_or_metric",
    "row_count",
    "blocking_row_count",
    "regressed_row_count",
    "protected_blocker_preserved",
    "protected_rows_in_success_denominator",
    "actor_visible_allowed",
    "readiness_effect",
    "claim_boundary",
]
NEXT_ACTION_FIELDNAMES = [
    "candidate_action_id",
    "route",
    "admission_status",
    "reason",
    "required_before_execution",
    "evidence_expansion",
    "claim_scope",
    "forbidden_interpretation",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2667",
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
    ("route_a_readiness_index_materialized", True, "M2667 summary and readiness artifacts"),
    ("route_a_artifact_coverage_indexed", True, "artifact coverage rows include six post-M2470 Route A artifacts"),
    ("baseline_checkpoint_contract_indexed", True, "checkpoint readiness rows preserve P0 72/action 3"),
    ("protected_failure_boundary_indexed", True, "M2664/M2665 protected blocker taxonomy remains visible"),
    ("follow_up_result_audit_registered", True, "M2668 result-audit manifest"),
    ("repair_success", False, "future repair result plus protected gates"),
    ("driver_performance", False, "future validation and claim audit"),
    ("validation_readiness", False, "future validation-readiness route decision"),
    ("validation_result", False, "future validation result"),
    ("controller_ranking", False, "future explicit ranking gate"),
    ("winner_selection", False, "future promotion gate"),
    ("checkpoint_promotion", False, "future promotion gate"),
    ("success_rate_verdict", False, "future verdict milestone"),
    ("paper_level_evidence", False, "future paper evidence matrix"),
    ("finite_window_vs_gru", False, "future controller-family comparison"),
    ("current_sim_verdict", False, "future current-sim synthesis"),
    ("high_fidelity_validation_result", False, "future high-fidelity validation"),
    ("full_ideal_driver_completion", False, "future full ideal driver gate"),
    ("level3_self_identification", False, "future self-ID proof gate"),
)


def materialize_readiness_index_after_protected_taxonomy(
    output_dir: Path | str,
    *,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    source = load_source_artifacts(follow_up_manifest=follow_up_manifest)
    checkpoint_rows = build_checkpoint_readiness_rows(source)
    artifact_rows = build_artifact_coverage_rows(source)
    failure_rows = build_known_failure_boundary_rows(source)
    next_rows = build_next_action_admission_rows()
    claim_rows = build_claim_boundary_rows()
    paths = {
        "summary": output_path / "summary.json",
        "checkpoint_readiness_rows": output_path / "checkpoint_readiness_rows.csv",
        "artifact_coverage_rows": output_path / "artifact_coverage_rows.csv",
        "known_failure_boundary_rows": output_path / "known_failure_boundary_rows.csv",
        "next_action_admission_rows": output_path / "next_action_admission_rows.csv",
        "claim_boundary_rows": output_path / "claim_boundary_rows.csv",
        "gate_matrix": output_path / "gate_matrix.csv",
        "doc": Path(doc_path),
    }

    write_csv_rows(paths["checkpoint_readiness_rows"], checkpoint_rows, fieldnames=CHECKPOINT_FIELDNAMES)
    write_csv_rows(paths["artifact_coverage_rows"], artifact_rows, fieldnames=ARTIFACT_FIELDNAMES)
    write_csv_rows(paths["known_failure_boundary_rows"], failure_rows, fieldnames=FAILURE_FIELDNAMES)
    write_csv_rows(paths["next_action_admission_rows"], next_rows, fieldnames=NEXT_ACTION_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)

    gate_rows = build_gate_matrix_rows(
        source,
        checkpoint_rows,
        artifact_rows,
        failure_rows,
        next_rows,
        claim_rows,
        required_artifacts_present=False,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output_path,
        paths=paths,
        source=source,
        checkpoint_rows=checkpoint_rows,
        artifact_rows=artifact_rows,
        failure_rows=failure_rows,
        next_rows=next_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=False,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(path.exists() for path in paths.values())
    gate_rows = build_gate_matrix_rows(
        source,
        checkpoint_rows,
        artifact_rows,
        failure_rows,
        next_rows,
        claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output_path,
        paths=paths,
        source=source,
        checkpoint_rows=checkpoint_rows,
        artifact_rows=artifact_rows,
        failure_rows=failure_rows,
        next_rows=next_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    return summary


def load_source_artifacts(*, follow_up_manifest: Path | str) -> dict[str, Any]:
    paths = {
        "m2666_doc": M2666_DOC,
        "m2665_doc": M2665_DOC,
        "m2664_summary": M2664_SUMMARY,
        "m2664_subject_rows": M2664_SUBJECT_ROWS,
        "m2664_axis_rows": M2664_AXIS_ROWS,
        "m2664_metric_rows": M2664_METRIC_ROWS,
        "m2664_combined_rows": M2664_COMBINED_ROWS,
        "m2541_summary": M2541_SUMMARY,
        "m2541_baseline_checkpoints": M2541_BASELINE_CHECKPOINTS,
        "m2541_actor_contract": M2541_ACTOR_CONTRACT,
        "m2541_artifact_map": M2541_ARTIFACT_MAP,
        "m2505_summary": M2505_SUMMARY,
        "m2505_artifact_manifest": M2505_ARTIFACT_MANIFEST,
        "m2508_summary": M2508_SUMMARY,
        "m2508_runtime_rows": M2508_RUNTIME_ROWS,
        "m2509_doc": M2509_DOC,
        "m2657_summary": M2657_SUMMARY,
        "m2657_scenario_role_report": M2657_SCENARIO_ROLE_REPORT,
        "m2657_tradeoff_rows": M2657_TRADEOFF_ROWS,
        "m2657_protected_focus": M2657_PROTECTED_FOCUS,
        "m2659_summary": M2659_SUMMARY,
        "m2659_evidence_index": M2659_EVIDENCE_INDEX,
        "m2659_gap_matrix": M2659_GAP_MATRIX,
        "route_plan": ROUTE_PLAN,
        "follow_up_manifest": Path(follow_up_manifest),
    }
    return {
        "paths": paths,
        "source_exists": {name: path.exists() for name, path in paths.items()},
        "m2664_summary": read_json(paths["m2664_summary"]),
        "m2664_subject_rows": _read_csv_rows(paths["m2664_subject_rows"]),
        "m2664_axis_rows": _read_csv_rows(paths["m2664_axis_rows"]),
        "m2664_metric_rows": _read_csv_rows(paths["m2664_metric_rows"]),
        "m2664_combined_rows": _read_csv_rows(paths["m2664_combined_rows"]),
        "m2541_summary": read_json(paths["m2541_summary"]),
        "m2541_baseline_checkpoints": _read_csv_rows(paths["m2541_baseline_checkpoints"]),
        "m2541_actor_contract": read_json(paths["m2541_actor_contract"]),
        "m2541_artifact_map": _read_csv_rows(paths["m2541_artifact_map"]),
        "m2505_summary": read_json(paths["m2505_summary"]),
        "m2505_artifact_manifest": _read_csv_rows(paths["m2505_artifact_manifest"]),
        "m2508_summary": read_json(paths["m2508_summary"]),
        "m2508_runtime_rows": _read_csv_rows(paths["m2508_runtime_rows"]),
        "m2657_summary": read_json(paths["m2657_summary"]),
        "m2657_scenario_role_report": _read_csv_rows(paths["m2657_scenario_role_report"]),
        "m2657_tradeoff_rows": _read_csv_rows(paths["m2657_tradeoff_rows"]),
        "m2657_protected_focus": _read_csv_rows(paths["m2657_protected_focus"]),
        "m2659_summary": read_json(paths["m2659_summary"]),
        "m2659_evidence_index": _read_csv_rows(paths["m2659_evidence_index"]),
        "m2659_gap_matrix": _read_csv_rows(paths["m2659_gap_matrix"]),
    }


def build_checkpoint_readiness_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    subject_rows = {
        row["subject_id"]: row
        for row in source["m2664_subject_rows"]
    }
    rows: list[dict[str, Any]] = []
    for checkpoint in source["m2541_baseline_checkpoints"]:
        subject_id = _checkpoint_subject_id(checkpoint["checkpoint_id"])
        taxonomy = subject_rows[subject_id]
        actor_contract_ok = (
            _bool(checkpoint.get("source_exists"))
            and checkpoint.get("observation_shape") == str(P0_OBSERVATION_DIM)
            and checkpoint.get("action_shape") == str(ACTION_DIM)
            and "no_oracle" in checkpoint.get("actor_contract_id", "")
        )
        protected_blocker = (
            _int(taxonomy.get("blocking_gate_row_count")) > 0
            and _bool(taxonomy.get("protected_blocker_preserved"))
            and not _bool(taxonomy.get("protected_rows_in_success_denominator"))
        )
        admitted = _bool(checkpoint.get("checkpoint_admitted"))
        readiness_status = (
            "diagnostic_ready_blocked_by_protected_mitigation"
            if actor_contract_ok and admitted and protected_blocker
            else "not_ready_missing_contract_lineage_or_blocker_boundary"
        )
        rows.append(
            {
                "checkpoint_id": checkpoint["checkpoint_id"],
                "checkpoint_path": checkpoint["checkpoint_path"],
                "source_milestone": checkpoint["source_milestone"],
                "source_exists": _bool(checkpoint.get("source_exists")),
                "actor_contract_shape_72_action_3": actor_contract_ok,
                "action_shape_3": checkpoint.get("action_shape") == str(ACTION_DIM),
                "checkpoint_admitted": admitted,
                "behavior_changed_from_parent": _bool(checkpoint.get("behavior_changed_from_parent")),
                "subject_taxonomy_id": taxonomy["taxonomy_id"],
                "protected_blocking_gate_row_count": _int(taxonomy.get("blocking_gate_row_count")),
                "protected_regressed_row_count": _int(taxonomy.get("regressed_row_count")),
                "target_evidence_present": _bool(checkpoint.get("behavior_changed_from_parent")),
                "protected_blocker_present": protected_blocker,
                "readiness_status": readiness_status,
                "readiness_reason": (
                    f"{subject_id} blocks {taxonomy['blocking_gate_row_count']}/"
                    f"{taxonomy['gate_row_count']} protected claim rows; readiness is packaging/index "
                    "only and not promotion or performance evidence"
                ),
                "allowed_use": "Route A engineering baseline readiness index and follow-up audit",
                "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
            }
        )
    return rows


def build_artifact_coverage_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    m2541 = source["m2541_summary"]
    m2505 = source["m2505_summary"]
    m2508 = source["m2508_summary"]
    m2657 = source["m2657_summary"]
    m2659 = source["m2659_summary"]
    m2664 = source["m2664_summary"]
    specs = [
        (
            "baseline_checkpoint_list",
            "m2541",
            source["paths"]["m2541_baseline_checkpoints"],
            "baseline checkpoint list",
            True,
            m2541.get("status_pass"),
            m2541.get("baseline_checkpoint_count"),
            "current_route_a_input",
        ),
        (
            "actor_input_output_contract",
            "m2541",
            source["paths"]["m2541_actor_contract"],
            "actor input/output contract",
            True,
            m2541.get("actor_contract_shape_72_action_3"),
            1,
            "current_route_a_input",
        ),
        (
            "public_benchmark_pack",
            "m2505",
            source["paths"]["m2505_summary"],
            "public benchmark pack",
            True,
            m2505.get("status_pass"),
            m2505.get("artifact_manifest_rows"),
            "current_route_a_input",
        ),
        (
            "runtime_inference_cost_report",
            "m2508/m2509",
            source["paths"]["m2508_summary"],
            "runtime/inference-cost report",
            True,
            m2508.get("status_pass") and source["source_exists"]["m2509_doc"],
            m2508.get("measurement_row_count"),
            "current_route_a_input",
        ),
        (
            "scenario_role_metric_report",
            "m2657",
            source["paths"]["m2657_scenario_role_report"],
            "scenario-role metric report",
            True,
            m2657.get("status_pass"),
            m2657.get("scenario_role_metric_report_row_count"),
            "current_route_a_input",
        ),
        (
            "known_failure_taxonomy",
            "m2664/m2665/m2666",
            source["paths"]["m2664_summary"],
            "known failure taxonomy",
            True,
            m2664.get("status_pass") and source["source_exists"]["m2665_doc"] and source["source_exists"]["m2666_doc"],
            m2664.get("combined_failure_taxonomy_row_count"),
            "current_route_a_input",
        ),
        (
            "post_m2665_evidence_index",
            "m2659",
            source["paths"]["m2659_summary"],
            "supporting target/protected evidence index",
            False,
            m2659.get("status_pass"),
            m2659.get("evidence_index_row_count"),
            "supporting_context",
        ),
        (
            "post_m2470_route_plan",
            "post-m2470",
            source["paths"]["route_plan"],
            "route plan",
            False,
            source["source_exists"]["route_plan"],
            1,
            "governing_context",
        ),
    ]
    rows = []
    for artifact_id, milestone, path, requirement, route_required, status, row_count, readiness_use in specs:
        exists = Path(path).exists()
        rows.append(
            {
                "artifact_id": artifact_id,
                "source_milestone": milestone,
                "artifact_path": str(path),
                "route_a_requirement": requirement,
                "route_a_required": route_required,
                "source_exists": exists,
                "status_pass_or_present": _bool(status),
                "row_count": _int(row_count),
                "coverage_status": "covered_current" if exists and _bool(status) else "missing_or_not_passing",
                "readiness_use": readiness_use,
                "claim_scope": CLAIM_SCOPE,
                "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
            }
        )
    return rows


def build_known_failure_boundary_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        {
            "boundary_id": "m2657_protected_mitigation_tradeoff_boundary",
            "source_milestone": "m2657",
            "failure_family": "behavior_regression",
            "taxonomy_axis": "scenario_role",
            "subject_or_axis_or_metric": "unavoidable_mitigation",
            "row_count": _int(source["m2657_summary"].get("protected_regression_focus_row_count")),
            "blocking_row_count": _int(source["m2657_summary"].get("protected_regression_focus_row_count")),
            "regressed_row_count": _int(source["m2657_summary"].get("m2655_protected_component_regressed_row_count")),
            "protected_blocker_preserved": True,
            "protected_rows_in_success_denominator": False,
            "actor_visible_allowed": False,
            "readiness_effect": "blocks repair success promotion validation readiness and driver-performance claims",
            "claim_boundary": CLAIM_SCOPE,
        }
    ]
    for axis_name, source_rows, label_key in (
        ("subject", source["m2664_subject_rows"], "subject_id"),
        ("dynamics_axis", source["m2664_axis_rows"], "dynamics_axis_id"),
        ("metric", source["m2664_metric_rows"], "metric"),
    ):
        for source_row in source_rows:
            rows.append(
                {
                    "boundary_id": f"m2667_known_failure_{axis_name}_{source_row[label_key]}",
                    "source_milestone": "m2664",
                    "failure_family": source_row["primary_failure_family"],
                    "taxonomy_axis": axis_name,
                    "subject_or_axis_or_metric": source_row[label_key],
                    "row_count": _int(source_row.get("gate_row_count")),
                    "blocking_row_count": _int(source_row.get("blocking_gate_row_count")),
                    "regressed_row_count": _int(source_row.get("regressed_row_count")),
                    "protected_blocker_preserved": _bool(source_row.get("protected_blocker_preserved")),
                    "protected_rows_in_success_denominator": _bool(source_row.get("protected_rows_in_success_denominator")),
                    "actor_visible_allowed": _bool(source_row.get("actor_visible_allowed")),
                    "readiness_effect": (
                        "known protected limitation remains visible in baseline readiness; "
                        "not actor-visible and not a success denominator"
                    ),
                    "claim_boundary": CLAIM_SCOPE,
                }
            )
    return rows


def build_next_action_admission_rows() -> list[dict[str, Any]]:
    return [
        next_action_row(
            "m2668_route_a_baseline_readiness_index_result_audit",
            "Route A",
            "admitted",
            "M2667 materializes readiness rows and must be audited before packaging validation or new evidence route",
            "M2667 status_pass true and required artifacts present",
            "audit readiness index and route to synthesis stop or non-overfit next evidence axis",
        ),
        next_action_row(
            "route_a_packaging_or_validation_freeze",
            "Route A",
            "defer_until_m2668_audit",
            "readiness index is not validation readiness and protected blocker remains broad",
            "M2668 audit plus explicit synthesis decision",
            "package only after claim-boundary audit preserves known limitations",
        ),
        next_action_row(
            "another_same_row_protected_repair",
            "Route A",
            "not_admitted",
            "M2666 pivot rejects same-row public protected repair from taxonomy/readiness rows",
            "new evidence axis and synthesis decision",
            "prevents public-gate local search",
        ),
        next_action_row(
            "checkpoint_promotion_or_winner_selection",
            "Route A",
            "not_admitted",
            "readiness rows index diagnostic baselines and protected blockers but do not rank checkpoints",
            "proof plus generalization plus promotion gate",
            "promotion remains forbidden",
        ),
        next_action_row(
            "validation_success_rate_or_driver_performance_claim",
            "Route A",
            "not_admitted",
            "M2667 performs no reset rollout replay or validation",
            "future validation manifest and claim audit",
            "validation and performance claims remain forbidden",
        ),
        next_action_row(
            "paper_self_id_or_finite_window_claim",
            "Route B",
            "not_admitted",
            "M2667 is engineering readiness indexing and does not test history necessity",
            "separate paper-route comparison matrix",
            "paper and self-ID claims remain forbidden",
        ),
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": f"m2667_claim_boundary_{claim}",
            "claim_family": claim,
            "allowed_in_m2667": allowed,
            "status_pass": True,
            "evidence_required_before_claim": evidence_required,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim, allowed, evidence_required in CLAIM_CHECKS
    ]


def build_gate_matrix_rows(
    source: dict[str, Any],
    checkpoint_rows: list[dict[str, Any]],
    artifact_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    next_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    *,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    route_required_rows = [row for row in artifact_rows if _bool(row["route_a_required"])]
    hidden_oracle_detected = hidden_oracle_actor_input_detected(source, checkpoint_rows)
    return [
        gate_row(
            "m2667_gate_source_artifacts_present",
            "artifact",
            all(source["source_exists"].values()),
            True,
        ),
        gate_row("m2667_gate_required_artifacts_present", "artifact", required_artifacts_present, True),
        gate_row(
            "m2667_gate_route_a_required_artifacts_covered",
            "artifact_coverage",
            sum(1 for row in route_required_rows if row["coverage_status"] == "covered_current"),
            len(route_required_rows),
        ),
        gate_row(
            "m2667_gate_checkpoint_contract_72_action_3",
            "actor_contract",
            all(_bool(row["actor_contract_shape_72_action_3"]) and _bool(row["action_shape_3"]) for row in checkpoint_rows),
            True,
        ),
        gate_row("m2667_gate_hidden_oracle_actor_input_absent", "actor_contract", hidden_oracle_detected, False),
        gate_row(
            "m2667_gate_protected_blocker_preserved",
            "known_failure_boundary",
            bool(failure_rows) and all(_bool(row["protected_blocker_preserved"]) for row in failure_rows),
            True,
        ),
        gate_row(
            "m2667_gate_protected_rows_outside_success_denominator",
            "known_failure_boundary",
            any(_bool(row["protected_rows_in_success_denominator"]) for row in failure_rows),
            False,
        ),
        gate_row(
            "m2667_gate_actor_visible_failure_labels_absent",
            "actor_contract",
            any(_bool(row["actor_visible_allowed"]) for row in failure_rows),
            False,
        ),
        gate_row(
            "m2667_gate_follow_up_result_audit_registered",
            "process",
            source["source_exists"]["follow_up_manifest"],
            True,
        ),
        gate_row(
            "m2667_gate_single_admitted_next_action",
            "process",
            sum(1 for row in next_rows if row["admission_status"] == "admitted"),
            1,
        ),
        gate_row(
            "m2667_gate_claim_boundary_pass",
            "claim_boundary",
            all(_bool(row["status_pass"]) for row in claim_rows) and not any(FALSE_CLAIM_FLAGS.values()),
            True,
        ),
        gate_row("m2667_gate_no_reset_rollout_training_validation", "claim_boundary", False, False),
        gate_row("m2667_gate_no_ranking_promotion_success_rate_performance", "claim_boundary", False, False),
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    checkpoint_rows: list[dict[str, Any]],
    artifact_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    next_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    route_required_rows = [row for row in artifact_rows if _bool(row["route_a_required"])]
    covered_required_rows = [row for row in route_required_rows if row["coverage_status"] == "covered_current"]
    admitted_actions = [row["candidate_action_id"] for row in next_rows if row["admission_status"] == "admitted"]
    protected_blocking_rows = [row for row in failure_rows if _int(row["blocking_row_count"]) > 0]
    actor_contract_preserved = all(
        _bool(row["actor_contract_shape_72_action_3"]) and _bool(row["action_shape_3"]) for row in checkpoint_rows
    )
    hidden_oracle_clean = not hidden_oracle_actor_input_detected(source, checkpoint_rows)
    protected_blocker_preserved = bool(failure_rows) and all(_bool(row["protected_blocker_preserved"]) for row in failure_rows)
    protected_rows_outside_success = not any(_bool(row["protected_rows_in_success_denominator"]) for row in failure_rows)
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    route_a_artifact_coverage_complete = len(covered_required_rows) == len(route_required_rows) == 6
    status_pass = (
        required_artifacts_present
        and all(source["source_exists"].values())
        and _bool(source["m2541_summary"].get("status_pass"))
        and _bool(source["m2505_summary"].get("status_pass"))
        and _bool(source["m2508_summary"].get("status_pass"))
        and _bool(source["m2657_summary"].get("status_pass"))
        and _bool(source["m2659_summary"].get("status_pass"))
        and _bool(source["m2664_summary"].get("status_pass"))
        and route_a_artifact_coverage_complete
        and actor_contract_preserved
        and hidden_oracle_clean
        and protected_blocker_preserved
        and protected_rows_outside_success
        and len(protected_blocking_rows) >= 10
        and len(admitted_actions) == 1
        and gate_matrix_pass
    )
    summary = {
        "protocol_version": "engineering_controller_route_a_baseline_readiness_after_protected_taxonomy_v0",
        "result_class": "engineering_controller_route_a_baseline_readiness_index_after_protected_taxonomy_pass",
        "milestone": milestone,
        "next_blocker": next_blocker,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "checkpoint_readiness_rows": str(paths["checkpoint_readiness_rows"]),
        "artifact_coverage_rows": str(paths["artifact_coverage_rows"]),
        "known_failure_boundary_rows": str(paths["known_failure_boundary_rows"]),
        "next_action_admission_rows": str(paths["next_action_admission_rows"]),
        "claim_boundary_rows": str(paths["claim_boundary_rows"]),
        "gate_matrix": str(paths["gate_matrix"]),
        "doc": str(paths["doc"]),
        "follow_up_manifest": str(source["paths"]["follow_up_manifest"]),
        "required_artifacts_present": required_artifacts_present,
        "source_artifacts_present": all(source["source_exists"].values()),
        "source_artifacts_reanalyzed_only": True,
        "route_a_required_artifact_count": len(route_required_rows),
        "route_a_required_artifacts_covered": len(covered_required_rows),
        "route_a_artifact_coverage_complete": route_a_artifact_coverage_complete,
        "checkpoint_readiness_row_count": len(checkpoint_rows),
        "artifact_coverage_row_count": len(artifact_rows),
        "known_failure_boundary_row_count": len(failure_rows),
        "known_failure_blocking_boundary_row_count": len(protected_blocking_rows),
        "next_action_admission_row_count": len(next_rows),
        "admitted_next_action_count": len(admitted_actions),
        "selected_next_action": admitted_actions[0] if admitted_actions else "",
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "actor_contract_shape_72_action_3": actor_contract_preserved,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": not hidden_oracle_clean,
        "taxonomy_labels_actor_visible": False,
        "repair_target_labels_actor_visible": False,
        "objective_gate_labels_actor_visible": False,
        "route_decision_labels_actor_visible": False,
        "protected_mitigation_blocker_preserved": protected_blocker_preserved,
        "protected_failure_blocking": len(protected_blocking_rows) > 0,
        "protected_rows_in_success_denominator": not protected_rows_outside_success,
        "protected_role_excluded_from_target_success_denominator": _bool(
            source["m2657_summary"].get("protected_role_excluded_from_target_success_denominator")
        ),
        "target_protected_split_preserved": _bool(source["m2664_summary"].get("target_protected_split_preserved")),
        "broad_protected_blocker_preserved": _bool(source["m2664_summary"].get("broad_protected_blocker_preserved")),
        "all_policy_subjects_blocking": _bool(source["m2664_summary"].get("all_policy_subjects_blocking")),
        "all_axes_blocking": _bool(source["m2664_summary"].get("all_axes_blocking")),
        "all_metrics_blocking": _bool(source["m2664_summary"].get("all_metrics_blocking")),
        "m2664_protected_gate_blocking_row_count": _int(source["m2664_summary"].get("protected_gate_blocking_row_count")),
        "m2664_protected_gate_regressed_row_count": _int(source["m2664_summary"].get("protected_gate_regressed_row_count")),
        "m2657_target_role_count": _int(source["m2657_summary"].get("target_role_count")),
        "m2657_protected_role_count": _int(source["m2657_summary"].get("protected_role_count")),
        "m2508_batch1_forward_time_us_p50": source["m2508_summary"].get("latency_by_batch", {}).get("1", {}).get(
            "forward_time_us_p50"
        ),
        "baseline_readiness_status": "index_ready_with_protected_mitigation_blocker",
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "status_pass": status_pass,
        **FALSE_CLAIM_FLAGS,
    }
    return summary


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2667 Engineering Controller Route A Engineering Baseline Readiness Index After Protected Taxonomy Materialization Preflight",
            "",
            "- status: completed" if summary["status_pass"] else "- status: failed",
            f"- result_class: `{summary['result_class']}`",
            f"- summary: `{summary['summary']}`",
            f"- checkpoint readiness rows: `{summary['checkpoint_readiness_rows']}`",
            f"- artifact coverage rows: `{summary['artifact_coverage_rows']}`",
            f"- known failure boundary rows: `{summary['known_failure_boundary_rows']}`",
            f"- next action admission rows: `{summary['next_action_admission_rows']}`",
            f"- claim boundary rows: `{summary['claim_boundary_rows']}`",
            f"- gate matrix: `{summary['gate_matrix']}`",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            f"- next: `{summary['next_blocker']}`",
            "",
            "## Readiness Index",
            "",
            f"- Route A required artifacts covered: {summary['route_a_required_artifacts_covered']}/{summary['route_a_required_artifact_count']}",
            f"- checkpoint readiness rows: {summary['checkpoint_readiness_row_count']}",
            f"- artifact coverage rows: {summary['artifact_coverage_row_count']}",
            f"- known failure boundary rows: {summary['known_failure_boundary_row_count']}",
            f"- selected next action: `{summary['selected_next_action']}`",
            "",
            "## Protected Boundary",
            "",
            f"- protected mitigation blocker preserved: `{str(summary['protected_mitigation_blocker_preserved']).lower()}`",
            f"- protected failure blocking: `{str(summary['protected_failure_blocking']).lower()}`",
            f"- protected rows in success denominator: `{str(summary['protected_rows_in_success_denominator']).lower()}`",
            f"- all policy subjects blocking: `{str(summary['all_policy_subjects_blocking']).lower()}`",
            f"- all axes blocking: `{str(summary['all_axes_blocking']).lower()}`",
            f"- all metrics blocking: `{str(summary['all_metrics_blocking']).lower()}`",
            f"- protected gate blocking rows: {summary['m2664_protected_gate_blocking_row_count']}",
            f"- protected regressed row count: {summary['m2664_protected_gate_regressed_row_count']}",
            "",
            "## Actor Boundary",
            "",
            f"- actor contract P0 72/action 3: `{str(summary['actor_contract_shape_72_action_3']).lower()}`",
            f"- hidden/oracle actor input detected: `{str(summary['hidden_oracle_actor_input_detected']).lower()}`",
            "- taxonomy, repair-target, objective-gate, and route-decision labels actor-visible: `false`",
            "",
            "## Claim Boundary",
            "",
            "M2667 is a readiness index over existing artifacts only. It performs no reset, step, rollout, replay, validation, training, PPO, source build, adapter probe, external simulation, ranking, winner selection, promotion, or success-rate computation.",
            "",
            "It does not claim repair success, driver performance, validation readiness, validation result, paper-level evidence, finite-window-vs-GRU, current-sim verdict, high-fidelity validation, full ideal driver completion, or self-ID evidence.",
            "",
        ]
    )


def checkpoint_subject_id_for_test(checkpoint_id: str) -> str:
    return _checkpoint_subject_id(checkpoint_id)


def next_action_row(
    candidate_action_id: str,
    route: str,
    admission_status: str,
    reason: str,
    required_before_execution: str,
    evidence_expansion: str,
) -> dict[str, Any]:
    return {
        "candidate_action_id": candidate_action_id,
        "route": route,
        "admission_status": admission_status,
        "reason": reason,
        "required_before_execution": required_before_execution,
        "evidence_expansion": evidence_expansion,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def gate_row(gate_id: str, gate_family: str, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "gate_family": gate_family,
        "status_pass": observed == expected,
        "observed": observed,
        "expected": expected,
        "failure_type": "" if observed == expected else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def hidden_oracle_actor_input_detected(source: dict[str, Any], checkpoint_rows: list[dict[str, Any]]) -> bool:
    summary_keys = (
        "hidden_oracle_actor_input_detected",
        "hidden_or_oracle_actor_input_detected",
        "hidden_or_oracle_actor_inputs_required",
    )
    summaries = (
        source["m2541_summary"],
        source["m2505_summary"],
        source["m2508_summary"],
        source["m2657_summary"],
        source["m2659_summary"],
        source["m2664_summary"],
    )
    summary_hidden = any(_bool(summary.get(key)) for summary in summaries for key in summary_keys)
    checkpoint_hidden = any("no_oracle" not in row.get("checkpoint_id", "") and not _bool(row["actor_contract_shape_72_action_3"]) for row in checkpoint_rows)
    return summary_hidden or checkpoint_hidden


def _checkpoint_subject_id(checkpoint_id: str) -> str:
    if checkpoint_id.startswith("m1154"):
        return "m1154_original_policy"
    if checkpoint_id.startswith("m2532"):
        return "m2532_guarded_repair_policy"
    if checkpoint_id.startswith("m2537"):
        return "m2537_mitigation_preserving_policy"
    raise KeyError(f"unknown checkpoint subject mapping: {checkpoint_id}")


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return bool(value)


def _int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Materialize Route A engineering baseline readiness index after protected taxonomy."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args(argv)
    summary = materialize_readiness_index_after_protected_taxonomy(
        args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
    )
    print(f"summary={summary['summary']}")
    print(f"status_pass={summary['status_pass']}")
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
