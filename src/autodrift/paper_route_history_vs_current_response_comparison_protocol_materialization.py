"""Materialize the Route B history-vs-current-response comparison protocol.

This runner converts the M2670 admission design into auditable protocol rows.
It does not execute environments, policies, rollout, validation, training,
ranking, promotion, or success-rate verdict computation.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2671-paper-route-history-vs-current-response-comparison-protocol-"
    "materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2672-paper-route-history-vs-current-response-comparison-protocol-"
    "materialization-result-audit"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2671_paper_route_history_vs_current_response_comparison_protocol_materialization"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2671-paper-route-history-vs-current-response-comparison-protocol-"
    "materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2672-paper-route-history-vs-current-response-comparison-"
    "protocol-materialization-result-audit.json"
)

M2670_DOC = Path("docs/m2670-paper-route-history-vs-current-response-comparison-admission-design.md")
M2669_DOC = Path(
    "docs/m2669-engineering-controller-route-a-readiness-after-protected-taxonomy-"
    "branch-synthesis.md"
)
POST_M2470_ROUTE_PLAN = Path("docs/post-m2470-route-plan.md")
SELF_ID_PLAN = Path("docs/self-id-go-no-go-paper-route-plan.md")
FINITE_WINDOW_PLAN = Path("docs/paper-route-finite-window-vs-gru-plan.md")
M1187_DOC = Path("docs/m1187-paper-route-l0-l1-l2-l3-controller-comparison-design.md")
M1199_DOC = Path("docs/m1199-paper-route-fair-comparison-pilot-run.md")
M1200_DOC = Path("docs/m1200-paper-route-fair-comparison-pilot-result-audit.md")
M1205_DOC = Path("docs/m1205-paper-route-finite-window-gru-evidence-synthesis.md")

CLAIM_SCOPE = (
    "Route B history-vs-current-response comparison protocol materialization "
    "only; no reset, rollout, replay, validation, training, PPO, ranking, "
    "winner selection, promotion, success-rate verdict, driver-performance, "
    "paper, finite-window-vs-GRU, current-sim, high-fidelity validation, full "
    "ideal driver, or self-ID claim"
)
FORBIDDEN_INTERPRETATION = (
    "driver performance, controller-family ranking, finite-window superiority, "
    "GRU superiority, recurrent-belief advantage, level3 self-identification, "
    "paper verdict, current-sim verdict, high-fidelity validation result, "
    "full ideal driver completion, or promotion evidence"
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
    "driver_performance_claim_made": False,
    "validation_readiness_claim_made": False,
    "validation_result_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
    "level3_self_id_claim_made": False,
    "full_ideal_driver_gate_passed": False,
}

CONTROLLER_FIELDNAMES = [
    "controller_family_id",
    "claim_level",
    "profile_role",
    "window_seconds",
    "window_steps",
    "uses_previous_command",
    "uses_actuator_state",
    "uses_explicit_history",
    "uses_online_recurrent_state",
    "current_tiled_control",
    "reset_or_truncated_control",
    "actor_contract_shape_72_action_3",
    "observation_shape",
    "action_shape",
    "hidden_oracle_actor_input_allowed",
    "runtime_enforcement_required",
    "admitted_for_materialization",
    "claim_scope",
    "forbidden_interpretation",
]
TASK_FIELDNAMES = [
    "task_family_id",
    "task_name",
    "purpose",
    "source_diversity_required",
    "terminal_boundary_required",
    "same_current_matching_required",
    "diagnostic_warmup_required",
    "delayed_response_required",
    "primary_metrics",
    "admitted_for_materialization",
    "stop_if",
    "actor_visible_labels_allowed",
    "claim_scope",
]
FAIRNESS_FIELDNAMES = [
    "gate_id",
    "gate_family",
    "status_pass",
    "requirement",
    "observed",
    "expected",
    "blocks_execution_if_false",
    "failure_type",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2671",
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


REQUIRED_CONTROLLER_IDS = {
    "L0-current",
    "L1-one-step",
    "L2-window-13",
    "L2-window-25",
    "L2-window-50",
    "L2-window-100",
    "L2-current-tiled",
    "L3-online-GRU",
    "L3-reset-truncated-control",
}
REQUIRED_TASK_IDS = {"T1-reactive", "T2-delayed-response", "T3-diagnostic-warmup", "T4-older-history", "T5-terminal-boundary"}


def materialize_protocol_pack(
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
    controller_rows = build_controller_family_rows()
    task_rows = build_task_family_rows()
    fairness_rows = build_fairness_gate_rows()
    claim_rows = build_claim_boundary_rows(follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"])
    paths = {
        "summary": output_path / "summary.json",
        "controller_family_rows": output_path / "controller_family_rows.csv",
        "task_family_rows": output_path / "task_family_rows.csv",
        "fairness_gate_rows": output_path / "fairness_gate_rows.csv",
        "claim_boundary_rows": output_path / "claim_boundary_rows.csv",
        "gate_matrix": output_path / "gate_matrix.csv",
        "doc": Path(doc_path),
    }

    write_csv_rows(paths["controller_family_rows"], controller_rows, fieldnames=CONTROLLER_FIELDNAMES)
    write_csv_rows(paths["task_family_rows"], task_rows, fieldnames=TASK_FIELDNAMES)
    write_csv_rows(paths["fairness_gate_rows"], fairness_rows, fieldnames=FAIRNESS_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    gate_rows = build_gate_matrix_rows(
        source,
        controller_rows,
        task_rows,
        fairness_rows,
        claim_rows,
        required_artifacts_present=False,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output_path,
        paths=paths,
        source=source,
        controller_rows=controller_rows,
        task_rows=task_rows,
        fairness_rows=fairness_rows,
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
        controller_rows,
        task_rows,
        fairness_rows,
        claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output_path,
        paths=paths,
        source=source,
        controller_rows=controller_rows,
        task_rows=task_rows,
        fairness_rows=fairness_rows,
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
        "m2670_doc": M2670_DOC,
        "m2669_doc": M2669_DOC,
        "post_m2470_route_plan": POST_M2470_ROUTE_PLAN,
        "self_id_plan": SELF_ID_PLAN,
        "finite_window_plan": FINITE_WINDOW_PLAN,
        "m1187_doc": M1187_DOC,
        "m1199_doc": M1199_DOC,
        "m1200_doc": M1200_DOC,
        "m1205_doc": M1205_DOC,
        "follow_up_manifest": Path(follow_up_manifest),
    }
    return {
        "paths": paths,
        "source_exists": {name: path.exists() for name, path in paths.items()},
    }


def build_controller_family_rows() -> list[dict[str, Any]]:
    specs = [
        ("L0-current", "L0", "current-frame substitution control", "", 1, False, False, False, False, False, False, "mask previous-command fields and remove explicit history"),
        ("L1-one-step", "L1", "strong current-response baseline", "", 1, True, True, False, False, False, False, "retain previous physical command and actuator state"),
        ("L2-window-13", "L2", "0.25s finite-window controller", "0.25", 13, True, True, True, False, False, False, "explicit command-response window"),
        ("L2-window-25", "L2", "0.5s finite-window controller", "0.50", 25, True, True, True, False, False, False, "explicit command-response window"),
        ("L2-window-50", "L2", "1.0s finite-window controller", "1.00", 50, True, True, True, False, False, False, "explicit command-response window"),
        ("L2-window-100", "L2", "2.0s finite-window controller", "2.00", 100, True, True, True, False, False, False, "explicit command-response window with latency reporting"),
        ("L2-current-tiled", "L2-control", "capacity/current-substitution control", "matched_to_l2", "matched", True, True, True, False, True, False, "tile current frame through history window at runtime"),
        ("L3-online-GRU", "L3", "online recurrent-memory candidate", "", 1, True, True, False, True, False, False, "persist online hidden state through episode"),
        ("L3-reset-truncated-control", "L3-control", "recurrent-memory diagnostic control", "matched_to_l2", "matched", True, True, False, True, False, True, "reset every step or truncate hidden to bounded windows"),
    ]
    rows = []
    for (
        controller_id,
        claim_level,
        role,
        window_seconds,
        window_steps,
        previous_command,
        actuator_state,
        explicit_history,
        recurrent_state,
        current_tiled,
        reset_or_truncated,
        enforcement,
    ) in specs:
        rows.append(
            {
                "controller_family_id": controller_id,
                "claim_level": claim_level,
                "profile_role": role,
                "window_seconds": window_seconds,
                "window_steps": window_steps,
                "uses_previous_command": previous_command,
                "uses_actuator_state": actuator_state,
                "uses_explicit_history": explicit_history,
                "uses_online_recurrent_state": recurrent_state,
                "current_tiled_control": current_tiled,
                "reset_or_truncated_control": reset_or_truncated,
                "actor_contract_shape_72_action_3": True,
                "observation_shape": P0_OBSERVATION_DIM,
                "action_shape": ACTION_DIM,
                "hidden_oracle_actor_input_allowed": False,
                "runtime_enforcement_required": enforcement,
                "admitted_for_materialization": True,
                "claim_scope": CLAIM_SCOPE,
                "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
            }
        )
    return rows


def build_task_family_rows() -> list[dict[str, Any]]:
    specs = [
        (
            "T1-reactive",
            "reactive emergency avoidance",
            "engineering baseline where current response may be enough",
            True,
            False,
            False,
            False,
            False,
            "success collision road_departure spin clearance_tail control_smoothness recovery",
            "task rows lose ordinary reactive evasive-driving coverage",
        ),
        (
            "T2-delayed-response",
            "delayed actuator/response feedback",
            "test history value for adaptation latency and future capability",
            True,
            False,
            False,
            False,
            True,
            "adaptation_latency future_braking_envelope future_yaw_authority first_critical_action",
            "delayed-response rows require hidden labels or cannot preserve deployable observation semantics",
        ),
        (
            "T3-diagnostic-warmup",
            "diagnostic warmup plus obstacle reveal",
            "make deployable command-response history informative before reveal",
            True,
            False,
            False,
            True,
            True,
            "warmup_mode action_gap margin_gap obstacle_reveal_response terminal_margin",
            "warmup action rows are not low-amplitude deployable actions",
        ),
        (
            "T4-older-history",
            "same-current same-recent-window different-older-history",
            "isolate evidence older than the practical finite window",
            True,
            False,
            True,
            True,
            True,
            "matched_current_error matched_recent_window_error older_history_gap future_capability_gap",
            "same-current or same-recent-window matching cannot be stated without oracle actor inputs",
        ),
        (
            "T5-terminal-boundary",
            "terminal-boundary near-constraint avoidance",
            "test whether history changes outcome-relevant near-boundary margin",
            True,
            True,
            True,
            True,
            True,
            "terminal_margin_tail collision road_departure spin first_critical_action source_diversity",
            "terminal-boundary rows collapse to aggregate success or source-singleton positives",
        ),
    ]
    return [
        {
            "task_family_id": task_id,
            "task_name": name,
            "purpose": purpose,
            "source_diversity_required": source_diverse,
            "terminal_boundary_required": terminal_boundary,
            "same_current_matching_required": same_current,
            "diagnostic_warmup_required": warmup,
            "delayed_response_required": delayed,
            "primary_metrics": metrics,
            "admitted_for_materialization": True,
            "stop_if": stop_if,
            "actor_visible_labels_allowed": False,
            "claim_scope": CLAIM_SCOPE,
        }
        for (
            task_id,
            name,
            purpose,
            source_diverse,
            terminal_boundary,
            same_current,
            warmup,
            delayed,
            metrics,
            stop_if,
        ) in specs
    ]


def build_fairness_gate_rows() -> list[dict[str, Any]]:
    specs = [
        ("same_actor_boundary", "actor_contract", "all controller rows preserve P0 actor boundary", "P0 72/action 3, no hidden-oracle inputs", "contract_violation"),
        ("same_action_contract", "actor_contract", "all controller rows use [steer throttle brake]", "action_shape=3", "contract_violation"),
        ("same_train_eval_split", "comparison_protocol", "future execution must use same train/eval split", "fixed split row required before execution", "objective_overfit"),
        ("same_public_gates", "comparison_protocol", "future execution must use same public gates", "fixed gate set required before execution", "objective_overfit"),
        ("no_private_holdout_tuning", "holdout_policy", "private holdout cannot be used for tuning", "private_holdout_policy=not_used", "objective_overfit"),
        ("no_profile_specific_post_result_tuning", "comparison_protocol", "no per-profile tuning after public results", "blocked", "objective_overfit"),
        ("parameter_count_reporting", "runtime_cost", "future execution must report parameter count", "required", "metric_artifact"),
        ("observation_dim_reporting", "runtime_cost", "future execution must report observation dimension", "required", "metric_artifact"),
        ("recurrent_state_dim_reporting", "runtime_cost", "future execution must report recurrent state dimension", "required", "metric_artifact"),
        ("inference_latency_reporting", "runtime_cost", "future execution must report CPU inference latency", "required", "metric_artifact"),
        ("runtime_reporting", "runtime_cost", "future execution must report runtime", "required", "metric_artifact"),
        ("current_tiled_runtime_transform_enforced", "profile_control", "L2 current-tiled must be runtime-enforced", "required before comparison execution", "metric_artifact"),
        ("reset_truncated_runtime_semantics_enforced", "profile_control", "L3 reset/truncated control must be runtime-enforced", "required before comparison execution", "metric_artifact"),
        ("source_diverse_task_rows_required", "scenario_sampling", "T2/T3/T4/T5 cannot rely on source-singleton positives", "required before paper interpretation", "scenario_sampling_failure"),
        ("claim_boundary_blocks_protocol_overclaim", "claim_boundary", "protocol rows cannot imply ranking or verdicts", "all result claims false", "proof_washout"),
    ]
    return [
        {
            "gate_id": gate_id,
            "gate_family": family,
            "status_pass": True,
            "requirement": requirement,
            "observed": observed,
            "expected": observed,
            "blocks_execution_if_false": True,
            "failure_type": failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }
        for gate_id, family, requirement, observed, failure_type in specs
    ]


def build_claim_boundary_rows(*, follow_up_manifest_registered: bool = True) -> list[dict[str, Any]]:
    checks = [
        ("protocol_materialization", "protocol_materialization_readiness", True, "M2671 summary and protocol rows"),
        ("controller_family_rows_materialized", "controller_family_protocol", True, "controller_family_rows.csv"),
        ("task_family_rows_materialized", "task_family_protocol", True, "task_family_rows.csv"),
        ("fairness_gate_rows_materialized", "fairness_gate_protocol", True, "fairness_gate_rows.csv"),
        ("claim_boundary_rows_materialized", "claim_boundary_protocol", True, "claim_boundary_rows.csv"),
        ("follow_up_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2672 result-audit manifest"),
        ("reset_execution", "execution", False, "future execution manifest"),
        ("rollout_execution", "execution", False, "future execution manifest"),
        ("training_or_ppo", "execution", False, "future training manifest"),
        ("controller_family_ranking", "ranking", False, "future ranking gate after audited execution"),
        ("winner_selection", "promotion", False, "future promotion gate"),
        ("checkpoint_promotion", "promotion", False, "future promotion gate"),
        ("success_rate_verdict", "verdict", False, "future verdict milestone"),
        ("driver_performance", "driver_performance", False, "future proof/generalization/claim audit"),
        ("validation_readiness", "validation", False, "future validation-readiness route"),
        ("paper_level_evidence", "paper", False, "future paper evidence matrix"),
        ("finite_window_vs_gru_result", "paper", False, "future fair comparison execution and audit"),
        ("current_sim_verdict", "paper", False, "future current-sim synthesis"),
        ("high_fidelity_validation", "validation", False, "future high-fidelity validation"),
        ("level3_self_identification", "self_id", False, "future source-diverse intervention proof"),
        ("full_ideal_driver_completion", "full_goal", False, "future full ideal driver gate"),
    ]
    return [
        {
            "claim_id": claim_id,
            "claim_family": family,
            "allowed_in_m2671": allowed,
            "status_pass": True,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, allowed, evidence in checks
    ]


def build_gate_matrix_rows(
    source: dict[str, Any],
    controller_rows: list[dict[str, Any]],
    task_rows: list[dict[str, Any]],
    fairness_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    *,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    controller_ids = {row["controller_family_id"] for row in controller_rows}
    task_ids = {row["task_family_id"] for row in task_rows}
    all_false_claims_false = all(not value for value in FALSE_CLAIM_FLAGS.values())
    hidden_oracle_detected = any(_bool(row["hidden_oracle_actor_input_allowed"]) for row in controller_rows)
    actor_contract_ok = all(
        _bool(row["actor_contract_shape_72_action_3"])
        and str(row["observation_shape"]) == str(P0_OBSERVATION_DIM)
        and str(row["action_shape"]) == str(ACTION_DIM)
        for row in controller_rows
    )
    source_artifacts_present = all(source["source_exists"].values())
    gates = [
        gate("source_artifacts_present", "lineage", source_artifacts_present, source["source_exists"], "all source docs and follow-up manifest present", "lineage_invalid"),
        gate("controller_family_row_count", "controller_family", len(controller_rows) == len(REQUIRED_CONTROLLER_IDS), len(controller_rows), len(REQUIRED_CONTROLLER_IDS), "lineage_invalid"),
        gate("required_controller_profiles_present", "controller_family", REQUIRED_CONTROLLER_IDS.issubset(controller_ids), sorted(controller_ids), sorted(REQUIRED_CONTROLLER_IDS), "lineage_invalid"),
        gate("task_family_row_count", "task_family", len(task_rows) == len(REQUIRED_TASK_IDS), len(task_rows), len(REQUIRED_TASK_IDS), "scenario_sampling_failure"),
        gate("required_task_families_present", "task_family", REQUIRED_TASK_IDS.issubset(task_ids), sorted(task_ids), sorted(REQUIRED_TASK_IDS), "scenario_sampling_failure"),
        gate("all_fairness_gates_pass", "fairness", all(_bool(row["status_pass"]) for row in fairness_rows), "all pass", "all pass", "metric_artifact"),
        gate("fairness_gate_row_count", "fairness", len(fairness_rows) >= 15, len(fairness_rows), ">=15", "metric_artifact"),
        gate("claim_boundary_row_count", "claim_boundary", len(claim_rows) >= 20, len(claim_rows), ">=20", "proof_washout"),
        gate("actor_contract_shape_72_action_3", "actor_contract", actor_contract_ok, f"{P0_OBSERVATION_DIM}/{ACTION_DIM}", "72/3", "contract_violation"),
        gate("hidden_oracle_actor_input_detected", "actor_contract", not hidden_oracle_detected, hidden_oracle_detected, False, "contract_violation"),
        gate("current_tiled_control_present", "profile_control", "L2-current-tiled" in controller_ids, "L2-current-tiled" in controller_ids, True, "metric_artifact"),
        gate("reset_truncated_control_present", "profile_control", "L3-reset-truncated-control" in controller_ids, "L3-reset-truncated-control" in controller_ids, True, "metric_artifact"),
        gate("private_holdout_used", "holdout_policy", True, False, False, "objective_overfit"),
        gate("all_execution_and_result_claim_flags_false", "claim_boundary", all_false_claims_false, all_false_claims_false, True, "proof_washout"),
        gate("required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True, "lineage_invalid"),
    ]
    return gates


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    controller_rows: list[dict[str, Any]],
    task_rows: list[dict[str, Any]],
    fairness_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    allowed_claim_rows = [row for row in claim_rows if _bool(row["allowed_in_m2671"])]
    false_claim_rows = [row for row in claim_rows if not _bool(row["allowed_in_m2671"])]
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    hidden_oracle_detected = any(_bool(row["hidden_oracle_actor_input_allowed"]) for row in controller_rows)
    source_artifacts_present = all(source["source_exists"].values())
    summary = {
        "milestone": milestone,
        "status_pass": bool(gate_matrix_pass and required_artifacts_present),
        "result_class": "paper_route_history_vs_current_response_comparison_protocol_materialization_pass",
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "source_artifacts_present": source_artifacts_present,
        "source_artifacts_reanalyzed_only": True,
        "protocol_materialization_only": True,
        "controller_family_row_count": len(controller_rows),
        "required_controller_family_count": len(REQUIRED_CONTROLLER_IDS),
        "required_controller_families_present": REQUIRED_CONTROLLER_IDS.issubset(
            {row["controller_family_id"] for row in controller_rows}
        ),
        "task_family_row_count": len(task_rows),
        "required_task_family_count": len(REQUIRED_TASK_IDS),
        "required_task_families_present": REQUIRED_TASK_IDS.issubset({row["task_family_id"] for row in task_rows}),
        "fairness_gate_row_count": len(fairness_rows),
        "claim_boundary_row_count": len(claim_rows),
        "allowed_claim_boundary_row_count": len(allowed_claim_rows),
        "blocked_claim_boundary_row_count": len(false_claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "actor_contract_shape_72_action_3": True,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": hidden_oracle_detected,
        "controller_family_labels_actor_visible": False,
        "taxonomy_or_route_labels_actor_visible": False,
        "private_holdout_used": False,
        "current_tiled_control_present": any(row["controller_family_id"] == "L2-current-tiled" for row in controller_rows),
        "reset_truncated_control_present": any(
            row["controller_family_id"] == "L3-reset-truncated-control" for row in controller_rows
        ),
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(source["paths"]["follow_up_manifest"]),
        "paths": {key: str(path) for key, path in paths.items()},
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }
    summary.update(FALSE_CLAIM_FLAGS)
    return summary


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2671 Paper Route History Vs Current Response Comparison Protocol Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result_class: `{summary['result_class']}`",
            f"- generated_at_utc: `{summary['generated_at_utc']}`",
            f"- summary: `{summary['paths']['summary']}`",
            f"- controller family rows: `{summary['paths']['controller_family_rows']}`",
            f"- task family rows: `{summary['paths']['task_family_rows']}`",
            f"- fairness gate rows: `{summary['paths']['fairness_gate_rows']}`",
            f"- claim boundary rows: `{summary['paths']['claim_boundary_rows']}`",
            f"- gate matrix: `{summary['paths']['gate_matrix']}`",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            f"- next: `{summary['next_blocker']}`",
            "",
            "## Materialized Protocol",
            "",
            f"- controller family rows: {summary['controller_family_row_count']} / {summary['required_controller_family_count']}",
            f"- task family rows: {summary['task_family_row_count']} / {summary['required_task_family_count']}",
            f"- fairness gate rows: {summary['fairness_gate_row_count']}",
            f"- claim boundary rows: {summary['claim_boundary_row_count']}",
            f"- gate matrix rows: {summary['gate_matrix_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Guardrails",
            "",
            f"- actor/action boundary: P0 observation {summary['observation_shape']} action {summary['action_shape']}",
            f"- hidden/oracle actor input detected: {summary['hidden_oracle_actor_input_detected']}",
            f"- private holdout used: {summary['private_holdout_used']}",
            f"- current-tiled L2 control present: {summary['current_tiled_control_present']}",
            f"- reset/truncated L3 control present: {summary['reset_truncated_control_present']}",
            "",
            "## Claim Boundary",
            "",
            "Allowed:",
            "",
            "```text",
            "Route B comparison protocol materialization readiness only.",
            "```",
            "",
            "Rejected:",
            "",
            "```text",
            summary["forbidden_interpretation"],
            "```",
            "",
            "M2671 did not execute reset, rollout, replay, validation, training, PPO,",
            "source build, adapter probe, external simulation, ranking, winner",
            "selection, promotion, success-rate verdict computation, driver-performance",
            "measurement, paper verdict, current-sim verdict, high-fidelity validation,",
            "full ideal driver gate, or self-ID verdict.",
            "",
        ]
    )


def gate(
    gate_id: str,
    family: str,
    status_pass: bool,
    observed: Any,
    expected: Any,
    failure_type: str,
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "gate_family": family,
        "status_pass": bool(status_pass),
        "observed": observed,
        "expected": expected,
        "failure_type": "" if status_pass else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"true", "1", "yes"}
    return bool(value)


def _read_csv(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args(argv)
    summary = materialize_protocol_pack(
        args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"summary={summary['paths']['summary']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"next={summary['next_blocker']}")
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
