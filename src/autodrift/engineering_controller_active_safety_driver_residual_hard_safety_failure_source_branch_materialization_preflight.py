"""Materialize M3164 residual hard-safety failure-source branch artifacts."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state


MILESTONE_ID = (
    "m3164-engineering-controller-active-safety-driver-residual-hard-safety-"
    "failure-source-branch-materialization-preflight"
)
NEXT_ID = "m3165-engineering-controller-active-safety-driver-residual-hard-safety-failure-source-branch-result-audit"
M3163_ID = "m3163-engineering-controller-active-safety-driver-route-a-public-deployable-validation-result-synthesis"
M3161_ID = "m3161-engineering-controller-active-safety-driver-route-a-public-deployable-validation-execution-preflight"
M3156_ID = "m3156-engineering-controller-active-safety-driver-route-a-deployable-benchmark-pack-materialization-preflight"
M3153_ID = (
    "m3153-engineering-controller-active-safety-driver-residual-action-delta-"
    "counterfactual-replay-diagnostic-materialization-preflight"
)

DEFAULT_M3163_SYNTHESIS = Path(f"docs/{M3163_ID}.md")
DEFAULT_M3161_DIR = Path(
    "runs/m3161_engineering_controller_active_safety_driver_route_a_public_deployable_"
    "validation_execution_preflight"
)
DEFAULT_M3156_DIR = Path(
    "runs/m3156_engineering_controller_active_safety_driver_route_a_deployable_benchmark_pack_"
    "materialization_preflight"
)
DEFAULT_M3153_DIR = Path(
    "runs/m3153_engineering_controller_active_safety_driver_residual_action_delta_counterfactual_"
    "replay_diagnostic_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3164_engineering_controller_active_safety_driver_residual_hard_safety_"
    "failure_source_branch_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_VALIDATION_ROWS = 64
EXPECTED_SUCCESS_ROWS = 57
EXPECTED_COLLISION_ROWS = 5
EXPECTED_OFFTRACK_ROWS = 2
EXPECTED_SPEED_TOO_LOW_ROWS = 0
EXPECTED_RESIDUAL_BLOCKERS = 7
EXPECTED_M3153_COMPARISONS = 21

CLAIM_SCOPE = (
    "M3164 Active Safety Driver residual hard-safety failure-source branch materialization only; "
    "M3163 synthesis, M3161 public deployable validation execution rows, M3156 known-failure "
    "taxonomy rows, and M3153 negative action-delta replay diagnostics may be converted into "
    "branch-pack, failure-source, route, claim-boundary, gate, doc, and M3165 audit artifacts. "
    "No reset, step, rollout, replay, fitting, PPO, training, repair implementation, validation "
    "execution, ranking, winner selection, checkpoint mutation, checkpoint promotion, "
    "driver-performance verdict, current-sim verdict, repair success, robustness-result, "
    "high-fidelity validation, paper evidence, finite-window-vs-GRU evidence, full ideal driver "
    "completion, feasibility proof, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair implementation, validation result, driver-performance verdict, current-sim verdict, "
    "robustness-result, repair success, feasibility proof, checkpoint ranking, winner selection, "
    "checkpoint promotion, high-fidelity validation readiness or result, paper evidence, "
    "finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification"
)

FAILURE_SOURCE_FIELDNAMES = [
    "failure_source_row_id",
    "source_blocker_id",
    "validation_episode_id",
    "source_measurement_episode_id",
    "fresh_panel_row_id",
    "axis_id",
    "binding_role",
    "task_family",
    "eval_seed",
    "blocker_family",
    "candidate_terminal",
    "baseline_terminal",
    "same_case_m3105_match",
    "same_case_improvement_claim_made",
    "min_clearance_margin",
    "high_sideslip_fraction",
    "lateral_rmse",
    "speed_mean",
    "m3153_comparison_count",
    "m3153_action_channel_sensitive_count",
    "m3153_terminal_invariant",
    "failure_source_label",
    "next_evidence_axis",
    "actor_contract",
    "repair_success_claim_made",
    "claim_boundary",
]
BRANCH_ROUTE_FIELDNAMES = [
    "branch_route_id",
    "route_name",
    "route_role",
    "required_before_repair",
    "allowed_actor_inputs",
    "forbidden_actor_inputs",
    "source_rows_required",
    "expected_output_artifacts",
    "overfit_guard",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3164",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
GATE_FIELDNAMES = ["gate_id", "gate_family", "status_pass", "observed", "expected", "failure_type", "claim_boundary"]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "failure_source_rows": output_dir / "failure_source_rows.csv",
        "branch_route_rows": output_dir / "branch_route_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3163_synthesis: Path, m3161_dir: Path, m3156_dir: Path, m3153_dir: Path) -> dict[str, Any]:
    paths = {
        "m3163_synthesis": m3163_synthesis,
        "m3161_summary": m3161_dir / "validation_execution_summary.json",
        "m3161_known_failure_rows": m3161_dir / "known_failure_validation_rows.csv",
        "m3161_same_case_rows": m3161_dir / "same_case_comparison_rows.csv",
        "m3161_gate_rows": m3161_dir / "gate_matrix.csv",
        "m3156_summary": m3156_dir / "summary.json",
        "m3156_failure_rows": m3156_dir / "known_failure_taxonomy_rows.csv",
        "m3156_gate_rows": m3156_dir / "gate_matrix.csv",
        "m3153_summary": m3153_dir / "summary.json",
        "m3153_comparison_rows": m3153_dir / "counterfactual_replay_comparison_rows.csv",
        "m3153_gate_rows": m3153_dir / "gate_matrix.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3163_synthesis_text": paths["m3163_synthesis"].read_text(encoding="utf-8") if exists["m3163_synthesis"] else "",
        "m3161_summary": read_json(paths["m3161_summary"]) if exists["m3161_summary"] else {},
        "m3161_known_failure_rows": read_csv_rows(paths["m3161_known_failure_rows"]),
        "m3161_same_case_rows": read_csv_rows(paths["m3161_same_case_rows"]),
        "m3161_gate_rows": read_csv_rows(paths["m3161_gate_rows"]),
        "m3156_summary": read_json(paths["m3156_summary"]) if exists["m3156_summary"] else {},
        "m3156_failure_rows": read_csv_rows(paths["m3156_failure_rows"]),
        "m3156_gate_rows": read_csv_rows(paths["m3156_gate_rows"]),
        "m3153_summary": read_json(paths["m3153_summary"]) if exists["m3153_summary"] else {},
        "m3153_comparison_rows": read_csv_rows(paths["m3153_comparison_rows"]),
        "m3153_gate_rows": read_csv_rows(paths["m3153_gate_rows"]),
    }


def _by_measurement(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {str(row.get("source_measurement_episode_id", "")): row for row in rows}


def _m3153_counts(rows: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("source_measurement_episode_id", ""))].append(row)
    for measurement_id, group in grouped.items():
        sensitive_count = sum(1 for row in group if _bool(row.get("action_channel_sensitive_diagnostic", False)))
        invariant_count = sum(1 for row in group if str(row.get("counterfactual_diagnostic_label", "")) == "counterfactual_terminal_outcome_unchanged_diagnostic")
        output[measurement_id] = {
            "comparison_count": len(group),
            "action_channel_sensitive_count": sensitive_count,
            "terminal_invariant": invariant_count == len(group) and bool(group),
        }
    return output


def _failure_source_label(blocker_family: str, clearance: float, sideslip_fraction: float, lateral_rmse: float) -> str:
    if blocker_family == "collision" and clearance < 0.0:
        return "negative_clearance_collision_preserved_under_action_delta_variants"
    if blocker_family == "offtrack" and (sideslip_fraction >= 0.2 or lateral_rmse >= 2.0):
        return "boundary_recovery_stability_failure_preserved_under_action_delta_variants"
    if blocker_family == "collision":
        return "collision_terminal_preserved_under_action_delta_variants"
    if blocker_family == "offtrack":
        return "offtrack_terminal_preserved_under_action_delta_variants"
    return "residual_hard_safety_terminal_preserved_under_action_delta_variants"


def _next_axis(blocker_family: str, axis_id: str) -> str:
    if blocker_family == "collision":
        return "actor_visible_observation_timeline_and_collision_clearance_source_localization"
    if blocker_family == "offtrack":
        return "actor_visible_boundary_recovery_stability_source_localization"
    if "offtrack" in axis_id:
        return "actor_visible_boundary_recovery_stability_source_localization"
    return "actor_visible_residual_hard_safety_source_localization"


def failure_source_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    known_rows = list(source.get("m3161_known_failure_rows", []))
    taxonomy_by_measurement = _by_measurement(list(source.get("m3156_failure_rows", [])))
    same_case_by_measurement = _by_measurement(list(source.get("m3161_same_case_rows", [])))
    action_delta_by_measurement = _m3153_counts(list(source.get("m3153_comparison_rows", [])))
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(known_rows, start=1):
        measurement_id = str(row.get("source_measurement_episode_id", ""))
        taxonomy = taxonomy_by_measurement.get(measurement_id, {})
        same_case = same_case_by_measurement.get(measurement_id, {})
        action_delta = action_delta_by_measurement.get(measurement_id, {})
        blocker_family = str(row.get("candidate_blocker_family") or row.get("source_blocker_family") or taxonomy.get("blocker_family", ""))
        clearance = _float(taxonomy.get("min_clearance_margin", same_case.get("candidate_min_clearance_margin", "")))
        sideslip_fraction = _float(taxonomy.get("high_sideslip_fraction", ""))
        lateral_rmse = _float(taxonomy.get("lateral_rmse", ""))
        axis_id = str(row.get("axis_id") or taxonomy.get("axis_id", ""))
        comparison_count = int(action_delta.get("comparison_count", taxonomy.get("m3153_comparison_count", 0) or 0))
        sensitive_count = int(action_delta.get("action_channel_sensitive_count", taxonomy.get("m3153_action_channel_sensitive_count", 0) or 0))
        terminal_invariant = bool(action_delta.get("terminal_invariant", _bool(taxonomy.get("m3153_terminal_invariant", False))))
        rows.append(
            {
                "failure_source_row_id": f"m3164-failure-source-{index:04d}",
                "source_blocker_id": row.get("source_blocker_id", ""),
                "validation_episode_id": row.get("validation_episode_id", ""),
                "source_measurement_episode_id": measurement_id,
                "fresh_panel_row_id": row.get("fresh_panel_row_id", ""),
                "axis_id": axis_id,
                "binding_role": row.get("binding_role") or taxonomy.get("binding_role", ""),
                "task_family": row.get("task_family") or taxonomy.get("task_family", ""),
                "eval_seed": row.get("eval_seed") or taxonomy.get("eval_seed", ""),
                "blocker_family": blocker_family,
                "candidate_terminal": row.get("candidate_terminal", ""),
                "baseline_terminal": row.get("baseline_terminal", ""),
                "same_case_m3105_match": _bool(row.get("blocker_preserved", False)) and _bool(row.get("termination_reason_match", False)),
                "same_case_improvement_claim_made": False,
                "min_clearance_margin": clearance,
                "high_sideslip_fraction": sideslip_fraction,
                "lateral_rmse": lateral_rmse,
                "speed_mean": _float(taxonomy.get("speed_mean", "")),
                "m3153_comparison_count": comparison_count,
                "m3153_action_channel_sensitive_count": sensitive_count,
                "m3153_terminal_invariant": terminal_invariant,
                "failure_source_label": _failure_source_label(blocker_family, clearance, sideslip_fraction, lateral_rmse),
                "next_evidence_axis": _next_axis(blocker_family, axis_id),
                "actor_contract": "actor_visible_obs72_to_direct_action3",
                "repair_success_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def branch_route_rows() -> list[dict[str, Any]]:
    specs = [
        (
            "residual_row_accountability",
            "branch_entry_guard",
            True,
            "obs72 history ego response actuator state scene geometry previous commands",
            "hidden dynamics oracle labels TTC reference trajectory target source route outcome progress verdict labels",
            "7 residual blocker rows plus M3161 same-case rows",
            "failure_source_rows.csv|gate_matrix.csv",
            "all residual rows must remain visible and cannot be averaged away",
        ),
        (
            "observation_timeline_source_localization",
            "next_evidence_axis_candidate",
            True,
            "actor-visible obs72 slices and existing row metadata for diagnostic only",
            "future outcome labels as actor inputs or route labels as actor inputs",
            "collision residual rows with negative clearance and terminal-invariant action-delta diagnostics",
            "timeline_source_rows.csv|source_axis_gate_matrix.csv",
            "must not tune the driver on the seven rows before audit",
        ),
        (
            "boundary_recovery_stability_source_localization",
            "next_evidence_axis_candidate",
            True,
            "actor-visible obs72 slices and existing stability metrics for diagnostic only",
            "hidden slip tire-force labels or simulator-private dynamics as actor inputs",
            "offtrack residual rows with sideslip or lateral-RMSE stress",
            "boundary_recovery_source_rows.csv|source_axis_gate_matrix.csv",
            "must preserve same-case comparison against M3105",
        ),
        (
            "local_action_delta_tuning",
            "blocked_route",
            False,
            "none for M3164",
            "unbounded gain retuning on fixed residual rows",
            "M3153 0 of 21 action-channel-sensitive comparisons",
            "synthesis_required_before_reopen",
            "blocked unless a new source-localization artifact changes the evidence axis",
        ),
    ]
    return [
        {
            "branch_route_id": f"m3164-branch-route-{index:04d}",
            "route_name": name,
            "route_role": role,
            "required_before_repair": required,
            "allowed_actor_inputs": allowed,
            "forbidden_actor_inputs": forbidden,
            "source_rows_required": source_rows,
            "expected_output_artifacts": output_artifacts,
            "overfit_guard": guard,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (name, role, required, allowed, forbidden, source_rows, output_artifacts, guard) in enumerate(specs, start=1)
    ]


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("failure_source_rows", "branch_pack", True, "failure_source_rows.csv"),
        ("branch_route_rows", "branch_pack", True, "branch_route_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3165 audit manifest"),
    ]
    blocked = [
        ("environment_reset", "execution", "future pre-registered execution route"),
        ("environment_step", "execution", "future pre-registered execution route"),
        ("policy_rollout", "execution", "future pre-registered execution route"),
        ("driver_mutation", "repair", "future pre-registered repair materialization"),
        ("validation_result", "validation", "future validation execution plus audit"),
        ("driver_performance_verdict", "driver_performance", "future proof/generalization/claim audit"),
        ("current_sim_verdict", "verdict", "future result audit and synthesis"),
        ("robustness_result", "verdict", "future robustness verification route"),
        ("repair_success", "verdict", "future repair measurement audit"),
        ("checkpoint_ranking", "ranking", "future audited ranking route"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("high_fidelity_validation", "validation", "future Route C HF validation"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("finite_window_vs_gru_result", "paper", "future same-case architecture comparison"),
        ("full_ideal_driver_completion", "full_goal", "future full goal gate"),
        ("feasibility_proof", "proof", "future feasibility proof route"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("hidden_oracle_actor_inputs", "contract", "actor contract forbids hidden/oracle inputs"),
        ("ttc_actor_inputs", "contract", "actor contract forbids TTC shortcuts"),
        ("runtime_base_policy_dependency", "contract", "public deployable reflex forbids runtime base policy use"),
    ]
    rows = [
        {
            "claim_id": f"m3164-{claim_id}",
            "claim_family": family,
            "allowed_in_m3164": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3164-{claim_id}",
            "claim_family": family,
            "allowed_in_m3164": False,
            "claim_made": False,
            "status_pass": True,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, evidence in blocked
    )
    return rows


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "baseline_checkpoints": [str(output_dir / "summary.json"), str(doc_path)],
        "commands": [
            {
                "command": "true",
                "name": "active_safety_driver_residual_hard_safety_failure_source_branch_result_audit_doc",
            }
        ],
        "decision_rule": "Pass only if M3165 audits M3164 branch-pack artifacts and selects one next source-localization diagnostic or repair-admission route without overclaiming.",
        "failure_criteria": [
            "M3165 hides M3164 residual rows or missing artifacts",
            "M3165 treats M3164 branch pack as repair success or performance verdict",
            "M3165 leaves the next route ambiguous",
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
        "forbidden_shortcuts": [
            "do not rerun tune rank promote validate or mutate checkpoints",
            "do not convert M3164 branch-pack rows into validation performance current-sim high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claims",
            "do not change actor input or action contract",
        ],
        "gate_tier": "process",
        "hypothesis": "A bounded result audit can accept or reject M3164 residual hard-safety failure-source branch artifacts before any repair validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper or self-ID claim.",
        "id": NEXT_ID,
        "lineage": {
            "blocked_by": [
                "M3164 branch-pack artifacts require audit before source-localization or repair-admission work",
                "M3164 is branch materialization not repair evidence",
            ],
            "derived_from": [MILESTONE_ID, M3163_ID, M3161_ID, M3156_ID, M3153_ID],
            "invalidates": [],
            "parent_checkpoint": [str(doc_path)],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "failure_source_rows.csv"),
                str(output_dir / "branch_route_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_objective": ["audit residual hard-safety failure-source branch pack"],
            "supersedes": ["direct repair-admission from M3163 synthesis without M3164 branch-pack audit"],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "evidence_expansion": "audits new residual failure-source branch-pack artifacts before repair",
            "local_search_risk": "medium",
            "must_synthesize_if": [
                "M3165 cannot accept M3164 as complete and claim-safe",
                "M3165 cannot select one source-localization diagnostic or repair-admission route",
            ],
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3165 audits engineering branch admission",
            "process_overhead": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
        },
        "next_blocker": NEXT_ID,
        "priority": 31650,
        "private_holdout_policy": "not_used",
        "promotion_decision": "not_applicable",
        "public_gates": [
            "M3165 must audit M3164 summary failure-source branch-route claim and gate artifacts",
            "M3165 must preserve obs72/action3 direct [steer throttle brake] contract and residual blocker disclosure",
            "M3165 must reject validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3165 must select exactly one next route or stop state",
        ],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "self_id_evidence_discipline": {
            "allowed_claims": [
                "M3164 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3165 audits engineering branch-pack artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3165; self-ID and GRU comparisons remain auxiliary diagnostics only."],
            "negative_result_policy": "Preserve residual blocker evidence and route to engineering source-localization rather than returning self-ID to the mainline objective.",
            "temporal_evidence_window": "M3164 branch-pack artifacts only.",
        },
        "status": "pending",
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3165 audits M3164 branch-pack artifacts and claim boundaries",
            "M3165 selects exactly one next route or stop state",
        ],
        "training_stage": {
            "admission_evidence": ["M3164 summary failure-source branch-route claim and gate artifacts"],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3165 status queue scoreboard research log and review",
                "one follow-up manifest only if M3165 selects exactly one next route",
            ],
            "blocked_shortcuts": [
                "no validation execution ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "next_stage_criteria": [
                "M3165 accepts or rejects M3164 as complete and claim-safe",
                "M3165 selects source-localization diagnostic repair-admission synthesis or stop explicitly",
            ],
            "stage": "process",
            "stage_objective": "Audit M3164 residual hard-safety failure-source branch artifacts",
        },
        "type": "gate",
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_hard_safety_failure_source_resolution",
            "claim_scope": "Result audit only; no repair validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "evidence_axis": "residual_hard_safety_failure_source_branch_result_audit",
            "evidence_increment": "audits M3164 residual failure-source branch-pack artifacts",
            "fallback_plan": [
                "route to M3164 artifact repair if branch-pack artifacts are incomplete",
                "route to source-localization diagnostic if M3164 is complete and claim-safe",
                "synthesize if M3165 cannot select one next route",
            ],
            "stop_condition": [
                "stop if M3164 artifacts are missing or gate matrix fails",
                "stop if actor or direct-action contracts were violated",
                "stop if next route would require hidden or oracle actor inputs",
            ],
            "synthesis_cadence": 10,
            "synthesis_decision": "not_applicable",
            "synthesis_trigger": "M3164 completes residual hard-safety failure-source branch-pack materialization",
        },
    }


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m3164-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def required_artifacts_present(paths: Mapping[str, Path]) -> bool:
    late_written = {"summary", "gate_matrix", "doc", "run_state"}
    return all(path.exists() for key, path in paths.items() if key not in late_written)


def gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    failure_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    synthesis_text = str(source.get("m3163_synthesis_text", ""))
    m3161_summary = source.get("m3161_summary", {})
    m3156_summary = source.get("m3156_summary", {})
    m3153_summary = source.get("m3153_summary", {})
    blocker_counts = Counter(str(row.get("blocker_family", "")) for row in failure_rows)
    route_names = {str(row.get("route_name", "")) for row in route_rows}
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3163_pivots_to_m3164", "lineage", "pivot_to_m3164_residual_hard_safety_failure_source_branch_materialization" in synthesis_text, "route marker", "present", "lineage_invalid"),
        gate("m3161_status_pass", "lineage", _bool(m3161_summary.get("status_pass", False)), m3161_summary.get("status_pass"), True, "lineage_invalid"),
        gate("m3161_gate_matrix_pass", "lineage", _bool(m3161_summary.get("gate_matrix_pass", False)), m3161_summary.get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3156_status_pass", "lineage", _bool(m3156_summary.get("status_pass", False)), m3156_summary.get("status_pass"), True, "lineage_invalid"),
        gate("m3153_status_pass", "lineage", _bool(m3153_summary.get("status_pass", False)), m3153_summary.get("status_pass"), True, "lineage_invalid"),
        gate("validation_denominator_rows", "validation", int(m3161_summary.get("validation_episode_row_count", 0)) == EXPECTED_VALIDATION_ROWS, m3161_summary.get("validation_episode_row_count"), EXPECTED_VALIDATION_ROWS, "metric_artifact"),
        gate("validation_success_count_preserved", "validation", int(m3161_summary.get("validation_success_count", 0)) == EXPECTED_SUCCESS_ROWS, m3161_summary.get("validation_success_count"), EXPECTED_SUCCESS_ROWS, "metric_artifact"),
        gate("failure_source_rows", "known_failures", len(failure_rows) == EXPECTED_RESIDUAL_BLOCKERS, len(failure_rows), EXPECTED_RESIDUAL_BLOCKERS, "metric_artifact"),
        gate("collision_blockers", "known_failures", blocker_counts.get("collision", 0) == EXPECTED_COLLISION_ROWS, dict(sorted(blocker_counts.items())), EXPECTED_COLLISION_ROWS, "metric_artifact"),
        gate("offtrack_blockers", "known_failures", blocker_counts.get("offtrack", 0) == EXPECTED_OFFTRACK_ROWS, dict(sorted(blocker_counts.items())), EXPECTED_OFFTRACK_ROWS, "metric_artifact"),
        gate("speed_too_low_blockers", "known_failures", blocker_counts.get("speed_too_low", 0) == EXPECTED_SPEED_TOO_LOW_ROWS, dict(sorted(blocker_counts.items())), EXPECTED_SPEED_TOO_LOW_ROWS, "metric_artifact"),
        gate("same_case_match_not_improvement", "comparison", all(_bool(row.get("same_case_m3105_match", False)) and not _bool(row.get("same_case_improvement_claim_made", True)) for row in failure_rows), "all rows", "match true and improvement claim false", "proof_washout"),
        gate("m3153_negative_action_delta_preserved", "negative_replay", sum(int(row.get("m3153_comparison_count", 0)) for row in failure_rows) == EXPECTED_M3153_COMPARISONS and sum(int(row.get("m3153_action_channel_sensitive_count", 0)) for row in failure_rows) == 0, (sum(int(row.get("m3153_comparison_count", 0)) for row in failure_rows), sum(int(row.get("m3153_action_channel_sensitive_count", 0)) for row in failure_rows)), (EXPECTED_M3153_COMPARISONS, 0), "metric_artifact"),
        gate("new_evidence_axis_present", "route", {"observation_timeline_source_localization", "boundary_recovery_stability_source_localization"}.issubset(route_names), sorted(route_names), "source localization routes present", "objective_overfit"),
        gate("local_action_delta_blocked", "route", any(row.get("route_name") == "local_action_delta_tuning" and not _bool(row.get("required_before_repair", True)) for row in route_rows), "blocked route row", "present", "objective_overfit"),
        gate("claim_boundary_pass", "claim", all(_bool(row.get("status_pass", False)) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("no_repair_success_claim", "claim", not any(_bool(row.get("repair_success_claim_made", False)) for row in failure_rows), "all rows", False, "proof_washout"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def render_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3164 Residual Hard-Safety Failure-Source Branch Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- failure-source rows: {summary['failure_source_row_count']}",
            f"- branch-route rows: {summary['branch_route_row_count']}",
            f"- claim-boundary rows: {summary['claim_boundary_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            f"- collision blockers: {summary['collision_blocker_count']}",
            f"- offtrack blockers: {summary['offtrack_blocker_count']}",
            f"- M3153 action-channel-sensitive comparisons: {summary['m3153_action_channel_sensitive_comparison_count']}",
            "",
            "## Interpretation",
            "",
            "M3164 materializes the new residual hard-safety branch selected by M3163. It preserves every M3161 known-failure row, links each row to the M3156 failure taxonomy and M3153 negative action-delta replay diagnostics, and records allowed next evidence axes before any driver mutation.",
            "",
            "The branch pack explicitly blocks returning to unbounded local action-delta tuning on the same seven residual rows. The next admissible route must first audit this pack and then choose source-localization diagnostics or a separately pre-registered repair-admission path.",
            "",
            "M3164 does not execute validation, reset or step the environment, replay rollouts, tune a policy, rank a driver, promote a checkpoint, or make validation, repair-success, robustness, driver-performance, current-sim, high-fidelity, paper, full-driver, feasibility-proof, or self-ID claims.",
            "",
            "Rejected claims:",
            "",
            "```text",
            FORBIDDEN_INTERPRETATION,
            "```",
            "",
            "## Next",
            "",
            f"- next blocker: `{summary['next_blocker']}`",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            "",
        ]
    )


def run_failure_source_branch_materialization_preflight(
    *,
    m3163_synthesis: Path,
    m3161_dir: Path,
    m3156_dir: Path,
    m3153_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(m3163_synthesis=m3163_synthesis, m3161_dir=m3161_dir, m3156_dir=m3156_dir, m3153_dir=m3153_dir)
    failure_rows = failure_source_rows(source)
    route_rows = branch_route_rows()
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claim_rows = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    write_csv_rows(paths["failure_source_rows"], failure_rows, fieldnames=FAILURE_SOURCE_FIELDNAMES)
    write_csv_rows(paths["branch_route_rows"], route_rows, fieldnames=BRANCH_ROUTE_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        failure_rows=failure_rows,
        route_rows=route_rows,
        claim_rows=claim_rows,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gates)
    status_pass = bool(gate_matrix_pass and present)
    blocker_counts = Counter(str(row.get("blocker_family", "")) for row in failure_rows)
    m3161_summary = source.get("m3161_summary", {})
    summary = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_residual_hard_safety_failure_source_branch_materialization_pass"
            if status_pass
            else "active_safety_driver_residual_hard_safety_failure_source_branch_materialization_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "failure_source_row_count": len(failure_rows),
        "branch_route_row_count": len(route_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
        "validation_episode_row_count": int(m3161_summary.get("validation_episode_row_count", 0)),
        "validation_success_count": int(m3161_summary.get("validation_success_count", 0)),
        "validation_collision_count": int(m3161_summary.get("validation_collision_count", 0)),
        "validation_offtrack_count": int(m3161_summary.get("validation_offtrack_count", 0)),
        "validation_speed_too_low_count": int(m3161_summary.get("validation_speed_too_low_count", 0)),
        "collision_blocker_count": blocker_counts.get("collision", 0),
        "offtrack_blocker_count": blocker_counts.get("offtrack", 0),
        "speed_too_low_blocker_count": blocker_counts.get("speed_too_low", 0),
        "m3153_comparison_count": sum(int(row.get("m3153_comparison_count", 0)) for row in failure_rows),
        "m3153_action_channel_sensitive_comparison_count": sum(int(row.get("m3153_action_channel_sensitive_count", 0)) for row in failure_rows),
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
        "robustness_result_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "feasibility_proof_claim_made": False,
        "level3_self_id_claim_made": False,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "decision": "active_safety_driver_residual_hard_safety_failure_source_branch_materialization_route_to_m3165_result_audit",
        "next_blocker": NEXT_ID,
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "follow_up_manifest_exists": paths["follow_up_manifest"].exists(),
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(path) for key, path in paths.items()},
    }
    write_json(paths["summary"], summary)
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(render_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "failure_source_row_count": len(failure_rows),
            "branch_route_row_count": len(route_rows),
            "complete": status_pass,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3163-synthesis", type=Path, default=DEFAULT_M3163_SYNTHESIS)
    parser.add_argument("--m3161-dir", type=Path, default=DEFAULT_M3161_DIR)
    parser.add_argument("--m3156-dir", type=Path, default=DEFAULT_M3156_DIR)
    parser.add_argument("--m3153-dir", type=Path, default=DEFAULT_M3153_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_failure_source_branch_materialization_preflight(
        m3163_synthesis=args.m3163_synthesis,
        m3161_dir=args.m3161_dir,
        m3156_dir=args.m3156_dir,
        m3153_dir=args.m3153_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"failure_source_rows={summary['failure_source_row_count']}")
    print(f"branch_route_rows={summary['branch_route_row_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
