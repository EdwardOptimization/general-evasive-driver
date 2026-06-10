"""Materialize M3168 source-localized repair-admission artifacts."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state


MILESTONE_ID = (
    "m3168-engineering-controller-active-safety-driver-residual-hard-safety-"
    "source-localized-repair-admission-materialization-preflight"
)
NEXT_ID = (
    "m3169-engineering-controller-active-safety-driver-residual-hard-safety-"
    "source-localized-repair-admission-result-audit"
)
M3167_ID = (
    "m3167-engineering-controller-active-safety-driver-residual-hard-safety-"
    "source-localization-diagnostic-result-audit"
)
M3166_ID = (
    "m3166-engineering-controller-active-safety-driver-residual-hard-safety-"
    "source-localization-diagnostic-materialization-preflight"
)
M3165_ID = (
    "m3165-engineering-controller-active-safety-driver-residual-hard-safety-"
    "failure-source-branch-result-audit"
)

DEFAULT_M3167_AUDIT = Path(f"docs/{M3167_ID}.md")
DEFAULT_M3166_DIR = Path(
    "runs/m3166_engineering_controller_active_safety_driver_residual_hard_safety_"
    "source_localization_diagnostic_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3168_engineering_controller_active_safety_driver_residual_hard_safety_"
    "source_localized_repair_admission_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_SOURCE_ROWS = 7
EXPECTED_COLLISION_ROWS = 5
EXPECTED_OFFTRACK_ROWS = 2
EXPECTED_REPAIR_HYPOTHESES = 2

CLAIM_SCOPE = (
    "M3168 Active Safety Driver residual hard-safety source-localized repair-admission materialization only; "
    "M3167 audit and M3166 source-localization diagnostic artifacts may be converted into bounded "
    "implementation-admission hypotheses, actor-contract guards, measurement-readiness gates, claim-boundary, "
    "gate, doc, and M3169 audit artifacts. No reset, step, rollout, replay, policy action, fitting, PPO, "
    "training, repair implementation, validation execution, ranking, winner selection, checkpoint mutation, "
    "checkpoint promotion, driver-performance verdict, current-sim verdict, repair success, robustness-result, "
    "high-fidelity validation, paper evidence, finite-window-vs-GRU evidence, full ideal driver completion, "
    "feasibility proof, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair implementation, validation result, driver-performance verdict, current-sim verdict, "
    "robustness-result, repair success, feasibility proof, checkpoint ranking, winner selection, "
    "checkpoint promotion, high-fidelity validation readiness or result, paper evidence, "
    "finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification"
)

REPAIR_HYPOTHESIS_FIELDNAMES = [
    "repair_hypothesis_id",
    "repair_hypothesis_name",
    "blocker_family",
    "source_localization_row_count",
    "source_localization_labels",
    "admitted_for_repair_implementation_materialization",
    "admitted_for_validation",
    "allowed_actor_visible_signals",
    "forbidden_actor_inputs",
    "allowed_action_channels",
    "intended_behavior_delta",
    "implementation_boundary",
    "measurement_gate_required",
    "repair_success_claim_made",
    "claim_boundary",
]
ACTOR_CONTRACT_FIELDNAMES = [
    "actor_contract_guard_id",
    "contract_family",
    "status_pass",
    "allowed_runtime_surface",
    "forbidden_runtime_surface",
    "enforcement_before_implementation",
    "claim_boundary",
]
MEASUREMENT_READINESS_FIELDNAMES = [
    "measurement_readiness_id",
    "stage_order",
    "required_before",
    "status_pass",
    "admission_decision",
    "evidence_basis",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3168",
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


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "repair_hypothesis_rows": output_dir / "repair_hypothesis_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "measurement_readiness_rows": output_dir / "measurement_readiness_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3167_audit: Path, m3166_dir: Path) -> dict[str, Any]:
    paths = {
        "m3167_audit": m3167_audit,
        "m3166_summary": m3166_dir / "summary.json",
        "m3166_source_localization_rows": m3166_dir / "source_localization_rows.csv",
        "m3166_repair_admission_rows": m3166_dir / "repair_admission_rows.csv",
        "m3166_gate_rows": m3166_dir / "gate_matrix.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3167_audit_text": paths["m3167_audit"].read_text(encoding="utf-8") if exists["m3167_audit"] else "",
        "m3166_summary": read_json(paths["m3166_summary"]) if exists["m3166_summary"] else {},
        "m3166_source_localization_rows": read_csv_rows(paths["m3166_source_localization_rows"]),
        "m3166_repair_admission_rows": read_csv_rows(paths["m3166_repair_admission_rows"]),
        "m3166_gate_rows": read_csv_rows(paths["m3166_gate_rows"]),
    }


def _labels(rows: list[dict[str, str]]) -> str:
    return "|".join(sorted({str(row.get("source_localization_label", "")) for row in rows if row.get("source_localization_label")}))


def _group_by_family(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("blocker_family", ""))].append(row)
    return grouped


def repair_hypothesis_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    grouped = _group_by_family(list(source.get("m3166_source_localization_rows", [])))
    collision_rows = grouped.get("collision", [])
    offtrack_rows = grouped.get("offtrack", [])
    return [
        {
            "repair_hypothesis_id": "m3168-repair-hypothesis-0001",
            "repair_hypothesis_name": "collision_clearance_observation_timeline_reflex",
            "blocker_family": "collision",
            "source_localization_row_count": len(collision_rows),
            "source_localization_labels": _labels(collision_rows),
            "admitted_for_repair_implementation_materialization": len(collision_rows) == EXPECTED_COLLISION_ROWS,
            "admitted_for_validation": False,
            "allowed_actor_visible_signals": "obs72 obstacle urgency visible obstacle slots nearest obstacle body geometry road-center error ego speed prior command state",
            "forbidden_actor_inputs": "hidden dynamics oracle labels TTC reference trajectory target source route outcome progress verdict future terminal labels",
            "allowed_action_channels": "steer|throttle|brake",
            "intended_behavior_delta": "bounded earlier throttle drop brake add and obstacle-side steering moderation using actor-visible obstacle timeline only",
            "implementation_boundary": "may materialize a candidate overlay after M3169 audit; must preserve obs72-only runtime and M3105 incumbent fallback semantics until measured",
            "measurement_gate_required": "post-implementation full-fresh same-case measurement and audit before validation or performance claim",
            "repair_success_claim_made": False,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "repair_hypothesis_id": "m3168-repair-hypothesis-0002",
            "repair_hypothesis_name": "boundary_recovery_stability_reflex",
            "blocker_family": "offtrack",
            "source_localization_row_count": len(offtrack_rows),
            "source_localization_labels": _labels(offtrack_rows),
            "admitted_for_repair_implementation_materialization": len(offtrack_rows) == EXPECTED_OFFTRACK_ROWS,
            "admitted_for_validation": False,
            "allowed_actor_visible_signals": "obs72 edge urgency road-center error min actor edge margin ego speed lateral/yaw response prior command state",
            "forbidden_actor_inputs": "hidden slip tire-force dynamics oracle labels TTC reference trajectory target source route outcome progress verdict future terminal labels",
            "allowed_action_channels": "steer|throttle|brake",
            "intended_behavior_delta": "bounded throttle damping brake support and center-recovery steering moderation using actor-visible boundary/stability timeline only",
            "implementation_boundary": "may materialize a candidate overlay after M3169 audit; must preserve obs72-only runtime and M3105 incumbent fallback semantics until measured",
            "measurement_gate_required": "post-implementation full-fresh same-case measurement and audit before validation or performance claim",
            "repair_success_claim_made": False,
            "claim_boundary": CLAIM_SCOPE,
        },
    ]


def actor_contract_guard_rows() -> list[dict[str, Any]]:
    specs = [
        (
            "obs72_only_runtime_input",
            "input_contract",
            "actor-visible obs72 vector",
            "hidden oracle labels TTC reference trajectory target source route outcome progress verdict future terminal labels",
        ),
        (
            "direct_action3_output",
            "output_contract",
            "direct clipped [steer throttle brake]",
            "latent action head base-policy action route labels or target tensors at runtime",
        ),
        (
            "runtime_base_policy_forbidden",
            "runtime_dependency",
            "materialized deterministic reflex code only",
            "runtime base policy checkpoint recurrent hidden state or learned model dependency",
        ),
        (
            "diagnostic_labels_trainer_only",
            "metadata_boundary",
            "source-localization labels may inform offline implementation design",
            "source-localization failure labels as actor inputs or runtime switches keyed by row id",
        ),
    ]
    return [
        {
            "actor_contract_guard_id": f"m3168-actor-contract-guard-{index:04d}",
            "contract_family": family,
            "status_pass": True,
            "allowed_runtime_surface": allowed,
            "forbidden_runtime_surface": forbidden,
            "enforcement_before_implementation": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (guard_id, family, allowed, forbidden) in enumerate(specs, start=1)
    ]


def measurement_readiness_rows() -> list[dict[str, Any]]:
    specs = [
        (
            "m3169_audit_before_repair_materialization",
            "repair_implementation_materialization",
            "admit_audit_first",
            "M3168 can admit implementation materialization only after M3169 accepts these contract artifacts",
        ),
        (
            "repair_materialization_before_measurement",
            "full_fresh_measurement",
            "implementation_required_first",
            "no measurement or validation can run before a separately pre-registered repair implementation artifact exists",
        ),
        (
            "measurement_audit_before_performance_claim",
            "driver_performance_claim",
            "result_audit_required",
            "measurement rows require result audit and claim-boundary review before any driver-performance or repair-success interpretation",
        ),
        (
            "same_case_denominator_preserved",
            "future_measurement_spec",
            "preserve_m3105_same_case_rows",
            "future measurement must preserve the Route A same-case denominator and residual blocker disclosure",
        ),
    ]
    return [
        {
            "measurement_readiness_id": f"m3168-measurement-readiness-{index:04d}",
            "stage_order": order,
            "required_before": required_before,
            "status_pass": True,
            "admission_decision": decision,
            "evidence_basis": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (order, required_before, decision, evidence) in enumerate(specs, start=1)
    ]


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("repair_hypothesis_rows", "admission_artifact", True, "repair_hypothesis_rows.csv"),
        ("actor_contract_guard_rows", "contract_artifact", True, "actor_contract_guard_rows.csv"),
        ("measurement_readiness_rows", "process_artifact", True, "measurement_readiness_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3169 audit manifest"),
    ]
    blocked = [
        ("environment_reset", "execution", "future pre-registered execution route"),
        ("environment_step", "execution", "future pre-registered execution route"),
        ("policy_action", "execution", "future pre-registered execution route"),
        ("policy_rollout", "execution", "future pre-registered execution route"),
        ("replay_run", "execution", "future pre-registered replay route"),
        ("driver_mutation", "repair", "future post-M3169 repair materialization"),
        ("repair_implementation", "repair", "future post-M3169 repair materialization"),
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
            "claim_id": f"m3168-{claim_id}",
            "claim_family": family,
            "allowed_in_m3168": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3168-{claim_id}",
            "claim_family": family,
            "allowed_in_m3168": False,
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
                "name": "active_safety_driver_residual_hard_safety_source_localized_repair_admission_result_audit_doc",
            }
        ],
        "decision_rule": "Pass only if M3169 audits M3168 repair-admission contract artifacts and selects one repair implementation materialization artifact-repair synthesis or stop route without overclaiming.",
        "failure_criteria": [
            "M3169 hides missing M3168 rows or failed gates",
            "M3169 treats M3168 admission artifacts as repair success or performance verdict",
            "M3169 leaves the next route ambiguous",
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
            "do not convert M3168 repair-admission rows into validation performance current-sim high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claims",
            "do not change actor input or action contract",
        ],
        "gate_tier": "process",
        "hypothesis": "A bounded result audit can accept or reject M3168 source-localized repair-admission artifacts before any repair implementation validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper or self-ID claim.",
        "id": NEXT_ID,
        "lineage": {
            "blocked_by": [
                "M3168 repair-admission contract artifacts require audit before repair implementation materialization",
                "M3168 is admission materialization not repair evidence",
            ],
            "derived_from": [MILESTONE_ID, M3167_ID, M3166_ID, M3165_ID],
            "invalidates": [],
            "parent_checkpoint": [str(doc_path)],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "repair_hypothesis_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "measurement_readiness_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_objective": ["audit source-localized repair-admission contracts"],
            "supersedes": ["direct repair implementation from M3167 without M3168 admission audit"],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "evidence_expansion": "audits repair-admission contracts before driver mutation",
            "local_search_risk": "medium",
            "must_synthesize_if": [
                "M3169 cannot accept M3168 as complete and claim-safe",
                "M3169 cannot select one repair implementation materialization artifact-repair synthesis or stop route",
            ],
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3169 audits engineering repair-admission evidence",
            "process_overhead": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 0,
        },
        "next_blocker": NEXT_ID,
        "priority": 31690,
        "private_holdout_policy": "not_used",
        "promotion_decision": "not_applicable",
        "public_gates": [
            "M3169 must audit M3168 summary repair-hypothesis actor-contract measurement-readiness claim and gate artifacts",
            "M3169 must preserve obs72/action3 direct [steer throttle brake] contract and residual blocker disclosure",
            "M3169 must reject validation ranking promotion driver-performance current-sim high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3169 must select exactly one next route or stop state",
        ],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "self_id_evidence_discipline": {
            "allowed_claims": [
                "M3168 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3169 audits engineering admission artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3169; self-ID and GRU comparisons remain auxiliary diagnostics only."],
            "negative_result_policy": "Preserve residual blocker evidence and route to bounded actor-visible repair implementation only after audit.",
            "temporal_evidence_window": "M3168 repair-admission artifacts only.",
        },
        "status": "pending",
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3169 audits M3168 repair-admission artifacts and claim boundaries",
            "M3169 selects exactly one next route or stop state",
        ],
        "training_stage": {
            "admission_evidence": ["M3168 summary repair-hypothesis actor-contract measurement-readiness claim and gate artifacts"],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3169 status queue scoreboard research log and review",
                "one follow-up manifest only if M3169 selects exactly one next route",
            ],
            "blocked_shortcuts": [
                "no validation execution ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "next_stage_criteria": [
                "M3169 accepts or rejects M3168 as complete and claim-safe",
                "M3169 selects repair implementation materialization artifact-repair synthesis or stop explicitly",
            ],
            "stage": "process",
            "stage_objective": "Audit M3168 source-localized repair-admission artifacts",
        },
        "type": "gate",
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_hard_safety_failure_source_resolution",
            "claim_scope": "Result audit only; no repair validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "evidence_axis": "source_localized_repair_admission_result_audit",
            "evidence_increment": "audits M3168 repair-admission contracts before driver mutation",
            "fallback_plan": [
                "route to M3168 artifact repair if artifacts are incomplete",
                "route to repair implementation materialization if M3168 is complete and claim-safe",
                "synthesize if M3169 cannot select one next route",
            ],
            "stop_condition": [
                "stop if M3168 artifacts are missing or gate matrix fails",
                "stop if actor or direct-action contracts were violated",
                "stop if next route would require hidden or oracle actor inputs",
            ],
            "synthesis_cadence": 10,
            "synthesis_decision": "not_applicable",
            "synthesis_trigger": "M3168 completes source-localized repair-admission materialization",
        },
    }


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m3168-{gate_id}",
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
    hypothesis_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    measurement_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    audit_text = str(source.get("m3167_audit_text", ""))
    m3166_summary = source.get("m3166_summary", {})
    source_rows = list(source.get("m3166_source_localization_rows", []))
    repair_admission_rows = list(source.get("m3166_repair_admission_rows", []))
    blocker_counts = Counter(str(row.get("blocker_family", "")) for row in source_rows)
    implementation_admitted = [row for row in hypothesis_rows if _bool(row.get("admitted_for_repair_implementation_materialization", False))]
    validation_admitted = [row for row in hypothesis_rows if _bool(row.get("admitted_for_validation", False))]
    local_delta_blocked = any(
        row.get("route_name") == "local_action_delta_tuning"
        and not _bool(row.get("required_before_repair", True))
        and str(row.get("admission_decision", "")).startswith("blocked")
        for row in repair_admission_rows
    )
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3167_accepts_m3166_and_routes_m3168", "lineage", "accept_m3166_source_localization_route_to_m3168_source_localized_repair_admission_materialization" in audit_text, "M3167 route marker", "present", "lineage_invalid"),
        gate("m3166_status_pass", "lineage", _bool(m3166_summary.get("status_pass", False)), m3166_summary.get("status_pass"), True, "lineage_invalid"),
        gate("m3166_gate_matrix_pass", "lineage", _bool(m3166_summary.get("gate_matrix_pass", False)), m3166_summary.get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("source_localization_rows", "known_failures", len(source_rows) == EXPECTED_SOURCE_ROWS, len(source_rows), EXPECTED_SOURCE_ROWS, "metric_artifact"),
        gate("collision_source_rows", "known_failures", blocker_counts.get("collision", 0) == EXPECTED_COLLISION_ROWS, dict(sorted(blocker_counts.items())), EXPECTED_COLLISION_ROWS, "metric_artifact"),
        gate("offtrack_source_rows", "known_failures", blocker_counts.get("offtrack", 0) == EXPECTED_OFFTRACK_ROWS, dict(sorted(blocker_counts.items())), EXPECTED_OFFTRACK_ROWS, "metric_artifact"),
        gate("repair_hypothesis_rows", "repair_admission", len(hypothesis_rows) == EXPECTED_REPAIR_HYPOTHESES, len(hypothesis_rows), EXPECTED_REPAIR_HYPOTHESES, "metric_artifact"),
        gate("bounded_implementation_admission", "repair_admission", len(implementation_admitted) == EXPECTED_REPAIR_HYPOTHESES and not validation_admitted, (len(implementation_admitted), len(validation_admitted)), (EXPECTED_REPAIR_HYPOTHESES, 0), "objective_overfit"),
        gate("local_action_delta_blocked", "route", local_delta_blocked, "blocked local action-delta row", "present", "objective_overfit"),
        gate("actor_contract_guards_pass", "contract", actor_rows and all(_bool(row.get("status_pass", False)) for row in actor_rows), "all actor guards", "pass", "contract_violation"),
        gate("measurement_readiness_pass", "process", measurement_rows and all(_bool(row.get("status_pass", False)) for row in measurement_rows), "all measurement rows", "pass", "metric_artifact"),
        gate("claim_boundary_pass", "claim", all(_bool(row.get("status_pass", False)) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("no_repair_success_claim", "claim", not any(_bool(row.get("repair_success_claim_made", False)) for row in hypothesis_rows), "all hypothesis rows", False, "proof_washout"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def render_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3168 Residual Hard-Safety Source-Localized Repair-Admission Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- repair-hypothesis rows: {summary['repair_hypothesis_row_count']}",
            f"- actor-contract guard rows: {summary['actor_contract_guard_row_count']}",
            f"- measurement-readiness rows: {summary['measurement_readiness_row_count']}",
            f"- claim-boundary rows: {summary['claim_boundary_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            f"- source rows preserved: {summary['source_localization_row_count']}",
            f"- collision source rows: {summary['collision_source_row_count']}",
            f"- offtrack source rows: {summary['offtrack_source_row_count']}",
            "",
            "## Interpretation",
            "",
            "M3168 admits exactly two bounded actor-visible implementation hypotheses: collision-clearance observation-timeline reflex and boundary-recovery stability reflex. This is implementation admission only, not driver mutation or repair evidence.",
            "",
            "The admission preserves local action-delta tuning as blocked, preserves the obs72-to-direct-action3 runtime contract, and requires M3169 audit before any repair implementation materialization. Any later validation or performance interpretation still requires a separate post-implementation measurement and result audit.",
            "",
            "M3168 does not reset or step the environment, replay rollouts, run a policy action, train, tune, rank, promote, validate, implement repair, select a winner, mutate a checkpoint, or make validation, repair-success, robustness, driver-performance, current-sim, high-fidelity, paper, full-driver, feasibility-proof, or self-ID claims.",
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


def run_repair_admission_materialization_preflight(
    *,
    m3167_audit: Path,
    m3166_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(m3167_audit=m3167_audit, m3166_dir=m3166_dir)
    hypothesis_rows = repair_hypothesis_rows(source)
    actor_rows = actor_contract_guard_rows()
    measurement_rows = measurement_readiness_rows()
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claim_rows = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    write_csv_rows(paths["repair_hypothesis_rows"], hypothesis_rows, fieldnames=REPAIR_HYPOTHESIS_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=ACTOR_CONTRACT_FIELDNAMES)
    write_csv_rows(paths["measurement_readiness_rows"], measurement_rows, fieldnames=MEASUREMENT_READINESS_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        hypothesis_rows=hypothesis_rows,
        actor_rows=actor_rows,
        measurement_rows=measurement_rows,
        claim_rows=claim_rows,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gates)
    status_pass = bool(gate_matrix_pass and present)
    source_rows = list(source.get("m3166_source_localization_rows", []))
    blocker_counts = Counter(str(row.get("blocker_family", "")) for row in source_rows)
    summary = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_residual_hard_safety_source_localized_repair_admission_materialization_pass"
            if status_pass
            else "active_safety_driver_residual_hard_safety_source_localized_repair_admission_materialization_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "source_localization_row_count": len(source_rows),
        "collision_source_row_count": blocker_counts.get("collision", 0),
        "offtrack_source_row_count": blocker_counts.get("offtrack", 0),
        "repair_hypothesis_row_count": len(hypothesis_rows),
        "implementation_admitted_hypothesis_count": sum(
            1 for row in hypothesis_rows if _bool(row.get("admitted_for_repair_implementation_materialization", False))
        ),
        "validation_admitted_hypothesis_count": sum(1 for row in hypothesis_rows if _bool(row.get("admitted_for_validation", False))),
        "actor_contract_guard_row_count": len(actor_rows),
        "measurement_readiness_row_count": len(measurement_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
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
        "driver_mutation_run": False,
        "repair_implementation_run": False,
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
        "decision": "active_safety_driver_residual_hard_safety_source_localized_repair_admission_route_to_m3169_result_audit",
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
            "repair_hypothesis_row_count": len(hypothesis_rows),
            "complete": status_pass,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3167-audit", type=Path, default=DEFAULT_M3167_AUDIT)
    parser.add_argument("--m3166-dir", type=Path, default=DEFAULT_M3166_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_repair_admission_materialization_preflight(
        m3167_audit=args.m3167_audit,
        m3166_dir=args.m3166_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"repair_hypothesis_rows={summary['repair_hypothesis_row_count']}")
    print(f"implementation_admitted_hypotheses={summary['implementation_admitted_hypothesis_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
