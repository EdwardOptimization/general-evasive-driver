"""Materialize M3025 target-source readiness/feasibility rows.

M3025 consumes the M3024-admitted M3022 broad-failure objective contract and
materializes a row-preserving readiness panel. It does not run reset, step,
rollout, replay, local-action search, validation, fitting, training, ranking,
promotion, or target tensor materialization. Missing raw actor-view traces are
reported as explicit blockers rather than papered over with scalar episode
summaries.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3025-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-"
    "target-source-readiness-feasibility-materialization-preflight"
)
NEXT_ID = (
    "m3026-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-"
    "target-source-readiness-feasibility-materialization-result-audit"
)
M3024_DECISION = "admit_m3025_new_source_broad_failure_target_source_readiness_feasibility_materialization_preflight"
M3023_DECISION = "accept_m3022_claim_safe_objective_contract_route_to_m3024_target_source_feasibility_admission_design"

DEFAULT_M3022_DIR = Path(
    "runs/m3022_engineering_controller_route_a_post_residual_stop_new_source_"
    "broad_failure_objective_contract_materialization_preflight"
)
DEFAULT_M3023_AUDIT = Path(
    "docs/m3023-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-"
    "objective-contract-materialization-result-audit.md"
)
DEFAULT_M3024_DESIGN = Path(
    "docs/m3024-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-"
    "target-source-feasibility-admission-design.md"
)
DEFAULT_M3018_DIR = Path(
    "runs/m3018_engineering_controller_route_a_post_residual_stop_new_source_"
    "failure_localization_materialization_preflight"
)
DEFAULT_M3015_DIR = Path(
    "runs/m3015_engineering_controller_route_a_post_residual_stop_new_source_bounded_execution_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3025_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_"
    "target_source_readiness_feasibility_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_ROW_ASSIGNMENT_ROWS = 32
EXPECTED_FUTURE_TARGET_ELIGIBLE_ROWS = 29
EXPECTED_SUCCESS_IDENTITY_GUARD_ROWS = 3
EXPECTED_OBJECTIVE_COUNTS = {
    "collision_clearance_guard_contract": 5,
    "offtrack_recovery_broad_failure_contract": 22,
    "speed_floor_guard_contract": 2,
    "success_identity_context_guard": 3,
}
EXPECTED_FAILURE_COUNTS = {
    "collision_clearance_failure": 5,
    "offtrack_high_severity_recovery_failure": 5,
    "offtrack_recovery_failure": 17,
    "speed_floor_context": 2,
    "success_context": 3,
}

CLAIM_SCOPE = (
    "M3025 Route A post-residual-stop new-source broad-failure target-source readiness "
    "feasibility materialization only; accepted M3022 row assignments may be joined to "
    "M3018 localization rows and M3015 episode summaries to write readiness, blocker, "
    "success-identity guard, actor, claim, gate, summary, doc, and M3026 audit artifacts. "
    "No reset, step, rollout, replay, local-action search, target tensor materialization, "
    "fitting, training, PPO, validation, ranking, winner selection, checkpoint mutation, "
    "checkpoint promotion, profile tuning, repair-success, driver-performance, paper, "
    "current-sim verdict, high-fidelity validation, finite-window-vs-GRU, full ideal driver, "
    "or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "target-source feasibility where raw actor-view trace evidence is missing, numeric target "
    "readiness, residual fitting readiness, repair success, driver performance, validation "
    "readiness or result, controller/source/task/profile/checkpoint ranking, winner selection, "
    "checkpoint promotion, success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, "
    "current-sim verdict, high-fidelity validation readiness or result, full ideal driver "
    "completion, or level3 self-identification"
)

PATH_KEYS = [
    "summary",
    "target_source_readiness_rows",
    "target_source_blocker_rows",
    "success_identity_guard_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
    "follow_up_manifest",
]

READINESS_FIELDNAMES = [
    "target_source_readiness_row_id",
    "row_assignment_id",
    "source_localization_row_id",
    "source_episode_row_index",
    "task_source_id",
    "profile_name",
    "profile_binding_name",
    "binding_role",
    "task_family",
    "source_edge",
    "window_tag",
    "strata",
    "outcome_family",
    "failure_family",
    "primary_failure_mode",
    "objective_family",
    "target_role",
    "future_target_materialization_allowed",
    "diagnostic_success",
    "diagnostic_non_success",
    "source_localization_available",
    "episode_summary_available",
    "episode_summary_accepted_as_raw_trace",
    "raw_actor_view_trace_required",
    "raw_actor_view_trace_available",
    "raw_actor_view_trace_path",
    "target_source_feasibility_established",
    "target_source_status",
    "local_action_search_required_before_numeric_target",
    "local_action_search_run",
    "numeric_target_tensor_materialized",
    "target_labels_actor_visible",
    "target_provenance_actor_visible",
    "hidden_oracle_actor_input_required",
    "actor_observation_dim",
    "actor_action_dim",
    "preserve_row",
    "claim_boundary",
]

BLOCKER_FIELDNAMES = [
    "target_source_blocker_row_id",
    "target_source_readiness_row_id",
    "row_assignment_id",
    "source_localization_row_id",
    "source_episode_row_index",
    "task_source_id",
    "profile_name",
    "binding_role",
    "objective_family",
    "failure_family",
    "blocker_type",
    "blocked_claim",
    "raw_actor_view_trace_required",
    "raw_actor_view_trace_available",
    "episode_summary_available",
    "episode_summary_accepted_as_raw_trace",
    "numeric_target_tensor_materialized",
    "local_action_search_run",
    "next_legal_route",
    "claim_boundary",
]

SUCCESS_GUARD_FIELDNAMES = [
    "success_identity_guard_row_id",
    "target_source_readiness_row_id",
    "row_assignment_id",
    "source_localization_row_id",
    "source_episode_row_index",
    "task_source_id",
    "profile_name",
    "binding_role",
    "diagnostic_success",
    "success_identity_zero_target_guard",
    "positive_target_candidate",
    "future_target_materialization_allowed",
    "raw_actor_view_trace_required",
    "numeric_target_tensor_materialized",
    "target_labels_actor_visible",
    "target_provenance_actor_visible",
    "claim_boundary",
]

ACTOR_GUARD_FIELDNAMES = [
    "guard_id",
    "guard_family",
    "status_pass",
    "observed",
    "expected",
    "actor_input_change_required",
    "actor_visible_label_allowed",
    "claim_boundary",
]

CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3025",
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
        "target_source_readiness_rows": output_dir / "target_source_readiness_rows.csv",
        "target_source_blocker_rows": output_dir / "target_source_blocker_rows.csv",
        "success_identity_guard_rows": output_dir / "success_identity_guard_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_source_artifacts(
    *,
    m3022_dir: Path,
    m3023_audit: Path,
    m3024_design: Path,
    m3018_dir: Path,
    m3015_dir: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m3022_summary": m3022_dir / "summary.json",
        "m3022_row_assignment_rows": m3022_dir / "row_assignment_rows.csv",
        "m3022_profile_source_guard_rows": m3022_dir / "profile_source_guard_rows.csv",
        "m3022_actor_contract_guard_rows": m3022_dir / "actor_contract_guard_rows.csv",
        "m3022_claim_boundary_rows": m3022_dir / "claim_boundary_rows.csv",
        "m3022_gate_matrix": m3022_dir / "gate_matrix.csv",
        "m3023_audit": m3023_audit,
        "m3024_design": m3024_design,
        "m3018_failure_localization_rows": m3018_dir / "failure_localization_rows.csv",
        "m3018_profile_source_aggregate_rows": m3018_dir / "profile_source_aggregate_rows.csv",
        "m3015_episode_rows": m3015_dir / "episode_rows.csv",
        "m3015_execution_guard_rows": m3015_dir / "execution_guard_rows.csv",
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m3022_summary": read_json(paths["m3022_summary"]) if source_exists["m3022_summary"] else {},
        "m3022_row_assignment_rows": read_csv_rows(paths["m3022_row_assignment_rows"])
        if source_exists["m3022_row_assignment_rows"]
        else [],
        "m3022_profile_source_guard_rows": read_csv_rows(paths["m3022_profile_source_guard_rows"])
        if source_exists["m3022_profile_source_guard_rows"]
        else [],
        "m3022_actor_contract_guard_rows": read_csv_rows(paths["m3022_actor_contract_guard_rows"])
        if source_exists["m3022_actor_contract_guard_rows"]
        else [],
        "m3022_claim_boundary_rows": read_csv_rows(paths["m3022_claim_boundary_rows"])
        if source_exists["m3022_claim_boundary_rows"]
        else [],
        "m3022_gate_matrix": read_csv_rows(paths["m3022_gate_matrix"])
        if source_exists["m3022_gate_matrix"]
        else [],
        "m3023_audit_text": paths["m3023_audit"].read_text(encoding="utf-8")
        if source_exists["m3023_audit"]
        else "",
        "m3024_design_text": paths["m3024_design"].read_text(encoding="utf-8")
        if source_exists["m3024_design"]
        else "",
        "m3018_failure_localization_rows": read_csv_rows(paths["m3018_failure_localization_rows"])
        if source_exists["m3018_failure_localization_rows"]
        else [],
        "m3018_profile_source_aggregate_rows": read_csv_rows(paths["m3018_profile_source_aggregate_rows"])
        if source_exists["m3018_profile_source_aggregate_rows"]
        else [],
        "m3015_episode_rows": read_csv_rows(paths["m3015_episode_rows"])
        if source_exists["m3015_episode_rows"]
        else [],
        "m3015_execution_guard_rows": read_csv_rows(paths["m3015_execution_guard_rows"])
        if source_exists["m3015_execution_guard_rows"]
        else [],
    }


def build_target_source_readiness_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    localization_by_id = {
        row.get("localization_row_id", ""): row
        for row in source["m3018_failure_localization_rows"]
    }
    episodes_by_index = {
        str(index + 1): row for index, row in enumerate(source["m3015_episode_rows"])
    }
    episodes_by_execution_id = {
        row.get("execution_workload_id", ""): row
        for row in source["m3015_episode_rows"]
        if row.get("execution_workload_id")
    }

    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source["m3022_row_assignment_rows"], start=1):
        localization = localization_by_id.get(str(row.get("source_localization_row_id", "")), {})
        episode_index = str(row.get("source_episode_row_index", ""))
        episode = episodes_by_index.get(episode_index)
        if episode is None and localization.get("execution_workload_id"):
            episode = episodes_by_execution_id.get(str(localization["execution_workload_id"]))
        future_allowed = _bool(row.get("future_target_materialization_allowed", False))
        is_success_guard = row.get("objective_family") == "success_identity_context_guard"
        raw_trace_required = bool(future_allowed and not is_success_guard)
        raw_trace_available = False
        target_feasible = bool(raw_trace_required and raw_trace_available)
        if is_success_guard:
            target_role = "success_identity_zero_target_guard"
            status = "guard_only_success_identity"
        elif raw_trace_required and not raw_trace_available:
            target_role = "future_target_candidate"
            status = "blocked_raw_actor_view_trace_missing"
        else:
            target_role = "non_target_guard_context"
            status = "not_future_target_candidate"
        rows.append(
            {
                "target_source_readiness_row_id": f"m3025-target-source-readiness-{index:04d}",
                "row_assignment_id": row.get("row_assignment_id", ""),
                "source_localization_row_id": row.get("source_localization_row_id", ""),
                "source_episode_row_index": episode_index,
                "task_source_id": row.get("task_source_id", ""),
                "profile_name": row.get("profile_name", ""),
                "profile_binding_name": row.get("profile_binding_name", ""),
                "binding_role": row.get("binding_role", ""),
                "task_family": row.get("task_family", ""),
                "source_edge": row.get("source_edge", ""),
                "window_tag": row.get("window_tag", ""),
                "strata": row.get("strata", ""),
                "outcome_family": row.get("outcome_family", ""),
                "failure_family": row.get("failure_family", ""),
                "primary_failure_mode": row.get("primary_failure_mode", ""),
                "objective_family": row.get("objective_family", ""),
                "target_role": target_role,
                "future_target_materialization_allowed": future_allowed,
                "diagnostic_success": _bool(row.get("diagnostic_success", False)),
                "diagnostic_non_success": _bool(row.get("diagnostic_non_success", False)),
                "source_localization_available": bool(localization),
                "episode_summary_available": bool(episode),
                "episode_summary_accepted_as_raw_trace": False,
                "raw_actor_view_trace_required": raw_trace_required,
                "raw_actor_view_trace_available": raw_trace_available,
                "raw_actor_view_trace_path": "",
                "target_source_feasibility_established": target_feasible,
                "target_source_status": status,
                "local_action_search_required_before_numeric_target": raw_trace_required,
                "local_action_search_run": False,
                "numeric_target_tensor_materialized": False,
                "target_labels_actor_visible": False,
                "target_provenance_actor_visible": False,
                "hidden_oracle_actor_input_required": False,
                "actor_observation_dim": P0_OBSERVATION_DIM,
                "actor_action_dim": ACTION_DIM,
                "preserve_row": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_target_source_blocker_rows(readiness_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    blocked_rows = [
        row
        for row in readiness_rows
        if _bool(row.get("raw_actor_view_trace_required"))
        and not _bool(row.get("raw_actor_view_trace_available"))
    ]
    for index, row in enumerate(blocked_rows, start=1):
        rows.append(
            {
                "target_source_blocker_row_id": f"m3025-target-source-blocker-{index:04d}",
                "target_source_readiness_row_id": row["target_source_readiness_row_id"],
                "row_assignment_id": row["row_assignment_id"],
                "source_localization_row_id": row["source_localization_row_id"],
                "source_episode_row_index": row["source_episode_row_index"],
                "task_source_id": row["task_source_id"],
                "profile_name": row["profile_name"],
                "binding_role": row["binding_role"],
                "objective_family": row["objective_family"],
                "failure_family": row["failure_family"],
                "blocker_type": "raw_actor_view_trace_missing",
                "blocked_claim": "target_source_feasibility",
                "raw_actor_view_trace_required": True,
                "raw_actor_view_trace_available": False,
                "episode_summary_available": row["episode_summary_available"],
                "episode_summary_accepted_as_raw_trace": False,
                "numeric_target_tensor_materialized": False,
                "local_action_search_run": False,
                "next_legal_route": "result_audit_then_trace_capture_admission_or_synthesis",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_success_identity_guard_rows(readiness_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    success_rows = [
        row for row in readiness_rows if row.get("objective_family") == "success_identity_context_guard"
    ]
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(success_rows, start=1):
        rows.append(
            {
                "success_identity_guard_row_id": f"m3025-success-identity-guard-{index:04d}",
                "target_source_readiness_row_id": row["target_source_readiness_row_id"],
                "row_assignment_id": row["row_assignment_id"],
                "source_localization_row_id": row["source_localization_row_id"],
                "source_episode_row_index": row["source_episode_row_index"],
                "task_source_id": row["task_source_id"],
                "profile_name": row["profile_name"],
                "binding_role": row["binding_role"],
                "diagnostic_success": row["diagnostic_success"],
                "success_identity_zero_target_guard": True,
                "positive_target_candidate": False,
                "future_target_materialization_allowed": False,
                "raw_actor_view_trace_required": False,
                "numeric_target_tensor_materialized": False,
                "target_labels_actor_visible": False,
                "target_provenance_actor_visible": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_guard_rows(readiness_rows: list[dict[str, Any]], source: dict[str, Any]) -> list[dict[str, Any]]:
    summary = source["m3022_summary"]
    checks = [
        (
            "actor_observation_shape",
            "contract_shape",
            int(summary.get("observation_shape", -1)) == P0_OBSERVATION_DIM,
            summary.get("observation_shape"),
            P0_OBSERVATION_DIM,
        ),
        (
            "actor_action_shape",
            "contract_shape",
            int(summary.get("action_shape", -1)) == ACTION_DIM,
            summary.get("action_shape"),
            ACTION_DIM,
        ),
        (
            "readiness_rows_actor_shape_72_action_3",
            "contract_shape",
            all(
                int(row["actor_observation_dim"]) == P0_OBSERVATION_DIM
                and int(row["actor_action_dim"]) == ACTION_DIM
                for row in readiness_rows
            ),
            "all readiness rows",
            f"{P0_OBSERVATION_DIM}/action {ACTION_DIM}",
        ),
        (
            "actor_input_contract_unchanged",
            "actor_input",
            not _bool(summary.get("actor_input_contract_changed", False)),
            summary.get("actor_input_contract_changed"),
            False,
        ),
        (
            "hidden_oracle_actor_input_absent",
            "actor_input",
            not _bool(summary.get("hidden_oracle_actor_input_detected", False)),
            summary.get("hidden_oracle_actor_input_detected"),
            False,
        ),
        (
            "future_target_actor_input_absent",
            "actor_input",
            not _bool(summary.get("future_target_actor_input_required", False)),
            summary.get("future_target_actor_input_required"),
            False,
        ),
        (
            "target_labels_actor_invisible",
            "actor_input",
            not any(_bool(row["target_labels_actor_visible"]) for row in readiness_rows),
            "all target_labels_actor_visible false",
            False,
        ),
        (
            "target_provenance_actor_invisible",
            "actor_input",
            not any(_bool(row["target_provenance_actor_visible"]) for row in readiness_rows),
            "all target_provenance_actor_visible false",
            False,
        ),
        (
            "source_route_outcome_progress_verdict_ttc_labels_absent",
            "actor_input",
            not any_label_visible(summary),
            actor_label_visibility(summary),
            "all false",
        ),
    ]
    return [
        {
            "guard_id": f"m3025_{guard_id}",
            "guard_family": family,
            "status_pass": bool(status_pass),
            "observed": observed,
            "expected": expected,
            "actor_input_change_required": False,
            "actor_visible_label_allowed": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for guard_id, family, status_pass, observed, expected in checks
    ]


def build_claim_boundary_rows(*, artifacts_present: bool, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("target_source_readiness_rows_materialized", "artifact", artifacts_present, "target_source_readiness_rows.csv"),
        ("target_source_blocker_rows_materialized", "artifact", artifacts_present, "target_source_blocker_rows.csv"),
        ("success_identity_guard_rows_materialized", "artifact", artifacts_present, "success_identity_guard_rows.csv"),
        ("actor_contract_guard_rows_materialized", "artifact", artifacts_present, "actor_contract_guard_rows.csv"),
        ("claim_boundary_materialized", "artifact", artifacts_present, "claim_boundary_rows.csv"),
        ("gate_matrix_materialized", "artifact", artifacts_present, "gate_matrix.csv"),
        ("summary_materialized", "artifact", artifacts_present, "summary.json"),
        ("doc_materialized", "artifact", artifacts_present, f"docs/{MILESTONE_ID}.md"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3026 audit manifest"),
    ]
    blocked = [
        ("target_source_feasibility_without_raw_trace", "target_source", "M3026 audit plus legal raw trace evidence"),
        ("episode_summary_as_raw_trace", "target_source", "raw actor-view trace capture artifact"),
        ("local_action_search_run", "target_source", "future audited target materialization route"),
        ("numeric_target_tensor_materialized", "target_materialization", "future audited target tensor materialization route"),
        ("residual_fitting_or_training", "training", "future fitting/training manifest and audit"),
        ("reset_step_rollout_replay_execution", "execution", "future audited execution manifest"),
        ("validation_result", "validation", "future validation manifest and audit"),
        ("ranking_or_winner_selection", "ranking", "future ranking manifest and audit"),
        ("checkpoint_mutation_or_promotion", "promotion", "future promotion gate"),
        ("repair_success", "verdict", "future repair audit and validation route"),
        ("driver_performance", "driver_performance", "future proof/generalization/claim audit"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("current_sim_verdict", "paper", "future current-sim synthesis"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation"),
        ("finite_window_vs_gru_result", "paper", "future fair comparison audit"),
        ("full_ideal_driver_completion", "full_goal", "future full ideal driver gate"),
        ("level3_self_identification", "self_id", "future self-ID proof gate"),
        ("hidden_oracle_or_ttc_actor_inputs", "contract", "actor contract forbids these shortcut inputs"),
    ]
    rows: list[dict[str, Any]] = []
    for claim_id, family, made, evidence in allowed:
        rows.append(claim(claim_id, family, True, bool(made), evidence))
    rows.extend(claim(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def claim(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m3025_{claim_id}",
        "claim_family": family,
        "allowed_in_m3025": allowed,
        "claim_made": bool(made),
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    readiness_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    success_guard_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest: Path,
) -> list[dict[str, Any]]:
    summary = source["m3022_summary"]
    objective_counts = Counter(str(row.get("objective_family", "")) for row in readiness_rows)
    failure_counts = Counter(str(row.get("failure_family", "")) for row in readiness_rows)
    future_rows = [row for row in readiness_rows if _bool(row["future_target_materialization_allowed"])]
    feasibility_count = sum(_bool(row["target_source_feasibility_established"]) for row in readiness_rows)
    numeric_target_count = sum(_bool(row["numeric_target_tensor_materialized"]) for row in readiness_rows)
    local_action_search_count = sum(_bool(row["local_action_search_run"]) for row in readiness_rows)
    forbidden_flags = forbidden_m3025_summary_flags(summary)
    gates = [
        (
            "source_artifacts_present",
            "lineage",
            all(source["source_exists"].values()),
            source["source_exists"],
            "all source artifacts and follow-up manifest present",
            "lineage_invalid",
        ),
        (
            "m3022_status_pass",
            "lineage",
            _bool(summary.get("status_pass")) and _bool(summary.get("gate_matrix_pass")),
            {"status_pass": summary.get("status_pass"), "gate_matrix_pass": summary.get("gate_matrix_pass")},
            "all true",
            "lineage_invalid",
        ),
        (
            "m3023_accepts_m3022",
            "lineage",
            M3023_DECISION in source["m3023_audit_text"],
            M3023_DECISION in source["m3023_audit_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m3024_admits_m3025",
            "lineage",
            M3024_DECISION in source["m3024_design_text"],
            M3024_DECISION in source["m3024_design_text"],
            True,
            "lineage_invalid",
        ),
        (
            "row_assignments_accounted",
            "denominator",
            len(readiness_rows) == EXPECTED_ROW_ASSIGNMENT_ROWS,
            len(readiness_rows),
            EXPECTED_ROW_ASSIGNMENT_ROWS,
            "metric_artifact",
        ),
        (
            "future_target_eligible_rows_accounted",
            "denominator",
            len(future_rows) == EXPECTED_FUTURE_TARGET_ELIGIBLE_ROWS,
            len(future_rows),
            EXPECTED_FUTURE_TARGET_ELIGIBLE_ROWS,
            "metric_artifact",
        ),
        (
            "success_identity_guards_accounted",
            "denominator",
            len(success_guard_rows) == EXPECTED_SUCCESS_IDENTITY_GUARD_ROWS,
            len(success_guard_rows),
            EXPECTED_SUCCESS_IDENTITY_GUARD_ROWS,
            "metric_artifact",
        ),
        (
            "objective_family_counts_match_expected",
            "objective_contract",
            dict(sorted(objective_counts.items())) == EXPECTED_OBJECTIVE_COUNTS,
            dict(sorted(objective_counts.items())),
            EXPECTED_OBJECTIVE_COUNTS,
            "metric_artifact",
        ),
        (
            "failure_family_counts_match_expected",
            "objective_contract",
            dict(sorted(failure_counts.items())) == EXPECTED_FAILURE_COUNTS,
            dict(sorted(failure_counts.items())),
            EXPECTED_FAILURE_COUNTS,
            "metric_artifact",
        ),
        (
            "raw_trace_availability_reported_for_future_rows",
            "target_source",
            all("raw_actor_view_trace_available" in row for row in future_rows),
            "reported" if all("raw_actor_view_trace_available" in row for row in future_rows) else "missing",
            "reported",
            "metric_artifact",
        ),
        (
            "episode_summaries_not_accepted_as_raw_traces",
            "target_source",
            not any(_bool(row["episode_summary_accepted_as_raw_trace"]) for row in readiness_rows),
            "none accepted",
            "none accepted",
            "contract_violation",
        ),
        (
            "raw_trace_missing_blockers_materialized",
            "target_source",
            len(blocker_rows) == EXPECTED_FUTURE_TARGET_ELIGIBLE_ROWS and feasibility_count == 0,
            {"blocker_rows": len(blocker_rows), "feasibility_count": feasibility_count},
            {"blocker_rows": EXPECTED_FUTURE_TARGET_ELIGIBLE_ROWS, "feasibility_count": 0},
            "metric_artifact",
        ),
        (
            "success_identity_not_positive_targets",
            "guardrail",
            not any(_bool(row["positive_target_candidate"]) for row in success_guard_rows),
            "positive targets 0",
            "positive targets 0",
            "contract_violation",
        ),
        (
            "numeric_target_tensor_materialized_count",
            "claim_boundary",
            numeric_target_count == 0,
            numeric_target_count,
            0,
            "contract_violation",
        ),
        (
            "local_action_search_run_count",
            "claim_boundary",
            local_action_search_count == 0,
            local_action_search_count,
            0,
            "contract_violation",
        ),
        (
            "actor_contract_guards_pass",
            "actor_contract",
            all(_bool(row["status_pass"]) for row in actor_guard_rows),
            [row["guard_id"] for row in actor_guard_rows if not _bool(row["status_pass"])],
            [],
            "contract_violation",
        ),
        (
            "claim_boundary_rows_pass",
            "claim_boundary",
            all(_bool(row["status_pass"]) for row in claim_rows),
            [row["claim_id"] for row in claim_rows if not _bool(row["status_pass"])],
            [],
            "contract_violation",
        ),
        (
            "no_m3025_execution_training_or_mutation",
            "claim_boundary",
            not any(forbidden_flags.values()),
            forbidden_flags,
            "all false",
            "contract_violation",
        ),
        (
            "required_artifacts_present",
            "artifact",
            required_artifacts_present,
            required_artifacts_present,
            True,
            "metric_artifact",
        ),
        (
            "follow_up_manifest_registered",
            "process",
            follow_up_manifest.exists(),
            follow_up_manifest.exists(),
            True,
            "lineage_invalid",
        ),
    ]
    return [
        {
            "gate_id": f"m3025_{name}",
            "gate_family": family,
            "status_pass": bool(status_pass),
            "observed": observed,
            "expected": expected,
            "failure_type": "" if bool(status_pass) else failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }
        for name, family, status_pass, observed, expected, failure_type in gates
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    readiness_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    success_guard_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    objective_counts = Counter(str(row.get("objective_family", "")) for row in readiness_rows)
    failure_counts = Counter(str(row.get("failure_family", "")) for row in readiness_rows)
    future_rows = [row for row in readiness_rows if _bool(row["future_target_materialization_allowed"])]
    feasibility_count = sum(_bool(row["target_source_feasibility_established"]) for row in readiness_rows)
    numeric_target_count = sum(_bool(row["numeric_target_tensor_materialized"]) for row in readiness_rows)
    local_action_search_count = sum(_bool(row["local_action_search_run"]) for row in readiness_rows)
    status_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    return {
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "status_pass": status_pass,
        "gate_matrix_pass": status_pass,
        "required_artifacts_present": required_artifacts_present,
        "selected_next_action": next_blocker,
        "next_blocker": next_blocker,
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "row_assignment_row_count": len(readiness_rows),
        "target_source_readiness_row_count": len(readiness_rows),
        "future_target_eligible_row_count": len(future_rows),
        "success_identity_guard_row_count": len(success_guard_rows),
        "target_source_blocker_row_count": len(blocker_rows),
        "raw_actor_view_trace_missing_blocker_count": len(blocker_rows),
        "target_source_feasibility_established_count": feasibility_count,
        "numeric_target_tensor_materialized_count": numeric_target_count,
        "local_action_search_run_count": local_action_search_count,
        "episode_summary_accepted_as_raw_trace_count": sum(
            _bool(row["episode_summary_accepted_as_raw_trace"]) for row in readiness_rows
        ),
        "objective_family_counts": dict(sorted(objective_counts.items())),
        "failure_family_counts": dict(sorted(failure_counts.items())),
        "actor_contract_guard_row_count": len(actor_guard_rows),
        "actor_contract_guard_rows_pass": all(_bool(row["status_pass"]) for row in actor_guard_rows),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(_bool(row["status_pass"]) for row in claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "actor_contract_shape_72_action_3": all(
            int(row["actor_observation_dim"]) == P0_OBSERVATION_DIM
            and int(row["actor_action_dim"]) == ACTION_DIM
            for row in readiness_rows
        ),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_detected": False,
        "future_target_actor_input_required": False,
        "source_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "outcome_labels_actor_visible": False,
        "objective_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "ttc_actor_input_required": False,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "replay_run": False,
        "validation_run": False,
        "training_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "profile_specific_tuning": False,
        "target_tensor_materialization_run": False,
        "target_materialization_run": False,
        "fitting_run": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifact_paths": {key: str(path) for key, path in paths.items()},
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return f"""# M3025 Engineering Controller Route A Post-Residual-Stop New Source Broad-Failure Target-Source Readiness Feasibility Materialization Preflight

## Summary

- status_pass: `{summary['status_pass']}`
- gate_matrix_pass: `{summary['gate_matrix_pass']}`
- required_artifacts_present: `{summary['required_artifacts_present']}`
- selected_next_action: `{summary['selected_next_action']}`
- follow_up_manifest: `{summary['follow_up_manifest']}`

## Accounting

```text
row assignments: {summary['row_assignment_row_count']}
target-source readiness rows: {summary['target_source_readiness_row_count']}
future target-eligible rows: {summary['future_target_eligible_row_count']}
success identity guard rows: {summary['success_identity_guard_row_count']}
target-source blocker rows: {summary['target_source_blocker_row_count']}
raw actor-view trace missing blockers: {summary['raw_actor_view_trace_missing_blocker_count']}
target-source feasibility established rows: {summary['target_source_feasibility_established_count']}
numeric target tensors materialized: {summary['numeric_target_tensor_materialized_count']}
local action search runs: {summary['local_action_search_run_count']}
episode summaries accepted as raw traces: {summary['episode_summary_accepted_as_raw_trace_count']}
```

Objective-family split:

```text
{format_counts(summary['objective_family_counts'])}
```

Failure-family split:

```text
{format_counts(summary['failure_family_counts'])}
```

## Readiness Result

M3025 materializes target-source readiness and blocker artifacts only. For this
new-source surface, every future target-eligible row remains blocked because no
raw actor-view observation/action/response trace artifact is present in the
M3015/M3018/M3022 chain. Scalar episode summaries are preserved as diagnostic
context but are not accepted as raw traces or teacher actions.

The three success_context rows are preserved as success identity guard rows
with `positive_target_candidate=false`.

## Actor And Claim Boundary

```text
actor observation/action: {summary['observation_shape']}/action {summary['action_shape']}
actor input contract changed: {summary['actor_input_contract_changed']}
hidden/oracle actor input detected: {summary['hidden_oracle_actor_input_detected']}
future target actor input required: {summary['future_target_actor_input_required']}
source labels actor-visible: {summary['source_labels_actor_visible']}
route labels actor-visible: {summary['route_labels_actor_visible']}
outcome labels actor-visible: {summary['outcome_labels_actor_visible']}
objective labels actor-visible: {summary['objective_labels_actor_visible']}
success/progress labels actor-visible: {summary['success_progress_labels_actor_visible']}
verdict labels actor-visible: {summary['verdict_labels_actor_visible']}
TTC actor input required: {summary['ttc_actor_input_required']}
```

M3025 does not run environment reset, step, rollout, replay, local-action
search, target tensor materialization, fitting, training, validation, ranking,
promotion, or checkpoint mutation. It makes no repair-success, driver
performance, paper, current-sim, high-fidelity, full-driver,
finite-window-vs-GRU, or self-ID claim.

## Next Route

M3025 registers M3026 as the required result audit before any interpretation or
continuation:

```text
{summary['selected_next_action']}
```
"""


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
            "A bounded result audit can accept or reject the M3025 target-source readiness "
            "feasibility materialization artifacts before any target tensor materialization local-action "
            "search fitting execution validation ranking performance paper high-fidelity full-driver "
            "finite-window-vs-GRU or self-ID claim."
        ),
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "target_source_readiness_rows.csv"),
                str(output_dir / "target_source_blocker_rows.csv"),
                str(output_dir / "success_identity_guard_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "parent_config": [
                f"experiments/manifests/{MILESTONE_ID}.json",
                "experiments/manifests/m3024-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-target-source-feasibility-admission-design.json",
            ],
            "parent_objective": [
                "audit M3025 target-source readiness feasibility materialization before any target tensor or trace-capture continuation"
            ],
            "derived_from": [
                MILESTONE_ID,
                "m3024-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-target-source-feasibility-admission-design",
                "m3023-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-objective-contract-materialization-result-audit",
            ],
            "blocked_by": [
                "M3025 readiness artifacts require result audit before interpretation",
                "raw actor-view trace availability may be missing and must not be converted into target-source feasibility by narrative",
            ],
            "supersedes": [
                "direct numeric target tensor materialization from readiness rows without audit",
                "direct fitting execution ranking validation or promotion from readiness blockers",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3026 must audit M3025 summary readiness blocker success identity actor claim and gate artifacts",
            "M3026 must preserve all 32 M3022 row assignments 29 future target-eligible rows and 3 success identity guards",
            "M3026 must not treat missing raw actor-view trace blockers as target-source feasibility",
            "M3026 must preserve actor 72/action 3 and no hidden oracle future-target source route outcome objective progress verdict or TTC actor input",
            "M3026 must select exactly one next route or stop state before any target tensor materialization or trace-capture continuation",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run environment reset step rollout replay validation training PPO local-action search or private holdout",
            "do not materialize numeric targets target tensors residual deltas masks weights fitted artifacts checkpoints or teacher actions",
            "do not convert episode summary metrics or readiness blockers into raw actor-view traces",
            "do not claim validation repair-success driver performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_residual_stop_source_axis_expansion",
            "evidence_axis": "new_source_broad_failure_target_source_readiness_feasibility_result_audit",
            "evidence_increment": "audits the M3025 readiness and blocker panel before choosing trace-capture admission synthesis or stop",
            "claim_scope": "Result audit only; no target tensor materialization local-action search fitting execution validation ranking promotion repair-success performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M3025 artifacts are incomplete or row accounting is broken",
                "stop if blockers would be interpreted as target-source feasibility",
                "stop if another process-only milestone would not change the next admission decision",
            ],
            "fallback_plan": [
                "route to trace-capture admission design if raw actor-view trace absence is accepted as the blocker",
                "route to artifact repair if M3025 joins or gates fail",
                "route to branch synthesis or stop if no legal target-source continuation remains",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3025 completes target-source readiness feasibility materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3025 target-source readiness feasibility materialization artifacts",
            "admission_evidence": [
                "M3025 writes readiness blocker success identity actor claim and gate artifacts",
                "M3025 must be audited before any trace-capture or target tensor continuation",
            ],
            "blocked_shortcuts": [
                "no target tensor materialization fitting execution validation ranking promotion repair-success or performance verdict",
                "no local-action search or target action generation",
                "no hidden oracle future-target source route outcome objective progress verdict or TTC actor input",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3026 status queue scoreboard research log and review",
                "one follow-up manifest only if M3026 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3026 audits M3025 artifacts and selects one next route or stop state",
                "M3026 preserves actor and claim boundaries",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3026 is target-source readiness result audit only and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M3026; no wrong-history reset-hidden zero-history finite-window GRU comparison or self-ID verdict is run."
            ],
            "temporal_evidence_window": "M3025 target-source readiness materialization only.",
            "negative_result_policy": "Preserve trace blockers rather than weakening self-ID or paper gates.",
            "allowed_claims": [
                "M3025 readiness artifact audit decision",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits newly materialized readiness and blocker artifacts",
            "paper_verdict_delta": "no paper verdict; may route to trace-capture admission or synthesis",
            "must_synthesize_if": [
                "M3026 cannot select exactly one next route or stop state",
                "M3026 would continue another process-only milestone without changing the next admission decision",
                "M3026 would claim validation readiness driver performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID evidence",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3026 audits M3025 readiness and blocker artifacts",
            "M3026 selects exactly one next route or stop state",
            "M3026 makes no target tensor fitting execution validation ranking promotion performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claim",
        ],
        "failure_criteria": [
            "M3026 hides missing M3025 artifacts or gate failures",
            "M3026 treats blocker rows as target tensor or fitting readiness",
            "M3026 changes actor input or action contract",
            "M3026 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3026 writes a bounded audit artifact and chooses one next route or stop state without overclaiming.",
        "commands": [{"name": "target_source_readiness_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "target_source_readiness_rows.csv"),
            str(output_dir / "target_source_blocker_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def run_target_source_readiness_feasibility_materialization_preflight(
    *,
    m3022_dir: Path | str = DEFAULT_M3022_DIR,
    m3023_audit: Path | str = DEFAULT_M3023_AUDIT,
    m3024_design: Path | str = DEFAULT_M3024_DESIGN,
    m3018_dir: Path | str = DEFAULT_M3018_DIR,
    m3015_dir: Path | str = DEFAULT_M3015_DIR,
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
        m3022_dir=Path(m3022_dir),
        m3023_audit=Path(m3023_audit),
        m3024_design=Path(m3024_design),
        m3018_dir=Path(m3018_dir),
        m3015_dir=Path(m3015_dir),
        follow_up_manifest=Path(follow_up_manifest),
    )
    readiness_rows = build_target_source_readiness_rows(source)
    blocker_rows = build_target_source_blocker_rows(readiness_rows)
    success_guard_rows = build_success_identity_guard_rows(readiness_rows)
    actor_guard_rows = build_actor_contract_guard_rows(readiness_rows, source)

    write_csv_rows(paths["target_source_readiness_rows"], readiness_rows, fieldnames=READINESS_FIELDNAMES)
    write_csv_rows(paths["target_source_blocker_rows"], blocker_rows, fieldnames=BLOCKER_FIELDNAMES)
    write_csv_rows(paths["success_identity_guard_rows"], success_guard_rows, fieldnames=SUCCESS_GUARD_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_guard_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_json(
        paths["follow_up_manifest"],
        build_follow_up_manifest(output_dir=output, doc_path=Path(doc_path), summary_path=paths["summary"]),
    )
    source["source_exists"]["follow_up_manifest"] = Path(follow_up_manifest).exists()
    write_run_state(
        paths["run_state"],
        {
            "readiness_row_count": len(readiness_rows),
            "target_source_blocker_row_count": len(blocker_rows),
            "success_identity_guard_row_count": len(success_guard_rows),
            "execution_performed_by_m3025": False,
            "complete": False,
            "next_blocker": next_blocker,
        },
    )

    required_core_artifacts_present = all(
        paths[key].exists()
        for key in PATH_KEYS
        if key not in {"summary", "doc", "claim_boundary_rows", "gate_matrix"}
    )
    claim_rows = build_claim_boundary_rows(
        artifacts_present=required_core_artifacts_present,
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        readiness_rows=readiness_rows,
        blocker_rows=blocker_rows,
        success_guard_rows=success_guard_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_core_artifacts_present,
        follow_up_manifest=Path(follow_up_manifest),
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        readiness_rows=readiness_rows,
        blocker_rows=blocker_rows,
        success_guard_rows=success_guard_rows,
        actor_guard_rows=actor_guard_rows,
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
    claim_rows = build_claim_boundary_rows(
        artifacts_present=required_artifacts_present,
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        readiness_rows=readiness_rows,
        blocker_rows=blocker_rows,
        success_guard_rows=success_guard_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
        follow_up_manifest=Path(follow_up_manifest),
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        readiness_rows=readiness_rows,
        blocker_rows=blocker_rows,
        success_guard_rows=success_guard_rows,
        actor_guard_rows=actor_guard_rows,
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
            "readiness_row_count": len(readiness_rows),
            "target_source_blocker_row_count": len(blocker_rows),
            "success_identity_guard_row_count": len(success_guard_rows),
            "execution_performed_by_m3025": False,
            "status_pass": summary["status_pass"],
            "gate_matrix_pass": summary["gate_matrix_pass"],
            "complete": summary["status_pass"],
            "next_blocker": next_blocker,
        },
    )
    return summary


def forbidden_m3025_summary_flags(summary: dict[str, Any]) -> dict[str, bool]:
    keys = [
        "environment_reset_run",
        "environment_step_run",
        "policy_action_run",
        "policy_rollout_run",
        "replay_run",
        "validation_run",
        "training_run",
        "ppo_run",
        "ranking_run",
        "winner_selected",
        "checkpoint_mutated",
        "checkpoint_promoted",
        "profile_specific_tuning",
        "target_tensor_materialization_run",
        "target_materialization_run",
        "fitting_run",
        "repair_success_claim_made",
        "driver_performance_claim_made",
        "validation_result_claim_made",
        "paper_claim_made",
        "current_sim_verdict_claim_made",
        "high_fidelity_validation_claim_made",
        "finite_window_vs_gru_claim_made",
        "full_ideal_driver_gate_passed",
        "full_ideal_driver_completion_claim_made",
        "level3_self_id_claim_made",
    ]
    return {key: _bool(summary.get(key, False)) for key in keys}


def any_label_visible(summary: dict[str, Any]) -> bool:
    return any(_bool(value) for value in actor_label_visibility(summary).values())


def actor_label_visibility(summary: dict[str, Any]) -> dict[str, bool]:
    return {
        "source_labels_actor_visible": _bool(summary.get("source_labels_actor_visible", False)),
        "route_labels_actor_visible": _bool(summary.get("route_labels_actor_visible", False)),
        "outcome_labels_actor_visible": _bool(summary.get("outcome_labels_actor_visible", False)),
        "objective_labels_actor_visible": _bool(summary.get("objective_labels_actor_visible", False)),
        "success_progress_labels_actor_visible": _bool(summary.get("success_progress_labels_actor_visible", False)),
        "verdict_labels_actor_visible": _bool(summary.get("verdict_labels_actor_visible", False)),
        "ttc_actor_input_required": _bool(summary.get("ttc_actor_input_required", False)),
    }


def format_counts(counts: dict[str, Any]) -> str:
    return "\n".join(f"{key}: {value}" for key, value in sorted(counts.items()))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3022-dir", type=Path, default=DEFAULT_M3022_DIR)
    parser.add_argument("--m3023-audit", type=Path, default=DEFAULT_M3023_AUDIT)
    parser.add_argument("--m3024-design", type=Path, default=DEFAULT_M3024_DESIGN)
    parser.add_argument("--m3018-dir", type=Path, default=DEFAULT_M3018_DIR)
    parser.add_argument("--m3015-dir", type=Path, default=DEFAULT_M3015_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args()
    summary = run_target_source_readiness_feasibility_materialization_preflight(
        m3022_dir=args.m3022_dir,
        m3023_audit=args.m3023_audit,
        m3024_design=args.m3024_design,
        m3018_dir=args.m3018_dir,
        m3015_dir=args.m3015_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(
        "m3025_target_source_readiness_feasibility "
        f"status_pass={summary['status_pass']} "
        f"gate_matrix_pass={summary['gate_matrix_pass']} "
        f"readiness_rows={summary['target_source_readiness_row_count']} "
        f"blockers={summary['target_source_blocker_row_count']} "
        f"success_guards={summary['success_identity_guard_row_count']} "
        f"next={summary['selected_next_action']}"
    )


if __name__ == "__main__":
    main()
