"""Run M2807 post-clearance negative non-same-repair cross-axis bounded execution preflight.

M2807 consumes the M2806 design and the M1690 executable workload matrix. It
selects exactly 12 fixed non-same-repair L3_online_gru workload rows, excludes
M2737/M2746/M2753 prior-surface task sources plus the M2799/M2801 same-clearance
repair route, runs one bounded closed-loop diagnostic episode per resolved row,
and carries protected/HF3 blockers as guardrails. It does not rank, validate,
train, promote, or claim driver performance.
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
    DEFAULT_EXECUTABLE_WORKLOAD,
    load_executable_specs,
    read_csv_rows,
    run_workload_cell,
    selected_metrics_are_finite,
    write_run_state,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2807-engineering-controller-route-a-post-clearance-negative-non-same-repair-cross-axis-bounded-execution-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2808-engineering-controller-route-a-post-clearance-negative-non-same-repair-cross-axis-bounded-execution-result-audit"
)
DEFAULT_M2806_DESIGN = Path(
    "docs/m2806-engineering-controller-route-a-post-clearance-negative-non-same-repair-evidence-route-design.md"
)
DEFAULT_M2746_DIR = Path(
    "runs/m2746_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_preflight"
)
DEFAULT_M2737_DIR = Path(
    "runs/m2737_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_bounded_execution_preflight"
)
DEFAULT_M2753_DIR = Path(
    "runs/m2753_engineering_controller_route_a_cross_axis_stress_generalization_bounded_execution_preflight"
)
DEFAULT_M2804_DIR = Path(
    "runs/m2804_engineering_controller_route_a_post_clearance_corrective_readiness_index"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2807_engineering_controller_route_a_post_clearance_negative_non_same_repair_cross_axis_bounded_execution_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2807-engineering-controller-route-a-post-clearance-negative-non-same-repair-cross-axis-bounded-execution-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2808-engineering-controller-route-a-post-clearance-negative-non-same-repair-cross-axis-bounded-execution-result-audit.json"
)
DEFAULT_EVAL_SEED_BASE = 280700
CANONICAL_PROFILE = "L3_online_gru"

SELECTED_TASK_SOURCES: tuple[tuple[str, str, str, str], ...] = (
    ("m1680-spec-0014", "T4", "actuator_delay_step|capability_step_up", "actuator_delay_or_response"),
    ("m1680-spec-0016", "T4", "capability_step_down|t4_actuator_delay_response", "capability_step_or_authority"),
    ("m1680-spec-0018", "T4", "t4_actuator_delay_response|capability_step_up", "actuator_delay_or_response"),
    ("m1680-spec-0022", "T4", "actuator_delay_step|t4_capability_step_temporal", "actuator_delay_or_response"),
    ("m1680-spec-0026", "T4", "t4_capability_step_temporal|capability_step_down", "capability_step_or_authority"),
    ("m1680-spec-0032", "T4", "t4_actuator_delay_response|capability_step_up", "actuator_delay_or_response"),
    ("m1680-spec-0048", "T5", "curved_boundary_obstacle|t5_boundary_axis_retarget", "late_boundary_or_near_boundary"),
    ("m1680-spec-0051", "T5", "actuator_delay_step|t5_near_boundary_warmup", "actuator_delay_or_response"),
    ("m1680-spec-0052", "T5", "capability_step_down|t5_near_boundary_warmup", "capability_step_or_authority"),
    ("m1680-spec-0053", "T5", "curved_boundary_obstacle|t5_boundary_axis_retarget", "curved_or_retargeted_obstacle"),
    ("m1680-spec-0058", "T5", "capability_step_down|t5_near_boundary_warmup", "capability_step_or_authority"),
    ("m1680-spec-0063", "T5", "actuator_delay_step|t5_near_boundary_warmup", "actuator_delay_or_response"),
)
EXPECTED_CANDIDATE_COUNT = len(SELECTED_TASK_SOURCES)
EXPECTED_PRIOR_SURFACE_MIN_COUNT = 21

STRESS_AXIS_TAGS: dict[str, tuple[str, ...]] = {
    "m1680-spec-0014": ("actuator_delay_or_response", "capability_step_or_authority"),
    "m1680-spec-0016": ("actuator_delay_or_response", "capability_step_or_authority"),
    "m1680-spec-0018": ("actuator_delay_or_response", "capability_step_or_authority"),
    "m1680-spec-0022": ("actuator_delay_or_response",),
    "m1680-spec-0026": ("capability_step_or_authority",),
    "m1680-spec-0032": ("actuator_delay_or_response", "capability_step_or_authority"),
    "m1680-spec-0048": ("late_boundary_or_near_boundary", "curved_or_retargeted_obstacle"),
    "m1680-spec-0051": ("actuator_delay_or_response", "late_boundary_or_near_boundary"),
    "m1680-spec-0052": ("capability_step_or_authority", "late_boundary_or_near_boundary"),
    "m1680-spec-0053": ("late_boundary_or_near_boundary", "curved_or_retargeted_obstacle"),
    "m1680-spec-0058": ("capability_step_or_authority", "late_boundary_or_near_boundary"),
    "m1680-spec-0063": ("actuator_delay_or_response", "late_boundary_or_near_boundary"),
}

CLAIM_SCOPE = (
    "M2807 Route A post-clearance negative non-same-repair cross-axis bounded execution preflight "
    "only; reset, step, rollout, and policy actions may be recorded for the 12 "
    "selected non-same-repair M1690 L3_online_gru rows, while M2737/M2746/M2753 "
    "prior-surface rows, M2799/M2801 same-clearance repair rows, protected "
    "blocker rows, and HF3 blocker rows remain guardrails outside execution "
    "and success denominators. No replay, "
    "validation, training, PPO, source build, adapter probe, external "
    "simulation, ranking, winner selection, promotion, success-rate verdict, "
    "repair-success, driver-performance, paper, finite-window-vs-GRU, "
    "current-sim, high-fidelity validation, full ideal driver, or self-ID "
    "claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, "
    "controller-family ranking, source-family ranking, task-family ranking, "
    "stress-axis ranking, profile ranking, winner selection, checkpoint "
    "promotion, success-rate verdict, paper evidence, finite-window-vs-GRU "
    "conclusion, current-sim verdict, high-fidelity validation readiness or "
    "result, full ideal driver completion, or level3 self-identification"
)

CANDIDATE_FIELDNAMES = [
    "candidate_id",
    "task_source_id",
    "workload_id",
    "profile_name",
    "task_family",
    "source_edge",
    "window_tag",
    "strata",
    "stress_axis_primary",
    "stress_axis_tags",
    "profile_config_path",
    "checkpoint_path",
    "config_exists",
    "checkpoint_exists",
    "prior_panel_excluded",
    "candidate_admitted",
    "candidate_failure_reason",
    "actor_contract_shape_72_action_3",
    "hidden_oracle_actor_input_required",
    "stress_axis_labels_actor_visible",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
RESOLUTION_FIELDNAMES = [
    "resolution_id",
    "candidate_id",
    "task_source_id",
    "workload_id",
    "profile_name",
    "task_family",
    "source_edge",
    "stress_axis_primary",
    "stress_axis_tags",
    "resolution_status",
    "profile_config_path",
    "checkpoint_path",
    "execution_admitted",
    "execution_planned",
    "failure_reason",
    "actor_contract_shape_72_action_3",
    "hidden_oracle_actor_input_required",
    "stress_axis_labels_actor_visible",
    "diagnostic_only_no_verdict",
    "ranking_run",
    "claim_boundary",
]
FAILURE_FIELDNAMES = [
    "resolution_id",
    "candidate_id",
    "task_source_id",
    "workload_id",
    "profile_name",
    "task_family",
    "source_edge",
    "stress_axis_primary",
    "stress_axis_tags",
    "m2807_eval_seed",
    "error_type",
    "error_message",
    "environment_reset_run",
    "environment_step_run",
    "policy_action_run",
    "policy_rollout_run",
    "prior_panel_execution",
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
    "stress_axis_labels_actor_visible",
    "blocker_labels_actor_visible",
    "route_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "protected_rows_in_success_denominator",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
STRESS_AGGREGATE_FIELDNAMES = [
    "aggregate_id",
    "stress_axis_tag",
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
PRIOR_EXCLUSION_FIELDNAMES = [
    "exclusion_id",
    "source_panel",
    "task_source_id",
    "row_count",
    "execution_candidate",
    "execution_admitted",
    "execution_run",
    "actor_visible_allowed",
    "ordinary_success_denominator_allowed",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
BLOCKER_GUARD_FIELDNAMES = [
    "guard_id",
    "blocker_id",
    "route",
    "evidence_family",
    "current_status",
    "blocking_count",
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
    "allowed_in_m2807",
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
    "non_same_repair_candidate_rows",
    "execution_candidate_resolution_rows",
    "candidate_execution_rows",
    "candidate_execution_failure_rows",
    "stress_axis_aggregate_rows",
    "prior_surface_exclusion_rows",
    "blocker_guard_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
]


def run_post_clearance_negative_non_same_repair_cross_axis_bounded_execution_preflight(
    *,
    m1690_workload: Path | str = DEFAULT_EXECUTABLE_WORKLOAD,
    m2746_dir: Path | str = DEFAULT_M2746_DIR,
    m2737_dir: Path | str = DEFAULT_M2737_DIR,
    m2753_dir: Path | str = DEFAULT_M2753_DIR,
    m2804_dir: Path | str = DEFAULT_M2804_DIR,
    m2806_design: Path | str = DEFAULT_M2806_DESIGN,
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
        m1690_workload=Path(m1690_workload),
        m2746_dir=Path(m2746_dir),
        m2737_dir=Path(m2737_dir),
        m2753_dir=Path(m2753_dir),
        m2804_dir=Path(m2804_dir),
        m2806_design=Path(m2806_design),
        executable_specs=Path(executable_specs),
        follow_up_manifest=Path(follow_up_manifest),
    )
    prior_exclusion_rows = build_prior_panel_exclusion_rows(source)
    candidate_rows = build_non_same_repair_candidate_rows(source, prior_exclusion_rows)
    resolution_rows, resolved_sources = build_resolution_rows(candidate_rows, source["m1690_by_task_source"])

    write_csv_rows(paths["non_same_repair_candidate_rows"], candidate_rows, fieldnames=CANDIDATE_FIELDNAMES)
    write_csv_rows(paths["prior_surface_exclusion_rows"], prior_exclusion_rows, fieldnames=PRIOR_EXCLUSION_FIELDNAMES)
    write_csv_rows(paths["execution_candidate_resolution_rows"], resolution_rows, fieldnames=RESOLUTION_FIELDNAMES)

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
    stress_axis_aggregate_rows = build_stress_axis_aggregate_rows(
        candidate_rows=candidate_rows,
        episode_rows=artifact_rows["candidate_execution_rows"],
        failure_rows=artifact_rows["candidate_execution_failure_rows"],
    )
    blocker_guard_rows = build_blocker_guard_rows(source["blocker_rows"])
    actor_guard_rows = build_actor_contract_guard_rows(
        candidate_rows=candidate_rows,
        resolution_rows=resolution_rows,
        episode_rows=artifact_rows["candidate_execution_rows"],
        failure_rows=artifact_rows["candidate_execution_failure_rows"],
        prior_exclusion_rows=prior_exclusion_rows,
        blocker_guard_rows=blocker_guard_rows,
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
        candidate_rows=candidate_rows,
        resolution_rows=resolution_rows,
        execution_summary=execution_summary,
        artifact_rows=artifact_rows,
        stress_axis_aggregate_rows=stress_axis_aggregate_rows,
        prior_exclusion_rows=prior_exclusion_rows,
        blocker_guard_rows=blocker_guard_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        required_artifacts_present=False,
    )
    write_derived_outputs(paths, stress_axis_aggregate_rows, blocker_guard_rows, actor_guard_rows, claim_rows, gate_rows)

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
        candidate_rows=candidate_rows,
        resolution_rows=resolution_rows,
        execution_summary=execution_summary,
        artifact_rows=load_execution_artifact_rows(paths),
        stress_axis_aggregate_rows=stress_axis_aggregate_rows,
        prior_exclusion_rows=prior_exclusion_rows,
        blocker_guard_rows=blocker_guard_rows,
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
        candidate_rows=candidate_rows,
        resolution_rows=resolution_rows,
        execution_summary=execution_summary,
        artifact_rows=load_execution_artifact_rows(paths),
        stress_axis_aggregate_rows=stress_axis_aggregate_rows,
        prior_exclusion_rows=prior_exclusion_rows,
        blocker_guard_rows=blocker_guard_rows,
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
        candidate_rows=candidate_rows,
        resolution_rows=resolution_rows,
        execution_summary=execution_summary,
        artifact_rows=load_execution_artifact_rows(paths),
        stress_axis_aggregate_rows=stress_axis_aggregate_rows,
        prior_exclusion_rows=prior_exclusion_rows,
        blocker_guard_rows=blocker_guard_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        candidate_rows=candidate_rows,
        resolution_rows=resolution_rows,
        execution_summary=execution_summary,
        artifact_rows=load_execution_artifact_rows(paths),
        stress_axis_aggregate_rows=stress_axis_aggregate_rows,
        prior_exclusion_rows=prior_exclusion_rows,
        blocker_guard_rows=blocker_guard_rows,
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
        "non_same_repair_candidate_rows": output_dir / "non_same_repair_candidate_rows.csv",
        "execution_candidate_resolution_rows": output_dir / "execution_candidate_resolution_rows.csv",
        "candidate_execution_rows": output_dir / "candidate_execution_rows.csv",
        "candidate_execution_failure_rows": output_dir / "candidate_execution_failure_rows.csv",
        "stress_axis_aggregate_rows": output_dir / "stress_axis_aggregate_rows.csv",
        "prior_surface_exclusion_rows": output_dir / "prior_surface_exclusion_rows.csv",
        "blocker_guard_rows": output_dir / "blocker_guard_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m1690_workload: Path,
    m2746_dir: Path,
    m2737_dir: Path,
    m2753_dir: Path,
    m2804_dir: Path,
    m2806_design: Path,
    executable_specs: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2806_design": m2806_design,
        "m1690_workload": m1690_workload,
        "m2746_execution_candidate_rows": m2746_dir / "execution_candidate_rows.csv",
        "m2746_candidate_execution_rows": m2746_dir / "candidate_execution_rows.csv",
        "m2737_candidate_execution_rows": m2737_dir / "candidate_execution_rows.csv",
        "m2753_candidate_execution_rows": m2753_dir / "candidate_execution_rows.csv",
        "m2804_blocker_matrix": m2804_dir / "blocker_matrix.csv",
        "m2804_next_action_rows": m2804_dir / "next_action_admission_rows.csv",
        "executable_task_specs": executable_specs,
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    m1690_rows = read_csv_rows(paths["m1690_workload"])
    m1690_by_task_source: dict[str, dict[str, str]] = {}
    for row in m1690_rows:
        if row.get("profile_name") == CANONICAL_PROFILE:
            m1690_by_task_source[str(row.get("task_source_id", ""))] = row
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2806_design_text": paths["m2806_design"].read_text(encoding="utf-8") if source_exists["m2806_design"] else "",
        "m1690_rows": m1690_rows,
        "m1690_by_task_source": m1690_by_task_source,
        "m2746_execution_candidate_rows": read_csv_rows(paths["m2746_execution_candidate_rows"]),
        "m2746_candidate_execution_rows": read_csv_rows(paths["m2746_candidate_execution_rows"]),
        "m2737_candidate_execution_rows": read_csv_rows(paths["m2737_candidate_execution_rows"]),
        "m2753_candidate_execution_rows": read_csv_rows(paths["m2753_candidate_execution_rows"]),
        "blocker_rows": read_csv_rows(paths["m2804_blocker_matrix"]),
        "next_action_rows": read_csv_rows(paths["m2804_next_action_rows"]),
    }


def build_prior_panel_exclusion_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    counts: dict[tuple[str, str], int] = Counter()
    for source_panel, key in (
        ("m2746_execution_candidate_rows", "m2746_execution_candidate_rows"),
        ("m2746_candidate_execution_rows", "m2746_candidate_execution_rows"),
        ("m2737_candidate_execution_rows", "m2737_candidate_execution_rows"),
        ("m2753_candidate_execution_rows", "m2753_candidate_execution_rows"),
    ):
        for row in source[key]:
            task_source_id = str(row.get("task_source_id", ""))
            if task_source_id:
                counts[(source_panel, task_source_id)] += 1

    rows: list[dict[str, Any]] = []
    for index, ((source_panel, task_source_id), row_count) in enumerate(sorted(counts.items()), start=1):
        rows.append(
            {
                "exclusion_id": f"m2807-prior-surface-exclusion-{index:04d}",
                "source_panel": source_panel,
                "task_source_id": task_source_id,
                "row_count": row_count,
                "execution_candidate": False,
                "execution_admitted": False,
                "execution_run": False,
                "actor_visible_allowed": False,
                "ordinary_success_denominator_allowed": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_non_same_repair_candidate_rows(
    source: dict[str, Any], prior_exclusion_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    excluded_task_sources = {str(row["task_source_id"]) for row in prior_exclusion_rows}
    rows: list[dict[str, Any]] = []
    for index, (task_source_id, expected_task_family, expected_source_edge, primary_axis) in enumerate(
        SELECTED_TASK_SOURCES, start=1
    ):
        source_row = source["m1690_by_task_source"].get(task_source_id)
        prior_panel_excluded = task_source_id in excluded_task_sources
        failure_reason = ""
        if source_row is None:
            failure_reason = "selected_task_source_missing_from_m1690_l3_rows"
        elif str(source_row.get("task_family", "")) != expected_task_family:
            failure_reason = "task_family_mismatch"
        elif str(source_row.get("source_edge", "")) != expected_source_edge:
            failure_reason = "source_edge_mismatch"
        elif prior_panel_excluded:
            failure_reason = "prior_panel_task_source_excluded"
        elif str(source_row.get("config_exists", "")) != "True":
            failure_reason = "profile_config_missing"
        elif str(source_row.get("checkpoint_exists", "")) != "True":
            failure_reason = "checkpoint_missing"
        elif _bool(source_row.get("profile_specific_tuning", False)):
            failure_reason = "profile_specific_tuning_detected"
        candidate_admitted = bool(source_row is not None and not failure_reason)
        rows.append(
            {
                "candidate_id": f"m2807-cross-axis-candidate-{index:04d}",
                "task_source_id": task_source_id,
                "workload_id": source_row.get("workload_id", "") if source_row else f"{task_source_id}::{CANONICAL_PROFILE}",
                "profile_name": source_row.get("profile_name", CANONICAL_PROFILE) if source_row else CANONICAL_PROFILE,
                "task_family": source_row.get("task_family", expected_task_family) if source_row else expected_task_family,
                "source_edge": source_row.get("source_edge", expected_source_edge) if source_row else expected_source_edge,
                "window_tag": source_row.get("window_tag", "") if source_row else "",
                "strata": source_row.get("strata", "") if source_row else "",
                "stress_axis_primary": primary_axis,
                "stress_axis_tags": ";".join(STRESS_AXIS_TAGS[task_source_id]),
                "profile_config_path": source_row.get("profile_config_path", "") if source_row else "",
                "checkpoint_path": source_row.get("checkpoint_path", "") if source_row else "",
                "config_exists": _bool(source_row.get("config_exists", False)) if source_row else False,
                "checkpoint_exists": _bool(source_row.get("checkpoint_exists", False)) if source_row else False,
                "prior_panel_excluded": prior_panel_excluded,
                "candidate_admitted": candidate_admitted,
                "candidate_failure_reason": failure_reason,
                "actor_contract_shape_72_action_3": True,
                "hidden_oracle_actor_input_required": False,
                "stress_axis_labels_actor_visible": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_resolution_rows(
    candidate_rows: list[dict[str, Any]], m1690_by_task_source: dict[str, dict[str, str]]
) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]]]:
    rows: list[dict[str, Any]] = []
    resolved_sources: dict[str, dict[str, str]] = {}
    for index, candidate in enumerate(candidate_rows, start=1):
        resolution_id = f"m2807-resolution-{index:04d}"
        task_source_id = str(candidate["task_source_id"])
        source_row = m1690_by_task_source.get(task_source_id)
        execution_admitted = bool(_bool(candidate["candidate_admitted"]) and source_row is not None)
        failure_reason = "" if execution_admitted else str(candidate.get("candidate_failure_reason", "candidate_not_admitted"))
        row = {
            "resolution_id": resolution_id,
            "candidate_id": candidate["candidate_id"],
            "task_source_id": task_source_id,
            "workload_id": candidate["workload_id"],
            "profile_name": candidate["profile_name"],
            "task_family": candidate["task_family"],
            "source_edge": candidate["source_edge"],
            "stress_axis_primary": candidate["stress_axis_primary"],
            "stress_axis_tags": candidate["stress_axis_tags"],
            "resolution_status": "resolved_to_m1690_l3_workload" if execution_admitted else "accounted_by_failure",
            "profile_config_path": candidate["profile_config_path"],
            "checkpoint_path": candidate["checkpoint_path"],
            "execution_admitted": execution_admitted,
            "execution_planned": execution_admitted,
            "failure_reason": failure_reason,
            "actor_contract_shape_72_action_3": True,
            "hidden_oracle_actor_input_required": False,
            "stress_axis_labels_actor_visible": False,
            "diagnostic_only_no_verdict": True,
            "ranking_run": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        rows.append(row)
        if execution_admitted and source_row is not None:
            resolved_sources[resolution_id] = source_row
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
        resolution_id = str(resolution["resolution_id"])
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
            "engineering_controller_route_a_post_clearance_negative_non_same_repair_cross_axis_bounded_execution_pass"
            if status_pass
            else "engineering_controller_route_a_post_clearance_negative_non_same_repair_cross_axis_bounded_execution_incomplete_or_fail"
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
        "m2807_eval_seed": int(eval_seed),
        "resolution_id": resolution.get("resolution_id", ""),
        "candidate_id": resolution.get("candidate_id", ""),
        "bounded_post_clearance_negative_non_same_repair_cross_axis_execution_preflight": True,
        "candidate_surface_count": EXPECTED_CANDIDATE_COUNT,
        "stress_axis_primary": resolution.get("stress_axis_primary", ""),
        "stress_axis_tags": resolution.get("stress_axis_tags", ""),
        "prior_panel_execution": False,
        "protected_blocker_execution": False,
        "hf3_blocker_execution": False,
        "protected_rows_in_success_denominator": False,
        "hidden_oracle_actor_input_required": False,
        "stress_axis_labels_actor_visible": False,
        "blocker_labels_actor_visible": False,
        "route_labels_actor_visible": False,
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
    resolution: Mapping[str, Any], *, eval_seed: int, error_type: str, error_message: str
) -> dict[str, Any]:
    return {
        "resolution_id": resolution.get("resolution_id", ""),
        "candidate_id": resolution.get("candidate_id", ""),
        "task_source_id": resolution.get("task_source_id", ""),
        "workload_id": resolution.get("workload_id", ""),
        "profile_name": resolution.get("profile_name", ""),
        "task_family": resolution.get("task_family", ""),
        "source_edge": resolution.get("source_edge", ""),
        "stress_axis_primary": resolution.get("stress_axis_primary", ""),
        "stress_axis_tags": resolution.get("stress_axis_tags", ""),
        "m2807_eval_seed": int(eval_seed),
        "error_type": error_type,
        "error_message": error_message,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "prior_panel_execution": False,
        "protected_blocker_execution": False,
        "hf3_blocker_execution": False,
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
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_required": False,
        "stress_axis_labels_actor_visible": False,
        "blocker_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "protected_rows_in_success_denominator": False,
        "diagnostic_only_no_verdict": True,
        "claim_boundary": CLAIM_SCOPE,
    }


def load_execution_artifact_rows(paths: dict[str, Path]) -> dict[str, list[dict[str, str]]]:
    return {
        "candidate_execution_rows": read_csv_rows(paths["candidate_execution_rows"]),
        "candidate_execution_failure_rows": read_csv_rows(paths["candidate_execution_failure_rows"]),
    }


def write_derived_outputs(
    paths: dict[str, Path],
    stress_axis_aggregate_rows: list[dict[str, Any]],
    blocker_guard_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    write_csv_rows(paths["stress_axis_aggregate_rows"], stress_axis_aggregate_rows, fieldnames=STRESS_AGGREGATE_FIELDNAMES)
    write_csv_rows(paths["blocker_guard_rows"], blocker_guard_rows, fieldnames=BLOCKER_GUARD_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_guard_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)


def build_stress_axis_aggregate_rows(
    *,
    candidate_rows: list[dict[str, Any]],
    episode_rows: list[dict[str, str]],
    failure_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    candidate_by_id = {str(row["candidate_id"]): row for row in candidate_rows}
    episodes_by_candidate = _group_by(episode_rows, "candidate_id")
    failures_by_candidate = _group_by(failure_rows, "candidate_id")
    rows: list[dict[str, Any]] = []
    for index, tag in enumerate(
        (
            "actuator_delay_or_response",
            "capability_step_or_authority",
            "late_boundary_or_near_boundary",
            "curved_or_retargeted_obstacle",
        ),
        start=1,
    ):
        candidate_ids = [
            str(candidate["candidate_id"])
            for candidate in candidate_rows
            if tag in str(candidate.get("stress_axis_tags", "")).split(";")
        ]
        axis_episodes = [row for candidate_id in candidate_ids for row in episodes_by_candidate.get(candidate_id, [])]
        axis_failures = [row for candidate_id in candidate_ids for row in failures_by_candidate.get(candidate_id, [])]
        candidate_count = len([candidate_by_id[candidate_id] for candidate_id in candidate_ids if candidate_id in candidate_by_id])
        rows.append(
            {
                "aggregate_id": f"m2807-stress-axis-aggregate-{index:04d}",
                "stress_axis_tag": tag,
                "candidate_count": candidate_count,
                "episode_count": len(axis_episodes),
                "failure_count": len(axis_failures),
                "accounted_count": len(axis_episodes) + len(axis_failures),
                "success_rate_diagnostic": mean_bool(axis_episodes, "success"),
                "collision_rate_diagnostic": mean_bool(axis_episodes, "collision"),
                "offtrack_rate_diagnostic": mean_eq(axis_episodes, "termination_reason", "off_track"),
                "clearance_margin_mean": mean_float(axis_episodes, "min_clearance_margin"),
                "return_mean": mean_float(axis_episodes, "return"),
                "all_selected_metrics_finite": selected_metrics_are_finite(axis_episodes) if axis_episodes else False,
                "ranking_claim_made": False,
                "success_rate_verdict_claim_made": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_blocker_guard_rows(blocker_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, blocker in enumerate(blocker_rows, start=1):
        rows.append(
            {
                "guard_id": f"m2807-blocker-guard-{index:04d}",
                "blocker_id": blocker.get("blocker_id", ""),
                "route": blocker.get("route", ""),
                "evidence_family": blocker.get("evidence_family", ""),
                "current_status": blocker.get("current_status", ""),
                "blocking_count": blocker.get("blocking_count", ""),
                "execution_candidate": False,
                "execution_admitted": False,
                "execution_run": False,
                "protected_rows_in_success_denominator": False,
                "actor_visible_allowed": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_guard_rows(
    *,
    candidate_rows: list[dict[str, Any]],
    resolution_rows: list[dict[str, Any]],
    episode_rows: list[dict[str, str]],
    failure_rows: list[dict[str, str]],
    prior_exclusion_rows: list[dict[str, Any]],
    blocker_guard_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        actor_guard("p0_observation_dim", P0_OBSERVATION_DIM, 72),
        actor_guard("action_dim", ACTION_DIM, 3),
        actor_guard("hidden_oracle_actor_input_required", any_flag(candidate_rows, "hidden_oracle_actor_input_required"), False),
        actor_guard("actor_input_contract_changed", any_flag(episode_rows + failure_rows, "actor_input_contract_changed"), False),
        actor_guard("stress_axis_labels_actor_visible", any_flag(candidate_rows + episode_rows + failure_rows, "stress_axis_labels_actor_visible"), False),
        actor_guard("blocker_labels_actor_visible", any_flag(episode_rows + failure_rows, "blocker_labels_actor_visible"), False),
        actor_guard("route_labels_actor_visible", any_flag(episode_rows + failure_rows, "route_labels_actor_visible"), False),
        actor_guard("verdict_labels_actor_visible", any_flag(episode_rows + failure_rows, "verdict_labels_actor_visible"), False),
        actor_guard("prior_panel_rows_actor_visible", any_flag(prior_exclusion_rows, "actor_visible_allowed"), False),
        actor_guard("blocker_rows_actor_visible", any_flag(blocker_guard_rows, "actor_visible_allowed"), False),
        actor_guard("all_candidates_actor_contract_shape_72_action_3", all(_bool(row.get("actor_contract_shape_72_action_3", False)) for row in candidate_rows), True),
        actor_guard("all_resolutions_actor_contract_shape_72_action_3", all(_bool(row.get("actor_contract_shape_72_action_3", False)) for row in resolution_rows), True),
    ]


def actor_guard(field: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": f"m2807-actor-guard-{field}",
        "guard_family": field,
        "observed": observed,
        "expected": expected,
        "status_pass": observed == expected,
        "actor_visible_allowed": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_claim_boundary_rows(
    *,
    follow_up_manifest_registered: bool,
    artifacts_present: bool,
    episode_or_failure_rows_present: bool,
) -> list[dict[str, Any]]:
    specs = [
        ("bounded_execution_artifact_completeness", "artifact", True, artifacts_present and episode_or_failure_rows_present, "M2807 artifacts"),
        ("follow_up_result_audit_registered", "follow_up_route", True, follow_up_manifest_registered, "M2808 result-audit manifest"),
        ("driver_performance", "performance", False, False, "future validation gate"),
        ("validation_readiness", "validation", False, False, "future validation-readiness manifest"),
        ("success_rate_verdict", "verdict", False, False, "future validation or promotion gate"),
        ("controller_ranking", "ranking", False, False, "future comparison gate"),
        ("stress_axis_ranking", "ranking", False, False, "future comparison gate"),
        ("winner_selection", "promotion", False, False, "future promotion gate"),
        ("checkpoint_promotion", "promotion", False, False, "future promotion gate"),
        ("paper_evidence", "paper", False, False, "Route B proof/generalization gates"),
        ("finite_window_vs_gru_conclusion", "paper", False, False, "Route B comparison gates"),
        ("current_sim_verdict", "verdict", False, False, "future current-sim validation route"),
        ("high_fidelity_validation", "high_fidelity", False, False, "Route C source dependency and validation gates"),
        ("full_ideal_driver_completion", "goal", False, False, "full ideal driver gate"),
        ("level3_self_id", "self_id", False, False, "Route B self-ID proof gates"),
    ]
    return [claim(*spec) for spec in specs]


def claim(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m2807-claim-{claim_id}",
        "claim_family": family,
        "allowed_in_m2807": allowed,
        "claim_made": made,
        "status_pass": made == allowed if allowed else not made,
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    resolution_rows: list[dict[str, Any]],
    execution_summary: dict[str, Any],
    artifact_rows: dict[str, list[dict[str, str]]],
    stress_axis_aggregate_rows: list[dict[str, Any]],
    prior_exclusion_rows: list[dict[str, Any]],
    blocker_guard_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    episode_rows = artifact_rows["candidate_execution_rows"]
    failure_rows = artifact_rows["candidate_execution_failure_rows"]
    checks = [
        ("source_artifacts_present", "lineage", all(source["source_exists"].values()), source["source_exists"], "all M2806/M1690/M2737/M2746/M2753/M2804/spec/follow-up artifacts present", "lineage_invalid"),
        ("candidate_count", "candidate_surface", len(candidate_rows) == EXPECTED_CANDIDATE_COUNT, len(candidate_rows), EXPECTED_CANDIDATE_COUNT, "scenario_sampling_failure"),
        ("selected_l3_profile_only", "candidate_surface", {row["profile_name"] for row in candidate_rows} == {CANONICAL_PROFILE}, sorted({row["profile_name"] for row in candidate_rows}), CANONICAL_PROFILE, "contract_violation"),
        ("prior_surface_exclusions_loaded", "candidate_surface", len({row["task_source_id"] for row in prior_exclusion_rows}) >= EXPECTED_PRIOR_SURFACE_MIN_COUNT, len({row["task_source_id"] for row in prior_exclusion_rows}), f">={EXPECTED_PRIOR_SURFACE_MIN_COUNT}", "lineage_invalid"),
        ("selected_prior_panel_execution_false", "candidate_surface", not any(_bool(row["prior_panel_excluded"]) for row in candidate_rows), [row["task_source_id"] for row in candidate_rows if _bool(row["prior_panel_excluded"])], [], "objective_overfit"),
        ("all_candidates_resolved_or_accounted", "execution", len(episode_rows) + len(failure_rows) == len(resolution_rows), len(episode_rows) + len(failure_rows), len(resolution_rows), "lineage_invalid"),
        ("any_execution_or_failure_rows", "execution", bool(episode_rows or failure_rows), len(episode_rows) + len(failure_rows), ">0", "lineage_invalid"),
        ("all_selected_metrics_finite", "metric", selected_metrics_are_finite(episode_rows) if episode_rows else False, execution_summary.get("all_selected_metrics_finite"), True, "metric_artifact"),
        ("prior_panel_execution_false", "boundary", not any_flag(episode_rows + failure_rows, "prior_panel_execution"), any_flag(episode_rows + failure_rows, "prior_panel_execution"), False, "objective_overfit"),
        ("protected_blocker_execution_false", "boundary", not any_flag(episode_rows + failure_rows, "protected_blocker_execution"), any_flag(episode_rows + failure_rows, "protected_blocker_execution"), False, "proof_washout"),
        ("hf3_blocker_execution_false", "boundary", not any_flag(episode_rows + failure_rows, "hf3_blocker_execution"), any_flag(episode_rows + failure_rows, "hf3_blocker_execution"), False, "proof_washout"),
        ("protected_denominator_false", "boundary", not any_flag(episode_rows + failure_rows + blocker_guard_rows, "protected_rows_in_success_denominator"), any_flag(episode_rows + failure_rows + blocker_guard_rows, "protected_rows_in_success_denominator"), False, "proof_washout"),
        ("stress_axis_aggregate_rows", "metric", len(stress_axis_aggregate_rows) == 4, len(stress_axis_aggregate_rows), 4, "metric_artifact"),
        ("actor_contract_guards_pass", "contract", all(_bool(row["status_pass"]) for row in actor_guard_rows), "all_pass" if all(_bool(row["status_pass"]) for row in actor_guard_rows) else actor_guard_rows, "all_pass", "contract_violation"),
        ("claim_boundary_rows_pass", "claim", all(_bool(row["status_pass"]) for row in claim_rows), "all_pass" if all(_bool(row["status_pass"]) for row in claim_rows) else claim_rows, "all_pass", "proof_washout"),
        ("ranking_false", "claim", not any_flag(episode_rows + failure_rows, "ranking_run"), any_flag(episode_rows + failure_rows, "ranking_run"), False, "objective_overfit"),
        ("driver_performance_claim_false", "claim", not any_flag(episode_rows + failure_rows, "driver_performance_claim_made"), any_flag(episode_rows + failure_rows, "driver_performance_claim_made"), False, "proof_washout"),
        ("paper_claim_false", "claim", not any_flag(episode_rows + failure_rows, "paper_claim_made"), any_flag(episode_rows + failure_rows, "paper_claim_made"), False, "proof_washout"),
        ("current_sim_verdict_false", "claim", not any_flag(episode_rows + failure_rows, "current_sim_verdict_claim_made"), any_flag(episode_rows + failure_rows, "current_sim_verdict_claim_made"), False, "proof_washout"),
        ("level3_self_id_claim_false", "claim", not any_flag(episode_rows + failure_rows, "level3_self_id_claim_made"), any_flag(episode_rows + failure_rows, "level3_self_id_claim_made"), False, "proof_washout"),
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
        "gate_id": f"m2807-gate-{gate_id}",
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
    candidate_rows: list[dict[str, Any]],
    resolution_rows: list[dict[str, Any]],
    execution_summary: dict[str, Any],
    artifact_rows: dict[str, list[dict[str, str]]],
    stress_axis_aggregate_rows: list[dict[str, Any]],
    prior_exclusion_rows: list[dict[str, Any]],
    blocker_guard_rows: list[dict[str, Any]],
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
    termination_counts = Counter(str(row.get("termination_reason", "")) for row in episode_rows)
    status_pass = bool(all(_bool(row["status_pass"]) for row in gate_rows))
    return {
        "milestone": milestone,
        "result_class": (
            "engineering_controller_route_a_post_clearance_negative_non_same_repair_cross_axis_bounded_execution_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_post_clearance_negative_non_same_repair_cross_axis_bounded_execution_preflight_fail"
        ),
        "status_pass": status_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "candidate_count": len(candidate_rows),
        "selected_task_source_ids": [row["task_source_id"] for row in candidate_rows],
        "resolved_candidate_count": sum(1 for row in resolution_rows if _bool(row.get("execution_admitted", False))),
        "candidate_execution_row_count": len(episode_rows),
        "candidate_execution_failure_row_count": len(failure_rows),
        "accounted_candidate_count": len(episode_rows) + len(failure_rows),
        "diagnostic_success_count": sum(1 for row in episode_rows if _episode_success(row)),
        "diagnostic_collision_count": sum(1 for row in episode_rows if _bool(row.get("collision", False))),
        "diagnostic_offtrack_count": sum(1 for row in episode_rows if str(row.get("termination_reason", "")) == "off_track"),
        "diagnostic_termination_counts": dict(sorted(termination_counts.items())),
        "stress_axis_aggregate_row_count": len(stress_axis_aggregate_rows),
        "prior_panel_exclusion_row_count": len(prior_exclusion_rows),
        "prior_panel_unique_task_source_count": len({row["task_source_id"] for row in prior_exclusion_rows}),
        "blocker_guard_row_count": len(blocker_guard_rows),
        "actor_contract_guard_row_count": len(actor_guard_rows),
        "actor_contract_guard_rows_pass": all(_bool(row["status_pass"]) for row in actor_guard_rows),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(_bool(row["status_pass"]) for row in claim_rows),
        "gate_row_count": len(gate_rows),
        "gate_matrix_pass": all(_bool(row["status_pass"]) for row in gate_rows),
        "required_artifacts_present": required_artifacts_present,
        "source_exists": source["source_exists"],
        "m1690_l3_row_count": len(source["m1690_by_task_source"]),
        "all_selected_metrics_finite": bool(execution_summary.get("all_selected_metrics_finite", False)),
        "prior_panel_execution": any_flag(episode_rows + failure_rows, "prior_panel_execution"),
        "protected_blocker_execution": any_flag(episode_rows + failure_rows, "protected_blocker_execution"),
        "hf3_blocker_execution": any_flag(episode_rows + failure_rows, "hf3_blocker_execution"),
        "protected_rows_in_success_denominator": any_flag(episode_rows + failure_rows + blocker_guard_rows, "protected_rows_in_success_denominator"),
        "actor_input_contract_changed": any_flag(episode_rows + failure_rows, "actor_input_contract_changed"),
        "hidden_oracle_actor_input_required": any_flag(candidate_rows + episode_rows + failure_rows, "hidden_oracle_actor_input_required"),
        "stress_axis_labels_actor_visible": any_flag(candidate_rows + episode_rows + failure_rows, "stress_axis_labels_actor_visible"),
        "ranking_run": any_flag(episode_rows + failure_rows, "ranking_run"),
        "winner_selected": any_flag(episode_rows + failure_rows, "winner_selected"),
        "checkpoint_promoted": any_flag(episode_rows + failure_rows, "checkpoint_promoted"),
        "success_rate_verdict_claim_made": any_flag(episode_rows + failure_rows, "success_rate_verdict_claim_made"),
        "driver_performance_claim_made": any_flag(episode_rows + failure_rows, "driver_performance_claim_made"),
        "validation_readiness_claim_made": any_flag(episode_rows + failure_rows, "validation_readiness_claim_made"),
        "paper_claim_made": any_flag(episode_rows + failure_rows, "paper_claim_made"),
        "current_sim_verdict_claim_made": any_flag(episode_rows + failure_rows, "current_sim_verdict_claim_made"),
        "high_fidelity_validation_claim_made": any_flag(episode_rows + failure_rows, "high_fidelity_validation_claim_made"),
        "level3_self_id_claim_made": any_flag(episode_rows + failure_rows, "level3_self_id_claim_made"),
        "full_ideal_driver_gate_passed": any_flag(episode_rows + failure_rows, "full_ideal_driver_gate_passed"),
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
        "# M2807 Engineering Controller Route A Post-Clearance Negative Non-Same-Repair Cross-Axis Bounded Execution Preflight",
        "",
        "## Metadata",
        "",
        f"- status: {'completed' if summary['status_pass'] else 'failed'}",
        f"- result class: `{summary['result_class']}`",
        f"- candidate rows: {summary['candidate_count']}",
        f"- resolved candidates: {summary['resolved_candidate_count']}/{summary['candidate_count']}",
        f"- execution rows: {summary['candidate_execution_row_count']}",
        f"- failure rows: {summary['candidate_execution_failure_row_count']}",
        f"- accounted candidates: {summary['accounted_candidate_count']}/{summary['candidate_count']}",
        f"- diagnostic outcomes: success {summary['diagnostic_success_count']} collision {summary['diagnostic_collision_count']} offtrack {summary['diagnostic_offtrack_count']}",
        f"- diagnostic termination counts: {summary['diagnostic_termination_counts']}",
        f"- stress-axis aggregate rows: {summary['stress_axis_aggregate_row_count']}",
        f"- prior-surface exclusion rows: {summary['prior_panel_exclusion_row_count']}",
        f"- blocker guard rows: {summary['blocker_guard_row_count']}",
        f"- actor-contract guard rows: {summary['actor_contract_guard_row_count']}",
        f"- gate matrix pass: {summary['gate_matrix_pass']}",
        f"- next blocker: `{summary['next_blocker']}`",
        f"- follow-up manifest: `{summary['follow_up_manifest']}`",
        "",
        "## Boundary",
        "",
        "M2807 is a bounded diagnostic execution preflight. It records closed-loop",
        "diagnostic rows over the fixed post-clearance non-same-repair M1690 L3_online_gru surface",
        "selected by M2806. It does not rank profiles, select a winner, validate",
        "driver performance, or make paper/self-ID/current-sim/high-fidelity claims.",
        "",
        "## Selected Task Sources",
        "",
        "```text",
        *[str(item) for item in summary["selected_task_source_ids"]],
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


def _group_by(rows: list[Mapping[str, Any]], key: str) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key, ""))].append(row)
    return grouped


def _float_values(rows: list[Mapping[str, Any]], key: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        try:
            values.append(float(row.get(key, "")))
        except (TypeError, ValueError):
            continue
    return values


def mean_float(rows: list[Mapping[str, Any]], key: str) -> float | str:
    values = _float_values(rows, key)
    if not values:
        return ""
    return sum(values) / len(values)


def mean_bool(rows: list[Mapping[str, Any]], key: str) -> float | str:
    if not rows:
        return ""
    return sum(1.0 for row in rows if _bool(row.get(key, False))) / len(rows)


def mean_eq(rows: list[Mapping[str, Any]], key: str, expected: str) -> float | str:
    if not rows:
        return ""
    return sum(1.0 for row in rows if str(row.get(key, "")) == expected) / len(rows)


def any_flag(rows: list[Mapping[str, Any]], key: str) -> bool:
    return any(_bool(row.get(key, False)) for row in rows)


def forbidden_execution_flag(row: Mapping[str, Any]) -> bool:
    return any(
        _bool(row.get(key, False))
        for key in (
            "prior_panel_execution",
            "protected_blocker_execution",
            "hf3_blocker_execution",
            "protected_rows_in_success_denominator",
            "hidden_oracle_actor_input_required",
            "stress_axis_labels_actor_visible",
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
            "success_rate_verdict_claim_made",
            "driver_performance_claim_made",
            "paper_claim_made",
            "current_sim_verdict_claim_made",
            "high_fidelity_validation_claim_made",
            "level3_self_id_claim_made",
            "full_ideal_driver_gate_passed",
        )
    )


def _episode_success(row: Mapping[str, Any]) -> bool:
    return _bool(row.get("success", False)) or (
        _bool(row.get("obstacle_completed", False)) and not _bool(row.get("collision", False))
    )


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m1690-workload", type=Path, default=DEFAULT_EXECUTABLE_WORKLOAD)
    parser.add_argument("--m2746-dir", type=Path, default=DEFAULT_M2746_DIR)
    parser.add_argument("--m2737-dir", type=Path, default=DEFAULT_M2737_DIR)
    parser.add_argument("--m2753-dir", type=Path, default=DEFAULT_M2753_DIR)
    parser.add_argument("--m2804-dir", type=Path, default=DEFAULT_M2804_DIR)
    parser.add_argument("--m2806-design", type=Path, default=DEFAULT_M2806_DESIGN)
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
    summary = run_post_clearance_negative_non_same_repair_cross_axis_bounded_execution_preflight(
        m1690_workload=args.m1690_workload,
        m2746_dir=args.m2746_dir,
        m2737_dir=args.m2737_dir,
        m2753_dir=args.m2753_dir,
        m2804_dir=args.m2804_dir,
        m2806_design=args.m2806_design,
        executable_specs=args.executable_specs,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        eval_seed_base=args.eval_seed_base,
        device=args.device,
        resume=not args.no_resume,
    )
    print(
        "M2807 post-clearance negative non-same-repair cross-axis execution preflight: "
        f"status={summary['status_pass']} "
        f"candidates={summary['candidate_count']} "
        f"episodes={summary['candidate_execution_row_count']} "
        f"failures={summary['candidate_execution_failure_row_count']} "
        f"next={summary['next_blocker']}"
    )


if __name__ == "__main__":
    main()
