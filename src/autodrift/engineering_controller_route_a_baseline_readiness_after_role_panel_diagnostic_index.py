"""Materialize Route A readiness index after role-panel diagnostics.

This runner reanalyzes existing Route A artifacts only. It does not execute
environments, policies, replay, validation, training, ranking, source builds,
adapter probes, or high-fidelity simulation.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2749-engineering-controller-route-a-baseline-readiness-after-role-panel-"
    "diagnostic-index-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2750-engineering-controller-route-a-baseline-readiness-after-role-panel-"
    "diagnostic-index-materialization-result-audit"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2749_engineering_controller_route_a_baseline_readiness_after_role_panel_diagnostic_index"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2749-engineering-controller-route-a-baseline-readiness-after-role-panel-"
    "diagnostic-index-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2750-engineering-controller-route-a-baseline-readiness-"
    "after-role-panel-diagnostic-index-materialization-result-audit.json"
)

M2748_DOC = Path(
    "docs/m2748-engineering-controller-route-a-source-diverse-failure-taxonomy-"
    "scenario-role-metric-panel-bounded-execution-result-synthesis.md"
)
M2747_DOC = Path(
    "docs/m2747-engineering-controller-route-a-source-diverse-failure-taxonomy-"
    "scenario-role-metric-panel-bounded-execution-result-audit.md"
)
M2746_SUMMARY = Path(
    "runs/m2746_engineering_controller_route_a_source_diverse_failure_taxonomy_"
    "scenario_role_metric_panel_bounded_execution_preflight/summary.json"
)
M2746_CANDIDATE_ROWS = Path(
    "runs/m2746_engineering_controller_route_a_source_diverse_failure_taxonomy_"
    "scenario_role_metric_panel_bounded_execution_preflight/candidate_execution_rows.csv"
)
M2746_GUARDRAIL_CONTEXT_ROWS = Path(
    "runs/m2746_engineering_controller_route_a_source_diverse_failure_taxonomy_"
    "scenario_role_metric_panel_bounded_execution_preflight/guardrail_context_rows.csv"
)
M2746_GATE_MATRIX = Path(
    "runs/m2746_engineering_controller_route_a_source_diverse_failure_taxonomy_"
    "scenario_role_metric_panel_bounded_execution_preflight/gate_matrix.csv"
)
M2743_SUMMARY = Path(
    "runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_"
    "scenario_role_metric_panel/summary.json"
)
M2740_SUMMARY = Path(
    "runs/m2740_engineering_controller_route_a_post_negative_diagnostic_source_diverse_"
    "failure_taxonomy/summary.json"
)
M2667_SUMMARY = Path(
    "runs/m2667_engineering_controller_route_a_engineering_baseline_readiness_index_"
    "after_protected_taxonomy/summary.json"
)
M2667_ARTIFACT_COVERAGE_ROWS = Path(
    "runs/m2667_engineering_controller_route_a_engineering_baseline_readiness_index_"
    "after_protected_taxonomy/artifact_coverage_rows.csv"
)
M2667_KNOWN_FAILURE_ROWS = Path(
    "runs/m2667_engineering_controller_route_a_engineering_baseline_readiness_index_"
    "after_protected_taxonomy/known_failure_boundary_rows.csv"
)
M2541_SUMMARY = Path(
    "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/summary.json"
)
M2541_BASELINE_CHECKPOINTS = Path(
    "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/"
    "baseline_checkpoint_list.csv"
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
    "Route A baseline readiness/admission index after role-panel diagnostic synthesis "
    "only; source-artifact reanalysis with no reset, step, rollout, replay, validation, "
    "training, PPO, source build, adapter probe, external simulation, ranking, winner "
    "selection, promotion, success-rate verdict, repair-success, driver-performance, "
    "paper, finite-window-vs-GRU, current-sim, high-fidelity validation, full ideal "
    "driver, or self-ID claim"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness, validation result, "
    "controller ranking, source-family ranking, task-family ranking, profile ranking, "
    "scenario-role ranking, winner selection, checkpoint promotion, success-rate verdict, "
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
    "source_family_ranking_run": False,
    "task_family_ranking_run": False,
    "profile_ranking_run": False,
    "scenario_role_ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_computed": False,
    "success_rate_metric_recorded": False,
    "success_rate_verdict_field_emitted": False,
    "controller_family_verdict_computed": False,
    "driver_performance_claim_made": False,
    "repair_success_claim_made": False,
    "validation_readiness_claim_made": False,
    "validation_result_claim_made": False,
    "verdict_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "current_response_sufficiency_claim_made": False,
    "level3_self_id_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_readiness_claim_made": False,
    "high_fidelity_validation_claim_made": False,
    "full_ideal_driver_completion_claim_made": False,
    "full_ideal_driver_gate_passed": False,
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
    "diagnostic_success_count",
    "collision_count",
    "offtrack_count",
    "speed_too_low_count",
    "unset_or_completed_count",
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
    "allowed_in_m2749",
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
    ("route_a_readiness_after_role_panel_index_materialized", True, "M2749 readiness index artifacts"),
    ("m2746_role_panel_diagnostic_indexed", True, "M2746 diagnostic row accounting preserved"),
    ("route_a_deliverable_readiness_indexed", True, "Route A near-term deliverable rows"),
    ("m2667_protected_blocker_preserved", True, "M2667 protected mitigation blocker remains visible"),
    ("m2638_hf3_blocker_preserved", True, "M2638 HF3 source dependency blocker remains visible"),
    ("actor_contract_indexed", True, "P0 observation 72/action 3 actor contract indexed"),
    ("follow_up_result_audit_registered", True, "M2750 result-audit manifest"),
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


def materialize_baseline_readiness_after_role_panel_diagnostic_index(
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
    diagnostic_counts = count_m2746_diagnostics(source)
    evidence_rows = build_evidence_index_rows(source, diagnostic_counts)
    deliverable_rows = build_deliverable_readiness_rows(source)
    blocker_rows = build_blocker_matrix_rows(source, diagnostic_counts)
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
        diagnostic_counts,
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
        diagnostic_counts=diagnostic_counts,
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
        diagnostic_counts,
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
        diagnostic_counts=diagnostic_counts,
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
        "m2748_doc": M2748_DOC,
        "m2747_doc": M2747_DOC,
        "m2746_summary": M2746_SUMMARY,
        "m2746_candidate_rows": M2746_CANDIDATE_ROWS,
        "m2746_guardrail_context_rows": M2746_GUARDRAIL_CONTEXT_ROWS,
        "m2746_gate_matrix": M2746_GATE_MATRIX,
        "m2743_summary": M2743_SUMMARY,
        "m2740_summary": M2740_SUMMARY,
        "m2667_summary": M2667_SUMMARY,
        "m2667_artifact_coverage_rows": M2667_ARTIFACT_COVERAGE_ROWS,
        "m2667_known_failure_rows": M2667_KNOWN_FAILURE_ROWS,
        "m2541_summary": M2541_SUMMARY,
        "m2541_baseline_checkpoints": M2541_BASELINE_CHECKPOINTS,
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
        "m2746_summary": read_json(paths["m2746_summary"]),
        "m2746_candidate_rows": _read_csv_rows(paths["m2746_candidate_rows"]),
        "m2746_guardrail_context_rows": _read_csv_rows(paths["m2746_guardrail_context_rows"]),
        "m2746_gate_matrix": _read_csv_rows(paths["m2746_gate_matrix"]),
        "m2743_summary": read_json(paths["m2743_summary"]),
        "m2740_summary": read_json(paths["m2740_summary"]),
        "m2667_summary": read_json(paths["m2667_summary"]),
        "m2667_artifact_coverage_rows": _read_csv_rows(paths["m2667_artifact_coverage_rows"]),
        "m2667_known_failure_rows": _read_csv_rows(paths["m2667_known_failure_rows"]),
        "m2541_summary": read_json(paths["m2541_summary"]),
        "m2541_baseline_checkpoints": _read_csv_rows(paths["m2541_baseline_checkpoints"]),
        "m2541_actor_contract": read_json(paths["m2541_actor_contract"]),
        "m2505_summary": read_json(paths["m2505_summary"]),
        "m2508_summary": read_json(paths["m2508_summary"]),
    }


def build_evidence_index_rows(source: dict[str, Any], counts: dict[str, int]) -> list[dict[str, Any]]:
    actor_ok = actor_contract_preserved(source)
    hidden = hidden_oracle_actor_input_detected(source)
    paths = source["paths"]
    return [
        evidence_row(
            "m2748_role_panel_result_synthesis",
            "m2748",
            paths["m2748_doc"],
            "route_synthesis",
            "pivot_completed",
            1,
            actor_ok,
            hidden,
            counts,
            "closes same-panel role execution branch before readiness indexing",
            "governing pivot for M2749 admission rows",
        ),
        evidence_row(
            "m2747_role_panel_result_audit",
            "m2747",
            paths["m2747_doc"],
            "result_audit",
            "accepted_claim_safe_weak_diagnostic",
            1,
            actor_ok,
            hidden,
            counts,
            "audit accepts completeness but not performance or validation interpretation",
            "source audit for weak diagnostic accounting",
        ),
        evidence_row(
            "m2746_role_panel_diagnostic_execution",
            "m2746",
            paths["m2746_candidate_rows"],
            "closed_loop_diagnostic",
            "weak_offtrack_speed_dominated",
            counts["row_count"],
            actor_ok,
            hidden,
            counts,
            "1 diagnostic success with collision offtrack and speed-too-low dominating",
            "diagnostic context only; not ranking or success-rate verdict",
        ),
        evidence_row(
            "m2743_scenario_role_metric_panel",
            "m2743",
            paths["m2743_summary"],
            "scenario_role_metric_panel",
            "materialized_actor_invisible",
            _int(source["m2743_summary"].get("target_panel_row_count")),
            actor_ok,
            hidden,
            {},
            "role and metric labels remain actor-invisible and non-ranking",
            "readiness deliverable and M2746 lineage",
        ),
        evidence_row(
            "m2740_failure_taxonomy",
            "m2740",
            paths["m2740_summary"],
            "known_failure_taxonomy",
            "materialized_nonranking",
            _int(source["m2740_summary"].get("taxonomy_row_count")),
            actor_ok,
            hidden,
            {},
            "taxonomy rows are context and guardrails not actor input labels",
            "readiness deliverable and blocker context",
        ),
        evidence_row(
            "m2667_route_a_artifact_readiness",
            "m2667",
            paths["m2667_artifact_coverage_rows"],
            "route_a_readiness",
            source["m2667_summary"].get("baseline_readiness_status", "index_ready"),
            len(source["m2667_artifact_coverage_rows"]),
            actor_ok,
            hidden,
            {},
            "readiness package still contains protected blocker boundaries",
            "deliverable coverage input for M2749",
        ),
        evidence_row(
            "m2667_protected_mitigation_blocker",
            "m2667",
            paths["m2667_known_failure_rows"],
            "known_failure_boundary",
            "protected_mitigation_blocker_preserved",
            len(source["m2667_known_failure_rows"]),
            actor_ok,
            hidden,
            {},
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
            {},
            "contract is deployable actuator action only and no hidden/oracle actor input",
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
            {},
            "source-only diagnostic pack is not validation or performance evidence",
            "benchmark/package input for Route A readiness",
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
            {},
            "actor-forward runtime report uses synthetic shape-only observations",
            "runtime deliverable input for Route A readiness",
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
            {},
            "selected-platform HF3 execution remains paused without source dependency",
            "prevents high-fidelity execution admission from M2749",
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
            {},
            "Route A focuses on engineering baseline readiness while paper and HF routes remain separate",
            "governs M2749 deliverable and admission scope",
        ),
    ]


def build_deliverable_readiness_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    coverage = {row["artifact_id"]: row for row in source["m2667_artifact_coverage_rows"]}
    protected_count = _int(source["m2667_summary"].get("known_failure_blocking_boundary_row_count"))
    hf3_blocked = source["source_exists"]["m2638_doc"]
    specs = [
        (
            "baseline_checkpoint_list",
            "baseline checkpoint list",
            "m2541",
            source["paths"]["m2541_baseline_checkpoints"],
            "ready_with_limitations",
            _int(source["m2541_summary"].get("baseline_checkpoint_count")),
            protected_count,
            "baseline checkpoints are admitted as diagnostic inputs only",
            "M2750 audit and any later package/readiness decision",
        ),
        (
            "actor_input_output_contract",
            "actor input/output contract",
            "m2541/m2746",
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
            protected_count,
            "source-only diagnostic scope; not validation readiness",
            "package evidence input with explicit limitations",
        ),
        (
            "known_failure_taxonomy",
            "known failure taxonomy",
            "m2740",
            source["paths"]["m2740_summary"],
            "refreshed_with_role_panel_diagnostic",
            _int(source["m2740_summary"].get("taxonomy_row_count")),
            _int(source["m2740_summary"].get("protected_or_hf3_blocker_taxonomy_row_count")),
            "taxonomy is actor-invisible and non-ranking",
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
            "m2743/m2746",
            source["paths"]["m2743_summary"],
            "refreshed_with_m2746_diagnostic",
            _int(source["m2743_summary"].get("target_panel_row_count")),
            counts_from_guardrail_context(source),
            "role-panel execution remains weak and non-ranking",
            "role/metric context for future non-same-panel evidence route",
        ),
        (
            "protected_mitigation_blocker",
            "protected mitigation blocker",
            "m2667",
            source["paths"]["m2667_known_failure_rows"],
            "active_blocker",
            len(source["m2667_known_failure_rows"]),
            protected_count,
            "protected mitigation remains broad and blocking outside success denominators",
            "blocks validation readiness and performance claims",
        ),
        (
            "hf3_source_dependency",
            "HF3 source dependency",
            "m2638",
            source["paths"]["m2638_doc"],
            "active_blocker" if hf3_blocked else "missing_blocker_doc",
            1 if hf3_blocked else 0,
            1,
            "selected-platform HF3 execution is paused until source dependency is supplied",
            "blocks HF3 execution admission from M2749",
        ),
        (
            "driver_performance_or_validation",
            "driver performance or validation readiness",
            "m2749",
            DEFAULT_DOC_PATH,
            "not_ready",
            0,
            1,
            "M2749 is artifact reanalysis and cannot support validation or performance claims",
            "requires future separately registered validation evidence and claim audit",
        ),
    ]
    rows = []
    for deliverable_id, requirement, milestone, path, status, row_count, blocker_count, limitation, next_use in specs:
        if deliverable_id in coverage:
            row_count = _int(coverage[deliverable_id].get("row_count"))
        rows.append(
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
        )
    return rows


def build_blocker_matrix_rows(source: dict[str, Any], counts: dict[str, int]) -> list[dict[str, Any]]:
    unsuccessful = counts["row_count"] - counts["success_count"]
    protected_count = _int(source["m2667_summary"].get("known_failure_blocking_boundary_row_count"))
    return [
        blocker_row(
            "m2749_blocker_role_panel_weak_diagnostic",
            "Route A",
            "role_panel_diagnostic",
            "active",
            unsuccessful,
            "M2750 audit before any new evidence route; no same-panel repetition",
            "admits_result_audit_only",
            "keeps M2746 weak outcome visible as non-ranking diagnostic evidence",
            "do not reinterpret M2746 as success-rate verdict or performance",
        ),
        blocker_row(
            "m2749_blocker_same_panel_local_search",
            "Route A",
            "local_search_guard",
            "closed_by_m2748_pivot",
            1,
            "new evidence axis or synthesis stop after M2750",
            "not_admitted",
            "prevents another same role-panel public execution loop",
            "do not open another M2746-like same-panel execution from M2749",
        ),
        blocker_row(
            "m2749_blocker_protected_mitigation",
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
            "m2749_blocker_hf3_source_dependency_unavailable",
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
            "m2749_blocker_validation_performance_not_admitted",
            "Route A",
            "claim_boundary",
            "not_admitted",
            1,
            "separately registered validation manifest plus claim audit",
            "not_admitted",
            "prevents readiness rows from becoming performance evidence",
            "do not claim validation readiness or driver performance from M2749",
        ),
        blocker_row(
            "m2749_blocker_actor_contract_guard",
            "Route A",
            "actor_contract",
            "pass",
            0,
            "preserve P0 observation 72 action 3 and no hidden/oracle actor input",
            "guard_pass",
            "keeps all taxonomy/role/metric/verdict labels actor-invisible",
            "do not change actor inputs or deployed action contract",
        ),
    ]


def build_next_action_admission_rows() -> list[dict[str, Any]]:
    return [
        next_action_row(
            "m2750_route_a_readiness_after_role_panel_result_audit",
            "Route A",
            "admitted",
            "M2749 materializes the readiness/admission index and must be audited before another route",
            "M2749 status_pass true and required artifacts present",
            "audit readiness rows and choose synthesis stop or non-same-panel evidence axis",
        ),
        next_action_row(
            "route_a_non_same_panel_execution_surface",
            "Route A",
            "defer_until_m2750_audit",
            "execution may be considered only after M2750 audits evidence boundaries and selects a new axis",
            "M2750 audit and explicit design manifest",
            "keeps future execution separated from M2746 public-panel local search",
        ),
        next_action_row(
            "same_panel_role_execution",
            "Route A",
            "not_admitted",
            "M2748 pivot rejects another same role-panel execution loop",
            "new evidence axis plus result audit and design manifest",
            "prevents overfitting M2746 role-panel rows",
        ),
        next_action_row(
            "same_surface_repair_loop",
            "Route A",
            "not_admitted",
            "M2730 and M2748 already closed direct same-surface repair/execution loops",
            "new source-diverse evidence route and audit",
            "prevents local public-gate repair cycling",
        ),
        next_action_row(
            "hf3_selected_platform_execution",
            "Route C",
            "not_admitted",
            "M2638 source dependency remains unavailable",
            "valid source dependency route or user-supplied source root",
            "keeps high-fidelity execution separate from M2749",
        ),
        next_action_row(
            "controller_ranking_or_winner_selection",
            "Route A",
            "not_admitted",
            "M2749 is readiness indexing and does not compare or rank controllers",
            "future proof plus generalization plus promotion gate",
            "ranking and winner selection remain forbidden",
        ),
        next_action_row(
            "validation_or_driver_performance_claim",
            "Route A",
            "not_admitted",
            "M2749 performs no reset rollout replay validation or performance test",
            "future validation manifest and claim audit",
            "validation and performance claims remain forbidden",
        ),
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": f"m2749_claim_boundary_{claim}",
            "claim_family": claim,
            "allowed_in_m2749": allowed,
            "status_pass": True,
            "evidence_required_before_claim": evidence_required,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim, allowed, evidence_required in CLAIM_CHECKS
    ]


def build_gate_matrix_rows(
    source: dict[str, Any],
    counts: dict[str, int],
    evidence_rows: list[dict[str, Any]],
    deliverable_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    next_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    *,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    hidden = hidden_oracle_actor_input_detected(source)
    protected_rows_inside_success = _bool(source["m2667_summary"].get("protected_rows_in_success_denominator"))
    return [
        gate_row("m2749_gate_source_artifacts_present", "artifact", all(source["source_exists"].values()), True),
        gate_row("m2749_gate_required_artifacts_present", "artifact", required_artifacts_present, True),
        gate_row("m2749_gate_m2748_synthesis_doc_present", "lineage", source["source_exists"]["m2748_doc"], True),
        gate_row("m2749_gate_m2747_audit_doc_present", "lineage", source["source_exists"]["m2747_doc"], True),
        gate_row("m2749_gate_m2746_summary_status_pass", "lineage", source["m2746_summary"].get("status_pass"), True),
        gate_row("m2749_gate_m2746_rows_accounted", "diagnostic_accounting", counts["row_count"], 14),
        gate_row("m2749_gate_m2746_success_count_preserved", "diagnostic_accounting", counts["success_count"], 1),
        gate_row("m2749_gate_m2746_collision_count_preserved", "diagnostic_accounting", counts["collision_count"], 1),
        gate_row("m2749_gate_m2746_offtrack_count_preserved", "diagnostic_accounting", counts["offtrack_count"], 9),
        gate_row("m2749_gate_m2746_speed_too_low_count_preserved", "diagnostic_accounting", counts["speed_too_low_count"], 3),
        gate_row(
            "m2749_gate_m2746_unset_or_completed_count_preserved",
            "diagnostic_accounting",
            counts["unset_or_completed_count"],
            1,
        ),
        gate_row("m2749_gate_m2746_guardrails_not_executed", "diagnostic_accounting", guardrails_executed(source), False),
        gate_row("m2749_gate_same_panel_execution_closed", "process", same_panel_execution_closed(source), True),
        gate_row("m2749_gate_deliverables_indexed", "artifact", len(deliverable_rows), 9),
        gate_row("m2749_gate_evidence_rows_materialized", "artifact", len(evidence_rows), 12),
        gate_row("m2749_gate_blocker_rows_materialized", "artifact", len(blocker_rows), 6),
        gate_row("m2749_gate_actor_contract_72_action_3", "actor_contract", actor_contract_preserved(source), True),
        gate_row("m2749_gate_hidden_oracle_actor_input_absent", "actor_contract", hidden, False),
        gate_row("m2749_gate_actor_visible_labels_absent", "actor_contract", actor_visible_labels_detected(source), False),
        gate_row(
            "m2749_gate_protected_blocker_preserved",
            "known_failure_boundary",
            source["m2667_summary"].get("protected_mitigation_blocker_preserved"),
            True,
        ),
        gate_row(
            "m2749_gate_protected_rows_outside_success_denominator",
            "known_failure_boundary",
            protected_rows_inside_success,
            False,
        ),
        gate_row("m2749_gate_hf3_source_dependency_blocker_present", "hf3_dependency", source["source_exists"]["m2638_doc"], True),
        gate_row("m2749_gate_follow_up_result_audit_registered", "process", source["source_exists"]["follow_up_manifest"], True),
        gate_row(
            "m2749_gate_single_admitted_next_action",
            "process",
            sum(1 for row in next_rows if row["admission_status"] == "admitted"),
            1,
        ),
        gate_row(
            "m2749_gate_same_panel_execution_not_admitted",
            "process",
            any(
                row["candidate_action_id"] == "same_panel_role_execution"
                and row["admission_status"] == "admitted"
                for row in next_rows
            ),
            False,
        ),
        gate_row(
            "m2749_gate_hf3_execution_not_admitted",
            "process",
            any(
                row["candidate_action_id"] == "hf3_selected_platform_execution"
                and row["admission_status"] == "admitted"
                for row in next_rows
            ),
            False,
        ),
        gate_row(
            "m2749_gate_claim_boundary_pass",
            "claim_boundary",
            all(_bool(row["status_pass"]) for row in claim_rows) and not any(FALSE_CLAIM_FLAGS.values()),
            True,
        ),
        gate_row("m2749_gate_no_reset_rollout_training_validation", "claim_boundary", False, False),
        gate_row("m2749_gate_no_source_build_adapter_probe_external_sim", "claim_boundary", False, False),
        gate_row("m2749_gate_no_ranking_promotion_success_rate_performance", "claim_boundary", False, False),
        gate_row("m2749_gate_no_paper_current_sim_hf_full_driver_self_id_claim", "claim_boundary", False, False),
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    diagnostic_counts: dict[str, int],
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
    hidden = hidden_oracle_actor_input_detected(source)
    actor_ok = actor_contract_preserved(source)
    protected_blocker_preserved = _bool(source["m2667_summary"].get("protected_mitigation_blocker_preserved"))
    protected_rows_outside_success = not _bool(source["m2667_summary"].get("protected_rows_in_success_denominator"))
    weak_diagnostic_preserved = diagnostic_counts == {
        "row_count": 14,
        "success_count": 1,
        "collision_count": 1,
        "offtrack_count": 9,
        "speed_too_low_count": 3,
        "unset_or_completed_count": 1,
    }
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    status_pass = (
        required_artifacts_present
        and all(source["source_exists"].values())
        and _bool(source["m2746_summary"].get("status_pass"))
        and _bool(source["m2743_summary"].get("status_pass"))
        and _bool(source["m2740_summary"].get("status_pass"))
        and _bool(source["m2667_summary"].get("status_pass"))
        and _bool(source["m2541_summary"].get("status_pass"))
        and _bool(source["m2505_summary"].get("status_pass"))
        and _bool(source["m2508_summary"].get("status_pass"))
        and weak_diagnostic_preserved
        and same_panel_execution_closed(source)
        and not guardrails_executed(source)
        and actor_ok
        and not hidden
        and not actor_visible_labels_detected(source)
        and protected_blocker_preserved
        and protected_rows_outside_success
        and len(deliverable_rows) == 9
        and len(admitted_actions) == 1
        and gate_matrix_pass
        and not any(FALSE_CLAIM_FLAGS.values())
    )
    return {
        "protocol_version": "engineering_controller_route_a_baseline_readiness_after_role_panel_diagnostic_v0",
        "result_class": "engineering_controller_route_a_baseline_readiness_after_role_panel_diagnostic_index_pass",
        "milestone": milestone,
        "next_blocker": next_blocker,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "evidence_index": str(paths["evidence_index"]),
        "deliverable_readiness_rows": str(paths["deliverable_readiness_rows"]),
        "blocker_matrix": str(paths["blocker_matrix"]),
        "next_action_admission_rows": str(paths["next_action_admission_rows"]),
        "claim_boundary_rows": str(paths["claim_boundary_rows"]),
        "gate_matrix": str(paths["gate_matrix"]),
        "doc": str(paths["doc"]),
        "follow_up_manifest": str(source["paths"]["follow_up_manifest"]),
        "follow_up_manifest_exists": source["source_exists"]["follow_up_manifest"],
        "required_artifacts_present": required_artifacts_present,
        "source_artifacts_present": all(source["source_exists"].values()),
        "source_artifacts_reanalyzed_only": True,
        "evidence_index_row_count": len(evidence_rows),
        "route_a_deliverable_readiness_row_count": len(deliverable_rows),
        "blocker_matrix_row_count": len(blocker_rows),
        "next_action_admission_row_count": len(next_rows),
        "admitted_next_action_count": len(admitted_actions),
        "selected_next_action": admitted_actions[0] if admitted_actions else "",
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "m2746_execution_row_count": diagnostic_counts["row_count"],
        "m2746_candidate_execution_row_count": diagnostic_counts["row_count"],
        "m2746_diagnostic_success_count": diagnostic_counts["success_count"],
        "m2746_diagnostic_collision_count": diagnostic_counts["collision_count"],
        "m2746_offtrack_count": diagnostic_counts["offtrack_count"],
        "m2746_speed_too_low_count": diagnostic_counts["speed_too_low_count"],
        "m2746_unset_or_completed_count": diagnostic_counts["unset_or_completed_count"],
        "m2746_weak_diagnostic_preserved": weak_diagnostic_preserved,
        "m2746_guardrails_executed": guardrails_executed(source),
        "same_panel_execution_closed": same_panel_execution_closed(source),
        "hf3_source_dependency_paused": source["source_exists"]["m2638_doc"],
        "protected_mitigation_blocker_preserved": protected_blocker_preserved,
        "protected_failure_blocking": _bool(source["m2667_summary"].get("protected_failure_blocking")),
        "protected_rows_in_success_denominator": not protected_rows_outside_success,
        "protected_rows_in_success_denominator_or_actor_input": False,
        "protected_rows_in_success_denominator_allowed": False,
        "protected_rows_in_success_denominator_used": False,
        "known_failure_boundary_row_count": len(source["m2667_known_failure_rows"]),
        "actor_contract_shape_72_action_3": actor_ok,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": hidden,
        "taxonomy_labels_actor_visible": False,
        "scenario_role_labels_actor_visible": False,
        "metric_labels_actor_visible": False,
        "target_labels_actor_visible": False,
        "protected_labels_actor_visible": False,
        "blocker_labels_actor_visible": False,
        "route_decision_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "status_pass": status_pass,
        **FALSE_CLAIM_FLAGS,
    }


def count_m2746_diagnostics(source: dict[str, Any]) -> dict[str, int]:
    summary = source["m2746_summary"]
    termination_counts = summary.get("diagnostic_termination_counts", {})
    return {
        "row_count": len(source["m2746_candidate_rows"]),
        "success_count": _int(summary.get("diagnostic_success_count")),
        "collision_count": _int(summary.get("diagnostic_collision_count")),
        "offtrack_count": _int(summary.get("diagnostic_offtrack_count")),
        "speed_too_low_count": _int(summary.get("diagnostic_speed_too_low_count")),
        "unset_or_completed_count": _int(termination_counts.get("unset_or_completed")),
    }


def actor_contract_preserved(source: dict[str, Any]) -> bool:
    return (
        _bool(source["m2746_summary"].get("actor_contract_shape_72_action_3"))
        and _bool(source["m2743_summary"].get("actor_contract_shape_72_action_3"))
        and _bool(source["m2740_summary"].get("actor_contract_shape_72_action_3"))
        and _bool(source["m2667_summary"].get("actor_contract_shape_72_action_3"))
        and _bool(source["m2541_summary"].get("actor_contract_shape_72_action_3"))
        and _int(source["m2541_summary"].get("observation_shape")) == P0_OBSERVATION_DIM
        and _int(source["m2541_summary"].get("action_shape")) == ACTION_DIM
        and _int(source["m2541_actor_contract"].get("observation_shape")) == P0_OBSERVATION_DIM
        and _int(source["m2541_actor_contract"].get("action_shape")) == ACTION_DIM
        and _int(source["m2508_summary"].get("observation_shape")) == P0_OBSERVATION_DIM
        and _int(source["m2508_summary"].get("action_shape")) == ACTION_DIM
    )


def hidden_oracle_actor_input_detected(source: dict[str, Any]) -> bool:
    hidden_keys = (
        "hidden_oracle_actor_input_detected",
        "hidden_or_oracle_actor_input_detected",
        "hidden_or_oracle_actor_inputs_required",
        "hidden_oracle_actor_input_required",
        "hidden_or_oracle_actor_inputs_required",
    )
    summaries = (
        source["m2746_summary"],
        source["m2743_summary"],
        source["m2740_summary"],
        source["m2667_summary"],
        source["m2541_summary"],
        source["m2541_actor_contract"],
        source["m2505_summary"],
        source["m2508_summary"],
    )
    summary_hidden = any(_bool(summary.get(key)) for summary in summaries for key in hidden_keys)
    row_hidden = any(_bool(row.get("hidden_oracle_actor_input_required")) for row in source["m2746_candidate_rows"])
    return summary_hidden or row_hidden


def actor_visible_labels_detected(source: dict[str, Any]) -> bool:
    label_keys = (
        "taxonomy_labels_actor_visible",
        "scenario_role_labels_actor_visible",
        "metric_labels_actor_visible",
        "target_labels_actor_visible",
        "repair_target_labels_actor_visible",
        "protected_labels_actor_visible",
        "blocker_labels_actor_visible",
        "objective_gate_labels_actor_visible",
        "route_labels_actor_visible",
        "route_decision_labels_actor_visible",
        "success_progress_labels_actor_visible",
        "verdict_labels_actor_visible",
    )
    summaries = (
        source["m2746_summary"],
        source["m2743_summary"],
        source["m2740_summary"],
        source["m2667_summary"],
    )
    summary_visible = any(_bool(summary.get(key)) for summary in summaries for key in label_keys)
    row_visible = any(_bool(row.get(key)) for row in source["m2746_candidate_rows"] for key in label_keys)
    return summary_visible or row_visible


def guardrails_executed(source: dict[str, Any]) -> bool:
    summary = source["m2746_summary"]
    guardrail_summary_flags = (
        "guardrail_execution",
        "collision_caution_execution",
        "diagnostic_success_context_execution",
        "negative_context_execution",
        "blocked_same_surface_execution",
        "protected_hf3_execution",
    )
    summary_executed = any(_bool(summary.get(key)) for key in guardrail_summary_flags)
    row_executed = any(_bool(row.get("execution_run")) for row in source["m2746_guardrail_context_rows"])
    return summary_executed or row_executed


def same_panel_execution_closed(source: dict[str, Any]) -> bool:
    return (
        source["source_exists"]["m2748_doc"]
        and source["source_exists"]["m2747_doc"]
        and _bool(source["m2746_summary"].get("status_pass"))
        and _int(source["m2746_summary"].get("candidate_execution_row_count")) == 14
    )


def counts_from_guardrail_context(source: dict[str, Any]) -> int:
    return sum(_int(row.get("row_count")) for row in source["m2746_guardrail_context_rows"])


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2749 Engineering Controller Route A Baseline Readiness After Role-Panel Diagnostic Index Materialization Preflight",
            "",
            "- status: completed" if summary["status_pass"] else "- status: failed",
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
            "## M2746 Diagnostic Boundary",
            "",
            f"- execution rows: {summary['m2746_execution_row_count']}",
            f"- diagnostic success rows: {summary['m2746_diagnostic_success_count']}",
            f"- collision rows: {summary['m2746_diagnostic_collision_count']}",
            f"- off_track rows: {summary['m2746_offtrack_count']}",
            f"- speed_too_low rows: {summary['m2746_speed_too_low_count']}",
            f"- unset_or_completed rows: {summary['m2746_unset_or_completed_count']}",
            f"- weak diagnostic preserved: `{str(summary['m2746_weak_diagnostic_preserved']).lower()}`",
            f"- same-panel execution closed by M2748: `{str(summary['same_panel_execution_closed']).lower()}`",
            "",
            "## Blockers",
            "",
            f"- protected mitigation blocker preserved: `{str(summary['protected_mitigation_blocker_preserved']).lower()}`",
            f"- protected rows in success denominator: `{str(summary['protected_rows_in_success_denominator']).lower()}`",
            f"- HF3 source dependency paused: `{str(summary['hf3_source_dependency_paused']).lower()}`",
            "",
            "## Actor Boundary",
            "",
            f"- actor contract P0 72/action 3: `{str(summary['actor_contract_shape_72_action_3']).lower()}`",
            f"- hidden/oracle actor input detected: `{str(summary['hidden_oracle_actor_input_detected']).lower()}`",
            "- taxonomy, scenario-role, metric, target, protected, blocker, route-decision, success/progress, and verdict labels actor-visible: `false`",
            "",
            "## Claim Boundary",
            "",
            "M2749 is a Route A readiness/admission index over existing artifacts only. It performs no reset, step, rollout, replay, validation, training, PPO, source build, adapter probe, external simulation, ranking, winner selection, promotion, or success-rate computation.",
            "",
            "It does not claim repair success, driver performance, validation readiness, validation result, paper-level evidence, finite-window-vs-GRU, current-sim verdict, high-fidelity validation, full ideal driver completion, or self-ID evidence.",
            "",
        ]
    )


def evidence_row(
    evidence_id: str,
    source_milestone: str,
    artifact_path: Path,
    evidence_family: str,
    evidence_status: str,
    row_count: int,
    actor_contract_ok: bool,
    hidden_oracle_detected: bool,
    counts: dict[str, int],
    gap_or_limit: str,
    next_use: str,
) -> dict[str, Any]:
    return {
        "evidence_id": evidence_id,
        "source_milestone": source_milestone,
        "artifact_path": str(artifact_path),
        "evidence_family": evidence_family,
        "evidence_status": evidence_status,
        "row_count": row_count,
        "actor_contract_shape_72_action_3": actor_contract_ok,
        "action_shape_3": actor_contract_ok,
        "hidden_oracle_actor_input_detected": hidden_oracle_detected,
        "diagnostic_success_count": counts.get("success_count", ""),
        "collision_count": counts.get("collision_count", ""),
        "offtrack_count": counts.get("offtrack_count", ""),
        "speed_too_low_count": counts.get("speed_too_low_count", ""),
        "unset_or_completed_count": counts.get("unset_or_completed_count", ""),
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
    current_status: str,
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
        "current_status": current_status,
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


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args(argv)
    materialize_baseline_readiness_after_role_panel_diagnostic_index(
        args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
    )


if __name__ == "__main__":
    main()
