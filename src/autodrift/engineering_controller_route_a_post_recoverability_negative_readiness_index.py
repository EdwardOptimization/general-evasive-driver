"""Materialize Route A readiness index after negative recoverability results.

M2820 reanalyzes existing artifacts only. It does not execute environments,
policies, replay, validation, training, ranking, source builds, adapter probes,
or high-fidelity simulation.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2820-engineering-controller-route-a-post-recoverability-negative-readiness-index-"
    "materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2821-engineering-controller-route-a-post-recoverability-negative-readiness-index-"
    "materialization-result-audit"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2820_engineering_controller_route_a_post_recoverability_negative_readiness_index"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2820-engineering-controller-route-a-post-recoverability-negative-readiness-index-"
    "materialization-preflight.md"
)
DEFAULT_M2819_DESIGN = Path(
    "docs/m2819-engineering-controller-route-a-post-recoverability-negative-readiness-index-design.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2821-engineering-controller-route-a-post-recoverability-negative-"
    "readiness-index-materialization-result-audit.json"
)

M2818_DOC = Path(
    "docs/m2818-engineering-controller-route-a-post-action-response-recoverability-window-"
    "branch-synthesis.md"
)
M2817_DOC = Path(
    "docs/m2817-engineering-controller-route-a-post-action-response-recoverability-window-"
    "instrumented-bounded-execution-result-audit.md"
)
M2816_DIR = Path(
    "runs/m2816_engineering_controller_route_a_post_action_response_recoverability_window_"
    "instrumented_bounded_execution_preflight"
)
M2816_SUMMARY = M2816_DIR / "summary.json"
M2816_RECOVERABILITY_ROWS = M2816_DIR / "recoverability_window_rows.csv"
M2816_POST_OFFTRACK_ROWS = M2816_DIR / "post_offtrack_action_response_rows.csv"
M2816_GATE_MATRIX = M2816_DIR / "gate_matrix.csv"
M2804_DIR = Path(
    "runs/m2804_engineering_controller_route_a_post_clearance_corrective_readiness_index"
)
M2804_SUMMARY = M2804_DIR / "summary.json"
M2804_EVIDENCE = M2804_DIR / "evidence_index.csv"
M2804_BLOCKERS = M2804_DIR / "blocker_matrix.csv"
M2804_NEXT_ACTIONS = M2804_DIR / "next_action_admission_rows.csv"
M2805_DOC = Path(
    "docs/m2805-engineering-controller-route-a-post-clearance-corrective-readiness-index-"
    "materialization-result-audit.md"
)
M2777_DOC = Path(
    "docs/m2777-engineering-controller-route-a-source-only-action-response-belief-"
    "intervention-branch-synthesis.md"
)
M2643_DOC = Path(
    "docs/m2643-engineering-controller-route-a-baseline-source-only-fresh-generalization-"
    "panel-materialization-result-synthesis.md"
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
    "Route A post-recoverability-negative readiness/admission index only; existing-artifact "
    "reanalysis with no reset, step, policy action, rollout, replay, validation, training, "
    "PPO, repair, source build, adapter probe, external simulation, ranking, winner "
    "selection, promotion, success-rate verdict, repair-success, driver-performance, paper, "
    "finite-window-vs-GRU, current-sim, high-fidelity validation, full ideal driver, or "
    "self-ID claim"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness, validation result, controller "
    "ranking, action-response ranking, recoverability ranking, source-family ranking, "
    "task-family ranking, stress-axis ranking, profile ranking, scenario-role ranking, "
    "winner selection, checkpoint promotion, success-rate verdict, paper evidence, "
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
    "repair_run": False,
    "repair_execution_started": False,
    "repair_training_started": False,
    "training_run": False,
    "ppo_run": False,
    "source_build_run": False,
    "adapter_probe_run": False,
    "backend_started": False,
    "external_high_fidelity_simulation_included": False,
    "external_simulation_run": False,
    "high_fidelity_simulation_run": False,
    "ranking_run": False,
    "recoverability_ranking_run": False,
    "action_response_ranking_run": False,
    "stress_axis_ranking_run": False,
    "source_edge_ranking_run": False,
    "task_family_ranking_run": False,
    "profile_ranking_run": False,
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
    "post_event_available_count",
    "recoverability_window_available_count",
    "recoverability_success_count",
    "diagnostic_success_count",
    "diagnostic_collision_count",
    "diagnostic_offtrack_termination_count",
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
    "allowed_in_m2820",
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
    ("route_a_post_recoverability_negative_readiness_index_materialized", True, "M2820 artifact set"),
    ("m2816_negative_recoverability_indexed", True, "M2816/M2817 negative recoverability diagnostics"),
    ("m2818_pivot_preserved", True, "M2818 pivot to readiness/admission refresh"),
    ("m2804_prior_readiness_blockers_carried_forward", True, "M2804/M2805 readiness blockers"),
    ("negative_clearance_and_stable_avoidable_risk_preserved", True, "M2801/M2802 via M2804"),
    ("protected_guardrails_preserved", True, "M2804 protected mitigation and guardrail blockers"),
    ("hf3_blocker_preserved", True, "M2638 source dependency blocker"),
    ("actor_contract_indexed", True, "P0 observation 72/action 3 actor contract"),
    ("follow_up_result_audit_registered", True, "M2821 result-audit manifest"),
    ("same_recoverability_repair_or_ranking", False, "future separately designed evidence route"),
    ("repair_success", False, "future repair result plus claim audit"),
    ("driver_performance", False, "future validation and claim audit"),
    ("validation_readiness", False, "future validation-readiness route decision"),
    ("validation_result", False, "future validation result"),
    ("controller_ranking", False, "future explicit ranking gate"),
    ("action_response_ranking", False, "future explicit ranking gate"),
    ("recoverability_ranking", False, "future explicit ranking gate"),
    ("source_family_ranking", False, "future explicit ranking gate"),
    ("task_family_ranking", False, "future explicit ranking gate"),
    ("stress_axis_ranking", False, "future explicit ranking gate"),
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


def materialize_post_recoverability_negative_readiness_index(
    output_dir: Path | str,
    *,
    m2819_design: Path | str = DEFAULT_M2819_DESIGN,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    follow_up_path = Path(follow_up_manifest)
    write_json(follow_up_path, build_follow_up_manifest(output_path=output_path, m2819_design=Path(m2819_design)))

    source = load_source_artifacts(m2819_design=Path(m2819_design), follow_up_manifest=follow_up_path)
    recoverability = build_recoverability_accounting(source)
    evidence_rows = build_evidence_index_rows(source, recoverability)
    deliverable_rows = build_deliverable_readiness_rows(source, recoverability)
    blocker_rows = build_blocker_matrix_rows(source, recoverability)
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
        "follow_up_manifest": follow_up_path,
    }

    write_csv_rows(paths["evidence_index"], evidence_rows, fieldnames=EVIDENCE_FIELDNAMES)
    write_csv_rows(paths["deliverable_readiness_rows"], deliverable_rows, fieldnames=DELIVERABLE_FIELDNAMES)
    write_csv_rows(paths["blocker_matrix"], blocker_rows, fieldnames=BLOCKER_FIELDNAMES)
    write_csv_rows(paths["next_action_admission_rows"], next_rows, fieldnames=NEXT_ACTION_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)

    gate_rows = build_gate_matrix_rows(
        source,
        recoverability,
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
        recoverability=recoverability,
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
        recoverability,
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
        recoverability=recoverability,
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


def load_source_artifacts(*, m2819_design: Path, follow_up_manifest: Path) -> dict[str, Any]:
    paths = {
        "m2819_design": m2819_design,
        "m2818_doc": M2818_DOC,
        "m2817_doc": M2817_DOC,
        "m2816_summary": M2816_SUMMARY,
        "m2816_recoverability_rows": M2816_RECOVERABILITY_ROWS,
        "m2816_post_offtrack_rows": M2816_POST_OFFTRACK_ROWS,
        "m2816_gate_matrix": M2816_GATE_MATRIX,
        "m2804_summary": M2804_SUMMARY,
        "m2804_evidence": M2804_EVIDENCE,
        "m2804_blockers": M2804_BLOCKERS,
        "m2804_next_actions": M2804_NEXT_ACTIONS,
        "m2805_doc": M2805_DOC,
        "m2777_doc": M2777_DOC,
        "m2643_doc": M2643_DOC,
        "m2541_summary": M2541_SUMMARY,
        "m2541_actor_contract": M2541_ACTOR_CONTRACT,
        "m2505_summary": M2505_SUMMARY,
        "m2508_summary": M2508_SUMMARY,
        "m2638_doc": M2638_DOC,
        "route_plan": ROUTE_PLAN,
        "follow_up_manifest": follow_up_manifest,
    }
    return {
        "paths": paths,
        "source_exists": {name: path.exists() for name, path in paths.items()},
        "m2819_design_text": paths["m2819_design"].read_text(encoding="utf-8"),
        "m2818_doc_text": paths["m2818_doc"].read_text(encoding="utf-8"),
        "m2817_doc_text": paths["m2817_doc"].read_text(encoding="utf-8"),
        "m2805_doc_text": paths["m2805_doc"].read_text(encoding="utf-8"),
        "m2777_doc_text": paths["m2777_doc"].read_text(encoding="utf-8"),
        "m2643_doc_text": paths["m2643_doc"].read_text(encoding="utf-8"),
        "m2638_doc_text": paths["m2638_doc"].read_text(encoding="utf-8"),
        "route_plan_text": paths["route_plan"].read_text(encoding="utf-8"),
        "m2816_summary": read_json(paths["m2816_summary"]),
        "m2816_recoverability_rows": _read_csv_rows(paths["m2816_recoverability_rows"]),
        "m2816_post_offtrack_rows": _read_csv_rows(paths["m2816_post_offtrack_rows"]),
        "m2816_gate_matrix": _read_csv_rows(paths["m2816_gate_matrix"]),
        "m2804_summary": read_json(paths["m2804_summary"]),
        "m2804_evidence": _read_csv_rows(paths["m2804_evidence"]),
        "m2804_blockers": _read_csv_rows(paths["m2804_blockers"]),
        "m2804_next_actions": _read_csv_rows(paths["m2804_next_actions"]),
        "m2541_summary": read_json(paths["m2541_summary"]),
        "m2541_actor_contract": read_json(paths["m2541_actor_contract"]),
        "m2505_summary": read_json(paths["m2505_summary"]),
        "m2508_summary": read_json(paths["m2508_summary"]),
        "follow_up_manifest": read_json(paths["follow_up_manifest"]),
    }


def build_recoverability_accounting(source: dict[str, Any]) -> dict[str, Any]:
    rows = source["m2816_recoverability_rows"]
    post_rows = source["m2816_post_offtrack_rows"]
    gate_rows = source["m2816_gate_matrix"]
    post_event_rows = [
        row
        for row in rows
        if _bool(row.get("post_event_speed_mps_available"))
        or _bool(row.get("post_event_yaw_rate_abs_available"))
        or _bool(row.get("post_event_offtrack_overshoot_available"))
    ]
    return {
        "fixed_row_count": _int(source["m2816_summary"].get("mechanism_row_count")),
        "accounted_count": _int(source["m2816_summary"].get("accounted_count")),
        "episode_count": _int(source["m2816_summary"].get("episode_count")),
        "execution_failure_count": sum(1 for row in rows if _bool(row.get("execution_failure"))),
        "diagnostic_success_count": sum(1 for row in rows if _bool(row.get("success"))),
        "diagnostic_collision_count": sum(1 for row in rows if _bool(row.get("collision"))),
        "diagnostic_offtrack_termination_count": sum(
            1 for row in rows if str(row.get("termination_reason", "")).strip() == "off_track"
        ),
        "post_event_available_count": len(post_event_rows),
        "recoverability_window_row_count": len(rows),
        "recoverability_available_count": sum(
            1 for row in rows if _bool(row.get("recoverability_window_success_available"))
        ),
        "recoverability_success_count": sum(1 for row in rows if _bool(row.get("recoverability_window_success"))),
        "post_offtrack_action_response_row_count": len(post_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": all(_bool(row.get("status_pass")) for row in gate_rows),
        "guardrail_context_row_count": _int(source["m2816_summary"].get("guardrail_context_row_count")),
        "actor_contract_guard_row_count": _int(source["m2816_summary"].get("actor_contract_guard_row_count")),
        "claim_boundary_row_count": _int(source["m2816_summary"].get("claim_boundary_row_count")),
    }


def build_evidence_index_rows(source: dict[str, Any], recoverability: dict[str, Any]) -> list[dict[str, Any]]:
    actor_ok = actor_contract_preserved(source)
    hidden = hidden_oracle_actor_input_detected(source)
    paths = source["paths"]
    recovery_counts = {
        "post_event_available_count": recoverability["post_event_available_count"],
        "recoverability_window_available_count": recoverability["recoverability_available_count"],
        "recoverability_success_count": recoverability["recoverability_success_count"],
        "diagnostic_success_count": recoverability["diagnostic_success_count"],
        "diagnostic_collision_count": recoverability["diagnostic_collision_count"],
        "diagnostic_offtrack_termination_count": recoverability["diagnostic_offtrack_termination_count"],
    }
    specs = [
        (
            "m2819_post_recoverability_negative_index_design",
            "m2819",
            paths["m2819_design"],
            "design",
            "admit_m2820_existing_artifact_materialization",
            1,
            {},
            "design admits M2820 only as no-execution readiness/admission refresh",
            "source contract for this materialization",
        ),
        (
            "m2818_recoverability_window_branch_synthesis",
            "m2818",
            paths["m2818_doc"],
            "branch_synthesis",
            "pivot_to_post_recoverability_negative_readiness_index",
            1,
            recovery_counts,
            "branch complete but negative for direct recoverability interpretation",
            "governing pivot for M2820",
        ),
        (
            "m2817_recoverability_window_result_audit",
            "m2817",
            paths["m2817_doc"],
            "result_audit",
            "accepted_claim_safe_negative_recoverability_diagnostic",
            1,
            recovery_counts,
            "audit accepts M2816 artifacts but rejects repair validation performance claims",
            "claim boundary for M2820",
        ),
        (
            "m2816_recoverability_window_summary",
            "m2816",
            paths["m2816_summary"],
            "bounded_execution_summary",
            "negative_recoverability_window_diagnostic",
            recoverability["episode_count"],
            recovery_counts,
            "12 bounded diagnostic executions with 0 execution failures",
            "primary post-recoverability negative input",
        ),
        (
            "m2816_recoverability_window_rows",
            "m2816",
            paths["m2816_recoverability_rows"],
            "recoverability_window_rows",
            "zero_available_zero_success",
            recoverability["recoverability_window_row_count"],
            recovery_counts,
            "7 post-event traces but 0 recoverability-window availability and 0 success",
            "active blocker for direct recoverability interpretation",
        ),
        (
            "m2816_post_offtrack_action_response_rows",
            "m2816",
            paths["m2816_post_offtrack_rows"],
            "post_offtrack_action_response_rows",
            "diagnostic_non_ranking",
            recoverability["post_offtrack_action_response_row_count"],
            recovery_counts,
            "post-event action-response rows are diagnostic and actor-invisible",
            "mechanism context without ranking",
        ),
        (
            "m2816_gate_matrix",
            "m2816",
            paths["m2816_gate_matrix"],
            "gate_matrix",
            "all_pass_claim_boundary",
            recoverability["gate_matrix_row_count"],
            recovery_counts,
            "M2816 gates pass without admitting verdict claims",
            "gate lineage input",
        ),
        (
            "m2804_prior_readiness_index",
            "m2804",
            paths["m2804_summary"],
            "prior_readiness_index",
            "stale_after_m2816_m2817_m2818",
            _int(source["m2804_summary"].get("route_a_deliverable_readiness_row_count")),
            {},
            "prior readiness index predates negative recoverability branch",
            "baseline to refresh and carry forward",
        ),
        (
            "m2804_prior_evidence_index",
            "m2804",
            paths["m2804_evidence"],
            "prior_evidence_index",
            "carried_forward",
            len(source["m2804_evidence"]),
            {},
            "prior negative clearance stable_avoidable protected HF3 evidence remains active",
            "source for carried-forward blockers",
        ),
        (
            "m2804_prior_blocker_matrix",
            "m2804",
            paths["m2804_blockers"],
            "prior_blocker_matrix",
            "carried_forward",
            len(source["m2804_blockers"]),
            {},
            "M2804 blockers remain visible after recoverability branch",
            "source for M2820 blocker rows",
        ),
        (
            "m2804_prior_next_action_admission",
            "m2804",
            paths["m2804_next_actions"],
            "prior_next_action_admission",
            "superseded_by_post_recoverability_refresh",
            len(source["m2804_next_actions"]),
            {},
            "older next-action map requires M2820/M2821 audit refresh",
            "lineage only",
        ),
        (
            "m2805_prior_readiness_result_audit",
            "m2805",
            paths["m2805_doc"],
            "result_audit",
            "accepted_prior_readiness_index",
            1,
            {},
            "M2805 accepted M2804 before M2816/M2817/M2818 existed",
            "claim boundary and lineage input",
        ),
        (
            "m2777_action_response_belief_synthesis",
            "m2777",
            paths["m2777_doc"],
            "source_only_action_response_belief_synthesis",
            "lineage_context_only",
            1,
            {},
            "source-only action-response belief evidence remains diagnostic context",
            "lineage context without ranking",
        ),
        (
            "m2643_source_only_generalization_synthesis",
            "m2643",
            paths["m2643_doc"],
            "source_only_generalization_synthesis",
            "lineage_context_only",
            1,
            {},
            "source-only generalization evidence remains separate from validation verdicts",
            "lineage context without performance claims",
        ),
        (
            "m2541_baseline_actor_contract",
            "m2541",
            paths["m2541_actor_contract"],
            "actor_contract",
            "p0_observation_72_action_3_no_oracle",
            1,
            {},
            "contract is deployable actor input/output only",
            "actor contract guard",
        ),
        (
            "m2505_public_benchmark_pack",
            "m2505",
            paths["m2505_summary"],
            "public_benchmark_pack",
            "source_only_diagnostic_pack_ready",
            _int(source["m2505_summary"].get("artifact_manifest_rows")),
            {},
            "source-only diagnostic pack is not validation or performance evidence",
            "package input with limitations",
        ),
        (
            "m2508_runtime_inference_cost_report",
            "m2508",
            paths["m2508_summary"],
            "runtime_inference_cost",
            "actor_forward_cost_measured",
            _int(source["m2508_summary"].get("measurement_row_count")),
            {},
            "actor-forward runtime report uses synthetic shape-only observations",
            "runtime deliverable input",
        ),
        (
            "m2638_hf3_source_dependency_blocker",
            "m2638",
            paths["m2638_doc"],
            "hf3_source_dependency",
            "blocked_until_user_supplied_source",
            1,
            {},
            "selected-platform HF3 execution remains paused without source dependency",
            "prevents high-fidelity execution admission",
        ),
        (
            "post_m2470_route_plan",
            "post-m2470",
            paths["route_plan"],
            "route_plan",
            "route_a_governing_context",
            1,
            {},
            "Route A readiness must stay separate from Route B paper and Route C HF validation",
            "governs M2820 admission scope",
        ),
    ]
    return [
        evidence_row(
            evidence_id,
            source_milestone,
            artifact_path,
            evidence_family,
            evidence_status,
            row_count,
            actor_ok,
            hidden,
            counts,
            gap_or_limit,
            next_use,
        )
        for (
            evidence_id,
            source_milestone,
            artifact_path,
            evidence_family,
            evidence_status,
            row_count,
            counts,
            gap_or_limit,
            next_use,
        ) in specs
    ]


def build_deliverable_readiness_rows(
    source: dict[str, Any], recoverability: dict[str, Any]
) -> list[dict[str, Any]]:
    specs = [
        (
            "baseline_checkpoint_list",
            "baseline checkpoint list",
            "m2541/m2804",
            source["paths"]["m2541_summary"],
            "ready_with_negative_recoverability_limitations",
            _int(source["m2541_summary"].get("baseline_checkpoint_count")),
            recoverability["diagnostic_collision_count"] + recoverability["diagnostic_offtrack_termination_count"],
            "baseline checkpoints are lineage inputs only; no promotion or winner selection",
            "M2821 audit and any later package/readiness decision",
        ),
        (
            "actor_input_output_contract",
            "actor input/output contract",
            "m2541/m2816",
            source["paths"]["m2541_actor_contract"],
            "ready_contract_guarded",
            1,
            0,
            "P0 observation 72 action 3; hidden/oracle and diagnostic labels forbidden",
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
            "m2804/m2818",
            source["paths"]["m2804_summary"],
            "needs_refresh_after_negative_recoverability",
            _int(source["m2804_summary"].get("blocker_matrix_row_count")),
            5,
            "M2816/M2817 add active recoverability-window collision/offtrack blockers",
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
            "m2804/m2816",
            source["paths"]["m2816_recoverability_rows"],
            "refreshed_with_recoverability_negative_diagnostic",
            recoverability["recoverability_window_row_count"],
            recoverability["diagnostic_collision_count"] + recoverability["diagnostic_offtrack_termination_count"],
            "stress labels remain actor-invisible and non-ranking",
            "role/metric context for future non-same-surface route",
        ),
        (
            "prior_clearance_corrective_readiness_index",
            "prior post-clearance readiness/admission index",
            "m2804/m2805",
            source["paths"]["m2804_summary"],
            "carried_forward_but_stale",
            _int(source["m2804_summary"].get("evidence_index_row_count")),
            _int(source["m2804_summary"].get("blocker_matrix_row_count")),
            "M2804/M2805 remains valid lineage but predates M2816/M2817/M2818",
            "input to M2821 audit and continuation selection",
        ),
        (
            "post_recoverability_negative_result",
            "post-recoverability negative diagnostic result",
            "m2816/m2817/m2818",
            source["paths"]["m2816_summary"],
            "active_blocker",
            recoverability["recoverability_window_row_count"],
            recoverability["recoverability_window_row_count"] - recoverability["recoverability_success_count"],
            "0 recoverability-window availability and 0 recoverability success",
            "blocks same recoverability repair/ranking and validation claims",
        ),
        (
            "action_response_recoverability_diagnostic_rows",
            "post-offtrack action-response diagnostic rows",
            "m2816",
            source["paths"]["m2816_post_offtrack_rows"],
            "ready_diagnostic_non_ranking",
            recoverability["post_offtrack_action_response_row_count"],
            recoverability["diagnostic_collision_count"] + recoverability["diagnostic_offtrack_termination_count"],
            "post-event rows are diagnostic only and cannot support success-rate verdicts",
            "mechanism context for future bounded design",
        ),
        (
            "protected_mitigation_and_guardrail_boundary",
            "protected mitigation and guardrail boundary",
            "m2804/m2816",
            source["paths"]["m2804_blockers"],
            "active_blocker",
            recoverability["guardrail_context_row_count"],
            1,
            "protected and guardrail rows remain outside ordinary success denominators",
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
            "blocks HF3 execution admission from M2820",
        ),
        (
            "driver_performance_or_validation",
            "driver performance or validation readiness",
            "m2820",
            DEFAULT_DOC_PATH,
            "not_ready",
            0,
            1,
            "M2820 is artifact reanalysis and cannot support validation or performance claims",
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


def build_blocker_matrix_rows(source: dict[str, Any], recoverability: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        blocker_row(
            "m2820_blocker_recoverability_window_absent",
            "Route A",
            "recoverability_window_rows",
            "active",
            recoverability["recoverability_window_row_count"],
            "M2821 audit before any new evidence route; no same recoverability repair/ranking",
            "admits_result_audit_only",
            "keeps 0 recoverability-window availability and 0 success visible",
            "do not reinterpret post-event traces as recoverability proof",
        ),
        blocker_row(
            "m2820_blocker_diagnostic_collision_and_offtrack",
            "Route A",
            "diagnostic_outcomes",
            "active",
            recoverability["diagnostic_collision_count"] + recoverability["diagnostic_offtrack_termination_count"],
            "future route must handle collision and offtrack terminations before validation claims",
            "blocks_validation_performance_claims",
            "keeps 1 collision and 5 offtrack terminations first-class",
            "do not hide collision or offtrack terminations behind aggregate success rows",
        ),
        blocker_row(
            "m2820_blocker_same_recoverability_local_search",
            "Route A",
            "local_search_guard",
            "closed_by_m2818_pivot",
            1,
            "M2821 audit plus new non-same-surface design or explicit stop",
            "not_admitted",
            "prevents another direct repair or ranking loop over the same 12 rows",
            "do not open another same recoverability-window repair from M2820",
        ),
        blocker_row(
            "m2820_blocker_negative_clearance_and_stable_avoidable_retention",
            "Route A",
            "prior_readiness_blockers",
            "active",
            _int(source["m2804_summary"].get("m2801_candidate_minus_source_obstacle_clearance_negative_count"))
            + _int(source["m2804_summary"].get("m2801_candidate_minus_m2791_start_obstacle_clearance_negative_count"))
            + _int(source["m2804_summary"].get("m2801_stable_avoidable_candidate_minus_source_obstacle_clearance_negative_count"))
            + _int(source["m2804_summary"].get("m2801_stable_avoidable_candidate_minus_m2791_start_obstacle_clearance_negative_count")),
            "future route must preserve negative clearance and stable_avoidable before promotion or validation",
            "blocks_promotion_validation_claims",
            "carries M2804/M2805 blockers forward after M2816/M2817",
            "do not weaken prior negative clearance or stable_avoidable retention rows",
        ),
        blocker_row(
            "m2820_blocker_protected_mitigation_and_guardrails",
            "Route A",
            "known_failure_boundary",
            "active",
            recoverability["guardrail_context_row_count"],
            "future evidence must keep protected and guardrail rows outside ordinary success denominators",
            "blocks_validation_performance_claims",
            "preserves protected mitigation and guardrail denominator boundary",
            "do not weaken or hide protected mitigation or guardrail rows",
        ),
        blocker_row(
            "m2820_blocker_hf3_source_dependency_unavailable",
            "Route C",
            "hf3_dependency",
            "paused_by_m2638",
            1,
            "valid user-supplied source root or dependency acquisition route",
            "not_admitted",
            "keeps high-fidelity route explicit without fetching building probing or running source",
            "do not fetch install build probe or run external simulator",
        ),
        blocker_row(
            "m2820_blocker_validation_performance_not_admitted",
            "Route A",
            "claim_boundary",
            "not_admitted",
            1,
            "separately registered validation manifest plus claim audit",
            "not_admitted",
            "prevents readiness rows from becoming performance evidence",
            "do not claim validation readiness or driver performance from M2820",
        ),
        blocker_row(
            "m2820_blocker_actor_contract_guard",
            "Route A",
            "actor_contract",
            "pass",
            0,
            "preserve P0 observation 72 action 3 and no hidden/oracle actor input",
            "guard_pass",
            "keeps all recoverability action-response source-family task-family blocker route verdict labels actor-invisible",
            "do not change actor inputs or deployed action contract",
        ),
    ]


def build_next_action_admission_rows() -> list[dict[str, Any]]:
    return [
        next_action_row(
            "m2821_post_recoverability_negative_readiness_index_result_audit",
            "Route A",
            "admitted",
            "M2820 materializes the refreshed post-recoverability readiness/admission index and must be audited",
            "M2820 status_pass true and required artifacts present",
            "audit refreshed readiness rows before selecting stop package or new evidence route",
        ),
        next_action_row(
            "same_recoverability_window_repair_or_ranking",
            "Route A",
            "not_admitted",
            "M2818 rejects another direct same-surface recoverability repair or ranking loop",
            "new evidence axis plus M2821 audit and explicit design manifest",
            "prevents overfitting the same 12 recoverability rows",
        ),
        next_action_row(
            "route_a_package_with_limitations",
            "Route A",
            "defer_until_m2821_audit",
            "packaging may be considered only after M2821 audits evidence boundaries",
            "M2821 audit and explicit package/synthesis decision",
            "keeps package claims separated from driver-performance claims",
        ),
        next_action_row(
            "route_a_non_same_surface_evidence_route",
            "Route A",
            "defer_until_m2821_audit_and_design",
            "new execution may be considered only after audit selects a non-same evidence axis",
            "M2821 audit and explicit design manifest",
            "keeps future execution separated from direct recoverability local search",
        ),
        next_action_row(
            "route_b_controller_family_comparison",
            "Route B",
            "defer_to_separate_pre_registered_design",
            "paper/self-ID comparison is a separate route from Route A readiness indexing",
            "separate Route B design manifest and fair comparison matrix",
            "keeps self-ID claims out of M2820",
        ),
        next_action_row(
            "route_c_hf3_selected_platform_execution",
            "Route C",
            "not_admitted_until_source_dependency_supplied",
            "M2638 source dependency remains unavailable",
            "valid source dependency route or user-supplied source root",
            "keeps high-fidelity execution separate from M2820",
        ),
        next_action_row(
            "validation_or_driver_performance_claim",
            "Route A",
            "not_admitted",
            "M2820 performs no reset rollout replay validation or performance test",
            "future validation manifest and claim audit",
            "validation and performance claims remain forbidden",
        ),
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": f"m2820_claim_boundary_{claim}",
            "claim_family": claim,
            "allowed_in_m2820": allowed,
            "status_pass": True,
            "evidence_required_before_claim": evidence_required,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim, allowed, evidence_required in CLAIM_CHECKS
    ]


def build_gate_matrix_rows(
    source: dict[str, Any],
    recoverability: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
    deliverable_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    next_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    *,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    return [
        gate_row("m2820_gate_source_artifacts_present", "artifact", all(source["source_exists"].values()), True),
        gate_row("m2820_gate_required_artifacts_present", "artifact", required_artifacts_present, True),
        gate_row("m2820_gate_m2819_design_admission_preserved", "lineage", m2819_admission_preserved(source), True),
        gate_row("m2820_gate_m2818_pivot_preserved", "lineage", m2818_pivot_preserved(source), True),
        gate_row("m2820_gate_m2817_audit_doc_present", "lineage", source["source_exists"]["m2817_doc"], True),
        gate_row("m2820_gate_m2816_status_pass", "lineage", source["m2816_summary"].get("status_pass"), True),
        gate_row("m2820_gate_m2816_gate_matrix_pass", "lineage", source["m2816_summary"].get("gate_matrix_pass"), True),
        gate_row("m2820_gate_m2816_gate_rows_all_pass", "lineage", recoverability["gate_matrix_pass"], True),
        gate_row("m2820_gate_m2816_fixed_rows_preserved", "diagnostic_accounting", recoverability["fixed_row_count"], 12),
        gate_row("m2820_gate_m2816_accounted_rows_preserved", "diagnostic_accounting", recoverability["accounted_count"], 12),
        gate_row("m2820_gate_m2816_episode_rows_preserved", "diagnostic_accounting", recoverability["episode_count"], 12),
        gate_row("m2820_gate_m2816_execution_failure_count", "diagnostic_accounting", recoverability["execution_failure_count"], 0),
        gate_row("m2820_gate_m2816_diagnostic_success_count", "diagnostic_accounting", recoverability["diagnostic_success_count"], 6),
        gate_row("m2820_gate_m2816_diagnostic_collision_count", "diagnostic_accounting", recoverability["diagnostic_collision_count"], 1),
        gate_row(
            "m2820_gate_m2816_diagnostic_offtrack_termination_count",
            "diagnostic_accounting",
            recoverability["diagnostic_offtrack_termination_count"],
            5,
        ),
        gate_row(
            "m2820_gate_m2816_post_event_available_count",
            "diagnostic_accounting",
            recoverability["post_event_available_count"],
            7,
        ),
        gate_row(
            "m2820_gate_m2816_recoverability_rows_preserved",
            "diagnostic_accounting",
            recoverability["recoverability_window_row_count"],
            12,
        ),
        gate_row(
            "m2820_gate_m2816_recoverability_available_count",
            "diagnostic_accounting",
            recoverability["recoverability_available_count"],
            0,
        ),
        gate_row(
            "m2820_gate_m2816_recoverability_success_count",
            "diagnostic_accounting",
            recoverability["recoverability_success_count"],
            0,
        ),
        gate_row("m2820_gate_m2804_status_pass", "lineage", source["m2804_summary"].get("status_pass"), True),
        gate_row(
            "m2820_gate_m2804_negative_clearance_preserved",
            "prior_readiness",
            source["m2804_summary"].get("m2801_negative_clearance_preserved"),
            True,
        ),
        gate_row(
            "m2820_gate_m2804_stable_avoidable_risk_preserved",
            "prior_readiness",
            source["m2804_summary"].get("m2801_stable_avoidable_retention_risk_preserved"),
            True,
        ),
        gate_row(
            "m2820_gate_protected_rows_outside_success_denominator",
            "known_failure_boundary",
            protected_rows_in_success_denominator(source),
            False,
        ),
        gate_row("m2820_gate_hf3_source_dependency_blocker_present", "hf3_dependency", source["source_exists"]["m2638_doc"], True),
        gate_row("m2820_gate_actor_contract_72_action_3", "actor_contract", actor_contract_preserved(source), True),
        gate_row("m2820_gate_hidden_oracle_actor_input_absent", "actor_contract", hidden_oracle_actor_input_detected(source), False),
        gate_row("m2820_gate_actor_visible_labels_absent", "actor_contract", actor_visible_labels_detected(source), False),
        gate_row("m2820_gate_evidence_rows_materialized", "artifact", len(evidence_rows), 19),
        gate_row("m2820_gate_deliverables_indexed", "artifact", len(deliverable_rows), 12),
        gate_row("m2820_gate_blocker_rows_materialized", "artifact", len(blocker_rows), 8),
        gate_row("m2820_gate_claim_rows_materialized", "artifact", len(claim_rows), len(CLAIM_CHECKS)),
        gate_row("m2820_gate_follow_up_result_audit_registered", "process", source["source_exists"]["follow_up_manifest"], True),
        gate_row(
            "m2820_gate_follow_up_manifest_id",
            "process",
            source["follow_up_manifest"].get("id"),
            DEFAULT_NEXT_BLOCKER,
        ),
        gate_row(
            "m2820_gate_single_admitted_next_action",
            "process",
            sum(1 for row in next_rows if row["admission_status"] == "admitted"),
            1,
        ),
        gate_row(
            "m2820_gate_selected_next_action",
            "process",
            next((row["candidate_action_id"] for row in next_rows if row["admission_status"] == "admitted"), ""),
            "m2821_post_recoverability_negative_readiness_index_result_audit",
        ),
        gate_row(
            "m2820_gate_same_recoverability_repair_ranking_not_admitted",
            "process",
            any(
                row["candidate_action_id"] == "same_recoverability_window_repair_or_ranking"
                and row["admission_status"] == "admitted"
                for row in next_rows
            ),
            False,
        ),
        gate_row(
            "m2820_gate_hf3_execution_not_admitted",
            "process",
            any(
                row["candidate_action_id"] == "route_c_hf3_selected_platform_execution"
                and row["admission_status"] == "admitted"
                for row in next_rows
            ),
            False,
        ),
        gate_row(
            "m2820_gate_claim_boundary_pass",
            "claim_boundary",
            all(_bool(row["status_pass"]) for row in claim_rows) and not any(FALSE_CLAIM_FLAGS.values()),
            True,
        ),
        gate_row("m2820_gate_no_reset_rollout_training_validation", "claim_boundary", False, False),
        gate_row("m2820_gate_no_source_build_adapter_probe_external_sim", "claim_boundary", False, False),
        gate_row("m2820_gate_no_ranking_promotion_success_rate_performance", "claim_boundary", False, False),
        gate_row("m2820_gate_no_paper_current_sim_hf_full_driver_self_id_claim", "claim_boundary", False, False),
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    recoverability: dict[str, Any],
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
    negative_recoverability_preserved = (
        recoverability["post_event_available_count"] == 7
        and recoverability["recoverability_available_count"] == 0
        and recoverability["recoverability_success_count"] == 0
        and recoverability["diagnostic_collision_count"] == 1
        and recoverability["diagnostic_offtrack_termination_count"] == 5
    )
    prior_readiness_preserved = (
        _bool(source["m2804_summary"].get("m2801_negative_clearance_preserved"))
        and _bool(source["m2804_summary"].get("m2801_stable_avoidable_retention_risk_preserved"))
    )
    status_pass = (
        required_artifacts_present
        and all(source["source_exists"].values())
        and _bool(source["m2816_summary"].get("status_pass"))
        and _bool(source["m2816_summary"].get("gate_matrix_pass"))
        and recoverability["gate_matrix_pass"]
        and _bool(source["m2804_summary"].get("status_pass"))
        and _bool(source["m2541_summary"].get("status_pass"))
        and _bool(source["m2505_summary"].get("status_pass"))
        and _bool(source["m2508_summary"].get("status_pass"))
        and m2819_admission_preserved(source)
        and m2818_pivot_preserved(source)
        and negative_recoverability_preserved
        and prior_readiness_preserved
        and actor_contract_preserved(source)
        and not hidden_oracle_actor_input_detected(source)
        and not actor_visible_labels_detected(source)
        and not protected_rows_in_success_denominator(source)
        and source["source_exists"]["m2638_doc"]
        and len(admitted_actions) == 1
        and admitted_actions[0] == "m2821_post_recoverability_negative_readiness_index_result_audit"
        and gate_matrix_pass
    )
    summary = {
        "protocol_version": "engineering_controller_route_a_post_recoverability_negative_readiness_index_v0",
        "milestone": milestone,
        "result_class": (
            "engineering_controller_route_a_post_recoverability_negative_readiness_index_pass"
            if status_pass
            else "engineering_controller_route_a_post_recoverability_negative_readiness_index_fail"
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
        "follow_up_manifest": str(paths["follow_up_manifest"]),
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
        "m2819_admission_preserved": m2819_admission_preserved(source),
        "m2818_pivot_preserved": m2818_pivot_preserved(source),
        "m2816_status_pass": source["m2816_summary"].get("status_pass"),
        "m2816_gate_matrix_pass": source["m2816_summary"].get("gate_matrix_pass"),
        "m2816_fixed_row_count": recoverability["fixed_row_count"],
        "m2816_accounted_count": recoverability["accounted_count"],
        "m2816_episode_count": recoverability["episode_count"],
        "m2816_execution_failure_count": recoverability["execution_failure_count"],
        "m2816_diagnostic_success_count": recoverability["diagnostic_success_count"],
        "m2816_diagnostic_collision_count": recoverability["diagnostic_collision_count"],
        "m2816_diagnostic_offtrack_termination_count": recoverability["diagnostic_offtrack_termination_count"],
        "m2816_post_event_available_count": recoverability["post_event_available_count"],
        "m2816_recoverability_window_row_count": recoverability["recoverability_window_row_count"],
        "m2816_recoverability_available_count": recoverability["recoverability_available_count"],
        "m2816_recoverability_success_count": recoverability["recoverability_success_count"],
        "m2816_post_offtrack_action_response_row_count": recoverability["post_offtrack_action_response_row_count"],
        "m2816_negative_recoverability_preserved": negative_recoverability_preserved,
        "m2816_guardrail_context_row_count": recoverability["guardrail_context_row_count"],
        "m2816_actor_contract_guard_row_count": recoverability["actor_contract_guard_row_count"],
        "m2816_claim_boundary_row_count": recoverability["claim_boundary_row_count"],
        "m2804_prior_readiness_preserved": prior_readiness_preserved,
        "m2804_status_pass": source["m2804_summary"].get("status_pass"),
        "m2804_negative_clearance_preserved": source["m2804_summary"].get("m2801_negative_clearance_preserved"),
        "m2804_stable_avoidable_retention_risk_preserved": source["m2804_summary"].get(
            "m2801_stable_avoidable_retention_risk_preserved"
        ),
        "m2804_blocker_matrix_row_count": _int(source["m2804_summary"].get("blocker_matrix_row_count")),
        "same_recoverability_repair_admitted": False,
        "same_recoverability_ranking_admitted": False,
        "hf3_source_dependency_paused": source["source_exists"]["m2638_doc"],
        "protected_mitigation_blocker_preserved": _bool(
            source["m2804_summary"].get("protected_mitigation_blocker_preserved")
        ),
        "protected_rows_in_success_denominator": protected_rows_in_success_denominator(source),
        "protected_rows_in_success_denominator_or_actor_input": False,
        "guardrails_outside_success_denominator": not protected_rows_in_success_denominator(source),
        "actor_contract_shape_72_action_3": actor_contract_preserved(source),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": hidden_oracle_actor_input_detected(source),
        "recoverability_labels_actor_visible": False,
        "action_response_labels_actor_visible": False,
        "source_family_labels_actor_visible": False,
        "task_family_labels_actor_visible": False,
        "blocker_labels_actor_visible": False,
        "route_decision_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
    }
    summary.update(FALSE_CLAIM_FLAGS)
    return summary


def build_follow_up_manifest(*, output_path: Path, m2819_design: Path) -> dict[str, Any]:
    summary_path = output_path / "summary.json"
    return {
        "id": DEFAULT_NEXT_BLOCKER,
        "type": "gate",
        "gate_tier": "process",
        "promotion_decision": "not_applicable",
        "failure_types": [
            "contract_violation",
            "lineage_invalid",
            "metric_artifact",
            "scenario_sampling_failure",
            "behavior_regression",
            "objective_overfit",
            "proof_washout",
        ],
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_path / "evidence_index.csv"),
                str(output_path / "deliverable_readiness_rows.csv"),
                str(output_path / "blocker_matrix.csv"),
                str(output_path / "next_action_admission_rows.csv"),
                str(output_path / "claim_boundary_rows.csv"),
                str(output_path / "gate_matrix.csv"),
                str(DEFAULT_DOC_PATH),
                str(m2819_design),
                str(M2818_DOC),
                str(M2817_DOC),
                str(M2816_SUMMARY),
                str(M2804_SUMMARY),
                str(M2638_DOC),
                str(ROUTE_PLAN),
            ],
            "parent_config": [
                "experiments/manifests/m2820-engineering-controller-route-a-post-recoverability-negative-readiness-index-materialization-preflight.json",
                "experiments/manifests/m2819-engineering-controller-route-a-post-recoverability-negative-readiness-index-design.json",
                "experiments/manifests/m2818-engineering-controller-route-a-post-action-response-recoverability-window-branch-synthesis.json",
                "experiments/manifests/m2816-engineering-controller-route-a-post-action-response-recoverability-window-instrumented-bounded-execution-preflight.json",
            ],
            "parent_objective": [
                "audit M2820 post-recoverability negative readiness/admission index before any interpretation"
            ],
            "derived_from": [
                DEFAULT_MILESTONE,
                "m2819-engineering-controller-route-a-post-recoverability-negative-readiness-index-design",
                "m2818-engineering-controller-route-a-post-action-response-recoverability-window-branch-synthesis",
                "m2816-engineering-controller-route-a-post-action-response-recoverability-window-instrumented-bounded-execution-preflight",
                "m2804-engineering-controller-route-a-post-clearance-corrective-readiness-index-materialization-preflight",
            ],
            "blocked_by": [
                "M2820 readiness index must be audited before continuation",
                "M2816/M2817 preserve 7 post-event traces but 0 recoverability-window availability and 0 recoverability success",
                "M2816 diagnostic outcomes include 1 collision and 5 offtrack terminations",
                "M2804/M2805 prior readiness blockers remain active",
                "M2638 HF3 source dependency remains unavailable",
            ],
            "supersedes": [
                "direct same recoverability-window repair or ranking from M2820",
                "direct validation readiness or driver-performance claim from M2820",
                "direct selected-platform HF3 execution while M2638 source dependency is unresolved",
            ],
            "invalidates": [],
        },
        "review_artifact": "docs/reviews/m2821-engineering-controller-route-a-post-recoverability-negative-readiness-index-materialization-result-audit.md",
        "public_gates": [
            "M2821 must audit M2820 required artifacts for completeness before interpretation",
            "M2821 must verify M2820 preserves M2816 7 post-event traces 0 recoverability-window availability 0 recoverability success 1 collision and 5 offtrack terminations",
            "M2821 must verify M2820 carries forward M2804/M2805 negative clearance stable_avoidable protected mitigation and HF3 blockers",
            "M2821 must verify actor 72/action 3 no hidden/oracle actor input and actor-invisible recoverability action-response blocker route success progress and verdict labels",
            "M2821 must not execute reset step rollout replay validation training PPO repair source build adapter probe external simulation ranking winner selection promotion or success-rate verdict computation",
            "M2821 must not claim repair success driver performance validation readiness/result high-fidelity validation paper finite-window-vs-GRU current-sim verdict full ideal driver completion or self-ID result",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not execute reset",
            "do not step environments",
            "do not execute policy action",
            "do not execute policy rollout",
            "do not execute replay",
            "do not execute measured validation",
            "do not train",
            "do not run PPO",
            "do not repair policy weights",
            "do not execute source build",
            "do not execute adapter probe",
            "do not execute external simulation",
            "do not promote a checkpoint",
            "do not use private holdout",
            "do not change actor inputs",
            "do not change the deployed action contract",
            "do not inject hidden or oracle actor features",
            "do not hide M2816 absent recoverability-window availability or recoverability success",
            "do not hide M2816 diagnostic collision or offtrack terminations",
            "do not weaken M2804 prior blockers or M2638 HF3 dependency blocker",
            "do not treat protected guardrail or blocker rows as ordinary success denominators",
            "do not rank controller families source families task families profiles action-response families recoverability families stress axes or scenario roles",
            "do not select a winner",
            "do not compute success-rate or controller-family verdict metrics",
            "do not claim repair success",
            "do not claim validation readiness",
            "do not claim validation result",
            "do not claim high-fidelity validation readiness",
            "do not claim high-fidelity validation result",
            "do not claim paper-level evidence",
            "do not claim finite-window vs GRU conclusion",
            "do not claim current-sim verdict",
            "do not claim level3 self-identification",
            "do not claim full ideal driver completion",
            "do not claim driver performance from M2820 readiness indexing",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_recoverability_negative_readiness_index",
            "evidence_axis": "post_recoverability_negative_readiness_index_result_audit",
            "evidence_increment": "audits M2820 readiness/admission artifacts before any stop package or new evidence route",
            "claim_scope": "Route A readiness/admission result audit only; no reset rollout replay validation training PPO repair ranking winner selection promotion success-rate verdict driver-performance paper finite-window-vs-GRU self-ID current-sim high-fidelity validation or full ideal driver claim",
            "stop_condition": [
                "stop if M2820 required artifacts are missing or incomplete",
                "stop if M2820 hides absent recoverability-window availability or recoverability success",
                "stop if M2820 weakens prior readiness protected mitigation or HF3 blockers",
                "stop if M2820 changes actor input or action contract",
                "stop if audit would rank recoverability rows controllers profiles stress axes or winners",
            ],
            "fallback_plan": [
                "route to artifact repair if required artifacts are incomplete",
                "route to branch synthesis if M2820 artifacts are complete",
                "preserve negative recoverability evidence instead of weakening gates",
                "route to explicit stop or new non-same-surface design after audit",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2820 materializes post-recoverability negative readiness/admission artifacts that require audit",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "evaluation_only",
            "stage_objective": "post-recoverability-negative readiness index result audit",
            "admission_evidence": [
                "M2820 materializes the readiness/admission index from existing artifacts only",
                "M2819 admits M2820 materialization and routes to M2821 audit",
                "M2818 stops direct recoverability-window local search",
                "M2816/M2817 preserve complete but negative recoverability diagnostics",
                "M2638 keeps selected-platform HF3 execution blocked until source dependency evidence is supplied",
            ],
            "blocked_shortcuts": [
                "no reset step rollout replay validation training PPO repair source build adapter probe external simulation",
                "no ranking winner selection promotion success-rate verdict",
                "no actor input expansion",
                "no repair success driver-performance validation-readiness paper current-sim high-fidelity full ideal driver or self-ID claim",
            ],
            "allowed_updates": [
                "docs/m2821-engineering-controller-route-a-post-recoverability-negative-readiness-index-materialization-result-audit.md",
                "M2821 status queue scoreboard research log and review",
                "one bounded synthesis or design manifest if M2820 is accepted",
            ],
            "next_stage_criteria": [
                "audit artifact exists",
                "audit records M2820 row counts and gate matrix",
                "audit preserves M2816 negative recoverability accounting",
                "audit preserves M2804/M2805 M2638 actor and claim boundaries",
                "audit selects only a bounded stop package or new pre-registered route if accepted",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2821 audits Route A readiness/admission rows and does not test history necessity or current-frame substitution.",
            "history_necessity_tests": [
                "None in M2821; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "Post-M2820 Route A post-recoverability negative readiness index only.",
            "negative_result_policy": "If M2820 artifacts are complete, preserve negative recoverability evidence and route to synthesis or bounded design instead of weakening gates.",
            "allowed_claims": [
                "Route A post-recoverability negative readiness/admission artifact audit",
                "actor and claim boundary preserved or violated",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits the refreshed readiness/admission index rather than adding another same-surface recoverability repair",
            "paper_verdict_delta": "no paper verdict; prevents M2820 readiness rows from being overinterpreted as self-ID or performance evidence",
            "must_synthesize_if": [
                "M2821 accepts complete M2820 artifacts",
                "M2821 rejects M2820 due to incomplete artifacts or boundary violations",
                "M2821 would claim repair success driver performance validation readiness paper evidence current-sim high-fidelity or self-ID",
                "M2821 would rank controllers source families profiles action-response families recoverability families stress axes select a winner promote a checkpoint or compute success-rate verdict",
            ],
        },
        "hypothesis": "A bounded result audit can accept or reject M2820 readiness-index artifacts while preserving actor blocker and claim boundaries before interpretation.",
        "success_criteria": [
            "docs/m2821-engineering-controller-route-a-post-recoverability-negative-readiness-index-materialization-result-audit.md exists",
            "audit records M2820 status_pass required artifacts evidence deliverable blocker next-action claim and gate counts",
            "audit verifies M2816/M2817 negative recoverability accounting remains visible",
            "audit verifies M2804/M2805 prior blockers and M2638 HF3 source dependency remain active",
            "audit preserves P0 observation 72 action 3 no hidden/oracle actor input actor-invisible labels",
            "no reset step rollout replay validation training PPO repair source build adapter probe external simulation ranking winner promotion success-rate driver-performance validation-readiness paper finite-window-vs-GRU current-sim high-fidelity validation full ideal driver completion or self-ID claim is made",
        ],
        "failure_criteria": [
            "M2821 executes reset step rollout replay validation training PPO repair source build adapter probe or external simulation",
            "M2821 changes actor input or action contract",
            "M2821 exposes recoverability action-response blocker gate outcome route success progress or verdict labels to actor input",
            "M2821 weakens M2816 negative recoverability accounting M2804 prior blockers or M2638 HF3 dependency blocker",
            "M2821 ranks controller families source families task families profiles action-response families recoverability families stress axes or scenario roles selects a winner promotes a checkpoint or computes success rate",
            "M2821 claims repair success driver performance validation readiness/result high-fidelity validation paper finite-window-vs-GRU current-sim verdict full ideal driver completion or self-ID result",
        ],
        "decision_rule": "Pass only if M2821 audits M2820 artifacts as complete and claim-safe and preserves blocker actor and claim boundaries without execution ranking validation performance paper current-sim high-fidelity full ideal driver or self-ID claims.",
        "commands": [{"name": "result_audit", "command": "true"}],
        "required_artifacts": [
            {
                "path": "docs/m2821-engineering-controller-route-a-post-recoverability-negative-readiness-index-materialization-result-audit.md",
                "type": "md",
            }
        ],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(DEFAULT_DOC_PATH),
            str(m2819_design),
            str(M2818_DOC),
            str(M2816_SUMMARY),
            str(M2804_SUMMARY),
            str(M2638_DOC),
            str(ROUTE_PLAN),
        ],
        "scoreboard_checkpoint": "docs/m2821-engineering-controller-route-a-post-recoverability-negative-readiness-index-materialization-result-audit.md",
        "next_blocker": "m2822-engineering-controller-route-a-post-recoverability-negative-readiness-index-result-synthesis",
    }


def evidence_row(
    evidence_id: str,
    source_milestone: str,
    artifact_path: Path,
    evidence_family: str,
    evidence_status: str,
    row_count: int,
    actor_ok: bool,
    hidden: bool,
    counts: dict[str, Any],
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
        "actor_contract_shape_72_action_3": actor_ok,
        "action_shape_3": actor_ok,
        "hidden_oracle_actor_input_detected": hidden,
        "post_event_available_count": counts.get("post_event_available_count", ""),
        "recoverability_window_available_count": counts.get("recoverability_window_available_count", ""),
        "recoverability_success_count": counts.get("recoverability_success_count", ""),
        "diagnostic_success_count": counts.get("diagnostic_success_count", ""),
        "diagnostic_collision_count": counts.get("diagnostic_collision_count", ""),
        "diagnostic_offtrack_termination_count": counts.get("diagnostic_offtrack_termination_count", ""),
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
        "# M2820 Engineering Controller Route A Post-Recoverability Negative Readiness Index Materialization Preflight",
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
        "## M2816/M2817 Recoverability Boundary",
        "",
        f"- fixed rows accounted: {summary['m2816_accounted_count']}",
        f"- instrumented execution rows: {summary['m2816_episode_count']}",
        f"- execution failures: {summary['m2816_execution_failure_count']}",
        f"- diagnostic success outcomes: {summary['m2816_diagnostic_success_count']}",
        f"- diagnostic collision outcomes: {summary['m2816_diagnostic_collision_count']}",
        f"- diagnostic offtrack terminations: {summary['m2816_diagnostic_offtrack_termination_count']}",
        f"- post-event available rows: {summary['m2816_post_event_available_count']}",
        f"- recoverability-window rows: {summary['m2816_recoverability_window_row_count']}",
        f"- recoverability-window available rows: {summary['m2816_recoverability_available_count']}",
        f"- recoverability-window success rows: {summary['m2816_recoverability_success_count']}",
        f"- negative recoverability preserved: `{str(summary['m2816_negative_recoverability_preserved']).lower()}`",
        "",
        "## Carried-Forward Blockers",
        "",
        f"- M2804 prior readiness preserved: `{str(summary['m2804_prior_readiness_preserved']).lower()}`",
        f"- negative clearance preserved: `{str(summary['m2804_negative_clearance_preserved']).lower()}`",
        f"- stable_avoidable retention risk preserved: `{str(summary['m2804_stable_avoidable_retention_risk_preserved']).lower()}`",
        f"- protected mitigation blocker preserved: `{str(summary['protected_mitigation_blocker_preserved']).lower()}`",
        f"- protected rows in success denominator: `{str(summary['protected_rows_in_success_denominator']).lower()}`",
        f"- HF3 source dependency paused: `{str(summary['hf3_source_dependency_paused']).lower()}`",
        "",
        "## Actor Boundary",
        "",
        f"- actor contract P0 72/action 3: `{str(summary['actor_contract_shape_72_action_3']).lower()}`",
        f"- hidden/oracle actor input detected: `{str(summary['hidden_oracle_actor_input_detected']).lower()}`",
        "- recoverability, action-response, source-family, task-family, blocker, route-decision, "
        "success/progress, and verdict labels actor-visible: `false`",
        "",
        "## Claim Boundary",
        "",
        "M2820 is a Route A readiness/admission index over existing artifacts only. It performs no reset, step, policy action, rollout, replay, validation, training, PPO, repair, source build, adapter probe, external simulation, ranking, winner selection, promotion, or success-rate computation.",
        "",
        "It does not claim repair success, driver performance, validation readiness, validation result, paper-level evidence, finite-window-vs-GRU, current-sim verdict, high-fidelity validation, full ideal driver completion, or self-ID evidence.",
        "",
    ]
    return "\n".join(lines)


def m2819_admission_preserved(source: dict[str, Any]) -> bool:
    text = source["m2819_design_text"]
    return (
        "admit_post_recoverability_negative_readiness_index_materialization_preflight" in text
        and "M2820 should reanalyze existing artifacts only" in text
    )


def m2818_pivot_preserved(source: dict[str, Any]) -> bool:
    return "pivot_to_post_recoverability_negative_route_a_readiness_index_design" in source["m2818_doc_text"]


def actor_contract_preserved(source: dict[str, Any]) -> bool:
    contract = source["m2541_actor_contract"]
    return (
        _int(contract.get("observation_shape")) == P0_OBSERVATION_DIM
        and _int(contract.get("action_shape")) == ACTION_DIM
        and _bool(source["m2541_summary"].get("actor_contract_shape_72_action_3"))
        and _bool(source["m2816_summary"].get("actor_contract_shape_72_action_3"))
        and _bool(source["m2804_summary"].get("actor_contract_shape_72_action_3"))
    )


def hidden_oracle_actor_input_detected(source: dict[str, Any]) -> bool:
    return (
        _bool(source["m2541_summary"].get("hidden_or_oracle_actor_inputs_required"))
        or _bool(source["m2816_summary"].get("hidden_oracle_actor_input_detected"))
        or _bool(source["m2804_summary"].get("hidden_oracle_actor_input_detected"))
        or not actor_contract_preserved(source)
    )


def actor_visible_labels_detected(source: dict[str, Any]) -> bool:
    recoverability_rows_visible = any(_bool(row.get("actor_visible_allowed")) for row in source["m2816_recoverability_rows"])
    post_rows_visible = any(_bool(row.get("actor_visible_allowed")) for row in source["m2816_post_offtrack_rows"])
    return (
        recoverability_rows_visible
        or post_rows_visible
        or _bool(source["m2804_summary"].get("taxonomy_labels_actor_visible"))
        or _bool(source["m2804_summary"].get("scenario_role_labels_actor_visible"))
        or _bool(source["m2804_summary"].get("metric_labels_actor_visible"))
        or _bool(source["m2804_summary"].get("target_labels_actor_visible"))
        or _bool(source["m2804_summary"].get("blocker_labels_actor_visible"))
        or _bool(source["m2804_summary"].get("route_decision_labels_actor_visible"))
        or _bool(source["m2804_summary"].get("success_progress_labels_actor_visible"))
        or _bool(source["m2804_summary"].get("verdict_labels_actor_visible"))
    )


def protected_rows_in_success_denominator(source: dict[str, Any]) -> bool:
    return _bool(source["m2804_summary"].get("protected_rows_in_success_denominator")) or _bool(
        source["m2816_summary"].get("protected_rows_in_success_denominator")
    )


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


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Materialize M2820 Route A post-recoverability negative readiness index."
    )
    parser.add_argument("--m2819-design", type=Path, default=DEFAULT_M2819_DESIGN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args(argv)
    summary = materialize_post_recoverability_negative_readiness_index(
        args.output_dir,
        m2819_design=args.m2819_design,
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
