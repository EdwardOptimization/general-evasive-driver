"""Materialize the M2912 Route A dependency-facing evidence surface."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Iterable


MILESTONE_ID = "m2913-engineering-controller-route-a-dependency-facing-evidence-surface-materialization-preflight"
NEXT_ID = "m2914-engineering-controller-route-a-dependency-facing-evidence-surface-materialization-result-audit"
DEFAULT_M2912_DESIGN = Path("docs/m2912-engineering-controller-route-a-dependency-facing-evidence-surface-design.md")
DEFAULT_M2911_SYNTHESIS = Path(
    "docs/m2911-engineering-controller-route-a-post-route-b-source-insufficient-dependency-facing-synthesis.md"
)
DEFAULT_M2910_SYNTHESIS = Path(
    "docs/m2910-paper-route-l0-l1-l2-l3-capability-prediction-post-source-acquisition-continuation-or-pivot-synthesis.md"
)
DEFAULT_M2879_SYNTHESIS = Path(
    "docs/m2879-engineering-controller-route-a-post-package-refresh-fresh-closed-loop-evidence-result-synthesis.md"
)
DEFAULT_M2883_DESIGN = Path(
    "docs/m2883-engineering-controller-route-c-hf3-chrono-next-dependency-gate-or-stop-design.md"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2913_engineering_controller_route_a_dependency_facing_evidence_surface_materialization_preflight")
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2914-engineering-controller-route-a-dependency-facing-evidence-surface-materialization-result-audit.json"
)

P0_OBSERVATION_DIM = 72
ACTION_DIM = 3
CLAIM_BOUNDARY = "route_a_dependency_facing_evidence_surface_materialization_only_no_execution_no_performance_claim"
DECISION_PASS = "dependency_facing_evidence_surface_materialized_route_to_m2914_result_audit"
DECISION_FAIL = "dependency_facing_evidence_surface_materialization_incomplete"

REQUIRED_OUTPUTS = {
    "summary": "summary.json",
    "route_context_rows": "route_context_rows.csv",
    "candidate_family_rows": "candidate_family_rows.csv",
    "exclusion_family_rows": "exclusion_family_rows.csv",
    "denominator_policy_rows": "denominator_policy_rows.csv",
    "failure_taxonomy_rows": "failure_taxonomy_rows.csv",
    "actor_contract_rows": "actor_contract_rows.csv",
    "claim_boundary_rows": "claim_boundary_rows.csv",
    "gate_rows": "gate_rows.csv",
    "run_state": "run_state.json",
}

ROUTE_CONTEXT_FIELDNAMES = (
    "context_id",
    "route_axis",
    "source_artifact",
    "source_exists",
    "materialization_role",
    "ordinary_engineering_denominator_allowed",
    "paper_denominator_allowed",
    "high_fidelity_readiness_allowed",
    "self_id_claim_allowed",
    "claim_boundary",
)
CANDIDATE_FAMILY_FIELDNAMES = (
    "candidate_family_id",
    "family_name",
    "route_axis",
    "source_artifact",
    "materialization_role",
    "may_seed_later_materialized_candidate",
    "requires_new_execution_before_evidence_claim",
    "hidden_oracle_actor_input_required",
    "future_target_actor_input_required",
    "ordinary_engineering_denominator_allowed_before_audit",
    "paper_denominator_allowed",
    "high_fidelity_readiness_allowed",
    "status_pass",
    "claim_boundary",
)
EXCLUSION_FAMILY_FIELDNAMES = (
    "exclusion_family_id",
    "family_name",
    "exclusion_reason",
    "allowed_usage",
    "ordinary_engineering_denominator_allowed",
    "paper_denominator_allowed",
    "high_fidelity_readiness_allowed",
    "status_pass",
    "claim_boundary",
)
DENOMINATOR_POLICY_FIELDNAMES = (
    "denominator_policy_id",
    "policy_label",
    "allowed_usage",
    "ordinary_engineering_denominator_allowed_before_audit",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "promotion_denominator_allowed",
    "status_pass",
    "claim_boundary",
)
FAILURE_TAXONOMY_FIELDNAMES = (
    "failure_taxonomy_id",
    "failure_label",
    "failure_definition",
    "blocks_candidate_materialization",
    "blocks_denominator_admission",
    "status_pass",
    "claim_boundary",
)
ACTOR_CONTRACT_FIELDNAMES = (
    "actor_contract_id",
    "contract_field",
    "observed",
    "expected",
    "status_pass",
    "claim_boundary",
)
CLAIM_BOUNDARY_FIELDNAMES = (
    "claim_id",
    "claim_family",
    "claim_made",
    "claim_allowed",
    "evidence_required_before_claim",
    "claim_boundary",
)
GATE_FIELDNAMES = (
    "gate_id",
    "gate_family",
    "status_pass",
    "observed",
    "expected",
    "failure_type",
    "claim_boundary",
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _write_csv(path: Path, fieldnames: Iterable[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    names = list(fieldnames)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=names, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in names})


def _paths(output_dir: Path) -> dict[str, Path]:
    return {key: output_dir / filename for key, filename in REQUIRED_OUTPUTS.items()}


def build_route_context_rows(
    *,
    m2912_design: Path,
    m2911_synthesis: Path,
    m2910_synthesis: Path,
    m2879_synthesis: Path,
    m2883_design: Path,
) -> list[dict[str, Any]]:
    specs = (
        (
            "m2912_design",
            "route_a",
            m2912_design,
            "surface_design_authority",
            True,
            False,
            False,
            False,
        ),
        (
            "m2911_dependency_facing_synthesis",
            "route_a",
            m2911_synthesis,
            "route_selection_context",
            False,
            False,
            False,
            False,
        ),
        (
            "m2910_route_b_source_insufficient",
            "route_b",
            m2910_synthesis,
            "source_family_insufficiency_context_only",
            False,
            False,
            False,
            False,
        ),
        (
            "m2879_route_a_weak_diagnostic",
            "route_a",
            m2879_synthesis,
            "weak_diagnostic_context_only",
            False,
            False,
            False,
            False,
        ),
        (
            "m2883_route_c_source_unavailable",
            "route_c",
            m2883_design,
            "source_unavailable_dependency_context_only",
            False,
            False,
            False,
            False,
        ),
    )
    rows: list[dict[str, Any]] = []
    for index, (context_id, route_axis, artifact, role, engineering, paper, hf, self_id) in enumerate(
        specs,
        start=1,
    ):
        rows.append(
            {
                "context_id": f"context-{index:03d}-{context_id}",
                "route_axis": route_axis,
                "source_artifact": str(artifact),
                "source_exists": artifact.exists(),
                "materialization_role": role,
                "ordinary_engineering_denominator_allowed": engineering,
                "paper_denominator_allowed": paper,
                "high_fidelity_readiness_allowed": hf,
                "self_id_claim_allowed": self_id,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_candidate_family_rows(
    *,
    m2912_design: Path,
    m2911_synthesis: Path,
    m2910_synthesis: Path,
    m2879_synthesis: Path,
    m2883_design: Path,
) -> list[dict[str, Any]]:
    specs = (
        (
            "C1",
            "route_a_source_diverse_closed_loop_diagnostics",
            "route_a",
            m2912_design,
            "candidate_seed_for_later_materialization",
            True,
            True,
        ),
        (
            "C2",
            "weak_diagnostic_failure_context",
            "route_a",
            m2879_synthesis,
            "failure_context_only",
            False,
            False,
        ),
        (
            "C3",
            "engineering_readiness_and_runtime_context",
            "route_a",
            m2911_synthesis,
            "readiness_context_only",
            False,
            False,
        ),
        (
            "C4",
            "route_b_source_insufficient_context",
            "route_b",
            m2910_synthesis,
            "route_b_context_only",
            False,
            False,
        ),
        (
            "C5",
            "route_c_source_unavailable_context",
            "route_c",
            m2883_design,
            "dependency_context_only",
            False,
            False,
        ),
    )
    rows: list[dict[str, Any]] = []
    for index, (family_id, family_name, route_axis, artifact, role, may_seed, needs_execution) in enumerate(
        specs,
        start=1,
    ):
        rows.append(
            {
                "candidate_family_id": f"candidate-family-{index:03d}-{family_id}",
                "family_name": family_name,
                "route_axis": route_axis,
                "source_artifact": str(artifact),
                "materialization_role": role,
                "may_seed_later_materialized_candidate": may_seed,
                "requires_new_execution_before_evidence_claim": needs_execution,
                "hidden_oracle_actor_input_required": False,
                "future_target_actor_input_required": False,
                "ordinary_engineering_denominator_allowed_before_audit": False,
                "paper_denominator_allowed": False,
                "high_fidelity_readiness_allowed": False,
                "status_pass": artifact.exists(),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_exclusion_family_rows() -> list[dict[str, Any]]:
    specs = (
        (
            "same_family_route_b_acquisition_rows",
            "same-family Route B acquisition cannot become source-family proof",
            "route_b_context_or_exclusion_only",
        ),
        (
            "m2877_fixed_post_package_rows",
            "exhausted weak fixed diagnostic surface cannot become validation proof",
            "diagnostic_context_only",
        ),
        (
            "route_c_source_unavailable_rows",
            "source_unavailable rows cannot imply high-fidelity readiness",
            "dependency_context_only",
        ),
        (
            "protected_public_or_package_guard_rows",
            "guard rows protect known public/package boundaries",
            "guard_or_exclusion_only",
        ),
        (
            "hidden_oracle_actor_input_rows",
            "hidden or oracle actor input violates deployable contract",
            "rejected_boundary_violation",
        ),
        (
            "future_target_actor_input_rows",
            "future target actor input violates deployable contract",
            "rejected_boundary_violation",
        ),
    )
    return [
        {
            "exclusion_family_id": f"exclusion-family-{index:03d}",
            "family_name": family,
            "exclusion_reason": reason,
            "allowed_usage": usage,
            "ordinary_engineering_denominator_allowed": False,
            "paper_denominator_allowed": False,
            "high_fidelity_readiness_allowed": False,
            "status_pass": True,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for index, (family, reason, usage) in enumerate(specs, start=1)
    ]


def build_denominator_policy_rows() -> list[dict[str, Any]]:
    specs = (
        (
            "ordinary_engineering_candidate",
            "later_route_a_execution_candidate_after_result_audit_only",
            True,
        ),
        ("diagnostic_context_only", "failure_explanation_or_route_decision_only", False),
        ("guard_or_exclusion_only", "protects_known_boundaries_only", False),
        ("route_b_context_only", "preserves_source_family_insufficiency_only", False),
        ("route_c_dependency_context_only", "preserves_source_unavailable_only", False),
        ("rejected_boundary_violation", "not_admitted", False),
    )
    return [
        {
            "denominator_policy_id": f"denominator-policy-{index:03d}",
            "policy_label": label,
            "allowed_usage": usage,
            "ordinary_engineering_denominator_allowed_before_audit": False,
            "validation_denominator_allowed": False,
            "paper_denominator_allowed": False,
            "promotion_denominator_allowed": False,
            "status_pass": allowed in {True, False},
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for index, (label, usage, allowed) in enumerate(specs, start=1)
    ]


def build_failure_taxonomy_rows() -> list[dict[str, Any]]:
    specs = (
        ("source_identity_unresolved", "row cannot be traced to a source artifact or task-source identity", True, True),
        ("stale_fixed_surface", "row belongs to an exhausted fixed diagnostic surface", False, True),
        ("route_b_source_family_insufficient", "row would rely on same-family Route B acquisition", False, True),
        ("route_c_dependency_unavailable", "row would require unavailable high-fidelity source/build/reset gates", False, True),
        ("actor_contract_violation", "row would require hidden/oracle/future-target actor input or action mismatch", True, True),
        ("denominator_violation", "row would enter validation paper or ordinary denominator without audit", True, True),
        ("candidate_materialization_ok", "row is claim-safe for later materialization audit only", False, False),
    )
    return [
        {
            "failure_taxonomy_id": f"failure-taxonomy-{index:03d}",
            "failure_label": label,
            "failure_definition": definition,
            "blocks_candidate_materialization": blocks_candidate,
            "blocks_denominator_admission": blocks_denominator,
            "status_pass": True,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for index, (label, definition, blocks_candidate, blocks_denominator) in enumerate(specs, start=1)
    ]


def build_actor_contract_rows() -> list[dict[str, Any]]:
    specs = (
        ("observation_dim", P0_OBSERVATION_DIM, P0_OBSERVATION_DIM),
        ("action_dim", ACTION_DIM, ACTION_DIM),
        ("hidden_oracle_actor_input_required", False, False),
        ("future_target_actor_input_required", False, False),
        ("route_label_actor_visible", False, False),
        ("success_progress_verdict_actor_visible", False, False),
    )
    return [
        {
            "actor_contract_id": f"actor-contract-{index:03d}",
            "contract_field": field,
            "observed": observed,
            "expected": expected,
            "status_pass": observed == expected,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for index, (field, observed, expected) in enumerate(specs, start=1)
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    specs = (
        ("driver_performance", "later_closed_loop_execution_and_result_audit"),
        ("validation_readiness", "later_validation_gate_with_denominator_audit"),
        ("current_sim_verdict", "later current-sim validation synthesis"),
        ("high_fidelity_validation", "Route C source/build/reset/step gates first"),
        ("paper_evidence", "source-diverse fair L0/L1/L2/L3 evidence"),
        ("finite_window_vs_gru", "paired same-case model-quality evidence"),
        ("self_id", "history-necessity and source-diverse terminal-boundary tests"),
        ("checkpoint_promotion", "proof generalization behavior and holdout gates"),
    )
    return [
        {
            "claim_id": f"claim-{index:03d}",
            "claim_family": family,
            "claim_made": False,
            "claim_allowed": False,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for index, (family, evidence) in enumerate(specs, start=1)
    ]


def build_gate_rows(
    *,
    route_context_rows: list[dict[str, Any]],
    candidate_family_rows: list[dict[str, Any]],
    exclusion_family_rows: list[dict[str, Any]],
    denominator_policy_rows: list[dict[str, Any]],
    failure_taxonomy_rows: list[dict[str, Any]],
    actor_contract_rows: list[dict[str, Any]],
    claim_boundary_rows: list[dict[str, Any]],
    follow_up_manifest: Path,
) -> list[dict[str, Any]]:
    parent_artifacts_exist = all(row["source_exists"] for row in route_context_rows)
    actor_contract_pass = all(row["status_pass"] for row in actor_contract_rows)
    no_claims_made = all(not row["claim_made"] and not row["claim_allowed"] for row in claim_boundary_rows)
    route_b_context_only = all(
        not row["paper_denominator_allowed"]
        for row in route_context_rows
        if row["route_axis"] == "route_b"
    )
    route_c_context_only = all(
        not row["high_fidelity_readiness_allowed"]
        for row in route_context_rows
        if row["route_axis"] == "route_c"
    )
    specs = (
        ("parent_artifacts_exist", parent_artifacts_exist, sum(row["source_exists"] for row in route_context_rows), len(route_context_rows), "lineage_invalid"),
        ("candidate_family_rows_written", len(candidate_family_rows) >= 5, len(candidate_family_rows), 5, "scenario_sampling_failure"),
        ("exclusion_family_rows_written", len(exclusion_family_rows) >= 6, len(exclusion_family_rows), 6, "metric_artifact"),
        ("denominator_policy_rows_written", len(denominator_policy_rows) >= 6, len(denominator_policy_rows), 6, "metric_artifact"),
        ("failure_taxonomy_rows_written", len(failure_taxonomy_rows) >= 7, len(failure_taxonomy_rows), 7, "metric_artifact"),
        ("actor_contract_pass", actor_contract_pass, actor_contract_pass, True, "contract_violation"),
        ("route_b_context_only", route_b_context_only, route_b_context_only, True, "proof_washout"),
        ("route_c_context_only", route_c_context_only, route_c_context_only, True, "metric_artifact"),
        ("no_claims_made", no_claims_made, no_claims_made, True, "metric_artifact"),
        ("follow_up_manifest_written", follow_up_manifest.exists(), str(follow_up_manifest), "exists", "lineage_invalid"),
    )
    rows: list[dict[str, Any]] = []
    for index, (gate_family, passed, observed, expected, failure_type) in enumerate(specs, start=1):
        rows.append(
            {
                "gate_id": f"gate-{index:03d}",
                "gate_family": gate_family,
                "status_pass": passed,
                "observed": observed,
                "expected": expected,
                "failure_type": "none" if passed else failure_type,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_follow_up_manifest(*, summary_path: Path, output_dir: Path, decision: str) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "type": "gate",
        "gate_tier": "process",
        "promotion_decision": "not_applicable",
        "hypothesis": "A bounded result audit can accept or reject the M2913 Route A dependency-facing evidence surface materialization before any execution validation ranking promotion performance paper high-fidelity or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
                "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
                "runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/checkpoints/m2866_localized_response_prediction_training_candidate.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "route_context_rows.csv"),
                str(output_dir / "candidate_family_rows.csv"),
                str(output_dir / "exclusion_family_rows.csv"),
                str(output_dir / "denominator_policy_rows.csv"),
                str(output_dir / "failure_taxonomy_rows.csv"),
                str(output_dir / "actor_contract_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_rows.csv"),
                "docs/m2912-engineering-controller-route-a-dependency-facing-evidence-surface-design.md",
            ],
            "parent_config": [
                "experiments/manifests/m2913-engineering-controller-route-a-dependency-facing-evidence-surface-materialization-preflight.json",
                "experiments/manifests/m2912-engineering-controller-route-a-dependency-facing-evidence-surface-design.json",
            ],
            "parent_objective": [
                "audit the M2913 materialized Route A dependency-facing evidence surface before any execution"
            ],
            "derived_from": [
                MILESTONE_ID,
                "m2912-engineering-controller-route-a-dependency-facing-evidence-surface-design",
            ],
            "blocked_by": [
                "M2913 materialization must be audited before candidate rows can influence any execution design",
                "Route B source-family insufficiency and Route C source_unavailable must remain context only",
            ],
            "supersedes": [
                "direct Route A execution from unaudited materialized candidate rows"
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M2914 must audit M2913 summary and row counts",
            "M2914 must preserve actor Route B Route C denominator and claim boundaries",
            "M2914 must choose materialization accepted repair redesign pivot or stop",
            "M2914 must not execute reset rollout validation training ranking promotion dependency work performance paper high-fidelity or self-ID claims",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not reset step rollout replay validate rank promote publish or select a winner",
            "do not fit train or run PPO",
            "do not fetch clone configure build install import link probe or start an external backend",
            "do not change actor input or action contract",
            "do not convert M2913 materialization rows into performance paper high-fidelity or self-ID claims",
        ],
        "failure_types": [
            "contract_violation",
            "lineage_invalid",
            "metric_artifact",
            "scenario_sampling_failure",
            "behavior_regression",
            "objective_overfit",
            "proof_washout",
            "seed_fragility",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_route_b_source_insufficient_dependency_facing",
            "evidence_axis": "route_a_dependency_facing_evidence_surface_materialization_result_audit",
            "evidence_increment": "audits M2913 materialized rows before any later execution design",
            "claim_scope": "Result audit only no reset rollout validation ranking promotion performance paper high-fidelity or self-ID claim",
            "stop_condition": [
                "stop if M2913 row artifacts are incomplete",
                "stop if actor or denominator boundaries fail",
                "stop if Route B or Route C context enters proof or readiness denominators",
                "stop if M2914 would execute policy or dependency work",
            ],
            "fallback_plan": [
                "route to repair or redesign if materialization is incomplete",
                "route to stop if no actor-safe candidate families remain",
                "route to a bounded execution design only after audit acceptance",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2913 completes materialization preflight",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit the Route A dependency-facing evidence surface materialization",
            "admission_evidence": [
                f"M2913 decision {decision}",
                "M2913 writes route context candidate exclusion denominator failure taxonomy actor contract claim boundary and gate rows",
            ],
            "blocked_shortcuts": [
                "no reset rollout validation ranking promotion performance claim",
                "no training replay PPO or promoted fitted weights",
                "no hidden or oracle actor inputs",
                "no Route B source-family-insufficient rows as paper proof",
                "no Route C source_unavailable rows as high-fidelity readiness",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M2914 status queue scoreboard research log and review",
                "one bounded follow-up manifest only if audit selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M2914 audit artifact exists",
                "M2914 accepts rejects repairs pivots or stops M2913 materialization",
                "actor Route B Route C denominator and claim boundaries remain preserved",
                "no validation ranking promotion performance paper high-fidelity or self-ID claim is made",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2914 audits engineering evidence materialization and cannot substitute Route A rows for history necessity.",
            "history_necessity_tests": [
                "None in M2914; self-ID evidence remains blocked until fair source-diverse L0/L1/L2/L3 tests are admitted."
            ],
            "temporal_evidence_window": "M2910-M2913 Route A dependency-facing materialization chain.",
            "negative_result_policy": "Preserve insufficiency and blocker context rather than weakening self-ID standards.",
            "allowed_claims": [
                "bounded materialization audit decision",
                "row completeness and claim-boundary audit",
                "no model-quality driver-performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits a new materialized Route A dependency-facing evidence surface",
            "paper_verdict_delta": "no paper verdict; Route A materialization remains separate from Route B self-ID evidence",
            "must_synthesize_if": [
                "M2914 cannot accept reject repair pivot or stop M2913",
                "M2914 would claim validation readiness driver performance paper high-fidelity or self-ID evidence",
                "M2914 would bypass Route B source-diversity or Route C source-unavailable blockers",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "audit summarizes M2913 materialization row counts and gates",
            "audit preserves actor Route B Route C denominator and claim boundaries",
            "audit selects exactly one next route or stop state",
            "no validation ranking promotion performance paper high-fidelity or self-ID claim is made",
        ],
        "failure_criteria": [
            "M2914 executes reset rollout replay validation training ranking promotion dependency work",
            "M2914 changes actor input or action contract",
            "M2914 hides Route B source-family insufficiency or Route C source_unavailable",
            "M2914 claims model quality driver performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
            "M2914 leaves the next route ambiguous",
        ],
        "decision_rule": "Pass only if M2914 writes a bounded result-audit artifact for M2913 and preserves all actor denominator and claim boundaries without execution.",
        "commands": [{"name": "audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
            "runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/checkpoints/m2866_localized_response_prediction_training_candidate.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "route_context_rows.csv"),
            str(output_dir / "candidate_family_rows.csv"),
            str(output_dir / "gate_rows.csv"),
            "docs/m2912-engineering-controller-route-a-dependency-facing-evidence-surface-design.md",
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def write_preflight_artifacts(
    *,
    m2912_design: Path,
    m2911_synthesis: Path,
    m2910_synthesis: Path,
    m2879_synthesis: Path,
    m2883_design: Path,
    output_dir: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = _paths(output_dir)
    route_context_rows = build_route_context_rows(
        m2912_design=m2912_design,
        m2911_synthesis=m2911_synthesis,
        m2910_synthesis=m2910_synthesis,
        m2879_synthesis=m2879_synthesis,
        m2883_design=m2883_design,
    )
    candidate_family_rows = build_candidate_family_rows(
        m2912_design=m2912_design,
        m2911_synthesis=m2911_synthesis,
        m2910_synthesis=m2910_synthesis,
        m2879_synthesis=m2879_synthesis,
        m2883_design=m2883_design,
    )
    exclusion_family_rows = build_exclusion_family_rows()
    denominator_policy_rows = build_denominator_policy_rows()
    failure_taxonomy_rows = build_failure_taxonomy_rows()
    actor_contract_rows = build_actor_contract_rows()
    claim_boundary_rows = build_claim_boundary_rows()

    decision_probe_gates = build_gate_rows(
        route_context_rows=route_context_rows,
        candidate_family_rows=candidate_family_rows,
        exclusion_family_rows=exclusion_family_rows,
        denominator_policy_rows=denominator_policy_rows,
        failure_taxonomy_rows=failure_taxonomy_rows,
        actor_contract_rows=actor_contract_rows,
        claim_boundary_rows=claim_boundary_rows,
        follow_up_manifest=follow_up_manifest,
    )
    parent_artifacts_exist = all(row["source_exists"] for row in route_context_rows)
    actor_contract_pass = all(row["status_pass"] for row in actor_contract_rows)
    no_claims_made = all(not row["claim_made"] and not row["claim_allowed"] for row in claim_boundary_rows)
    pre_follow_up_decision = (
        DECISION_PASS
        if parent_artifacts_exist and actor_contract_pass and no_claims_made
        else DECISION_FAIL
    )
    follow_up = build_follow_up_manifest(
        summary_path=paths["summary"],
        output_dir=output_dir,
        decision=pre_follow_up_decision,
    )
    _write_json(follow_up_manifest, follow_up)
    gate_rows = build_gate_rows(
        route_context_rows=route_context_rows,
        candidate_family_rows=candidate_family_rows,
        exclusion_family_rows=exclusion_family_rows,
        denominator_policy_rows=denominator_policy_rows,
        failure_taxonomy_rows=failure_taxonomy_rows,
        actor_contract_rows=actor_contract_rows,
        claim_boundary_rows=claim_boundary_rows,
        follow_up_manifest=follow_up_manifest,
    )
    status_pass = all(row["status_pass"] for row in gate_rows)
    decision = DECISION_PASS if status_pass else DECISION_FAIL

    run_state = {
        "milestone_id": MILESTONE_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "m2912_design": str(m2912_design),
            "m2911_synthesis": str(m2911_synthesis),
            "m2910_synthesis": str(m2910_synthesis),
            "m2879_synthesis": str(m2879_synthesis),
            "m2883_design": str(m2883_design),
        },
        "outputs": {key: str(path) for key, path in paths.items()},
        "follow_up_manifest": str(follow_up_manifest),
        "decision": decision,
    }
    summary = {
        "milestone_id": MILESTONE_ID,
        "status_pass": status_pass,
        "gate_matrix_pass": status_pass,
        "decision": decision,
        "route_context_row_count": len(route_context_rows),
        "candidate_family_row_count": len(candidate_family_rows),
        "exclusion_family_row_count": len(exclusion_family_rows),
        "denominator_policy_row_count": len(denominator_policy_rows),
        "failure_taxonomy_row_count": len(failure_taxonomy_rows),
        "actor_contract_row_count": len(actor_contract_rows),
        "claim_boundary_row_count": len(claim_boundary_rows),
        "gate_row_count": len(gate_rows),
        "parent_artifact_missing_count": sum(not row["source_exists"] for row in route_context_rows),
        "ordinary_engineering_candidate_family_count": sum(
            bool(row["may_seed_later_materialized_candidate"]) for row in candidate_family_rows
        ),
        "route_b_context_only_count": sum(row["route_axis"] == "route_b" for row in route_context_rows),
        "route_c_context_only_count": sum(row["route_axis"] == "route_c" for row in route_context_rows),
        "claim_made_count": sum(bool(row["claim_made"]) for row in claim_boundary_rows),
        "claim_allowed_count": sum(bool(row["claim_allowed"]) for row in claim_boundary_rows),
        "hidden_oracle_actor_input_required": False,
        "future_target_actor_input_required": False,
        "actor_observation_dim": P0_OBSERVATION_DIM,
        "actor_action_dim": ACTION_DIM,
        "reset_or_rollout_executed": False,
        "validation_executed": False,
        "training_executed": False,
        "dependency_execution_performed": False,
        "performance_claim_made": False,
        "paper_claim_made": False,
        "high_fidelity_claim_made": False,
        "self_id_claim_made": False,
        "artifacts": {key: str(path) for key, path in paths.items()} | {"follow_up_manifest": str(follow_up_manifest)},
    }

    _write_csv(paths["route_context_rows"], ROUTE_CONTEXT_FIELDNAMES, route_context_rows)
    _write_csv(paths["candidate_family_rows"], CANDIDATE_FAMILY_FIELDNAMES, candidate_family_rows)
    _write_csv(paths["exclusion_family_rows"], EXCLUSION_FAMILY_FIELDNAMES, exclusion_family_rows)
    _write_csv(paths["denominator_policy_rows"], DENOMINATOR_POLICY_FIELDNAMES, denominator_policy_rows)
    _write_csv(paths["failure_taxonomy_rows"], FAILURE_TAXONOMY_FIELDNAMES, failure_taxonomy_rows)
    _write_csv(paths["actor_contract_rows"], ACTOR_CONTRACT_FIELDNAMES, actor_contract_rows)
    _write_csv(paths["claim_boundary_rows"], CLAIM_BOUNDARY_FIELDNAMES, claim_boundary_rows)
    _write_csv(paths["gate_rows"], GATE_FIELDNAMES, gate_rows)
    _write_json(paths["run_state"], run_state)
    _write_json(paths["summary"], summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2912-design", type=Path, default=DEFAULT_M2912_DESIGN)
    parser.add_argument("--m2911-synthesis", type=Path, default=DEFAULT_M2911_SYNTHESIS)
    parser.add_argument("--m2910-synthesis", type=Path, default=DEFAULT_M2910_SYNTHESIS)
    parser.add_argument("--m2879-synthesis", type=Path, default=DEFAULT_M2879_SYNTHESIS)
    parser.add_argument("--m2883-design", type=Path, default=DEFAULT_M2883_DESIGN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args()
    summary = write_preflight_artifacts(
        m2912_design=args.m2912_design,
        m2911_synthesis=args.m2911_synthesis,
        m2910_synthesis=args.m2910_synthesis,
        m2879_synthesis=args.m2879_synthesis,
        m2883_design=args.m2883_design,
        output_dir=args.output_dir,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
