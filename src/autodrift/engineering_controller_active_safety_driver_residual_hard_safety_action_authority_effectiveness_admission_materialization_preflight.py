"""Materialize M3201 action-authority/effectiveness admission artifacts."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state


MILESTONE_ID = (
    "m3201-engineering-controller-active-safety-driver-residual-hard-safety-"
    "action-authority-effectiveness-admission-materialization-preflight"
)
NEXT_ID = (
    "m3202-engineering-controller-active-safety-driver-residual-hard-safety-"
    "action-authority-effectiveness-admission-result-audit"
)
M3200_ID = (
    "m3200-engineering-controller-active-safety-driver-residual-hard-safety-"
    "preterminal-authority-boundary-stability-neutral-candidate-vs-incumbent-"
    "trace-delta-diagnostic-result-audit"
)
M3199_ID = (
    "m3199-engineering-controller-active-safety-driver-residual-hard-safety-"
    "preterminal-authority-boundary-stability-neutral-candidate-vs-incumbent-"
    "trace-delta-diagnostic-materialization-preflight"
)

DEFAULT_M3200_AUDIT = Path(f"docs/{M3200_ID}.md")
DEFAULT_M3199_DIR = Path(
    "runs/m3199_engineering_controller_active_safety_driver_residual_hard_safety_"
    "preterminal_authority_boundary_stability_neutral_candidate_vs_incumbent_"
    "trace_delta_diagnostic_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3201_engineering_controller_active_safety_driver_residual_hard_safety_"
    "action_authority_effectiveness_admission_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_TRACE_BINDINGS = 7
EXPECTED_DELTA_SUMMARY_ROWS = 7
EXPECTED_ADMISSION_ROWS = 4
EXPECTED_RECOMMENDED_ROWS = 3
EXPECTED_GUARD_ONLY_ROWS = 1
EXPECTED_COLLISION_ROWS = 5
EXPECTED_OFFTRACK_ROWS = 2
FORBIDDEN_RUNTIME_INPUTS = (
    "source_id|blocker_label|row_outcome|baseline_outcome|target_label|route_label|"
    "progress_label|verdict_label|ttc_oracle|future_terminal_status"
)
CLAIM_SCOPE = (
    "M3201 Active Safety Driver residual hard-safety action-authority/effectiveness "
    "admission materialization only; M3200 audit and M3199 trace-delta diagnostic "
    "artifacts may be converted into actor-visible implementation-admission rows, "
    "contract guard rows, claim rows, gate rows, doc, and M3202 audit manifest. No "
    "reset, step, rollout, replay, policy action, fitting, PPO, training, repair "
    "implementation, validation execution, ranking, winner selection, checkpoint "
    "mutation, checkpoint promotion, public driver default mutation, driver-performance "
    "verdict, current-sim verdict, repair success, robustness-result, high-fidelity "
    "validation, paper evidence, finite-window-vs-GRU evidence, full ideal driver "
    "completion, feasibility proof, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair implementation, validation result, driver-performance verdict, current-sim "
    "verdict, robustness-result, repair success, feasibility proof, checkpoint ranking, "
    "winner selection, checkpoint promotion, public driver default replacement, high-fidelity "
    "validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full "
    "ideal driver completion, or level3 self-identification"
)

ADMISSION_FIELDNAMES = [
    "admission_id",
    "admission_family",
    "admission_role",
    "target_blocker_family",
    "target_evidence_axes",
    "source_trace_count",
    "source_step_count",
    "meaningful_delta_step_count",
    "preterminal_delta_step_count",
    "terminal_window_delta_step_count",
    "outcome_changed_trace_count",
    "candidate_collision_count",
    "candidate_offtrack_count",
    "mean_action_delta_l2",
    "max_action_delta_l2",
    "mean_abs_steer_delta",
    "mean_abs_throttle_delta",
    "mean_abs_brake_delta",
    "steer_delta_positive_count",
    "steer_delta_negative_count",
    "throttle_drop_count",
    "brake_add_count",
    "candidate_clip_step_count",
    "incumbent_clip_step_count",
    "clearance_margin_delta_mean",
    "implementation_admission_recommended",
    "implementation_allowed_now",
    "requires_m3202_audit",
    "actor_runtime_input_contract",
    "allowed_actor_visible_signals",
    "forbidden_actor_inputs",
    "admitted_design_pressure",
    "expected_action_authority_change",
    "proof_gate_required",
    "offline_diagnostic_inputs_used",
    "hidden_actor_inputs_used",
    "repair_success_claim_made",
    "claim_boundary",
]
CONTRACT_GUARD_FIELDNAMES = [
    "guard_id",
    "guard_family",
    "observed_value",
    "expected_value",
    "status_pass",
    "actor_runtime_allowed",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3201",
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
        "action_authority_effectiveness_admission_rows": output_dir
        / "action_authority_effectiveness_admission_rows.csv",
        "contract_guard_rows": output_dir / "contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3200_audit: Path, m3199_dir: Path) -> dict[str, Any]:
    paths = {
        "m3200_audit": m3200_audit,
        "m3199_summary": m3199_dir / "summary.json",
        "m3199_candidate_trace_execution_rows": m3199_dir / "candidate_trace_execution_rows.csv",
        "m3199_trace_delta_rows": m3199_dir / "trace_delta_rows.csv",
        "m3199_trace_delta_summary_rows": m3199_dir / "trace_delta_summary_rows.csv",
        "m3199_contract_guard_rows": m3199_dir / "contract_guard_rows.csv",
        "m3199_claim_boundary_rows": m3199_dir / "claim_boundary_rows.csv",
        "m3199_gate_rows": m3199_dir / "gate_matrix.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3200_audit_text": paths["m3200_audit"].read_text(encoding="utf-8") if exists["m3200_audit"] else "",
        "m3199_summary": read_json(paths["m3199_summary"]) if exists["m3199_summary"] else {},
        "m3199_candidate_trace_execution_rows": read_csv_rows(paths["m3199_candidate_trace_execution_rows"]),
        "m3199_trace_delta_rows": read_csv_rows(paths["m3199_trace_delta_rows"]),
        "m3199_trace_delta_summary_rows": read_csv_rows(paths["m3199_trace_delta_summary_rows"]),
        "m3199_contract_guard_rows": read_csv_rows(paths["m3199_contract_guard_rows"]),
        "m3199_claim_boundary_rows": read_csv_rows(paths["m3199_claim_boundary_rows"]),
        "m3199_gate_rows": read_csv_rows(paths["m3199_gate_rows"]),
    }


def _subset_stats(
    summaries: list[dict[str, Any]],
    deltas: list[dict[str, Any]],
    *,
    blocker_family: str | None = None,
    evidence_axis_contains: str | None = None,
) -> dict[str, Any]:
    selected_summaries = []
    for row in summaries:
        if blocker_family is not None and str(row.get("blocker_family", "")) != blocker_family:
            continue
        if evidence_axis_contains is not None and evidence_axis_contains not in str(row.get("evidence_axis", "")):
            continue
        selected_summaries.append(row)
    binding_ids = {str(row.get("trace_source_binding_id", "")) for row in selected_summaries}
    selected_deltas = [row for row in deltas if str(row.get("trace_source_binding_id", "")) in binding_ids]
    sign_counts = Counter(str(row.get("steer_delta_sign", "")) for row in selected_deltas)
    axes = "|".join(sorted({str(row.get("evidence_axis", "")) for row in selected_summaries if row.get("evidence_axis")}))
    return {
        "target_evidence_axes": axes,
        "source_trace_count": len(selected_summaries),
        "source_step_count": sum(int(_float(row.get("candidate_steps"))) for row in selected_summaries),
        "meaningful_delta_step_count": sum(int(_float(row.get("meaningful_delta_step_count"))) for row in selected_summaries),
        "preterminal_delta_step_count": sum(int(_float(row.get("preterminal_delta_step_count"))) for row in selected_summaries),
        "terminal_window_delta_step_count": sum(int(_float(row.get("terminal_window_delta_step_count"))) for row in selected_summaries),
        "outcome_changed_trace_count": sum(_bool(row.get("outcome_changed")) for row in selected_summaries),
        "candidate_collision_count": sum(_bool(row.get("candidate_collision")) for row in selected_summaries),
        "candidate_offtrack_count": sum(_bool(row.get("candidate_offtrack")) for row in selected_summaries),
        "mean_action_delta_l2": _mean(_float(row.get("action_delta_l2")) for row in selected_deltas),
        "max_action_delta_l2": max((_float(row.get("action_delta_l2")) for row in selected_deltas), default=0.0),
        "mean_abs_steer_delta": _mean(_float(row.get("abs_steer_delta")) for row in selected_deltas),
        "mean_abs_throttle_delta": _mean(_float(row.get("abs_throttle_delta")) for row in selected_deltas),
        "mean_abs_brake_delta": _mean(_float(row.get("abs_brake_delta")) for row in selected_deltas),
        "steer_delta_positive_count": int(sign_counts.get("positive", 0)),
        "steer_delta_negative_count": int(sign_counts.get("negative", 0)),
        "throttle_drop_count": sum(str(row.get("throttle_delta_sign")) == "negative" for row in selected_deltas),
        "brake_add_count": sum(str(row.get("brake_delta_sign")) == "positive" for row in selected_deltas),
        "candidate_clip_step_count": sum(_bool(row.get("candidate_clip_hit")) for row in selected_deltas),
        "incumbent_clip_step_count": sum(_bool(row.get("incumbent_clip_hit")) for row in selected_deltas),
        "clearance_margin_delta_mean": _mean(_float(row.get("clearance_margin_delta")) for row in selected_summaries),
    }


def action_authority_effectiveness_admission_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    summaries = list(source.get("m3199_trace_delta_summary_rows", []))
    deltas = list(source.get("m3199_trace_delta_rows", []))
    collision = _subset_stats(summaries, deltas, blocker_family="collision")
    offtrack = _subset_stats(summaries, deltas, blocker_family="offtrack")
    all_stats = _subset_stats(summaries, deltas)
    collision_boundary = _subset_stats(summaries, deltas, blocker_family="collision", evidence_axis_contains="boundary")
    specs = [
        (
            "longitudinal_collision_authority_effectiveness_gap",
            "implementation_candidate_after_audit",
            "collision",
            collision,
            "obs72 ego speed obstacle geometry proxy relative clearance proxy lane corridor geometry",
            "current throttle-drop/brake-add overlay engages preterminally but collision outcomes remain",
            "stronger and earlier longitudinal authority with bounded low-speed and recovery guards",
        ),
        (
            "lateral_collision_clearance_authority_effectiveness_gap",
            "implementation_candidate_after_audit",
            "collision",
            collision_boundary if collision_boundary["source_trace_count"] else collision,
            "obs72 obstacle geometry proxy lane corridor geometry lateral error heading alignment",
            "current steering deltas are bounded and outcome-neutral on collision boundary-recovery traces",
            "larger corridor-aware steering authority with action-rate and offtrack guards",
        ),
        (
            "boundary_recovery_override_authority_effectiveness_gap",
            "implementation_candidate_after_audit",
            "offtrack",
            offtrack,
            "obs72 lane boundary geometry lateral error heading alignment sideslip proxy ego speed",
            "current boundary recovery steering/brake/throttle deltas are preterminal but offtrack remains",
            "higher-priority boundary recovery override with stability damping and speed-preservation guard",
        ),
        (
            "action_effectiveness_saturation_guard",
            "cross_cutting_guard_only",
            "collision|offtrack",
            all_stats,
            "offline public action telemetry for guard design only not standalone runtime thesis",
            "candidate and incumbent both reach clip surfaces; stronger authority must remain bounded",
            "guard stronger candidates against terminal-only saturation and excessive action-rate changes",
        ),
    ]
    rows: list[dict[str, Any]] = []
    for index, (family, role, blocker, stats, allowed, pressure, action_change) in enumerate(specs, start=1):
        guard_only = role == "cross_cutting_guard_only"
        recommended = bool(
            not guard_only
            and stats["source_trace_count"] > 0
            and stats["preterminal_delta_step_count"] > 0
            and stats["outcome_changed_trace_count"] == 0
        )
        rows.append(
            {
                "admission_id": f"m3201-action-authority-effectiveness-admission-{index:04d}",
                "admission_family": family,
                "admission_role": role,
                "target_blocker_family": blocker,
                **stats,
                "implementation_admission_recommended": recommended,
                "implementation_allowed_now": False,
                "requires_m3202_audit": True,
                "actor_runtime_input_contract": "obs72_only_direct_action3",
                "allowed_actor_visible_signals": allowed,
                "forbidden_actor_inputs": FORBIDDEN_RUNTIME_INPUTS,
                "admitted_design_pressure": pressure,
                "expected_action_authority_change": action_change,
                "proof_gate_required": "post-implementation same-seven residual trace measurement plus full-fresh denominator audit before validation",
                "offline_diagnostic_inputs_used": "M3199 trace_delta_rows|trace_delta_summary_rows|candidate_trace_execution_rows",
                "hidden_actor_inputs_used": False,
                "repair_success_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def contract_guard_rows(source: Mapping[str, Any], admissions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary = source.get("m3199_summary", {})
    hidden_used = _bool(summary.get("hidden_actor_inputs_used")) or any(
        _bool(row.get("hidden_actor_inputs_used")) for row in admissions
    )
    return [
        guard("source_artifacts_present", "source", all(source["source_exists"].values()), True),
        guard("m3199_status_pass", "lineage", _bool(summary.get("status_pass")), True),
        guard("m3199_gate_matrix_pass", "lineage", _bool(summary.get("gate_matrix_pass")), True),
        guard("m3199_trace_delta_rows", "evidence", len(source["m3199_trace_delta_rows"]), int(_float(summary.get("trace_delta_row_count")))),
        guard("m3199_trace_delta_summary_rows", "evidence", len(source["m3199_trace_delta_summary_rows"]), EXPECTED_DELTA_SUMMARY_ROWS),
        guard("actor_runtime_input_contract", "contract", summary.get("actor_runtime_input_contract"), "obs72_only_direct_action3"),
        guard("action_components", "contract", "|".join(summary.get("action_components", [])), "steer|throttle|brake"),
        guard("hidden_actor_inputs_used", "contract", hidden_used, False),
        guard("public_driver_default_mutated", "contract", _bool(summary.get("public_driver_default_mutated")), False),
        guard("validation_run", "claim", _bool(summary.get("validation_run")), False),
        guard("repair_success_claim_made", "claim", _bool(summary.get("repair_success_claim_made")), False),
        guard("admission_rows", "admission", len(admissions), EXPECTED_ADMISSION_ROWS),
        guard("implementation_not_allowed_now", "contract", any(_bool(row.get("implementation_allowed_now")) for row in admissions), False),
    ]


def guard(guard_id: str, family: str, observed: Any, expected: Any, *, actor_runtime_allowed: bool = False) -> dict[str, Any]:
    return {
        "guard_id": f"m3201-{guard_id}",
        "guard_family": family,
        "observed_value": observed,
        "expected_value": expected,
        "status_pass": str(observed) == str(expected),
        "actor_runtime_allowed": actor_runtime_allowed,
        "claim_boundary": CLAIM_SCOPE,
    }


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    claims = [
        ("action_authority_effectiveness_admission_rows", "admission_artifact", True, True, "action_authority_effectiveness_admission_rows.csv"),
        ("contract_guard_rows", "contract_artifact", True, True, "contract_guard_rows.csv"),
        ("follow_up_result_audit_registered", "process", True, follow_up_manifest_registered, f"experiments/manifests/{NEXT_ID}.json"),
        ("repair_implementation", "forbidden", False, False, "M3202 audit before any implementation materialization"),
        ("validation_result", "forbidden", False, False, "separate validation execution route"),
        ("driver_performance_verdict", "forbidden", False, False, "future proof generalization and promotion gates"),
        ("current_sim_verdict", "forbidden", False, False, "future audited result synthesis"),
        ("repair_success", "forbidden", False, False, "accepted measurement improvement plus validation route"),
        ("ranking_or_winner_selection", "forbidden", False, False, "future audited ranking route"),
        ("checkpoint_promotion", "forbidden", False, False, "promotion gate"),
        ("public_driver_default_mutation", "forbidden", False, False, "future admitted implementation route"),
        ("self_id", "forbidden", False, False, "history necessity tests outside M3201"),
    ]
    return [
        {
            "claim_id": f"m3201-{claim_id}",
            "claim_family": family,
            "allowed_in_m3201": allowed,
            "claim_made": made,
            "status_pass": bool(made) == bool(allowed) if allowed else not bool(made),
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, allowed, made, evidence in claims
    ]


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m3201-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def _m3200_selects_m3201(text: str) -> bool:
    return (
        "m3201-engineering-controller-active-safety-driver-residual-hard-safety-action-authority-effectiveness-admission-materialization-preflight"
        in text
        or "action-authority/effectiveness admission" in text
    )


def gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    admissions: list[dict[str, Any]],
    guards: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    summary = source["m3199_summary"]
    families = {str(row.get("admission_family", "")) for row in admissions}
    recommended = [row for row in admissions if _bool(row.get("implementation_admission_recommended"))]
    guard_only = [row for row in admissions if str(row.get("admission_role", "")) == "cross_cutting_guard_only"]
    outcome_changed = sum(_bool(row.get("outcome_changed")) for row in source["m3199_trace_delta_summary_rows"])
    blocker_counts = Counter(str(row.get("blocker_family", "")) for row in source["m3199_trace_delta_summary_rows"])
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3200_selects_m3201_route", "lineage", _m3200_selects_m3201(source["m3200_audit_text"]), "route marker", "present", "lineage_invalid"),
        gate("m3199_status_pass", "lineage", _bool(summary.get("status_pass")), summary.get("status_pass"), True, "lineage_invalid"),
        gate("m3199_gate_matrix_pass", "lineage", _bool(summary.get("gate_matrix_pass")), summary.get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("trace_binding_count", "evidence", int(_float(summary.get("candidate_trace_execution_row_count"))) == EXPECTED_TRACE_BINDINGS, summary.get("candidate_trace_execution_row_count"), EXPECTED_TRACE_BINDINGS, "metric_artifact"),
        gate("trace_delta_summary_rows", "evidence", len(source["m3199_trace_delta_summary_rows"]) == EXPECTED_DELTA_SUMMARY_ROWS, len(source["m3199_trace_delta_summary_rows"]), EXPECTED_DELTA_SUMMARY_ROWS, "metric_artifact"),
        gate("residual_outcome_counts", "evidence", blocker_counts.get("collision", 0) == EXPECTED_COLLISION_ROWS and blocker_counts.get("offtrack", 0) == EXPECTED_OFFTRACK_ROWS, dict(blocker_counts), f"{EXPECTED_COLLISION_ROWS} collision {EXPECTED_OFFTRACK_ROWS} offtrack", "metric_artifact"),
        gate("preterminal_deltas_exist", "evidence", int(_float(summary.get("preterminal_delta_step_count"))) > 0, summary.get("preterminal_delta_step_count"), ">0", "metric_artifact"),
        gate("outcome_neutral", "evidence", outcome_changed == 0 and int(_float(summary.get("outcome_changed_trace_count"))) == 0, outcome_changed, 0, "behavior_regression"),
        gate("admission_rows", "admission", len(admissions) == EXPECTED_ADMISSION_ROWS, len(admissions), EXPECTED_ADMISSION_ROWS, "metric_artifact"),
        gate("required_admission_families", "admission", {"longitudinal_collision_authority_effectiveness_gap", "lateral_collision_clearance_authority_effectiveness_gap", "boundary_recovery_override_authority_effectiveness_gap", "action_effectiveness_saturation_guard"}.issubset(families), sorted(families), "all required", "metric_artifact"),
        gate("recommended_rows", "admission", len(recommended) == EXPECTED_RECOMMENDED_ROWS, len(recommended), EXPECTED_RECOMMENDED_ROWS, "objective_overfit"),
        gate("guard_only_row", "admission", len(guard_only) == EXPECTED_GUARD_ONLY_ROWS and not any(_bool(row.get("implementation_admission_recommended")) for row in guard_only), len(guard_only), EXPECTED_GUARD_ONLY_ROWS, "objective_overfit"),
        gate("implementation_not_allowed_now", "contract", not any(_bool(row.get("implementation_allowed_now")) for row in admissions), "none", "allowed", "contract_violation"),
        gate("actor_runtime_obs72_only", "contract", all(str(row.get("actor_runtime_input_contract", "")) == "obs72_only_direct_action3" for row in admissions), "all", "obs72_only_direct_action3", "contract_violation"),
        gate("hidden_inputs_not_used", "contract", not any(_bool(row.get("hidden_actor_inputs_used")) for row in admissions) and not _bool(summary.get("hidden_actor_inputs_used")), "none", "used", "contract_violation"),
        gate("contract_guards_pass", "contract", all(_bool(row.get("status_pass")) for row in guards), "all", "pass", "contract_violation"),
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
        "priority": 32020,
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
        "hypothesis": "A bounded result audit can accept or reject M3201 action-authority/effectiveness admission artifacts before any implementation materialization validation or stop.",
        "lineage": {
            "parent_checkpoint": [str(doc_path)],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "action_authority_effectiveness_admission_rows.csv"),
                str(output_dir / "contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit M3201 action-authority/effectiveness admission artifacts"],
            "derived_from": [MILESTONE_ID, M3200_ID, M3199_ID],
            "blocked_by": [
                "M3201 admission rows require audit before implementation materialization",
                "M3201 is admission materialization only and not repair implementation",
            ],
            "supersedes": ["direct stronger-authority implementation without audited admission rows"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3202 must audit M3201 admission rows guards claims and gates",
            "M3202 must preserve obs72-only direct action runtime and public driver unchanged",
            "M3202 must reject validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3202 must select implementation materialization artifact-repair synthesis or stop as exactly one route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not implement repair logic in M3202",
            "do not convert admission rows into validation repair-success performance current-sim robustness-result paper or self-ID claims",
            "do not change actor input action contract or public driver default",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_hard_safety_action_authority_effectiveness",
            "evidence_axis": "action_authority_effectiveness_admission_result_audit",
            "evidence_increment": "audits M3201 admission artifacts before implementation materialization",
            "claim_scope": "Result audit only; no repair implementation validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "stop_condition": [
                "stop if M3201 artifacts are missing or gate matrix fails",
                "stop if admission requires hidden actor inputs",
                "route to implementation materialization only after M3202 accepts claim boundaries",
            ],
            "fallback_plan": [
                "route to M3201 artifact repair if rows or guards fail",
                "route to synthesis if no actor-visible action-effectiveness implementation axis remains",
                "preserve M3105/M3103 incumbent until later accepted measurement improves hard-safety counts",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3201 materializes admission artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3201 action-authority/effectiveness admission artifacts",
            "admission_evidence": ["M3201 summary admission guard claim and gate artifacts"],
            "blocked_shortcuts": [
                "no repair implementation validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim",
                "no checkpoint mutation profile tuning or public driver mutation",
                "no hidden oracle target TTC source route outcome progress verdict actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3202 status queue scoreboard research log and review",
                "one follow-up manifest only if M3202 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3202 accepts or rejects M3201 as complete and claim-safe",
                "next implementation materialization artifact-repair synthesis or stop route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3202 audits engineering admission artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3202; self-ID and GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3201 admission artifacts only.",
            "negative_result_policy": "Preserve admission evidence and route implementation materialization or stop rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3201 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 1,
            "evidence_expansion": "audits action-authority/effectiveness admission before implementation route",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3202 audits engineering admission evidence",
            "must_synthesize_if": [
                "M3202 cannot select implementation materialization artifact-repair synthesis or stop",
                "M3202 would claim repair-success validation driver-performance current-sim verdict robustness-result or self-ID evidence",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3202 audits M3201 row counts gates actor contract and claim boundaries",
            "M3202 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3202 hides missing M3201 artifacts or failed gates",
            "M3202 treats M3201 admission as repair success or performance verdict",
            "M3202 changes actor input or action contract",
            "M3202 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3202 audits M3201 artifacts and selects one next route or stop state while preserving actor direct-action and claim boundaries without overclaiming.",
        "commands": [
            {
                "name": "active_safety_driver_action_authority_effectiveness_admission_result_audit_doc",
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
            "# M3201 Action-Authority/Effectiveness Admission Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- admission rows: {summary['admission_row_count']}",
            f"- implementation recommended rows: {summary['implementation_recommended_count']}",
            f"- guard-only rows: {summary['guard_only_count']}",
            f"- M3199 trace delta rows: {summary['m3199_trace_delta_row_count']}",
            f"- M3199 outcome-changed traces: {summary['outcome_changed_trace_count']}",
            f"- implementation allowed now: {summary['implementation_allowed_now']}",
            f"- public driver default mutated: {summary['public_driver_default_mutated']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Interpretation",
            "",
            "M3201 materializes actor-visible implementation-admission contracts for stronger action-authority/effectiveness routes. The evidence is M3199's preterminal action-delta but outcome-neutral residual trace diagnostic: the M3194 candidate changed actions, but the five collision and two offtrack outcomes did not change. M3201 does not implement a repair or admit validation.",
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


def run_action_authority_effectiveness_admission_materialization_preflight(
    *,
    m3200_audit: Path,
    m3199_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(m3200_audit=m3200_audit, m3199_dir=m3199_dir)
    admissions = action_authority_effectiveness_admission_rows(source)
    follow_up_payload = build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path)
    write_json(paths["follow_up_manifest"], follow_up_payload)
    guards = contract_guard_rows(source, admissions)
    claims = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    write_csv_rows(paths["action_authority_effectiveness_admission_rows"], admissions, fieldnames=ADMISSION_FIELDNAMES)
    write_csv_rows(paths["contract_guard_rows"], guards, fieldnames=CONTRACT_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claims, fieldnames=CLAIM_FIELDNAMES)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        admissions=admissions,
        guards=guards,
        claims=claims,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass")) for row in gates)
    implementation_recommended = sum(_bool(row.get("implementation_admission_recommended")) for row in admissions)
    guard_only = sum(str(row.get("admission_role", "")) == "cross_cutting_guard_only" for row in admissions)
    implementation_allowed_now = any(_bool(row.get("implementation_allowed_now")) for row in admissions)
    outcome_changed = sum(_bool(row.get("outcome_changed")) for row in source["m3199_trace_delta_summary_rows"])
    status_pass = bool(
        gate_matrix_pass
        and implementation_recommended == EXPECTED_RECOMMENDED_ROWS
        and guard_only == EXPECTED_GUARD_ONLY_ROWS
        and not implementation_allowed_now
    )
    summary = {
        "milestone_id": MILESTONE_ID,
        "created_at_utc": utc_timestamp(),
        "result_class": "action_authority_effectiveness_admission_materialized" if status_pass else "action_authority_effectiveness_admission_incomplete",
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "source_artifacts_present": all(source["source_exists"].values()),
        "m3199_status_pass": _bool(source["m3199_summary"].get("status_pass")),
        "m3199_gate_matrix_pass": _bool(source["m3199_summary"].get("gate_matrix_pass")),
        "m3199_trace_delta_row_count": len(source["m3199_trace_delta_rows"]),
        "m3199_trace_delta_summary_row_count": len(source["m3199_trace_delta_summary_rows"]),
        "m3199_candidate_trace_execution_row_count": len(source["m3199_candidate_trace_execution_rows"]),
        "outcome_changed_trace_count": outcome_changed,
        "admission_row_count": len(admissions),
        "implementation_recommended_count": implementation_recommended,
        "guard_only_count": guard_only,
        "contract_guard_row_count": len(guards),
        "claim_boundary_row_count": len(claims),
        "implementation_allowed_now": implementation_allowed_now,
        "requires_m3202_audit": True,
        "actor_runtime_input_contract": "obs72_only_direct_action3",
        "public_driver_default_mutated": False,
        "validation_run": False,
        "repair_implementation_run": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "robustness_result_claim_made": False,
        "self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "follow_up_manifest_exists": paths["follow_up_manifest"].exists(),
        "next_blocker": NEXT_ID,
        "paths": {key: str(path) for key, path in paths.items()},
    }
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "admission_row_count": len(admissions),
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
    parser.add_argument("--m3200-audit", type=Path, default=DEFAULT_M3200_AUDIT)
    parser.add_argument("--m3199-dir", type=Path, default=DEFAULT_M3199_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    summary = run_action_authority_effectiveness_admission_materialization_preflight(
        m3200_audit=args.m3200_audit,
        m3199_dir=args.m3199_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(summary)


if __name__ == "__main__":
    main()
