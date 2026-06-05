"""M2759 bounded action-response and containment probe execution."""

from __future__ import annotations

import argparse
import math
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

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
    "m2759-engineering-controller-route-a-post-cross-axis-negative-action-response-containment-probe-bounded-execution-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2760-engineering-controller-route-a-post-cross-axis-negative-action-response-containment-probe-bounded-execution-result-audit"
)
DEFAULT_M2756_DIR = Path("runs/m2756_engineering_controller_route_a_post_cross_axis_negative_failure_localization_panel")
DEFAULT_M2758_DESIGN = Path(
    "docs/m2758-engineering-controller-route-a-post-cross-axis-negative-action-response-containment-probe-design.md"
)
DEFAULT_M2753_DIR = Path("runs/m2753_engineering_controller_route_a_cross_axis_stress_generalization_bounded_execution_preflight")
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2759_engineering_controller_route_a_post_cross_axis_negative_action_response_containment_probe_bounded_execution_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2759-engineering-controller-route-a-post-cross-axis-negative-action-response-containment-probe-bounded-execution-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2760-engineering-controller-route-a-post-cross-axis-negative-action-response-containment-probe-bounded-execution-result-audit.json"
)
DEFAULT_EVAL_SEED_BASE = 275900

EXPECTED_CANDIDATE_COUNT = 12
EXPECTED_COLLISION_NEGATIVE_CLEARANCE_COUNT = 3
EXPECTED_OFFTRACK_POSITIVE_CLEARANCE_COUNT = 9
EXPECTED_GUARDRAIL_COUNT = 31
CANONICAL_PROFILE = "L3_online_gru"
CLAIM_SCOPE = (
    "M2759 Route A post-cross-axis negative action-response and containment probe bounded execution only; "
    "reset, step, policy action, and rollout are allowed only for the 12 M2756 localized candidate rows while "
    "no replay, validation, training, PPO, source build, adapter probe, external simulation, ranking, winner "
    "selection, promotion, success-rate verdict, repair-success, driver-performance, paper, finite-window-vs-GRU, "
    "current-sim, high-fidelity validation, full ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, controller-family ranking, source-edge "
    "ranking, stress-axis ranking, task-family ranking, profile ranking, winner selection, checkpoint promotion, "
    "success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity "
    "validation readiness or result, full ideal driver completion, or level3 self-identification"
)
ALLOWED_MECHANISM_TAGS = (
    "collision_negative_clearance",
    "offtrack_positive_clearance",
    "action_response_mismatch_context",
    "track_containment_context",
    "obstacle_timing_context",
    "mixed_mechanism_context",
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

RESOLUTION_FIELDNAMES = [
    "probe_resolution_id",
    "localization_id",
    "candidate_id",
    "source_resolution_id",
    "task_source_id",
    "workload_id",
    "profile_name",
    "task_family",
    "source_edge",
    "stress_axis_primary",
    "stress_axis_tags",
    "failure_family",
    "clearance_sign",
    "source_termination_reason",
    "source_min_clearance_margin",
    "profile_config_path",
    "checkpoint_path",
    "resolution_status",
    "execution_admitted",
    "execution_planned",
    "failure_reason",
    "actor_contract_shape_72_action_3",
    "hidden_oracle_actor_input_required",
    "localization_labels_actor_visible",
    "action_response_labels_actor_visible",
    "containment_labels_actor_visible",
    "mechanism_tags_actor_visible",
    "stress_axis_labels_actor_visible",
    "source_edge_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "guardrail_execution",
    "protected_rows_in_success_denominator",
    "diagnostic_only_no_verdict",
    "ranking_run",
    "claim_boundary",
]
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
    "m2759_eval_seed",
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
    "localization_labels_actor_visible",
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
    "current_action",
    "actuator_lag_proxy",
    "actuator_error_proxy",
    "action_rate_mean",
    "action_rate_peak",
    "command_response_phase_lag_proxy",
    "speed_response_proxy",
    "yaw_response_proxy",
    "beta_response_proxy",
    "plan_first_action_error_proxy",
    "finite_metric",
    "action_response_labels_actor_visible",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
CONTAINMENT_FIELDNAMES = [
    "probe_id",
    "probe_resolution_id",
    "candidate_id",
    "localization_id",
    "task_source_id",
    "failure_family",
    "termination_reason",
    "min_clearance_margin",
    "clearance_sign",
    "obstacle_completed",
    "max_off_track_overshoot",
    "time_to_first_off_track_s",
    "off_track_severity_proxy",
    "impact_speed_proxy",
    "impact_severity_proxy",
    "recoverability_window_success",
    "post_event_speed_proxy",
    "post_event_yaw_proxy",
    "post_event_offtrack_proxy",
    "containment_failure_flag",
    "collision_risk_flag",
    "containment_labels_actor_visible",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
MECHANISM_FIELDNAMES = [
    "mechanism_context_id",
    "probe_resolution_id",
    "candidate_id",
    "localization_id",
    "task_source_id",
    "failure_family",
    "mechanism_tag",
    "mechanism_tag_actor_visible",
    "tag_scope",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
GUARDRAIL_FIELDNAMES = [
    "m2759_guardrail_id",
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
    "allowed_in_m2759",
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
    "probe_candidate_resolution_rows",
    "probe_execution_rows",
    "probe_execution_failure_rows",
    "action_response_probe_rows",
    "containment_probe_rows",
    "mechanism_context_rows",
    "guardrail_context_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
]


def run_post_cross_axis_negative_action_response_containment_probe_bounded_execution_preflight(
    *,
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
    paths = artifact_paths(output, doc_path=Path(doc_path))
    source = load_source_artifacts(
        m2756_dir=Path(m2756_dir),
        m2758_design=Path(m2758_design),
        m2753_dir=Path(m2753_dir),
        m1690_workload=Path(m1690_workload),
        executable_specs=Path(executable_specs),
        follow_up_manifest=Path(follow_up_manifest),
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
    containment_rows = build_containment_probe_rows(artifact_rows["probe_execution_rows"])
    mechanism_rows = build_mechanism_context_rows(resolution_rows, artifact_rows["probe_execution_rows"])
    guardrail_rows = build_guardrail_context_rows(source["guardrail_rows"])
    actor_guard_rows = build_actor_contract_guard_rows(source, resolution_rows, artifact_rows, guardrail_rows)
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=False,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        resolution_rows=resolution_rows,
        execution_summary=execution_summary,
        artifact_rows=artifact_rows,
        action_rows=action_rows,
        containment_rows=containment_rows,
        mechanism_rows=mechanism_rows,
        guardrail_rows=guardrail_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        required_artifacts_present=False,
    )
    write_derived_outputs(paths, action_rows, containment_rows, mechanism_rows, guardrail_rows, actor_guard_rows, claim_rows, gate_rows)

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"})
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_artifacts_present,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        resolution_rows=resolution_rows,
        execution_summary=execution_summary,
        artifact_rows=load_artifact_rows(paths),
        action_rows=action_rows,
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
        containment_rows=containment_rows,
        mechanism_rows=mechanism_rows,
        guardrail_rows=guardrail_rows,
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
        resolution_rows=resolution_rows,
        execution_summary=execution_summary,
        artifact_rows=load_artifact_rows(paths),
        action_rows=action_rows,
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
        containment_rows=containment_rows,
        mechanism_rows=mechanism_rows,
        guardrail_rows=guardrail_rows,
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
        "probe_candidate_resolution_rows": output_dir / "probe_candidate_resolution_rows.csv",
        "probe_execution_rows": output_dir / "probe_execution_rows.csv",
        "probe_execution_failure_rows": output_dir / "probe_execution_failure_rows.csv",
        "action_response_probe_rows": output_dir / "action_response_probe_rows.csv",
        "containment_probe_rows": output_dir / "containment_probe_rows.csv",
        "mechanism_context_rows": output_dir / "mechanism_context_rows.csv",
        "guardrail_context_rows": output_dir / "guardrail_context_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2756_dir: Path,
    m2758_design: Path,
    m2753_dir: Path,
    m1690_workload: Path,
    executable_specs: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    localization_rows = read_csv_rows(m2756_dir / "failure_localization_rows.csv")
    m2753_candidate_rows = read_csv_rows(m2753_dir / "cross_axis_candidate_rows.csv")
    m2753_resolution_rows = read_csv_rows(m2753_dir / "execution_candidate_resolution_rows.csv")
    m1690_workload_rows = read_csv_rows(m1690_workload)
    source_exists = {
        "m2756_summary": (m2756_dir / "summary.json").exists(),
        "m2756_localization_rows": (m2756_dir / "failure_localization_rows.csv").exists(),
        "m2756_guardrail_rows": (m2756_dir / "guardrail_context_rows.csv").exists(),
        "m2756_actor_rows": (m2756_dir / "actor_contract_guard_rows.csv").exists(),
        "m2756_claim_rows": (m2756_dir / "claim_boundary_rows.csv").exists(),
        "m2756_gate_rows": (m2756_dir / "gate_matrix.csv").exists(),
        "m2758_design": m2758_design.exists(),
        "m2753_candidate_rows": (m2753_dir / "cross_axis_candidate_rows.csv").exists(),
        "m2753_resolution_rows": (m2753_dir / "execution_candidate_resolution_rows.csv").exists(),
        "m1690_workload": m1690_workload.exists(),
        "executable_specs": executable_specs.exists(),
        "follow_up_manifest": follow_up_manifest.exists(),
    }
    return {
        "m2756_dir": str(m2756_dir),
        "m2758_design": str(m2758_design),
        "m2753_dir": str(m2753_dir),
        "m1690_workload": str(m1690_workload),
        "executable_specs": str(executable_specs),
        "source_exists": source_exists,
        "m2756_summary": read_json(m2756_dir / "summary.json") if source_exists["m2756_summary"] else {},
        "m2758_design_text": m2758_design.read_text(encoding="utf-8") if m2758_design.exists() else "",
        "localization_rows": localization_rows,
        "guardrail_rows": read_csv_rows(m2756_dir / "guardrail_context_rows.csv"),
        "actor_rows": read_csv_rows(m2756_dir / "actor_contract_guard_rows.csv"),
        "claim_rows": read_csv_rows(m2756_dir / "claim_boundary_rows.csv"),
        "gate_rows": read_csv_rows(m2756_dir / "gate_matrix.csv"),
        "m2753_candidate_by_candidate_id": {str(row.get("candidate_id", "")): row for row in m2753_candidate_rows},
        "m2753_resolution_by_resolution_id": {str(row.get("resolution_id", "")): row for row in m2753_resolution_rows},
        "m2753_resolution_by_candidate_id": {str(row.get("candidate_id", "")): row for row in m2753_resolution_rows},
        "m1690_workload_by_workload_id": {str(row.get("workload_id", "")): row for row in m1690_workload_rows},
        "m1690_workload_by_task_source_id": {str(row.get("task_source_id", "")): row for row in m1690_workload_rows},
        "follow_up_manifest": str(follow_up_manifest),
    }


def build_probe_candidate_resolution_rows(source: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]]]:
    rows: list[dict[str, Any]] = []
    resolved_sources: dict[str, dict[str, str]] = {}
    for index, localization in enumerate(source["localization_rows"], start=1):
        candidate_id = str(localization.get("candidate_id", ""))
        source_resolution_id = str(localization.get("resolution_id", ""))
        m2753_candidate = source["m2753_candidate_by_candidate_id"].get(candidate_id, {})
        m2753_resolution = source["m2753_resolution_by_resolution_id"].get(source_resolution_id) or source[
            "m2753_resolution_by_candidate_id"
        ].get(candidate_id, {})
        m1690_workload = source["m1690_workload_by_workload_id"].get(str(localization.get("workload_id", ""))) or source[
            "m1690_workload_by_task_source_id"
        ].get(str(localization.get("task_source_id", "")), {})
        profile_config_path = str(m2753_resolution.get("profile_config_path") or m2753_candidate.get("profile_config_path", ""))
        checkpoint_path = str(m2753_resolution.get("checkpoint_path") or m2753_candidate.get("checkpoint_path", ""))
        hidden_oracle_required = any(
            _bool(localization.get(key, False))
            for key in ["hidden_oracle_actor_input_required", "actor_visible_allowed"]
        )
        label_visible = any(
            _bool(localization.get(key, False))
            for key in [
                "localization_labels_actor_visible",
                "stress_axis_labels_actor_visible",
                "source_edge_labels_actor_visible",
                "success_progress_labels_actor_visible",
                "verdict_labels_actor_visible",
            ]
        )
        admitted = bool(
            m2753_candidate
            and m2753_resolution
            and m1690_workload
            and str(localization.get("profile_name", "")) == CANONICAL_PROFILE
            and _bool(localization.get("candidate_admitted", False))
            and not _bool(localization.get("prior_panel_excluded", False))
            and profile_config_path
            and checkpoint_path
            and Path(profile_config_path).exists()
            and Path(checkpoint_path).exists()
            and not hidden_oracle_required
            and not label_visible
        )
        failure_reasons = []
        if not m2753_candidate:
            failure_reasons.append("missing_m2753_candidate_metadata")
        if not m2753_resolution:
            failure_reasons.append("missing_m2753_resolution_metadata")
        if not m1690_workload:
            failure_reasons.append("missing_m1690_workload_metadata")
        if str(localization.get("profile_name", "")) != CANONICAL_PROFILE:
            failure_reasons.append("non_canonical_profile")
        if _bool(localization.get("prior_panel_excluded", False)):
            failure_reasons.append("prior_panel_excluded")
        if not profile_config_path or not Path(profile_config_path).exists():
            failure_reasons.append("missing_profile_config_path")
        if not checkpoint_path or not Path(checkpoint_path).exists():
            failure_reasons.append("missing_checkpoint_path")
        if hidden_oracle_required:
            failure_reasons.append("hidden_or_oracle_actor_input_required")
        if label_visible:
            failure_reasons.append("actor_visible_diagnostic_labels")
        probe_resolution_id = f"m2759-probe-resolution-{index:04d}"
        row = {
            "probe_resolution_id": probe_resolution_id,
            "localization_id": localization.get("localization_id", ""),
            "candidate_id": candidate_id,
            "source_resolution_id": source_resolution_id,
            "task_source_id": localization.get("task_source_id", ""),
            "workload_id": localization.get("workload_id", ""),
            "profile_name": localization.get("profile_name", ""),
            "task_family": localization.get("task_family", ""),
            "source_edge": localization.get("source_edge", ""),
            "stress_axis_primary": localization.get("stress_axis_primary", ""),
            "stress_axis_tags": localization.get("stress_axis_tags", ""),
            "failure_family": localization.get("failure_family", ""),
            "clearance_sign": localization.get("clearance_sign", ""),
            "source_termination_reason": localization.get("termination_reason", ""),
            "source_min_clearance_margin": localization.get("min_clearance_margin", ""),
            "profile_config_path": profile_config_path,
            "checkpoint_path": checkpoint_path,
            "resolution_status": "resolved_to_m2756_localized_m2753_l3_workload" if admitted else "unresolved_or_not_admitted",
            "execution_admitted": admitted,
            "execution_planned": admitted,
            "failure_reason": ";".join(failure_reasons),
            "actor_contract_shape_72_action_3": True,
            "hidden_oracle_actor_input_required": False,
            "localization_labels_actor_visible": False,
            "action_response_labels_actor_visible": False,
            "containment_labels_actor_visible": False,
            "mechanism_tags_actor_visible": False,
            "stress_axis_labels_actor_visible": False,
            "source_edge_labels_actor_visible": False,
            "success_progress_labels_actor_visible": False,
            "verdict_labels_actor_visible": False,
            "guardrail_execution": False,
            "protected_rows_in_success_denominator": False,
            "diagnostic_only_no_verdict": True,
            "ranking_run": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        rows.append(row)
        if admitted:
            resolved_source = dict(m1690_workload)
            resolved_source.update(m2753_candidate)
            resolved_source.update(
                {
                    "profile_config_path": profile_config_path,
                    "checkpoint_path": checkpoint_path,
                    "candidate_id": candidate_id,
                    "resolution_id": source_resolution_id,
                    "failure_family": str(localization.get("failure_family", "")),
                }
            )
            resolved_sources[probe_resolution_id] = resolved_source
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
            "engineering_controller_route_a_post_cross_axis_negative_action_response_containment_probe_execution_pass"
            if status_pass
            else "engineering_controller_route_a_post_cross_axis_negative_action_response_containment_probe_execution_incomplete_or_fail"
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
        "m2759_eval_seed": int(eval_seed),
        "probe_resolution_id": resolution.get("probe_resolution_id", ""),
        "localization_id": resolution.get("localization_id", ""),
        "candidate_id": resolution.get("candidate_id", ""),
        "source_resolution_id": resolution.get("source_resolution_id", ""),
        "failure_family": resolution.get("failure_family", ""),
        "clearance_sign": resolution.get("clearance_sign", ""),
        "source_termination_reason": resolution.get("source_termination_reason", ""),
        "source_min_clearance_margin": resolution.get("source_min_clearance_margin", ""),
        "bounded_action_response_containment_probe": True,
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
            "m2759_eval_seed": int(eval_seed),
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
    containment_rows: list[dict[str, Any]],
    mechanism_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    write_csv_rows(paths["action_response_probe_rows"], action_rows, fieldnames=ACTION_RESPONSE_FIELDNAMES)
    write_csv_rows(paths["containment_probe_rows"], containment_rows, fieldnames=CONTAINMENT_FIELDNAMES)
    write_csv_rows(paths["mechanism_context_rows"], mechanism_rows, fieldnames=MECHANISM_FIELDNAMES)
    write_csv_rows(paths["guardrail_context_rows"], guardrail_rows, fieldnames=GUARDRAIL_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_guard_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)


def build_action_response_probe_rows(execution_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(execution_rows, start=1):
        plan_first_error = _float(row.get("plan_first_action_error_mean"))
        action_rate_mean = _float(row.get("action_rate_mean"))
        plan_rate = _float(row.get("plan_action_rate_mean"))
        speed_response = _float(row.get("speed_mean"))
        yaw_response = _float(row.get("max_abs_yaw_rate"))
        beta_response = _float(row.get("beta_abs_peak") or row.get("max_abs_beta"))
        finite_values = [plan_first_error, action_rate_mean, plan_rate, speed_response, yaw_response, beta_response]
        rows.append(
            {
                "probe_id": f"m2759-action-response-probe-{index:04d}",
                "probe_resolution_id": row.get("probe_resolution_id", ""),
                "candidate_id": row.get("candidate_id", ""),
                "localization_id": row.get("localization_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "failure_family": row.get("failure_family", ""),
                "previous_command": _finite_or_blank(plan_rate),
                "current_action": _finite_or_blank(action_rate_mean),
                "actuator_lag_proxy": _finite_or_blank(plan_first_error),
                "actuator_error_proxy": _finite_or_blank(plan_first_error),
                "action_rate_mean": _finite_or_blank(action_rate_mean),
                "action_rate_peak": _finite_or_blank(max(_finite_or_zero(action_rate_mean), _finite_or_zero(plan_rate))),
                "command_response_phase_lag_proxy": _finite_or_blank(_mean_finite([plan_first_error, action_rate_mean])),
                "speed_response_proxy": _finite_or_blank(speed_response),
                "yaw_response_proxy": _finite_or_blank(yaw_response),
                "beta_response_proxy": _finite_or_blank(beta_response),
                "plan_first_action_error_proxy": _finite_or_blank(plan_first_error),
                "finite_metric": all(_is_finite(value) for value in finite_values),
                "action_response_labels_actor_visible": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_containment_probe_rows(execution_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(execution_rows, start=1):
        min_clearance = _float(row.get("min_clearance_margin"))
        overshoot = _float(row.get("max_off_track_overshoot"))
        impact_speed = _float(row.get("impact_speed_proxy") or row.get("impact_speed_mps"))
        impact_severity = _float(row.get("impact_severity_proxy"))
        rows.append(
            {
                "probe_id": f"m2759-containment-probe-{index:04d}",
                "probe_resolution_id": row.get("probe_resolution_id", ""),
                "candidate_id": row.get("candidate_id", ""),
                "localization_id": row.get("localization_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "failure_family": row.get("failure_family", ""),
                "termination_reason": row.get("termination_reason", ""),
                "min_clearance_margin": _finite_or_blank(min_clearance),
                "clearance_sign": row.get("clearance_sign", ""),
                "obstacle_completed": _bool(row.get("obstacle_completed", False)),
                "max_off_track_overshoot": _finite_or_blank(overshoot),
                "time_to_first_off_track_s": _finite_or_blank(_float(row.get("time_to_first_off_track_s"))),
                "off_track_severity_proxy": _finite_or_blank(_float(row.get("off_track_severity_proxy"))),
                "impact_speed_proxy": _finite_or_blank(impact_speed),
                "impact_severity_proxy": _finite_or_blank(impact_severity),
                "recoverability_window_success": _bool(row.get("recoverability_window_success", False)),
                "post_event_speed_proxy": _finite_or_blank(_float(row.get("post_event_speed_mps"))),
                "post_event_yaw_proxy": _finite_or_blank(_float(row.get("post_event_yaw_rate_abs"))),
                "post_event_offtrack_proxy": _finite_or_blank(_float(row.get("post_event_offtrack_overshoot"))),
                "containment_failure_flag": str(row.get("termination_reason", "")) == "off_track" or _finite_or_zero(overshoot) > 0.0,
                "collision_risk_flag": _bool(row.get("collision", False)) or _finite_or_zero(min_clearance) < 0.0,
                "containment_labels_actor_visible": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_mechanism_context_rows(
    resolution_rows: list[Mapping[str, Any]],
    execution_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    execution_by_resolution = {str(row.get("probe_resolution_id", "")): row for row in execution_rows}
    rows: list[dict[str, Any]] = []
    for resolution in resolution_rows:
        execution = execution_by_resolution.get(str(resolution.get("probe_resolution_id", "")), {})
        tags = mechanism_tags(resolution, execution)
        for tag in tags:
            rows.append(
                {
                    "mechanism_context_id": f"m2759-mechanism-context-{len(rows) + 1:04d}",
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


def mechanism_tags(resolution: Mapping[str, Any], execution: Mapping[str, Any]) -> list[str]:
    tags = [str(resolution.get("failure_family", ""))]
    termination = str(execution.get("termination_reason") or resolution.get("source_termination_reason", ""))
    if termination == "off_track":
        tags.append("track_containment_context")
    if _bool(execution.get("collision", False)) or str(resolution.get("failure_family", "")) == "collision_negative_clearance":
        tags.append("obstacle_timing_context")
    plan_error = _float(execution.get("plan_first_action_error_mean"))
    action_rate = _float(execution.get("action_rate_mean"))
    if _finite_or_zero(plan_error) > 0.0 or _finite_or_zero(action_rate) > 0.0:
        tags.append("action_response_mismatch_context")
    if len(set(tags)) >= 3:
        tags.append("mixed_mechanism_context")
    return [tag for tag in dict.fromkeys(tags) if tag in ALLOWED_MECHANISM_TAGS]


def build_guardrail_context_rows(guardrail_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(guardrail_rows, start=1):
        rows.append(
            {
                "m2759_guardrail_id": f"m2759-guardrail-context-{index:04d}",
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
) -> list[dict[str, Any]]:
    all_rows: list[Mapping[str, Any]] = resolution_rows + artifact_rows["probe_execution_rows"] + artifact_rows["probe_execution_failure_rows"]
    actor_rows = source["actor_rows"]
    obs_status = actor_observed_expected_pass(actor_rows, "p0_observation_dim", "72", "72")
    action_status = actor_observed_expected_pass(actor_rows, "action_dim", "3", "3")
    checks = [
        ("p0_observation_dim", 72 if obs_status else "missing_or_failed", 72, obs_status),
        ("action_dim", 3 if action_status else "missing_or_failed", 3, action_status),
        ("hidden_oracle_actor_input_detected", any_flag(all_rows, "hidden_oracle_actor_input_required"), False, not any_flag(all_rows, "hidden_oracle_actor_input_required")),
        ("actor_input_contract_changed", any_flag(all_rows, "actor_input_contract_changed"), False, not any_flag(all_rows, "actor_input_contract_changed")),
        ("diagnostic_labels_actor_visible", any_label_actor_visible(all_rows), False, not any_label_actor_visible(all_rows)),
        ("guardrails_actor_visible", any_flag(guardrail_rows, "actor_visible_allowed"), False, not any_flag(guardrail_rows, "actor_visible_allowed")),
    ]
    return [actor_guard(f"m2759-actor-guard-{index:04d}", family, observed, expected, status) for index, (family, observed, expected, status) in enumerate(checks, start=1)]


def actor_observed_expected_pass(rows: list[Mapping[str, Any]], family: str, observed: str, expected: str) -> bool:
    for row in rows:
        if str(row.get("guard_family", "")) == family:
            return str(row.get("observed", "")) == observed and str(row.get("expected", "")) == expected and _bool(row.get("status_pass", False))
    return False


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


def build_claim_boundary_rows(*, follow_up_manifest_registered: bool, artifacts_present: bool) -> list[dict[str, Any]]:
    claims = [
        ("route_a_probe_artifact_completeness", True, artifacts_present, "M2759 complete probe artifacts"),
        ("result_audit_follow_up_registered", True, follow_up_manifest_registered, "M2760 result-audit manifest"),
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
            "claim_id": f"m2759-claim-{index:04d}",
            "claim_family": family,
            "allowed_in_m2759": allowed,
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
    checks = [
        ("source_artifacts_present", "lineage", all(source["source_exists"].values()), source["source_exists"], "M2756 M2758 M2753 resolver specs and M2760 manifest present", "lineage_invalid"),
        ("m2756_summary_status_pass", "lineage", _bool(source["m2756_summary"].get("status_pass", False)), source["m2756_summary"].get("status_pass", False), True, "lineage_invalid"),
        ("m2758_design_present", "lineage", "M2759" in source["m2758_design_text"], "M2759" in source["m2758_design_text"], True, "lineage_invalid"),
        ("localized_candidate_count", "candidate_surface", len(resolution_rows) == EXPECTED_CANDIDATE_COUNT, len(resolution_rows), EXPECTED_CANDIDATE_COUNT, "scenario_sampling_failure"),
        ("collision_negative_clearance_count", "candidate_surface", count_eq(resolution_rows, "failure_family", "collision_negative_clearance") == EXPECTED_COLLISION_NEGATIVE_CLEARANCE_COUNT, count_eq(resolution_rows, "failure_family", "collision_negative_clearance"), EXPECTED_COLLISION_NEGATIVE_CLEARANCE_COUNT, "scenario_sampling_failure"),
        ("offtrack_positive_clearance_count", "candidate_surface", count_eq(resolution_rows, "failure_family", "offtrack_positive_clearance") == EXPECTED_OFFTRACK_POSITIVE_CLEARANCE_COUNT, count_eq(resolution_rows, "failure_family", "offtrack_positive_clearance"), EXPECTED_OFFTRACK_POSITIVE_CLEARANCE_COUNT, "scenario_sampling_failure"),
        ("l3_profile_only", "candidate_surface", {row["profile_name"] for row in resolution_rows} == {CANONICAL_PROFILE}, sorted({row["profile_name"] for row in resolution_rows}), CANONICAL_PROFILE, "contract_violation"),
        ("all_candidates_resolved_or_accounted", "execution", len(execution_rows) + len(failure_rows) == len(resolution_rows), len(execution_rows) + len(failure_rows), len(resolution_rows), "lineage_invalid"),
        ("new_probe_execution_rows_present", "execution", bool(execution_rows), len(execution_rows), ">0", "behavior_regression"),
        ("all_selected_metrics_finite", "metric", selected_metrics_are_finite(execution_rows) if execution_rows else False, execution_summary.get("all_selected_metrics_finite"), True, "metric_artifact"),
        ("guardrail_rows_carried", "guardrail", len(guardrail_rows) == EXPECTED_GUARDRAIL_COUNT, len(guardrail_rows), EXPECTED_GUARDRAIL_COUNT, "lineage_invalid"),
        ("guardrail_execution_false", "guardrail", not any_flag(guardrail_rows, "execution_run"), any_flag(guardrail_rows, "execution_run"), False, "proof_washout"),
        ("protected_denominator_false", "guardrail", not any_flag(all_exec_rows + guardrail_rows, "protected_rows_in_success_denominator"), any_flag(all_exec_rows + guardrail_rows, "protected_rows_in_success_denominator"), False, "proof_washout"),
        ("action_response_rows_written", "metric", len(action_rows) == len(execution_rows), len(action_rows), len(execution_rows), "metric_artifact"),
        ("containment_rows_written", "metric", len(containment_rows) == len(execution_rows), len(containment_rows), len(execution_rows), "metric_artifact"),
        ("mechanism_rows_cover_candidates", "metric", len({row["probe_resolution_id"] for row in mechanism_rows}) == len(resolution_rows), len({row["probe_resolution_id"] for row in mechanism_rows}), len(resolution_rows), "metric_artifact"),
        ("mechanism_tags_actor_invisible", "contract", not any_flag(mechanism_rows, "mechanism_tag_actor_visible"), any_flag(mechanism_rows, "mechanism_tag_actor_visible"), False, "contract_violation"),
        ("actor_contract_guards_pass", "contract", all(_bool(row["status_pass"]) for row in actor_guard_rows), "all_pass" if all(_bool(row["status_pass"]) for row in actor_guard_rows) else actor_guard_rows, "all_pass", "contract_violation"),
        ("hidden_oracle_actor_input_false", "contract", not any_flag(all_exec_rows + resolution_rows, "hidden_oracle_actor_input_required"), any_flag(all_exec_rows + resolution_rows, "hidden_oracle_actor_input_required"), False, "contract_violation"),
        ("diagnostic_labels_actor_visible_false", "contract", not any_label_actor_visible(all_exec_rows + resolution_rows), any_label_actor_visible(all_exec_rows + resolution_rows), False, "contract_violation"),
        ("forbidden_execution_false", "claim", not any(forbidden_execution_flag(row) for row in all_exec_rows), "forbidden flag present" if any(forbidden_execution_flag(row) for row in all_exec_rows) else False, False, "proof_washout"),
        ("claim_boundary_rows_pass", "claim", all(_bool(row["status_pass"]) for row in claim_rows), "all_pass" if all(_bool(row["status_pass"]) for row in claim_rows) else claim_rows, "all_pass", "proof_washout"),
        ("required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True, "lineage_invalid"),
    ]
    return [gate(*check) for check in checks]


def gate(
    gate_id: str,
    family: str,
    status_pass: bool,
    observed: Any,
    expected: Any,
    failure_type: str,
) -> dict[str, Any]:
    return {
        "gate_id": f"m2759-gate-{gate_id}",
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
            "engineering_controller_route_a_post_cross_axis_negative_action_response_containment_probe_bounded_execution_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_post_cross_axis_negative_action_response_containment_probe_bounded_execution_preflight_fail"
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
        "containment_probe_row_count": len(containment_rows),
        "mechanism_context_row_count": len(mechanism_rows),
        "mechanism_tags": sorted({str(row.get("mechanism_tag", "")) for row in mechanism_rows}),
        "diagnostic_success_count": sum(1 for row in execution_rows if _episode_success(row)),
        "diagnostic_collision_count": sum(1 for row in execution_rows if _bool(row.get("collision", False))),
        "diagnostic_offtrack_count": sum(1 for row in execution_rows if str(row.get("termination_reason", "")) == "off_track"),
        "diagnostic_termination_counts": dict(sorted(termination_counts.items())),
        "all_selected_metrics_finite": bool(execution_summary.get("all_selected_metrics_finite", False)),
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
        "actor_input_contract_changed": any_flag(execution_rows + failure_rows, "actor_input_contract_changed"),
        "hidden_oracle_actor_input_required": any_flag(resolution_rows + execution_rows + failure_rows, "hidden_oracle_actor_input_required"),
        "diagnostic_labels_actor_visible": any_label_actor_visible(resolution_rows + execution_rows + failure_rows + mechanism_rows),
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
        "# M2759 Engineering Controller Route A Post-Cross-Axis Negative Action-Response Containment Probe Bounded Execution Preflight",
        "",
        "## Metadata",
        "",
        f"- status: {'completed' if summary['status_pass'] else 'failed'}",
        f"- result class: `{summary['result_class']}`",
        f"- localized candidates: {summary['localized_candidate_count']}",
        f"- resolved candidates: {summary['resolved_candidate_count']}/{summary['localized_candidate_count']}",
        f"- execution rows: {summary['probe_execution_row_count']}",
        f"- failure rows: {summary['probe_execution_failure_row_count']}",
        f"- accounted candidates: {summary['accounted_candidate_count']}/{summary['localized_candidate_count']}",
        f"- collision negative-clearance rows: {summary['collision_negative_clearance_count']}",
        f"- offtrack positive-clearance rows: {summary['offtrack_positive_clearance_count']}",
        f"- guardrail context rows: {summary['guardrail_context_row_count']}",
        f"- action-response probe rows: {summary['action_response_probe_row_count']}",
        f"- containment probe rows: {summary['containment_probe_row_count']}",
        f"- mechanism context rows: {summary['mechanism_context_row_count']}",
        f"- diagnostic outcomes: success {summary['diagnostic_success_count']} collision {summary['diagnostic_collision_count']} offtrack {summary['diagnostic_offtrack_count']}",
        f"- diagnostic termination counts: {summary['diagnostic_termination_counts']}",
        f"- gate matrix pass: {summary['gate_matrix_pass']}",
        f"- next blocker: `{summary['next_blocker']}`",
        f"- follow-up manifest: `{summary['follow_up_manifest']}`",
        "",
        "## Boundary",
        "",
        "M2759 is a bounded diagnostic execution preflight. It executes only the",
        "12 M2756 localized candidate rows and carries the 31 M2756 guardrails as",
        "non-executed interpretation boundaries. It writes evaluator-only",
        "action-response, containment, and mechanism-context artifacts. It does",
        "not rank rows, select a winner, validate driver performance, or make",
        "paper/self-ID/current-sim/high-fidelity/full-driver claims.",
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


def count_eq(rows: list[Mapping[str, Any]], key: str, expected: str) -> int:
    return sum(1 for row in rows if str(row.get(key, "")) == expected)


def any_label_actor_visible(rows: list[Mapping[str, Any]]) -> bool:
    label_keys = [
        "localization_labels_actor_visible",
        "action_response_labels_actor_visible",
        "containment_labels_actor_visible",
        "mechanism_tags_actor_visible",
        "mechanism_tag_actor_visible",
        "stress_axis_labels_actor_visible",
        "source_edge_labels_actor_visible",
        "success_progress_labels_actor_visible",
        "verdict_labels_actor_visible",
    ]
    return any(any(_bool(row.get(key, False)) for key in label_keys) for row in rows)


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
    run_post_cross_axis_negative_action_response_containment_probe_bounded_execution_preflight(
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
