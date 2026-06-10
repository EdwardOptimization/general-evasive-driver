"""Materialize M3192 preterminal authority and boundary-stability admission artifacts."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state


MILESTONE_ID = (
    "m3192-engineering-controller-active-safety-driver-residual-hard-safety-"
    "preterminal-authority-boundary-stability-admission-materialization-preflight"
)
NEXT_ID = (
    "m3193-engineering-controller-active-safety-driver-residual-hard-safety-"
    "preterminal-authority-boundary-stability-admission-result-audit"
)
M3191_ID = (
    "m3191-engineering-controller-active-safety-driver-residual-hard-safety-"
    "blocker-axis-trace-execution-synthesis"
)
M3189_ID = (
    "m3189-engineering-controller-active-safety-driver-residual-hard-safety-"
    "blocker-axis-trace-execution-materialization-preflight"
)
M3187_ID = (
    "m3187-engineering-controller-active-safety-driver-residual-hard-safety-"
    "blocker-axis-trace-spec-materialization-preflight"
)

DEFAULT_M3191_SYNTHESIS = Path(f"docs/{M3191_ID}.md")
DEFAULT_M3189_DIR = Path(
    "runs/m3189_engineering_controller_active_safety_driver_residual_hard_safety_"
    "blocker_axis_trace_execution_materialization_preflight"
)
DEFAULT_M3187_DIR = Path(
    "runs/m3187_engineering_controller_active_safety_driver_residual_hard_safety_"
    "blocker_axis_trace_spec_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3192_engineering_controller_active_safety_driver_residual_hard_safety_"
    "preterminal_authority_boundary_stability_admission_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_TRACE_EXECUTIONS = 7
EXPECTED_COLLISION_ROWS = 5
EXPECTED_OFFTRACK_ROWS = 2
EXPECTED_ADMISSION_RULES = 2
EXPECTED_GUARD_RULES = 1
FORBIDDEN_RUNTIME_INPUTS = (
    "source_id|blocker_label|row_outcome|baseline_outcome|target_label|route_label|"
    "progress_label|verdict_label|ttc_oracle|future_terminal_status"
)
CLAIM_SCOPE = (
    "M3192 Active Safety Driver residual hard-safety preterminal authority and "
    "boundary-stability admission materialization only; M3191 synthesis, M3189 "
    "trace telemetry, and M3187 trace specs may be converted into actor-visible "
    "implementation-admission rows, rule-contract rows, forbidden-label guards, "
    "claim rows, gate rows, doc, and M3193 audit manifest artifacts. No reset, "
    "step, rollout, replay, policy action, fitting, PPO, training, repair "
    "implementation, validation execution, ranking, winner selection, checkpoint "
    "mutation, checkpoint promotion, public driver default mutation, "
    "driver-performance verdict, current-sim verdict, repair success, "
    "robustness-result, high-fidelity validation, paper evidence, "
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

ADMISSION_FIELDNAMES = [
    "implementation_admission_id",
    "rule_family",
    "admission_role",
    "target_blocker_family",
    "source_trace_execution_count",
    "source_step_count",
    "evidence_axes",
    "terminal_window_speed_min",
    "terminal_window_speed_max",
    "terminal_clearance_min",
    "terminal_lateral_abs_mean",
    "terminal_beta_abs_mean",
    "terminal_clip_step_count",
    "terminal_window_step_count",
    "implementation_admission_recommended",
    "implementation_allowed_now",
    "requires_m3193_audit",
    "actor_runtime_input_contract",
    "allowed_actor_visible_signals",
    "forbidden_actor_inputs",
    "expected_action_delta",
    "proof_gate_required",
    "repair_success_claim_made",
    "claim_boundary",
]
RULE_CONTRACT_FIELDNAMES = [
    "rule_contract_id",
    "rule_family",
    "contract_family",
    "status_pass",
    "runtime_actor_inputs",
    "output_semantics",
    "allowed_runtime_surface",
    "forbidden_runtime_surface",
    "public_driver_mutation_allowed",
    "action_authority_saturation_role",
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
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3192",
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


def _mean(values: Iterable[float]) -> float:
    items = list(values)
    return float(sum(items) / len(items)) if items else 0.0


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "implementation_admission_rows": output_dir / "implementation_admission_rows.csv",
        "rule_contract_rows": output_dir / "rule_contract_rows.csv",
        "forbidden_label_guard_rows": output_dir / "forbidden_label_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3191_synthesis: Path, m3189_dir: Path, m3187_dir: Path) -> dict[str, Any]:
    paths = {
        "m3191_synthesis": m3191_synthesis,
        "m3189_summary": m3189_dir / "summary.json",
        "m3189_trace_execution_rows": m3189_dir / "trace_execution_rows.csv",
        "m3189_trace_step_rows": m3189_dir / "trace_step_rows.csv",
        "m3189_gate_rows": m3189_dir / "gate_matrix.csv",
        "m3187_summary": m3187_dir / "summary.json",
        "m3187_trace_spec_rows": m3187_dir / "trace_spec_rows.csv",
        "m3187_boundary_rows": m3187_dir / "obs72_public_telemetry_boundary_rows.csv",
        "m3187_forbidden_label_guard_rows": m3187_dir / "forbidden_label_guard_rows.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3191_synthesis_text": paths["m3191_synthesis"].read_text(encoding="utf-8") if exists["m3191_synthesis"] else "",
        "m3189_summary": read_json(paths["m3189_summary"]) if exists["m3189_summary"] else {},
        "m3189_trace_execution_rows": read_csv_rows(paths["m3189_trace_execution_rows"]),
        "m3189_trace_step_rows": read_csv_rows(paths["m3189_trace_step_rows"]),
        "m3189_gate_rows": read_csv_rows(paths["m3189_gate_rows"]),
        "m3187_summary": read_json(paths["m3187_summary"]) if exists["m3187_summary"] else {},
        "m3187_trace_spec_rows": read_csv_rows(paths["m3187_trace_spec_rows"]),
        "m3187_boundary_rows": read_csv_rows(paths["m3187_boundary_rows"]),
        "m3187_forbidden_label_guard_rows": read_csv_rows(paths["m3187_forbidden_label_guard_rows"]),
    }


def _steps_by_execution(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("trace_execution_id", ""))].append(row)
    for group in grouped.values():
        group.sort(key=lambda row: _float(row.get("step_index", 0)))
    return grouped


def _terminal_rows(execution_ids: set[str], source: Mapping[str, Any], *, window: int = 5) -> list[dict[str, Any]]:
    grouped = _steps_by_execution(list(source.get("m3189_trace_step_rows", [])))
    rows: list[dict[str, Any]] = []
    for execution_id in sorted(execution_ids):
        rows.extend(grouped.get(execution_id, [])[-window:])
    return rows


def _axis_label(rows: list[dict[str, Any]]) -> str:
    return "|".join(sorted({str(row.get("evidence_axis", "")) for row in rows if row.get("evidence_axis")}))


def _terminal_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    speeds = [_float(row.get("post_speed")) for row in rows]
    margins = [_float(row.get("relative_clearance_proxy")) for row in rows]
    lat_abs = [abs(_float(row.get("post_lateral_error"))) for row in rows]
    beta_abs = [abs(_float(row.get("post_beta"))) for row in rows]
    clip_steps = sum(_bool(row.get("action_clip_hit")) for row in rows)
    return {
        "terminal_window_speed_min": min(speeds) if speeds else 0.0,
        "terminal_window_speed_max": max(speeds) if speeds else 0.0,
        "terminal_clearance_min": min(margins) if margins else 0.0,
        "terminal_lateral_abs_mean": _mean(lat_abs),
        "terminal_beta_abs_mean": _mean(beta_abs),
        "terminal_clip_step_count": clip_steps,
        "terminal_window_step_count": len(rows),
    }


def implementation_admission_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    executions = list(source.get("m3189_trace_execution_rows", []))
    collision_execs = [row for row in executions if str(row.get("blocker_family", "")) == "collision"]
    offtrack_execs = [row for row in executions if str(row.get("blocker_family", "")) == "offtrack"]
    all_ids = {str(row.get("trace_execution_id", "")) for row in executions}
    collision_ids = {str(row.get("trace_execution_id", "")) for row in collision_execs}
    offtrack_ids = {str(row.get("trace_execution_id", "")) for row in offtrack_execs}
    collision_stats = _terminal_stats(_terminal_rows(collision_ids, source))
    offtrack_stats = _terminal_stats(_terminal_rows(offtrack_ids, source))
    all_stats = _terminal_stats(_terminal_rows(all_ids, source))
    return [
        {
            "implementation_admission_id": "m3192-implementation-admission-0001",
            "rule_family": "preterminal_clearance_authority_timing",
            "admission_role": "implementation_candidate_after_audit",
            "target_blocker_family": "collision",
            "source_trace_execution_count": len(collision_execs),
            "source_step_count": sum(int(_float(row.get("steps"))) for row in collision_execs),
            "evidence_axes": _axis_label(collision_execs),
            **collision_stats,
            "implementation_admission_recommended": len(collision_execs) == EXPECTED_COLLISION_ROWS,
            "implementation_allowed_now": False,
            "requires_m3193_audit": True,
            "actor_runtime_input_contract": "obs72_only_direct_action3",
            "allowed_actor_visible_signals": "obs72 ego speed obstacle geometry proxy relative clearance proxy lane corridor geometry lateral error",
            "forbidden_actor_inputs": FORBIDDEN_RUNTIME_INPUTS,
            "expected_action_delta": "preterminal throttle reduction brake support and bounded steering before terminal clearance saturation",
            "proof_gate_required": "post-implementation same-row residual blocker measurement plus full-fresh denominator audit before validation",
            "repair_success_claim_made": False,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "implementation_admission_id": "m3192-implementation-admission-0002",
            "rule_family": "boundary_stability_recovery_authority",
            "admission_role": "implementation_candidate_after_audit",
            "target_blocker_family": "offtrack",
            "source_trace_execution_count": len(offtrack_execs),
            "source_step_count": sum(int(_float(row.get("steps"))) for row in offtrack_execs),
            "evidence_axes": _axis_label(offtrack_execs),
            **offtrack_stats,
            "implementation_admission_recommended": len(offtrack_execs) == EXPECTED_OFFTRACK_ROWS,
            "implementation_allowed_now": False,
            "requires_m3193_audit": True,
            "actor_runtime_input_contract": "obs72_only_direct_action3",
            "allowed_actor_visible_signals": "obs72 lane boundary geometry lateral error heading alignment sideslip proxy ego speed",
            "forbidden_actor_inputs": FORBIDDEN_RUNTIME_INPUTS,
            "expected_action_delta": "bounded center-recovery steering modulation throttle damping and brake support during boundary-stability stress",
            "proof_gate_required": "post-implementation same-row residual blocker measurement plus full-fresh denominator audit before validation",
            "repair_success_claim_made": False,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "implementation_admission_id": "m3192-implementation-admission-0003",
            "rule_family": "action_authority_saturation_guard",
            "admission_role": "cross_cutting_guard_only",
            "target_blocker_family": "collision|offtrack",
            "source_trace_execution_count": len(executions),
            "source_step_count": sum(int(_float(row.get("steps"))) for row in executions),
            "evidence_axes": _axis_label(executions),
            **all_stats,
            "implementation_admission_recommended": False,
            "implementation_allowed_now": False,
            "requires_m3193_audit": True,
            "actor_runtime_input_contract": "obs72_only_direct_action3",
            "allowed_actor_visible_signals": "offline public action telemetry for guard design only not standalone runtime thesis",
            "forbidden_actor_inputs": FORBIDDEN_RUNTIME_INPUTS,
            "expected_action_delta": "guard candidate implementations against terminal-only saturation and excessive action rate",
            "proof_gate_required": "must remain a guard paired with blocker-family rule measurement",
            "repair_success_claim_made": False,
            "claim_boundary": CLAIM_SCOPE,
        },
    ]


def rule_contract_rows(admissions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for admission in admissions:
        family = str(admission["rule_family"])
        role = "guard_only" if family == "action_authority_saturation_guard" else "candidate_rule"
        specs = [
            ("runtime_input", "obs72", "direct_action_clipped", admission["allowed_actor_visible_signals"], admission["forbidden_actor_inputs"], False),
            ("output_action3", "obs72", "direct_action_clipped", "direct [steer throttle brake] bounded action deltas", "latent policy action or hidden route target tensors", False),
            ("public_driver_default", "obs72", "direct_action_clipped", "candidate artifact only after M3193 audit", "public driver default mutation in M3192", False),
        ]
        for contract_family, runtime_inputs, output_semantics, allowed, forbidden, mutation_allowed in specs:
            rows.append(
                {
                    "rule_contract_id": f"m3192-rule-contract-{len(rows) + 1:04d}",
                    "rule_family": family,
                    "contract_family": contract_family,
                    "status_pass": True,
                    "runtime_actor_inputs": runtime_inputs,
                    "output_semantics": output_semantics,
                    "allowed_runtime_surface": allowed,
                    "forbidden_runtime_surface": forbidden,
                    "public_driver_mutation_allowed": mutation_allowed,
                    "action_authority_saturation_role": role if family == "action_authority_saturation_guard" else "guard_checked",
                    "claim_boundary": CLAIM_SCOPE,
                }
            )
    return rows


def forbidden_label_guard_rows() -> list[dict[str, Any]]:
    specs = [
        ("row_identity_labels", "trace_source_binding_id|source_measurement_episode_id|fresh_panel_row_id", True),
        ("terminal_outcome_labels", "blocker_family|termination_reason|outcome_bucket|success", True),
        ("baseline_comparison_labels", "baseline_success|baseline_collision|same_row_delta", True),
        ("oracle_progress_labels", "target_label|ttc_oracle|verdict_label|future_terminal_status", False),
        ("route_context_labels", "axis_id|binding_role|task_family|evidence_axis", True),
    ]
    return [
        {
            "forbidden_label_guard_id": f"m3192-forbidden-label-guard-{index:04d}",
            "label_family": family,
            "example_fields": examples,
            "actor_runtime_allowed": False,
            "offline_analysis_allowed": offline,
            "status_pass": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, examples, offline) in enumerate(specs, start=1)
    ]


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    claims = [
        ("implementation_admission_rows", "admission_artifact", True, True, "implementation_admission_rows.csv"),
        ("rule_contract_rows", "contract_artifact", True, True, "rule_contract_rows.csv"),
        ("forbidden_label_guard_rows", "contract_artifact", True, True, "forbidden_label_guard_rows.csv"),
        ("follow_up_result_audit_registered", "process", True, follow_up_manifest_registered, f"experiments/manifests/{NEXT_ID}.json"),
        ("repair_implementation", "forbidden", False, False, "M3193 audit before any implementation materialization"),
        ("validation_result", "forbidden", False, False, "separate validation execution route"),
        ("driver_performance_verdict", "forbidden", False, False, "future proof generalization and promotion gates"),
        ("current_sim_verdict", "forbidden", False, False, "future audited result synthesis"),
        ("repair_success", "forbidden", False, False, "accepted measurement improvement plus validation route"),
        ("public_driver_default_mutation", "forbidden", False, False, "future promotion gate"),
        ("self_id", "forbidden", False, False, "history necessity tests outside M3192"),
    ]
    return [
        {
            "claim_id": f"m3192-{claim_id}",
            "claim_family": family,
            "allowed_in_m3192": allowed,
            "claim_made": made,
            "status_pass": bool(made) == bool(allowed) if allowed else not bool(made),
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, allowed, made, evidence in claims
    ]


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m3192-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def _m3191_selects_m3192(text: str) -> bool:
    return (
        "m3192-engineering-controller-active-safety-driver-residual-hard-safety-preterminal-authority-boundary-stability-admission-materialization-preflight"
        in text
        or "pre-terminal authority and boundary-stability admission" in text
        or "preterminal_authority_boundary_stability_admission" in text
    )


def gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    admissions: list[dict[str, Any]],
    contracts: list[dict[str, Any]],
    forbidden_rows: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    rule_families = {str(row.get("rule_family", "")) for row in admissions}
    recommended = [row for row in admissions if _bool(row.get("implementation_admission_recommended"))]
    guard_only = [row for row in admissions if str(row.get("admission_role", "")) == "cross_cutting_guard_only"]
    axis_counts = Counter(str(row.get("blocker_family", "")) for row in source["m3189_trace_execution_rows"])
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3191_selects_m3192_route", "lineage", _m3191_selects_m3192(source["m3191_synthesis_text"]), "route marker", "present", "lineage_invalid"),
        gate("m3189_status_pass", "lineage", _bool(source["m3189_summary"].get("status_pass")), source["m3189_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3189_gate_matrix_pass", "lineage", _bool(source["m3189_summary"].get("gate_matrix_pass")), source["m3189_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3187_status_pass", "lineage", _bool(source["m3187_summary"].get("status_pass")), source["m3187_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("trace_execution_rows", "evidence", len(source["m3189_trace_execution_rows"]) == EXPECTED_TRACE_EXECUTIONS, len(source["m3189_trace_execution_rows"]), EXPECTED_TRACE_EXECUTIONS, "metric_artifact"),
        gate("trace_step_rows", "evidence", len(source["m3189_trace_step_rows"]) > 0, len(source["m3189_trace_step_rows"]), ">0", "metric_artifact"),
        gate("residual_blocker_counts", "evidence", axis_counts.get("collision", 0) == EXPECTED_COLLISION_ROWS and axis_counts.get("offtrack", 0) == EXPECTED_OFFTRACK_ROWS, dict(axis_counts), f"{EXPECTED_COLLISION_ROWS} collision {EXPECTED_OFFTRACK_ROWS} offtrack", "metric_artifact"),
        gate("implementation_admission_rows", "admission", len(admissions) == EXPECTED_ADMISSION_RULES + EXPECTED_GUARD_RULES, len(admissions), EXPECTED_ADMISSION_RULES + EXPECTED_GUARD_RULES, "metric_artifact"),
        gate("required_rule_families_present", "admission", {"preterminal_clearance_authority_timing", "boundary_stability_recovery_authority", "action_authority_saturation_guard"}.issubset(rule_families), sorted(rule_families), "all required", "metric_artifact"),
        gate("implementation_recommended_rules", "admission", len(recommended) == EXPECTED_ADMISSION_RULES, len(recommended), EXPECTED_ADMISSION_RULES, "objective_overfit"),
        gate("implementation_not_allowed_now", "contract", not any(_bool(row.get("implementation_allowed_now")) for row in admissions), "none", "allowed", "contract_violation"),
        gate("saturation_guard_not_standalone", "contract", len(guard_only) == EXPECTED_GUARD_RULES and not any(_bool(row.get("implementation_admission_recommended")) for row in guard_only), len(guard_only), EXPECTED_GUARD_RULES, "objective_overfit"),
        gate("rule_contract_rows_pass", "contract", len(contracts) >= 9 and all(_bool(row.get("status_pass")) for row in contracts), len(contracts), ">=9 pass", "contract_violation"),
        gate("forbidden_label_guards_pass", "contract", len(forbidden_rows) >= 5 and all(not _bool(row.get("actor_runtime_allowed")) and _bool(row.get("status_pass")) for row in forbidden_rows), len(forbidden_rows), ">=5 pass", "contract_violation"),
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
        "priority": 31930,
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
        "hypothesis": "A bounded result audit can accept or reject M3192 admission artifacts before any repair implementation validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path)],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "implementation_admission_rows.csv"),
                str(output_dir / "rule_contract_rows.csv"),
                str(output_dir / "forbidden_label_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit M3192 admission artifacts before repair implementation materialization"],
            "derived_from": [MILESTONE_ID, M3191_ID, M3189_ID, M3187_ID],
            "blocked_by": [
                "M3192 admission rows require audit before implementation materialization",
                "M3192 is admission materialization only and not repair implementation",
            ],
            "supersedes": ["direct implementation without audited M3192 admission rows"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3193 must audit M3192 admission rows contract guards claims and gates",
            "M3193 must preserve obs72-only direct action runtime and public driver unchanged",
            "M3193 must reject validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3193 must select implementation materialization artifact-repair synthesis or stop as exactly one route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not implement repair logic in M3193",
            "do not convert admission rows into validation repair-success performance current-sim robustness-result paper or self-ID claims",
            "do not change actor input action contract or public driver default",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_hard_safety_preterminal_authority_boundary_stability",
            "evidence_axis": "preterminal_authority_boundary_stability_admission_result_audit",
            "evidence_increment": "audits M3192 admission artifacts before implementation materialization",
            "claim_scope": "Result audit only; no repair implementation validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "stop_condition": [
                "stop if M3192 artifacts are missing or gate matrix fails",
                "stop if admission requires hidden actor inputs",
                "route to implementation materialization only after M3193 accepts claim boundaries",
            ],
            "fallback_plan": [
                "route to M3192 artifact repair if rows or guards fail",
                "route to synthesis if no actor-visible implementation axis remains",
                "preserve M3105/M3103 incumbent until later accepted measurement improves hard-safety counts",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3192 materializes admission artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3192 admission artifacts",
            "admission_evidence": ["M3192 summary admission contract forbidden-label claim and gate artifacts"],
            "blocked_shortcuts": [
                "no repair implementation validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim",
                "no checkpoint mutation profile tuning or public driver mutation",
                "no hidden oracle target TTC source route outcome progress verdict actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3193 status queue scoreboard research log and review",
                "one follow-up manifest only if M3193 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3193 accepts or rejects M3192 as complete and claim-safe",
                "next implementation materialization artifact-repair synthesis or stop route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3193 audits engineering admission artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3193; self-ID and GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3192 admission artifacts only.",
            "negative_result_policy": "Preserve admission evidence and route implementation materialization or stop rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3192 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits admission materialization before implementation route",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3193 audits engineering admission evidence",
            "must_synthesize_if": [
                "M3193 cannot select implementation materialization artifact-repair synthesis or stop",
                "M3193 would claim repair-success validation driver-performance current-sim verdict robustness-result or self-ID evidence",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3193 audits M3192 row counts gates actor contract and claim boundaries",
            "M3193 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3193 hides missing M3192 artifacts or failed gates",
            "M3193 treats M3192 admission as repair success or performance verdict",
            "M3193 changes actor input or action contract",
            "M3193 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3193 audits M3192 artifacts and selects one next route or stop state while preserving actor direct-action and claim boundaries without overclaiming.",
        "commands": [
            {
                "name": "active_safety_driver_residual_hard_safety_preterminal_authority_boundary_stability_admission_result_audit_doc",
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
            "# M3192 Preterminal Authority Boundary-Stability Admission Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- implementation admission rows: {summary['implementation_admission_row_count']}",
            f"- implementation recommended rows: {summary['implementation_recommended_count']}",
            f"- guard-only rows: {summary['guard_only_count']}",
            f"- rule contract rows: {summary['rule_contract_row_count']}",
            f"- forbidden-label guard rows: {summary['forbidden_label_guard_row_count']}",
            f"- implementation allowed now: {summary['implementation_allowed_now']}",
            f"- public driver default mutated: {summary['public_driver_default_mutated']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3192 materializes actor-visible implementation-admission contracts for preterminal collision-clearance authority timing and boundary-stability recovery. Action-authority saturation is retained as a cross-cutting guard rather than a standalone implementation thesis. M3192 does not implement a repair or admit validation.",
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


def run_admission_materialization_preflight(
    *,
    m3191_synthesis: Path,
    m3189_dir: Path,
    m3187_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(m3191_synthesis=m3191_synthesis, m3189_dir=m3189_dir, m3187_dir=m3187_dir)
    admissions = implementation_admission_rows(source)
    contracts = rule_contract_rows(admissions)
    forbidden_rows = forbidden_label_guard_rows()
    follow_up_payload = build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path)
    write_json(paths["follow_up_manifest"], follow_up_payload)
    claims = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    write_csv_rows(paths["implementation_admission_rows"], admissions, fieldnames=ADMISSION_FIELDNAMES)
    write_csv_rows(paths["rule_contract_rows"], contracts, fieldnames=RULE_CONTRACT_FIELDNAMES)
    write_csv_rows(paths["forbidden_label_guard_rows"], forbidden_rows, fieldnames=FORBIDDEN_LABEL_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claims, fieldnames=CLAIM_FIELDNAMES)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        admissions=admissions,
        contracts=contracts,
        forbidden_rows=forbidden_rows,
        claims=claims,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass")) for row in gates)
    implementation_recommended = sum(_bool(row.get("implementation_admission_recommended")) for row in admissions)
    guard_only = sum(str(row.get("admission_role", "")) == "cross_cutting_guard_only" for row in admissions)
    implementation_allowed_now = any(_bool(row.get("implementation_allowed_now")) for row in admissions)
    status_pass = bool(gate_matrix_pass and implementation_recommended == EXPECTED_ADMISSION_RULES and not implementation_allowed_now)
    summary = {
        "milestone_id": MILESTONE_ID,
        "created_at_utc": utc_timestamp(),
        "result_class": "admission_materialized" if status_pass else "admission_incomplete",
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "source_artifacts_present": all(source["source_exists"].values()),
        "m3189_trace_execution_row_count": len(source["m3189_trace_execution_rows"]),
        "m3189_trace_step_row_count": len(source["m3189_trace_step_rows"]),
        "implementation_admission_row_count": len(admissions),
        "implementation_recommended_count": implementation_recommended,
        "guard_only_count": guard_only,
        "rule_contract_row_count": len(contracts),
        "forbidden_label_guard_row_count": len(forbidden_rows),
        "claim_boundary_row_count": len(claims),
        "implementation_allowed_now": implementation_allowed_now,
        "requires_m3193_audit": True,
        "actor_runtime_input_contract": "obs72_only_direct_action3",
        "public_driver_default_mutated": False,
        "validation_run": False,
        "repair_implementation_run": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
        "self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "follow_up_manifest_exists": paths["follow_up_manifest"].exists(),
        "next_blocker": NEXT_ID,
    }
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "implementation_admission_row_count": len(admissions),
            "implementation_recommended_count": implementation_recommended,
            "guard_only_count": guard_only,
            "complete": True,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3191-synthesis", type=Path, default=DEFAULT_M3191_SYNTHESIS)
    parser.add_argument("--m3189-dir", type=Path, default=DEFAULT_M3189_DIR)
    parser.add_argument("--m3187-dir", type=Path, default=DEFAULT_M3187_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    summary = run_admission_materialization_preflight(
        m3191_synthesis=args.m3191_synthesis,
        m3189_dir=args.m3189_dir,
        m3187_dir=args.m3187_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(summary)


if __name__ == "__main__":
    main()
