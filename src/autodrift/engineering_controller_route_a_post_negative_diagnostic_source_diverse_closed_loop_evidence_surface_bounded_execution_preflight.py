"""Run M2737 source-diverse bounded diagnostic execution preflight.

M2737 consumes the M2734 post-negative diagnostic source-diverse evidence
surface after M2736 design. It resolves the 18 admitted M2734 candidate rows to
current-M1690 executable rows, runs one bounded closed-loop diagnostic episode
per resolved candidate, and carries M2728 negative context plus protected/HF3
blockers as guardrails. It does not rank, validate, train, promote, or claim
driver performance.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.controller_family_full_rollout_execution import (
    DEFAULT_EXECUTABLE_SPECS,
    load_executable_specs,
    read_csv_rows,
    run_workload_cell,
    selected_metrics_are_finite,
    write_run_state,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2737-engineering-controller-route-a-post-negative-diagnostic-source-diverse-"
    "closed-loop-evidence-surface-bounded-execution-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2738-engineering-controller-route-a-post-negative-diagnostic-source-diverse-"
    "closed-loop-evidence-surface-bounded-execution-result-audit"
)
DEFAULT_M2734_DIR = Path(
    "runs/m2734_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface"
)
DEFAULT_M2736_DESIGN = Path(
    "docs/m2736-engineering-controller-route-a-post-negative-diagnostic-source-diverse-"
    "closed-loop-evidence-surface-bounded-execution-design.md"
)
DEFAULT_M2693_EXECUTION_ROWS = Path(
    "runs/m2693_engineering_controller_source_diverse_offtrack_protected_bounded_execution_preflight/"
    "target_execution_rows.csv"
)
DEFAULT_M2716_EXECUTION_ROWS = Path(
    "runs/m2716_engineering_controller_route_a_current_m1690_exact_executable_reentry_bounded_execution_preflight/"
    "exact_execution_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2737_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_bounded_execution_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2737-engineering-controller-route-a-post-negative-diagnostic-source-diverse-"
    "closed-loop-evidence-surface-bounded-execution-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2738-engineering-controller-route-a-post-negative-diagnostic-"
    "source-diverse-closed-loop-evidence-surface-bounded-execution-result-audit.json"
)
DEFAULT_EVAL_SEED_BASE = 273700
EXPECTED_CANDIDATE_COUNT = 18
EXPECTED_M2693_CANDIDATE_COUNT = 9
EXPECTED_M2716_CANDIDATE_COUNT = 9
EXPECTED_NEGATIVE_CONTEXT_COUNT = 31
EXPECTED_BLOCKED_SURFACE_COUNT = 12
CANONICAL_M2716_PROFILE = "L3_online_gru"

CLAIM_SCOPE = (
    "M2737 Route A post-negative diagnostic source-diverse bounded execution "
    "preflight only; reset, step, rollout, and policy actions may be recorded "
    "for resolved non-same-surface M2734 candidate rows, while M2728 negative "
    "context rows, protected blocker rows, and HF3 blocker rows remain "
    "guardrails outside execution and success denominators. No replay, "
    "validation, training, PPO, source build, adapter probe, external "
    "simulation, ranking, winner selection, promotion, success-rate verdict, "
    "repair-success, driver-performance, paper, finite-window-vs-GRU, "
    "current-sim, high-fidelity validation, full ideal driver, or self-ID "
    "claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, "
    "controller-family ranking, source-family ranking, profile ranking, "
    "winner selection, checkpoint promotion, success-rate verdict, paper "
    "evidence, finite-window-vs-GRU conclusion, current-sim verdict, "
    "high-fidelity validation readiness or result, full ideal driver "
    "completion, or level3 self-identification"
)

RESOLUTION_FIELDNAMES = [
    "resolution_id",
    "candidate_id",
    "source_milestone",
    "source_row_id",
    "source_family",
    "source_bucket",
    "task_family",
    "source_key",
    "source_execution_row_count",
    "materialization_admitted",
    "same_surface_m2728_repair",
    "protected_or_hf3_blocked",
    "hidden_oracle_actor_input_detected",
    "resolution_status",
    "resolved_execution_row_id",
    "workload_id",
    "task_source_id",
    "profile_name",
    "source_execution_seed",
    "profile_config_path",
    "checkpoint_path",
    "execution_admitted",
    "execution_planned",
    "failure_reason",
    "actor_contract_shape_72_action_3",
    "diagnostic_only_no_verdict",
    "ranking_run",
    "claim_boundary",
]
FAILURE_FIELDNAMES = [
    "resolution_id",
    "candidate_id",
    "source_milestone",
    "source_row_id",
    "source_family",
    "source_bucket",
    "task_family",
    "source_key",
    "workload_id",
    "task_source_id",
    "profile_name",
    "m2737_eval_seed",
    "error_type",
    "error_message",
    "environment_reset_run",
    "environment_step_run",
    "policy_action_run",
    "policy_rollout_run",
    "m2728_negative_context_execution",
    "same_surface_m2728_repair_execution",
    "protected_blocker_execution",
    "hf3_blocker_execution",
    "training_started",
    "replay_started",
    "ppo_used",
    "source_build_run",
    "adapter_probe_run",
    "external_simulation_run",
    "private_holdout_used",
    "profile_specific_tuning",
    "active_config_overwritten",
    "ranking_run",
    "winner_selected",
    "checkpoint_promoted",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "target_labels_actor_visible",
    "protected_labels_actor_visible",
    "blocker_labels_actor_visible",
    "route_labels_actor_visible",
    "verdict_labels_actor_visible",
    "protected_rows_in_success_denominator",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
SOURCE_AGGREGATE_FIELDNAMES = [
    "aggregate_id",
    "source_milestone",
    "source_family",
    "candidate_count",
    "episode_count",
    "failure_count",
    "accounted_count",
    "success_rate_diagnostic",
    "collision_rate_diagnostic",
    "offtrack_rate_diagnostic",
    "clearance_margin_mean",
    "return_mean",
    "all_selected_metrics_finite",
    "ranking_claim_made",
    "success_rate_verdict_claim_made",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
TASK_AGGREGATE_FIELDNAMES = [
    "aggregate_id",
    "task_family",
    "source_family_count",
    "candidate_count",
    "episode_count",
    "failure_count",
    "accounted_count",
    "success_rate_diagnostic",
    "collision_rate_diagnostic",
    "offtrack_rate_diagnostic",
    "clearance_margin_mean",
    "return_mean",
    "all_selected_metrics_finite",
    "ranking_claim_made",
    "success_rate_verdict_claim_made",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
NEGATIVE_GUARD_FIELDNAMES = [
    "guard_id",
    "context_id",
    "source_row_id",
    "candidate_row_id",
    "anchor_task_source_id",
    "profile_name",
    "task_family",
    "success",
    "collision",
    "termination_reason",
    "outcome_bucket",
    "execution_candidate",
    "execution_admitted",
    "execution_run",
    "direct_same_surface_repair_execution_admitted",
    "protected_rows_in_success_denominator",
    "actor_visible_allowed",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
BLOCKED_GUARD_FIELDNAMES = [
    "guard_id",
    "blocked_id",
    "blocked_family",
    "source_milestone",
    "source_row_id",
    "row_count",
    "blocking_count",
    "blocked_reason",
    "execution_candidate",
    "execution_admitted",
    "execution_run",
    "protected_rows_in_success_denominator",
    "actor_visible_allowed",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
ACTOR_GUARD_FIELDNAMES = [
    "guard_id",
    "guard_family",
    "observed",
    "expected",
    "status_pass",
    "actor_visible_allowed",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2737",
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
    "execution_candidate_resolution_rows",
    "candidate_execution_rows",
    "candidate_execution_failure_rows",
    "source_family_aggregate",
    "task_family_aggregate",
    "negative_context_guard_rows",
    "blocked_surface_guard_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
]


def run_post_negative_source_diverse_bounded_execution_preflight(
    *,
    m2734_dir: Path | str = DEFAULT_M2734_DIR,
    m2736_design: Path | str = DEFAULT_M2736_DESIGN,
    m2693_execution_rows: Path | str = DEFAULT_M2693_EXECUTION_ROWS,
    m2716_execution_rows: Path | str = DEFAULT_M2716_EXECUTION_ROWS,
    executable_specs: Path | str = DEFAULT_EXECUTABLE_SPECS,
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
        m2734_dir=Path(m2734_dir),
        m2736_design=Path(m2736_design),
        m2693_execution_rows=Path(m2693_execution_rows),
        m2716_execution_rows=Path(m2716_execution_rows),
        executable_specs=Path(executable_specs),
        follow_up_manifest=Path(follow_up_manifest),
    )
    resolution_rows, resolved_sources = build_resolution_rows(source)
    write_csv_rows(
        paths["execution_candidate_resolution_rows"],
        resolution_rows,
        fieldnames=RESOLUTION_FIELDNAMES,
    )

    execution_summary = run_candidate_execution(
        resolution_rows=resolution_rows,
        resolved_sources=resolved_sources,
        output_dir=output,
        executable_specs_path=Path(executable_specs),
        eval_seed_base=int(eval_seed_base),
        device=device,
        resume=resume,
        next_blocker=next_blocker,
    )
    artifact_rows = load_execution_artifact_rows(paths)
    negative_guard_rows = build_negative_context_guard_rows(source["negative_context_rows"])
    blocked_guard_rows = build_blocked_surface_guard_rows(source["blocked_surface_rows"])
    source_aggregate = build_source_family_aggregate_rows(
        resolution_rows=resolution_rows,
        episode_rows=artifact_rows["candidate_execution_rows"],
        failure_rows=artifact_rows["candidate_execution_failure_rows"],
    )
    task_aggregate = build_task_family_aggregate_rows(
        resolution_rows=resolution_rows,
        episode_rows=artifact_rows["candidate_execution_rows"],
        failure_rows=artifact_rows["candidate_execution_failure_rows"],
    )
    actor_guard_rows = build_actor_contract_guard_rows(
        resolution_rows=resolution_rows,
        episode_rows=artifact_rows["candidate_execution_rows"],
        failure_rows=artifact_rows["candidate_execution_failure_rows"],
        negative_guard_rows=negative_guard_rows,
        blocked_guard_rows=blocked_guard_rows,
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=False,
        episode_or_failure_rows_present=bool(
            artifact_rows["candidate_execution_rows"] or artifact_rows["candidate_execution_failure_rows"]
        ),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        execution_summary=execution_summary,
        artifact_rows=artifact_rows,
        resolution_rows=resolution_rows,
        source_aggregate=source_aggregate,
        task_aggregate=task_aggregate,
        negative_guard_rows=negative_guard_rows,
        blocked_guard_rows=blocked_guard_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        required_artifacts_present=False,
    )
    write_derived_outputs(paths, source_aggregate, task_aggregate, negative_guard_rows, blocked_guard_rows, actor_guard_rows, claim_rows, gate_rows)

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"})
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_artifacts_present,
        episode_or_failure_rows_present=bool(
            artifact_rows["candidate_execution_rows"] or artifact_rows["candidate_execution_failure_rows"]
        ),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        execution_summary=execution_summary,
        artifact_rows=load_execution_artifact_rows(paths),
        resolution_rows=resolution_rows,
        source_aggregate=source_aggregate,
        task_aggregate=task_aggregate,
        negative_guard_rows=negative_guard_rows,
        blocked_guard_rows=blocked_guard_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        execution_summary=execution_summary,
        artifact_rows=load_execution_artifact_rows(paths),
        resolution_rows=resolution_rows,
        source_aggregate=source_aggregate,
        task_aggregate=task_aggregate,
        negative_guard_rows=negative_guard_rows,
        blocked_guard_rows=blocked_guard_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
        eval_seed_base=int(eval_seed_base),
        device=device,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    gate_rows = build_gate_matrix_rows(
        source=source,
        execution_summary=execution_summary,
        artifact_rows=load_execution_artifact_rows(paths),
        resolution_rows=resolution_rows,
        source_aggregate=source_aggregate,
        task_aggregate=task_aggregate,
        negative_guard_rows=negative_guard_rows,
        blocked_guard_rows=blocked_guard_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        execution_summary=execution_summary,
        artifact_rows=load_execution_artifact_rows(paths),
        resolution_rows=resolution_rows,
        source_aggregate=source_aggregate,
        task_aggregate=task_aggregate,
        negative_guard_rows=negative_guard_rows,
        blocked_guard_rows=blocked_guard_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
        eval_seed_base=int(eval_seed_base),
        device=device,
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "execution_candidate_resolution_rows": output_dir / "execution_candidate_resolution_rows.csv",
        "candidate_execution_rows": output_dir / "candidate_execution_rows.csv",
        "candidate_execution_failure_rows": output_dir / "candidate_execution_failure_rows.csv",
        "source_family_aggregate": output_dir / "source_family_aggregate.csv",
        "task_family_aggregate": output_dir / "task_family_aggregate.csv",
        "negative_context_guard_rows": output_dir / "negative_context_guard_rows.csv",
        "blocked_surface_guard_rows": output_dir / "blocked_surface_guard_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2734_dir: Path,
    m2736_design: Path,
    m2693_execution_rows: Path,
    m2716_execution_rows: Path,
    executable_specs: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2736_design": m2736_design,
        "m2734_summary": m2734_dir / "summary.json",
        "candidate_rows": m2734_dir / "evidence_surface_candidate_rows.csv",
        "blocked_surface_rows": m2734_dir / "blocked_surface_rows.csv",
        "negative_context_rows": m2734_dir / "negative_diagnostic_context_rows.csv",
        "actor_contract_guard_rows": m2734_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": m2734_dir / "claim_boundary_rows.csv",
        "gate_matrix": m2734_dir / "gate_matrix.csv",
        "m2693_execution_rows": m2693_execution_rows,
        "m2716_execution_rows": m2716_execution_rows,
        "executable_task_specs": executable_specs,
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2736_design_text": paths["m2736_design"].read_text(encoding="utf-8")
        if source_exists["m2736_design"]
        else "",
        "m2734_summary": read_json(paths["m2734_summary"]) if source_exists["m2734_summary"] else {},
        "candidate_rows": read_csv_rows(paths["candidate_rows"]),
        "blocked_surface_rows": read_csv_rows(paths["blocked_surface_rows"]),
        "negative_context_rows": read_csv_rows(paths["negative_context_rows"]),
        "actor_contract_guard_rows": read_csv_rows(paths["actor_contract_guard_rows"]),
        "claim_boundary_rows": read_csv_rows(paths["claim_boundary_rows"]),
        "gate_matrix": read_csv_rows(paths["gate_matrix"]),
        "m2693_execution_rows": read_csv_rows(paths["m2693_execution_rows"]),
        "m2716_execution_rows": read_csv_rows(paths["m2716_execution_rows"]),
    }


def build_resolution_rows(source: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]]]:
    m2693_by_target_id = {
        str(row.get("target_id", "")): row for row in source["m2693_execution_rows"] if row.get("target_id")
    }
    m2716_by_task_source: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in source["m2716_execution_rows"]:
        if str(row.get("profile_name", "")) == CANONICAL_M2716_PROFILE:
            m2716_by_task_source[str(row.get("task_source_id", ""))].append(row)

    rows: list[dict[str, Any]] = []
    resolved_sources: dict[str, dict[str, str]] = {}
    for index, candidate in enumerate(sorted(source["candidate_rows"], key=lambda row: str(row.get("candidate_id", ""))), start=1):
        candidate_id = str(candidate.get("candidate_id", ""))
        source_milestone = str(candidate.get("source_milestone", ""))
        source_row_id = str(candidate.get("source_row_id", ""))
        source_row: dict[str, str] | None = None
        failure_reason = ""
        if not _bool(candidate.get("materialization_admitted", False)):
            failure_reason = "candidate_not_materialization_admitted"
        elif _bool(candidate.get("same_surface_m2728_repair", False)):
            failure_reason = "same_surface_m2728_repair_candidate_rejected"
        elif _bool(candidate.get("protected_or_hf3_blocked", False)):
            failure_reason = "protected_or_hf3_blocked_candidate_rejected"
        elif _bool(candidate.get("hidden_oracle_actor_input_detected", False)):
            failure_reason = "hidden_oracle_actor_input_required"
        elif source_milestone == "m2693":
            source_row = m2693_by_target_id.get(source_row_id)
            if not source_row:
                failure_reason = "m2693_target_execution_row_not_found"
        elif source_milestone == "m2716":
            matches = sorted(m2716_by_task_source.get(source_row_id, []), key=lambda row: str(row.get("workload_id", "")))
            if not matches:
                failure_reason = f"m2716_{CANONICAL_M2716_PROFILE}_execution_row_not_found"
            else:
                source_row = matches[0]
        else:
            failure_reason = f"unsupported_source_milestone_{source_milestone}"

        execution_admitted = source_row is not None and not failure_reason
        row = {
            "resolution_id": f"m2737-resolution-{index:04d}",
            "candidate_id": candidate_id,
            "source_milestone": source_milestone,
            "source_row_id": source_row_id,
            "source_family": candidate.get("source_family", ""),
            "source_bucket": candidate.get("source_bucket", ""),
            "task_family": candidate.get("task_family", ""),
            "source_key": candidate.get("source_key", ""),
            "source_execution_row_count": candidate.get("source_execution_row_count", ""),
            "materialization_admitted": _bool(candidate.get("materialization_admitted", False)),
            "same_surface_m2728_repair": _bool(candidate.get("same_surface_m2728_repair", False)),
            "protected_or_hf3_blocked": _bool(candidate.get("protected_or_hf3_blocked", False)),
            "hidden_oracle_actor_input_detected": _bool(candidate.get("hidden_oracle_actor_input_detected", False)),
            "resolution_status": "resolved_to_current_m1690_workload" if execution_admitted else "accounted_by_failure",
            "resolved_execution_row_id": _resolved_source_id(source_row) if source_row else "",
            "workload_id": source_row.get("workload_id", "") if source_row else "",
            "task_source_id": source_row.get("task_source_id", "") if source_row else "",
            "profile_name": source_row.get("profile_name", "") if source_row else "",
            "source_execution_seed": source_row.get("eval_seed", source_row.get("m2716_eval_seed", "")) if source_row else "",
            "profile_config_path": source_row.get("profile_config_path", "") if source_row else "",
            "checkpoint_path": source_row.get("checkpoint_path", "") if source_row else "",
            "execution_admitted": execution_admitted,
            "execution_planned": execution_admitted,
            "failure_reason": failure_reason,
            "actor_contract_shape_72_action_3": _bool(candidate.get("actor_contract_shape_72_action_3", False)),
            "diagnostic_only_no_verdict": _bool(candidate.get("diagnostic_only_no_verdict", False)),
            "ranking_run": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        rows.append(row)
        if source_row is not None:
            resolved_sources[str(row["resolution_id"])] = source_row
    return rows, resolved_sources


def run_candidate_execution(
    *,
    resolution_rows: list[dict[str, Any]],
    resolved_sources: dict[str, dict[str, str]],
    output_dir: Path,
    executable_specs_path: Path,
    eval_seed_base: int,
    device: str,
    resume: bool,
    next_blocker: str,
) -> dict[str, Any]:
    if not resume:
        for name in ("candidate_execution_rows.csv", "candidate_execution_failure_rows.csv", "run_state.json"):
            path = output_dir / name
            if path.exists():
                path.unlink()

    specs = load_executable_specs(executable_specs_path)
    spec_by_id = {str(spec["task_source_id"]): spec for spec in specs}
    profile_cache: dict[tuple[str, str, str], tuple[dict[str, Any], Any, dict[str, str]]] = {}
    episode_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []

    for index, resolution in enumerate(resolution_rows):
        eval_seed = int(eval_seed_base) + index
        resolution_id = str(resolution.get("resolution_id", ""))
        try:
            if not _bool(resolution.get("execution_admitted", False)):
                raise ValueError(str(resolution.get("failure_reason", "candidate resolution not admitted")))
            source_row = resolved_sources[resolution_id]
            task_source_id = str(source_row["task_source_id"])
            if task_source_id not in spec_by_id:
                raise KeyError(f"task_source_id {task_source_id} missing from executable specs")
            profile_name = str(source_row["profile_name"])
            config_path = str(source_row["profile_config_path"])
            checkpoint_path = str(source_row["checkpoint_path"])
            cache_key = (profile_name, config_path, checkpoint_path)
            if cache_key not in profile_cache:
                profile_config = read_json(config_path)
                model, _ = load_actor_critic_checkpoint(checkpoint_path, device=device)
                profile_cache[cache_key] = (
                    profile_config,
                    model,
                    {"profile_name": profile_name, "config_path": config_path, "checkpoint_path": checkpoint_path},
                )
            profile_config, model, profile_row = profile_cache[cache_key]
            row = run_workload_cell(
                workload_row=source_row,
                executable_spec=spec_by_id[task_source_id],
                profile_config=profile_config,
                model=model,
                profile_row=profile_row,
                eval_seed=eval_seed,
            )
            row.update(candidate_execution_metadata(resolution, eval_seed=eval_seed))
            episode_rows.append(row)
        except Exception as exc:  # noqa: BLE001 - every failed candidate must be accounted.
            failure_rows.append(
                failure_row(
                    resolution,
                    eval_seed=eval_seed,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                )
            )
        write_run_state(
            output_dir / "run_state.json",
            {
                "candidate_count": len(resolution_rows),
                "completed_execution_count": len(episode_rows),
                "failure_count": len(failure_rows),
                "accounted_count": len(episode_rows) + len(failure_rows),
                "latest_resolution_id": resolution_id,
                "complete": False,
                "next_blocker": next_blocker,
            },
        )

    write_csv_rows(output_dir / "candidate_execution_rows.csv", episode_rows)
    write_csv_rows(output_dir / "candidate_execution_failure_rows.csv", failure_rows, fieldnames=FAILURE_FIELDNAMES)
    all_metrics_finite = selected_metrics_are_finite(episode_rows) if episode_rows else False
    status_pass = bool(
        len(resolution_rows) == EXPECTED_CANDIDATE_COUNT
        and len(episode_rows) + len(failure_rows) == len(resolution_rows)
        and bool(episode_rows)
        and all_metrics_finite
        and not any(forbidden_execution_flag(row) for row in episode_rows + failure_rows)
    )
    summary = {
        "result_class": (
            "engineering_controller_route_a_post_negative_diagnostic_source_diverse_bounded_candidate_execution_pass"
            if status_pass
            else "engineering_controller_route_a_post_negative_diagnostic_source_diverse_bounded_candidate_execution_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "candidate_count": len(resolution_rows),
        "episode_count": len(episode_rows),
        "failure_count": len(failure_rows),
        "accounted_count": len(episode_rows) + len(failure_rows),
        "all_selected_metrics_finite": bool(all_metrics_finite),
        "environment_reset_run": bool(episode_rows),
        "environment_step_run": bool(episode_rows),
        "policy_action_run": bool(episode_rows),
        "policy_rollout_run": bool(episode_rows),
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "source_build_run": False,
        "adapter_probe_run": False,
        "external_simulation_run": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "active_config_overwritten": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "driver_performance_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "level3_self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "next_blocker": next_blocker,
    }
    write_json(output_dir / "candidate_execution_summary.json", summary)
    write_run_state(
        output_dir / "run_state.json",
        {
            "candidate_count": len(resolution_rows),
            "completed_execution_count": len(episode_rows),
            "failure_count": len(failure_rows),
            "accounted_count": len(episode_rows) + len(failure_rows),
            "complete": len(episode_rows) + len(failure_rows) == len(resolution_rows),
            "status_pass": status_pass,
            "next_blocker": next_blocker,
        },
    )
    return summary


def candidate_execution_metadata(resolution: Mapping[str, Any], *, eval_seed: int) -> dict[str, Any]:
    return {
        "m2737_eval_seed": int(eval_seed),
        "resolution_id": resolution.get("resolution_id", ""),
        "candidate_id": resolution.get("candidate_id", ""),
        "source_milestone": resolution.get("source_milestone", ""),
        "source_row_id": resolution.get("source_row_id", ""),
        "source_family": resolution.get("source_family", ""),
        "source_bucket": resolution.get("source_bucket", ""),
        "source_key": resolution.get("source_key", ""),
        "resolved_execution_row_id": resolution.get("resolved_execution_row_id", ""),
        "source_execution_seed": resolution.get("source_execution_seed", ""),
        "bounded_source_diverse_execution_preflight": True,
        "candidate_surface_count": EXPECTED_CANDIDATE_COUNT,
        "m2728_negative_context_execution": False,
        "same_surface_m2728_repair_execution": False,
        "protected_blocker_execution": False,
        "hf3_blocker_execution": False,
        "protected_rows_in_success_denominator": False,
        "target_labels_actor_visible": False,
        "protected_labels_actor_visible": False,
        "profile_labels_actor_visible": False,
        "blocker_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "hidden_oracle_actor_input_required": False,
        "diagnostic_only_no_verdict": True,
        "profile_specific_tuning": False,
        "active_config_overwritten": False,
        "ranking_run": False,
        "source_family_ranking_claim_made": False,
        "profile_ranking_claim_made": False,
        "task_family_ranking_claim_made": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_verdict_claim_made": False,
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
        "validation_readiness_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "level3_self_id_claim_made": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def failure_row(
    resolution: Mapping[str, Any],
    *,
    eval_seed: int,
    error_type: str,
    error_message: str,
) -> dict[str, Any]:
    row = {key: False for key in FAILURE_FIELDNAMES}
    row.update(
        {
            "resolution_id": resolution.get("resolution_id", ""),
            "candidate_id": resolution.get("candidate_id", ""),
            "source_milestone": resolution.get("source_milestone", ""),
            "source_row_id": resolution.get("source_row_id", ""),
            "source_family": resolution.get("source_family", ""),
            "source_bucket": resolution.get("source_bucket", ""),
            "task_family": resolution.get("task_family", ""),
            "source_key": resolution.get("source_key", ""),
            "workload_id": resolution.get("workload_id", ""),
            "task_source_id": resolution.get("task_source_id", ""),
            "profile_name": resolution.get("profile_name", ""),
            "m2737_eval_seed": int(eval_seed),
            "error_type": error_type,
            "error_message": error_message,
            "diagnostic_only_no_verdict": True,
            "claim_boundary": CLAIM_SCOPE,
        }
    )
    return row


def load_execution_artifact_rows(paths: dict[str, Path]) -> dict[str, list[dict[str, str]]]:
    return {
        "candidate_execution_rows": read_csv_rows(paths["candidate_execution_rows"]),
        "candidate_execution_failure_rows": read_csv_rows(paths["candidate_execution_failure_rows"]),
    }


def write_derived_outputs(
    paths: dict[str, Path],
    source_aggregate: list[dict[str, Any]],
    task_aggregate: list[dict[str, Any]],
    negative_guard_rows: list[dict[str, Any]],
    blocked_guard_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    write_csv_rows(paths["source_family_aggregate"], source_aggregate, fieldnames=SOURCE_AGGREGATE_FIELDNAMES)
    write_csv_rows(paths["task_family_aggregate"], task_aggregate, fieldnames=TASK_AGGREGATE_FIELDNAMES)
    write_csv_rows(paths["negative_context_guard_rows"], negative_guard_rows, fieldnames=NEGATIVE_GUARD_FIELDNAMES)
    write_csv_rows(paths["blocked_surface_guard_rows"], blocked_guard_rows, fieldnames=BLOCKED_GUARD_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_guard_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)


def build_source_family_aggregate_rows(
    *,
    resolution_rows: list[dict[str, Any]],
    episode_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in resolution_rows:
        groups[(str(row.get("source_milestone", "")), str(row.get("source_family", "")))].append(row)
    episodes_by_group = _group_rows(episode_rows, "source_milestone", "source_family")
    failures_by_group = _group_rows(failure_rows, "source_milestone", "source_family")
    rows = []
    for index, ((source_milestone, source_family), candidates) in enumerate(sorted(groups.items()), start=1):
        episodes = episodes_by_group.get((source_milestone, source_family), [])
        failures = failures_by_group.get((source_milestone, source_family), [])
        rows.append(
            {
                "aggregate_id": f"m2737-source-family-aggregate-{index:04d}",
                "source_milestone": source_milestone,
                "source_family": source_family,
                "candidate_count": len(candidates),
                "episode_count": len(episodes),
                "failure_count": len(failures),
                "accounted_count": len(episodes) + len(failures),
                "success_rate_diagnostic": mean_bool(episodes, "success"),
                "collision_rate_diagnostic": mean_bool(episodes, "collision"),
                "offtrack_rate_diagnostic": mean_eq(episodes, "termination_reason", "off_track"),
                "clearance_margin_mean": mean_float(episodes, "min_clearance_margin"),
                "return_mean": mean_float(episodes, "return"),
                "all_selected_metrics_finite": selected_metrics_are_finite(episodes) if episodes else "",
                "ranking_claim_made": False,
                "success_rate_verdict_claim_made": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_task_family_aggregate_rows(
    *,
    resolution_rows: list[dict[str, Any]],
    episode_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in resolution_rows:
        groups[str(row.get("task_family", ""))].append(row)
    episodes_by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    failures_by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in episode_rows:
        episodes_by_task[str(row.get("task_family", ""))].append(row)
    for row in failure_rows:
        failures_by_task[str(row.get("task_family", ""))].append(row)
    rows = []
    for index, (task_family, candidates) in enumerate(sorted(groups.items()), start=1):
        episodes = episodes_by_task.get(task_family, [])
        failures = failures_by_task.get(task_family, [])
        rows.append(
            {
                "aggregate_id": f"m2737-task-family-aggregate-{index:04d}",
                "task_family": task_family,
                "source_family_count": len({str(row.get("source_family", "")) for row in candidates}),
                "candidate_count": len(candidates),
                "episode_count": len(episodes),
                "failure_count": len(failures),
                "accounted_count": len(episodes) + len(failures),
                "success_rate_diagnostic": mean_bool(episodes, "success"),
                "collision_rate_diagnostic": mean_bool(episodes, "collision"),
                "offtrack_rate_diagnostic": mean_eq(episodes, "termination_reason", "off_track"),
                "clearance_margin_mean": mean_float(episodes, "min_clearance_margin"),
                "return_mean": mean_float(episodes, "return"),
                "all_selected_metrics_finite": selected_metrics_are_finite(episodes) if episodes else "",
                "ranking_claim_made": False,
                "success_rate_verdict_claim_made": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_negative_context_guard_rows(context_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "guard_id": f"m2737-negative-context-guard-{index:04d}",
            "context_id": row.get("context_id", ""),
            "source_row_id": row.get("source_row_id", ""),
            "candidate_row_id": row.get("candidate_row_id", ""),
            "anchor_task_source_id": row.get("anchor_task_source_id", ""),
            "profile_name": row.get("profile_name", ""),
            "task_family": row.get("task_family", ""),
            "success": _bool(row.get("success", False)),
            "collision": _bool(row.get("collision", False)),
            "termination_reason": row.get("termination_reason", ""),
            "outcome_bucket": row.get("outcome_bucket", ""),
            "execution_candidate": False,
            "execution_admitted": False,
            "execution_run": False,
            "direct_same_surface_repair_execution_admitted": False,
            "protected_rows_in_success_denominator": False,
            "actor_visible_allowed": False,
            "diagnostic_only_no_verdict": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, row in enumerate(context_rows, start=1)
    ]


def build_blocked_surface_guard_rows(blocked_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "guard_id": f"m2737-blocked-surface-guard-{index:04d}",
            "blocked_id": row.get("blocked_id", ""),
            "blocked_family": row.get("blocked_family", ""),
            "source_milestone": row.get("source_milestone", ""),
            "source_row_id": row.get("source_row_id", ""),
            "row_count": row.get("row_count", ""),
            "blocking_count": row.get("blocking_count", ""),
            "blocked_reason": row.get("blocked_reason", ""),
            "execution_candidate": False,
            "execution_admitted": False,
            "execution_run": False,
            "protected_rows_in_success_denominator": False,
            "actor_visible_allowed": False,
            "diagnostic_only_no_verdict": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, row in enumerate(blocked_rows, start=1)
    ]


def build_actor_contract_guard_rows(
    *,
    resolution_rows: list[dict[str, Any]],
    episode_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    negative_guard_rows: list[dict[str, Any]],
    blocked_guard_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    combined = resolution_rows + episode_rows + failure_rows + negative_guard_rows + blocked_guard_rows
    return [
        actor_guard("observation_shape", P0_OBSERVATION_DIM, 72),
        actor_guard("action_shape", ACTION_DIM, 3),
        actor_guard("deployed_action_mapping", "[steer, throttle, brake]", "[steer, throttle, brake]"),
        actor_guard("hidden_oracle_actor_input_detected", any(_bool(row.get("hidden_oracle_actor_input_required", row.get("hidden_oracle_actor_input_detected", False))) for row in combined), False),
        actor_guard("actor_input_contract_changed", any(_bool(row.get("actor_input_contract_changed", False)) for row in combined), False),
        actor_guard("target_labels_actor_visible", any(_bool(row.get("target_labels_actor_visible", False)) for row in combined), False),
        actor_guard("protected_labels_actor_visible", any(_bool(row.get("protected_labels_actor_visible", False)) for row in combined), False),
        actor_guard("blocker_labels_actor_visible", any(_bool(row.get("blocker_labels_actor_visible", False)) for row in combined), False),
        actor_guard("route_labels_actor_visible", any(_bool(row.get("route_labels_actor_visible", False)) for row in combined), False),
        actor_guard("verdict_labels_actor_visible", any(_bool(row.get("verdict_labels_actor_visible", False)) for row in combined), False),
        actor_guard("protected_rows_in_success_denominator", any(_bool(row.get("protected_rows_in_success_denominator", False)) for row in combined), False),
        actor_guard("same_surface_m2728_repair_execution", any(_bool(row.get("same_surface_m2728_repair_execution", False)) for row in combined), False),
        actor_guard("active_config_overwritten", any(_bool(row.get("active_config_overwritten", False)) for row in combined), False),
    ]


def actor_guard(field: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": f"m2737-actor-guard-{field}",
        "guard_family": field,
        "observed": observed,
        "expected": expected,
        "status_pass": str(observed) == str(expected),
        "actor_visible_allowed": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_claim_boundary_rows(
    *,
    follow_up_manifest_registered: bool,
    artifacts_present: bool,
    episode_or_failure_rows_present: bool,
) -> list[dict[str, Any]]:
    allowed = [
        ("bounded_execution_preflight", "execution", episode_or_failure_rows_present, "M2737 execution/failure rows"),
        ("candidate_resolution_materialized", "artifact", artifacts_present, "execution_candidate_resolution_rows.csv"),
        ("candidate_execution_rows_materialized", "artifact", artifacts_present, "candidate_execution_rows.csv"),
        ("candidate_failure_rows_materialized", "artifact", artifacts_present, "candidate_execution_failure_rows.csv"),
        ("source_family_aggregate_materialized", "artifact", artifacts_present, "source_family_aggregate.csv"),
        ("task_family_aggregate_materialized", "artifact", artifacts_present, "task_family_aggregate.csv"),
        ("negative_context_guard_materialized", "artifact", artifacts_present, "negative_context_guard_rows.csv"),
        ("blocked_surface_guard_materialized", "artifact", artifacts_present, "blocked_surface_guard_rows.csv"),
        ("actor_guard_materialized", "artifact", artifacts_present, "actor_contract_guard_rows.csv"),
        ("claim_boundary_materialized", "artifact", artifacts_present, "claim_boundary_rows.csv"),
        ("gate_matrix_materialized", "artifact", artifacts_present, "gate_matrix.csv"),
        ("run_state_materialized", "artifact", artifacts_present, "run_state.json"),
        ("diagnostic_metrics_recorded", "diagnostic_metric", episode_or_failure_rows_present, "diagnostic aggregates only"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2738 result-audit manifest"),
    ]
    blocked = [
        ("m2728_same_surface_repair_execution", "execution", "explicitly blocked by M2736"),
        ("m2728_negative_context_execution", "execution", "guardrail only"),
        ("protected_blocker_execution", "execution", "guardrail only"),
        ("hf3_blocker_execution", "execution", "source dependency unresolved"),
        ("replay_validation_training_ppo", "execution", "future manifest"),
        ("source_build_adapter_external_sim", "execution", "future dependency route"),
        ("controller_or_source_family_ranking", "ranking", "future audited comparison route"),
        ("profile_or_task_family_ranking", "ranking", "future audited comparison route"),
        ("winner_selection", "promotion", "future promotion gate"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("success_rate_verdict", "verdict", "future result audit and verdict milestone"),
        ("repair_success", "verdict", "future repair audit and validation route"),
        ("driver_performance", "driver_performance", "future proof/generalization/claim audit"),
        ("validation_readiness", "validation", "future validation-readiness route"),
        ("validation_result", "validation", "future validation route"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("finite_window_vs_gru_result", "paper", "future fair comparison audit"),
        ("current_sim_verdict", "paper", "future current-sim synthesis"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("full_ideal_driver_completion", "full_goal", "future full ideal driver gate"),
    ]
    rows: list[dict[str, Any]] = []
    for claim_id, family, made, evidence in allowed:
        rows.append(claim(claim_id, family, True, made, evidence))
    rows.extend(claim(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def claim(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m2737_{claim_id}",
        "claim_family": family,
        "allowed_in_m2737": allowed,
        "claim_made": made,
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    execution_summary: dict[str, Any],
    artifact_rows: dict[str, list[dict[str, Any]]],
    resolution_rows: list[dict[str, Any]],
    source_aggregate: list[dict[str, Any]],
    task_aggregate: list[dict[str, Any]],
    negative_guard_rows: list[dict[str, Any]],
    blocked_guard_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    episode_rows = artifact_rows["candidate_execution_rows"]
    failure_rows = artifact_rows["candidate_execution_failure_rows"]
    source_counts = Counter(str(row.get("source_milestone", "")) for row in resolution_rows)
    resolved_count = sum(_bool(row.get("execution_admitted", False)) for row in resolution_rows)
    accounted_count = len({str(row.get("candidate_id", "")) for row in episode_rows + failure_rows if row.get("candidate_id")})
    allowed_claims = [row for row in claim_rows if _bool(row["allowed_in_m2737"])]
    blocked_claims = [row for row in claim_rows if not _bool(row["allowed_in_m2737"])]
    gates = [
        ("source_artifacts_present", "lineage", all(source["source_exists"].values()), source["source_exists"], "all M2734/M2736/M2693/M2716/spec/follow-up artifacts present", "lineage_invalid"),
        ("m2736_admits_m2737", "lineage", DEFAULT_MILESTONE in source["m2736_design_text"], "M2737 milestone in design doc", "M2737 milestone in design doc", "lineage_invalid"),
        ("m2734_status_pass", "lineage", _bool(source["m2734_summary"].get("status_pass", False)), source["m2734_summary"].get("status_pass"), True, "lineage_invalid"),
        ("candidate_surface_count", "candidate_resolution", len(resolution_rows) == EXPECTED_CANDIDATE_COUNT, len(resolution_rows), EXPECTED_CANDIDATE_COUNT, "metric_artifact"),
        ("candidate_source_split", "candidate_resolution", source_counts.get("m2693", 0) == EXPECTED_M2693_CANDIDATE_COUNT and source_counts.get("m2716", 0) == EXPECTED_M2716_CANDIDATE_COUNT, dict(source_counts), f"m2693={EXPECTED_M2693_CANDIDATE_COUNT} m2716={EXPECTED_M2716_CANDIDATE_COUNT}", "metric_artifact"),
        ("all_candidates_resolved", "candidate_resolution", resolved_count == len(resolution_rows), resolved_count, len(resolution_rows), "lineage_invalid"),
        ("resolution_excludes_same_surface_and_blockers", "contract", not any(_bool(row.get("same_surface_m2728_repair", False)) or _bool(row.get("protected_or_hf3_blocked", False)) for row in resolution_rows), "all false", "all false", "contract_violation"),
        ("execution_accounts_all_candidates", "execution", accounted_count == len(resolution_rows), accounted_count, len(resolution_rows), "scenario_sampling_failure"),
        ("execution_rows_present", "execution", bool(episode_rows), len(episode_rows), ">0", "scenario_sampling_failure"),
        ("all_selected_metrics_finite", "metric", selected_metrics_are_finite(episode_rows) if episode_rows else False, execution_summary.get("all_selected_metrics_finite"), True, "metric_artifact"),
        ("source_family_aggregate_shape", "artifact", len(source_aggregate) == 2, len(source_aggregate), 2, "metric_artifact"),
        ("task_family_aggregate_shape", "artifact", bool(task_aggregate), len(task_aggregate), ">0", "metric_artifact"),
        ("negative_context_guard_count", "guardrail", len(negative_guard_rows) == EXPECTED_NEGATIVE_CONTEXT_COUNT, len(negative_guard_rows), EXPECTED_NEGATIVE_CONTEXT_COUNT, "metric_artifact"),
        ("blocked_surface_guard_count", "guardrail", len(blocked_guard_rows) == EXPECTED_BLOCKED_SURFACE_COUNT, len(blocked_guard_rows), EXPECTED_BLOCKED_SURFACE_COUNT, "metric_artifact"),
        ("negative_and_blocked_not_executed", "contract", not any(_bool(row.get("execution_run", False)) or _bool(row.get("execution_admitted", False)) for row in negative_guard_rows + blocked_guard_rows), "all guard rows not executed", "all false", "contract_violation"),
        ("protected_not_success_denominator", "contract", not any(_bool(row.get("protected_rows_in_success_denominator", False)) for row in episode_rows + failure_rows + negative_guard_rows + blocked_guard_rows), "protected rows outside denominator", "all false", "proof_washout"),
        ("actor_contract_preserved", "contract", all(_bool(row.get("status_pass", False)) for row in actor_guard_rows), f"rows={len(actor_guard_rows)} pass={sum(_bool(row.get('status_pass', False)) for row in actor_guard_rows)}", "all actor guards pass", "contract_violation"),
        ("no_hidden_oracle_actor_input", "contract", not any(_bool(row.get("hidden_oracle_actor_input_required", False)) for row in episode_rows + failure_rows), "hidden/oracle false", "all false", "contract_violation"),
        ("no_forbidden_execution", "execution_guardrail", not any(forbidden_execution_flag(row) for row in episode_rows + failure_rows), "no train/replay/PPO/ranking/promotion/overclaim flags", "all false", "objective_overfit"),
        ("claim_boundary_blocks_overclaim", "claim_boundary", all(_bool(row["status_pass"]) for row in allowed_claims) and all(not _bool(row["claim_made"]) and _bool(row["status_pass"]) for row in blocked_claims), f"allowed={len(allowed_claims)} blocked={len(blocked_claims)}", "allowed pass and blocked not made", "proof_washout"),
        ("required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
    ]
    return [gate(gate_id, family, status_pass, observed, expected, failure_type) for gate_id, family, status_pass, observed, expected, failure_type in gates]


def gate(
    gate_id: str,
    family: str,
    status_pass: bool,
    observed: Any,
    expected: Any,
    failure_type: str,
) -> dict[str, Any]:
    return {
        "gate_id": f"m2737_{gate_id}",
        "gate_family": family,
        "status_pass": bool(status_pass),
        "observed": observed,
        "expected": expected,
        "failure_type": "" if status_pass else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    execution_summary: dict[str, Any],
    artifact_rows: dict[str, list[dict[str, Any]]],
    resolution_rows: list[dict[str, Any]],
    source_aggregate: list[dict[str, Any]],
    task_aggregate: list[dict[str, Any]],
    negative_guard_rows: list[dict[str, Any]],
    blocked_guard_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
    eval_seed_base: int,
    device: str,
) -> dict[str, Any]:
    episode_rows = artifact_rows["candidate_execution_rows"]
    failure_rows = artifact_rows["candidate_execution_failure_rows"]
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gate_rows)
    source_counts = Counter(str(row.get("source_milestone", "")) for row in resolution_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_bounded_execution_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_bounded_execution_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "eval_seed_base": int(eval_seed_base),
        "device": device,
        "source_artifacts_present": all(source["source_exists"].values()),
        "m2734_status_pass": _bool(source["m2734_summary"].get("status_pass", False)),
        "candidate_count": len(resolution_rows),
        "expected_candidate_count": EXPECTED_CANDIDATE_COUNT,
        "m2693_candidate_count": int(source_counts.get("m2693", 0)),
        "m2716_candidate_count": int(source_counts.get("m2716", 0)),
        "resolved_candidate_count": sum(_bool(row.get("execution_admitted", False)) for row in resolution_rows),
        "candidate_execution_row_count": len(episode_rows),
        "candidate_execution_failure_row_count": len(failure_rows),
        "accounted_candidate_count": len({str(row.get("candidate_id", "")) for row in episode_rows + failure_rows if row.get("candidate_id")}),
        "source_family_aggregate_row_count": len(source_aggregate),
        "task_family_aggregate_row_count": len(task_aggregate),
        "negative_context_guard_row_count": len(negative_guard_rows),
        "blocked_surface_guard_row_count": len(blocked_guard_rows),
        "actor_contract_guard_row_count": len(actor_guard_rows),
        "actor_contract_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in actor_guard_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "execution_summary_result_class": execution_summary.get("result_class", ""),
        "all_selected_metrics_finite": selected_metrics_are_finite(episode_rows) if episode_rows else False,
        "environment_reset_run": bool(episode_rows),
        "environment_step_run": bool(episode_rows),
        "policy_action_run": bool(episode_rows),
        "policy_rollout_run": bool(episode_rows),
        "bounded_source_diverse_execution_preflight": bool(episode_rows),
        "m2728_negative_context_execution": False,
        "same_surface_m2728_repair_execution": False,
        "protected_blocker_execution": False,
        "hf3_blocker_execution": False,
        "measured_validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "source_build_run": False,
        "adapter_probe_run": False,
        "external_simulation_run": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "active_config_overwritten": False,
        "actor_input_contract_changed": False,
        "actor_contract_shape_72_action_3": True,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": any(_bool(row.get("hidden_oracle_actor_input_required", False)) for row in episode_rows + failure_rows),
        "target_labels_actor_visible": any(_bool(row.get("target_labels_actor_visible", False)) for row in episode_rows + failure_rows),
        "protected_labels_actor_visible": any(_bool(row.get("protected_labels_actor_visible", False)) for row in episode_rows + failure_rows),
        "blocker_labels_actor_visible": any(_bool(row.get("blocker_labels_actor_visible", False)) for row in episode_rows + failure_rows),
        "route_labels_actor_visible": any(_bool(row.get("route_labels_actor_visible", False)) for row in episode_rows + failure_rows),
        "verdict_labels_actor_visible": any(_bool(row.get("verdict_labels_actor_visible", False)) for row in episode_rows + failure_rows),
        "protected_rows_in_success_denominator": any(_bool(row.get("protected_rows_in_success_denominator", False)) for row in episode_rows + failure_rows),
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_metric_recorded": bool(episode_rows),
        "success_rate_verdict_claim_made": False,
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
        "validation_readiness_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_simulation_run": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(path) for key, path in paths.items()},
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2737 Engineering Controller Route A Post-Negative Diagnostic Source-Diverse Closed-Loop Evidence Surface Bounded Execution Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- candidate rows: {summary['candidate_count']}",
            f"- resolved candidates: {summary['resolved_candidate_count']}/{summary['candidate_count']}",
            f"- execution rows: {summary['candidate_execution_row_count']}",
            f"- failure rows: {summary['candidate_execution_failure_row_count']}",
            f"- accounted candidates: {summary['accounted_candidate_count']}/{summary['candidate_count']}",
            f"- M2693 candidates: {summary['m2693_candidate_count']}",
            f"- M2716 candidates: {summary['m2716_candidate_count']}",
            f"- negative-context guard rows: {summary['negative_context_guard_row_count']}",
            f"- blocked-surface guard rows: {summary['blocked_surface_guard_row_count']}",
            f"- source-family aggregate rows: {summary['source_family_aggregate_row_count']}",
            f"- task-family aggregate rows: {summary['task_family_aggregate_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M2737 records bounded closed-loop diagnostic data only for resolved non-same-surface M2734 candidate rows. M2728 negative context, protected blocker, and HF3 blocker rows are guardrails only and remain outside execution and success denominators.",
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


def _group_rows(rows: list[dict[str, Any]], first_key: str, second_key: str) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row.get(first_key, "")), str(row.get(second_key, "")))].append(row)
    return grouped


def _resolved_source_id(source_row: Mapping[str, Any] | None) -> str:
    if not source_row:
        return ""
    for key in ("target_id", "candidate_id", "workload_id"):
        if source_row.get(key):
            return str(source_row[key])
    return str(source_row.get("task_source_id", ""))


def _float_values(rows: list[Mapping[str, Any]], key: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        try:
            value = float(row.get(key, "nan"))
        except (TypeError, ValueError):
            value = float("nan")
        if value == value and value not in (float("inf"), float("-inf")):
            values.append(value)
    return values


def mean_float(rows: list[Mapping[str, Any]], key: str) -> float | str:
    values = _float_values(rows, key)
    return sum(values) / len(values) if values else ""


def mean_bool(rows: list[Mapping[str, Any]], key: str) -> float | str:
    return sum(1 for row in rows if _bool(row.get(key, False))) / len(rows) if rows else ""


def mean_eq(rows: list[Mapping[str, Any]], key: str, expected: str) -> float | str:
    return sum(1 for row in rows if str(row.get(key, "")) == expected) / len(rows) if rows else ""


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def forbidden_execution_flag(row: Mapping[str, Any]) -> bool:
    forbidden_keys = (
        "m2728_negative_context_execution",
        "same_surface_m2728_repair_execution",
        "protected_blocker_execution",
        "hf3_blocker_execution",
        "training_started",
        "training_run",
        "replay_started",
        "replay_run",
        "ppo_used",
        "ppo_run",
        "source_build_run",
        "adapter_probe_run",
        "external_simulation_run",
        "private_holdout_used",
        "profile_specific_tuning",
        "active_config_overwritten",
        "actor_input_contract_changed",
        "ranking_run",
        "winner_selected",
        "checkpoint_promoted",
        "success_rate_verdict_claim_made",
        "driver_performance_claim_made",
        "repair_success_claim_made",
        "validation_readiness_claim_made",
        "validation_result_claim_made",
        "paper_claim_made",
        "finite_window_vs_gru_claim_made",
        "current_sim_verdict_claim_made",
        "high_fidelity_validation_claim_made",
        "full_ideal_driver_gate_passed",
        "full_ideal_driver_completion_claim_made",
        "level3_self_id_claim_made",
    )
    return any(_bool(row.get(key, False)) for key in forbidden_keys)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2734-dir", type=Path, default=DEFAULT_M2734_DIR)
    parser.add_argument("--m2736-design", type=Path, default=DEFAULT_M2736_DESIGN)
    parser.add_argument("--m2693-execution-rows", type=Path, default=DEFAULT_M2693_EXECUTION_ROWS)
    parser.add_argument("--m2716-execution-rows", type=Path, default=DEFAULT_M2716_EXECUTION_ROWS)
    parser.add_argument("--executable-specs", type=Path, default=DEFAULT_EXECUTABLE_SPECS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--no-resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_post_negative_source_diverse_bounded_execution_preflight(
        m2734_dir=args.m2734_dir,
        m2736_design=args.m2736_design,
        m2693_execution_rows=args.m2693_execution_rows,
        m2716_execution_rows=args.m2716_execution_rows,
        executable_specs=args.executable_specs,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        eval_seed_base=args.eval_seed_base,
        device=args.device,
        resume=not args.no_resume,
    )
    print(
        "status_pass={status} candidates={candidates} execution_rows={episodes} "
        "failures={failures} next={next_blocker}".format(
            status=summary["status_pass"],
            candidates=summary["candidate_count"],
            episodes=summary["candidate_execution_row_count"],
            failures=summary["candidate_execution_failure_row_count"],
            next_blocker=summary["next_blocker"],
        )
    )


if __name__ == "__main__":
    main()
