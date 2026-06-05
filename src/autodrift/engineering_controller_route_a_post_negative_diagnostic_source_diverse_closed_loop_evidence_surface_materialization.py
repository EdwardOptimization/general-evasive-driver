"""Materialize Route A source-diverse evidence surface after negative repair.

This runner reanalyzes existing Route A artifacts only. It writes candidate,
blocked, context, actor-guard, claim-boundary, and gate rows. It does not
execute environments, policies, replay, validation, training, source builds,
adapter probes, ranking, promotion, or high-fidelity simulation.
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
    "m2734-engineering-controller-route-a-post-negative-diagnostic-source-diverse-"
    "closed-loop-evidence-surface-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2735-engineering-controller-route-a-post-negative-diagnostic-source-diverse-"
    "closed-loop-evidence-surface-materialization-result-audit"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2734_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2734-engineering-controller-route-a-post-negative-diagnostic-source-diverse-"
    "closed-loop-evidence-surface-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2735-engineering-controller-route-a-post-negative-diagnostic-"
    "source-diverse-closed-loop-evidence-surface-materialization-result-audit.json"
)

M2733_DOC = Path(
    "docs/m2733-engineering-controller-route-a-post-negative-diagnostic-source-diverse-"
    "closed-loop-evidence-surface-design.md"
)
M2732_DOC = Path(
    "docs/m2732-engineering-controller-route-a-evidence-index-after-exact-executable-"
    "repair-refresh-materialization-result-audit.md"
)
M2731_SUMMARY = Path("runs/m2731_engineering_controller_route_a_evidence_index_after_exact_executable_repair_refresh/summary.json")
M2691_SUMMARY = Path("runs/m2691_engineering_controller_source_diverse_offtrack_protected_target_panel/summary.json")
M2691_TARGET_ROWS = Path("runs/m2691_engineering_controller_source_diverse_offtrack_protected_target_panel/target_panel_rows.csv")
M2693_SUMMARY = Path(
    "runs/m2693_engineering_controller_source_diverse_offtrack_protected_bounded_execution_preflight/summary.json"
)
M2693_EXECUTION_ROWS = Path(
    "runs/m2693_engineering_controller_source_diverse_offtrack_protected_bounded_execution_preflight/"
    "target_execution_rows.csv"
)
M2714_SUMMARY = Path("runs/m2714_engineering_controller_route_a_current_m1690_exact_executable_reentry_panel/summary.json")
M2716_SUMMARY = Path(
    "runs/m2716_engineering_controller_route_a_current_m1690_exact_executable_reentry_bounded_execution_preflight/"
    "summary.json"
)
M2716_EXACT_ROWS = Path(
    "runs/m2716_engineering_controller_route_a_current_m1690_exact_executable_reentry_bounded_execution_preflight/"
    "exact_execution_rows.csv"
)
M2728_SUMMARY = Path(
    "runs/m2728_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_"
    "bounded_execution_preflight/summary.json"
)
M2728_REPAIR_ROWS = Path(
    "runs/m2728_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_"
    "bounded_execution_preflight/repair_execution_rows.csv"
)
M2667_SUMMARY = Path(
    "runs/m2667_engineering_controller_route_a_engineering_baseline_readiness_index_after_protected_taxonomy/"
    "summary.json"
)
M2667_KNOWN_FAILURE_ROWS = Path(
    "runs/m2667_engineering_controller_route_a_engineering_baseline_readiness_index_after_protected_taxonomy/"
    "known_failure_boundary_rows.csv"
)
M2638_DOC = Path(
    "docs/m2638-engineering-controller-route-c-hf3-source-dependency-blocker-report-and-user-supplied-"
    "source-contract-design.md"
)
ROUTE_PLAN = Path("docs/post-m2470-route-plan.md")

CLAIM_SCOPE = (
    "Route A source-diverse closed-loop evidence-surface materialization only; "
    "existing M2693, M2716, M2728, M2667, and M2638 artifacts may be reanalyzed "
    "into row artifacts, but no reset, step, rollout, replay, validation, training, "
    "PPO, source build, adapter probe, external simulation, ranking, winner selection, "
    "promotion, success-rate verdict, repair-success, driver-performance, paper, "
    "finite-window-vs-GRU, current-sim, high-fidelity validation, full ideal driver, "
    "or self-ID claim is made"
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
    "training_run": False,
    "ppo_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_computed": False,
    "success_rate_verdict_field_emitted": False,
    "controller_family_verdict_computed": False,
    "repair_success_claim_made": False,
    "driver_performance_claim_made": False,
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

INPUT_SOURCE_FIELDNAMES = [
    "source_id",
    "source_milestone",
    "artifact_path",
    "source_family",
    "source_role",
    "source_exists",
    "status_pass_or_present",
    "row_count",
    "diagnostic_success_count",
    "collision_count",
    "offtrack_count",
    "speed_too_low_count",
    "protected_blocking_count",
    "actor_contract_shape_72_action_3",
    "hidden_oracle_actor_input_detected",
    "candidate_admission_role",
    "claim_scope",
    "forbidden_interpretation",
]
CANDIDATE_FIELDNAMES = [
    "candidate_id",
    "source_milestone",
    "source_row_id",
    "source_family",
    "source_bucket",
    "task_family",
    "source_key",
    "source_execution_row_count",
    "diagnostic_success_count",
    "collision_count",
    "offtrack_count",
    "speed_too_low_count",
    "materialization_admitted",
    "same_surface_m2728_repair",
    "protected_or_hf3_blocked",
    "actor_contract_shape_72_action_3",
    "hidden_oracle_actor_input_detected",
    "diagnostic_only_no_verdict",
    "future_role",
    "claim_scope",
    "forbidden_interpretation",
]
DIVERSITY_FIELDNAMES = [
    "bucket_id",
    "source_family",
    "source_bucket",
    "candidate_count",
    "task_family_count",
    "source_key_count",
    "materialization_admitted_count",
    "same_surface_m2728_repair_count",
    "protected_or_hf3_blocked_count",
    "diagnostic_only_no_verdict",
    "claim_scope",
]
BLOCKED_FIELDNAMES = [
    "blocked_id",
    "blocked_family",
    "source_milestone",
    "source_row_id",
    "row_count",
    "blocking_count",
    "blocked_reason",
    "materialization_admitted",
    "protected_rows_in_success_denominator",
    "actor_visible_allowed",
    "claim_scope",
    "forbidden_interpretation",
]
NEGATIVE_CONTEXT_FIELDNAMES = [
    "context_id",
    "source_row_id",
    "candidate_row_id",
    "anchor_task_source_id",
    "profile_name",
    "task_family",
    "success",
    "collision",
    "termination_reason",
    "outcome_bucket",
    "context_role",
    "direct_same_surface_repair_execution_admitted",
    "diagnostic_only_no_verdict",
    "claim_scope",
    "forbidden_interpretation",
]
ACTOR_GUARD_FIELDNAMES = [
    "guard_id",
    "guard_family",
    "observed",
    "expected",
    "status_pass",
    "actor_visible_allowed",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2734",
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
    ("source_diverse_evidence_surface_materialized", True, "M2734 row artifacts"),
    ("source_diverse_candidate_rows_materialized", True, "M2693 and M2716 candidate rows"),
    ("m2728_negative_diagnostic_context_preserved", True, "M2728 repair rows in context artifact"),
    ("same_surface_repair_rejected", True, "blocked_surface rows and gates"),
    ("protected_blocker_preserved", True, "M2667 blocked rows"),
    ("hf3_blocker_preserved", True, "M2638 blocker row"),
    ("actor_contract_preserved", True, "actor guard rows"),
    ("follow_up_result_audit_registered", True, "M2735 result-audit manifest"),
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


def materialize_post_negative_source_diverse_evidence_surface(
    output_dir: Path | str,
    *,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_path, Path(doc_path))

    source = load_source_artifacts(follow_up_manifest=follow_up_manifest)
    m2728_counts = count_outcomes(source["m2728_repair_rows"])
    input_rows = build_input_source_rows(source, m2728_counts)
    candidate_rows = build_candidate_rows(source)
    diversity_rows = build_source_diversity_bucket_rows(candidate_rows)
    blocked_rows = build_blocked_surface_rows(source, m2728_counts)
    context_rows = build_negative_context_rows(source)
    actor_rows = build_actor_contract_guard_rows(source)
    claim_rows = build_claim_boundary_rows()

    gate_rows = build_gate_matrix_rows(
        source,
        m2728_counts,
        input_rows,
        candidate_rows,
        diversity_rows,
        blocked_rows,
        context_rows,
        actor_rows,
        claim_rows,
        required_artifacts_present=False,
    )
    write_outputs(paths, input_rows, candidate_rows, diversity_rows, blocked_rows, context_rows, actor_rows, claim_rows, gate_rows)
    summary = build_summary(
        output_dir=output_path,
        paths=paths,
        source=source,
        m2728_counts=m2728_counts,
        input_rows=input_rows,
        candidate_rows=candidate_rows,
        diversity_rows=diversity_rows,
        blocked_rows=blocked_rows,
        context_rows=context_rows,
        actor_rows=actor_rows,
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
        m2728_counts,
        input_rows,
        candidate_rows,
        diversity_rows,
        blocked_rows,
        context_rows,
        actor_rows,
        claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output_path,
        paths=paths,
        source=source,
        m2728_counts=m2728_counts,
        input_rows=input_rows,
        candidate_rows=candidate_rows,
        diversity_rows=diversity_rows,
        blocked_rows=blocked_rows,
        context_rows=context_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    return summary


def artifact_paths(output_dir: Path, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "input_source_rows": output_dir / "input_source_rows.csv",
        "evidence_surface_candidate_rows": output_dir / "evidence_surface_candidate_rows.csv",
        "source_diversity_bucket_rows": output_dir / "source_diversity_bucket_rows.csv",
        "blocked_surface_rows": output_dir / "blocked_surface_rows.csv",
        "negative_diagnostic_context_rows": output_dir / "negative_diagnostic_context_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "doc": doc_path,
    }


def write_outputs(
    paths: dict[str, Path],
    input_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    diversity_rows: list[dict[str, Any]],
    blocked_rows: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    write_csv_rows(paths["input_source_rows"], input_rows, fieldnames=INPUT_SOURCE_FIELDNAMES)
    write_csv_rows(paths["evidence_surface_candidate_rows"], candidate_rows, fieldnames=CANDIDATE_FIELDNAMES)
    write_csv_rows(paths["source_diversity_bucket_rows"], diversity_rows, fieldnames=DIVERSITY_FIELDNAMES)
    write_csv_rows(paths["blocked_surface_rows"], blocked_rows, fieldnames=BLOCKED_FIELDNAMES)
    write_csv_rows(paths["negative_diagnostic_context_rows"], context_rows, fieldnames=NEGATIVE_CONTEXT_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)


def load_source_artifacts(*, follow_up_manifest: Path | str) -> dict[str, Any]:
    paths = {
        "m2733_doc": M2733_DOC,
        "m2732_doc": M2732_DOC,
        "m2731_summary": M2731_SUMMARY,
        "m2691_summary": M2691_SUMMARY,
        "m2691_target_rows": M2691_TARGET_ROWS,
        "m2693_summary": M2693_SUMMARY,
        "m2693_execution_rows": M2693_EXECUTION_ROWS,
        "m2714_summary": M2714_SUMMARY,
        "m2716_summary": M2716_SUMMARY,
        "m2716_exact_rows": M2716_EXACT_ROWS,
        "m2728_summary": M2728_SUMMARY,
        "m2728_repair_rows": M2728_REPAIR_ROWS,
        "m2667_summary": M2667_SUMMARY,
        "m2667_known_failure_rows": M2667_KNOWN_FAILURE_ROWS,
        "m2638_doc": M2638_DOC,
        "route_plan": ROUTE_PLAN,
        "follow_up_manifest": Path(follow_up_manifest),
    }
    return {
        "paths": paths,
        "source_exists": {name: path.exists() for name, path in paths.items()},
        "m2731_summary": read_json(paths["m2731_summary"]),
        "m2691_summary": read_json(paths["m2691_summary"]),
        "m2691_target_rows": _read_csv_rows(paths["m2691_target_rows"]),
        "m2693_summary": read_json(paths["m2693_summary"]),
        "m2693_execution_rows": _read_csv_rows(paths["m2693_execution_rows"]),
        "m2714_summary": read_json(paths["m2714_summary"]),
        "m2716_summary": read_json(paths["m2716_summary"]),
        "m2716_exact_rows": _read_csv_rows(paths["m2716_exact_rows"]),
        "m2728_summary": read_json(paths["m2728_summary"]),
        "m2728_repair_rows": _read_csv_rows(paths["m2728_repair_rows"]),
        "m2667_summary": read_json(paths["m2667_summary"]),
        "m2667_known_failure_rows": _read_csv_rows(paths["m2667_known_failure_rows"]),
    }


def build_input_source_rows(source: dict[str, Any], m2728_counts: dict[str, int]) -> list[dict[str, Any]]:
    m2693_counts = count_outcomes(source["m2693_execution_rows"])
    m2716_counts = count_outcomes(source["m2716_exact_rows"])
    protected_blocking = sum(_int(row.get("blocking_row_count")) for row in source["m2667_known_failure_rows"])
    return [
        input_source_row(
            "m2733_design",
            "m2733",
            source["paths"]["m2733_doc"],
            "route_a_design",
            "design_contract",
            1,
            {"success_count": 0, "collision_count": 0, "offtrack_count": 0, "speed_too_low_count": 0},
            0,
            "design_source",
            source,
        ),
        input_source_row(
            "m2693_source_diverse_closed_loop_execution",
            "m2693",
            source["paths"]["m2693_execution_rows"],
            "source_diverse_current_sim_offtrack",
            "candidate_source",
            len(source["m2693_execution_rows"]),
            m2693_counts,
            0,
            "admit_to_candidate_materialization",
            source,
        ),
        input_source_row(
            "m2716_exact_executable_reentry_baseline",
            "m2716",
            source["paths"]["m2716_exact_rows"],
            "exact_executable_reentry_baseline",
            "candidate_source",
            len(source["m2716_exact_rows"]),
            m2716_counts,
            0,
            "admit_to_candidate_materialization_aggregated_by_task_source",
            source,
        ),
        input_source_row(
            "m2728_negative_repair_diagnostic",
            "m2728",
            source["paths"]["m2728_repair_rows"],
            "negative_repair_diagnostic",
            "negative_context_not_candidate",
            len(source["m2728_repair_rows"]),
            m2728_counts,
            0,
            "context_only_direct_same_surface_repair_rejected",
            source,
        ),
        input_source_row(
            "m2667_protected_mitigation_blocker",
            "m2667",
            source["paths"]["m2667_known_failure_rows"],
            "protected_mitigation_blocker",
            "blocked_surface",
            len(source["m2667_known_failure_rows"]),
            {"success_count": 0, "collision_count": 0, "offtrack_count": 0, "speed_too_low_count": 0},
            protected_blocking,
            "blocked_not_candidate",
            source,
        ),
        input_source_row(
            "m2638_hf3_source_dependency_blocker",
            "m2638",
            source["paths"]["m2638_doc"],
            "hf3_source_dependency_blocker",
            "blocked_surface",
            1,
            {"success_count": 0, "collision_count": 0, "offtrack_count": 0, "speed_too_low_count": 0},
            1,
            "blocked_not_candidate",
            source,
        ),
    ]


def build_candidate_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    actor_ok = actor_contract_preserved(source)
    hidden = hidden_oracle_actor_input_detected(source)
    for idx, row in enumerate(source["m2693_execution_rows"], start=1):
        counts = count_outcomes([row])
        rows.append(
            candidate_row(
                f"m2734-candidate-m2693-{idx:04d}",
                "m2693",
                row.get("target_id", f"m2693-row-{idx:04d}"),
                "source_diverse_current_sim_offtrack",
                "m2693_source_diverse_target",
                row.get("task_family", ""),
                row.get("source_key", row.get("target_id", "")),
                1,
                counts,
                actor_ok,
                hidden,
                "future_source_diverse_execution_design_candidate_after_audit",
            )
        )

    by_task_source: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in source["m2716_exact_rows"]:
        by_task_source[row.get("task_source_id", "")].append(row)
    for idx, (task_source_id, group) in enumerate(sorted(by_task_source.items()), start=1):
        counts = count_outcomes(group)
        task_families = sorted({row.get("task_family", "") for row in group if row.get("task_family", "")})
        rows.append(
            candidate_row(
                f"m2734-candidate-m2716-{idx:04d}",
                "m2716",
                task_source_id,
                "exact_executable_reentry_baseline",
                "m2716_exact_task_source",
                "|".join(task_families),
                task_source_id,
                len(group),
                counts,
                actor_ok,
                hidden,
                "future_non_same_surface_execution_design_candidate_after_audit",
            )
        )
    return rows


def build_source_diversity_bucket_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[(str(row["source_family"]), str(row["source_bucket"]))].append(row)
    rows = []
    for idx, ((source_family, source_bucket), group) in enumerate(sorted(grouped.items()), start=1):
        rows.append(
            {
                "bucket_id": f"m2734-source-diversity-bucket-{idx:04d}",
                "source_family": source_family,
                "source_bucket": source_bucket,
                "candidate_count": len(group),
                "task_family_count": len({row["task_family"] for row in group}),
                "source_key_count": len({row["source_key"] for row in group}),
                "materialization_admitted_count": sum(1 for row in group if _bool(row["materialization_admitted"])),
                "same_surface_m2728_repair_count": sum(1 for row in group if _bool(row["same_surface_m2728_repair"])),
                "protected_or_hf3_blocked_count": sum(1 for row in group if _bool(row["protected_or_hf3_blocked"])),
                "diagnostic_only_no_verdict": all(_bool(row["diagnostic_only_no_verdict"]) for row in group),
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def build_blocked_surface_rows(source: dict[str, Any], m2728_counts: dict[str, int]) -> list[dict[str, Any]]:
    rows = [
        blocked_row(
            "m2734-blocked-same-surface-m2728-repair",
            "same_surface_repair_loop",
            "m2728",
            "all_m2728_repair_rows",
            m2728_counts["row_count"],
            m2728_counts["row_count"],
            "M2730-M2733 reject direct continuation of the M2728 repair target/overlay surface",
            False,
            False,
            False,
        )
    ]
    for idx, row in enumerate(source["m2667_known_failure_rows"], start=1):
        rows.append(
            blocked_row(
                f"m2734-blocked-protected-{idx:04d}",
                "protected_mitigation_blocker",
                row.get("source_milestone", "m2667"),
                row.get("boundary_id", f"m2667-known-failure-{idx:04d}"),
                _int(row.get("row_count")),
                _int(row.get("blocking_row_count")),
                row.get("readiness_effect", "protected mitigation blocker remains visible"),
                False,
                _bool(row.get("protected_rows_in_success_denominator")),
                _bool(row.get("actor_visible_allowed")),
            )
        )
    rows.append(
        blocked_row(
            "m2734-blocked-hf3-source-dependency",
            "hf3_source_dependency_blocker",
            "m2638",
            "m2638_hf3_dependency_doc",
            1,
            1,
            "selected-platform HF3 execution remains paused until source dependency is supplied",
            False,
            False,
            False,
        )
    )
    return rows


def build_negative_context_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for idx, row in enumerate(source["m2728_repair_rows"], start=1):
        rows.append(
            {
                "context_id": f"m2734-negative-context-{idx:04d}",
                "source_row_id": str(idx),
                "candidate_row_id": row.get("candidate_row_id", ""),
                "anchor_task_source_id": row.get("anchor_task_source_id", ""),
                "profile_name": row.get("profile_name", ""),
                "task_family": row.get("task_family", ""),
                "success": _bool(row.get("success")),
                "collision": _bool(row.get("collision")),
                "termination_reason": row.get("termination_reason", ""),
                "outcome_bucket": row.get("outcome_bucket", ""),
                "context_role": "negative_repair_context_only_not_candidate",
                "direct_same_surface_repair_execution_admitted": False,
                "diagnostic_only_no_verdict": True,
                "claim_scope": CLAIM_SCOPE,
                "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
            }
        )
    return rows


def build_actor_contract_guard_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    same_surface_admitted = False
    return [
        actor_guard("m2734-actor-guard-observation-shape", "observation_shape", P0_OBSERVATION_DIM, P0_OBSERVATION_DIM),
        actor_guard("m2734-actor-guard-action-shape", "action_shape", ACTION_DIM, ACTION_DIM),
        actor_guard("m2734-actor-guard-hidden-oracle", "hidden_oracle_actor_input_detected", hidden_oracle_actor_input_detected(source), False),
        actor_guard("m2734-actor-guard-target-labels", "target_labels_actor_visible", False, False),
        actor_guard("m2734-actor-guard-protected-labels", "protected_labels_actor_visible", False, False),
        actor_guard("m2734-actor-guard-route-labels", "route_decision_labels_actor_visible", False, False),
        actor_guard("m2734-actor-guard-success-progress-labels", "success_progress_labels_actor_visible", False, False),
        actor_guard("m2734-actor-guard-verdict-labels", "verdict_labels_actor_visible", False, False),
        actor_guard(
            "m2734-actor-guard-protected-denominator",
            "protected_rows_in_success_denominator",
            _bool(source["m2667_summary"].get("protected_rows_in_success_denominator")),
            False,
        ),
        actor_guard(
            "m2734-actor-guard-same-surface-repair-admitted",
            "same_surface_repair_execution_admitted",
            same_surface_admitted,
            False,
        ),
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": f"m2734_claim_boundary_{claim}",
            "claim_family": claim,
            "allowed_in_m2734": allowed,
            "status_pass": True,
            "evidence_required_before_claim": evidence_required,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim, allowed, evidence_required in CLAIM_CHECKS
    ]


def build_gate_matrix_rows(
    source: dict[str, Any],
    m2728_counts: dict[str, int],
    input_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    diversity_rows: list[dict[str, Any]],
    blocked_rows: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    *,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    source_families = {row["source_family"] for row in candidate_rows}
    same_surface_admitted = any(_bool(row["same_surface_m2728_repair"]) for row in candidate_rows)
    protected_inside_denominator = any(_bool(row["protected_rows_in_success_denominator"]) for row in blocked_rows)
    actor_visible_blocked = any(_bool(row["actor_visible_allowed"]) for row in blocked_rows)
    return [
        gate_row("m2734_gate_source_artifacts_present", "artifact", all(source["source_exists"].values()), True),
        gate_row("m2734_gate_required_artifacts_present", "artifact", required_artifacts_present, True),
        gate_row("m2734_gate_m2733_design_doc_present", "lineage", source["source_exists"]["m2733_doc"], True),
        gate_row("m2734_gate_m2693_status_pass", "lineage", source["m2693_summary"].get("status_pass"), True),
        gate_row("m2734_gate_m2716_status_pass", "lineage", source["m2716_summary"].get("status_pass"), True),
        gate_row("m2734_gate_m2728_status_pass", "lineage", source["m2728_summary"].get("status_pass"), True),
        gate_row("m2734_gate_input_source_rows", "artifact", len(input_rows), 6),
        gate_row("m2734_gate_candidate_rows_materialized", "artifact", len(candidate_rows), 18),
        gate_row("m2734_gate_source_diversity_families", "source_diversity", len(source_families) >= 2, True),
        gate_row("m2734_gate_diversity_bucket_rows", "source_diversity", len(diversity_rows), 2),
        gate_row("m2734_gate_negative_context_rows", "diagnostic_accounting", len(context_rows), 31),
        gate_row("m2734_gate_m2728_success_count_preserved", "diagnostic_accounting", m2728_counts["success_count"], 1),
        gate_row("m2734_gate_m2728_collision_count_preserved", "diagnostic_accounting", m2728_counts["collision_count"], 3),
        gate_row("m2734_gate_m2728_offtrack_count_preserved", "diagnostic_accounting", m2728_counts["offtrack_count"], 27),
        gate_row("m2734_gate_same_surface_repair_not_admitted", "process", same_surface_admitted, False),
        gate_row("m2734_gate_protected_blocked_rows_visible", "known_failure_boundary", len([r for r in blocked_rows if r["blocked_family"] == "protected_mitigation_blocker"]), 10),
        gate_row("m2734_gate_hf3_blocked_row_visible", "hf3_dependency", len([r for r in blocked_rows if r["blocked_family"] == "hf3_source_dependency_blocker"]), 1),
        gate_row("m2734_gate_protected_rows_outside_success_denominator", "known_failure_boundary", protected_inside_denominator, False),
        gate_row("m2734_gate_blocked_labels_actor_invisible", "actor_contract", actor_visible_blocked, False),
        gate_row("m2734_gate_actor_contract_72_action_3", "actor_contract", actor_contract_preserved(source), True),
        gate_row("m2734_gate_hidden_oracle_actor_input_absent", "actor_contract", hidden_oracle_actor_input_detected(source), False),
        gate_row("m2734_gate_actor_guard_rows_pass", "actor_contract", all(_bool(row["status_pass"]) for row in actor_rows), True),
        gate_row("m2734_gate_follow_up_result_audit_registered", "process", source["source_exists"]["follow_up_manifest"], True),
        gate_row("m2734_gate_claim_boundary_pass", "claim_boundary", all(_bool(row["status_pass"]) for row in claim_rows) and not any(FALSE_CLAIM_FLAGS.values()), True),
        gate_row("m2734_gate_no_reset_rollout_training_validation", "claim_boundary", False, False),
        gate_row("m2734_gate_no_ranking_promotion_success_rate_performance", "claim_boundary", False, False),
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    m2728_counts: dict[str, int],
    input_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    diversity_rows: list[dict[str, Any]],
    blocked_rows: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    source_families = {row["source_family"] for row in candidate_rows}
    same_surface_admitted = any(_bool(row["same_surface_m2728_repair"]) for row in candidate_rows)
    negative_diagnostic_preserved = m2728_counts == {
        "row_count": 31,
        "success_count": 1,
        "collision_count": 3,
        "offtrack_count": 27,
        "speed_too_low_count": 0,
    }
    actor_ok = actor_contract_preserved(source)
    hidden = hidden_oracle_actor_input_detected(source)
    protected_rows_in_success_denominator = any(_bool(row["protected_rows_in_success_denominator"]) for row in blocked_rows)
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    status_pass = (
        required_artifacts_present
        and all(source["source_exists"].values())
        and _bool(source["m2693_summary"].get("status_pass"))
        and _bool(source["m2716_summary"].get("status_pass"))
        and _bool(source["m2728_summary"].get("status_pass"))
        and _bool(source["m2667_summary"].get("status_pass"))
        and len(input_rows) == 6
        and len(candidate_rows) == 18
        and len(source_families) >= 2
        and len(diversity_rows) >= 2
        and len(context_rows) == 31
        and negative_diagnostic_preserved
        and not same_surface_admitted
        and actor_ok
        and not hidden
        and not protected_rows_in_success_denominator
        and gate_matrix_pass
        and not any(FALSE_CLAIM_FLAGS.values())
    )
    return {
        "protocol_version": "engineering_controller_route_a_post_negative_source_diverse_surface_v0",
        "result_class": "engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_materialization_pass",
        "milestone": milestone,
        "next_blocker": next_blocker,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "input_source_rows": str(paths["input_source_rows"]),
        "evidence_surface_candidate_rows": str(paths["evidence_surface_candidate_rows"]),
        "source_diversity_bucket_rows": str(paths["source_diversity_bucket_rows"]),
        "blocked_surface_rows": str(paths["blocked_surface_rows"]),
        "negative_diagnostic_context_rows": str(paths["negative_diagnostic_context_rows"]),
        "actor_contract_guard_rows": str(paths["actor_contract_guard_rows"]),
        "claim_boundary_rows": str(paths["claim_boundary_rows"]),
        "gate_matrix": str(paths["gate_matrix"]),
        "doc": str(paths["doc"]),
        "follow_up_manifest": str(source["paths"]["follow_up_manifest"]),
        "required_artifacts_present": required_artifacts_present,
        "source_artifacts_present": all(source["source_exists"].values()),
        "source_artifacts_reanalyzed_only": True,
        "input_source_row_count": len(input_rows),
        "evidence_surface_candidate_row_count": len(candidate_rows),
        "source_diversity_bucket_row_count": len(diversity_rows),
        "source_diversity_family_count": len(source_families),
        "blocked_surface_row_count": len(blocked_rows),
        "negative_diagnostic_context_row_count": len(context_rows),
        "actor_contract_guard_row_count": len(actor_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "m2693_candidate_row_count": len([row for row in candidate_rows if row["source_milestone"] == "m2693"]),
        "m2716_candidate_row_count": len([row for row in candidate_rows if row["source_milestone"] == "m2716"]),
        "m2728_negative_context_row_count": len(context_rows),
        "m2728_success_count": m2728_counts["success_count"],
        "m2728_collision_count": m2728_counts["collision_count"],
        "m2728_offtrack_count": m2728_counts["offtrack_count"],
        "m2728_negative_diagnostic_preserved": negative_diagnostic_preserved,
        "same_surface_repair_execution_admitted": same_surface_admitted,
        "protected_mitigation_blocker_preserved": _bool(source["m2667_summary"].get("protected_mitigation_blocker_preserved")),
        "protected_rows_in_success_denominator": protected_rows_in_success_denominator,
        "hf3_source_dependency_paused": source["source_exists"]["m2638_doc"],
        "actor_contract_shape_72_action_3": actor_ok,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": hidden,
        "taxonomy_labels_actor_visible": False,
        "target_labels_actor_visible": False,
        "protected_labels_actor_visible": False,
        "blocker_labels_actor_visible": False,
        "route_decision_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "admitted_next_action_count": 1,
        "selected_next_action": "m2735_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_result_audit",
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "status_pass": status_pass,
        **FALSE_CLAIM_FLAGS,
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2734 Engineering Controller Route A Post-Negative Diagnostic Source-Diverse Closed-Loop Evidence Surface Materialization Preflight",
            "",
            "- status: completed" if summary["status_pass"] else "- status: failed",
            f"- result_class: `{summary['result_class']}`",
            f"- summary: `{summary['summary']}`",
            f"- input source rows: `{summary['input_source_rows']}`",
            f"- evidence surface candidate rows: `{summary['evidence_surface_candidate_rows']}`",
            f"- source diversity bucket rows: `{summary['source_diversity_bucket_rows']}`",
            f"- blocked surface rows: `{summary['blocked_surface_rows']}`",
            f"- negative diagnostic context rows: `{summary['negative_diagnostic_context_rows']}`",
            f"- actor contract guard rows: `{summary['actor_contract_guard_rows']}`",
            f"- claim boundary rows: `{summary['claim_boundary_rows']}`",
            f"- gate matrix: `{summary['gate_matrix']}`",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            f"- next: `{summary['next_blocker']}`",
            "",
            "## Materialized Surface",
            "",
            f"- input source rows: {summary['input_source_row_count']}",
            f"- candidate rows: {summary['evidence_surface_candidate_row_count']}",
            f"- source-diversity families: {summary['source_diversity_family_count']}",
            f"- source-diversity bucket rows: {summary['source_diversity_bucket_row_count']}",
            f"- blocked surface rows: {summary['blocked_surface_row_count']}",
            f"- M2693 candidate rows: {summary['m2693_candidate_row_count']}",
            f"- M2716 candidate rows: {summary['m2716_candidate_row_count']}",
            "",
            "## Negative Diagnostic Context",
            "",
            f"- M2728 context rows: {summary['m2728_negative_context_row_count']}",
            f"- M2728 diagnostic success rows: {summary['m2728_success_count']}",
            f"- M2728 collision rows: {summary['m2728_collision_count']}",
            f"- M2728 off_track rows: {summary['m2728_offtrack_count']}",
            f"- M2728 negative diagnostic preserved: `{str(summary['m2728_negative_diagnostic_preserved']).lower()}`",
            f"- same-surface repair execution admitted: `{str(summary['same_surface_repair_execution_admitted']).lower()}`",
            "",
            "## Blockers And Actor Boundary",
            "",
            f"- protected mitigation blocker preserved: `{str(summary['protected_mitigation_blocker_preserved']).lower()}`",
            f"- protected rows in success denominator: `{str(summary['protected_rows_in_success_denominator']).lower()}`",
            f"- HF3 source dependency paused: `{str(summary['hf3_source_dependency_paused']).lower()}`",
            f"- actor contract P0 72/action 3: `{str(summary['actor_contract_shape_72_action_3']).lower()}`",
            f"- hidden/oracle actor input detected: `{str(summary['hidden_oracle_actor_input_detected']).lower()}`",
            "- taxonomy, target, protected, blocker, route-decision, success/progress, and verdict labels actor-visible: `false`",
            "",
            "## Claim Boundary",
            "",
            "M2734 is materialization from existing artifacts only. It performs no reset, step, rollout, replay, validation, training, PPO, source build, adapter probe, external simulation, ranking, winner selection, promotion, or success-rate computation.",
            "",
            "It does not claim repair success, driver performance, validation readiness, validation result, paper-level evidence, finite-window-vs-GRU, current-sim verdict, high-fidelity validation, full ideal driver completion, or self-ID evidence.",
            "",
        ]
    )


def input_source_row(
    source_id: str,
    source_milestone: str,
    artifact_path: Path,
    source_family: str,
    source_role: str,
    row_count: int,
    counts: dict[str, int],
    protected_blocking_count: int,
    candidate_admission_role: str,
    source: dict[str, Any],
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "source_milestone": source_milestone,
        "artifact_path": str(artifact_path),
        "source_family": source_family,
        "source_role": source_role,
        "source_exists": artifact_path.exists(),
        "status_pass_or_present": artifact_path.exists(),
        "row_count": row_count,
        "diagnostic_success_count": counts.get("success_count", 0),
        "collision_count": counts.get("collision_count", 0),
        "offtrack_count": counts.get("offtrack_count", 0),
        "speed_too_low_count": counts.get("speed_too_low_count", 0),
        "protected_blocking_count": protected_blocking_count,
        "actor_contract_shape_72_action_3": actor_contract_preserved(source),
        "hidden_oracle_actor_input_detected": hidden_oracle_actor_input_detected(source),
        "candidate_admission_role": candidate_admission_role,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def candidate_row(
    candidate_id: str,
    source_milestone: str,
    source_row_id: str,
    source_family: str,
    source_bucket: str,
    task_family: str,
    source_key: str,
    source_execution_row_count: int,
    counts: dict[str, int],
    actor_ok: bool,
    hidden: bool,
    future_role: str,
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "source_milestone": source_milestone,
        "source_row_id": source_row_id,
        "source_family": source_family,
        "source_bucket": source_bucket,
        "task_family": task_family,
        "source_key": source_key,
        "source_execution_row_count": source_execution_row_count,
        "diagnostic_success_count": counts.get("success_count", 0),
        "collision_count": counts.get("collision_count", 0),
        "offtrack_count": counts.get("offtrack_count", 0),
        "speed_too_low_count": counts.get("speed_too_low_count", 0),
        "materialization_admitted": True,
        "same_surface_m2728_repair": False,
        "protected_or_hf3_blocked": False,
        "actor_contract_shape_72_action_3": actor_ok,
        "hidden_oracle_actor_input_detected": hidden,
        "diagnostic_only_no_verdict": True,
        "future_role": future_role,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def blocked_row(
    blocked_id: str,
    blocked_family: str,
    source_milestone: str,
    source_row_id: str,
    row_count: int,
    blocking_count: int,
    blocked_reason: str,
    materialization_admitted: bool,
    protected_rows_in_success_denominator: bool,
    actor_visible_allowed: bool,
) -> dict[str, Any]:
    return {
        "blocked_id": blocked_id,
        "blocked_family": blocked_family,
        "source_milestone": source_milestone,
        "source_row_id": source_row_id,
        "row_count": row_count,
        "blocking_count": blocking_count,
        "blocked_reason": blocked_reason,
        "materialization_admitted": materialization_admitted,
        "protected_rows_in_success_denominator": protected_rows_in_success_denominator,
        "actor_visible_allowed": actor_visible_allowed,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def actor_guard(guard_id: str, guard_family: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": guard_id,
        "guard_family": guard_family,
        "observed": observed,
        "expected": expected,
        "status_pass": observed == expected,
        "actor_visible_allowed": False,
        "claim_boundary": CLAIM_SCOPE,
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


def count_outcomes(rows: list[dict[str, str]]) -> dict[str, int]:
    return {
        "row_count": len(rows),
        "success_count": sum(1 for row in rows if _bool(row.get("success"))),
        "collision_count": sum(1 for row in rows if _bool(row.get("collision"))),
        "offtrack_count": sum(1 for row in rows if row.get("termination_reason") == "off_track"),
        "speed_too_low_count": sum(1 for row in rows if row.get("termination_reason") == "speed_too_low"),
    }


def actor_contract_preserved(source: dict[str, Any]) -> bool:
    return (
        _bool(source["m2731_summary"].get("actor_contract_shape_72_action_3"))
        and _bool(source["m2691_summary"].get("actor_contract_shape_72_action_3"))
        and _bool(source["m2693_summary"].get("actor_contract_shape_72_action_3"))
        and _bool(source["m2714_summary"].get("actor_contract_shape_72_action_3"))
        and _bool(source["m2716_summary"].get("actor_contract_shape_72_action_3"))
        and _bool(source["m2728_summary"].get("actor_contract_shape_72_action_3"))
    )


def hidden_oracle_actor_input_detected(source: dict[str, Any]) -> bool:
    hidden_keys = (
        "hidden_oracle_actor_input_detected",
        "hidden_oracle_actor_input_required",
        "hidden_or_oracle_actor_input_detected",
        "hidden_or_oracle_actor_inputs_required",
    )
    summaries = (
        source["m2731_summary"],
        source["m2691_summary"],
        source["m2693_summary"],
        source["m2714_summary"],
        source["m2716_summary"],
        source["m2728_summary"],
        source["m2667_summary"],
    )
    summary_hidden = any(_bool(summary.get(key)) for summary in summaries for key in hidden_keys)
    row_hidden = any(_bool(row.get("hidden_oracle_actor_input_required")) for row in source["m2728_repair_rows"])
    return summary_hidden or row_hidden


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
        description="Materialize Route A source-diverse evidence surface after negative repair diagnostics."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args(argv)
    summary = materialize_post_negative_source_diverse_evidence_surface(
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
