"""Materialize Route A readiness index after clearance-corrective negative result.

This runner reanalyzes existing Route A artifacts only. It does not execute
environments, policies, replay, validation, training, ranking, source builds,
adapter probes, or high-fidelity simulation.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from statistics import mean, median
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2804-engineering-controller-route-a-post-clearance-corrective-readiness-index-"
    "materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2805-engineering-controller-route-a-post-clearance-corrective-readiness-index-"
    "materialization-result-audit"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2804_engineering_controller_route_a_post_clearance_corrective_readiness_index"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2804-engineering-controller-route-a-post-clearance-corrective-readiness-index-"
    "materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2805-engineering-controller-route-a-post-clearance-corrective-"
    "readiness-index-materialization-result-audit.json"
)

M2803_DOC = Path(
    "docs/m2803-engineering-controller-route-a-source-only-belief-stress-clearance-localized-"
    "corrective-branch-synthesis.md"
)
M2802_DOC = Path(
    "docs/m2802-engineering-controller-route-a-source-only-belief-stress-clearance-localized-"
    "candidate-fresh-holdout-triad-delta-panel-result-audit.md"
)
M2801_DIR = Path(
    "runs/m2801_engineering_controller_route_a_source_only_belief_stress_clearance_localized_"
    "candidate_fresh_holdout_triad_delta_panel"
)
M2801_SUMMARY = M2801_DIR / "summary.json"
M2801_SOURCE_DELTAS = M2801_DIR / "candidate_minus_source_delta_rows.csv"
M2801_BASE_DELTAS = M2801_DIR / "candidate_minus_base_delta_rows.csv"
M2801_GATE_MATRIX = M2801_DIR / "gate_matrix.csv"
M2800_DOC = Path(
    "docs/m2800-engineering-controller-route-a-source-only-belief-stress-clearance-localized-"
    "corrective-training-result-audit.md"
)
M2799_SUMMARY = Path(
    "runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_"
    "corrective_training_preflight/summary.json"
)
M2749_SUMMARY = Path(
    "runs/m2749_engineering_controller_route_a_baseline_readiness_after_role_panel_diagnostic_"
    "index/summary.json"
)
M2749_EVIDENCE = Path(
    "runs/m2749_engineering_controller_route_a_baseline_readiness_after_role_panel_diagnostic_"
    "index/evidence_index.csv"
)
M2749_DELIVERABLES = Path(
    "runs/m2749_engineering_controller_route_a_baseline_readiness_after_role_panel_diagnostic_"
    "index/deliverable_readiness_rows.csv"
)
M2749_BLOCKERS = Path(
    "runs/m2749_engineering_controller_route_a_baseline_readiness_after_role_panel_diagnostic_"
    "index/blocker_matrix.csv"
)
M2749_NEXT_ACTIONS = Path(
    "runs/m2749_engineering_controller_route_a_baseline_readiness_after_role_panel_diagnostic_"
    "index/next_action_admission_rows.csv"
)
M2667_SUMMARY = Path(
    "runs/m2667_engineering_controller_route_a_engineering_baseline_readiness_index_"
    "after_protected_taxonomy/summary.json"
)
M2541_SUMMARY = Path(
    "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/summary.json"
)
M2541_ACTOR_CONTRACT = Path(
    "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/"
    "actor_io_contract_snapshot.json"
)
M2505_SUMMARY = Path("public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505/summary.json")
M2508_SUMMARY = Path("runs/m2508_engineering_controller_runtime_inference_cost_report/summary.json")
M2638_DOC = Path(
    "docs/m2638-engineering-controller-route-c-hf3-source-dependency-blocker-report-"
    "and-user-supplied-source-contract-design.md"
)
ROUTE_PLAN = Path("docs/post-m2470-route-plan.md")

CLAIM_SCOPE = (
    "Route A post-clearance-corrective readiness/admission index only; existing-artifact "
    "reanalysis with no reset, step, rollout, replay, validation, training, PPO, source "
    "build, adapter probe, external simulation, ranking, winner selection, promotion, "
    "success-rate verdict, repair-success, driver-performance, paper, finite-window-vs-GRU, "
    "current-sim, high-fidelity validation, full ideal driver, or self-ID claim"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness, validation result, controller "
    "ranking, source-family ranking, task-family ranking, profile ranking, scenario-role "
    "ranking, winner selection, checkpoint promotion, success-rate verdict, paper evidence, "
    "finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity validation result, "
    "full ideal driver completion, or self-ID evidence"
)
FALSE_CLAIM_FLAGS = {
    "environment_reset_run": False,
    "environment_step_run": False,
    "source_only_backend_reset_run": False,
    "source_only_backend_step_run": False,
    "policy_action_run": False,
    "policy_rollout_run": False,
    "closed_loop_rollout_run": False,
    "replay_run": False,
    "measured_validation_run": False,
    "new_repair_training_or_rollout_run": False,
    "repair_execution_started": False,
    "repair_training_started": False,
    "training_run": False,
    "ppo_run": False,
    "source_build_run": False,
    "adapter_probe_run": False,
    "backend_started": False,
    "external_high_fidelity_simulation_included": False,
    "high_fidelity_simulation_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_computed": False,
    "success_rate_metric_recorded": False,
    "success_rate_verdict_field_emitted": False,
    "controller_family_verdict_computed": False,
    "repair_success_claim_made": False,
    "driver_performance_claim_made": False,
    "validation_readiness_claim_made": False,
    "validation_result_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_readiness_claim_made": False,
    "high_fidelity_validation_claim_made": False,
    "full_ideal_driver_completion_claim_made": False,
    "full_ideal_driver_gate_passed": False,
    "level3_self_id_claim_made": False,
    "private_holdout_used": False,
}

EVIDENCE_FIELDNAMES = [
    "evidence_id",
    "source_milestone",
    "artifact_path",
    "evidence_family",
    "evidence_status",
    "row_count",
    "actor_contract_shape_72_action_3",
    "action_shape_3",
    "hidden_oracle_actor_input_detected",
    "clearance_positive_count",
    "clearance_negative_count",
    "clearance_mean",
    "clearance_median",
    "stable_avoidable_negative_count",
    "claim_scope",
    "gap_or_limit",
    "next_use",
    "source_exists",
    "forbidden_interpretation",
]
DELIVERABLE_FIELDNAMES = [
    "deliverable_id",
    "route_a_requirement",
    "source_milestone",
    "artifact_path",
    "readiness_status",
    "row_count",
    "blocker_count",
    "current_limitation",
    "next_use",
    "claim_boundary",
]
BLOCKER_FIELDNAMES = [
    "blocker_id",
    "route",
    "evidence_family",
    "current_status",
    "blocking_count",
    "required_next_evidence",
    "admission_to_next_action",
    "evidence_expansion_value",
    "forbidden_shortcut",
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
    "allowed_in_m2804",
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
    ("route_a_post_clearance_corrective_readiness_index_materialized", True, "M2804 readiness index artifacts"),
    ("m2801_negative_clearance_indexed", True, "M2801/M2802 negative clearance diagnostics preserved"),
    ("stable_avoidable_retention_risk_indexed", True, "M2801 stable_avoidable negative rows preserved"),
    ("route_a_deliverable_readiness_refreshed", True, "Route A deliverable rows refreshed after M2803"),
    ("protected_blocker_preserved", True, "M2667 protected blocker remains visible"),
    ("hf3_blocker_preserved", True, "M2638 HF3 source dependency blocker remains visible"),
    ("actor_contract_indexed", True, "P0 observation 72/action 3 actor contract indexed"),
    ("follow_up_result_audit_registered", True, "M2805 result-audit manifest"),
    ("repair_success", False, "future repair result plus claim audit"),
    ("driver_performance", False, "future validation and claim audit"),
    ("validation_readiness", False, "future validation-readiness route decision"),
    ("validation_result", False, "future validation result"),
    ("controller_ranking", False, "future explicit ranking gate"),
    ("source_family_ranking", False, "future explicit ranking gate"),
    ("task_family_ranking", False, "future explicit ranking gate"),
    ("profile_ranking", False, "future explicit ranking gate"),
    ("scenario_role_ranking", False, "future explicit ranking gate"),
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


def materialize_post_clearance_corrective_readiness_index(
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
    clearance = build_clearance_accounting(source)
    evidence_rows = build_evidence_index_rows(source, clearance)
    deliverable_rows = build_deliverable_readiness_rows(source, clearance)
    blocker_rows = build_blocker_matrix_rows(source, clearance)
    next_rows = build_next_action_admission_rows()
    claim_rows = build_claim_boundary_rows()

    paths = {
        "summary": output_path / "summary.json",
        "evidence_index": output_path / "evidence_index.csv",
        "deliverable_readiness_rows": output_path / "deliverable_readiness_rows.csv",
        "blocker_matrix": output_path / "blocker_matrix.csv",
        "next_action_admission_rows": output_path / "next_action_admission_rows.csv",
        "claim_boundary_rows": output_path / "claim_boundary_rows.csv",
        "gate_matrix": output_path / "gate_matrix.csv",
        "doc": Path(doc_path),
    }

    write_csv_rows(paths["evidence_index"], evidence_rows, fieldnames=EVIDENCE_FIELDNAMES)
    write_csv_rows(paths["deliverable_readiness_rows"], deliverable_rows, fieldnames=DELIVERABLE_FIELDNAMES)
    write_csv_rows(paths["blocker_matrix"], blocker_rows, fieldnames=BLOCKER_FIELDNAMES)
    write_csv_rows(paths["next_action_admission_rows"], next_rows, fieldnames=NEXT_ACTION_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)

    gate_rows = build_gate_matrix_rows(
        source,
        clearance,
        evidence_rows,
        deliverable_rows,
        blocker_rows,
        next_rows,
        claim_rows,
        required_artifacts_present=False,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output_path,
        paths=paths,
        source=source,
        clearance=clearance,
        evidence_rows=evidence_rows,
        deliverable_rows=deliverable_rows,
        blocker_rows=blocker_rows,
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
        clearance,
        evidence_rows,
        deliverable_rows,
        blocker_rows,
        next_rows,
        claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output_path,
        paths=paths,
        source=source,
        clearance=clearance,
        evidence_rows=evidence_rows,
        deliverable_rows=deliverable_rows,
        blocker_rows=blocker_rows,
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
        "m2803_doc": M2803_DOC,
        "m2802_doc": M2802_DOC,
        "m2801_summary": M2801_SUMMARY,
        "m2801_source_deltas": M2801_SOURCE_DELTAS,
        "m2801_base_deltas": M2801_BASE_DELTAS,
        "m2801_gate_matrix": M2801_GATE_MATRIX,
        "m2800_doc": M2800_DOC,
        "m2799_summary": M2799_SUMMARY,
        "m2749_summary": M2749_SUMMARY,
        "m2749_evidence": M2749_EVIDENCE,
        "m2749_deliverables": M2749_DELIVERABLES,
        "m2749_blockers": M2749_BLOCKERS,
        "m2749_next_actions": M2749_NEXT_ACTIONS,
        "m2667_summary": M2667_SUMMARY,
        "m2541_summary": M2541_SUMMARY,
        "m2541_actor_contract": M2541_ACTOR_CONTRACT,
        "m2505_summary": M2505_SUMMARY,
        "m2508_summary": M2508_SUMMARY,
        "m2638_doc": M2638_DOC,
        "route_plan": ROUTE_PLAN,
        "follow_up_manifest": Path(follow_up_manifest),
    }
    return {
        "paths": paths,
        "source_exists": {name: path.exists() for name, path in paths.items()},
        "m2803_doc_text": paths["m2803_doc"].read_text(encoding="utf-8"),
        "m2802_doc_text": paths["m2802_doc"].read_text(encoding="utf-8"),
        "m2801_summary": read_json(paths["m2801_summary"]),
        "m2801_source_deltas": _read_csv_rows(paths["m2801_source_deltas"]),
        "m2801_base_deltas": _read_csv_rows(paths["m2801_base_deltas"]),
        "m2801_gate_matrix": _read_csv_rows(paths["m2801_gate_matrix"]),
        "m2799_summary": read_json(paths["m2799_summary"]),
        "m2749_summary": read_json(paths["m2749_summary"]),
        "m2749_evidence": _read_csv_rows(paths["m2749_evidence"]),
        "m2749_deliverables": _read_csv_rows(paths["m2749_deliverables"]),
        "m2749_blockers": _read_csv_rows(paths["m2749_blockers"]),
        "m2749_next_actions": _read_csv_rows(paths["m2749_next_actions"]),
        "m2667_summary": read_json(paths["m2667_summary"]),
        "m2541_summary": read_json(paths["m2541_summary"]),
        "m2541_actor_contract": read_json(paths["m2541_actor_contract"]),
        "m2505_summary": read_json(paths["m2505_summary"]),
        "m2508_summary": read_json(paths["m2508_summary"]),
    }


def build_clearance_accounting(source: dict[str, Any]) -> dict[str, Any]:
    source_rows = source["m2801_source_deltas"]
    base_rows = source["m2801_base_deltas"]
    source_stats = _metric_stats(source_rows, "candidate_minus_reference_minimum_obstacle_clearance_m")
    base_stats = _metric_stats(base_rows, "candidate_minus_reference_minimum_obstacle_clearance_m")
    stable_source = [
        row for row in source_rows if row.get("role_family") == "stable_avoidable"
    ]
    stable_base = [
        row for row in base_rows if row.get("role_family") == "stable_avoidable"
    ]
    stable_source_stats = _metric_stats(stable_source, "candidate_minus_reference_minimum_obstacle_clearance_m")
    stable_base_stats = _metric_stats(stable_base, "candidate_minus_reference_minimum_obstacle_clearance_m")
    return {
        "source": source_stats,
        "m2791_start": base_stats,
        "stable_source": stable_source_stats,
        "stable_m2791_start": stable_base_stats,
        "triad_execution_rows": _int(source["m2801_summary"].get("triad_execution_row_count")),
        "candidate_minus_source_delta_rows": len(source_rows),
        "candidate_minus_m2791_start_delta_rows": len(base_rows),
        "gate_rows": _int(source["m2801_summary"].get("gate_matrix_row_count")),
        "proof_gate_rows": _int(source["m2801_summary"].get("proof_gate_row_count")),
        "generalization_gate_rows": _int(source["m2801_summary"].get("generalization_gate_row_count")),
        "behavior_retention_gate_rows": _int(source["m2801_summary"].get("behavior_retention_gate_row_count")),
    }


def build_evidence_index_rows(source: dict[str, Any], clearance: dict[str, Any]) -> list[dict[str, Any]]:
    actor_ok = actor_contract_preserved(source)
    hidden = hidden_oracle_actor_input_detected(source)
    paths = source["paths"]
    return [
        evidence_row(
            "m2803_clearance_corrective_branch_synthesis",
            "m2803",
            paths["m2803_doc"],
            "branch_synthesis",
            "pivot_to_route_a_post_clearance_corrective_readiness_index",
            1,
            actor_ok,
            hidden,
            None,
            "closes same clearance-localized corrective repair loop",
            "governing pivot for M2804 admission rows",
        ),
        evidence_row(
            "m2802_fresh_holdout_triad_result_audit",
            "m2802",
            paths["m2802_doc"],
            "result_audit",
            "accepted_claim_safe_negative_clearance_diagnostic",
            1,
            actor_ok,
            hidden,
            None,
            "audit accepts M2801 artifacts but rejects repair-success interpretation",
            "claim boundary for M2804",
        ),
        evidence_row(
            "m2801_fresh_holdout_triad_summary",
            "m2801",
            paths["m2801_summary"],
            "closed_loop_diagnostic_summary",
            "negative_clearance_skew_claim_safe",
            clearance["triad_execution_rows"],
            actor_ok,
            hidden,
            None,
            "216 triad execution rows with 38 gates all pass but clearance negative",
            "primary negative diagnostic input",
        ),
        evidence_row(
            "m2801_candidate_minus_source_clearance_deltas",
            "m2801",
            paths["m2801_source_deltas"],
            "clearance_delta_rows",
            "source_reference_negative",
            clearance["source"]["count"],
            actor_ok,
            hidden,
            clearance["source"],
            "23 positive and 49 negative obstacle-clearance rows",
            "active behavior-regression blocker",
        ),
        evidence_row(
            "m2801_candidate_minus_m2791_start_clearance_deltas",
            "m2801",
            paths["m2801_base_deltas"],
            "clearance_delta_rows",
            "m2791_start_reference_negative",
            clearance["m2791_start"]["count"],
            actor_ok,
            hidden,
            clearance["m2791_start"],
            "23 positive and 49 negative obstacle-clearance rows",
            "active behavior-regression blocker",
        ),
        evidence_row(
            "m2801_stable_avoidable_retention_risk",
            "m2801",
            paths["m2801_summary"],
            "behavior_retention",
            "stable_avoidable_negative_rows_present",
            clearance["stable_source"]["count"],
            actor_ok,
            hidden,
            clearance["stable_source"],
            "stable_avoidable has negative clearance rows against source and M2791 start",
            "behavior-retention risk for future Route A actions",
        ),
        evidence_row(
            "m2800_clearance_corrective_training_result_audit",
            "m2800",
            paths["m2800_doc"],
            "result_audit",
            "accepted_preflight_not_repair_success",
            1,
            actor_ok,
            hidden,
            None,
            "M2800 accepted M2799 artifacts but rejected repair-success claims",
            "lineage and claim-boundary input",
        ),
        evidence_row(
            "m2799_clearance_corrective_preflight",
            "m2799",
            paths["m2799_summary"],
            "corrective_preflight",
            "candidate_artifact_only",
            _int(source["m2799_summary"].get("gate_matrix_row_count")),
            actor_ok,
            hidden,
            None,
            "candidate checkpoint exists but was not promoted",
            "lineage input only",
        ),
        evidence_row(
            "m2749_prior_route_a_readiness_index",
            "m2749",
            paths["m2749_summary"],
            "prior_readiness_index",
            "stale_after_m2801_m2802_negative_clearance",
            _int(source["m2749_summary"].get("route_a_deliverable_readiness_row_count")),
            actor_ok,
            hidden,
            None,
            "prior readiness index must be refreshed after the failed corrective branch",
            "baseline for M2804 deliverable rows",
        ),
        evidence_row(
            "m2667_protected_mitigation_blocker",
            "m2667",
            paths["m2667_summary"],
            "known_failure_boundary",
            "protected_mitigation_blocker_preserved",
            _int(source["m2667_summary"].get("known_failure_boundary_row_count")),
            actor_ok,
            hidden,
            None,
            "protected rows remain outside ordinary success denominators",
            "blocks validation readiness and driver-performance interpretation",
        ),
        evidence_row(
            "m2541_baseline_actor_contract",
            "m2541",
            paths["m2541_actor_contract"],
            "actor_contract",
            "p0_observation_72_action_3_no_oracle",
            1,
            actor_ok,
            hidden,
            None,
            "contract is deployable actor input/output only",
            "actor contract guard for all Route A next actions",
        ),
        evidence_row(
            "m2505_public_benchmark_pack",
            "m2505",
            paths["m2505_summary"],
            "public_benchmark_pack",
            "source_only_diagnostic_pack_ready",
            _int(source["m2505_summary"].get("artifact_manifest_rows")),
            actor_ok,
            hidden,
            None,
            "source-only diagnostic pack is not validation or performance evidence",
            "package input with explicit limitations",
        ),
        evidence_row(
            "m2508_runtime_inference_cost_report",
            "m2508",
            paths["m2508_summary"],
            "runtime_inference_cost",
            "actor_forward_cost_measured",
            _int(source["m2508_summary"].get("measurement_row_count")),
            actor_ok,
            hidden,
            None,
            "actor-forward runtime report uses synthetic shape-only observations",
            "runtime deliverable input",
        ),
        evidence_row(
            "m2638_hf3_source_dependency_blocker",
            "m2638",
            paths["m2638_doc"],
            "hf3_source_dependency",
            "blocked_until_user_supplied_source",
            1,
            actor_ok,
            hidden,
            None,
            "selected-platform HF3 execution remains paused without source dependency",
            "prevents high-fidelity execution admission from M2804",
        ),
        evidence_row(
            "post_m2470_route_plan",
            "post-m2470",
            paths["route_plan"],
            "route_plan",
            "route_a_governing_context",
            1,
            actor_ok,
            hidden,
            None,
            "Route A readiness must stay separate from Route B paper and Route C HF validation",
            "governs M2804 deliverable and admission scope",
        ),
    ]


def build_deliverable_readiness_rows(source: dict[str, Any], clearance: dict[str, Any]) -> list[dict[str, Any]]:
    specs = [
        (
            "baseline_checkpoint_list",
            "baseline checkpoint list",
            "m2541/m2799",
            source["paths"]["m2541_summary"],
            "ready_with_negative_clearance_limitations",
            _int(source["m2541_summary"].get("baseline_checkpoint_count")),
            clearance["source"]["negative"],
            "baseline and corrective checkpoints are lineage inputs only; no promotion",
            "M2805 audit and any later package/readiness decision",
        ),
        (
            "actor_input_output_contract",
            "actor input/output contract",
            "m2541/m2801",
            source["paths"]["m2541_actor_contract"],
            "ready_contract_guarded",
            1,
            0,
            "P0 observation 72 action 3; hidden/oracle features forbidden",
            "hard actor boundary for future Route A work",
        ),
        (
            "public_benchmark_pack",
            "public benchmark pack",
            "m2505",
            source["paths"]["m2505_summary"],
            "ready_source_only_diagnostic",
            _int(source["m2505_summary"].get("artifact_manifest_rows")),
            1,
            "source-only diagnostic scope; not validation readiness",
            "package evidence input with explicit limitations",
        ),
        (
            "known_failure_taxonomy",
            "known failure taxonomy",
            "m2749/m2803",
            source["paths"]["m2749_summary"],
            "needs_refresh_after_negative_clearance",
            _int(source["m2749_summary"].get("blocker_matrix_row_count")),
            3,
            "M2801/M2802 add active clearance and stable_avoidable retention blockers",
            "failure surface input for next evidence route",
        ),
        (
            "runtime_inference_cost_report",
            "runtime/inference-cost report",
            "m2508",
            source["paths"]["m2508_summary"],
            "ready_actor_only_runtime",
            _int(source["m2508_summary"].get("measurement_row_count")),
            0,
            "runtime is actor-forward cost only, not environment validation",
            "runtime deliverable for Route A baseline package",
        ),
        (
            "scenario_role_metric_report",
            "scenario-role metric report",
            "m2749/m2801",
            source["paths"]["m2801_summary"],
            "refreshed_with_clearance_negative_diagnostic",
            clearance["triad_execution_rows"],
            clearance["source"]["negative"],
            "role and stress labels remain actor-invisible and non-ranking",
            "role/metric context for future non-same-repair route",
        ),
        (
            "clearance_corrective_negative_result",
            "post-clearance corrective negative result",
            "m2801/m2802/m2803",
            source["paths"]["m2801_summary"],
            "active_blocker",
            clearance["source"]["count"] + clearance["m2791_start"]["count"],
            clearance["source"]["negative"] + clearance["m2791_start"]["negative"],
            "same clearance-localized corrective loop failed fresh holdout",
            "blocks same repair update and promotion claims",
        ),
        (
            "stable_avoidable_retention_risk",
            "stable_avoidable behavior-retention risk",
            "m2801/m2802",
            source["paths"]["m2801_summary"],
            "active_blocker",
            clearance["stable_source"]["count"] + clearance["stable_m2791_start"]["count"],
            clearance["stable_source"]["negative"] + clearance["stable_m2791_start"]["negative"],
            "stable_avoidable has negative clearance rows after corrective update",
            "must be protected before future execution or training routes",
        ),
        (
            "protected_mitigation_blocker",
            "protected mitigation blocker",
            "m2667",
            source["paths"]["m2667_summary"],
            "active_blocker",
            _int(source["m2667_summary"].get("known_failure_boundary_row_count")),
            _int(source["m2667_summary"].get("known_failure_blocking_boundary_row_count")),
            "protected mitigation remains broad and blocking outside success denominators",
            "blocks validation readiness and performance claims",
        ),
        (
            "hf3_source_dependency",
            "HF3 source dependency",
            "m2638",
            source["paths"]["m2638_doc"],
            "active_blocker",
            1,
            1,
            "selected-platform HF3 execution is paused until source dependency is supplied",
            "blocks HF3 execution admission from M2804",
        ),
        (
            "driver_performance_or_validation",
            "driver performance or validation readiness",
            "m2804",
            DEFAULT_DOC_PATH,
            "not_ready",
            0,
            1,
            "M2804 is artifact reanalysis and cannot support validation or performance claims",
            "requires future separately registered validation evidence and claim audit",
        ),
    ]
    return [
        {
            "deliverable_id": deliverable_id,
            "route_a_requirement": requirement,
            "source_milestone": milestone,
            "artifact_path": str(path),
            "readiness_status": status,
            "row_count": row_count,
            "blocker_count": blocker_count,
            "current_limitation": limitation,
            "next_use": next_use,
            "claim_boundary": CLAIM_SCOPE,
        }
        for deliverable_id, requirement, milestone, path, status, row_count, blocker_count, limitation, next_use in specs
    ]


def build_blocker_matrix_rows(source: dict[str, Any], clearance: dict[str, Any]) -> list[dict[str, Any]]:
    protected_count = _int(source["m2667_summary"].get("known_failure_blocking_boundary_row_count"))
    return [
        blocker_row(
            "m2804_blocker_clearance_negative_fresh_holdout",
            "Route A",
            "clearance_delta_rows",
            "active",
            clearance["source"]["negative"] + clearance["m2791_start"]["negative"],
            "M2805 audit before any new execution route; no same corrective update",
            "admits_result_audit_only",
            "keeps M2801 obstacle-clearance negative skew visible as non-ranking diagnostic evidence",
            "do not reinterpret road-margin speed yaw-rate or action-delta positives as repair success",
        ),
        blocker_row(
            "m2804_blocker_stable_avoidable_retention_risk",
            "Route A",
            "behavior_retention",
            "active",
            clearance["stable_source"]["negative"] + clearance["stable_m2791_start"]["negative"],
            "future route must preserve stable_avoidable before promotion or validation claims",
            "blocks_promotion_validation_claims",
            "keeps stable_avoidable negative rows first-class instead of side effects",
            "do not weaken stable_avoidable retention guards",
        ),
        blocker_row(
            "m2804_blocker_same_clearance_corrective_local_search",
            "Route A",
            "local_search_guard",
            "closed_by_m2803_pivot",
            1,
            "new evidence axis, result audit, or synthesis stop after M2805",
            "not_admitted",
            "prevents another same actor-head clearance repair loop",
            "do not open another M2799-like same-surface repair from M2804",
        ),
        blocker_row(
            "m2804_blocker_protected_mitigation",
            "Route A",
            "known_failure_boundary",
            "active",
            protected_count,
            "future evidence must keep protected rows outside ordinary success denominators",
            "blocks_validation_performance_claims",
            "preserves M2667 protected mitigation boundary",
            "do not weaken or hide protected mitigation rows",
        ),
        blocker_row(
            "m2804_blocker_hf3_source_dependency_unavailable",
            "Route C",
            "hf3_dependency",
            "paused_by_m2638",
            1,
            "valid user-supplied source root or dependency acquisition route",
            "not_admitted",
            "keeps high-fidelity route explicit without fetching or building source",
            "do not fetch install build probe or run external simulator",
        ),
        blocker_row(
            "m2804_blocker_validation_performance_not_admitted",
            "Route A",
            "claim_boundary",
            "not_admitted",
            1,
            "separately registered validation manifest plus claim audit",
            "not_admitted",
            "prevents readiness rows from becoming performance evidence",
            "do not claim validation readiness or driver performance from M2804",
        ),
        blocker_row(
            "m2804_blocker_actor_contract_guard",
            "Route A",
            "actor_contract",
            "pass",
            0,
            "preserve P0 observation 72 action 3 and no hidden/oracle actor input",
            "guard_pass",
            "keeps all taxonomy/role/metric/blocker/verdict labels actor-invisible",
            "do not change actor inputs or deployed action contract",
        ),
    ]


def build_next_action_admission_rows() -> list[dict[str, Any]]:
    return [
        next_action_row(
            "m2805_route_a_post_clearance_corrective_readiness_index_result_audit",
            "Route A",
            "admitted",
            "M2804 materializes the refreshed readiness/admission index and must be audited",
            "M2804 status_pass true and required artifacts present",
            "audit readiness rows and choose synthesis stop or non-same-repair evidence axis",
        ),
        next_action_row(
            "route_a_non_same_repair_execution_surface",
            "Route A",
            "defer_until_m2805_audit",
            "execution may be considered only after M2805 audits evidence boundaries and selects a new axis",
            "M2805 audit and explicit design manifest",
            "keeps future execution separated from M2799/M2801 local repair loop",
        ),
        next_action_row(
            "same_clearance_localized_corrective_update",
            "Route A",
            "not_admitted",
            "M2803 pivot rejects another same clearance-localized corrective update",
            "new evidence axis plus result audit and design manifest",
            "prevents overfitting M2801 clearance rows",
        ),
        next_action_row(
            "same_style_fresh_holdout_triad_panel",
            "Route A",
            "not_admitted",
            "another same-style triad panel would be local search without a new route decision",
            "new evidence axis or synthesis stop after M2805",
            "prevents repeated measurement over the same branch",
        ),
        next_action_row(
            "hf3_selected_platform_execution",
            "Route C",
            "not_admitted",
            "M2638 source dependency remains unavailable",
            "valid source dependency route or user-supplied source root",
            "keeps high-fidelity execution separate from M2804",
        ),
        next_action_row(
            "controller_ranking_or_winner_selection",
            "Route A",
            "not_admitted",
            "M2804 is readiness indexing and does not compare or rank controllers",
            "future proof plus generalization plus promotion gate",
            "ranking and winner selection remain forbidden",
        ),
        next_action_row(
            "validation_or_driver_performance_claim",
            "Route A",
            "not_admitted",
            "M2804 performs no reset rollout replay validation or performance test",
            "future validation manifest and claim audit",
            "validation and performance claims remain forbidden",
        ),
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": f"m2804_claim_boundary_{claim}",
            "claim_family": claim,
            "allowed_in_m2804": allowed,
            "status_pass": True,
            "evidence_required_before_claim": evidence_required,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim, allowed, evidence_required in CLAIM_CHECKS
    ]


def build_gate_matrix_rows(
    source: dict[str, Any],
    clearance: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
    deliverable_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    next_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    *,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    return [
        gate_row("m2804_gate_source_artifacts_present", "artifact", all(source["source_exists"].values()), True),
        gate_row("m2804_gate_required_artifacts_present", "artifact", required_artifacts_present, True),
        gate_row("m2804_gate_m2803_synthesis_doc_present", "lineage", source["source_exists"]["m2803_doc"], True),
        gate_row("m2804_gate_m2803_pivot_preserved", "lineage", m2803_pivot_preserved(source), True),
        gate_row("m2804_gate_m2802_audit_doc_present", "lineage", source["source_exists"]["m2802_doc"], True),
        gate_row("m2804_gate_m2801_summary_status_pass", "lineage", source["m2801_summary"].get("status_pass"), True),
        gate_row("m2804_gate_m2801_gate_matrix_pass", "lineage", source["m2801_summary"].get("gate_matrix_pass"), True),
        gate_row("m2804_gate_m2801_triad_rows_preserved", "diagnostic_accounting", clearance["triad_execution_rows"], 216),
        gate_row("m2804_gate_m2801_source_delta_rows_preserved", "diagnostic_accounting", clearance["source"]["count"], 72),
        gate_row("m2804_gate_m2801_m2791_start_delta_rows_preserved", "diagnostic_accounting", clearance["m2791_start"]["count"], 72),
        gate_row("m2804_gate_source_clearance_positive_count", "diagnostic_accounting", clearance["source"]["positive"], 23),
        gate_row("m2804_gate_source_clearance_negative_count", "diagnostic_accounting", clearance["source"]["negative"], 49),
        gate_row("m2804_gate_m2791_start_clearance_positive_count", "diagnostic_accounting", clearance["m2791_start"]["positive"], 23),
        gate_row("m2804_gate_m2791_start_clearance_negative_count", "diagnostic_accounting", clearance["m2791_start"]["negative"], 49),
        gate_row("m2804_gate_stable_avoidable_source_negative_count", "behavior_retention", clearance["stable_source"]["negative"], 4),
        gate_row("m2804_gate_stable_avoidable_m2791_start_negative_count", "behavior_retention", clearance["stable_m2791_start"]["negative"], 2),
        gate_row("m2804_gate_seed_indices_disjoint", "generalization", source["m2801_summary"].get("fresh_holdout_seed_indices_disjoint_from_previous"), True),
        gate_row("m2804_gate_horizon_longer_than_m2793", "generalization", source["m2801_summary"].get("horizon_longer_than_m2793"), True),
        gate_row("m2804_gate_mitigation_reference_rows_guarded", "known_failure_boundary", source["m2801_summary"].get("mitigation_reference_rows_guarded"), True),
        gate_row("m2804_gate_prior_readiness_status_pass", "lineage", source["m2749_summary"].get("status_pass"), True),
        gate_row("m2804_gate_deliverables_indexed", "artifact", len(deliverable_rows), 11),
        gate_row("m2804_gate_evidence_rows_materialized", "artifact", len(evidence_rows), 15),
        gate_row("m2804_gate_blocker_rows_materialized", "artifact", len(blocker_rows), 7),
        gate_row("m2804_gate_actor_contract_72_action_3", "actor_contract", actor_contract_preserved(source), True),
        gate_row("m2804_gate_hidden_oracle_actor_input_absent", "actor_contract", hidden_oracle_actor_input_detected(source), False),
        gate_row("m2804_gate_actor_visible_labels_absent", "actor_contract", actor_visible_labels_detected(source), False),
        gate_row("m2804_gate_protected_blocker_preserved", "known_failure_boundary", protected_blocker_preserved(source), True),
        gate_row("m2804_gate_protected_rows_outside_success_denominator", "known_failure_boundary", protected_rows_in_success_denominator(source), False),
        gate_row("m2804_gate_hf3_source_dependency_blocker_present", "hf3_dependency", source["source_exists"]["m2638_doc"], True),
        gate_row("m2804_gate_follow_up_result_audit_registered", "process", source["source_exists"]["follow_up_manifest"], True),
        gate_row(
            "m2804_gate_single_admitted_next_action",
            "process",
            sum(1 for row in next_rows if row["admission_status"] == "admitted"),
            1,
        ),
        gate_row(
            "m2804_gate_same_clearance_update_not_admitted",
            "process",
            any(
                row["candidate_action_id"] == "same_clearance_localized_corrective_update"
                and row["admission_status"] == "admitted"
                for row in next_rows
            ),
            False,
        ),
        gate_row(
            "m2804_gate_same_style_triad_panel_not_admitted",
            "process",
            any(
                row["candidate_action_id"] == "same_style_fresh_holdout_triad_panel"
                and row["admission_status"] == "admitted"
                for row in next_rows
            ),
            False,
        ),
        gate_row(
            "m2804_gate_claim_boundary_pass",
            "claim_boundary",
            all(_bool(row["status_pass"]) for row in claim_rows) and not any(FALSE_CLAIM_FLAGS.values()),
            True,
        ),
        gate_row("m2804_gate_no_reset_rollout_training_validation", "claim_boundary", False, False),
        gate_row("m2804_gate_no_source_build_adapter_probe_external_sim", "claim_boundary", False, False),
        gate_row("m2804_gate_no_ranking_promotion_success_rate_performance", "claim_boundary", False, False),
        gate_row("m2804_gate_no_paper_current_sim_hf_full_driver_self_id_claim", "claim_boundary", False, False),
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    clearance: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
    deliverable_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    next_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    admitted_actions = [row["candidate_action_id"] for row in next_rows if row["admission_status"] == "admitted"]
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    negative_clearance_preserved = (
        clearance["source"]["positive"] == 23
        and clearance["source"]["negative"] == 49
        and clearance["m2791_start"]["positive"] == 23
        and clearance["m2791_start"]["negative"] == 49
    )
    stable_risk_preserved = (
        clearance["stable_source"]["negative"] == 4
        and clearance["stable_m2791_start"]["negative"] == 2
    )
    status_pass = (
        required_artifacts_present
        and all(source["source_exists"].values())
        and _bool(source["m2801_summary"].get("status_pass"))
        and _bool(source["m2801_summary"].get("gate_matrix_pass"))
        and _bool(source["m2799_summary"].get("status_pass"))
        and _bool(source["m2749_summary"].get("status_pass"))
        and _bool(source["m2667_summary"].get("status_pass"))
        and _bool(source["m2541_summary"].get("status_pass"))
        and _bool(source["m2505_summary"].get("status_pass"))
        and _bool(source["m2508_summary"].get("status_pass"))
        and m2803_pivot_preserved(source)
        and negative_clearance_preserved
        and stable_risk_preserved
        and actor_contract_preserved(source)
        and not hidden_oracle_actor_input_detected(source)
        and not actor_visible_labels_detected(source)
        and protected_blocker_preserved(source)
        and not protected_rows_in_success_denominator(source)
        and source["source_exists"]["m2638_doc"]
        and len(admitted_actions) == 1
        and admitted_actions[0] == "m2805_route_a_post_clearance_corrective_readiness_index_result_audit"
        and gate_matrix_pass
    )
    summary = {
        "protocol_version": "engineering_controller_route_a_post_clearance_corrective_readiness_index_v0",
        "milestone": milestone,
        "result_class": (
            "engineering_controller_route_a_post_clearance_corrective_readiness_index_pass"
            if status_pass
            else "engineering_controller_route_a_post_clearance_corrective_readiness_index_fail"
        ),
        "status_pass": status_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "doc": str(paths["doc"]),
        "evidence_index": str(paths["evidence_index"]),
        "deliverable_readiness_rows": str(paths["deliverable_readiness_rows"]),
        "blocker_matrix": str(paths["blocker_matrix"]),
        "next_action_admission_rows": str(paths["next_action_admission_rows"]),
        "claim_boundary_rows": str(paths["claim_boundary_rows"]),
        "gate_matrix": str(paths["gate_matrix"]),
        "follow_up_manifest": str(source["paths"]["follow_up_manifest"]),
        "follow_up_manifest_exists": source["source_exists"]["follow_up_manifest"],
        "next_blocker": next_blocker,
        "required_artifacts_present": required_artifacts_present,
        "source_artifacts_present": all(source["source_exists"].values()),
        "source_artifacts_reanalyzed_only": True,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "gate_matrix_pass": gate_matrix_pass,
        "gate_matrix_row_count": len(gate_rows),
        "evidence_index_row_count": len(evidence_rows),
        "route_a_deliverable_readiness_row_count": len(deliverable_rows),
        "blocker_matrix_row_count": len(blocker_rows),
        "next_action_admission_row_count": len(next_rows),
        "claim_boundary_row_count": len(claim_rows),
        "admitted_next_action_count": len(admitted_actions),
        "selected_next_action": admitted_actions[0] if admitted_actions else "",
        "m2803_synthesis_pivot_preserved": m2803_pivot_preserved(source),
        "m2801_status_pass": source["m2801_summary"].get("status_pass"),
        "m2801_gate_matrix_pass": source["m2801_summary"].get("gate_matrix_pass"),
        "m2801_triad_execution_row_count": clearance["triad_execution_rows"],
        "m2801_candidate_minus_source_delta_row_count": clearance["source"]["count"],
        "m2801_candidate_minus_m2791_start_delta_row_count": clearance["m2791_start"]["count"],
        "m2801_candidate_minus_source_obstacle_clearance_positive_count": clearance["source"]["positive"],
        "m2801_candidate_minus_source_obstacle_clearance_negative_count": clearance["source"]["negative"],
        "m2801_candidate_minus_source_obstacle_clearance_mean": clearance["source"]["mean"],
        "m2801_candidate_minus_source_obstacle_clearance_median": clearance["source"]["median"],
        "m2801_candidate_minus_m2791_start_obstacle_clearance_positive_count": clearance["m2791_start"]["positive"],
        "m2801_candidate_minus_m2791_start_obstacle_clearance_negative_count": clearance["m2791_start"]["negative"],
        "m2801_candidate_minus_m2791_start_obstacle_clearance_mean": clearance["m2791_start"]["mean"],
        "m2801_candidate_minus_m2791_start_obstacle_clearance_median": clearance["m2791_start"]["median"],
        "m2801_stable_avoidable_candidate_minus_source_obstacle_clearance_negative_count": clearance["stable_source"]["negative"],
        "m2801_stable_avoidable_candidate_minus_m2791_start_obstacle_clearance_negative_count": clearance["stable_m2791_start"]["negative"],
        "m2801_negative_clearance_preserved": negative_clearance_preserved,
        "m2801_stable_avoidable_retention_risk_preserved": stable_risk_preserved,
        "m2801_seed_indices_disjoint_from_previous": source["m2801_summary"].get("fresh_holdout_seed_indices_disjoint_from_previous"),
        "m2801_horizon_longer_than_m2793": source["m2801_summary"].get("horizon_longer_than_m2793"),
        "same_clearance_corrective_repair_loop_closed": True,
        "same_clearance_corrective_update_admitted": False,
        "same_style_triad_panel_admitted": False,
        "hf3_source_dependency_paused": source["source_exists"]["m2638_doc"],
        "protected_mitigation_blocker_preserved": protected_blocker_preserved(source),
        "protected_rows_in_success_denominator": protected_rows_in_success_denominator(source),
        "protected_rows_in_success_denominator_or_actor_input": False,
        "mitigation_reference_rows_guarded": source["m2801_summary"].get("mitigation_reference_rows_guarded"),
        "actor_contract_shape_72_action_3": actor_contract_preserved(source),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": hidden_oracle_actor_input_detected(source),
        "taxonomy_labels_actor_visible": False,
        "scenario_role_labels_actor_visible": False,
        "metric_labels_actor_visible": False,
        "target_labels_actor_visible": False,
        "blocker_labels_actor_visible": False,
        "route_decision_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
    }
    summary.update(FALSE_CLAIM_FLAGS)
    return summary


def evidence_row(
    evidence_id: str,
    source_milestone: str,
    artifact_path: Path,
    evidence_family: str,
    evidence_status: str,
    row_count: int,
    actor_ok: bool,
    hidden: bool,
    clearance: dict[str, Any] | None,
    gap_or_limit: str,
    next_use: str,
) -> dict[str, Any]:
    clearance = clearance or {}
    return {
        "evidence_id": evidence_id,
        "source_milestone": source_milestone,
        "artifact_path": str(artifact_path),
        "evidence_family": evidence_family,
        "evidence_status": evidence_status,
        "row_count": row_count,
        "actor_contract_shape_72_action_3": actor_ok,
        "action_shape_3": actor_ok,
        "hidden_oracle_actor_input_detected": hidden,
        "clearance_positive_count": clearance.get("positive", ""),
        "clearance_negative_count": clearance.get("negative", ""),
        "clearance_mean": clearance.get("mean", ""),
        "clearance_median": clearance.get("median", ""),
        "stable_avoidable_negative_count": clearance.get("negative", "") if "stable" in evidence_id else "",
        "claim_scope": CLAIM_SCOPE,
        "gap_or_limit": gap_or_limit,
        "next_use": next_use,
        "source_exists": artifact_path.exists(),
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def blocker_row(
    blocker_id: str,
    route: str,
    evidence_family: str,
    status: str,
    blocking_count: int,
    required_next_evidence: str,
    admission_to_next_action: str,
    evidence_expansion_value: str,
    forbidden_shortcut: str,
) -> dict[str, Any]:
    return {
        "blocker_id": blocker_id,
        "route": route,
        "evidence_family": evidence_family,
        "current_status": status,
        "blocking_count": blocking_count,
        "required_next_evidence": required_next_evidence,
        "admission_to_next_action": admission_to_next_action,
        "evidence_expansion_value": evidence_expansion_value,
        "forbidden_shortcut": forbidden_shortcut,
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


def gate_row(gate_id: str, family: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "gate_family": family,
        "status_pass": observed == expected,
        "observed": observed,
        "expected": expected,
        "failure_type": "none" if observed == expected else family,
        "claim_boundary": CLAIM_SCOPE,
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    lines = [
        "# M2804 Engineering Controller Route A Post-Clearance Corrective Readiness Index Materialization Preflight",
        "",
        "- status: completed",
        f"- result_class: `{summary['result_class']}`",
        f"- summary: `{summary['summary']}`",
        f"- evidence index: `{summary['evidence_index']}`",
        f"- deliverable readiness rows: `{summary['deliverable_readiness_rows']}`",
        f"- blocker matrix: `{summary['blocker_matrix']}`",
        f"- next-action admission rows: `{summary['next_action_admission_rows']}`",
        f"- claim boundary rows: `{summary['claim_boundary_rows']}`",
        f"- gate matrix: `{summary['gate_matrix']}`",
        f"- follow-up manifest: `{summary['follow_up_manifest']}`",
        f"- next: `{summary['next_blocker']}`",
        "",
        "## Evidence Index",
        "",
        f"- evidence rows: {summary['evidence_index_row_count']}",
        f"- deliverable readiness rows: {summary['route_a_deliverable_readiness_row_count']}",
        f"- blocker rows: {summary['blocker_matrix_row_count']}",
        f"- selected next action: `{summary['selected_next_action']}`",
        f"- source artifacts reanalyzed only: `{str(summary['source_artifacts_reanalyzed_only']).lower()}`",
        "",
        "## M2801/M2802 Clearance Boundary",
        "",
        f"- triad execution rows: {summary['m2801_triad_execution_row_count']}",
        "- candidate-minus-source obstacle clearance: "
        f"{summary['m2801_candidate_minus_source_obstacle_clearance_positive_count']} positive / "
        f"{summary['m2801_candidate_minus_source_obstacle_clearance_negative_count']} negative, "
        f"mean `{summary['m2801_candidate_minus_source_obstacle_clearance_mean']}`",
        "- candidate-minus-M2791-start obstacle clearance: "
        f"{summary['m2801_candidate_minus_m2791_start_obstacle_clearance_positive_count']} positive / "
        f"{summary['m2801_candidate_minus_m2791_start_obstacle_clearance_negative_count']} negative, "
        f"mean `{summary['m2801_candidate_minus_m2791_start_obstacle_clearance_mean']}`",
        "- stable_avoidable source negative rows: "
        f"{summary['m2801_stable_avoidable_candidate_minus_source_obstacle_clearance_negative_count']}",
        "- stable_avoidable M2791-start negative rows: "
        f"{summary['m2801_stable_avoidable_candidate_minus_m2791_start_obstacle_clearance_negative_count']}",
        "- same clearance-localized repair loop closed: "
        f"`{str(summary['same_clearance_corrective_repair_loop_closed']).lower()}`",
        "",
        "## Blockers",
        "",
        f"- protected mitigation blocker preserved: `{str(summary['protected_mitigation_blocker_preserved']).lower()}`",
        f"- protected rows in success denominator: `{str(summary['protected_rows_in_success_denominator']).lower()}`",
        f"- mitigation reference rows guarded: `{str(summary['mitigation_reference_rows_guarded']).lower()}`",
        f"- HF3 source dependency paused: `{str(summary['hf3_source_dependency_paused']).lower()}`",
        "",
        "## Actor Boundary",
        "",
        f"- actor contract P0 72/action 3: `{str(summary['actor_contract_shape_72_action_3']).lower()}`",
        f"- hidden/oracle actor input detected: `{str(summary['hidden_oracle_actor_input_detected']).lower()}`",
        "- taxonomy, scenario-role, metric, target, blocker, route-decision, success/progress, "
        "and verdict labels actor-visible: `false`",
        "",
        "## Claim Boundary",
        "",
        "M2804 is a Route A readiness/admission index over existing artifacts only. It performs no reset, step, rollout, replay, validation, training, PPO, source build, adapter probe, external simulation, ranking, winner selection, promotion, or success-rate computation.",
        "",
        "It does not claim repair success, driver performance, validation readiness, validation result, paper-level evidence, finite-window-vs-GRU, current-sim verdict, high-fidelity validation, full ideal driver completion, or self-ID evidence.",
        "",
    ]
    return "\n".join(lines)


def m2803_pivot_preserved(source: dict[str, Any]) -> bool:
    return "pivot_to_route_a_post_clearance_corrective_readiness_index" in source["m2803_doc_text"]


def actor_contract_preserved(source: dict[str, Any]) -> bool:
    contract = source["m2541_actor_contract"]
    return (
        _int(contract.get("observation_shape")) == P0_OBSERVATION_DIM
        and _int(contract.get("action_shape")) == ACTION_DIM
        and _bool(source["m2801_summary"].get("actor_contract_shape_72_action_3"))
        and _bool(source["m2541_summary"].get("actor_contract_shape_72_action_3"))
    )


def hidden_oracle_actor_input_detected(source: dict[str, Any]) -> bool:
    return (
        _bool(source["m2801_summary"].get("hidden_or_oracle_actor_inputs_required"))
        or _bool(source["m2749_summary"].get("hidden_oracle_actor_input_detected"))
        or not actor_contract_preserved(source)
    )


def actor_visible_labels_detected(source: dict[str, Any]) -> bool:
    return (
        _bool(source["m2801_summary"].get("actor_visible_atlas_or_role_labels_detected"))
        or _bool(source["m2749_summary"].get("taxonomy_labels_actor_visible"))
        or _bool(source["m2749_summary"].get("scenario_role_labels_actor_visible"))
        or _bool(source["m2749_summary"].get("metric_labels_actor_visible"))
        or _bool(source["m2749_summary"].get("target_labels_actor_visible"))
        or _bool(source["m2749_summary"].get("blocker_labels_actor_visible"))
        or _bool(source["m2749_summary"].get("route_decision_labels_actor_visible"))
        or _bool(source["m2749_summary"].get("success_progress_labels_actor_visible"))
        or _bool(source["m2749_summary"].get("verdict_labels_actor_visible"))
    )


def protected_blocker_preserved(source: dict[str, Any]) -> bool:
    return _bool(source["m2667_summary"].get("protected_mitigation_blocker_preserved")) and _bool(
        source["m2749_summary"].get("protected_mitigation_blocker_preserved")
    )


def protected_rows_in_success_denominator(source: dict[str, Any]) -> bool:
    return _bool(source["m2667_summary"].get("protected_rows_in_success_denominator")) or _bool(
        source["m2749_summary"].get("protected_rows_in_success_denominator")
    )


def _metric_stats(rows: list[dict[str, str]], key: str) -> dict[str, Any]:
    values = [_float(row[key]) for row in rows]
    return {
        "count": len(values),
        "positive": sum(1 for value in values if value > 0.0),
        "negative": sum(1 for value in values if value < 0.0),
        "zero": sum(1 for value in values if value == 0.0),
        "mean": mean(values) if values else 0.0,
        "median": median(values) if values else 0.0,
        "min": min(values) if values else 0.0,
        "max": max(values) if values else 0.0,
    }


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "pass"}
    return bool(value)


def _int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def _float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Materialize M2804 Route A post-clearance-corrective readiness index."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args(argv)
    summary = materialize_post_clearance_corrective_readiness_index(
        args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
    )
    print(
        "status_pass={status_pass} result_class={result_class} summary={summary}".format(
            **summary
        )
    )


if __name__ == "__main__":
    main()
