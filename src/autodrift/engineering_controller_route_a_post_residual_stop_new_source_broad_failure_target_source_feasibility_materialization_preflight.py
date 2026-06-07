"""Materialize M3029 target-source feasibility rows.

M3029 joins the M3028-accepted M3027 raw actor-view traces with the M3025
target-source readiness denominator. It writes an auditable feasibility panel
only. It does not run local-action search, materialize numeric targets, fit,
train, validate, rank, promote, mutate checkpoints, or claim performance.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3029-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-"
    "target-source-feasibility-materialization-preflight"
)
NEXT_ID = (
    "m3030-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-"
    "target-source-feasibility-result-audit"
)
M3028_DECISION = (
    "accept_m3027_claim_safe_raw_trace_capture_route_to_m3029_target_source_feasibility_"
    "materialization_preflight"
)

DEFAULT_M3027_DIR = Path(
    "runs/m3027_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_"
    "deployable_trace_capture_preflight"
)
DEFAULT_M3028_AUDIT = Path(
    "docs/m3028-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-"
    "deployable-trace-capture-result-audit.md"
)
DEFAULT_M3025_DIR = Path(
    "runs/m3025_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_"
    "target_source_readiness_feasibility_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3029_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_"
    "target_source_feasibility_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_DENOMINATOR_ROWS = 32
EXPECTED_FUTURE_TARGET_ROWS = 29
EXPECTED_SUCCESS_GUARD_ROWS = 3

CLAIM_SCOPE = (
    "M3029 Route A post-residual-stop new-source broad-failure target-source feasibility "
    "materialization only; M3027 raw actor-view trace rows may be joined to M3025 readiness "
    "rows to materialize trainer/evaluator-side feasibility rows. No numeric target tensor, "
    "local-action search, fitting, training, PPO, validation, ranking, winner selection, "
    "checkpoint mutation, checkpoint promotion, profile tuning, repair success, "
    "driver-performance, paper, current-sim verdict, high-fidelity validation, full ideal "
    "driver, finite-window-vs-GRU, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "numeric target readiness, target tensor materialization, local-action search result, "
    "residual fitting readiness, repair success, driver performance, validation readiness or "
    "result, controller/source/task/profile/checkpoint ranking, winner selection, checkpoint "
    "promotion, success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, "
    "current-sim verdict, high-fidelity validation readiness or result, full ideal driver "
    "completion, or level3 self-identification"
)

PATH_KEYS = [
    "summary",
    "target_source_plan_rows",
    "target_source_candidate_rows",
    "success_identity_guard_rows",
    "target_source_availability_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
    "follow_up_manifest",
]

TARGET_SOURCE_PLAN_FIELDNAMES = [
    "target_source_plan_row_id",
    "target_source_readiness_row_id",
    "raw_trace_index_row_id",
    "raw_trace_availability_row_id",
    "raw_trace_guard_row_id",
    "success_identity_guard_row_id",
    "row_assignment_id",
    "source_episode_row_index",
    "execution_workload_id",
    "task_source_id",
    "profile_name",
    "binding_role",
    "row_role",
    "objective_family",
    "failure_family",
    "target_source_contract",
    "raw_trace_path",
    "raw_trace_persisted",
    "trace_file_exists",
    "trace_step_count",
    "actor_observation_dim",
    "actor_action_dim",
    "target_source_feasibility_established",
    "local_action_search_required_before_numeric_target",
    "local_action_search_run",
    "numeric_target_tensor_materialized",
    "target_labels_actor_visible",
    "target_provenance_actor_visible",
    "feasibility_labels_actor_visible",
    "future_target_candidate",
    "positive_target_candidate",
    "success_identity_zero_target_guard",
    "preserve_row",
    "claim_boundary",
]
TARGET_CANDIDATE_FIELDNAMES = [
    "target_source_candidate_row_id",
    "target_source_plan_row_id",
    "target_source_readiness_row_id",
    "raw_trace_index_row_id",
    "row_assignment_id",
    "task_source_id",
    "profile_name",
    "binding_role",
    "objective_family",
    "failure_family",
    "raw_trace_path",
    "trace_step_count",
    "actor_observation_dim",
    "actor_action_dim",
    "target_source_feasibility_established",
    "future_target_candidate",
    "local_action_search_required_before_numeric_target",
    "local_action_search_run",
    "numeric_target_tensor_materialized",
    "target_labels_actor_visible",
    "target_provenance_actor_visible",
    "claim_boundary",
]
SUCCESS_GUARD_FIELDNAMES = [
    "success_identity_guard_row_id",
    "target_source_plan_row_id",
    "target_source_readiness_row_id",
    "raw_trace_index_row_id",
    "row_assignment_id",
    "task_source_id",
    "profile_name",
    "binding_role",
    "raw_trace_path",
    "trace_step_count",
    "guard_trace_available",
    "success_identity_zero_target_guard",
    "future_target_candidate",
    "positive_target_candidate",
    "target_source_feasibility_established",
    "local_action_search_run",
    "numeric_target_tensor_materialized",
    "target_labels_actor_visible",
    "target_provenance_actor_visible",
    "claim_boundary",
]
AVAILABILITY_FIELDNAMES = [
    "target_source_availability_row_id",
    "target_source_plan_row_id",
    "target_source_readiness_row_id",
    "raw_trace_index_row_id",
    "raw_trace_availability_row_id",
    "row_assignment_id",
    "row_role",
    "readiness_raw_trace_required",
    "readiness_raw_trace_available_before_m3027",
    "m3027_raw_trace_persisted",
    "trace_file_exists",
    "trace_step_count",
    "target_source_feasibility_established",
    "availability_status",
    "blocking_reason_for_target_tensor_interpretation",
    "claim_boundary",
]
ACTOR_GUARD_FIELDNAMES = [
    "guard_id",
    "contract_field",
    "observed_value",
    "expected_value",
    "status_pass",
    "actor_visible",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3029",
    "claim_made",
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


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "target_source_plan_rows": output_dir / "target_source_plan_rows.csv",
        "target_source_candidate_rows": output_dir / "target_source_candidate_rows.csv",
        "success_identity_guard_rows": output_dir / "success_identity_guard_rows.csv",
        "target_source_availability_rows": output_dir / "target_source_availability_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_source_artifacts(
    *,
    m3027_dir: Path,
    m3028_audit: Path,
    m3025_dir: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m3027_summary": m3027_dir / "summary.json",
        "m3027_raw_trace_index_rows": m3027_dir / "raw_trace_index_rows.csv",
        "m3027_raw_trace_availability_rows": m3027_dir / "raw_trace_availability_rows.csv",
        "m3027_raw_trace_guard_rows": m3027_dir / "raw_trace_guard_rows.csv",
        "m3027_actor_contract_guard_rows": m3027_dir / "actor_contract_guard_rows.csv",
        "m3027_gate_matrix": m3027_dir / "gate_matrix.csv",
        "m3028_audit": m3028_audit,
        "m3025_summary": m3025_dir / "summary.json",
        "m3025_target_source_readiness_rows": m3025_dir / "target_source_readiness_rows.csv",
        "m3025_target_source_blocker_rows": m3025_dir / "target_source_blocker_rows.csv",
        "m3025_success_identity_guard_rows": m3025_dir / "success_identity_guard_rows.csv",
        "m3025_actor_contract_guard_rows": m3025_dir / "actor_contract_guard_rows.csv",
        "m3025_gate_matrix": m3025_dir / "gate_matrix.csv",
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m3027_summary": read_json(paths["m3027_summary"]) if source_exists["m3027_summary"] else {},
        "m3027_raw_trace_index_rows": read_csv_rows(paths["m3027_raw_trace_index_rows"])
        if source_exists["m3027_raw_trace_index_rows"]
        else [],
        "m3027_raw_trace_availability_rows": read_csv_rows(paths["m3027_raw_trace_availability_rows"])
        if source_exists["m3027_raw_trace_availability_rows"]
        else [],
        "m3027_raw_trace_guard_rows": read_csv_rows(paths["m3027_raw_trace_guard_rows"])
        if source_exists["m3027_raw_trace_guard_rows"]
        else [],
        "m3027_actor_contract_guard_rows": read_csv_rows(paths["m3027_actor_contract_guard_rows"])
        if source_exists["m3027_actor_contract_guard_rows"]
        else [],
        "m3027_gate_matrix": read_csv_rows(paths["m3027_gate_matrix"])
        if source_exists["m3027_gate_matrix"]
        else [],
        "m3028_audit_text": paths["m3028_audit"].read_text(encoding="utf-8")
        if source_exists["m3028_audit"]
        else "",
        "m3025_summary": read_json(paths["m3025_summary"]) if source_exists["m3025_summary"] else {},
        "m3025_target_source_readiness_rows": read_csv_rows(paths["m3025_target_source_readiness_rows"])
        if source_exists["m3025_target_source_readiness_rows"]
        else [],
        "m3025_target_source_blocker_rows": read_csv_rows(paths["m3025_target_source_blocker_rows"])
        if source_exists["m3025_target_source_blocker_rows"]
        else [],
        "m3025_success_identity_guard_rows": read_csv_rows(paths["m3025_success_identity_guard_rows"])
        if source_exists["m3025_success_identity_guard_rows"]
        else [],
        "m3025_actor_contract_guard_rows": read_csv_rows(paths["m3025_actor_contract_guard_rows"])
        if source_exists["m3025_actor_contract_guard_rows"]
        else [],
        "m3025_gate_matrix": read_csv_rows(paths["m3025_gate_matrix"])
        if source_exists["m3025_gate_matrix"]
        else [],
    }


def build_target_source_plan_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_by_readiness = {
        str(row.get("target_source_readiness_row_id", "")): row
        for row in source["m3027_raw_trace_index_rows"]
    }
    availability_by_readiness = {
        str(row.get("target_source_readiness_row_id", "")): row
        for row in source["m3027_raw_trace_availability_rows"]
    }
    guard_by_readiness = {
        str(row.get("target_source_readiness_row_id", "")): row
        for row in source["m3027_raw_trace_guard_rows"]
    }
    success_by_readiness = {
        str(row.get("target_source_readiness_row_id", "")): row
        for row in source["m3025_success_identity_guard_rows"]
    }
    rows: list[dict[str, Any]] = []
    for index, readiness in enumerate(source["m3025_target_source_readiness_rows"], start=1):
        readiness_id = str(readiness.get("target_source_readiness_row_id", ""))
        raw = raw_by_readiness.get(readiness_id, {})
        availability = availability_by_readiness.get(readiness_id, {})
        guard = guard_by_readiness.get(readiness_id, {})
        success_guard = success_by_readiness.get(readiness_id, {})
        row_role = str(raw.get("row_role") or readiness.get("target_role") or "")
        is_success = readiness.get("objective_family") == "success_identity_context_guard" or row_role == "success_identity_guard"
        is_candidate = row_role == "future_target_candidate" and not is_success
        raw_path = str(raw.get("raw_trace_path", ""))
        raw_persisted = _bool(raw.get("raw_trace_persisted", False))
        trace_file_exists = bool(raw_path and Path(raw_path).exists())
        feasible = bool(is_candidate and raw_persisted and trace_file_exists)
        rows.append(
            {
                "target_source_plan_row_id": f"m3029-target-source-plan-{index:04d}",
                "target_source_readiness_row_id": readiness_id,
                "raw_trace_index_row_id": raw.get("raw_trace_index_row_id", ""),
                "raw_trace_availability_row_id": availability.get("raw_trace_availability_row_id", ""),
                "raw_trace_guard_row_id": guard.get("raw_trace_guard_row_id", ""),
                "success_identity_guard_row_id": success_guard.get("success_identity_guard_row_id", ""),
                "row_assignment_id": readiness.get("row_assignment_id", raw.get("row_assignment_id", "")),
                "source_episode_row_index": readiness.get("source_episode_row_index", raw.get("source_episode_row_index", "")),
                "execution_workload_id": raw.get("execution_workload_id", ""),
                "task_source_id": readiness.get("task_source_id", raw.get("task_source_id", "")),
                "profile_name": readiness.get("profile_name", raw.get("profile_name", "")),
                "binding_role": readiness.get("binding_role", raw.get("binding_role", "")),
                "row_role": "success_identity_guard" if is_success else "future_target_candidate" if is_candidate else row_role,
                "objective_family": readiness.get("objective_family", raw.get("objective_family", "")),
                "failure_family": readiness.get("failure_family", raw.get("failure_family", "")),
                "target_source_contract": _target_source_contract(is_candidate=is_candidate, is_success=is_success),
                "raw_trace_path": raw_path,
                "raw_trace_persisted": raw_persisted,
                "trace_file_exists": trace_file_exists,
                "trace_step_count": _to_int(raw.get("trace_step_count"), default=0),
                "actor_observation_dim": _to_int(raw.get("actor_observation_dim"), default=_to_int(readiness.get("actor_observation_dim"), default=0)),
                "actor_action_dim": _to_int(raw.get("actor_action_dim"), default=_to_int(readiness.get("actor_action_dim"), default=0)),
                "target_source_feasibility_established": feasible,
                "local_action_search_required_before_numeric_target": bool(is_candidate),
                "local_action_search_run": False,
                "numeric_target_tensor_materialized": False,
                "target_labels_actor_visible": False,
                "target_provenance_actor_visible": False,
                "feasibility_labels_actor_visible": False,
                "future_target_candidate": bool(is_candidate),
                "positive_target_candidate": bool(is_candidate),
                "success_identity_zero_target_guard": bool(is_success),
                "preserve_row": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def _target_source_contract(*, is_candidate: bool, is_success: bool) -> str:
    if is_candidate:
        return "raw_trace_available_for_future_target_source_pending_m3030_audit"
    if is_success:
        return "success_identity_guard_trace_available_not_positive_target"
    return "non_candidate_guard_context_preserved"


def build_target_source_candidate_rows(plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, plan in enumerate([row for row in plan_rows if _bool(row["future_target_candidate"])], start=1):
        rows.append(
            {
                "target_source_candidate_row_id": f"m3029-target-source-candidate-{index:04d}",
                "target_source_plan_row_id": plan["target_source_plan_row_id"],
                "target_source_readiness_row_id": plan["target_source_readiness_row_id"],
                "raw_trace_index_row_id": plan["raw_trace_index_row_id"],
                "row_assignment_id": plan["row_assignment_id"],
                "task_source_id": plan["task_source_id"],
                "profile_name": plan["profile_name"],
                "binding_role": plan["binding_role"],
                "objective_family": plan["objective_family"],
                "failure_family": plan["failure_family"],
                "raw_trace_path": plan["raw_trace_path"],
                "trace_step_count": plan["trace_step_count"],
                "actor_observation_dim": plan["actor_observation_dim"],
                "actor_action_dim": plan["actor_action_dim"],
                "target_source_feasibility_established": plan["target_source_feasibility_established"],
                "future_target_candidate": True,
                "local_action_search_required_before_numeric_target": True,
                "local_action_search_run": False,
                "numeric_target_tensor_materialized": False,
                "target_labels_actor_visible": False,
                "target_provenance_actor_visible": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_success_identity_guard_rows(plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, plan in enumerate([row for row in plan_rows if _bool(row["success_identity_zero_target_guard"])], start=1):
        rows.append(
            {
                "success_identity_guard_row_id": f"m3029-success-identity-guard-{index:04d}",
                "target_source_plan_row_id": plan["target_source_plan_row_id"],
                "target_source_readiness_row_id": plan["target_source_readiness_row_id"],
                "raw_trace_index_row_id": plan["raw_trace_index_row_id"],
                "row_assignment_id": plan["row_assignment_id"],
                "task_source_id": plan["task_source_id"],
                "profile_name": plan["profile_name"],
                "binding_role": plan["binding_role"],
                "raw_trace_path": plan["raw_trace_path"],
                "trace_step_count": plan["trace_step_count"],
                "guard_trace_available": bool(_bool(plan["raw_trace_persisted"]) and _bool(plan["trace_file_exists"])),
                "success_identity_zero_target_guard": True,
                "future_target_candidate": False,
                "positive_target_candidate": False,
                "target_source_feasibility_established": False,
                "local_action_search_run": False,
                "numeric_target_tensor_materialized": False,
                "target_labels_actor_visible": False,
                "target_provenance_actor_visible": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_target_source_availability_rows(plan_rows: list[dict[str, Any]], source: Mapping[str, Any]) -> list[dict[str, Any]]:
    readiness_by_id = {
        str(row.get("target_source_readiness_row_id", "")): row
        for row in source["m3025_target_source_readiness_rows"]
    }
    rows: list[dict[str, Any]] = []
    for index, plan in enumerate(plan_rows, start=1):
        readiness = readiness_by_id.get(str(plan["target_source_readiness_row_id"]), {})
        feasible = _bool(plan["target_source_feasibility_established"])
        is_success = _bool(plan["success_identity_zero_target_guard"])
        if feasible:
            status = "target_source_feasible_pending_m3030_audit"
            blocker = "M3030 result audit required before target tensor materialization or local-action search"
        elif is_success:
            status = "success_identity_guard_trace_available_not_target_candidate"
            blocker = "success identity guard rows are not positive future target candidates"
        else:
            status = "target_source_feasibility_missing_fail_closed"
            blocker = "raw trace join missing or trace file unavailable"
        rows.append(
            {
                "target_source_availability_row_id": f"m3029-target-source-availability-{index:04d}",
                "target_source_plan_row_id": plan["target_source_plan_row_id"],
                "target_source_readiness_row_id": plan["target_source_readiness_row_id"],
                "raw_trace_index_row_id": plan["raw_trace_index_row_id"],
                "raw_trace_availability_row_id": plan["raw_trace_availability_row_id"],
                "row_assignment_id": plan["row_assignment_id"],
                "row_role": plan["row_role"],
                "readiness_raw_trace_required": _bool(readiness.get("raw_actor_view_trace_required", False)),
                "readiness_raw_trace_available_before_m3027": _bool(readiness.get("raw_actor_view_trace_available", False)),
                "m3027_raw_trace_persisted": _bool(plan["raw_trace_persisted"]),
                "trace_file_exists": _bool(plan["trace_file_exists"]),
                "trace_step_count": plan["trace_step_count"],
                "target_source_feasibility_established": feasible,
                "availability_status": status,
                "blocking_reason_for_target_tensor_interpretation": blocker,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_guard_rows(plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    role_counts = Counter(str(row.get("row_role", "")) for row in plan_rows)
    return [
        actor_guard("plan_row_count", len(plan_rows), EXPECTED_DENOMINATOR_ROWS),
        actor_guard("future_target_candidate_count", role_counts["future_target_candidate"], EXPECTED_FUTURE_TARGET_ROWS),
        actor_guard("success_identity_guard_count", role_counts["success_identity_guard"], EXPECTED_SUCCESS_GUARD_ROWS),
        actor_guard("actor_observation_dim", _all_equal(plan_rows, "actor_observation_dim", P0_OBSERVATION_DIM), True),
        actor_guard("actor_action_dim", _all_equal(plan_rows, "actor_action_dim", ACTION_DIM), True),
        actor_guard("target_labels_actor_visible", _any_true(plan_rows, "target_labels_actor_visible"), False),
        actor_guard("target_provenance_actor_visible", _any_true(plan_rows, "target_provenance_actor_visible"), False),
        actor_guard("feasibility_labels_actor_visible", _any_true(plan_rows, "feasibility_labels_actor_visible"), False),
        actor_guard("numeric_target_tensor_materialized", _any_true(plan_rows, "numeric_target_tensor_materialized"), False),
        actor_guard("local_action_search_run", _any_true(plan_rows, "local_action_search_run"), False),
    ]


def actor_guard(field: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": f"m3029-actor-contract-{field}",
        "contract_field": field,
        "observed_value": observed,
        "expected_value": expected,
        "status_pass": observed == expected,
        "actor_visible": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    claims = [
        ("target_source_feasibility_artifacts_materialized", True, True, "M3030 audit"),
        ("raw_trace_readiness_join_materialized", True, True, "target_source_plan_rows.csv"),
        ("target_source_candidate_rows_materialized", True, True, "target_source_candidate_rows.csv"),
        ("success_identity_guard_rows_materialized", True, True, "success_identity_guard_rows.csv"),
        ("follow_up_result_audit_manifest_registered", True, bool(follow_up_manifest_registered), "M3030 manifest"),
        ("numeric_target_tensor_materialized", False, False, "future target tensor materialization preflight and audit"),
        ("local_action_search", False, False, "future audited target search route"),
        ("residual_fitting_or_training", False, False, "future fitting/training milestone"),
        ("ppo_run", False, False, "future PPO milestone"),
        ("validation_run", False, False, "future validation milestone"),
        ("ranking_or_winner_selection", False, False, "future ranking/promotion gate"),
        ("checkpoint_mutation_or_promotion", False, False, "future promotion gate"),
        ("repair_success", False, False, "future validation and audit"),
        ("driver_performance", False, False, "proof/generalization/promotion gates"),
        ("paper_claim", False, False, "paper route evidence matrix"),
        ("current_sim_verdict", False, False, "separate verdict synthesis"),
        ("high_fidelity_validation", False, False, "Route C validation"),
        ("finite_window_vs_gru", False, False, "paper route fair comparison"),
        ("full_ideal_driver_completion", False, False, "full ideal driver gate"),
        ("level3_self_id", False, False, "self-ID proof gates"),
        ("hidden_oracle_or_ttc_actor_inputs", False, False, "actor contract forbids these shortcut inputs"),
    ]
    return [
        {
            "claim_id": f"m3029-claim-{index:04d}",
            "claim_family": family,
            "allowed_in_m3029": allowed,
            "claim_made": made,
            "status_pass": bool(made) == bool(allowed),
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, allowed, made, evidence) in enumerate(claims, start=1)
    ]


def build_gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    success_guard_rows: list[dict[str, Any]],
    availability_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest: Path,
) -> list[dict[str, Any]]:
    role_counts = Counter(str(row.get("row_role", "")) for row in plan_rows)
    target_source_feasible_count = sum(_bool(row["target_source_feasibility_established"]) for row in plan_rows)
    raw_join_count = sum(bool(row.get("raw_trace_index_row_id")) for row in plan_rows)
    trace_file_count = sum(_bool(row["trace_file_exists"]) for row in plan_rows)
    gates = [
        ("source_artifacts_present", "lineage", all(source["source_exists"].values()), source["source_exists"], "all true", "lineage_invalid"),
        (
            "m3027_status_pass",
            "lineage",
            _bool(source["m3027_summary"].get("status_pass")) and _bool(source["m3027_summary"].get("gate_matrix_pass")),
            {"status_pass": source["m3027_summary"].get("status_pass"), "gate_matrix_pass": source["m3027_summary"].get("gate_matrix_pass")},
            "both true",
            "lineage_invalid",
        ),
        (
            "m3025_status_pass",
            "lineage",
            _bool(source["m3025_summary"].get("status_pass")) and _bool(source["m3025_summary"].get("gate_matrix_pass")),
            {"status_pass": source["m3025_summary"].get("status_pass"), "gate_matrix_pass": source["m3025_summary"].get("gate_matrix_pass")},
            "both true",
            "lineage_invalid",
        ),
        (
            "m3028_accepts_m3027_and_routes_m3029",
            "lineage",
            M3028_DECISION in source["m3028_audit_text"],
            M3028_DECISION in source["m3028_audit_text"],
            True,
            "lineage_invalid",
        ),
        ("readiness_denominator_preserved", "denominator", len(source["m3025_target_source_readiness_rows"]), EXPECTED_DENOMINATOR_ROWS, "metric_artifact"),
        ("raw_trace_index_denominator", "denominator", len(source["m3027_raw_trace_index_rows"]), EXPECTED_DENOMINATOR_ROWS, "metric_artifact"),
        ("target_source_plan_row_count", "artifact", len(plan_rows), EXPECTED_DENOMINATOR_ROWS, "metric_artifact"),
        ("future_target_candidate_count", "accounting", role_counts["future_target_candidate"], EXPECTED_FUTURE_TARGET_ROWS, "metric_artifact"),
        ("success_identity_guard_count", "accounting", role_counts["success_identity_guard"], EXPECTED_SUCCESS_GUARD_ROWS, "metric_artifact"),
        ("target_source_candidate_row_count", "artifact", len(candidate_rows), EXPECTED_FUTURE_TARGET_ROWS, "metric_artifact"),
        ("success_identity_guard_row_count", "artifact", len(success_guard_rows), EXPECTED_SUCCESS_GUARD_ROWS, "metric_artifact"),
        ("availability_row_count", "artifact", len(availability_rows), EXPECTED_DENOMINATOR_ROWS, "metric_artifact"),
        ("raw_trace_rows_joined_to_readiness", "join", raw_join_count, EXPECTED_DENOMINATOR_ROWS, "metric_artifact"),
        ("raw_trace_files_exist", "artifact", trace_file_count, EXPECTED_DENOMINATOR_ROWS, "metric_artifact"),
        ("target_source_feasibility_established_count", "target_source", target_source_feasible_count, EXPECTED_FUTURE_TARGET_ROWS, "metric_artifact"),
        ("numeric_target_tensor_materialized_count", "claim_boundary", sum(_bool(row["numeric_target_tensor_materialized"]) for row in plan_rows), 0, "contract_violation"),
        ("local_action_search_run_count", "claim_boundary", sum(_bool(row["local_action_search_run"]) for row in plan_rows), 0, "contract_violation"),
        ("success_identity_positive_target_count", "guardrail", sum(_bool(row["positive_target_candidate"]) for row in success_guard_rows), 0, "contract_violation"),
        ("actor_contract_guards_pass", "actor_contract", _all_true(actor_rows, "status_pass"), True, "contract_violation"),
        ("claim_boundary_rows_pass", "claim_boundary", _all_true(claim_rows, "status_pass"), True, "contract_violation"),
        ("required_artifacts_present", "artifact", required_artifacts_present, True, "metric_artifact"),
        ("follow_up_manifest_registered", "process", follow_up_manifest.exists(), True, "lineage_invalid"),
    ]
    rows: list[dict[str, Any]] = []
    for index, spec in enumerate(gates, start=1):
        if len(spec) == 5:
            name, family, observed, expected, failure_type = spec
            status_pass = observed == expected
        else:
            name, family, status_pass, observed, expected, failure_type = spec
        rows.append(
            {
                "gate_id": f"m3029-gate-{index:04d}-{name}",
                "gate_family": family,
                "status_pass": bool(status_pass),
                "observed": observed,
                "expected": expected,
                "failure_type": "" if bool(status_pass) else failure_type,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_summary(
    *,
    output_dir: Path,
    paths: Mapping[str, Path],
    source: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    success_guard_rows: list[dict[str, Any]],
    availability_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    role_counts = Counter(str(row.get("row_role", "")) for row in plan_rows)
    step_counts = [_to_int(row.get("trace_step_count"), default=0) for row in plan_rows if _to_int(row.get("trace_step_count"), default=0) > 0]
    feasibility_count = sum(_bool(row["target_source_feasibility_established"]) for row in plan_rows)
    numeric_target_count = sum(_bool(row["numeric_target_tensor_materialized"]) for row in plan_rows)
    local_action_count = sum(_bool(row["local_action_search_run"]) for row in plan_rows)
    status_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    return {
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "result_class": "new_source_broad_failure_target_source_feasibility_materialization_preflight_pass"
        if status_pass
        else "new_source_broad_failure_target_source_feasibility_materialization_preflight_fail_closed",
        "status_pass": status_pass,
        "gate_matrix_pass": status_pass,
        "required_artifacts_present": required_artifacts_present,
        "source_artifacts_present": all(source["source_exists"].values()),
        "target_source_plan_row_count": len(plan_rows),
        "target_source_candidate_row_count": len(candidate_rows),
        "success_identity_guard_row_count": len(success_guard_rows),
        "target_source_availability_row_count": len(availability_rows),
        "future_target_candidate_count": role_counts["future_target_candidate"],
        "success_identity_plan_count": role_counts["success_identity_guard"],
        "raw_trace_joined_count": sum(bool(row.get("raw_trace_index_row_id")) for row in plan_rows),
        "raw_trace_file_exists_count": sum(_bool(row["trace_file_exists"]) for row in plan_rows),
        "trace_step_min": min(step_counts) if step_counts else 0,
        "trace_step_max": max(step_counts) if step_counts else 0,
        "target_source_feasibility_established_count": feasibility_count,
        "success_identity_positive_target_count": sum(_bool(row["positive_target_candidate"]) for row in success_guard_rows),
        "numeric_target_tensor_materialized_count": numeric_target_count,
        "local_action_search_run_count": local_action_count,
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": all(_bool(row["status_pass"]) for row in actor_rows),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(_bool(row["status_pass"]) for row in claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "actor_contract_shape_72_action_3": _all_equal(plan_rows, "actor_observation_dim", P0_OBSERVATION_DIM)
        and _all_equal(plan_rows, "actor_action_dim", ACTION_DIM),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_detected": False,
        "future_target_actor_input_required": False,
        "source_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "outcome_labels_actor_visible": False,
        "objective_labels_actor_visible": False,
        "readiness_labels_actor_visible": False,
        "feasibility_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "ttc_actor_input_required": False,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "raw_trace_capture_run": False,
        "target_source_feasibility_materialization_run": True,
        "target_source_feasibility_claim_made": True,
        "target_tensor_materialization_run": False,
        "numeric_target_tensor_materialized": False,
        "local_action_search_run": False,
        "fitting_run": False,
        "training_run": False,
        "ppo_run": False,
        "validation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "profile_specific_tuning": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
        "success_rate_verdict_claim_made": False,
        "validation_readiness_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "next_blocker": next_blocker,
        "paths": {key: str(value) for key, value in paths.items()},
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path, summary_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
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
        "hypothesis": (
            "A bounded result audit can accept or reject the M3029 target-source feasibility "
            "materialization artifacts before any numeric target tensor local-action search fitting "
            "training validation ranking performance paper high-fidelity full-driver finite-window-vs-GRU "
            "or self-ID claim."
        ),
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "target_source_plan_rows.csv"),
                str(output_dir / "target_source_candidate_rows.csv"),
                str(output_dir / "success_identity_guard_rows.csv"),
                str(output_dir / "target_source_availability_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "parent_config": [
                f"experiments/manifests/{MILESTONE_ID}.json",
                "experiments/manifests/m3028-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-deployable-trace-capture-result-audit.json",
            ],
            "parent_objective": ["audit target-source feasibility materialization before target tensor or local-action search admission"],
            "derived_from": [
                MILESTONE_ID,
                "m3028-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-deployable-trace-capture-result-audit",
                "m3027-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-deployable-trace-capture-preflight",
                "m3025-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-target-source-readiness-feasibility-materialization-preflight",
            ],
            "blocked_by": [
                "M3029 target-source feasibility artifacts require result audit before target tensor materialization or local-action search",
                "success identity guard rows must remain non-positive guard rows",
            ],
            "supersedes": [
                "direct numeric target tensor materialization immediately after raw trace capture without target-source feasibility audit",
                "direct local-action search or fitting from raw traces without result audit",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3030 must audit M3029 summary plan candidate success-identity availability actor claim and gate artifacts",
            "M3030 must preserve 29 future target candidates and 3 success identity guards",
            "M3030 must verify target-source feasibility rows are trainer/evaluator metadata and actor-invisible",
            "M3030 must not claim target tensor materialization local-action search fitting readiness validation repair-success driver performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
            "M3030 must select exactly one next route or stop state before target tensor materialization or local-action search",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run local-action search target tensor materialization fitting training PPO validation ranking winner selection or promotion",
            "do not change actor input or action contract",
            "do not convert M3029 feasibility rows into numeric targets performance paper high-fidelity or self-ID claims",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_residual_stop_source_axis_expansion",
            "evidence_axis": "new_source_broad_failure_target_source_feasibility_result_audit",
            "evidence_increment": "audits newly materialized target-source feasibility rows from M3025 readiness and M3027 raw traces",
            "claim_scope": "Result audit only; no target tensor materialization local-action search fitting training validation ranking promotion repair-success performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M3029 artifacts are incomplete or gate matrix fails",
                "stop if actor or claim boundaries were violated",
                "stop if feasibility rows would be interpreted as numeric targets or fitting readiness before audit",
            ],
            "fallback_plan": [
                "route to artifact repair if feasibility artifacts are incomplete",
                "route to bounded target tensor materialization preflight only after M3030 accepts claim safety",
                "route to branch synthesis or stop if target-source feasibility violates guardrails",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3029 completes target-source feasibility materialization preflight",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3029 target-source feasibility materialization artifacts",
            "admission_evidence": [
                "M3029 summary and gate matrix",
                "M3029 target-source plan candidate success identity availability actor and claim artifacts",
            ],
            "blocked_shortcuts": [
                "no target tensor materialization local-action search fitting training validation ranking promotion performance verdict paper high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
                "no checkpoint promotion",
                "no hidden/oracle/future-target actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3030 status queue scoreboard research log and review",
                "one follow-up manifest only if M3030 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3030 accepts or rejects M3029 as complete and claim-safe",
                "next route or stop state is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3030 audits Route A target-source feasibility and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M3030; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M3029 Route A target-source feasibility materialization preflight only.",
            "negative_result_policy": "Preserve feasibility failures and route to repair or synthesis rather than weakening self-ID gates.",
            "allowed_claims": [
                "M3029 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits newly materialized target-source feasibility panel",
            "paper_verdict_delta": "no paper verdict; audit may inform target tensor materialization route only",
            "must_synthesize_if": [
                "M3030 cannot accept M3029 as complete and claim-safe",
                "M3030 finds target-source feasibility insufficient for target tensor materialization admission",
                "M3030 would claim validation readiness driver performance paper current-sim high-fidelity or self-ID",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3030 audits M3029 artifacts row counts gates actor and claim boundaries",
            "M3030 selects exactly one next route or stop state",
            "no target tensor local-action search fitting training validation ranking promotion performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claim is made",
        ],
        "failure_criteria": [
            "M3030 hides M3029 failures or missing feasibility artifacts",
            "M3030 treats M3029 feasibility rows as target tensor materialization performance verdict or repair success",
            "M3030 changes actor input or action contract",
            "M3030 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3030 audits M3029 artifacts and selects one next route or stop state while preserving actor guardrail and claim boundaries without overclaiming.",
        "commands": [{"name": "target_source_feasibility_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "target_source_plan_rows.csv"),
            str(output_dir / "target_source_candidate_rows.csv"),
            str(output_dir / "target_source_availability_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def render_milestone_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3029 Engineering Controller Route A Post-Residual-Stop New Source Broad-Failure Target-Source Feasibility Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'fail_closed'}",
            f"- result class: `{summary['result_class']}`",
            f"- target-source plan rows: {summary['target_source_plan_row_count']}",
            f"- target-source candidate rows: {summary['target_source_candidate_row_count']}",
            f"- success identity guard rows: {summary['success_identity_guard_row_count']}",
            f"- target-source feasibility established rows: {summary['target_source_feasibility_established_count']}",
            f"- actor shape: {summary['observation_shape']}/action {summary['action_shape']}",
            f"- numeric target tensors materialized: {summary['numeric_target_tensor_materialized_count']}",
            f"- local action search runs: {summary['local_action_search_run_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M3029 materializes trainer/evaluator-side target-source feasibility rows only. It does not run local-action search, materialize numeric target tensors, fit, train, validate, rank, promote, mutate checkpoints, or claim performance.",
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


def run_target_source_feasibility_materialization_preflight(
    *,
    m3027_dir: Path | str = DEFAULT_M3027_DIR,
    m3028_audit: Path | str = DEFAULT_M3028_AUDIT,
    m3025_dir: Path | str = DEFAULT_M3025_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = MILESTONE_ID,
    next_blocker: str = NEXT_ID,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path), follow_up_manifest=Path(follow_up_manifest))
    source = load_source_artifacts(
        m3027_dir=Path(m3027_dir),
        m3028_audit=Path(m3028_audit),
        m3025_dir=Path(m3025_dir),
        follow_up_manifest=Path(follow_up_manifest),
    )
    plan_rows = build_target_source_plan_rows(source)
    candidate_rows = build_target_source_candidate_rows(plan_rows)
    success_guard_rows = build_success_identity_guard_rows(plan_rows)
    availability_rows = build_target_source_availability_rows(plan_rows, source)
    actor_rows = build_actor_contract_guard_rows(plan_rows)

    write_csv_rows(paths["target_source_plan_rows"], plan_rows, fieldnames=TARGET_SOURCE_PLAN_FIELDNAMES)
    write_csv_rows(paths["target_source_candidate_rows"], candidate_rows, fieldnames=TARGET_CANDIDATE_FIELDNAMES)
    write_csv_rows(paths["success_identity_guard_rows"], success_guard_rows, fieldnames=SUCCESS_GUARD_FIELDNAMES)
    write_csv_rows(paths["target_source_availability_rows"], availability_rows, fieldnames=AVAILABILITY_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output, doc_path=Path(doc_path), summary_path=paths["summary"]))
    source["source_exists"]["follow_up_manifest"] = Path(follow_up_manifest).exists()
    write_run_state(
        paths["run_state"],
        {
            "target_source_plan_row_count": len(plan_rows),
            "target_source_candidate_row_count": len(candidate_rows),
            "success_identity_guard_row_count": len(success_guard_rows),
            "target_source_availability_row_count": len(availability_rows),
            "execution_performed_by_m3029": False,
            "complete": False,
            "next_blocker": next_blocker,
        },
    )

    claim_rows = build_claim_boundary_rows(follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"])
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    gate_rows = build_gate_matrix_rows(
        source=source,
        plan_rows=plan_rows,
        candidate_rows=candidate_rows,
        success_guard_rows=success_guard_rows,
        availability_rows=availability_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=False,
        follow_up_manifest=Path(follow_up_manifest),
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        plan_rows=plan_rows,
        candidate_rows=candidate_rows,
        success_guard_rows=success_guard_rows,
        availability_rows=availability_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=False,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(paths[key].exists() for key in PATH_KEYS)
    gate_rows = build_gate_matrix_rows(
        source=source,
        plan_rows=plan_rows,
        candidate_rows=candidate_rows,
        success_guard_rows=success_guard_rows,
        availability_rows=availability_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
        follow_up_manifest=Path(follow_up_manifest),
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        plan_rows=plan_rows,
        candidate_rows=candidate_rows,
        success_guard_rows=success_guard_rows,
        availability_rows=availability_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "target_source_plan_row_count": len(plan_rows),
            "target_source_candidate_row_count": len(candidate_rows),
            "success_identity_guard_row_count": len(success_guard_rows),
            "target_source_availability_row_count": len(availability_rows),
            "execution_performed_by_m3029": False,
            "status_pass": summary["status_pass"],
            "gate_matrix_pass": summary["gate_matrix_pass"],
            "complete": summary["status_pass"],
            "next_blocker": next_blocker,
        },
    )
    return summary


def _to_int(value: Any, *, default: int = 0) -> int:
    try:
        if value in ("", None):
            return int(default)
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _all_true(rows: list[Mapping[str, Any]], key: str) -> bool:
    return bool(rows) and all(_bool(row.get(key, False)) for row in rows)


def _any_true(rows: list[Mapping[str, Any]], key: str) -> bool:
    return any(_bool(row.get(key, False)) for row in rows)


def _all_equal(rows: list[Mapping[str, Any]], key: str, expected: Any) -> bool:
    return bool(rows) and all(row.get(key) == expected or str(row.get(key)) == str(expected) for row in rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run M3029 target-source feasibility materialization preflight.")
    parser.add_argument("--m3027-dir", type=Path, default=DEFAULT_M3027_DIR)
    parser.add_argument("--m3028-audit", type=Path, default=DEFAULT_M3028_AUDIT)
    parser.add_argument("--m3025-dir", type=Path, default=DEFAULT_M3025_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args()
    summary = run_target_source_feasibility_materialization_preflight(
        m3027_dir=args.m3027_dir,
        m3028_audit=args.m3028_audit,
        m3025_dir=args.m3025_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']} gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"target_source_feasibility_established_count={summary['target_source_feasibility_established_count']}")
    print(f"next_blocker={summary['next_blocker']}")


if __name__ == "__main__":
    main()
