"""Refresh the Route A baseline evidence index after M2657/M2658.

This runner reanalyzes existing Route A artifacts and materializes an updated
evidence index. It does not execute environments, policies, replay,
validation, training, ranking, or promotion.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2659-engineering-controller-route-a-baseline-evidence-index-after-target-"
    "protected-report-refresh-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2660-engineering-controller-route-a-baseline-evidence-index-after-target-"
    "protected-report-refresh-materialization-result-audit"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2659_engineering_controller_route_a_baseline_evidence_index_after_target_protected_report_refresh"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2659-engineering-controller-route-a-baseline-evidence-index-after-target-"
    "protected-report-refresh-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2660-engineering-controller-route-a-baseline-evidence-"
    "index-after-target-protected-report-refresh-materialization-result-audit.json"
)

M2639_SUMMARY = Path("runs/m2639_engineering_controller_route_a_baseline_evidence_index_refresh/summary.json")
M2639_EVIDENCE_INDEX = Path("runs/m2639_engineering_controller_route_a_baseline_evidence_index_refresh/evidence_index.csv")
M2641_SUMMARY = Path("runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/summary.json")
M2641_BEHAVIOR_ROWS = Path(
    "runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/measured_behavior_rows.csv"
)
M2644_SUMMARY = Path("runs/m2644_engineering_controller_route_a_source_only_behavior_gap_taxonomy/summary.json")
M2644_REPAIR_TARGETS = Path(
    "runs/m2644_engineering_controller_route_a_source_only_behavior_gap_taxonomy/repair_target_admission_rows.csv"
)
M2648_SUMMARY = Path("runs/m2648_engineering_controller_route_a_source_only_gap_targeted_repair_execution/summary.json")
M2648_GATES = Path("runs/m2648_engineering_controller_route_a_source_only_gap_targeted_repair_execution/repair_gate_evaluation.csv")
M2655_SUMMARY = Path(
    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/summary.json"
)
M2655_CANDIDATES = Path(
    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/repair_candidate_sweep.csv"
)
M2655_GATES = Path(
    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/mitigation_preserving_gate_evaluation.csv"
)
M2656_DOC = Path(
    "docs/m2656-engineering-controller-route-a-baseline-source-only-gap-targeted-"
    "repair-mitigation-preserving-repair-execution-branch-synthesis.md"
)
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
M2657_REPORT_GATES = Path(
    "runs/m2657_engineering_controller_route_a_source_only_target_protected_tradeoff_report/"
    "report_gate_evaluation.csv"
)
M2658_AUDIT_DOC = Path(
    "docs/m2658-engineering-controller-route-a-baseline-source-only-target-protected-"
    "tradeoff-report-materialization-result-audit.md"
)

CLAIM_SCOPE = (
    "Route A baseline evidence index refresh after target/protected report only; "
    "no repair execution, validation, ranking, promotion, success-rate verdict, "
    "driver-performance, paper, current-sim, high-fidelity validation, "
    "finite-window-vs-GRU, or self-ID claim"
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

EVIDENCE_FIELDNAMES = [
    "evidence_id",
    "source_milestone",
    "artifact_path",
    "evidence_family",
    "evidence_role",
    "evidence_status",
    "row_count",
    "target_or_protected",
    "target_improvement_evidence",
    "protected_failure_blocking",
    "actor_contract_shape_72_action_3",
    "hidden_oracle_actor_input_detected",
    "source_exists",
    "next_use",
    "claim_scope",
    "forbidden_interpretation",
]
GAP_FIELDNAMES = [
    "gap_id",
    "route",
    "evidence_family",
    "current_status",
    "blocker",
    "required_next_evidence",
    "admission_to_next_action",
    "evidence_expansion_value",
    "forbidden_shortcut",
    "claim_scope",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2659",
    "status_pass",
    "evidence_required_before_claim",
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

CLAIM_CHECKS = (
    ("baseline_evidence_index_refreshed", True, "M2659 summary and refreshed evidence index artifacts"),
    ("target_protected_report_indexed", True, "M2657 report artifacts and M2658 audit"),
    ("protected_failure_blocker_indexed", True, "M2657 protected tradeoff and focus rows"),
    ("follow_up_result_audit_registered", True, "M2660 manifest"),
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
)


def materialize_evidence_index_after_target_protected_report_refresh(
    output_dir: Path | str,
    *,
    m2639_summary: Path | str = M2639_SUMMARY,
    m2639_evidence_index: Path | str = M2639_EVIDENCE_INDEX,
    m2641_summary: Path | str = M2641_SUMMARY,
    m2641_behavior_rows: Path | str = M2641_BEHAVIOR_ROWS,
    m2644_summary: Path | str = M2644_SUMMARY,
    m2644_repair_targets: Path | str = M2644_REPAIR_TARGETS,
    m2648_summary: Path | str = M2648_SUMMARY,
    m2648_gates: Path | str = M2648_GATES,
    m2655_summary: Path | str = M2655_SUMMARY,
    m2655_candidates: Path | str = M2655_CANDIDATES,
    m2655_gates: Path | str = M2655_GATES,
    m2656_doc: Path | str = M2656_DOC,
    m2657_summary: Path | str = M2657_SUMMARY,
    m2657_scenario_role_report: Path | str = M2657_SCENARIO_ROLE_REPORT,
    m2657_tradeoff_rows: Path | str = M2657_TRADEOFF_ROWS,
    m2657_protected_focus: Path | str = M2657_PROTECTED_FOCUS,
    m2657_report_gates: Path | str = M2657_REPORT_GATES,
    m2658_audit_doc: Path | str = M2658_AUDIT_DOC,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    source = load_source_artifacts(
        m2639_summary=m2639_summary,
        m2639_evidence_index=m2639_evidence_index,
        m2641_summary=m2641_summary,
        m2641_behavior_rows=m2641_behavior_rows,
        m2644_summary=m2644_summary,
        m2644_repair_targets=m2644_repair_targets,
        m2648_summary=m2648_summary,
        m2648_gates=m2648_gates,
        m2655_summary=m2655_summary,
        m2655_candidates=m2655_candidates,
        m2655_gates=m2655_gates,
        m2656_doc=m2656_doc,
        m2657_summary=m2657_summary,
        m2657_scenario_role_report=m2657_scenario_role_report,
        m2657_tradeoff_rows=m2657_tradeoff_rows,
        m2657_protected_focus=m2657_protected_focus,
        m2657_report_gates=m2657_report_gates,
        m2658_audit_doc=m2658_audit_doc,
        follow_up_manifest=follow_up_manifest,
    )

    evidence_rows = build_evidence_index_rows(source)
    gap_rows = build_gap_matrix_rows(source)
    claim_rows = build_claim_boundary_rows()
    next_rows = build_next_action_admission_rows()
    paths = {
        "summary": output_path / "summary.json",
        "evidence_index": output_path / "evidence_index.csv",
        "gap_matrix": output_path / "gap_matrix.csv",
        "claim_boundary_rows": output_path / "claim_boundary_rows.csv",
        "next_action_admission": output_path / "next_action_admission.csv",
        "doc": Path(doc_path),
    }
    write_csv_rows(paths["evidence_index"], evidence_rows, fieldnames=EVIDENCE_FIELDNAMES)
    write_csv_rows(paths["gap_matrix"], gap_rows, fieldnames=GAP_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["next_action_admission"], next_rows, fieldnames=NEXT_ACTION_FIELDNAMES)

    summary = build_summary(
        output_dir=output_path,
        paths=paths,
        source=source,
        evidence_rows=evidence_rows,
        gap_rows=gap_rows,
        claim_rows=claim_rows,
        next_rows=next_rows,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(
        render_milestone_doc(summary, evidence_rows, gap_rows, claim_rows, next_rows),
        encoding="utf-8",
    )
    summary["required_artifacts_present"] = all(
        path.exists()
        for path in (
            paths["summary"],
            paths["evidence_index"],
            paths["gap_matrix"],
            paths["claim_boundary_rows"],
            paths["next_action_admission"],
            paths["doc"],
        )
    )
    summary["status_pass"] = bool(summary["status_pass"] and summary["required_artifacts_present"])
    write_json(paths["summary"], summary)
    return summary


def load_source_artifacts(
    *,
    m2639_summary: Path | str,
    m2639_evidence_index: Path | str,
    m2641_summary: Path | str,
    m2641_behavior_rows: Path | str,
    m2644_summary: Path | str,
    m2644_repair_targets: Path | str,
    m2648_summary: Path | str,
    m2648_gates: Path | str,
    m2655_summary: Path | str,
    m2655_candidates: Path | str,
    m2655_gates: Path | str,
    m2656_doc: Path | str,
    m2657_summary: Path | str,
    m2657_scenario_role_report: Path | str,
    m2657_tradeoff_rows: Path | str,
    m2657_protected_focus: Path | str,
    m2657_report_gates: Path | str,
    m2658_audit_doc: Path | str,
    follow_up_manifest: Path | str,
) -> dict[str, Any]:
    paths = {
        "m2639_summary": Path(m2639_summary),
        "m2639_evidence_index": Path(m2639_evidence_index),
        "m2641_summary": Path(m2641_summary),
        "m2641_behavior_rows": Path(m2641_behavior_rows),
        "m2644_summary": Path(m2644_summary),
        "m2644_repair_targets": Path(m2644_repair_targets),
        "m2648_summary": Path(m2648_summary),
        "m2648_gates": Path(m2648_gates),
        "m2655_summary": Path(m2655_summary),
        "m2655_candidates": Path(m2655_candidates),
        "m2655_gates": Path(m2655_gates),
        "m2656_doc": Path(m2656_doc),
        "m2657_summary": Path(m2657_summary),
        "m2657_scenario_role_report": Path(m2657_scenario_role_report),
        "m2657_tradeoff_rows": Path(m2657_tradeoff_rows),
        "m2657_protected_focus": Path(m2657_protected_focus),
        "m2657_report_gates": Path(m2657_report_gates),
        "m2658_audit_doc": Path(m2658_audit_doc),
        "follow_up_manifest": Path(follow_up_manifest),
    }
    return {
        "paths": paths,
        "source_exists": {name: path.exists() for name, path in paths.items()},
        "m2639_summary": read_json(paths["m2639_summary"]),
        "m2639_evidence_index": _read_csv_rows(paths["m2639_evidence_index"]),
        "m2641_summary": read_json(paths["m2641_summary"]),
        "m2641_behavior_rows": _read_csv_rows(paths["m2641_behavior_rows"]),
        "m2644_summary": read_json(paths["m2644_summary"]),
        "m2644_repair_targets": _read_csv_rows(paths["m2644_repair_targets"]),
        "m2648_summary": read_json(paths["m2648_summary"]),
        "m2648_gates": _read_csv_rows(paths["m2648_gates"]),
        "m2655_summary": read_json(paths["m2655_summary"]),
        "m2655_candidates": _read_csv_rows(paths["m2655_candidates"]),
        "m2655_gates": _read_csv_rows(paths["m2655_gates"]),
        "m2657_summary": read_json(paths["m2657_summary"]),
        "m2657_scenario_role_report": _read_csv_rows(paths["m2657_scenario_role_report"]),
        "m2657_tradeoff_rows": _read_csv_rows(paths["m2657_tradeoff_rows"]),
        "m2657_protected_focus": _read_csv_rows(paths["m2657_protected_focus"]),
        "m2657_report_gates": _read_csv_rows(paths["m2657_report_gates"]),
    }


def build_evidence_index_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    m2639 = source["m2639_summary"]
    m2641 = source["m2641_summary"]
    m2644 = source["m2644_summary"]
    m2648 = source["m2648_summary"]
    m2655 = source["m2655_summary"]
    m2657 = source["m2657_summary"]
    tradeoff_rows = source["m2657_tradeoff_rows"]
    target_tradeoff_count = sum(1 for row in tradeoff_rows if row.get("role_class") == "target")
    protected_tradeoff_count = sum(1 for row in tradeoff_rows if row.get("role_class") == "protected")
    protected_focus_blockers = sum(
        1 for row in source["m2657_protected_focus"] if _bool(row.get("blocks_claims"))
    )
    return [
        evidence_row(
            "m2639_previous_route_a_evidence_index",
            "m2639",
            source["paths"]["m2639_evidence_index"],
            "baseline_evidence_index",
            "prior_index",
            "stale_but_traceable",
            _int(m2639.get("evidence_index_row_count")),
            "mixed",
            False,
            False,
            _bool(m2639.get("actor_contract_shape_72_action_3")),
            _bool(m2639.get("hidden_oracle_actor_input_detected")),
            "superseded by M2659 refreshed index",
        ),
        evidence_row(
            "m2641_source_only_fresh_generalization_panel",
            "m2641",
            source["paths"]["m2641_behavior_rows"],
            "source_only_closed_loop_generalization",
            "source_baseline",
            "materialized",
            _int(m2641.get("measured_behavior_row_count")),
            "mixed",
            False,
            False,
            _bool(m2641.get("actor_contract_shape_72_action_3")),
            _hidden_detected(m2641),
            "source behavior rows remain baseline evidence",
        ),
        evidence_row(
            "m2644_behavior_gap_taxonomy",
            "m2644",
            source["paths"]["m2644_repair_targets"],
            "behavior_gap_taxonomy",
            "target_map_and_reference_map",
            "materialized",
            _int(m2644.get("repair_target_admission_row_count")),
            "target_and_protected",
            False,
            True,
            _bool(m2644.get("actor_contract_shape_72_action_3")),
            _hidden_detected(m2644),
            "taxonomy admits target design while preserving mitigation as reference",
        ),
        evidence_row(
            "m2648_gap_targeted_repair_evidence",
            "m2648",
            source["paths"]["m2648_gates"],
            "source_only_repair_branch",
            "target_pass_protected_fail",
            "materialized_not_promoted",
            _int(m2648.get("repair_gate_evaluation_row_count")),
            "target_and_protected",
            True,
            True,
            _bool(m2648.get("actor_contract_shape_72_action_3")),
            _hidden_detected(m2648),
            "target gates pass but protected mitigation reference fails",
        ),
        evidence_row(
            "m2655_mitigation_preserving_repair_evidence",
            "m2655",
            source["paths"]["m2655_gates"],
            "source_only_repair_branch",
            "target_pass_protected_fail",
            "materialized_not_promoted",
            _int(m2655.get("mitigation_preserving_gate_evaluation_row_count")),
            "target_and_protected",
            True,
            True,
            _bool(m2655.get("actor_contract_shape_72_action_3")),
            _hidden_detected(m2655),
            "target preservation passes but protected component gates fail",
        ),
        evidence_row(
            "m2656_repair_branch_pivot_synthesis",
            "m2656",
            source["paths"]["m2656_doc"],
            "branch_synthesis",
            "repair_loop_pivot",
            "materialized",
            1,
            "protected_blocker",
            False,
            True,
            True,
            False,
            "closes same-row repair loop and routes to target/protected report",
        ),
        evidence_row(
            "m2657_target_protected_report_summary",
            "m2657",
            source["paths"]["m2657_summary"],
            "target_protected_tradeoff_report",
            "summary",
            "materialized",
            _int(m2657.get("scenario_role_metric_report_row_count")),
            "target_and_protected",
            True,
            True,
            _bool(m2657.get("actor_contract_shape_72_action_3")),
            _bool(m2657.get("hidden_or_oracle_actor_input_detected")),
            "current target/protected report is accepted for index input only",
        ),
        evidence_row(
            "m2657_scenario_role_metric_report",
            "m2657",
            source["paths"]["m2657_scenario_role_report"],
            "scenario_role_metric_report",
            "target_protected_split",
            "materialized",
            len(source["m2657_scenario_role_report"]),
            "target_and_protected",
            True,
            True,
            _all_actor_contract_ok(source["m2657_scenario_role_report"]),
            _any_hidden_detected(source["m2657_scenario_role_report"]),
            "keeps target roles separate from protected mitigation role",
        ),
        evidence_row(
            "m2657_target_tradeoff_rows",
            "m2657",
            source["paths"]["m2657_tradeoff_rows"],
            "target_tradeoff_rows",
            "target_improvement_evidence",
            "materialized_not_success_denominator",
            target_tradeoff_count,
            "target",
            True,
            False,
            _bool(m2657.get("actor_contract_shape_72_action_3")),
            _bool(m2657.get("hidden_or_oracle_actor_input_detected")),
            "index target improvements without repair success or promotion claim",
        ),
        evidence_row(
            "m2657_protected_tradeoff_rows",
            "m2657",
            source["paths"]["m2657_tradeoff_rows"],
            "protected_tradeoff_rows",
            "protected_failure_blocker",
            "materialized_blocking",
            protected_tradeoff_count,
            "protected",
            False,
            True,
            _bool(m2657.get("actor_contract_shape_72_action_3")),
            _bool(m2657.get("hidden_or_oracle_actor_input_detected")),
            "protected severity obstacle-penetration and clearance failures remain blocking",
        ),
        evidence_row(
            "m2657_protected_regression_focus_rows",
            "m2657",
            source["paths"]["m2657_protected_focus"],
            "protected_regression_focus",
            "row_level_blocker",
            "materialized_blocking",
            len(source["m2657_protected_focus"]),
            "protected",
            False,
            protected_focus_blockers > 0,
            _bool(m2657.get("actor_contract_shape_72_action_3")),
            _bool(m2657.get("hidden_or_oracle_actor_input_detected")),
            f"{protected_focus_blockers} protected focus rows block claims",
        ),
        evidence_row(
            "m2658_target_protected_report_result_audit",
            "m2658",
            source["paths"]["m2658_audit_doc"],
            "result_audit",
            "report_accepted_for_index_only",
            "materialized",
            1,
            "target_and_protected",
            False,
            True,
            True,
            False,
            "accepts M2657 as baseline-index input only",
        ),
    ]


def build_gap_matrix_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    m2657 = source["m2657_summary"]
    failed_gates = ";".join(m2657.get("m2655_failed_protected_gate_ids", []))
    return [
        gap_row(
            "route_a_pre_m2657_index_staleness",
            "Route A",
            "baseline_evidence_index",
            "resolved_by_m2659_materialization",
            "M2639 predates M2657 target/protected tradeoff report",
            "M2660 result audit of refreshed index",
            "admitted_to_result_audit",
            "prevents later route decisions from using stale pre-M2657 index",
            "do not use M2639 alone as current Route A index",
        ),
        gap_row(
            "route_a_target_improvement_evidence",
            "Route A",
            "target_tradeoff_rows",
            "indexed_bounded",
            "target rows improve but are not success denominator",
            "M2660 audit and later synthesis before another action",
            "admitted_to_index_only",
            "keeps target gains available without promotion claim",
            "do not claim repair success from target gates",
        ),
        gap_row(
            "route_a_protected_mitigation_blocker",
            "Route A",
            "protected_tradeoff_rows",
            "blocking",
            f"M2655 protected component gates fail: {failed_gates}",
            "audit or synthesis before any repair or baseline-readiness route",
            "blocks_repair_success_and_promotion",
            "keeps negative result visible in the baseline index",
            "do not weaken protected mitigation gates",
        ),
        gap_row(
            "route_a_same_row_repair_loop",
            "Route A",
            "repair_branch",
            "closed_pending_new_evidence_axis",
            "M2656 pivot closed same-row repair loop",
            "branch synthesis or new evidence route after M2660 audit",
            "not_admitted",
            "prevents public-gate local search",
            "do not run another same-row repair sweep",
        ),
        gap_row(
            "route_a_training_or_repair_admission",
            "Route A",
            "training_repair_action",
            "not_admitted",
            "needs M2660 audit and a new evidence axis or synthesis",
            "explicit post-index audit route decision",
            "not_admitted",
            "prevents training from targeting stale or protected-failing rows",
            "do not train from refreshed index alone",
        ),
        gap_row(
            "paper_self_id_verdict",
            "Route B",
            "paper_self_identification",
            "not_supported",
            "M2659 is an engineering index and no history-necessity test",
            "separate paper-route comparison panel",
            "not_admitted",
            "keeps Route A index from overclaiming self-ID evidence",
            "do not claim finite-window-vs-GRU or level3 self-ID",
        ),
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    allowed = {claim for claim, allowed_flag, _ in CLAIM_CHECKS if allowed_flag}
    return [
        {
            "claim_id": f"m2659_claim_boundary_{claim}",
            "claim_family": claim,
            "allowed_in_m2659": bool(allowed_flag),
            "status_pass": bool(claim in allowed or not allowed_flag),
            "evidence_required_before_claim": evidence_required,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim, allowed_flag, evidence_required in CLAIM_CHECKS
    ]


def build_next_action_admission_rows() -> list[dict[str, Any]]:
    return [
        next_action_row(
            "m2660_route_a_baseline_evidence_index_refresh_result_audit",
            "Route A",
            "admitted",
            "M2659 materializes refreshed index and must be audited before another route decision",
            "M2659 status_pass true and required artifacts present",
            "audit refreshed target/protected index without ranking or validation claims",
        ),
        next_action_row(
            "route_a_branch_synthesis_or_new_evidence_route",
            "Route A",
            "defer_until_m2660_audit",
            "synthesis or new evidence route must consume the audited refreshed index",
            "M2660 result audit",
            "choose synthesis stop or non-overfit new evidence route after audit",
        ),
        next_action_row(
            "another_same_row_source_only_repair",
            "Route A",
            "not_admitted",
            "M2656 closed the same-row repair loop and M2659 only refreshes the index",
            "new evidence axis and synthesis decision",
            "repair remains forbidden",
        ),
        next_action_row(
            "checkpoint_promotion_or_winner_selection",
            "Route A",
            "not_admitted",
            "M2655 selected candidate is diagnostic trace only and protected gates fail",
            "proof plus generalization plus promotion gate",
            "promotion remains forbidden",
        ),
        next_action_row(
            "validation_success_rate_or_driver_performance_claim",
            "Route A",
            "not_admitted",
            "M2659 is an evidence index refresh and performs no validation",
            "future validation manifest and claim audit",
            "validation and performance claims remain forbidden",
        ),
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
    gap_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    next_rows: list[dict[str, Any]],
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    m2657 = source["m2657_summary"]
    target_role_count = sum(1 for row in source["m2657_scenario_role_report"] if row.get("role_class") == "target")
    protected_role_count = sum(
        1 for row in source["m2657_scenario_role_report"] if row.get("role_class") == "protected"
    )
    protected_blocking_rows = [row for row in evidence_rows if _bool(row["protected_failure_blocking"])]
    target_rows = [row for row in evidence_rows if _bool(row["target_improvement_evidence"])]
    admitted_actions = [row["candidate_action_id"] for row in next_rows if row["admission_status"] == "admitted"]
    source_artifacts_present = all(source["source_exists"].values())
    m2657_report_gates_pass = bool(source["m2657_report_gates"]) and all(
        _bool(row.get("status_pass")) for row in source["m2657_report_gates"]
    )
    target_protected_split_preserved = (
        target_role_count == 3
        and protected_role_count == 1
        and _bool(m2657.get("protected_role_excluded_from_target_success_denominator"))
        and all(not _bool(row.get("protected_rows_in_success_denominator")) for row in source["m2657_tradeoff_rows"])
    )
    protected_failure_preserved = (
        _bool(m2657.get("m2655_target_preservation_gates_all_passed"))
        and not _bool(m2657.get("m2655_protected_component_gates_all_passed"))
        and not _bool(m2657.get("m2655_target_and_protected_gates_all_passed"))
        and len(protected_blocking_rows) >= 3
    )
    actor_contract_preserved = _all_actor_contract_ok(source["m2657_scenario_role_report"]) and _bool(
        m2657.get("actor_contract_shape_72_action_3")
    )
    hidden_oracle_clean = not _bool(m2657.get("hidden_or_oracle_actor_input_detected")) and not _any_hidden_detected(
        source["m2657_scenario_role_report"]
    )
    claim_boundary_pass = all(_bool(row["status_pass"]) for row in claim_rows) and not any(FALSE_CLAIM_FLAGS.values())
    status_pass = (
        source_artifacts_present
        and _bool(source["m2639_summary"].get("status_pass"))
        and _bool(source["m2641_summary"].get("status_pass"))
        and _bool(source["m2644_summary"].get("status_pass"))
        and _bool(source["m2648_summary"].get("status_pass"))
        and _bool(source["m2655_summary"].get("status_pass"))
        and _bool(m2657.get("status_pass"))
        and m2657_report_gates_pass
        and target_protected_split_preserved
        and protected_failure_preserved
        and actor_contract_preserved
        and hidden_oracle_clean
        and claim_boundary_pass
        and len(admitted_actions) == 1
        and source["source_exists"]["follow_up_manifest"]
    )
    summary = {
        "protocol_version": "engineering_controller_route_a_baseline_index_after_target_protected_report_v0",
        "result_class": (
            "engineering_controller_route_a_baseline_evidence_index_after_target_protected_report_refresh_pass"
            if status_pass
            else "engineering_controller_route_a_baseline_evidence_index_after_target_protected_report_refresh_failed"
        ),
        "status_pass": bool(status_pass),
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "evidence_index": str(paths["evidence_index"]),
        "gap_matrix": str(paths["gap_matrix"]),
        "claim_boundary_rows": str(paths["claim_boundary_rows"]),
        "next_action_admission": str(paths["next_action_admission"]),
        "doc": str(paths["doc"]),
        "follow_up_manifest": str(source["paths"]["follow_up_manifest"]),
        "follow_up_manifest_registered": source["source_exists"]["follow_up_manifest"],
        "required_artifacts_present": False,
        "source_artifacts_present": bool(source_artifacts_present),
        "source_artifacts_reanalyzed_only": True,
        "evidence_index_row_count": len(evidence_rows),
        "gap_matrix_row_count": len(gap_rows),
        "claim_boundary_row_count": len(claim_rows),
        "next_action_admission_row_count": len(next_rows),
        "admitted_next_action_count": len(admitted_actions),
        "selected_next_action": admitted_actions[0] if admitted_actions else "",
        "m2639_evidence_index_row_count": _int(source["m2639_summary"].get("evidence_index_row_count")),
        "m2641_behavior_row_count": _int(source["m2641_summary"].get("measured_behavior_row_count")),
        "m2644_repair_target_admission_row_count": _int(
            source["m2644_summary"].get("repair_target_admission_row_count")
        ),
        "m2648_repair_gate_evaluation_row_count": len(source["m2648_gates"]),
        "m2655_mitigation_preserving_gate_evaluation_row_count": len(source["m2655_gates"]),
        "m2657_report_indexed": True,
        "m2658_audit_indexed": True,
        "m2657_scenario_role_metric_report_row_count": len(source["m2657_scenario_role_report"]),
        "m2657_target_protected_tradeoff_row_count": len(source["m2657_tradeoff_rows"]),
        "m2657_protected_regression_focus_row_count": len(source["m2657_protected_focus"]),
        "m2657_report_gate_evaluation_row_count": len(source["m2657_report_gates"]),
        "target_role_count": target_role_count,
        "protected_role_count": protected_role_count,
        "target_evidence_index_row_count": len(target_rows),
        "protected_blocking_evidence_index_row_count": len(protected_blocking_rows),
        "target_protected_split_preserved": bool(target_protected_split_preserved),
        "protected_failure_blocking": bool(protected_failure_preserved),
        "protected_role_excluded_from_target_success_denominator": _bool(
            m2657.get("protected_role_excluded_from_target_success_denominator")
        ),
        "m2655_selected_candidate_id": m2657.get("m2655_selected_candidate_id", ""),
        "m2655_selected_candidate_treated_as_winner": False,
        "m2655_target_preservation_gates_all_passed": _bool(
            m2657.get("m2655_target_preservation_gates_all_passed")
        ),
        "m2655_protected_component_gates_all_passed": _bool(
            m2657.get("m2655_protected_component_gates_all_passed")
        ),
        "m2655_target_and_protected_gates_all_passed": _bool(
            m2657.get("m2655_target_and_protected_gates_all_passed")
        ),
        "m2655_failed_protected_gate_ids": m2657.get("m2655_failed_protected_gate_ids", []),
        "actor_contract_shape_72_action_3": bool(actor_contract_preserved),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": not hidden_oracle_clean,
        "taxonomy_labels_actor_visible": False,
        "repair_target_labels_actor_visible": False,
        "localization_labels_actor_visible": False,
        "objective_gate_labels_actor_visible": False,
        "route_decision_labels_actor_visible": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }
    summary.update(FALSE_CLAIM_FLAGS)
    return summary


def render_milestone_doc(
    summary: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
    gap_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    next_rows: list[dict[str, Any]],
) -> str:
    evidence_lines = "\n".join(
        "- "
        f"{row['evidence_id']}: {row['evidence_status']} rows={row['row_count']} "
        f"role={row['target_or_protected']} protected_blocking={row['protected_failure_blocking']}"
        for row in evidence_rows
    )
    gap_lines = "\n".join(
        f"- {row['gap_id']}: {row['current_status']} -> {row['admission_to_next_action']}"
        for row in gap_rows
    )
    claim_lines = "\n".join(
        f"- {row['claim_family']}: allowed={row['allowed_in_m2659']} pass={row['status_pass']}"
        for row in claim_rows
    )
    next_lines = "\n".join(
        f"- {row['candidate_action_id']}: {row['admission_status']} ({row['reason']})"
        for row in next_rows
    )
    failed_gates = ";".join(summary["m2655_failed_protected_gate_ids"])
    return f"""# M2659 Route A Baseline Evidence Index After Target/Protected Report Refresh

- status: {'completed' if summary['status_pass'] else 'failed'}
- result_class: `{summary['result_class']}`
- manifest: `experiments/manifests/{summary['milestone']}.json`
- summary: `{summary['summary']}`
- evidence index: `{summary['evidence_index']}`
- gap matrix: `{summary['gap_matrix']}`
- claim boundary rows: `{summary['claim_boundary_rows']}`
- next-action admission: `{summary['next_action_admission']}`
- evidence rows: {summary['evidence_index_row_count']}
- gap rows: {summary['gap_matrix_row_count']}
- claim rows: {summary['claim_boundary_row_count']}
- next-action rows: {summary['next_action_admission_row_count']}
- M2657 report indexed: {summary['m2657_report_indexed']}
- M2658 audit indexed: {summary['m2658_audit_indexed']}
- target/protected split preserved: {summary['target_protected_split_preserved']}
- protected failure blocking: {summary['protected_failure_blocking']}
- failed protected gates: `{failed_gates}`
- selected M2655 candidate: `{summary['m2655_selected_candidate_id']}` diagnostic only, not winner
- selected next action: `{summary['selected_next_action']}`
- actor/action boundary: P0 observation {P0_OBSERVATION_DIM} action {ACTION_DIM}; no hidden/oracle actor input
- supported operational claim: refreshed Route A baseline evidence index includes M2657/M2658
- rejected claims: {summary['forbidden_interpretation']}
- follow-up manifest: `{summary['follow_up_manifest']}`
- next: `{summary['next_blocker']}`

## Evidence Index

{evidence_lines}

## Gap Matrix

{gap_lines}

## Claim Boundary

{claim_lines}

## Next Actions

{next_lines}
"""


def evidence_row(
    evidence_id: str,
    source_milestone: str,
    artifact_path: Path,
    evidence_family: str,
    evidence_role: str,
    evidence_status: str,
    row_count: int,
    target_or_protected: str,
    target_improvement_evidence: bool,
    protected_failure_blocking: bool,
    actor_contract_shape_72_action_3: bool,
    hidden_oracle_actor_input_detected: bool,
    next_use: str,
) -> dict[str, Any]:
    return {
        "evidence_id": evidence_id,
        "source_milestone": source_milestone,
        "artifact_path": str(artifact_path),
        "evidence_family": evidence_family,
        "evidence_role": evidence_role,
        "evidence_status": evidence_status,
        "row_count": int(row_count),
        "target_or_protected": target_or_protected,
        "target_improvement_evidence": bool(target_improvement_evidence),
        "protected_failure_blocking": bool(protected_failure_blocking),
        "actor_contract_shape_72_action_3": bool(actor_contract_shape_72_action_3),
        "hidden_oracle_actor_input_detected": bool(hidden_oracle_actor_input_detected),
        "source_exists": artifact_path.exists(),
        "next_use": next_use,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def gap_row(
    gap_id: str,
    route: str,
    evidence_family: str,
    current_status: str,
    blocker: str,
    required_next_evidence: str,
    admission_to_next_action: str,
    evidence_expansion_value: str,
    forbidden_shortcut: str,
) -> dict[str, Any]:
    return {
        "gap_id": gap_id,
        "route": route,
        "evidence_family": evidence_family,
        "current_status": current_status,
        "blocker": blocker,
        "required_next_evidence": required_next_evidence,
        "admission_to_next_action": admission_to_next_action,
        "evidence_expansion_value": evidence_expansion_value,
        "forbidden_shortcut": forbidden_shortcut,
        "claim_scope": CLAIM_SCOPE,
    }


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


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _all_actor_contract_ok(rows: list[dict[str, str]]) -> bool:
    if not rows:
        return False
    if all("observation_shape" in row and "action_shape" in row for row in rows):
        return all(
            _int(row.get("observation_shape")) == P0_OBSERVATION_DIM
            and _int(row.get("action_shape")) == ACTION_DIM
            for row in rows
        )
    return all(_bool(row.get("actor_contract_shape_72_action_3")) for row in rows)


def _any_hidden_detected(rows: list[dict[str, str]]) -> bool:
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


def _hidden_detected(summary: dict[str, Any]) -> bool:
    return bool(
        _bool(summary.get("hidden_oracle_actor_input_detected"))
        or _bool(summary.get("hidden_or_oracle_actor_input_detected"))
        or _bool(summary.get("hidden_or_oracle_actor_inputs_required"))
        or not _bool(summary.get("no_hidden_oracle_actor_inputs_encoded", True))
    )


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    materialize_evidence_index_after_target_protected_report_refresh(
        args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
    )


if __name__ == "__main__":
    main()
