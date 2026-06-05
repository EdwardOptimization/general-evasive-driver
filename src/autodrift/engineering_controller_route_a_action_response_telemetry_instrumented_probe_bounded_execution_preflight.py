"""M2764 bounded instrumented action-response telemetry probe execution."""

from __future__ import annotations

import argparse
import math
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from autodrift import (
    engineering_controller_route_a_post_cross_axis_negative_action_response_containment_probe_bounded_execution_preflight
    as m2759,
)
from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.controller_family_full_rollout_execution import (
    DEFAULT_EXECUTABLE_SPECS,
    DEFAULT_EXECUTABLE_WORKLOAD,
    load_executable_specs,
    read_csv_rows,
    run_workload_cell,
    selected_metrics_are_finite,
    write_run_state,
)


DEFAULT_MILESTONE = (
    "m2764-engineering-controller-route-a-action-response-telemetry-instrumented-probe-bounded-execution-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2765-engineering-controller-route-a-action-response-telemetry-instrumented-probe-bounded-execution-result-audit"
)
DEFAULT_M2762_DIR = Path(
    "runs/m2762_engineering_controller_route_a_action_response_telemetry_coverage_instrumentation_repair_preflight"
)
DEFAULT_M2763_AUDIT = Path(
    "docs/m2763-engineering-controller-route-a-action-response-telemetry-coverage-instrumentation-repair-result-audit.md"
)
DEFAULT_M2756_DIR = Path("runs/m2756_engineering_controller_route_a_post_cross_axis_negative_failure_localization_panel")
DEFAULT_M2758_DESIGN = Path(
    "docs/m2758-engineering-controller-route-a-post-cross-axis-negative-action-response-containment-probe-design.md"
)
DEFAULT_M2753_DIR = Path("runs/m2753_engineering_controller_route_a_cross_axis_stress_generalization_bounded_execution_preflight")
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2764_engineering_controller_route_a_action_response_telemetry_instrumented_probe_bounded_execution_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2764-engineering-controller-route-a-action-response-telemetry-instrumented-probe-bounded-execution-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2765-engineering-controller-route-a-action-response-telemetry-instrumented-probe-bounded-execution-result-audit.json"
)
DEFAULT_EVAL_SEED_BASE = 276400

EXPECTED_CANDIDATE_COUNT = 12
EXPECTED_COLLISION_NEGATIVE_CLEARANCE_COUNT = 3
EXPECTED_OFFTRACK_POSITIVE_CLEARANCE_COUNT = 9
EXPECTED_GUARDRAIL_COUNT = 31
CANONICAL_PROFILE = "L3_online_gru"

CLAIM_SCOPE = (
    "M2764 Route A action-response telemetry instrumented probe bounded execution only; reset, step, "
    "policy action, and rollout are allowed only for the 12 M2756 localized probe rows while evaluator-only "
    "previous-command and trace-delta telemetry remains actor-invisible and no replay, validation, training, "
    "PPO, source build, adapter probe, external simulation, ranking, winner selection, promotion, success-rate "
    "verdict, repair-success, driver-performance, paper, finite-window-vs-GRU, current-sim, high-fidelity "
    "validation, full ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, controller-family ranking, source-edge "
    "ranking, stress-axis ranking, task-family ranking, profile ranking, winner selection, checkpoint promotion, "
    "success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity "
    "validation readiness or result, full ideal driver completion, or level3 self-identification"
)
FALSE_CLAIM_FLAGS = {
    "replay_run": False,
    "validation_run": False,
    "training_run": False,
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
    "success_rate_verdict_claim_made": False,
    "repair_success_claim_made": False,
    "driver_performance_claim_made": False,
    "validation_readiness_claim_made": False,
    "validation_result_claim_made": False,
    "paper_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
    "full_ideal_driver_gate_passed": False,
    "level3_self_id_claim_made": False,
}

RESOLUTION_FIELDNAMES = m2759.RESOLUTION_FIELDNAMES
CONTAINMENT_FIELDNAMES = m2759.CONTAINMENT_FIELDNAMES
MECHANISM_FIELDNAMES = m2759.MECHANISM_FIELDNAMES
ACTOR_GUARD_FIELDNAMES = m2759.ACTOR_GUARD_FIELDNAMES
GATE_FIELDNAMES = m2759.GATE_FIELDNAMES

FAILURE_FIELDNAMES = [
    "probe_resolution_id",
    "localization_id",
    "candidate_id",
    "source_resolution_id",
    "task_source_id",
    "workload_id",
    "profile_name",
    "task_family",
    "source_edge",
    "failure_family",
    "m2764_eval_seed",
    "error_type",
    "error_message",
    "environment_reset_run",
    "environment_step_run",
    "policy_action_run",
    "policy_rollout_run",
    "guardrail_execution",
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
    "action_response_labels_actor_visible",
    "containment_labels_actor_visible",
    "mechanism_tags_actor_visible",
    "stress_axis_labels_actor_visible",
    "source_edge_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "protected_rows_in_success_denominator",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
ACTION_RESPONSE_FIELDNAMES = [
    "probe_id",
    "probe_resolution_id",
    "candidate_id",
    "localization_id",
    "task_source_id",
    "failure_family",
    "previous_command",
    "previous_command_source",
    "current_action",
    "current_action_source",
    "actuator_lag_proxy",
    "actuator_error_proxy",
    "action_rate_mean",
    "action_rate_peak",
    "trace_delta_proxy",
    "trace_delta_source",
    "command_response_phase_lag_proxy",
    "speed_response_proxy",
    "yaw_response_proxy",
    "beta_response_proxy",
    "plan_first_action_error_proxy",
    "plan_first_action_error_source",
    "finite_metric",
    "m2762_contract_satisfied",
    "action_response_labels_actor_visible",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
TELEMETRY_COVERAGE_FIELDNAMES = [
    "telemetry_coverage_id",
    "probe_id",
    "probe_resolution_id",
    "candidate_id",
    "localization_id",
    "task_source_id",
    "failure_family",
    "m2759_incoming_finite_metric",
    "m2762_gap_class",
    "previous_command_finite",
    "previous_command_source",
    "current_action_finite",
    "plan_first_or_trace_delta_finite",
    "plan_first_or_trace_delta_source",
    "response_proxy_finite",
    "m2764_finite_metric",
    "finite_metric_improved_from_m2759",
    "m2759_row_backfilled",
    "actor_visible_allowed",
    "hidden_oracle_actor_input_required",
    "actor_input_contract_changed",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
GUARDRAIL_FIELDNAMES = [
    "m2764_guardrail_id",
    "guardrail_context_id",
    "guardrail_source",
    "guardrail_source_id",
    "task_source_id",
    "blocker_id",
    "route",
    "evidence_family",
    "row_count",
    "blocking_count",
    "execution_candidate",
    "execution_admitted",
    "execution_run",
    "ordinary_success_denominator_allowed",
    "protected_rows_in_success_denominator",
    "actor_visible_allowed",
    "diagnostic_only_no_verdict",
    "guardrail_role",
    "claim_scope",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2764",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
REQUIRED_ARTIFACT_KEYS = [
    "summary",
    "probe_candidate_resolution_rows",
    "probe_execution_rows",
    "probe_execution_failure_rows",
    "action_response_probe_rows",
    "telemetry_coverage_rows",
    "containment_probe_rows",
    "mechanism_context_rows",
    "guardrail_context_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
    "follow_up_manifest",
]


def run(
    *,
    m2762_dir: Path | str = DEFAULT_M2762_DIR,
    m2763_audit: Path | str = DEFAULT_M2763_AUDIT,
    m2756_dir: Path | str = DEFAULT_M2756_DIR,
    m2758_design: Path | str = DEFAULT_M2758_DESIGN,
    m2753_dir: Path | str = DEFAULT_M2753_DIR,
    m1690_workload: Path | str = DEFAULT_EXECUTABLE_WORKLOAD,
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
    follow_up_path = Path(follow_up_manifest)
    write_follow_up_manifest(follow_up_path)
    paths = artifact_paths(output, doc_path=Path(doc_path), follow_up_manifest=follow_up_path)
    source = load_source_artifacts(
        m2762_dir=Path(m2762_dir),
        m2763_audit=Path(m2763_audit),
        m2756_dir=Path(m2756_dir),
        m2758_design=Path(m2758_design),
        m2753_dir=Path(m2753_dir),
        m1690_workload=Path(m1690_workload),
        executable_specs=Path(executable_specs),
        follow_up_manifest=follow_up_path,
    )
    resolution_rows, resolved_sources = build_probe_candidate_resolution_rows(source)
    write_csv_rows(paths["probe_candidate_resolution_rows"], resolution_rows, fieldnames=RESOLUTION_FIELDNAMES)

    execution_summary = run_probe_execution(
        resolution_rows=resolution_rows,
        resolved_sources=resolved_sources,
        output_dir=output,
        executable_specs_path=Path(executable_specs),
        eval_seed_base=int(eval_seed_base),
        device=device,
        resume=resume,
        next_blocker=next_blocker,
    )
    artifact_rows = load_artifact_rows(paths)
    action_rows = build_action_response_probe_rows(artifact_rows["probe_execution_rows"])
    telemetry_rows = build_telemetry_coverage_rows(source, action_rows)
    containment_rows = build_containment_probe_rows(artifact_rows["probe_execution_rows"])
    mechanism_rows = build_mechanism_context_rows(resolution_rows, artifact_rows["probe_execution_rows"])
    guardrail_rows = build_guardrail_context_rows(source["guardrail_rows"])
    actor_guard_rows = build_actor_contract_guard_rows(source, resolution_rows, artifact_rows, guardrail_rows, telemetry_rows)
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=False,
        all_action_telemetry_finite=all_action_telemetry_finite(action_rows),
        telemetry_improved_count=count_improved_telemetry(telemetry_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        resolution_rows=resolution_rows,
        execution_summary=execution_summary,
        artifact_rows=artifact_rows,
        action_rows=action_rows,
        telemetry_rows=telemetry_rows,
        containment_rows=containment_rows,
        mechanism_rows=mechanism_rows,
        guardrail_rows=guardrail_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        required_artifacts_present=False,
    )
    write_derived_outputs(paths, action_rows, telemetry_rows, containment_rows, mechanism_rows, guardrail_rows, actor_guard_rows, claim_rows, gate_rows)

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"})
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_artifacts_present,
        all_action_telemetry_finite=all_action_telemetry_finite(action_rows),
        telemetry_improved_count=count_improved_telemetry(telemetry_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        resolution_rows=resolution_rows,
        execution_summary=execution_summary,
        artifact_rows=load_artifact_rows(paths),
        action_rows=action_rows,
        telemetry_rows=telemetry_rows,
        containment_rows=containment_rows,
        mechanism_rows=mechanism_rows,
        guardrail_rows=guardrail_rows,
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
        resolution_rows=resolution_rows,
        execution_summary=execution_summary,
        artifact_rows=load_artifact_rows(paths),
        action_rows=action_rows,
        telemetry_rows=telemetry_rows,
        containment_rows=containment_rows,
        mechanism_rows=mechanism_rows,
        guardrail_rows=guardrail_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=follow_up_path,
        eval_seed_base=int(eval_seed_base),
        device=device,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    gate_rows = build_gate_matrix_rows(
        source=source,
        resolution_rows=resolution_rows,
        execution_summary=execution_summary,
        artifact_rows=load_artifact_rows(paths),
        action_rows=action_rows,
        telemetry_rows=telemetry_rows,
        containment_rows=containment_rows,
        mechanism_rows=mechanism_rows,
        guardrail_rows=guardrail_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        resolution_rows=resolution_rows,
        execution_summary=execution_summary,
        artifact_rows=load_artifact_rows(paths),
        action_rows=action_rows,
        telemetry_rows=telemetry_rows,
        containment_rows=containment_rows,
        mechanism_rows=mechanism_rows,
        guardrail_rows=guardrail_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=follow_up_path,
        eval_seed_base=int(eval_seed_base),
        device=device,
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "probe_candidate_resolution_rows": output_dir / "probe_candidate_resolution_rows.csv",
        "probe_execution_rows": output_dir / "probe_execution_rows.csv",
        "probe_execution_failure_rows": output_dir / "probe_execution_failure_rows.csv",
        "action_response_probe_rows": output_dir / "action_response_probe_rows.csv",
        "telemetry_coverage_rows": output_dir / "telemetry_coverage_rows.csv",
        "containment_probe_rows": output_dir / "containment_probe_rows.csv",
        "mechanism_context_rows": output_dir / "mechanism_context_rows.csv",
        "guardrail_context_rows": output_dir / "guardrail_context_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_source_artifacts(
    *,
    m2762_dir: Path,
    m2763_audit: Path,
    m2756_dir: Path,
    m2758_design: Path,
    m2753_dir: Path,
    m1690_workload: Path,
    executable_specs: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    source = m2759.load_source_artifacts(
        m2756_dir=m2756_dir,
        m2758_design=m2758_design,
        m2753_dir=m2753_dir,
        m1690_workload=m1690_workload,
        executable_specs=executable_specs,
        follow_up_manifest=follow_up_manifest,
    )
    source["m2762_dir"] = str(m2762_dir)
    source["m2763_audit"] = str(m2763_audit)
    source["m2762_summary"] = read_json(m2762_dir / "summary.json") if (m2762_dir / "summary.json").exists() else {}
    source["m2762_gap_rows"] = read_csv_rows(m2762_dir / "telemetry_coverage_gap_rows.csv")
    source["m2762_schema_rows"] = read_csv_rows(m2762_dir / "telemetry_schema_contract_rows.csv")
    source["m2763_audit_text"] = m2763_audit.read_text(encoding="utf-8") if m2763_audit.exists() else ""
    source["source_exists"].update(
        {
            "m2762_summary": (m2762_dir / "summary.json").exists(),
            "m2762_gap_rows": (m2762_dir / "telemetry_coverage_gap_rows.csv").exists(),
            "m2762_schema_rows": (m2762_dir / "telemetry_schema_contract_rows.csv").exists(),
            "m2763_audit": m2763_audit.exists(),
        }
    )
    return source


def build_probe_candidate_resolution_rows(source: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]]]:
    parent_rows, parent_sources = m2759.build_probe_candidate_resolution_rows(source)
    rows: list[dict[str, Any]] = []
    resolved_sources: dict[str, dict[str, str]] = {}
    for index, parent in enumerate(parent_rows, start=1):
        parent_id = str(parent.get("probe_resolution_id", ""))
        probe_resolution_id = f"m2764-probe-resolution-{index:04d}"
        row = dict(parent)
        row["probe_resolution_id"] = probe_resolution_id
        row["resolution_status"] = (
            "resolved_to_m2764_instrumented_action_response_probe_surface"
            if _bool(row.get("execution_admitted", False))
            else "unresolved_or_not_admitted"
        )
        row["claim_boundary"] = CLAIM_SCOPE
        rows.append(row)
        if parent_id in parent_sources:
            resolved_sources[probe_resolution_id] = dict(parent_sources[parent_id])
    return rows, resolved_sources


def run_probe_execution(
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
        for name in ("probe_execution_rows.csv", "probe_execution_failure_rows.csv", "run_state.json"):
            path = output_dir / name
            if path.exists():
                path.unlink()

    specs = load_executable_specs(executable_specs_path)
    spec_by_id = {str(spec["task_source_id"]): spec for spec in specs}
    profile_cache: dict[tuple[str, str, str], tuple[dict[str, Any], Any, dict[str, str]]] = {}
    execution_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []

    for index, resolution in enumerate(resolution_rows):
        eval_seed = int(eval_seed_base) + index
        probe_resolution_id = str(resolution["probe_resolution_id"])
        try:
            if not _bool(resolution.get("execution_admitted", False)):
                raise ValueError(str(resolution.get("failure_reason", "candidate resolution not admitted")))
            source_row = resolved_sources[probe_resolution_id]
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
            row.update(probe_execution_metadata(resolution, eval_seed=eval_seed))
            execution_rows.append(row)
        except Exception as exc:  # noqa: BLE001 - every candidate must be accounted.
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
                "completed_execution_count": len(execution_rows),
                "failure_count": len(failure_rows),
                "accounted_count": len(execution_rows) + len(failure_rows),
                "latest_probe_resolution_id": probe_resolution_id,
                "complete": False,
                "next_blocker": next_blocker,
            },
        )

    write_csv_rows(output_dir / "probe_execution_rows.csv", execution_rows)
    write_csv_rows(output_dir / "probe_execution_failure_rows.csv", failure_rows, fieldnames=FAILURE_FIELDNAMES)
    all_metrics_finite = selected_metrics_are_finite(execution_rows) if execution_rows else False
    status_pass = bool(
        len(resolution_rows) == EXPECTED_CANDIDATE_COUNT
        and len(execution_rows) + len(failure_rows) == len(resolution_rows)
        and bool(execution_rows)
        and all_metrics_finite
        and not any(forbidden_execution_flag(row) for row in execution_rows + failure_rows)
    )
    summary = {
        "result_class": (
            "engineering_controller_route_a_action_response_telemetry_instrumented_probe_execution_pass"
            if status_pass
            else "engineering_controller_route_a_action_response_telemetry_instrumented_probe_execution_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "candidate_count": len(resolution_rows),
        "episode_count": len(execution_rows),
        "failure_count": len(failure_rows),
        "accounted_count": len(execution_rows) + len(failure_rows),
        "all_selected_metrics_finite": bool(all_metrics_finite),
        "environment_reset_run": bool(execution_rows),
        "environment_step_run": bool(execution_rows),
        "policy_action_run": bool(execution_rows),
        "policy_rollout_run": bool(execution_rows),
        **FALSE_CLAIM_FLAGS,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "next_blocker": next_blocker,
    }
    write_json(output_dir / "candidate_execution_summary.json", summary)
    write_run_state(
        output_dir / "run_state.json",
        {
            "candidate_count": len(resolution_rows),
            "completed_execution_count": len(execution_rows),
            "failure_count": len(failure_rows),
            "accounted_count": len(execution_rows) + len(failure_rows),
            "complete": len(execution_rows) + len(failure_rows) == len(resolution_rows),
            "status_pass": status_pass,
            "next_blocker": next_blocker,
        },
    )
    return summary


def probe_execution_metadata(resolution: Mapping[str, Any], *, eval_seed: int) -> dict[str, Any]:
    return {
        "m2764_eval_seed": int(eval_seed),
        "probe_resolution_id": resolution.get("probe_resolution_id", ""),
        "localization_id": resolution.get("localization_id", ""),
        "candidate_id": resolution.get("candidate_id", ""),
        "source_resolution_id": resolution.get("source_resolution_id", ""),
        "failure_family": resolution.get("failure_family", ""),
        "clearance_sign": resolution.get("clearance_sign", ""),
        "source_termination_reason": resolution.get("source_termination_reason", ""),
        "source_min_clearance_margin": resolution.get("source_min_clearance_margin", ""),
        "bounded_action_response_telemetry_instrumented_probe": True,
        "localized_candidate_surface_count": EXPECTED_CANDIDATE_COUNT,
        "guardrail_execution": False,
        "protected_rows_in_success_denominator": False,
        "hidden_oracle_actor_input_required": False,
        "localization_labels_actor_visible": False,
        "action_response_labels_actor_visible": False,
        "containment_labels_actor_visible": False,
        "mechanism_tags_actor_visible": False,
        "stress_axis_labels_actor_visible": False,
        "source_edge_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        **FALSE_CLAIM_FLAGS,
        "diagnostic_only_no_verdict": True,
        "claim_boundary": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
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
            "probe_resolution_id": resolution.get("probe_resolution_id", ""),
            "localization_id": resolution.get("localization_id", ""),
            "candidate_id": resolution.get("candidate_id", ""),
            "source_resolution_id": resolution.get("source_resolution_id", ""),
            "task_source_id": resolution.get("task_source_id", ""),
            "workload_id": resolution.get("workload_id", ""),
            "profile_name": resolution.get("profile_name", ""),
            "task_family": resolution.get("task_family", ""),
            "source_edge": resolution.get("source_edge", ""),
            "failure_family": resolution.get("failure_family", ""),
            "m2764_eval_seed": int(eval_seed),
            "error_type": error_type,
            "error_message": error_message,
            "environment_reset_run": False,
            "environment_step_run": False,
            "policy_action_run": False,
            "policy_rollout_run": False,
            "guardrail_execution": False,
            "diagnostic_only_no_verdict": True,
            "claim_boundary": CLAIM_SCOPE,
        }
    )
    return row


def load_artifact_rows(paths: dict[str, Path]) -> dict[str, list[dict[str, str]]]:
    return {
        "probe_execution_rows": read_csv_rows(paths["probe_execution_rows"]),
        "probe_execution_failure_rows": read_csv_rows(paths["probe_execution_failure_rows"]),
    }


def write_derived_outputs(
    paths: dict[str, Path],
    action_rows: list[dict[str, Any]],
    telemetry_rows: list[dict[str, Any]],
    containment_rows: list[dict[str, Any]],
    mechanism_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    write_csv_rows(paths["action_response_probe_rows"], action_rows, fieldnames=ACTION_RESPONSE_FIELDNAMES)
    write_csv_rows(paths["telemetry_coverage_rows"], telemetry_rows, fieldnames=TELEMETRY_COVERAGE_FIELDNAMES)
    write_csv_rows(paths["containment_probe_rows"], containment_rows, fieldnames=CONTAINMENT_FIELDNAMES)
    write_csv_rows(paths["mechanism_context_rows"], mechanism_rows, fieldnames=MECHANISM_FIELDNAMES)
    write_csv_rows(paths["guardrail_context_rows"], guardrail_rows, fieldnames=GUARDRAIL_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_guard_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)


def build_action_response_probe_rows(execution_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(execution_rows, start=1):
        previous_command = _float(row.get("previous_command_norm_mean"))
        current_action = _float(row.get("current_action_norm_mean"))
        action_rate_mean = _float(row.get("action_rate_mean"))
        trace_delta = _float(row.get("action_trace_delta_mean"))
        trace_delta_peak = _float(row.get("action_trace_delta_peak"))
        plan_first_error = _float(row.get("plan_first_action_error_mean"))
        plan_or_trace = plan_first_error if _is_finite(plan_first_error) else trace_delta
        plan_source = "planner_first_action_error" if _is_finite(plan_first_error) else "policy_action_trace_delta_fallback"
        speed_response = _float(row.get("speed_mean"))
        yaw_response = _float(row.get("max_abs_yaw_rate"))
        beta_response = _float(row.get("beta_abs_peak") or row.get("max_abs_beta"))
        finite_values = [
            previous_command,
            current_action,
            plan_or_trace,
            action_rate_mean,
            speed_response,
            yaw_response,
            beta_response,
        ]
        finite_metric = all(_is_finite(value) for value in finite_values)
        rows.append(
            {
                "probe_id": f"m2764-action-response-probe-{index:04d}",
                "probe_resolution_id": row.get("probe_resolution_id", ""),
                "candidate_id": row.get("candidate_id", ""),
                "localization_id": row.get("localization_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "failure_family": row.get("failure_family", ""),
                "previous_command": _finite_or_blank(previous_command),
                "previous_command_source": row.get("previous_command_source", "policy_action_trace_zero_bootstrap"),
                "current_action": _finite_or_blank(current_action),
                "current_action_source": "policy_action_trace",
                "actuator_lag_proxy": _finite_or_blank(plan_or_trace),
                "actuator_error_proxy": _finite_or_blank(plan_or_trace),
                "action_rate_mean": _finite_or_blank(action_rate_mean),
                "action_rate_peak": _finite_or_blank(max(_finite_or_zero(action_rate_mean), _finite_or_zero(trace_delta_peak))),
                "trace_delta_proxy": _finite_or_blank(trace_delta),
                "trace_delta_source": row.get("action_trace_delta_source", "current_action_minus_previous_command"),
                "command_response_phase_lag_proxy": _finite_or_blank(_mean_finite([plan_or_trace, action_rate_mean])),
                "speed_response_proxy": _finite_or_blank(speed_response),
                "yaw_response_proxy": _finite_or_blank(yaw_response),
                "beta_response_proxy": _finite_or_blank(beta_response),
                "plan_first_action_error_proxy": _finite_or_blank(plan_or_trace),
                "plan_first_action_error_source": plan_source,
                "finite_metric": finite_metric,
                "m2762_contract_satisfied": finite_metric,
                "action_response_labels_actor_visible": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_telemetry_coverage_rows(
    source: dict[str, Any],
    action_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    gap_by_candidate = {str(row.get("candidate_id", "")): row for row in source["m2762_gap_rows"]}
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(action_rows, start=1):
        gap = gap_by_candidate.get(str(row.get("candidate_id", "")), {})
        finite_metric = _bool(row.get("finite_metric", False))
        incoming_finite = _bool(gap.get("incoming_finite_metric", False))
        plan_finite = _is_finite(_float(row.get("plan_first_action_error_proxy")))
        response_finite = all(
            _is_finite(_float(row.get(key)))
            for key in ("speed_response_proxy", "yaw_response_proxy", "beta_response_proxy")
        )
        rows.append(
            {
                "telemetry_coverage_id": f"m2764-telemetry-coverage-{index:04d}",
                "probe_id": row.get("probe_id", ""),
                "probe_resolution_id": row.get("probe_resolution_id", ""),
                "candidate_id": row.get("candidate_id", ""),
                "localization_id": row.get("localization_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "failure_family": row.get("failure_family", ""),
                "m2759_incoming_finite_metric": incoming_finite,
                "m2762_gap_class": gap.get("gap_class", ""),
                "previous_command_finite": _is_finite(_float(row.get("previous_command"))),
                "previous_command_source": row.get("previous_command_source", ""),
                "current_action_finite": _is_finite(_float(row.get("current_action"))),
                "plan_first_or_trace_delta_finite": plan_finite,
                "plan_first_or_trace_delta_source": row.get("plan_first_action_error_source", ""),
                "response_proxy_finite": response_finite,
                "m2764_finite_metric": finite_metric,
                "finite_metric_improved_from_m2759": bool(finite_metric and not incoming_finite),
                "m2759_row_backfilled": False,
                "actor_visible_allowed": False,
                "hidden_oracle_actor_input_required": False,
                "actor_input_contract_changed": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_containment_probe_rows(execution_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(execution_rows, start=1):
        item = m2759.build_containment_probe_rows([row])[0]
        item["probe_id"] = f"m2764-containment-probe-{index:04d}"
        item["claim_boundary"] = CLAIM_SCOPE
        rows.append(item)
    return rows


def build_mechanism_context_rows(
    resolution_rows: list[Mapping[str, Any]],
    execution_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    execution_by_resolution = {str(row.get("probe_resolution_id", "")): row for row in execution_rows}
    rows: list[dict[str, Any]] = []
    for resolution in resolution_rows:
        execution = execution_by_resolution.get(str(resolution.get("probe_resolution_id", "")), {})
        tags = m2759.mechanism_tags(resolution, execution)
        for tag in tags:
            rows.append(
                {
                    "mechanism_context_id": f"m2764-mechanism-context-{len(rows) + 1:04d}",
                    "probe_resolution_id": resolution.get("probe_resolution_id", ""),
                    "candidate_id": resolution.get("candidate_id", ""),
                    "localization_id": resolution.get("localization_id", ""),
                    "task_source_id": resolution.get("task_source_id", ""),
                    "failure_family": resolution.get("failure_family", ""),
                    "mechanism_tag": tag,
                    "mechanism_tag_actor_visible": False,
                    "tag_scope": "evaluator_artifact_only",
                    "diagnostic_only_no_verdict": True,
                    "claim_boundary": CLAIM_SCOPE,
                }
            )
    return rows


def build_guardrail_context_rows(guardrail_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(guardrail_rows, start=1):
        rows.append(
            {
                "m2764_guardrail_id": f"m2764-guardrail-context-{index:04d}",
                "guardrail_context_id": row.get("guardrail_context_id", ""),
                "guardrail_source": row.get("guardrail_source", ""),
                "guardrail_source_id": row.get("guardrail_source_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "blocker_id": row.get("blocker_id", ""),
                "route": row.get("route", ""),
                "evidence_family": row.get("evidence_family", ""),
                "row_count": row.get("row_count", ""),
                "blocking_count": row.get("blocking_count", ""),
                "execution_candidate": False,
                "execution_admitted": False,
                "execution_run": False,
                "ordinary_success_denominator_allowed": False,
                "protected_rows_in_success_denominator": False,
                "actor_visible_allowed": False,
                "diagnostic_only_no_verdict": True,
                "guardrail_role": row.get("guardrail_role", "non_executed_guardrail_context"),
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_guard_rows(
    source: dict[str, Any],
    resolution_rows: list[Mapping[str, Any]],
    artifact_rows: dict[str, list[dict[str, str]]],
    guardrail_rows: list[Mapping[str, Any]],
    telemetry_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    all_rows: list[Mapping[str, Any]] = (
        resolution_rows + artifact_rows["probe_execution_rows"] + artifact_rows["probe_execution_failure_rows"] + telemetry_rows
    )
    actor_rows = source["actor_rows"]
    obs_status = m2759.actor_observed_expected_pass(actor_rows, "p0_observation_dim", "72", "72")
    action_status = m2759.actor_observed_expected_pass(actor_rows, "action_dim", "3", "3")
    checks = [
        ("p0_observation_dim", 72 if obs_status else "missing_or_failed", 72, obs_status),
        ("action_dim", 3 if action_status else "missing_or_failed", 3, action_status),
        (
            "hidden_oracle_actor_input_detected",
            any_flag(all_rows, "hidden_oracle_actor_input_required"),
            False,
            not any_flag(all_rows, "hidden_oracle_actor_input_required"),
        ),
        (
            "actor_input_contract_changed",
            any_flag(all_rows, "actor_input_contract_changed"),
            False,
            not any_flag(all_rows, "actor_input_contract_changed"),
        ),
        ("diagnostic_labels_actor_visible", any_label_actor_visible(all_rows), False, not any_label_actor_visible(all_rows)),
        ("telemetry_rows_actor_visible", any_flag(telemetry_rows, "actor_visible_allowed"), False, not any_flag(telemetry_rows, "actor_visible_allowed")),
        ("guardrails_actor_visible", any_flag(guardrail_rows, "actor_visible_allowed"), False, not any_flag(guardrail_rows, "actor_visible_allowed")),
    ]
    return [actor_guard(f"m2764-actor-guard-{index:04d}", family, observed, expected, status) for index, (family, observed, expected, status) in enumerate(checks, start=1)]


def actor_guard(guard_id: str, family: str, observed: Any, expected: Any, status: bool) -> dict[str, Any]:
    return {
        "guard_id": guard_id,
        "guard_family": family,
        "observed": observed,
        "expected": expected,
        "status_pass": bool(status),
        "actor_visible_allowed": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_claim_boundary_rows(
    *,
    follow_up_manifest_registered: bool,
    artifacts_present: bool,
    all_action_telemetry_finite: bool,
    telemetry_improved_count: int,
) -> list[dict[str, Any]]:
    claims = [
        ("route_a_instrumented_probe_artifact_completeness", True, artifacts_present, "M2764 complete probe artifacts"),
        ("finite_action_response_telemetry_observed", True, all_action_telemetry_finite, "finite M2764 evaluator telemetry rows"),
        ("telemetry_coverage_improved_from_m2759", True, telemetry_improved_count == EXPECTED_CANDIDATE_COUNT, "M2762 gap rows plus M2764 finite coverage rows"),
        ("result_audit_follow_up_registered", True, follow_up_manifest_registered, "M2765 result-audit manifest"),
        ("m2759_row_backfill", False, False, "new bounded execution with repaired evaluator telemetry"),
        ("repair_success", False, False, "separate repair design execution and audit"),
        ("driver_performance", False, False, "separate validation and promotion gates"),
        ("validation_readiness", False, False, "separate validation-readiness gate"),
        ("validation_result", False, False, "separate validation execution"),
        ("ranking_or_winner_selection", False, False, "separate controller-family comparison and ranking protocol"),
        ("checkpoint_promotion", False, False, "separate promotion gate"),
        ("paper_evidence", False, False, "separate paper route proof/generalization matrix"),
        ("finite_window_vs_gru", False, False, "separate controlled family comparison"),
        ("current_sim_verdict", False, False, "separate current-sim benchmark verdict gate"),
        ("high_fidelity_validation", False, False, "separate high-fidelity interface and validation route"),
        ("full_ideal_driver_completion", False, False, "full ideal driver gate"),
        ("level3_self_identification", False, False, "closed-loop self-identification proof gate"),
    ]
    return [
        {
            "claim_id": f"m2764-claim-{index:04d}",
            "claim_family": family,
            "allowed_in_m2764": allowed,
            "claim_made": made,
            "status_pass": bool((allowed and made) or (not allowed and not made)),
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, allowed, made, evidence) in enumerate(claims, start=1)
    ]


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    resolution_rows: list[dict[str, Any]],
    execution_summary: dict[str, Any],
    artifact_rows: dict[str, list[dict[str, str]]],
    action_rows: list[dict[str, Any]],
    telemetry_rows: list[dict[str, Any]],
    containment_rows: list[dict[str, Any]],
    mechanism_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    execution_rows = artifact_rows["probe_execution_rows"]
    failure_rows = artifact_rows["probe_execution_failure_rows"]
    all_exec_rows = execution_rows + failure_rows
    schema_fields = {str(row.get("output_column", "")) for row in source["m2762_schema_rows"]}
    return [
        gate("source_artifacts_present", "lineage", all(source["source_exists"].values()), source["source_exists"], "M2762 M2763 M2756 M2758 M2753 resolver specs and M2765 manifest present", "lineage_invalid"),
        gate("m2762_summary_status_pass", "lineage", _bool(source["m2762_summary"].get("status_pass", False)), source["m2762_summary"].get("status_pass", False), True, "lineage_invalid"),
        gate("m2763_audit_routes_to_m2764", "lineage", "m2764" in source["m2763_audit_text"], "m2764" in source["m2763_audit_text"], True, "lineage_invalid"),
        gate("m2762_schema_contract_present", "telemetry", {"previous_command", "current_action", "plan_first_action_error_proxy", "finite_metric"}.issubset(schema_fields), sorted(schema_fields), "previous/current/plan-or-trace/finite contract", "metric_artifact"),
        gate("localized_candidate_count", "candidate_surface", len(resolution_rows) == EXPECTED_CANDIDATE_COUNT, len(resolution_rows), EXPECTED_CANDIDATE_COUNT, "scenario_sampling_failure"),
        gate("collision_negative_clearance_count", "candidate_surface", count_eq(resolution_rows, "failure_family", "collision_negative_clearance") == EXPECTED_COLLISION_NEGATIVE_CLEARANCE_COUNT, count_eq(resolution_rows, "failure_family", "collision_negative_clearance"), EXPECTED_COLLISION_NEGATIVE_CLEARANCE_COUNT, "scenario_sampling_failure"),
        gate("offtrack_positive_clearance_count", "candidate_surface", count_eq(resolution_rows, "failure_family", "offtrack_positive_clearance") == EXPECTED_OFFTRACK_POSITIVE_CLEARANCE_COUNT, count_eq(resolution_rows, "failure_family", "offtrack_positive_clearance"), EXPECTED_OFFTRACK_POSITIVE_CLEARANCE_COUNT, "scenario_sampling_failure"),
        gate("l3_profile_only", "candidate_surface", {row["profile_name"] for row in resolution_rows} == {CANONICAL_PROFILE}, sorted({row["profile_name"] for row in resolution_rows}), CANONICAL_PROFILE, "contract_violation"),
        gate("all_candidates_resolved_or_accounted", "execution", len(execution_rows) + len(failure_rows) == len(resolution_rows), len(execution_rows) + len(failure_rows), len(resolution_rows), "lineage_invalid"),
        gate("new_probe_execution_rows_present", "execution", bool(execution_rows), len(execution_rows), ">0", "behavior_regression"),
        gate("all_selected_metrics_finite", "metric", selected_metrics_are_finite(execution_rows) if execution_rows else False, execution_summary.get("all_selected_metrics_finite"), True, "metric_artifact"),
        gate("action_response_rows_written", "metric", len(action_rows) == len(execution_rows), len(action_rows), len(execution_rows), "metric_artifact"),
        gate("action_response_rows_all_finite", "metric", all_action_telemetry_finite(action_rows), count_finite_metric(action_rows), len(action_rows), "metric_artifact"),
        gate("telemetry_coverage_rows_written", "metric", len(telemetry_rows) == len(action_rows), len(telemetry_rows), len(action_rows), "metric_artifact"),
        gate("telemetry_coverage_improved_from_m2759", "metric", count_improved_telemetry(telemetry_rows) == EXPECTED_CANDIDATE_COUNT, count_improved_telemetry(telemetry_rows), EXPECTED_CANDIDATE_COUNT, "metric_artifact"),
        gate("m2759_rows_not_backfilled", "telemetry", not any_flag(telemetry_rows, "m2759_row_backfilled"), any_flag(telemetry_rows, "m2759_row_backfilled"), False, "proof_washout"),
        gate("containment_rows_written", "metric", len(containment_rows) == len(execution_rows), len(containment_rows), len(execution_rows), "metric_artifact"),
        gate("mechanism_rows_cover_candidates", "metric", len({row["probe_resolution_id"] for row in mechanism_rows}) == len(resolution_rows), len({row["probe_resolution_id"] for row in mechanism_rows}), len(resolution_rows), "metric_artifact"),
        gate("guardrail_rows_carried", "guardrail", len(guardrail_rows) == EXPECTED_GUARDRAIL_COUNT, len(guardrail_rows), EXPECTED_GUARDRAIL_COUNT, "lineage_invalid"),
        gate("guardrail_execution_false", "guardrail", not any_flag(guardrail_rows, "execution_run"), any_flag(guardrail_rows, "execution_run"), False, "proof_washout"),
        gate("protected_denominator_false", "guardrail", not any_flag(all_exec_rows + guardrail_rows, "protected_rows_in_success_denominator"), any_flag(all_exec_rows + guardrail_rows, "protected_rows_in_success_denominator"), False, "proof_washout"),
        gate("actor_contract_guards_pass", "contract", all(_bool(row["status_pass"]) for row in actor_guard_rows), "all_pass" if all(_bool(row["status_pass"]) for row in actor_guard_rows) else actor_guard_rows, "all_pass", "contract_violation"),
        gate("hidden_oracle_actor_input_false", "contract", not any_flag(all_exec_rows + resolution_rows + telemetry_rows, "hidden_oracle_actor_input_required"), any_flag(all_exec_rows + resolution_rows + telemetry_rows, "hidden_oracle_actor_input_required"), False, "contract_violation"),
        gate("diagnostic_labels_actor_visible_false", "contract", not any_label_actor_visible(all_exec_rows + resolution_rows + telemetry_rows + mechanism_rows), any_label_actor_visible(all_exec_rows + resolution_rows + telemetry_rows + mechanism_rows), False, "contract_violation"),
        gate("forbidden_execution_false", "claim", not any(forbidden_execution_flag(row) for row in all_exec_rows), "forbidden flag present" if any(forbidden_execution_flag(row) for row in all_exec_rows) else False, False, "proof_washout"),
        gate("claim_boundary_rows_pass", "claim", all(_bool(row["status_pass"]) for row in claim_rows), "all_pass" if all(_bool(row["status_pass"]) for row in claim_rows) else claim_rows, "all_pass", "proof_washout"),
        gate("required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True, "lineage_invalid"),
    ]


def gate(
    gate_id: str,
    family: str,
    status_pass: bool,
    observed: Any,
    expected: Any,
    failure_type: str,
) -> dict[str, Any]:
    return {
        "gate_id": f"m2764-gate-{gate_id}",
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
    resolution_rows: list[dict[str, Any]],
    execution_summary: dict[str, Any],
    artifact_rows: dict[str, list[dict[str, str]]],
    action_rows: list[dict[str, Any]],
    telemetry_rows: list[dict[str, Any]],
    containment_rows: list[dict[str, Any]],
    mechanism_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
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
    execution_rows = artifact_rows["probe_execution_rows"]
    failure_rows = artifact_rows["probe_execution_failure_rows"]
    termination_counts = Counter(str(row.get("termination_reason", "")) for row in execution_rows)
    status_pass = bool(all(_bool(row["status_pass"]) for row in gate_rows))
    return {
        "milestone": milestone,
        "result_class": (
            "engineering_controller_route_a_action_response_telemetry_instrumented_probe_bounded_execution_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_action_response_telemetry_instrumented_probe_bounded_execution_preflight_fail"
        ),
        "status_pass": status_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "localized_candidate_count": len(resolution_rows),
        "resolved_candidate_count": sum(1 for row in resolution_rows if _bool(row.get("execution_admitted", False))),
        "probe_execution_row_count": len(execution_rows),
        "probe_execution_failure_row_count": len(failure_rows),
        "accounted_candidate_count": len(execution_rows) + len(failure_rows),
        "collision_negative_clearance_count": count_eq(resolution_rows, "failure_family", "collision_negative_clearance"),
        "offtrack_positive_clearance_count": count_eq(resolution_rows, "failure_family", "offtrack_positive_clearance"),
        "guardrail_context_row_count": len(guardrail_rows),
        "action_response_probe_row_count": len(action_rows),
        "telemetry_coverage_row_count": len(telemetry_rows),
        "containment_probe_row_count": len(containment_rows),
        "mechanism_context_row_count": len(mechanism_rows),
        "mechanism_tags": sorted({str(row.get("mechanism_tag", "")) for row in mechanism_rows}),
        "diagnostic_success_count": sum(1 for row in execution_rows if _episode_success(row)),
        "diagnostic_collision_count": sum(1 for row in execution_rows if _bool(row.get("collision", False))),
        "diagnostic_offtrack_count": sum(1 for row in execution_rows if str(row.get("termination_reason", "")) == "off_track"),
        "diagnostic_termination_counts": dict(sorted(termination_counts.items())),
        "all_selected_metrics_finite": bool(execution_summary.get("all_selected_metrics_finite", False)),
        "previous_command_finite_count": count_finite(action_rows, "previous_command"),
        "current_action_finite_count": count_finite(action_rows, "current_action"),
        "plan_first_or_trace_delta_finite_count": count_finite(action_rows, "plan_first_action_error_proxy"),
        "finite_metric_true_count": count_finite_metric(action_rows),
        "finite_metric_false_count": len(action_rows) - count_finite_metric(action_rows),
        "telemetry_coverage_improved_count": count_improved_telemetry(telemetry_rows),
        "m2759_rows_backfilled": any_flag(telemetry_rows, "m2759_row_backfilled"),
        "actor_contract_guard_row_count": len(actor_guard_rows),
        "actor_contract_guard_rows_pass": all(_bool(row["status_pass"]) for row in actor_guard_rows),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(_bool(row["status_pass"]) for row in claim_rows),
        "gate_row_count": len(gate_rows),
        "gate_matrix_pass": all(_bool(row["status_pass"]) for row in gate_rows),
        "required_artifacts_present": required_artifacts_present,
        "source_exists": source["source_exists"],
        "guardrail_execution": any_flag(guardrail_rows + execution_rows + failure_rows, "execution_run") or any_flag(execution_rows + failure_rows, "guardrail_execution"),
        "protected_rows_in_success_denominator": any_flag(guardrail_rows + execution_rows + failure_rows, "protected_rows_in_success_denominator"),
        "actor_input_contract_changed": any_flag(execution_rows + failure_rows + telemetry_rows, "actor_input_contract_changed"),
        "hidden_oracle_actor_input_required": any_flag(resolution_rows + execution_rows + failure_rows + telemetry_rows, "hidden_oracle_actor_input_required"),
        "diagnostic_labels_actor_visible": any_label_actor_visible(resolution_rows + execution_rows + failure_rows + mechanism_rows + telemetry_rows),
        **{key: any_flag(execution_rows + failure_rows, key) for key in FALSE_CLAIM_FLAGS},
        "eval_seed_base": int(eval_seed_base),
        "device": device,
        "next_blocker": next_blocker,
        "follow_up_manifest": str(follow_up_manifest),
        "artifacts": {key: str(value) for key, value in paths.items()},
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    lines = [
        "# M2764 Engineering Controller Route A Action-Response Telemetry Instrumented Probe Bounded Execution Preflight",
        "",
        "## Metadata",
        "",
        f"- status: {'completed' if summary['status_pass'] else 'failed'}",
        f"- result class: `{summary['result_class']}`",
        f"- localized candidates: {summary['localized_candidate_count']}",
        f"- resolved candidates: {summary['resolved_candidate_count']}/{summary['localized_candidate_count']}",
        f"- execution rows: {summary['probe_execution_row_count']}",
        f"- failure rows: {summary['probe_execution_failure_row_count']}",
        f"- action-response finite rows: {summary['finite_metric_true_count']}/{summary['action_response_probe_row_count']}",
        f"- telemetry coverage improved rows: {summary['telemetry_coverage_improved_count']}/{summary['telemetry_coverage_row_count']}",
        f"- previous-command finite rows: {summary['previous_command_finite_count']}",
        f"- plan-first-or-trace-delta finite rows: {summary['plan_first_or_trace_delta_finite_count']}",
        f"- guardrail context rows: {summary['guardrail_context_row_count']}",
        f"- diagnostic outcomes: success {summary['diagnostic_success_count']} collision {summary['diagnostic_collision_count']} offtrack {summary['diagnostic_offtrack_count']}",
        f"- diagnostic termination counts: {summary['diagnostic_termination_counts']}",
        f"- gate matrix pass: {summary['gate_matrix_pass']}",
        f"- next blocker: `{summary['next_blocker']}`",
        f"- follow-up manifest: `{summary['follow_up_manifest']}`",
        "",
        "## Result",
        "",
        "M2764 executes the bounded M2756 localized probe surface after the M2762",
        "telemetry coverage contract audit. The evaluator records previous physical",
        "command, current action, and a trace-delta fallback as actor-invisible",
        "telemetry. This repairs the forward probe artifact coverage only; it does",
        "not backfill M2759 rows and does not make a repair-success, performance,",
        "validation, paper, current-sim, high-fidelity, full-driver, or self-ID",
        "claim.",
        "",
        "## Mechanism Tags",
        "",
        "```text",
        *[str(tag) for tag in summary["mechanism_tags"]],
        "```",
        "",
        "## Claim Boundary",
        "",
        summary["claim_scope"],
        "",
        "Forbidden interpretation:",
        "",
        summary["forbidden_interpretation"],
        "",
    ]
    return "\n".join(lines)


def write_follow_up_manifest(path: Path) -> None:
    manifest_id = DEFAULT_NEXT_BLOCKER
    write_json(
        path,
        {
            "id": manifest_id,
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
            ],
            "lineage": {
                "parent_checkpoint": [
                    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"
                ],
                "parent_dataset": [
                    "docs/m2764-engineering-controller-route-a-action-response-telemetry-instrumented-probe-bounded-execution-preflight.md",
                    "runs/m2764_engineering_controller_route_a_action_response_telemetry_instrumented_probe_bounded_execution_preflight/summary.json",
                    "runs/m2764_engineering_controller_route_a_action_response_telemetry_instrumented_probe_bounded_execution_preflight/action_response_probe_rows.csv",
                    "runs/m2764_engineering_controller_route_a_action_response_telemetry_instrumented_probe_bounded_execution_preflight/telemetry_coverage_rows.csv",
                    "runs/m2764_engineering_controller_route_a_action_response_telemetry_instrumented_probe_bounded_execution_preflight/probe_execution_rows.csv",
                    "runs/m2764_engineering_controller_route_a_action_response_telemetry_instrumented_probe_bounded_execution_preflight/gate_matrix.csv",
                    "docs/m2763-engineering-controller-route-a-action-response-telemetry-coverage-instrumentation-repair-result-audit.md",
                    "runs/m2762_engineering_controller_route_a_action_response_telemetry_coverage_instrumentation_repair_preflight/summary.json",
                ],
                "parent_config": [
                    "experiments/manifests/m2764-engineering-controller-route-a-action-response-telemetry-instrumented-probe-bounded-execution-preflight.json",
                    "experiments/manifests/m2763-engineering-controller-route-a-action-response-telemetry-coverage-instrumentation-repair-result-audit.json",
                ],
                "parent_objective": [
                    "audit M2764 bounded instrumented probe artifacts before mechanism repair interpretation or another execution"
                ],
                "derived_from": [
                    "m2764-engineering-controller-route-a-action-response-telemetry-instrumented-probe-bounded-execution-preflight",
                    "m2763-engineering-controller-route-a-action-response-telemetry-coverage-instrumentation-repair-result-audit",
                    "m2762-engineering-controller-route-a-action-response-telemetry-coverage-instrumentation-repair-preflight",
                ],
                "blocked_by": [
                    "M2764 artifacts require result audit before any mechanism interpretation repair design validation ranking or performance claim"
                ],
                "supersedes": [
                    "same-surface execution extension before auditing M2764",
                    "repair success driver performance validation paper current-sim high-fidelity full-driver or self-ID claim from M2764"
                ],
                "invalidates": [],
            },
            "review_artifact": "docs/reviews/m2765-engineering-controller-route-a-action-response-telemetry-instrumented-probe-bounded-execution-result-audit.md",
            "public_gates": [
                "M2765 must consume M2764 summary action-response telemetry coverage execution guard actor claim and gate artifacts",
                "M2765 must accept or reject M2764 artifact completeness and claim safety",
                "M2765 must preserve actor 72/action 3 no hidden oracle actor input and actor-invisible telemetry labels",
                "M2765 must preserve M2759 no-backfill evidence and M2762 forward contract lineage",
                "M2765 must reject repair success driver performance validation ranking paper current-sim high-fidelity full ideal driver and self-ID claims",
                "M2765 must route to synthesis artifact repair or bounded next evidence step without executing replay validation training ranking or promotion",
            ],
            "private_holdout_policy": "not_used",
            "forbidden_shortcuts": [
                "do not execute replay validation training PPO source build adapter probe or external simulation",
                "do not rank controllers source edges stress axes profiles task families mechanism tags or candidates",
                "do not select a winner promote a checkpoint or compute success-rate verdict",
                "do not claim repair success driver performance validation readiness paper current-sim high-fidelity full ideal driver or self-ID",
                "do not backfill M2759 finite_metric rows",
                "do not change actor inputs or expose telemetry labels to actor input",
            ],
            "workflow_synthesis": {
                "branch": "engineering_controller_route_a_action_response_telemetry_instrumented_probe",
                "evidence_axis": "route_a_action_response_telemetry_instrumented_probe_result_audit",
                "evidence_increment": "audits whether M2764 produced complete finite evaluator-only action-response telemetry rows without overclaiming",
                "claim_scope": "Route A diagnostic artifact audit only; no replay validation training ranking promotion repair-success driver-performance paper current-sim high-fidelity self-ID or full ideal driver claim",
                "stop_condition": [
                    "stop if M2764 artifacts are incomplete or finite telemetry is absent",
                    "stop if actor or claim boundaries were violated",
                    "stop if another same-surface execution is proposed without synthesis",
                ],
                "fallback_plan": [
                    "route to telemetry artifact repair if finite rows are absent",
                    "route to branch synthesis if artifacts are complete but next mechanism route remains ambiguous",
                    "route to bounded repair design only if audit supports an evidence-changing non-ranking follow-up",
                ],
                "synthesis_cadence": 10,
                "synthesis_trigger": "M2764 instrumented probe execution has produced artifacts that require result audit",
                "synthesis_decision": "not_applicable",
            },
            "training_stage": {
                "stage": "evaluation_only",
                "stage_objective": "action-response telemetry instrumented probe result audit",
                "admission_evidence": [
                    "M2764 bounded probe artifacts exist",
                    "M2764 registered this result-audit follow-up before interpretation",
                ],
                "blocked_shortcuts": [
                    "no replay validation training ranking promotion or performance claim",
                    "no actor input change or hidden oracle input",
                ],
                "allowed_updates": [
                    "docs/m2765-engineering-controller-route-a-action-response-telemetry-instrumented-probe-bounded-execution-result-audit.md",
                    "M2765 status queue scoreboard research log and review",
                    "one bounded follow-up manifest if audit accepts artifacts",
                ],
                "next_stage_criteria": [
                    "M2765 accepts or rejects M2764 artifacts and claim boundaries",
                    "M2765 registers one bounded next step or synthesis route",
                ],
            },
            "self_id_evidence_discipline": {
                "claim_level": "not_applicable",
                "current_frame_substitution_risk": (
                    "M2765 audits Route A engineering telemetry artifacts and does not test history necessity or "
                    "current-frame substitution."
                ),
                "history_necessity_tests": [
                    "None in M2765; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
                ],
                "temporal_evidence_window": (
                    "M2759-M2764 Route A action-response containment probe and telemetry coverage artifacts only."
                ),
                "negative_result_policy": (
                    "If M2764 finite telemetry is absent or incomplete preserve the blocker and route to artifact repair "
                    "or synthesis rather than weakening gates or claiming self-ID evidence."
                ),
                "allowed_claims": [
                    "M2764 telemetry artifacts are complete and claim-safe or explicitly rejected",
                    "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
                ],
            },
            "local_search_guard": {
                "actual_progress_type": "result_audit",
                "process_overhead": "low",
                "local_search_risk": "medium",
                "same_failure_repeat_count": 0,
                "same_public_gate_repair_count": 0,
                "evidence_expansion": "audits new closed-loop telemetry rows from M2764 before another branch action",
                "paper_verdict_delta": "no paper verdict; can decide whether Route A has a finite action-response telemetry basis for the next bounded diagnostic step",
                "must_synthesize_if": [
                    "M2765 cannot decide a bounded next step after complete M2764 artifacts",
                    "M2765 proposes same-surface execution without a new evidence axis",
                    "M2765 would make validation performance paper current-sim high-fidelity full-driver or self-ID claims",
                ],
            },
            "hypothesis": "M2764 artifacts can be audited as complete and claim-safe before any mechanism repair interpretation.",
            "success_criteria": [
                "docs/m2765-engineering-controller-route-a-action-response-telemetry-instrumented-probe-bounded-execution-result-audit.md exists",
                "M2765 accepts or rejects M2764 finite telemetry and guardrail evidence",
                "actor and claim boundaries are preserved",
                "one bounded follow-up or synthesis route is registered",
            ],
            "failure_criteria": [
                "M2765 overclaims M2764 as repair success validation performance paper current-sim high-fidelity full-driver or self-ID evidence",
                "M2765 hides M2764 finite telemetry gaps or guardrail violations",
                "M2765 fails to register a bounded next step or synthesis route",
            ],
            "decision_rule": "Pass only if M2765 provides a bounded result audit of M2764 artifacts and preserves all actor guardrail and claim boundaries.",
            "commands": [{"name": "result_audit", "command": "true"}],
            "required_artifacts": [
                {
                    "path": "docs/m2765-engineering-controller-route-a-action-response-telemetry-instrumented-probe-bounded-execution-result-audit.md",
                    "type": "md",
                }
            ],
            "baseline_checkpoints": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"
            ],
            "baseline_artifacts": [
                "runs/m2764_engineering_controller_route_a_action_response_telemetry_instrumented_probe_bounded_execution_preflight/summary.json",
                "runs/m2764_engineering_controller_route_a_action_response_telemetry_instrumented_probe_bounded_execution_preflight/action_response_probe_rows.csv",
                "runs/m2764_engineering_controller_route_a_action_response_telemetry_instrumented_probe_bounded_execution_preflight/telemetry_coverage_rows.csv",
            ],
        },
    )


def count_eq(rows: list[Mapping[str, Any]], key: str, expected: str) -> int:
    return sum(1 for row in rows if str(row.get(key, "")) == expected)


def count_finite(rows: list[Mapping[str, Any]], key: str) -> int:
    return sum(1 for row in rows if _is_finite(_float(row.get(key))))


def count_finite_metric(rows: list[Mapping[str, Any]]) -> int:
    return sum(1 for row in rows if _bool(row.get("finite_metric", False)))


def count_improved_telemetry(rows: list[Mapping[str, Any]]) -> int:
    return sum(1 for row in rows if _bool(row.get("finite_metric_improved_from_m2759", False)))


def all_action_telemetry_finite(rows: list[Mapping[str, Any]]) -> bool:
    return bool(rows) and count_finite_metric(rows) == len(rows)


def any_label_actor_visible(rows: list[Mapping[str, Any]]) -> bool:
    return m2759.any_label_actor_visible(rows)


def forbidden_execution_flag(row: Mapping[str, Any]) -> bool:
    forbidden_keys = [
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
        "ranking_run",
        "winner_selected",
        "checkpoint_promoted",
        "success_rate_verdict_claim_made",
        "repair_success_claim_made",
        "driver_performance_claim_made",
        "validation_readiness_claim_made",
        "validation_result_claim_made",
        "paper_claim_made",
        "current_sim_verdict_claim_made",
        "high_fidelity_validation_claim_made",
        "full_ideal_driver_gate_passed",
        "level3_self_id_claim_made",
        "actor_input_contract_changed",
        "hidden_oracle_actor_input_required",
        "guardrail_execution",
        "protected_rows_in_success_denominator",
    ]
    return any(_bool(row.get(key, False)) for key in forbidden_keys)


def any_flag(rows: list[Mapping[str, Any]], key: str) -> bool:
    return any(_bool(row.get(key, False)) for row in rows)


def _episode_success(row: Mapping[str, Any]) -> bool:
    if "success" in row:
        return _bool(row.get("success"))
    return _bool(row.get("obstacle_completed", False)) and not _bool(row.get("collision", False))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "y", "pass", "passed"}


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _is_finite(value: float) -> bool:
    return math.isfinite(value)


def _finite_or_zero(value: float) -> float:
    return value if math.isfinite(value) else 0.0


def _finite_or_blank(value: float) -> float | str:
    return value if math.isfinite(value) else ""


def _mean_finite(values: list[float]) -> float:
    finite = [value for value in values if math.isfinite(value)]
    return sum(finite) / len(finite) if finite else float("nan")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2762-dir", type=Path, default=DEFAULT_M2762_DIR)
    parser.add_argument("--m2763-audit", type=Path, default=DEFAULT_M2763_AUDIT)
    parser.add_argument("--m2756-dir", type=Path, default=DEFAULT_M2756_DIR)
    parser.add_argument("--m2758-design", type=Path, default=DEFAULT_M2758_DESIGN)
    parser.add_argument("--m2753-dir", type=Path, default=DEFAULT_M2753_DIR)
    parser.add_argument("--m1690-workload", type=Path, default=DEFAULT_EXECUTABLE_WORKLOAD)
    parser.add_argument("--executable-specs", type=Path, default=DEFAULT_EXECUTABLE_SPECS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--no-resume", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = run(
        m2762_dir=args.m2762_dir,
        m2763_audit=args.m2763_audit,
        m2756_dir=args.m2756_dir,
        m2758_design=args.m2758_design,
        m2753_dir=args.m2753_dir,
        m1690_workload=args.m1690_workload,
        executable_specs=args.executable_specs,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        eval_seed_base=args.eval_seed_base,
        device=args.device,
        resume=not args.no_resume,
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"finite_metric_true_count={summary['finite_metric_true_count']}")
    print(f"telemetry_coverage_improved_count={summary['telemetry_coverage_improved_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
