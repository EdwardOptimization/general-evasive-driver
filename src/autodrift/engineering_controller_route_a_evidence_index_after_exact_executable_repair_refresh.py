"""Materialize Route A evidence index after exact-executable repair synthesis.

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
    "m2731-engineering-controller-route-a-evidence-index-after-exact-executable-"
    "repair-refresh-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2732-engineering-controller-route-a-evidence-index-after-exact-executable-"
    "repair-refresh-materialization-result-audit"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2731_engineering_controller_route_a_evidence_index_after_exact_executable_repair_refresh"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2731-engineering-controller-route-a-evidence-index-after-exact-executable-"
    "repair-refresh-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2732-engineering-controller-route-a-evidence-index-"
    "after-exact-executable-repair-refresh-materialization-result-audit.json"
)

M2730_DOC = Path(
    "docs/m2730-engineering-controller-route-a-current-m1690-exact-executable-"
    "reentry-offtrack-repair-result-synthesis.md"
)
M2729_DOC = Path(
    "docs/m2729-engineering-controller-route-a-current-m1690-exact-executable-"
    "reentry-offtrack-repair-bounded-execution-result-audit.md"
)
M2728_SUMMARY = Path(
    "runs/m2728_engineering_controller_route_a_current_m1690_exact_executable_reentry_"
    "offtrack_repair_bounded_execution_preflight/summary.json"
)
M2728_REPAIR_ROWS = Path(
    "runs/m2728_engineering_controller_route_a_current_m1690_exact_executable_reentry_"
    "offtrack_repair_bounded_execution_preflight/repair_execution_rows.csv"
)
M2728_PROFILE_AGGREGATE = Path(
    "runs/m2728_engineering_controller_route_a_current_m1690_exact_executable_reentry_"
    "offtrack_repair_bounded_execution_preflight/profile_aggregate.csv"
)
M2667_SUMMARY = Path(
    "runs/m2667_engineering_controller_route_a_engineering_baseline_readiness_index_"
    "after_protected_taxonomy/summary.json"
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
    "Route A evidence/readiness index after exact-executable repair synthesis only; "
    "source-artifact reanalysis with no reset, step, rollout, replay, validation, "
    "training, PPO, source build, adapter probe, external simulation, ranking, winner "
    "selection, promotion, success-rate verdict, repair-success, driver-performance, "
    "paper, finite-window-vs-GRU, current-sim, high-fidelity validation, full ideal "
    "driver, or self-ID claim"
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
    "claim_scope",
    "gap_or_limit",
    "next_use",
    "source_exists",
    "forbidden_interpretation",
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
    "allowed_in_m2731",
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
    ("route_a_evidence_index_materialized", True, "M2731 summary and evidence index artifacts"),
    ("m2728_negative_diagnostic_indexed", True, "M2728 repair rows indexed with diagnostic counts"),
    ("m2638_hf3_blocker_preserved", True, "M2638 source dependency blocker remains visible"),
    ("actor_contract_indexed", True, "M2541 and M2728 preserve P0 observation 72/action 3"),
    ("follow_up_result_audit_registered", True, "M2732 result-audit manifest"),
    ("repair_success", False, "future repair result plus claim audit"),
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


def materialize_evidence_index_after_exact_executable_repair_refresh(
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
    diagnostic_counts = count_m2728_diagnostics(source["m2728_repair_rows"])
    evidence_rows = build_evidence_index_rows(source, diagnostic_counts)
    blocker_rows = build_blocker_matrix_rows(source, diagnostic_counts)
    next_rows = build_next_action_admission_rows()
    claim_rows = build_claim_boundary_rows()

    paths = {
        "summary": output_path / "summary.json",
        "evidence_index": output_path / "evidence_index.csv",
        "blocker_matrix": output_path / "blocker_matrix.csv",
        "next_action_admission_rows": output_path / "next_action_admission_rows.csv",
        "claim_boundary_rows": output_path / "claim_boundary_rows.csv",
        "gate_matrix": output_path / "gate_matrix.csv",
        "doc": Path(doc_path),
    }

    write_csv_rows(paths["evidence_index"], evidence_rows, fieldnames=EVIDENCE_FIELDNAMES)
    write_csv_rows(paths["blocker_matrix"], blocker_rows, fieldnames=BLOCKER_FIELDNAMES)
    write_csv_rows(paths["next_action_admission_rows"], next_rows, fieldnames=NEXT_ACTION_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)

    gate_rows = build_gate_matrix_rows(
        source,
        diagnostic_counts,
        evidence_rows,
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
        "m2730_doc": M2730_DOC,
        "m2729_doc": M2729_DOC,
        "m2728_summary": M2728_SUMMARY,
        "m2728_repair_rows": M2728_REPAIR_ROWS,
        "m2728_profile_aggregate": M2728_PROFILE_AGGREGATE,
        "m2667_summary": M2667_SUMMARY,
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
        "m2728_summary": read_json(paths["m2728_summary"]),
        "m2728_repair_rows": _read_csv_rows(paths["m2728_repair_rows"]),
        "m2728_profile_aggregate": _read_csv_rows(paths["m2728_profile_aggregate"]),
        "m2667_summary": read_json(paths["m2667_summary"]),
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
    return [
        evidence_row(
            "m2730_repair_result_synthesis",
            "m2730",
            source["paths"]["m2730_doc"],
            "branch_synthesis",
            "pivot_completed",
            1,
            actor_ok,
            hidden,
            counts,
            "same-surface repair branch is closed; synthesis is not repair success",
            "audit evidence index before choosing any new Route A action",
        ),
        evidence_row(
            "m2729_repair_result_audit",
            "m2729",
            source["paths"]["m2729_doc"],
            "result_audit",
            "accepted_claim_safe_negative_diagnostic",
            1,
            actor_ok,
            hidden,
            counts,
            "accepted artifact completeness but rejected direct repair-success interpretation",
            "source acceptance boundary for M2731",
        ),
        evidence_row(
            "m2728_negative_offtrack_repair_diagnostic",
            "m2728",
            source["paths"]["m2728_repair_rows"],
            "closed_loop_diagnostic",
            "negative_offtrack_dominant",
            len(source["m2728_repair_rows"]),
            actor_ok,
            hidden,
            counts,
            "1 success, 3 collision, and 27 off_track rows are diagnostic only",
            "preserve as non-ranking non-verdict evidence",
        ),
        evidence_row(
            "m2728_profile_aggregate_nonranking",
            "m2728",
            source["paths"]["m2728_profile_aggregate"],
            "profile_aggregate",
            "nonranking_diagnostic",
            len(source["m2728_profile_aggregate"]),
            actor_ok,
            hidden,
            counts,
            "profile aggregates are not controller-family ranking evidence",
            "retain only as accounting context for audit",
        ),
        evidence_row(
            "m2667_protected_readiness_blocker",
            "m2667",
            source["paths"]["m2667_known_failure_rows"],
            "protected_mitigation_blocker",
            "active_blocker_preserved",
            len(source["m2667_known_failure_rows"]),
            actor_ok,
            hidden,
            {},
            "protected mitigation blockers remain outside success denominators",
            "block repair, promotion, validation readiness, and driver-performance claims",
        ),
        evidence_row(
            "m2638_hf3_source_dependency_blocker",
            "m2638",
            source["paths"]["m2638_doc"],
            "hf3_source_dependency",
            "paused_until_source_supplied",
            1,
            actor_ok,
            hidden,
            {},
            "selected-platform HF3 execution remains blocked by missing source dependency",
            "keep Route C blocked unless source dependency is supplied",
        ),
        evidence_row(
            "m2541_baseline_actor_contract",
            "m2541",
            source["paths"]["m2541_actor_contract"],
            "actor_contract",
            "materialized",
            1,
            actor_ok,
            hidden,
            {},
            "actor contract is a boundary, not a performance result",
            "preserve P0 observation 72/action 3 for future Route A work",
        ),
        evidence_row(
            "m2505_public_benchmark_pack",
            "m2505",
            source["paths"]["m2505_summary"],
            "public_benchmark_pack",
            "materialized",
            _int(source["m2505_summary"].get("artifact_manifest_rows")),
            actor_ok,
            hidden,
            {},
            "benchmark pack is source-only diagnostic packaging, not a current verdict",
            "reuse as public artifact lineage",
        ),
        evidence_row(
            "m2508_runtime_inference_cost_report",
            "m2508",
            source["paths"]["m2508_summary"],
            "runtime_inference_cost",
            "materialized",
            _int(source["m2508_summary"].get("measurement_row_count")),
            actor_ok,
            hidden,
            {},
            "runtime cost evidence is not driver performance or validation readiness",
            "reuse as engineering feasibility context",
        ),
        evidence_row(
            "post_m2470_route_plan",
            "post-m2470",
            source["paths"]["route_plan"],
            "governing_route_plan",
            "active_route_constraint",
            1,
            actor_ok,
            hidden,
            {},
            "Route A engineering mainline remains separate from Route B paper evidence and Route C HF validation",
            "enforce non-overclaiming next-action admission",
        ),
    ]


def build_blocker_matrix_rows(source: dict[str, Any], counts: dict[str, int]) -> list[dict[str, Any]]:
    unsuccessful = counts["row_count"] - counts["success_count"]
    protected_blocking_rows = _int(source["m2667_summary"].get("known_failure_blocking_boundary_row_count"))
    return [
        blocker_row(
            "m2731_blocker_current_m1690_exact_executable_offtrack_negative",
            "Route A",
            "exact_executable_repair_diagnostic",
            "active_negative_diagnostic",
            unsuccessful,
            "M2732 audit then a new non-same-surface evidence axis before any further execution",
            "only M2732 result audit admitted",
            "keeps 1/31 success, 3/31 collision, 27/31 offtrack visible",
            "same-surface repair execution loop",
        ),
        blocker_row(
            "m2731_blocker_same_surface_repair_local_search",
            "Route A",
            "workflow_synthesis",
            "closed_by_m2730_pivot",
            1,
            "new Route A evidence surface or explicit stop after audit",
            "same-surface execution not admitted",
            "prevents public current-M1690 overfit loop",
            "direct repeat repair execution",
        ),
        blocker_row(
            "m2731_blocker_protected_mitigation",
            "Route A",
            "protected_mitigation_blocker",
            "active_blocker_preserved",
            protected_blocking_rows,
            "separate protected executable-support/source route before protected interpretation",
            "audit only; no protected success denominator",
            "keeps known protected limitations separate from repair diagnostic rows",
            "treating protected rows as ordinary success denominators",
        ),
        blocker_row(
            "m2731_blocker_hf3_source_dependency_unavailable",
            "Route C",
            "hf3_source_dependency",
            "paused_until_source_dependency_supplied",
            1,
            "user-supplied source root, package route, or dependency acquisition manifest",
            "HF3 execution not admitted",
            "keeps validation layer separate from Route A evidence indexing",
            "fetching external source or running selected-platform HF3 without dependency",
        ),
        blocker_row(
            "m2731_blocker_actor_contract_guard",
            "Route A",
            "actor_contract",
            "guard_pass_current",
            0,
            "preserve P0 observation 72/action 3 and no hidden/oracle labels",
            "future actions must keep actor input contract unchanged",
            "keeps evidence labels actor-invisible",
            "adding hidden dynamics, taxonomy, route, success, or verdict labels to actor input",
        ),
    ]


def build_next_action_admission_rows() -> list[dict[str, Any]]:
    return [
        next_action_row(
            "m2732_route_a_evidence_index_after_exact_executable_repair_result_audit",
            "Route A",
            "admitted",
            "M2731 materializes an evidence index and must be audited before any new route or stop decision",
            "M2731 status_pass true and required artifacts present",
            "audit whether the evidence index preserved negative diagnostics and blockers",
        ),
        next_action_row(
            "new_route_a_closed_loop_evidence_surface",
            "Route A",
            "defer_until_m2732_audit",
            "M2731 is reanalysis only and cannot select a new execution surface before audit",
            "M2732 audit plus explicit new evidence-axis manifest",
            "may expand evidence only after audit rejects same-surface local search",
        ),
        next_action_row(
            "same_surface_exact_executable_offtrack_repair_execution",
            "Route A",
            "not_admitted",
            "M2730 pivot closes immediate same-surface repair after negative M2728 diagnostic",
            "new evidence axis and synthesis/audit admission",
            "prevents public current-M1690 local search",
        ),
        next_action_row(
            "hf3_selected_platform_execution",
            "Route C",
            "not_admitted",
            "M2638 source dependency blocker remains unresolved",
            "source root, package route, or dependency acquisition manifest supplied by user",
            "keeps high-fidelity validation out of M2731",
        ),
        next_action_row(
            "controller_ranking_or_winner_selection",
            "Route A/B",
            "not_admitted",
            "M2728 aggregates and M2731 index are non-ranking diagnostics",
            "separate proof, generalization, and promotion gates",
            "ranking and winner selection remain forbidden",
        ),
        next_action_row(
            "validation_or_driver_performance_claim",
            "Route A",
            "not_admitted",
            "M2731 performs no validation and M2728 remains offtrack-dominant",
            "future validation manifest and claim audit",
            "validation readiness and driver-performance claims remain forbidden",
        ),
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": f"m2731_claim_boundary_{claim}",
            "claim_family": claim,
            "allowed_in_m2731": allowed,
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
    blocker_rows: list[dict[str, Any]],
    next_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    *,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    protected_rows_inside_success = _bool(source["m2667_summary"].get("protected_rows_in_success_denominator"))
    hidden = hidden_oracle_actor_input_detected(source)
    return [
        gate_row("m2731_gate_source_artifacts_present", "artifact", all(source["source_exists"].values()), True),
        gate_row("m2731_gate_required_artifacts_present", "artifact", required_artifacts_present, True),
        gate_row("m2731_gate_m2730_synthesis_doc_present", "lineage", source["source_exists"]["m2730_doc"], True),
        gate_row("m2731_gate_m2728_summary_status_pass", "lineage", source["m2728_summary"].get("status_pass"), True),
        gate_row("m2731_gate_m2728_repair_rows_accounted", "diagnostic_accounting", counts["row_count"], 31),
        gate_row("m2731_gate_m2728_success_count_preserved", "diagnostic_accounting", counts["success_count"], 1),
        gate_row("m2731_gate_m2728_collision_count_preserved", "diagnostic_accounting", counts["collision_count"], 3),
        gate_row("m2731_gate_m2728_offtrack_count_preserved", "diagnostic_accounting", counts["offtrack_count"], 27),
        gate_row("m2731_gate_actor_contract_72_action_3", "actor_contract", actor_contract_preserved(source), True),
        gate_row("m2731_gate_hidden_oracle_actor_input_absent", "actor_contract", hidden, False),
        gate_row(
            "m2731_gate_protected_blocker_preserved",
            "known_failure_boundary",
            source["m2667_summary"].get("protected_mitigation_blocker_preserved"),
            True,
        ),
        gate_row(
            "m2731_gate_protected_rows_outside_success_denominator",
            "known_failure_boundary",
            protected_rows_inside_success,
            False,
        ),
        gate_row("m2731_gate_hf3_source_dependency_blocker_present", "hf3_dependency", source["source_exists"]["m2638_doc"], True),
        gate_row("m2731_gate_follow_up_result_audit_registered", "process", source["source_exists"]["follow_up_manifest"], True),
        gate_row(
            "m2731_gate_single_admitted_next_action",
            "process",
            sum(1 for row in next_rows if row["admission_status"] == "admitted"),
            1,
        ),
        gate_row(
            "m2731_gate_same_surface_repair_not_admitted",
            "process",
            any(
                row["candidate_action_id"] == "same_surface_exact_executable_offtrack_repair_execution"
                and row["admission_status"] == "admitted"
                for row in next_rows
            ),
            False,
        ),
        gate_row(
            "m2731_gate_claim_boundary_pass",
            "claim_boundary",
            all(_bool(row["status_pass"]) for row in claim_rows) and not any(FALSE_CLAIM_FLAGS.values()),
            True,
        ),
        gate_row("m2731_gate_no_reset_rollout_training_validation", "claim_boundary", False, False),
        gate_row("m2731_gate_no_ranking_promotion_success_rate_performance", "claim_boundary", False, False),
        gate_row("m2731_gate_evidence_index_rows_materialized", "artifact", len(evidence_rows), 10),
        gate_row("m2731_gate_blocker_rows_materialized", "artifact", len(blocker_rows), 5),
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    diagnostic_counts: dict[str, int],
    evidence_rows: list[dict[str, Any]],
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
    negative_diagnostic_preserved = diagnostic_counts == {
        "row_count": 31,
        "success_count": 1,
        "collision_count": 3,
        "offtrack_count": 27,
    }
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    status_pass = (
        required_artifacts_present
        and all(source["source_exists"].values())
        and _bool(source["m2728_summary"].get("status_pass"))
        and _bool(source["m2667_summary"].get("status_pass"))
        and _bool(source["m2541_summary"].get("status_pass"))
        and _bool(source["m2505_summary"].get("status_pass"))
        and _bool(source["m2508_summary"].get("status_pass"))
        and negative_diagnostic_preserved
        and actor_ok
        and not hidden
        and protected_blocker_preserved
        and protected_rows_outside_success
        and len(admitted_actions) == 1
        and gate_matrix_pass
        and not any(FALSE_CLAIM_FLAGS.values())
    )
    return {
        "protocol_version": "engineering_controller_route_a_evidence_index_after_exact_executable_repair_v0",
        "result_class": "engineering_controller_route_a_evidence_index_after_exact_executable_repair_refresh_pass",
        "milestone": milestone,
        "next_blocker": next_blocker,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "evidence_index": str(paths["evidence_index"]),
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
        "blocker_matrix_row_count": len(blocker_rows),
        "next_action_admission_row_count": len(next_rows),
        "admitted_next_action_count": len(admitted_actions),
        "selected_next_action": admitted_actions[0] if admitted_actions else "",
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "repair_execution_row_count": diagnostic_counts["row_count"],
        "m2728_success_count": diagnostic_counts["success_count"],
        "m2728_collision_count": diagnostic_counts["collision_count"],
        "m2728_offtrack_count": diagnostic_counts["offtrack_count"],
        "m2728_negative_diagnostic_preserved": negative_diagnostic_preserved,
        "same_surface_repair_closed": source["source_exists"]["m2730_doc"],
        "hf3_source_dependency_paused": source["source_exists"]["m2638_doc"],
        "protected_mitigation_blocker_preserved": protected_blocker_preserved,
        "protected_failure_blocking": _bool(source["m2667_summary"].get("protected_failure_blocking")),
        "protected_rows_in_success_denominator": not protected_rows_outside_success,
        "known_failure_boundary_row_count": len(source["m2667_known_failure_rows"]),
        "actor_contract_shape_72_action_3": actor_ok,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": hidden,
        "taxonomy_labels_actor_visible": False,
        "repair_target_labels_actor_visible": False,
        "objective_gate_labels_actor_visible": False,
        "route_decision_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "status_pass": status_pass,
        **FALSE_CLAIM_FLAGS,
    }


def count_m2728_diagnostics(rows: list[dict[str, str]]) -> dict[str, int]:
    return {
        "row_count": len(rows),
        "success_count": sum(1 for row in rows if _bool(row.get("success"))),
        "collision_count": sum(1 for row in rows if _bool(row.get("collision"))),
        "offtrack_count": sum(1 for row in rows if row.get("termination_reason") == "off_track"),
    }


def actor_contract_preserved(source: dict[str, Any]) -> bool:
    return (
        _bool(source["m2728_summary"].get("actor_contract_shape_72_action_3"))
        and _bool(source["m2541_summary"].get("actor_contract_shape_72_action_3"))
        and _int(source["m2541_summary"].get("observation_shape")) == P0_OBSERVATION_DIM
        and _int(source["m2541_summary"].get("action_shape")) == ACTION_DIM
        and _int(source["m2508_summary"].get("observation_shape")) == P0_OBSERVATION_DIM
        and _int(source["m2508_summary"].get("action_shape")) == ACTION_DIM
    )


def hidden_oracle_actor_input_detected(source: dict[str, Any]) -> bool:
    hidden_keys = (
        "hidden_oracle_actor_input_detected",
        "hidden_or_oracle_actor_input_detected",
        "hidden_or_oracle_actor_inputs_required",
        "hidden_oracle_actor_input_required",
    )
    summaries = (
        source["m2728_summary"],
        source["m2667_summary"],
        source["m2541_summary"],
        source["m2505_summary"],
        source["m2508_summary"],
    )
    summary_hidden = any(_bool(summary.get(key)) for summary in summaries for key in hidden_keys)
    row_hidden = any(_bool(row.get("hidden_oracle_actor_input_required")) for row in source["m2728_repair_rows"])
    return summary_hidden or row_hidden


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2731 Engineering Controller Route A Evidence Index After Exact-Executable Repair Refresh Materialization Preflight",
            "",
            "- status: completed" if summary["status_pass"] else "- status: failed",
            f"- result_class: `{summary['result_class']}`",
            f"- summary: `{summary['summary']}`",
            f"- evidence index: `{summary['evidence_index']}`",
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
            f"- blocker rows: {summary['blocker_matrix_row_count']}",
            f"- selected next action: `{summary['selected_next_action']}`",
            f"- source artifacts reanalyzed only: `{str(summary['source_artifacts_reanalyzed_only']).lower()}`",
            "",
            "## M2728 Diagnostic Boundary",
            "",
            f"- repair execution rows: {summary['repair_execution_row_count']}",
            f"- diagnostic success rows: {summary['m2728_success_count']}",
            f"- collision rows: {summary['m2728_collision_count']}",
            f"- off_track rows: {summary['m2728_offtrack_count']}",
            f"- negative diagnostic preserved: `{str(summary['m2728_negative_diagnostic_preserved']).lower()}`",
            f"- same-surface repair closed by M2730: `{str(summary['same_surface_repair_closed']).lower()}`",
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
            "- taxonomy, repair-target, objective-gate, route-decision, and verdict labels actor-visible: `false`",
            "",
            "## Claim Boundary",
            "",
            "M2731 is an evidence/readiness index over existing artifacts only. It performs no reset, step, rollout, replay, validation, training, PPO, source build, adapter probe, external simulation, ranking, winner selection, promotion, or success-rate computation.",
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Materialize Route A evidence index after exact-executable repair synthesis."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args(argv)
    summary = materialize_evidence_index_after_exact_executable_repair_refresh(
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
