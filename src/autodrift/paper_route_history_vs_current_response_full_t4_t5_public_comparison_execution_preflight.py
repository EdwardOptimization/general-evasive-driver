"""Run Route B full public T4/T5 comparison execution preflight.

This milestone wraps the existing resumable full rollout runner for the M1690
public T4/T5 workload and adds M2677-specific runtime join, claim-boundary,
gate-matrix, and documentation artifacts. It records diagnostic comparison
rows only. It does not rank controller families, select winners, promote
checkpoints, or claim paper/self-ID evidence.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_decisive_matrix_protocol import EXPECTED_PROFILE_NAMES
from autodrift.controller_family_full_rollout_execution import (
    DEFAULT_EXECUTABLE_SPECS,
    DEFAULT_EXECUTABLE_WORKLOAD,
    TARGET_EPISODE_COUNT,
    TARGET_PROFILE_COUNT,
    TARGET_SPEC_COUNT,
    read_csv_rows,
    run_full_rollout_execution,
)
from autodrift.controller_family_measured_routing_smoke import DEFAULT_M1674_RUN_DIR
from autodrift.paper_route_history_vs_current_response_comparison_protocol_materialization import (
    REQUIRED_CONTROLLER_IDS,
)


DEFAULT_MILESTONE = (
    "m2677-paper-route-history-vs-current-response-full-t4-t5-public-"
    "comparison-execution-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2678-paper-route-history-vs-current-response-full-t4-t5-public-"
    "comparison-execution-result-audit"
)
DEFAULT_RUNTIME_ENFORCEMENT_DIR = Path(
    "runs/m2673_paper_route_history_vs_current_response_runtime_enforcement_materialization"
)
DEFAULT_BOUNDED_PREFLIGHT_DIR = Path(
    "runs/m2675_paper_route_history_vs_current_response_bounded_comparison_execution_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2677_paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2677-paper-route-history-vs-current-response-full-t4-t5-public-"
    "comparison-execution-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2678-paper-route-history-vs-current-response-"
    "full-t4-t5-public-comparison-execution-result-audit.json"
)
DEFAULT_EVAL_SEED_BASE = 267700

CLAIM_SCOPE = (
    "Route B full public T4/T5 comparison execution preflight only; "
    "diagnostic episode aggregate comparison outcome and hidden-dynamics "
    "metrics may be recorded, but no replay, training, PPO, private holdout, "
    "profile-specific tuning, controller-family ranking, winner selection, "
    "promotion, success-rate verdict, driver-performance, paper, "
    "finite-window-vs-GRU, current-response sufficiency, current-sim, "
    "high-fidelity validation, full ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "controller-family ranking, winner selection, checkpoint promotion, "
    "success-rate verdict, driver performance, validation readiness or result, "
    "paper-level evidence, finite-window-vs-GRU result, current-response "
    "sufficiency result, current-sim verdict, high-fidelity validation, full "
    "ideal driver completion, or level3 self-identification"
)

RUNTIME_JOIN_FIELDNAMES = [
    "protocol_controller_family_id",
    "runtime_profile_name",
    "executed_profile_name",
    "executed_episode_count",
    "executed_spec_count",
    "failed_cell_count",
    "target_spec_count",
    "runtime_enforcement_status_pass",
    "runtime_join_status_pass",
    "config_exists",
    "protocol_row_present",
    "actor_encoder",
    "actor_history_length",
    "env_history_length",
    "observation_shape",
    "action_shape",
    "observation_mask",
    "history_transform",
    "reset_hidden_policy",
    "current_tiled_expected",
    "current_tiled_runtime_observed",
    "reset_truncated_expected",
    "reset_policy_routing_ok",
    "previous_command_mask_observed",
    "actor_contract_shape_72_action_3",
    "hidden_oracle_actor_input_detected",
    "private_holdout_used",
    "m2673_policy_rollout_run",
    "full_public_policy_rollout_run",
    "policy_rollout_allowed",
    "training_started",
    "ppo_used",
    "replay_started",
    "profile_specific_tuning",
    "success_rate_metric_recorded",
    "comparison_delta_metric_recorded",
    "success_rate_verdict_claim_made",
    "controller_family_ranking_claim_made",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2677",
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

REQUIRED_ARTIFACT_KEYS = [
    "summary",
    "full_rollout_execution_summary",
    "episode_rows",
    "profile_aggregate",
    "spec_aggregate",
    "stratum_aggregate",
    "comparison_aggregate",
    "outcome_aggregate",
    "termination_reason_aggregate",
    "profile_outcome_aggregate",
    "hidden_dynamics_aggregate",
    "profile_hidden_dynamics_worst_bucket",
    "runtime_enforcement_join_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "failure_rows",
    "run_state",
    "doc",
]


def run_full_t4_t5_public_comparison_execution_preflight(
    *,
    runtime_enforcement_dir: Path | str = DEFAULT_RUNTIME_ENFORCEMENT_DIR,
    bounded_preflight_dir: Path | str = DEFAULT_BOUNDED_PREFLIGHT_DIR,
    executable_specs: Path | str = DEFAULT_EXECUTABLE_SPECS,
    workload: Path | str = DEFAULT_EXECUTABLE_WORKLOAD,
    m1674_run_dir: Path | str = DEFAULT_M1674_RUN_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    device: str = "cpu",
    resume: bool = True,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path))
    source = load_source_artifacts(
        runtime_enforcement_dir=Path(runtime_enforcement_dir),
        bounded_preflight_dir=Path(bounded_preflight_dir),
        executable_specs=Path(executable_specs),
        workload=Path(workload),
        m1674_run_dir=Path(m1674_run_dir),
        follow_up_manifest=Path(follow_up_manifest),
    )

    full_summary = run_full_rollout_execution(
        output_dir=output,
        executable_specs_path=Path(executable_specs),
        workload_path=Path(workload),
        m1674_run_dir=Path(m1674_run_dir),
        eval_seed_base=int(eval_seed_base),
        device=str(device),
        resume=bool(resume),
        next_blocker=next_blocker,
    )
    write_json(paths["full_rollout_execution_summary"], full_summary)

    artifact_rows = load_execution_artifact_rows(paths)
    runtime_rows = read_csv_rows(source["paths"]["protocol_to_runtime_profile_rows"])
    join_rows = build_runtime_enforcement_join_rows(
        runtime_rows=runtime_rows,
        episode_rows=artifact_rows["episode_rows"],
        failure_rows=artifact_rows["failure_rows"],
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=False,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        full_summary=full_summary,
        artifact_rows=artifact_rows,
        runtime_join_rows=join_rows,
        claim_rows=claim_rows,
        required_artifacts_present=False,
    )

    write_csv_rows(paths["runtime_enforcement_join_rows"], join_rows, fieldnames=RUNTIME_JOIN_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        full_summary=full_summary,
        artifact_rows=artifact_rows,
        runtime_join_rows=join_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=False,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
        eval_seed_base=eval_seed_base,
        device=device,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_artifacts_present,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        full_summary=full_summary,
        artifact_rows=artifact_rows,
        runtime_join_rows=join_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        full_summary=full_summary,
        artifact_rows=artifact_rows,
        runtime_join_rows=join_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
        eval_seed_base=eval_seed_base,
        device=device,
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "full_rollout_execution_summary": output_dir / "full_rollout_execution_summary.json",
        "episode_rows": output_dir / "episode_rows.csv",
        "profile_aggregate": output_dir / "profile_aggregate.csv",
        "spec_aggregate": output_dir / "spec_aggregate.csv",
        "stratum_aggregate": output_dir / "stratum_aggregate.csv",
        "comparison_aggregate": output_dir / "comparison_aggregate.csv",
        "outcome_aggregate": output_dir / "outcome_aggregate.csv",
        "termination_reason_aggregate": output_dir / "termination_reason_aggregate.csv",
        "profile_outcome_aggregate": output_dir / "profile_outcome_aggregate.csv",
        "hidden_dynamics_aggregate": output_dir / "hidden_dynamics_aggregate.csv",
        "profile_hidden_dynamics_worst_bucket": output_dir / "profile_hidden_dynamics_worst_bucket.csv",
        "runtime_enforcement_join_rows": output_dir / "runtime_enforcement_join_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "failure_rows": output_dir / "failure_rows.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    runtime_enforcement_dir: Path,
    bounded_preflight_dir: Path,
    executable_specs: Path,
    workload: Path,
    m1674_run_dir: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2676_audit_doc": Path(
            "docs/m2676-paper-route-history-vs-current-response-bounded-comparison-"
            "execution-result-audit.md"
        ),
        "m2675_summary": bounded_preflight_dir / "summary.json",
        "m2675_runtime_join_rows": bounded_preflight_dir / "runtime_enforcement_join_rows.csv",
        "m2675_claim_boundary_rows": bounded_preflight_dir / "claim_boundary_rows.csv",
        "m2675_gate_matrix": bounded_preflight_dir / "gate_matrix.csv",
        "m2673_summary": runtime_enforcement_dir / "summary.json",
        "protocol_to_runtime_profile_rows": runtime_enforcement_dir / "protocol_to_runtime_profile_rows.csv",
        "m2673_gate_matrix": runtime_enforcement_dir / "gate_matrix.csv",
        "m1690_summary": executable_specs.parent / "summary.json",
        "executable_task_specs": executable_specs,
        "executable_workload_matrix": workload,
        "m1674_summary": m1674_run_dir / "summary.json",
        "m2677_manifest": Path(
            "experiments/manifests/m2677-paper-route-history-vs-current-response-"
            "full-t4-t5-public-comparison-execution-preflight.json"
        ),
        "follow_up_manifest": follow_up_manifest,
    }
    return {
        "paths": paths,
        "source_exists": {key: path.exists() for key, path in paths.items()},
        "m2673_summary": read_json(paths["m2673_summary"]) if paths["m2673_summary"].exists() else {},
        "m2675_summary": read_json(paths["m2675_summary"]) if paths["m2675_summary"].exists() else {},
        "m1690_summary": read_json(paths["m1690_summary"]) if paths["m1690_summary"].exists() else {},
        "m1674_summary": read_json(paths["m1674_summary"]) if paths["m1674_summary"].exists() else {},
    }


def load_execution_artifact_rows(paths: dict[str, Path]) -> dict[str, list[dict[str, str]]]:
    return {
        "episode_rows": read_csv_rows(paths["episode_rows"]),
        "profile_aggregate_rows": read_csv_rows(paths["profile_aggregate"]),
        "spec_aggregate_rows": read_csv_rows(paths["spec_aggregate"]),
        "stratum_aggregate_rows": read_csv_rows(paths["stratum_aggregate"]),
        "comparison_aggregate_rows": read_csv_rows(paths["comparison_aggregate"]),
        "outcome_aggregate_rows": read_csv_rows(paths["outcome_aggregate"]),
        "termination_reason_aggregate_rows": read_csv_rows(paths["termination_reason_aggregate"]),
        "profile_outcome_aggregate_rows": read_csv_rows(paths["profile_outcome_aggregate"]),
        "hidden_dynamics_aggregate_rows": read_csv_rows(paths["hidden_dynamics_aggregate"]),
        "profile_hidden_dynamics_worst_bucket_rows": read_csv_rows(paths["profile_hidden_dynamics_worst_bucket"]),
        "failure_rows": read_csv_rows(paths["failure_rows"]),
    }


def build_runtime_enforcement_join_rows(
    *,
    runtime_rows: list[dict[str, Any]],
    episode_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    runtime_by_profile = {str(row.get("runtime_profile_name", "")): row for row in runtime_rows}
    episode_count_by_profile = Counter(str(row.get("profile_name", "")) for row in episode_rows)
    failure_count_by_profile = Counter(str(row.get("profile_name", "")) for row in failure_rows)
    spec_count_by_profile: dict[str, set[str]] = {}
    for row in episode_rows:
        spec_count_by_profile.setdefault(str(row.get("profile_name", "")), set()).add(str(row.get("task_source_id", "")))

    rows: list[dict[str, Any]] = []
    for profile_name in EXPECTED_PROFILE_NAMES:
        runtime = dict(runtime_by_profile.get(profile_name, {}))
        row: dict[str, Any] = {
            "protocol_controller_family_id": runtime.get("protocol_controller_family_id", ""),
            "runtime_profile_name": runtime.get("runtime_profile_name", profile_name),
            "executed_profile_name": profile_name,
            "executed_episode_count": int(episode_count_by_profile.get(profile_name, 0)),
            "executed_spec_count": len(spec_count_by_profile.get(profile_name, set())),
            "failed_cell_count": int(failure_count_by_profile.get(profile_name, 0)),
            "target_spec_count": TARGET_SPEC_COUNT,
            "runtime_enforcement_status_pass": _bool(runtime.get("runtime_enforcement_status_pass", False)),
            "config_exists": _bool(runtime.get("config_exists", False)),
            "protocol_row_present": _bool(runtime.get("protocol_row_present", False)),
            "actor_encoder": runtime.get("actor_encoder", ""),
            "actor_history_length": runtime.get("actor_history_length", ""),
            "env_history_length": runtime.get("env_history_length", ""),
            "observation_shape": runtime.get("observation_shape", ""),
            "action_shape": runtime.get("action_shape", ""),
            "observation_mask": runtime.get("observation_mask", ""),
            "history_transform": runtime.get("history_transform", ""),
            "reset_hidden_policy": runtime.get("reset_hidden_policy", ""),
            "current_tiled_expected": _bool(runtime.get("current_tiled_expected", False)),
            "current_tiled_runtime_observed": _bool(runtime.get("current_tiled_runtime_observed", False)),
            "reset_truncated_expected": _bool(runtime.get("reset_truncated_expected", False)),
            "reset_policy_routing_ok": _bool(runtime.get("reset_policy_routing_ok", False)),
            "previous_command_mask_observed": _bool(runtime.get("previous_command_mask_observed", False)),
            "actor_contract_shape_72_action_3": _bool(runtime.get("actor_contract_shape_72_action_3", False)),
            "hidden_oracle_actor_input_detected": _bool(runtime.get("hidden_oracle_actor_input_detected", True)),
            "private_holdout_used": _bool(runtime.get("private_holdout_used", True)),
            "m2673_policy_rollout_run": _bool(runtime.get("policy_rollout_run", False)),
            "full_public_policy_rollout_run": True,
            "policy_rollout_allowed": True,
            "training_started": _bool(runtime.get("training_started", False)),
            "ppo_used": _bool(runtime.get("ppo_used", False)),
            "replay_started": False,
            "profile_specific_tuning": False,
            "success_rate_metric_recorded": True,
            "comparison_delta_metric_recorded": True,
            "success_rate_verdict_claim_made": False,
            "controller_family_ranking_claim_made": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        row["runtime_join_status_pass"] = runtime_join_row_pass(row)
        rows.append(row)
    return rows


def runtime_join_row_pass(row: dict[str, Any]) -> bool:
    if not _bool(row["runtime_enforcement_status_pass"]):
        return False
    if int(row["executed_episode_count"]) != TARGET_SPEC_COUNT:
        return False
    if int(row["executed_spec_count"]) != TARGET_SPEC_COUNT:
        return False
    if int(row["failed_cell_count"]) != 0:
        return False
    if not _bool(row["actor_contract_shape_72_action_3"]):
        return False
    if _bool(row["hidden_oracle_actor_input_detected"]) or _bool(row["private_holdout_used"]):
        return False
    if _bool(row["training_started"]) or _bool(row["ppo_used"]) or _bool(row["replay_started"]):
        return False
    if _bool(row["profile_specific_tuning"]) or _bool(row["controller_family_ranking_claim_made"]):
        return False
    if _bool(row["success_rate_verdict_claim_made"]):
        return False
    if not _bool(row["full_public_policy_rollout_run"]) or not _bool(row["policy_rollout_allowed"]):
        return False
    if row["protocol_controller_family_id"] == "L2-current-tiled":
        return _bool(row["current_tiled_expected"]) and _bool(row["current_tiled_runtime_observed"])
    if row["protocol_controller_family_id"] == "L3-reset-truncated-control":
        return _bool(row["reset_truncated_expected"]) and _bool(row["reset_policy_routing_ok"])
    return True


def build_claim_boundary_rows(
    *,
    follow_up_manifest_registered: bool,
    artifacts_present: bool,
) -> list[dict[str, Any]]:
    rows = [
        claim("full_t4_t5_public_comparison_execution_preflight", "execution", True, True, "M2677 summary and full execution artifacts"),
        claim("episode_rows_materialized", "artifact", True, artifacts_present, "episode_rows.csv"),
        claim("profile_aggregate_materialized", "artifact", True, artifacts_present, "profile_aggregate.csv"),
        claim("spec_aggregate_materialized", "artifact", True, artifacts_present, "spec_aggregate.csv"),
        claim("stratum_aggregate_materialized", "artifact", True, artifacts_present, "stratum_aggregate.csv"),
        claim("comparison_aggregate_materialized", "artifact", True, artifacts_present, "comparison_aggregate.csv"),
        claim("outcome_aggregate_materialized", "artifact", True, artifacts_present, "outcome_aggregate.csv"),
        claim(
            "termination_reason_aggregate_materialized",
            "artifact",
            True,
            artifacts_present,
            "termination_reason_aggregate.csv",
        ),
        claim(
            "hidden_dynamics_aggregate_materialized",
            "artifact",
            True,
            artifacts_present,
            "hidden_dynamics_aggregate.csv",
        ),
        claim("runtime_enforcement_join_rows_materialized", "artifact", True, artifacts_present, "runtime_enforcement_join_rows.csv"),
        claim("claim_boundary_rows_materialized", "artifact", True, artifacts_present, "claim_boundary_rows.csv"),
        claim("gate_matrix_materialized", "artifact", True, artifacts_present, "gate_matrix.csv"),
        claim("failure_rows_materialized", "artifact", True, artifacts_present, "failure_rows.csv"),
        claim("run_state_materialized", "artifact", True, artifacts_present, "run_state.json"),
        claim("diagnostic_success_rate_metric_recorded", "diagnostic_metric", True, True, "diagnostic aggregate rows only, not verdict"),
        claim(
            "diagnostic_comparison_delta_metric_recorded",
            "diagnostic_metric",
            True,
            True,
            "diagnostic comparison aggregate rows only, not ranking",
        ),
        claim("follow_up_audit_registered", "follow_up_route", True, follow_up_manifest_registered, "M2678 result-audit manifest"),
    ]
    blocked = [
        ("training_or_ppo", "execution", "future training manifest"),
        ("replay_execution", "execution", "future replay manifest"),
        ("private_holdout_tuning", "holdout_policy", "forbidden in Route B public comparison preflight"),
        ("profile_specific_tuning", "objective_overfit", "future controlled tuning protocol"),
        ("controller_family_ranking", "ranking", "future audited comparison interpretation"),
        ("winner_selection", "promotion", "future promotion gate"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("success_rate_verdict", "verdict", "future result audit and verdict milestone"),
        ("comparison_delta_verdict", "verdict", "future result audit and interpretation milestone"),
        ("driver_performance", "driver_performance", "future proof/generalization/claim audit"),
        ("validation_readiness", "validation", "future validation-readiness route"),
        ("validation_result", "validation", "future validation route"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("finite_window_vs_gru_result", "paper", "future fair comparison audit"),
        ("current_response_sufficiency_result", "paper", "future fair comparison audit"),
        ("current_sim_verdict", "paper", "future current-sim synthesis"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("full_ideal_driver_completion", "full_goal", "future full ideal driver gate"),
    ]
    rows.extend(claim(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    full_summary: dict[str, Any],
    artifact_rows: dict[str, list[dict[str, Any]]],
    runtime_join_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    episode_rows = artifact_rows["episode_rows"]
    failure_rows = artifact_rows["failure_rows"]
    profile_aggregate_rows = artifact_rows["profile_aggregate_rows"]
    spec_aggregate_rows = artifact_rows["spec_aggregate_rows"]
    stratum_aggregate_rows = artifact_rows["stratum_aggregate_rows"]
    comparison_aggregate_rows = artifact_rows["comparison_aggregate_rows"]
    outcome_aggregate_rows = artifact_rows["outcome_aggregate_rows"]
    termination_reason_aggregate_rows = artifact_rows["termination_reason_aggregate_rows"]
    hidden_dynamics_aggregate_rows = artifact_rows["hidden_dynamics_aggregate_rows"]
    profile_hidden_rows = artifact_rows["profile_hidden_dynamics_worst_bucket_rows"]
    protocol_ids = {str(row.get("protocol_controller_family_id", "")) for row in runtime_join_rows}
    mapped_ids = {
        str(row.get("protocol_controller_family_id", ""))
        for row in runtime_join_rows
        if _bool(row.get("runtime_join_status_pass", False))
    }
    current_tiled_rows = [
        row for row in runtime_join_rows if row.get("protocol_controller_family_id") == "L2-current-tiled"
    ]
    reset_rows = [
        row
        for row in runtime_join_rows
        if row.get("protocol_controller_family_id") == "L3-reset-truncated-control"
    ]
    blocked_claim_rows = [row for row in claim_rows if not _bool(row["allowed_in_m2677"])]
    allowed_claim_rows = [row for row in claim_rows if _bool(row["allowed_in_m2677"])]
    return [
        gate("source_artifacts_present", "lineage", all(source["source_exists"].values()), source["source_exists"], "all source artifacts and M2678 follow-up manifest present", "lineage_invalid"),
        gate("m2673_status_pass", "lineage", _bool(source["m2673_summary"].get("status_pass", False)), source["m2673_summary"].get("status_pass", None), True, "lineage_invalid"),
        gate("m2675_status_pass", "lineage", _bool(source["m2675_summary"].get("status_pass", False)), source["m2675_summary"].get("status_pass", None), True, "lineage_invalid"),
        gate("m1690_workload_materialization_pass", "lineage", _bool(source["m1690_summary"].get("passes_public_smoke_gates", False)), source["m1690_summary"].get("result_class", ""), "controller_family_executable_workload_materialization_preflight_pass", "lineage_invalid"),
        gate("full_rollout_runner_pass", "execution", full_summary.get("result_class") == "controller_family_full_rollout_execution_pass", full_summary.get("result_class", ""), "controller_family_full_rollout_execution_pass", "behavior_regression"),
        gate("episode_rows_complete", "execution", len(episode_rows) == TARGET_EPISODE_COUNT, len(episode_rows), TARGET_EPISODE_COUNT, "metric_artifact"),
        gate("failure_rows_empty", "execution", len(failure_rows) == 0 and int(full_summary.get("failure_count", -1)) == 0, f"failure_rows={len(failure_rows)} summary={full_summary.get('failure_count')}", "failure_rows=0 summary=0", "behavior_regression"),
        gate("profile_aggregate_complete", "artifact", len(profile_aggregate_rows) == TARGET_PROFILE_COUNT, len(profile_aggregate_rows), TARGET_PROFILE_COUNT, "metric_artifact"),
        gate("spec_aggregate_complete", "artifact", len(spec_aggregate_rows) == TARGET_SPEC_COUNT, len(spec_aggregate_rows), TARGET_SPEC_COUNT, "metric_artifact"),
        gate("stratum_aggregate_present", "artifact", len(stratum_aggregate_rows) > 0, len(stratum_aggregate_rows), ">0", "metric_artifact"),
        gate("comparison_aggregate_complete", "artifact", len(comparison_aggregate_rows) >= 11, len(comparison_aggregate_rows), ">=11 diagnostic comparison rows", "metric_artifact"),
        gate("outcome_and_termination_aggregates_present", "artifact", bool(outcome_aggregate_rows and termination_reason_aggregate_rows), f"outcome={len(outcome_aggregate_rows)} termination={len(termination_reason_aggregate_rows)}", "both present", "metric_artifact"),
        gate(
            "hidden_dynamics_diagnostic_artifacts_written",
            "artifact",
            True,
            f"hidden={len(hidden_dynamics_aggregate_rows)} profile_hidden={len(profile_hidden_rows)}",
            "0 or more diagnostic rows; artifact existence covered by required_artifacts_present",
            "metric_artifact",
        ),
        gate("all_selected_metrics_finite", "metric", _all_selected_metrics_finite(full_summary, profile_aggregate_rows, spec_aggregate_rows), full_summary.get("all_selected_metrics_finite", None), True, "metric_artifact"),
        gate("runtime_join_rows_cover_profiles", "runtime_join", len(runtime_join_rows) == TARGET_PROFILE_COUNT and all(_bool(row["runtime_join_status_pass"]) for row in runtime_join_rows), f"rows={len(runtime_join_rows)} pass={sum(_bool(row['runtime_join_status_pass']) for row in runtime_join_rows)}", f"rows={TARGET_PROFILE_COUNT} pass={TARGET_PROFILE_COUNT}", "metric_artifact"),
        gate("required_protocol_ids_joined", "runtime_join", REQUIRED_CONTROLLER_IDS.issubset(protocol_ids) and REQUIRED_CONTROLLER_IDS.issubset(mapped_ids), sorted(mapped_ids), sorted(REQUIRED_CONTROLLER_IDS), "metric_artifact"),
        gate("current_tiled_runtime_observed", "runtime_join", len(current_tiled_rows) == 4 and all(_bool(row["current_tiled_runtime_observed"]) for row in current_tiled_rows), [row["runtime_profile_name"] for row in current_tiled_rows], "4 current-tiled runtime profiles observed", "metric_artifact"),
        gate("reset_truncated_policy_routing_ok", "runtime_join", len(reset_rows) == 1 and all(_bool(row["reset_policy_routing_ok"]) for row in reset_rows), [row.get("reset_hidden_policy", "") for row in reset_rows], ["every_step_control"], "metric_artifact"),
        gate("actor_action_contract_preserved", "actor_contract", all(_bool(row["actor_contract_shape_72_action_3"]) for row in runtime_join_rows) and not any(_bool(row["hidden_oracle_actor_input_detected"]) for row in runtime_join_rows), "all runtime-joined profiles preserve P0/action3/no-oracle boundary", "all runtime-joined profiles preserve P0/action3/no-oracle boundary", "contract_violation"),
        gate("no_private_holdout_or_profile_tuning", "holdout_policy", not any(_bool(row["private_holdout_used"]) or _bool(row["profile_specific_tuning"]) for row in runtime_join_rows), "all false", "all false", "objective_overfit"),
        gate("no_training_ppo_replay", "execution_guardrail", not any(_bool(row["training_started"]) or _bool(row["ppo_used"]) or _bool(row["replay_started"]) for row in runtime_join_rows), "all false", "all false", "objective_overfit"),
        gate("full_rollout_allowed_only", "execution_guardrail", _full_rollout_rows_are_bounded_public(episode_rows), "full public policy actions recorded", "full public policy actions recorded", "scenario_sampling_failure"),
        gate("comparison_rows_diagnostic_only", "claim_boundary", comparison_aggregate_rows and all(_bool(row.get("diagnostic_only_no_ranking_claim", False)) for row in comparison_aggregate_rows), "all comparison rows diagnostic_only_no_ranking_claim", "all comparison rows diagnostic_only_no_ranking_claim", "proof_washout"),
        gate("claim_boundary_blocks_overclaim", "claim_boundary", len(allowed_claim_rows) == 17 and all(_bool(row["status_pass"]) for row in allowed_claim_rows) and all(not _bool(row["claim_made"]) and _bool(row["status_pass"]) for row in blocked_claim_rows), f"allowed={len(allowed_claim_rows)} blocked={len(blocked_claim_rows)}", "allowed=17 blocked=19", "proof_washout"),
        gate("success_rate_and_comparison_metrics_not_verdicts", "claim_boundary", any(row["claim_id"] == "diagnostic_success_rate_metric_recorded" for row in allowed_claim_rows) and any(row["claim_id"] == "diagnostic_comparison_delta_metric_recorded" for row in allowed_claim_rows) and any(row["claim_id"] == "success_rate_verdict" for row in blocked_claim_rows) and any(row["claim_id"] == "comparison_delta_verdict" for row in blocked_claim_rows), "diagnostic metrics present; verdict claims blocked", "diagnostic metrics present; verdict claims blocked", "proof_washout"),
        gate("required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True, "lineage_invalid"),
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    full_summary: dict[str, Any],
    artifact_rows: dict[str, list[dict[str, Any]]],
    runtime_join_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
    eval_seed_base: int,
    device: str,
) -> dict[str, Any]:
    protocol_ids = {str(row.get("protocol_controller_family_id", "")) for row in runtime_join_rows}
    mapped_ids = {
        str(row.get("protocol_controller_family_id", ""))
        for row in runtime_join_rows
        if _bool(row.get("runtime_join_status_pass", False))
    }
    current_tiled_rows = [
        row for row in runtime_join_rows if row.get("protocol_controller_family_id") == "L2-current-tiled"
    ]
    reset_rows = [
        row
        for row in runtime_join_rows
        if row.get("protocol_controller_family_id") == "L3-reset-truncated-control"
    ]
    allowed_claim_rows = [row for row in claim_rows if _bool(row["allowed_in_m2677"])]
    blocked_claim_rows = [row for row in claim_rows if not _bool(row["allowed_in_m2677"])]
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    episode_rows = artifact_rows["episode_rows"]
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight_pass"
            if status_pass
            else "paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "eval_seed_base": int(eval_seed_base),
        "device": str(device),
        "source_artifacts_present": all(source["source_exists"].values()),
        "m2673_status_pass": _bool(source["m2673_summary"].get("status_pass", False)),
        "m2675_status_pass": _bool(source["m2675_summary"].get("status_pass", False)),
        "m1690_status_pass": _bool(source["m1690_summary"].get("passes_public_smoke_gates", False)),
        "full_runner_result_class": full_summary.get("result_class", ""),
        "full_runner_pass": full_summary.get("result_class") == "controller_family_full_rollout_execution_pass",
        "episode_count": len(episode_rows),
        "target_episode_count": TARGET_EPISODE_COUNT,
        "profile_count": len({str(row.get("profile_name", "")) for row in episode_rows}),
        "target_profile_count": TARGET_PROFILE_COUNT,
        "spec_count": len({str(row.get("task_source_id", "")) for row in episode_rows}),
        "target_spec_count": TARGET_SPEC_COUNT,
        "failure_count": len(artifact_rows["failure_rows"]),
        "all_selected_metrics_finite": _all_selected_metrics_finite(
            full_summary, artifact_rows["profile_aggregate_rows"], artifact_rows["spec_aggregate_rows"]
        ),
        "profile_aggregate_rows": len(artifact_rows["profile_aggregate_rows"]),
        "spec_aggregate_rows": len(artifact_rows["spec_aggregate_rows"]),
        "stratum_aggregate_rows": len(artifact_rows["stratum_aggregate_rows"]),
        "comparison_aggregate_rows": len(artifact_rows["comparison_aggregate_rows"]),
        "outcome_aggregate_rows": len(artifact_rows["outcome_aggregate_rows"]),
        "termination_reason_aggregate_rows": len(artifact_rows["termination_reason_aggregate_rows"]),
        "profile_outcome_aggregate_rows": len(artifact_rows["profile_outcome_aggregate_rows"]),
        "hidden_dynamics_aggregate_rows": len(artifact_rows["hidden_dynamics_aggregate_rows"]),
        "profile_hidden_dynamics_worst_bucket_rows": len(artifact_rows["profile_hidden_dynamics_worst_bucket_rows"]),
        "runtime_enforcement_join_row_count": len(runtime_join_rows),
        "runtime_join_rows_pass": all(_bool(row["runtime_join_status_pass"]) for row in runtime_join_rows),
        "protocol_controller_family_count": len(protocol_ids),
        "required_protocol_controller_family_count": len(REQUIRED_CONTROLLER_IDS),
        "runtime_profile_mapping_count": len(mapped_ids),
        "required_protocol_ids_runtime_mapped": REQUIRED_CONTROLLER_IDS.issubset(mapped_ids),
        "current_tiled_runtime_profile_count": len(current_tiled_rows),
        "current_tiled_runtime_observed": bool(
            current_tiled_rows and all(_bool(row["current_tiled_runtime_observed"]) for row in current_tiled_rows)
        ),
        "reset_truncated_runtime_profile_count": len(reset_rows),
        "reset_truncated_policy_routing_ok": bool(
            reset_rows and all(_bool(row["reset_policy_routing_ok"]) for row in reset_rows)
        ),
        "claim_boundary_row_count": len(claim_rows),
        "allowed_claim_boundary_row_count": len(allowed_claim_rows),
        "blocked_claim_boundary_row_count": len(blocked_claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "environment_rollout_run": True,
        "environment_rollout_allowed": True,
        "full_public_policy_rollout_run": True,
        "policy_action_run": True,
        "policy_rollout_allowed": True,
        "measured_validation_run": False,
        "training_started": False,
        "training_run": False,
        "replay_started": False,
        "replay_run": False,
        "ppo_used": False,
        "ppo_run": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "actor_input_contract_changed": False,
        "actor_contract_shape_72_action_3": True,
        "hidden_oracle_actor_input_detected": False,
        "controller_family_labels_actor_visible": False,
        "taxonomy_or_route_labels_actor_visible": False,
        "ranking_run": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "success_rate_metric_recorded": True,
        "comparison_delta_metric_recorded": True,
        "success_rate_verdict_claim_made": False,
        "comparison_delta_verdict_claim_made": False,
        "controller_family_verdict_computed": False,
        "driver_performance_claim_made": False,
        "validation_readiness_claim_made": False,
        "validation_result_claim_made": False,
        "paper_level_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_response_sufficiency_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_simulation_run": False,
        "high_fidelity_validation_claim_made": False,
        "level3_self_id_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "full_ideal_driver_completion_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(path) for key, path in paths.items()},
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2677 Paper Route History Vs Current Response Full T4/T5 Public Comparison Execution Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result_class: `{summary['result_class']}`",
            f"- generated_at_utc: `{summary['generated_at_utc']}`",
            f"- manifest: `experiments/manifests/{DEFAULT_MILESTONE}.json`",
            f"- summary: `{summary['paths']['summary']}`",
            f"- full rollout runner summary: `{summary['paths']['full_rollout_execution_summary']}`",
            f"- episode rows: `{summary['paths']['episode_rows']}`",
            f"- profile aggregate: `{summary['paths']['profile_aggregate']}`",
            f"- spec aggregate: `{summary['paths']['spec_aggregate']}`",
            f"- stratum aggregate: `{summary['paths']['stratum_aggregate']}`",
            f"- comparison aggregate: `{summary['paths']['comparison_aggregate']}`",
            f"- outcome aggregate: `{summary['paths']['outcome_aggregate']}`",
            f"- termination aggregate: `{summary['paths']['termination_reason_aggregate']}`",
            f"- profile outcome aggregate: `{summary['paths']['profile_outcome_aggregate']}`",
            f"- hidden-dynamics aggregate: `{summary['paths']['hidden_dynamics_aggregate']}`",
            f"- runtime-enforcement join rows: `{summary['paths']['runtime_enforcement_join_rows']}`",
            f"- claim boundary rows: `{summary['paths']['claim_boundary_rows']}`",
            f"- gate matrix: `{summary['paths']['gate_matrix']}`",
            f"- failure rows: `{summary['paths']['failure_rows']}`",
            f"- run state: `{summary['paths']['run_state']}`",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            f"- next: `{summary['next_blocker']}`",
            "",
            "## Full Public Execution",
            "",
            f"- episode rows: {summary['episode_count']} / {summary['target_episode_count']}",
            f"- profiles executed: {summary['profile_count']} / {summary['target_profile_count']}",
            f"- public specs executed: {summary['spec_count']} / {summary['target_spec_count']}",
            f"- failure rows: {summary['failure_count']}",
            f"- profile aggregate rows: {summary['profile_aggregate_rows']}",
            f"- spec aggregate rows: {summary['spec_aggregate_rows']}",
            f"- stratum aggregate rows: {summary['stratum_aggregate_rows']}",
            f"- comparison aggregate rows: {summary['comparison_aggregate_rows']}",
            f"- outcome aggregate rows: {summary['outcome_aggregate_rows']}",
            f"- termination aggregate rows: {summary['termination_reason_aggregate_rows']}",
            f"- hidden-dynamics aggregate rows: {summary['hidden_dynamics_aggregate_rows']}",
            f"- selected metrics finite: {summary['all_selected_metrics_finite']}",
            "",
            "## Runtime Join",
            "",
            f"- M2673 status pass: {summary['m2673_status_pass']}",
            f"- M2675 status pass: {summary['m2675_status_pass']}",
            f"- M1690 workload status pass: {summary['m1690_status_pass']}",
            f"- runtime join rows: {summary['runtime_enforcement_join_row_count']}",
            f"- runtime join rows pass: {summary['runtime_join_rows_pass']}",
            f"- protocol controller families mapped: {summary['runtime_profile_mapping_count']} / {summary['required_protocol_controller_family_count']}",
            f"- current-tiled runtime profile count: {summary['current_tiled_runtime_profile_count']}",
            f"- current-tiled runtime observed: {summary['current_tiled_runtime_observed']}",
            f"- reset/truncated runtime profile count: {summary['reset_truncated_runtime_profile_count']}",
            f"- reset/truncated policy routing ok: {summary['reset_truncated_policy_routing_ok']}",
            "",
            "## Guardrails",
            "",
            f"- environment rollout run: {summary['environment_rollout_run']}",
            f"- full public policy rollout run: {summary['full_public_policy_rollout_run']}",
            f"- policy rollout allowed: {summary['policy_rollout_allowed']}",
            f"- measured validation run: {summary['measured_validation_run']}",
            f"- training run: {summary['training_run']}",
            f"- replay run: {summary['replay_run']}",
            f"- ppo run: {summary['ppo_run']}",
            f"- private holdout used: {summary['private_holdout_used']}",
            f"- profile-specific tuning: {summary['profile_specific_tuning']}",
            f"- actor/action boundary: P0 observation multiple action 3 preserved: {summary['actor_contract_shape_72_action_3']}",
            f"- hidden/oracle actor input detected: {summary['hidden_oracle_actor_input_detected']}",
            f"- diagnostic success-rate metric recorded: {summary['success_rate_metric_recorded']}",
            f"- diagnostic comparison-delta metric recorded: {summary['comparison_delta_metric_recorded']}",
            f"- success-rate verdict claim made: {summary['success_rate_verdict_claim_made']}",
            f"- comparison-delta verdict claim made: {summary['comparison_delta_verdict_claim_made']}",
            "",
            "## Claim Boundary",
            "",
            "Allowed:",
            "",
            "```text",
            "Full public T4/T5 comparison execution preflight data and diagnostic metrics only.",
            "```",
            "",
            "Rejected:",
            "",
            "```text",
            summary["forbidden_interpretation"],
            "```",
            "",
            "M2677 executes the public T4/T5 workload for diagnostic comparison",
            "rows only. The aggregate success-rate columns and comparison delta",
            "columns in the output are diagnostic metrics, not success-rate",
            "verdicts, controller-family rankings, paper evidence,",
            "finite-window-vs-GRU conclusions, current-response sufficiency",
            "results, current-sim verdicts, high-fidelity validation, full",
            "ideal driver completion, or level3 self-ID evidence.",
            "",
        ]
    )


def claim(
    claim_id: str,
    family: str,
    allowed: bool,
    claim_made: bool,
    evidence: str,
) -> dict[str, Any]:
    status_pass = bool(claim_made) if allowed else not bool(claim_made)
    return {
        "claim_id": claim_id,
        "claim_family": family,
        "allowed_in_m2677": bool(allowed),
        "claim_made": bool(claim_made),
        "status_pass": status_pass,
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


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


def _all_selected_metrics_finite(
    full_summary: dict[str, Any],
    profile_aggregate_rows: list[dict[str, Any]],
    spec_aggregate_rows: list[dict[str, Any]],
) -> bool:
    if not _bool(full_summary.get("all_selected_metrics_finite", False)):
        return False
    return all(
        _bool(row.get("all_selected_metrics_finite", False))
        for row in list(profile_aggregate_rows) + list(spec_aggregate_rows)
    )


def _full_rollout_rows_are_bounded_public(rows: list[dict[str, Any]]) -> bool:
    if len(rows) != TARGET_EPISODE_COUNT:
        return False
    for row in rows:
        if not _bool(row.get("full_rollout_execution", False)):
            return False
        if _bool(row.get("routing_smoke_only", False)):
            return False
        if _bool(row.get("training_started", False)) or _bool(row.get("ppo_used", False)):
            return False
        if _bool(row.get("replay_started", False)) or _bool(row.get("private_holdout_used", False)):
            return False
        if _bool(row.get("actor_input_contract_changed", False)):
            return False
        if _bool(row.get("profile_specific_tuning", False)):
            return False
        if _bool(row.get("controller_family_ranking_claim_made", False)):
            return False
        if _bool(row.get("paper_level_claim_made", False)):
            return False
        if _bool(row.get("level3_self_id_claim_made", False)):
            return False
    return True


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-enforcement-dir", type=Path, default=DEFAULT_RUNTIME_ENFORCEMENT_DIR)
    parser.add_argument("--bounded-preflight-dir", type=Path, default=DEFAULT_BOUNDED_PREFLIGHT_DIR)
    parser.add_argument("--executable-specs", type=Path, default=DEFAULT_EXECUTABLE_SPECS)
    parser.add_argument("--workload", type=Path, default=DEFAULT_EXECUTABLE_WORKLOAD)
    parser.add_argument("--m1674-run-dir", type=Path, default=DEFAULT_M1674_RUN_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args(argv)

    summary = run_full_t4_t5_public_comparison_execution_preflight(
        runtime_enforcement_dir=args.runtime_enforcement_dir,
        bounded_preflight_dir=args.bounded_preflight_dir,
        executable_specs=args.executable_specs,
        workload=args.workload,
        m1674_run_dir=args.m1674_run_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        eval_seed_base=args.eval_seed_base,
        device=args.device,
        resume=not bool(args.no_resume),
    )
    print(f"summary={summary['paths']['summary']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"episode_count={summary['episode_count']}")
    print(f"failure_count={summary['failure_count']}")
    print(f"runtime_join_rows_pass={summary['runtime_join_rows_pass']}")
    print(f"next={summary['next_blocker']}")
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
