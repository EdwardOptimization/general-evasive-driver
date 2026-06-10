"""Materialize M3187 residual hard-safety blocker-axis trace specification artifacts."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state


MILESTONE_ID = (
    "m3187-engineering-controller-active-safety-driver-residual-hard-safety-"
    "blocker-axis-trace-spec-materialization-preflight"
)
NEXT_ID = (
    "m3188-engineering-controller-active-safety-driver-residual-hard-safety-"
    "blocker-axis-trace-spec-result-audit"
)
M3186_ID = (
    "m3186-engineering-controller-active-safety-driver-residual-hard-safety-"
    "blocker-axis-expansion-pack-result-audit"
)
M3185_ID = (
    "m3185-engineering-controller-active-safety-driver-residual-hard-safety-"
    "blocker-axis-expansion-pack-materialization-preflight"
)

DEFAULT_M3186_AUDIT = Path(f"docs/{M3186_ID}.md")
DEFAULT_M3185_DIR = Path(
    "runs/m3185_engineering_controller_active_safety_driver_residual_hard_safety_"
    "blocker_axis_expansion_pack_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3187_engineering_controller_active_safety_driver_residual_hard_safety_"
    "blocker_axis_trace_spec_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_BLOCKERS = 7
EXPECTED_AXIS_CANDIDATES = 4
EXPECTED_FORBIDDEN_GUARDS = 5

CLAIM_SCOPE = (
    "M3187 Active Safety Driver residual hard-safety blocker-axis trace-spec "
    "materialization only; existing M3186 audit and M3185 blocker-axis pack rows "
    "may be reanalyzed into trace-spec, source-binding, obs72/public-telemetry "
    "boundary, forbidden-label, implementation-admission, claim, gate, doc, and "
    "M3188 audit manifest artifacts. No reset, step, rollout, replay, policy action, "
    "fitting, PPO, training, repair implementation, validation execution, ranking, "
    "winner selection, checkpoint mutation, checkpoint promotion, public driver "
    "default mutation, driver-performance verdict, current-sim verdict, repair "
    "success, robustness-result, high-fidelity validation, paper evidence, "
    "finite-window-vs-GRU evidence, full ideal driver completion, feasibility "
    "proof, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair implementation, validation result, driver-performance verdict, current-sim "
    "verdict, robustness-result, repair success, feasibility proof, checkpoint ranking, "
    "winner selection, checkpoint promotion, public driver default replacement, high-fidelity "
    "validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full "
    "ideal driver completion, or level3 self-identification"
)
FORBIDDEN_RUNTIME_INPUTS = (
    "source_id|blocker_label|row_outcome|baseline_outcome|target_label|route_label|"
    "progress_label|verdict_label|ttc_oracle|future_terminal_status"
)

TRACE_SPEC_FIELDNAMES = [
    "trace_spec_id",
    "evidence_axis",
    "route_role",
    "source_blocker_count",
    "source_blocker_rows",
    "required_trace_channels",
    "trace_source_boundary",
    "sample_scope",
    "output_artifact_intent",
    "hidden_labels_required",
    "actor_runtime_input_contract",
    "implementation_admitted",
    "repair_success_claim_made",
    "claim_boundary",
]
BINDING_FIELDNAMES = [
    "trace_source_binding_id",
    "evidence_axis",
    "fresh_panel_row_id",
    "source_measurement_episode_id",
    "blocker_family",
    "axis_id",
    "binding_role",
    "task_family",
    "eval_seed",
    "offline_labels_only",
    "runtime_actor_input_allowed",
    "claim_boundary",
]
BOUNDARY_FIELDNAMES = [
    "boundary_row_id",
    "signal_family",
    "source_boundary",
    "actor_runtime_allowed",
    "offline_trace_allowed",
    "public_telemetry_allowed",
    "example_fields",
    "status_pass",
    "claim_boundary",
]
FORBIDDEN_LABEL_FIELDNAMES = [
    "forbidden_label_guard_id",
    "label_family",
    "example_fields",
    "actor_runtime_allowed",
    "offline_analysis_allowed",
    "status_pass",
    "claim_boundary",
]
ADMISSION_FIELDNAMES = [
    "implementation_admission_guard_id",
    "evidence_axis",
    "trace_spec_materialized",
    "implementation_allowed_now",
    "public_driver_mutation_allowed",
    "required_before_implementation",
    "forbidden_runtime_inputs",
    "status_pass",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3187",
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
        "trace_spec_rows": output_dir / "trace_spec_rows.csv",
        "trace_source_binding_rows": output_dir / "trace_source_binding_rows.csv",
        "obs72_public_telemetry_boundary_rows": output_dir / "obs72_public_telemetry_boundary_rows.csv",
        "forbidden_label_guard_rows": output_dir / "forbidden_label_guard_rows.csv",
        "implementation_admission_guard_rows": output_dir / "implementation_admission_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3186_audit: Path, m3185_dir: Path) -> dict[str, Any]:
    paths = {
        "m3186_audit": m3186_audit,
        "m3185_summary": m3185_dir / "summary.json",
        "m3185_residual_blocker_axis_rows": m3185_dir / "residual_blocker_axis_rows.csv",
        "m3185_actor_visible_axis_candidate_rows": m3185_dir / "actor_visible_axis_candidate_rows.csv",
        "m3185_forbidden_label_guard_rows": m3185_dir / "forbidden_label_guard_rows.csv",
        "m3185_gate_matrix": m3185_dir / "gate_matrix.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3186_audit_text": paths["m3186_audit"].read_text(encoding="utf-8") if exists["m3186_audit"] else "",
        "m3185_summary": read_json(paths["m3185_summary"]) if exists["m3185_summary"] else {},
        "m3185_residual_blocker_axis_rows": read_csv_rows(paths["m3185_residual_blocker_axis_rows"]),
        "m3185_actor_visible_axis_candidate_rows": read_csv_rows(paths["m3185_actor_visible_axis_candidate_rows"]),
        "m3185_forbidden_label_guard_rows": read_csv_rows(paths["m3185_forbidden_label_guard_rows"]),
        "m3185_gate_matrix": read_csv_rows(paths["m3185_gate_matrix"]),
    }


def required_trace_channels(evidence_axis: str, allowed_signal_families: str) -> str:
    common = "obs72_snapshot|previous_action|final_action|action_delta|terminal_status_offline"
    if evidence_axis == "clearance_timing_axis":
        return f"{common}|ego_speed|obstacle_geometry_proxy|relative_clearance_proxy|lane_corridor_geometry"
    if evidence_axis == "boundary_recovery_collision_axis":
        return f"{common}|lane_boundary_geometry|obstacle_geometry_proxy|lateral_error|previous_action_response"
    if evidence_axis == "boundary_recovery_stability_axis":
        return f"{common}|lane_boundary_geometry|lateral_error|heading_alignment|sideslip_proxy|previous_action_response"
    if evidence_axis == "action_authority_saturation_axis":
        return f"{common}|raw_action_bounds|final_action_bounds|action_rate|clip_fraction"
    return f"{common}|{allowed_signal_families}"


def trace_spec_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source["m3185_actor_visible_axis_candidate_rows"], start=1):
        evidence_axis = str(row.get("evidence_axis", ""))
        source_count = int(float(row.get("source_blocker_count", 0) or 0))
        rows.append(
            {
                "trace_spec_id": f"m3187-trace-spec-{index:04d}",
                "evidence_axis": evidence_axis,
                "route_role": row.get("route_role", ""),
                "source_blocker_count": source_count,
                "source_blocker_rows": row.get("source_blocker_rows", ""),
                "required_trace_channels": required_trace_channels(evidence_axis, str(row.get("allowed_signal_families", ""))),
                "trace_source_boundary": "obs72_snapshot_and_public_runtime_telemetry_only",
                "sample_scope": "same_case_residual_blocker_rows_only_not_validation",
                "output_artifact_intent": "future_trace_execution_spec_not_repair_implementation",
                "hidden_labels_required": False,
                "actor_runtime_input_contract": "obs72_only_direct_action3",
                "implementation_admitted": False,
                "repair_success_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def trace_source_binding_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source["m3185_residual_blocker_axis_rows"], start=1):
        rows.append(
            {
                "trace_source_binding_id": f"m3187-trace-source-binding-{index:04d}",
                "evidence_axis": row.get("proposed_evidence_axis", ""),
                "fresh_panel_row_id": row.get("fresh_panel_row_id", ""),
                "source_measurement_episode_id": row.get("source_measurement_episode_id", ""),
                "blocker_family": row.get("blocker_family", ""),
                "axis_id": row.get("axis_id", ""),
                "binding_role": row.get("binding_role", ""),
                "task_family": row.get("task_family", ""),
                "eval_seed": row.get("eval_seed", ""),
                "offline_labels_only": row.get("offline_labels_only", ""),
                "runtime_actor_input_allowed": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def obs72_public_telemetry_boundary_rows() -> list[dict[str, Any]]:
    specs = [
        ("obs72_snapshot", "actor_visible_observation", True, True, False, "obs72 vector values"),
        ("previous_action", "actor_visible_or_public_runtime_telemetry", True, True, True, "previous steer throttle brake"),
        ("final_action", "public_runtime_telemetry", False, True, True, "final clipped action3"),
        ("raw_action_bounds", "public_runtime_telemetry", False, True, True, "raw action abs max and l2"),
        ("action_rate", "public_runtime_telemetry", False, True, True, "per-step action delta magnitude"),
        ("clip_fraction", "public_runtime_telemetry", False, True, True, "final action clipping flag"),
        ("offline_source_labels", "offline_evidence_accounting_only", False, True, False, "source ids blocker family outcome labels"),
        ("oracle_ttc_or_verdict", "forbidden_runtime_or_trace_input", False, False, False, "ttc_oracle verdict progress future terminal status"),
    ]
    return [
        {
            "boundary_row_id": f"m3187-boundary-{index:04d}",
            "signal_family": signal,
            "source_boundary": source_boundary,
            "actor_runtime_allowed": actor_allowed,
            "offline_trace_allowed": trace_allowed,
            "public_telemetry_allowed": telemetry_allowed,
            "example_fields": examples,
            "status_pass": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (signal, source_boundary, actor_allowed, trace_allowed, telemetry_allowed, examples) in enumerate(specs, start=1)
    ]


def forbidden_label_guard_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source["m3185_forbidden_label_guard_rows"], start=1):
        rows.append(
            {
                "forbidden_label_guard_id": f"m3187-forbidden-label-guard-{index:04d}",
                "label_family": row.get("label_family", ""),
                "example_fields": row.get("example_fields", ""),
                "actor_runtime_allowed": False,
                "offline_analysis_allowed": _bool(row.get("offline_analysis_allowed")),
                "status_pass": not _bool(row.get("actor_runtime_allowed")),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def implementation_admission_guard_rows(trace_specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "implementation_admission_guard_id": f"m3187-implementation-admission-{index:04d}",
            "evidence_axis": row["evidence_axis"],
            "trace_spec_materialized": True,
            "implementation_allowed_now": False,
            "public_driver_mutation_allowed": False,
            "required_before_implementation": "M3188 audit and later trace execution artifacts with actor-visible-only boundaries",
            "forbidden_runtime_inputs": FORBIDDEN_RUNTIME_INPUTS,
            "status_pass": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, row in enumerate(trace_specs, start=1)
    ]


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    claims = [
        ("trace_spec_rows", "materialization", True, True, "trace_spec_rows.csv"),
        ("trace_source_binding_rows", "materialization", True, True, "trace_source_binding_rows.csv"),
        ("obs72_public_telemetry_boundary_rows", "materialization", True, True, "obs72_public_telemetry_boundary_rows.csv"),
        ("follow_up_result_audit_registered", "process", True, follow_up_manifest_registered, f"experiments/manifests/{NEXT_ID}.json"),
        ("repair_implementation", "forbidden", False, False, "later implementation preflight after trace execution evidence"),
        ("validation_result", "forbidden", False, False, "separate validation execution after accepted candidate"),
        ("driver_performance_verdict", "forbidden", False, False, "validation and promotion gates"),
        ("current_sim_verdict", "forbidden", False, False, "current-sim synthesis after validation"),
        ("repair_success", "forbidden", False, False, "accepted same-denominator improvement plus validation route"),
        ("checkpoint_promotion", "forbidden", False, False, "promotion gate"),
        ("self_id", "forbidden", False, False, "history necessity tests outside M3187"),
    ]
    return [
        {
            "claim_id": f"m3187-{claim_id}",
            "claim_family": family,
            "allowed_in_m3187": allowed,
            "claim_made": made,
            "status_pass": bool(made) == bool(allowed) if allowed else not bool(made),
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, allowed, made, evidence in claims
    ]


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m3187-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    trace_specs: list[dict[str, Any]],
    bindings: list[dict[str, Any]],
    boundaries: list[dict[str, Any]],
    forbidden_rows: list[dict[str, Any]],
    admissions: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    source_axis_counts = Counter(str(row.get("proposed_evidence_axis", "")) for row in source["m3185_residual_blocker_axis_rows"])
    trace_axes = {str(row.get("evidence_axis", "")) for row in trace_specs}
    source_axes = {str(row.get("evidence_axis", "")) for row in source["m3185_actor_visible_axis_candidate_rows"]}
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3186_selects_m3187_route", "lineage", "M3187 trace-spec materialization" in source["m3186_audit_text"], "route marker", "present", "lineage_invalid"),
        gate("m3185_status_pass", "lineage", _bool(source["m3185_summary"].get("status_pass")), source["m3185_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3185_gate_matrix_pass", "lineage", _bool(source["m3185_summary"].get("gate_matrix_pass")), source["m3185_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("trace_spec_rows", "evidence", len(trace_specs) == EXPECTED_AXIS_CANDIDATES, len(trace_specs), EXPECTED_AXIS_CANDIDATES, "metric_artifact"),
        gate("trace_axes_preserved", "evidence", trace_axes == source_axes, sorted(trace_axes), sorted(source_axes), "metric_artifact"),
        gate("trace_source_bindings", "evidence", len(bindings) == EXPECTED_BLOCKERS, len(bindings), EXPECTED_BLOCKERS, "metric_artifact"),
        gate("binding_axis_counts", "evidence", sum(source_axis_counts.values()) == EXPECTED_BLOCKERS, dict(source_axis_counts), EXPECTED_BLOCKERS, "metric_artifact"),
        gate("obs72_boundary_rows", "contract", len(boundaries) >= 8, len(boundaries), ">=8", "contract_violation"),
        gate("hidden_labels_not_actor_runtime", "contract", not any(_bool(row.get("actor_runtime_allowed")) for row in forbidden_rows), "none", "allowed", "contract_violation"),
        gate("oracle_ttc_not_trace_allowed", "contract", any(row["signal_family"] == "oracle_ttc_or_verdict" and not _bool(row["offline_trace_allowed"]) for row in boundaries), "oracle boundary", "trace disallowed", "contract_violation"),
        gate("forbidden_label_guard_rows", "contract", len(forbidden_rows) >= EXPECTED_FORBIDDEN_GUARDS, len(forbidden_rows), f">={EXPECTED_FORBIDDEN_GUARDS}", "contract_violation"),
        gate("forbidden_label_guards_pass", "contract", all(_bool(row.get("status_pass")) for row in forbidden_rows), "all", "pass", "contract_violation"),
        gate("implementation_admissions", "contract", len(admissions) == len(trace_specs), len(admissions), len(trace_specs), "contract_violation"),
        gate("implementation_not_admitted", "contract", not any(_bool(row.get("implementation_allowed_now")) for row in admissions), "none", "admitted", "contract_violation"),
        gate("claim_boundary_rows_pass", "claim", all(_bool(row.get("status_pass")) for row in claims), "all", "pass", "proof_washout"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def required_artifacts_present(paths: Mapping[str, Path]) -> bool:
    late_written = {"summary", "gate_matrix", "doc", "run_state"}
    return all(path.exists() for key, path in paths.items() if key not in late_written)


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 31880,
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
            "seed_fragility",
        ],
        "hypothesis": "A bounded result audit can accept or reject M3187 trace-spec artifacts before trace execution repair implementation validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path)],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "trace_spec_rows.csv"),
                str(output_dir / "trace_source_binding_rows.csv"),
                str(output_dir / "obs72_public_telemetry_boundary_rows.csv"),
                str(output_dir / "forbidden_label_guard_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit M3187 trace-spec materialization before trace execution or implementation admission"],
            "derived_from": [MILESTONE_ID, M3186_ID, M3185_ID],
            "blocked_by": [
                "M3187 trace specs require audit before execution or implementation admission",
                "obs72/public-telemetry boundaries must be verified against forbidden-label guards",
            ],
            "supersedes": ["direct residual blocker trace execution without trace-spec audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3188 must audit M3187 trace specs source bindings obs72 boundary forbidden-label guards claims and gates",
            "M3188 must preserve M3105/M3103 as incumbent and public driver default unchanged",
            "M3188 must reject trace execution repair implementation validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3188 must select exactly one trace-execution-spec, artifact-repair, synthesis, or stop route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run trace execution repair implementation validation ranking promotion or high-fidelity simulation in M3188",
            "do not convert M3187 trace specs into repair-success performance current-sim robustness-result paper or self-ID claims",
            "do not change actor input action contract or public driver default",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_hard_safety_blocker_axis_expansion",
            "evidence_axis": "residual_blocker_axis_trace_spec_result_audit",
            "evidence_increment": "audits no-new-execution trace specs for the M3185 residual blocker axes",
            "claim_scope": "Result audit only; no trace execution implementation validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "stop_condition": [
                "stop if M3187 artifacts are missing or gate matrix fails",
                "stop if any trace spec requires hidden runtime labels as actor inputs",
                "route to trace execution only after M3188 accepts claim boundaries",
            ],
            "fallback_plan": [
                "route to M3187 artifact repair if row counts or guards fail",
                "route to stop if no actor-visible trace spec remains after guard checks",
                "preserve M3105/M3103 incumbent until later accepted measurement improves hard-safety counts",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3187 materializes blocker-axis trace specification artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3187 blocker-axis trace specification artifacts",
            "admission_evidence": ["M3187 summary trace spec rows source bindings obs72 boundary forbidden-label guards claim and gate artifacts"],
            "blocked_shortcuts": [
                "no trace execution repair implementation validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3188 status queue scoreboard research log and review",
                "one follow-up manifest only if M3188 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3188 accepts or rejects M3187 as complete and claim-safe",
                "next trace-execution artifact-repair synthesis or stop route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3188 audits engineering trace-spec artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3188; self-ID and GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3187 trace-spec artifacts only.",
            "negative_result_policy": "Preserve engineering trace-spec evidence and route trace execution or stop rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3187 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits residual blocker-axis trace specs before trace execution or implementation admission",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3188 audits engineering trace-spec evidence",
            "must_synthesize_if": [
                "M3188 cannot select trace-execution artifact-repair synthesis or stop",
                "M3188 would claim repair-success validation driver-performance current-sim verdict robustness-result or self-ID evidence",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3188 audits M3187 row counts gates actor contract and claim boundaries",
            "M3188 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3188 hides missing M3187 artifacts or failed gates",
            "M3188 treats M3187 trace specs as repair success or performance verdict",
            "M3188 changes actor input or action contract",
            "M3188 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3188 audits M3187 artifacts and selects one next route or stop state while preserving actor direct-action and claim boundaries without overclaiming.",
        "commands": [
            {
                "name": "active_safety_driver_residual_hard_safety_blocker_axis_trace_spec_result_audit_doc",
                "command": "true",
            }
        ],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def render_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3187 Residual Hard-Safety Blocker Axis Trace Spec Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- trace spec rows: {summary['trace_spec_row_count']}",
            f"- trace source binding rows: {summary['trace_source_binding_row_count']}",
            f"- obs72/public telemetry boundary rows: {summary['obs72_public_telemetry_boundary_row_count']}",
            f"- forbidden-label guards pass: {summary['forbidden_label_guard_rows_pass']}",
            f"- implementation admitted: {summary['implementation_admitted']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3187 materializes no-new-execution trace specifications for the M3185 blocker axes. It preserves all source blocker bindings, separates obs72 and public runtime telemetry from offline labels, and keeps implementation admission blocked until a later audit and trace execution route.",
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


def run_materialization(
    *,
    m3186_audit: Path,
    m3185_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(m3186_audit=m3186_audit, m3185_dir=m3185_dir)
    trace_specs = trace_spec_rows(source)
    bindings = trace_source_binding_rows(source)
    boundaries = obs72_public_telemetry_boundary_rows()
    forbidden_rows = forbidden_label_guard_rows(source)
    admissions = implementation_admission_guard_rows(trace_specs)
    follow_up_payload = build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path)
    write_json(paths["follow_up_manifest"], follow_up_payload)
    claims = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())

    write_csv_rows(paths["trace_spec_rows"], trace_specs, fieldnames=TRACE_SPEC_FIELDNAMES)
    write_csv_rows(paths["trace_source_binding_rows"], bindings, fieldnames=BINDING_FIELDNAMES)
    write_csv_rows(paths["obs72_public_telemetry_boundary_rows"], boundaries, fieldnames=BOUNDARY_FIELDNAMES)
    write_csv_rows(paths["forbidden_label_guard_rows"], forbidden_rows, fieldnames=FORBIDDEN_LABEL_FIELDNAMES)
    write_csv_rows(paths["implementation_admission_guard_rows"], admissions, fieldnames=ADMISSION_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claims, fieldnames=CLAIM_FIELDNAMES)

    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        trace_specs=trace_specs,
        bindings=bindings,
        boundaries=boundaries,
        forbidden_rows=forbidden_rows,
        admissions=admissions,
        claims=claims,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass")) for row in gates)
    status_pass = bool(gate_matrix_pass and present)
    axis_counts = Counter(str(row.get("evidence_axis", "")) for row in bindings)
    summary: dict[str, Any] = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_residual_hard_safety_blocker_axis_trace_spec_materialization_pass"
            if status_pass
            else "active_safety_driver_residual_hard_safety_blocker_axis_trace_spec_materialization_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "trace_spec_row_count": len(trace_specs),
        "trace_source_binding_row_count": len(bindings),
        "trace_binding_axis_counts": dict(sorted(axis_counts.items())),
        "obs72_public_telemetry_boundary_row_count": len(boundaries),
        "forbidden_label_guard_row_count": len(forbidden_rows),
        "forbidden_label_guard_rows_pass": all(_bool(row.get("status_pass")) for row in forbidden_rows),
        "implementation_admission_guard_row_count": len(admissions),
        "implementation_admitted": any(_bool(row.get("implementation_allowed_now")) for row in admissions),
        "claim_boundary_row_count": len(claims),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass")) for row in claims),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
        "m3185_status_pass": _bool(source["m3185_summary"].get("status_pass")),
        "m3185_gate_matrix_pass": _bool(source["m3185_summary"].get("gate_matrix_pass")),
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
        "public_driver_default_mutated": False,
        "driver_performance_claim_made": False,
        "driver_performance_verdict_claim_made": False,
        "repair_success_claim_made": False,
        "robustness_result_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "decision": "active_safety_driver_residual_hard_safety_blocker_axis_trace_spec_route_to_m3188_result_audit",
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
            "trace_spec_row_count": len(trace_specs),
            "trace_source_binding_row_count": len(bindings),
            "complete": status_pass,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3186-audit", type=Path, default=DEFAULT_M3186_AUDIT)
    parser.add_argument("--m3185-dir", type=Path, default=DEFAULT_M3185_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_materialization(
        m3186_audit=args.m3186_audit,
        m3185_dir=args.m3185_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"trace_spec_rows={summary['trace_spec_row_count']}")
    print(f"trace_source_binding_rows={summary['trace_source_binding_row_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
