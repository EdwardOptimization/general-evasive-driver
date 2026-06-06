"""Run M2877 post-package-refresh fresh closed-loop evidence preflight.

M2877 consumes the M2876 design, M2873 package boundary artifacts, the M1690
executable workload, and the M2737/M2807/M2816/M2828/M2838/M2868 prior
execution surfaces. It executes one bounded diagnostic rollout for each fixed
non-same-surface L3_online_gru candidate selected by M2876 while keeping prior
surfaces, package limitations, protected rows, and HF3 blocker rows outside
execution and outside ordinary success denominators.
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
    "m2877-engineering-controller-route-a-post-package-refresh-fresh-closed-loop-"
    "evidence-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2878-engineering-controller-route-a-post-package-refresh-fresh-closed-loop-"
    "evidence-result-audit"
)
DEFAULT_M2876_DESIGN = Path(
    "docs/m2876-engineering-controller-route-a-post-package-refresh-fresh-closed-loop-"
    "evidence-surface-design.md"
)
DEFAULT_M2873_DIR = Path(
    "runs/m2873_engineering_controller_route_a_post_localized_response_prediction_"
    "limited_baseline_package_refresh"
)
DEFAULT_M2737_DIR = Path(
    "runs/m2737_engineering_controller_route_a_post_negative_diagnostic_source_diverse_"
    "closed_loop_evidence_surface_bounded_execution_preflight"
)
DEFAULT_M2807_DIR = Path(
    "runs/m2807_engineering_controller_route_a_post_clearance_negative_non_same_repair_"
    "cross_axis_bounded_execution_preflight"
)
DEFAULT_M2816_DIR = Path(
    "runs/m2816_engineering_controller_route_a_post_action_response_recoverability_window_"
    "instrumented_bounded_execution_preflight"
)
DEFAULT_M2828_DIR = Path(
    "runs/m2828_engineering_controller_route_a_post_package_source_diverse_closed_loop_"
    "evidence_expansion_preflight"
)
DEFAULT_M2838_DIR = Path(
    "runs/m2838_engineering_controller_post_route_c_hf3_stop_source_diverse_closed_loop_"
    "evidence_preflight"
)
DEFAULT_M2868_DIR = Path(
    "runs/m2868_engineering_controller_route_a_response_predictive_recurrent_belief_"
    "localized_response_prediction_candidate_closed_loop_delta_panel"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2877_engineering_controller_route_a_post_package_refresh_fresh_closed_loop_"
    "evidence_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2877-engineering-controller-route-a-post-package-refresh-fresh-closed-loop-"
    "evidence-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2878-engineering-controller-route-a-post-package-refresh-"
    "fresh-closed-loop-evidence-result-audit.json"
)
DEFAULT_EVAL_SEED_BASE = 287700
CANONICAL_PROFILE = "L3_online_gru"

SELECTED_TASK_SOURCES: tuple[tuple[str, str, str, str, str, str, tuple[str, ...]], ...] = (
    (
        "m1680-spec-0001",
        "T4",
        "actuator_delay_step|t4_capability_step_temporal",
        "mapping_window_unspecified",
        "actuator_delay_step",
        "t4_actuator_delay_response",
        ("t4_actuator_delay_or_response",),
    ),
    (
        "m1680-spec-0003",
        "T4",
        "t4_actuator_delay_response|actuator_delay_step",
        "mapping_window_unspecified",
        "t4_actuator_delay_response",
        "t4_actuator_delay_response",
        ("t4_actuator_delay_or_response",),
    ),
    (
        "m1680-spec-0008",
        "T4",
        "actuator_delay_step|t4_capability_step_temporal",
        "mapping_window_unspecified",
        "actuator_delay_step",
        "t4_actuator_delay_response",
        ("t4_actuator_delay_or_response",),
    ),
    (
        "m1680-spec-0010",
        "T4",
        "t4_actuator_delay_response|actuator_delay_step",
        "mapping_window_unspecified",
        "t4_actuator_delay_response",
        "t4_actuator_delay_response",
        ("t4_actuator_delay_or_response",),
    ),
    (
        "m1680-spec-0043",
        "T5",
        "t5_near_boundary_warmup|t5_boundary_axis_retarget",
        "mapping_window_unspecified",
        "t5_near_boundary_warmup",
        "t5_boundary_axis_retarget",
        ("t5_near_boundary_or_delay", "t5_retargeted_boundary"),
    ),
    (
        "m1680-spec-0045",
        "T5",
        "brake_fade_or_loss_proxy|late_reveal_boundary",
        "mapping_window_unspecified",
        "brake_fade_or_loss_proxy",
        "t5_near_boundary_warmup",
        ("t5_loss_or_boundary",),
    ),
    (
        "m1680-spec-0067",
        "T5",
        "capability_step_down|t5_near_boundary_warmup",
        "decision_minus_24",
        "t5_near_boundary_warmup",
        "t5_near_boundary_warmup",
        ("t5_near_boundary_or_delay",),
    ),
    (
        "m1680-spec-0068",
        "T5",
        "curved_boundary_obstacle|t5_boundary_axis_retarget",
        "decision_minus_32",
        "curved_boundary_obstacle",
        "t5_boundary_axis_retarget",
        ("t5_loss_or_boundary", "t5_retargeted_boundary"),
    ),
    (
        "m1680-spec-0069",
        "T5",
        "actuator_delay_step|t5_near_boundary_warmup",
        "reveal_plus_4",
        "t5_near_boundary_warmup",
        "t5_near_boundary_warmup",
        ("t5_near_boundary_or_delay",),
    ),
    (
        "m1680-spec-0070",
        "T5",
        "capability_step_down|t5_near_boundary_warmup",
        "decision_minus_24",
        "t5_near_boundary_warmup",
        "t5_near_boundary_warmup",
        ("t5_near_boundary_or_delay",),
    ),
    (
        "m1680-spec-0071",
        "T5",
        "curved_boundary_obstacle|t5_boundary_axis_retarget",
        "decision_minus_32",
        "curved_boundary_obstacle",
        "t5_boundary_axis_retarget",
        ("t5_loss_or_boundary", "t5_retargeted_boundary"),
    ),
)
EXPECTED_CANDIDATE_COUNT = len(SELECTED_TASK_SOURCES)
EXPECTED_PRIOR_SURFACE_UNIQUE_COUNT = 61

CLAIM_SCOPE = (
    "M2877 Route A post-package-refresh fresh closed-loop evidence preflight "
    "only; reset, step, policy action, and rollout fields may be recorded for "
    "the fixed 11 selected M1690 L3_online_gru rows while M2737, M2807, M2816, "
    "M2828, M2838, M2868, package-limitation, protected, and HF3 blocker rows "
    "remain guardrails outside execution and ordinary success denominators. No "
    "replay, validation, training, PPO, source build, adapter probe, external "
    "simulation, package publication, ranking, winner selection, promotion, "
    "success-rate verdict, repair-success, recoverability-success, driver-"
    "performance, paper, finite-window-vs-GRU, current-sim, high-fidelity "
    "validation, full ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "package publication, repair success, recoverability success, localized-"
    "response-prediction success, driver performance, validation readiness or "
    "result, controller ranking, source-family ranking, task-family ranking, "
    "scenario-role ranking, stress-axis ranking, profile ranking, winner "
    "selection, checkpoint promotion, success-rate verdict, paper evidence, "
    "finite-window-vs-GRU conclusion, current-response sufficiency, current-sim "
    "verdict, high-fidelity validation readiness or result, full ideal driver "
    "completion, or level3 self-identification"
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
    "source_family_tag",
    "scenario_role_primary",
    "diagnostic_tags",
    "profile_config_path",
    "checkpoint_path",
    "config_exists",
    "checkpoint_exists",
    "prior_surface_excluded",
    "candidate_admitted",
    "candidate_failure_reason",
    "actor_contract_shape_72_action_3",
    "hidden_oracle_actor_input_required",
    "package_labels_actor_visible",
    "blocker_labels_actor_visible",
    "diagnostic_labels_actor_visible",
    "route_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
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
    "window_tag",
    "source_family_tag",
    "scenario_role_primary",
    "diagnostic_tags",
    "resolution_status",
    "profile_config_path",
    "checkpoint_path",
    "execution_admitted",
    "execution_planned",
    "failure_reason",
    "actor_contract_shape_72_action_3",
    "hidden_oracle_actor_input_required",
    "package_labels_actor_visible",
    "blocker_labels_actor_visible",
    "diagnostic_labels_actor_visible",
    "route_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
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
    "window_tag",
    "source_family_tag",
    "scenario_role_primary",
    "diagnostic_tags",
    "m2877_eval_seed",
    "error_type",
    "error_message",
    "environment_reset_run",
    "environment_step_run",
    "policy_action_run",
    "policy_rollout_run",
    "prior_surface_execution",
    "package_limitation_execution",
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
    "package_labels_actor_visible",
    "blocker_labels_actor_visible",
    "diagnostic_labels_actor_visible",
    "route_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "ordinary_success_denominator_allowed",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
SCENARIO_ROLE_METRIC_FIELDNAMES = [
    "metric_id",
    "candidate_id",
    "task_source_id",
    "scenario_role_primary",
    "source_family_tag",
    "task_family",
    "source_edge",
    "episode_count",
    "failure_count",
    "success_diagnostic",
    "collision_diagnostic",
    "termination_reason",
    "min_clearance_margin",
    "return",
    "diagnostic_only_no_verdict",
    "ranking_claim_made",
    "actor_visible_allowed",
    "claim_boundary",
]
FAILURE_TAXONOMY_FIELDNAMES = [
    "failure_taxonomy_id",
    "candidate_id",
    "task_source_id",
    "scenario_role_primary",
    "source_family_tag",
    "outcome_family",
    "termination_reason",
    "success",
    "collision",
    "offtrack",
    "execution_failure",
    "error_type",
    "diagnostic_only_no_verdict",
    "ranking_claim_made",
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
PACKAGE_GUARD_FIELDNAMES = [
    "guard_id",
    "source_file",
    "source_row_id",
    "blocker_or_limitation",
    "source_milestone",
    "observed_value",
    "blocked_interpretation",
    "current_status",
    "execution_candidate",
    "execution_admitted",
    "execution_run",
    "ordinary_success_denominator_allowed",
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
    "allowed_in_m2877",
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
    "fresh_candidate_rows",
    "execution_candidate_resolution_rows",
    "candidate_execution_rows",
    "candidate_execution_failure_rows",
    "scenario_role_metric_rows",
    "failure_taxonomy_rows",
    "prior_surface_exclusion_rows",
    "package_limitation_guard_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
]


def run_post_package_refresh_fresh_closed_loop_evidence_preflight(
    *,
    m1690_workload: Path | str = DEFAULT_EXECUTABLE_WORKLOAD,
    m2876_design: Path | str = DEFAULT_M2876_DESIGN,
    m2873_dir: Path | str = DEFAULT_M2873_DIR,
    m2737_dir: Path | str = DEFAULT_M2737_DIR,
    m2807_dir: Path | str = DEFAULT_M2807_DIR,
    m2816_dir: Path | str = DEFAULT_M2816_DIR,
    m2828_dir: Path | str = DEFAULT_M2828_DIR,
    m2838_dir: Path | str = DEFAULT_M2838_DIR,
    m2868_dir: Path | str = DEFAULT_M2868_DIR,
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
        m2876_design=Path(m2876_design),
        m2873_dir=Path(m2873_dir),
        m2737_dir=Path(m2737_dir),
        m2807_dir=Path(m2807_dir),
        m2816_dir=Path(m2816_dir),
        m2828_dir=Path(m2828_dir),
        m2838_dir=Path(m2838_dir),
        m2868_dir=Path(m2868_dir),
        executable_specs=Path(executable_specs),
        follow_up_manifest=Path(follow_up_manifest),
    )
    prior_exclusion_rows = build_prior_surface_exclusion_rows(source)
    candidate_rows = build_fresh_candidate_rows(source, prior_exclusion_rows)
    resolution_rows, resolved_sources = build_resolution_rows(candidate_rows, source["m1690_by_task_source"])
    package_guard_rows = build_package_limitation_guard_rows(source)

    write_csv_rows(paths["fresh_candidate_rows"], candidate_rows, fieldnames=CANDIDATE_FIELDNAMES)
    write_csv_rows(paths["prior_surface_exclusion_rows"], prior_exclusion_rows, fieldnames=PRIOR_EXCLUSION_FIELDNAMES)
    write_csv_rows(paths["execution_candidate_resolution_rows"], resolution_rows, fieldnames=RESOLUTION_FIELDNAMES)
    write_csv_rows(paths["package_limitation_guard_rows"], package_guard_rows, fieldnames=PACKAGE_GUARD_FIELDNAMES)

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
    scenario_role_metric_rows = build_scenario_role_metric_rows(
        candidate_rows=candidate_rows,
        episode_rows=artifact_rows["candidate_execution_rows"],
        failure_rows=artifact_rows["candidate_execution_failure_rows"],
    )
    failure_taxonomy_rows = build_failure_taxonomy_rows(
        candidate_rows=candidate_rows,
        episode_rows=artifact_rows["candidate_execution_rows"],
        failure_rows=artifact_rows["candidate_execution_failure_rows"],
    )
    actor_guard_rows = build_actor_contract_guard_rows(
        candidate_rows=candidate_rows,
        resolution_rows=resolution_rows,
        episode_rows=artifact_rows["candidate_execution_rows"],
        failure_rows=artifact_rows["candidate_execution_failure_rows"],
        prior_exclusion_rows=prior_exclusion_rows,
        package_guard_rows=package_guard_rows,
    )
    required_artifacts_present = all(
        paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_artifacts_present,
        episode_or_failure_rows_present=bool(
            artifact_rows["candidate_execution_rows"] or artifact_rows["candidate_execution_failure_rows"]
        ),
        all_candidates_accounted=len(artifact_rows["candidate_execution_rows"])
        + len(artifact_rows["candidate_execution_failure_rows"])
        == len(resolution_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        candidate_rows=candidate_rows,
        resolution_rows=resolution_rows,
        execution_summary=execution_summary,
        artifact_rows=artifact_rows,
        scenario_role_metric_rows=scenario_role_metric_rows,
        failure_taxonomy_rows=failure_taxonomy_rows,
        prior_exclusion_rows=prior_exclusion_rows,
        package_guard_rows=package_guard_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["scenario_role_metric_rows"], scenario_role_metric_rows, fieldnames=SCENARIO_ROLE_METRIC_FIELDNAMES)
    write_csv_rows(paths["failure_taxonomy_rows"], failure_taxonomy_rows, fieldnames=FAILURE_TAXONOMY_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_guard_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    required_artifacts_present = all(
        paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_artifacts_present,
        episode_or_failure_rows_present=bool(
            artifact_rows["candidate_execution_rows"] or artifact_rows["candidate_execution_failure_rows"]
        ),
        all_candidates_accounted=len(artifact_rows["candidate_execution_rows"])
        + len(artifact_rows["candidate_execution_failure_rows"])
        == len(resolution_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        candidate_rows=candidate_rows,
        resolution_rows=resolution_rows,
        execution_summary=execution_summary,
        artifact_rows=artifact_rows,
        scenario_role_metric_rows=scenario_role_metric_rows,
        failure_taxonomy_rows=failure_taxonomy_rows,
        prior_exclusion_rows=prior_exclusion_rows,
        package_guard_rows=package_guard_rows,
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
        artifact_rows=artifact_rows,
        scenario_role_metric_rows=scenario_role_metric_rows,
        failure_taxonomy_rows=failure_taxonomy_rows,
        prior_exclusion_rows=prior_exclusion_rows,
        package_guard_rows=package_guard_rows,
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
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key != "summary")
    gate_rows = build_gate_matrix_rows(
        source=source,
        candidate_rows=candidate_rows,
        resolution_rows=resolution_rows,
        execution_summary=execution_summary,
        artifact_rows=artifact_rows,
        scenario_role_metric_rows=scenario_role_metric_rows,
        failure_taxonomy_rows=failure_taxonomy_rows,
        prior_exclusion_rows=prior_exclusion_rows,
        package_guard_rows=package_guard_rows,
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
        artifact_rows=artifact_rows,
        scenario_role_metric_rows=scenario_role_metric_rows,
        failure_taxonomy_rows=failure_taxonomy_rows,
        prior_exclusion_rows=prior_exclusion_rows,
        package_guard_rows=package_guard_rows,
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
        "fresh_candidate_rows": output_dir / "fresh_candidate_rows.csv",
        "execution_candidate_resolution_rows": output_dir / "execution_candidate_resolution_rows.csv",
        "candidate_execution_rows": output_dir / "candidate_execution_rows.csv",
        "candidate_execution_failure_rows": output_dir / "candidate_execution_failure_rows.csv",
        "scenario_role_metric_rows": output_dir / "scenario_role_metric_rows.csv",
        "failure_taxonomy_rows": output_dir / "failure_taxonomy_rows.csv",
        "prior_surface_exclusion_rows": output_dir / "prior_surface_exclusion_rows.csv",
        "package_limitation_guard_rows": output_dir / "package_limitation_guard_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m1690_workload: Path,
    m2876_design: Path,
    m2873_dir: Path,
    m2737_dir: Path,
    m2807_dir: Path,
    m2816_dir: Path,
    m2828_dir: Path,
    m2838_dir: Path,
    m2868_dir: Path,
    executable_specs: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2876_design": m2876_design,
        "m2873_summary": m2873_dir / "summary.json",
        "m2873_latest_negative_evidence_rows": m2873_dir / "latest_negative_evidence_rows.csv",
        "m2873_known_blocker_disclosure_rows": m2873_dir / "known_blocker_disclosure_rows.csv",
        "m2873_actor_action_contract_rows": m2873_dir / "actor_action_contract_rows.csv",
        "m2873_claim_boundary_rows": m2873_dir / "claim_boundary_rows.csv",
        "m2873_package_gate_matrix": m2873_dir / "package_gate_matrix.csv",
        "m1690_workload": m1690_workload,
        "m2737_candidate_execution_rows": m2737_dir / "candidate_execution_rows.csv",
        "m2807_candidate_execution_rows": m2807_dir / "candidate_execution_rows.csv",
        "m2816_instrumented_execution_rows": m2816_dir / "instrumented_execution_rows.csv",
        "m2828_candidate_execution_rows": m2828_dir / "candidate_execution_rows.csv",
        "m2838_candidate_execution_rows": m2838_dir / "candidate_execution_rows.csv",
        "m2868_paired_execution_rows": m2868_dir / "paired_execution_rows.csv",
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
        "m2876_design_text": paths["m2876_design"].read_text(encoding="utf-8")
        if source_exists["m2876_design"]
        else "",
        "m2873_summary": read_json(paths["m2873_summary"]) if source_exists["m2873_summary"] else {},
        "m2873_latest_negative_evidence_rows": read_csv_rows(paths["m2873_latest_negative_evidence_rows"]),
        "m2873_known_blocker_disclosure_rows": read_csv_rows(paths["m2873_known_blocker_disclosure_rows"]),
        "m2873_actor_action_contract_rows": read_csv_rows(paths["m2873_actor_action_contract_rows"]),
        "m2873_claim_boundary_rows": read_csv_rows(paths["m2873_claim_boundary_rows"]),
        "m2873_package_gate_rows": read_csv_rows(paths["m2873_package_gate_matrix"]),
        "m1690_rows": m1690_rows,
        "m1690_by_task_source": m1690_by_task_source,
        "m2737_candidate_execution_rows": read_csv_rows(paths["m2737_candidate_execution_rows"]),
        "m2807_candidate_execution_rows": read_csv_rows(paths["m2807_candidate_execution_rows"]),
        "m2816_instrumented_execution_rows": read_csv_rows(paths["m2816_instrumented_execution_rows"]),
        "m2828_candidate_execution_rows": read_csv_rows(paths["m2828_candidate_execution_rows"]),
        "m2838_candidate_execution_rows": read_csv_rows(paths["m2838_candidate_execution_rows"]),
        "m2868_paired_execution_rows": read_csv_rows(paths["m2868_paired_execution_rows"]),
    }


def build_prior_surface_exclusion_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    counts: dict[tuple[str, str], int] = Counter()
    for source_panel, key in (
        ("m2737_candidate_execution_rows", "m2737_candidate_execution_rows"),
        ("m2807_candidate_execution_rows", "m2807_candidate_execution_rows"),
        ("m2816_instrumented_execution_rows", "m2816_instrumented_execution_rows"),
        ("m2828_candidate_execution_rows", "m2828_candidate_execution_rows"),
        ("m2838_candidate_execution_rows", "m2838_candidate_execution_rows"),
        ("m2868_paired_execution_rows", "m2868_paired_execution_rows"),
    ):
        for row in source[key]:
            task_source_id = str(row.get("task_source_id", ""))
            if task_source_id:
                counts[(source_panel, task_source_id)] += 1

    rows: list[dict[str, Any]] = []
    for index, ((source_panel, task_source_id), row_count) in enumerate(sorted(counts.items()), start=1):
        rows.append(
            {
                "exclusion_id": f"m2877-prior-surface-exclusion-{index:04d}",
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


def build_fresh_candidate_rows(source: dict[str, Any], prior_exclusion_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    excluded_task_sources = {str(row["task_source_id"]) for row in prior_exclusion_rows}
    rows: list[dict[str, Any]] = []
    for index, selected in enumerate(SELECTED_TASK_SOURCES, start=1):
        task_source_id, expected_family, expected_edge, expected_window, scenario_role, source_family, tags = selected
        source_row = source["m1690_by_task_source"].get(task_source_id)
        prior_surface_excluded = task_source_id in excluded_task_sources
        failure_reason = ""
        if source_row is None:
            failure_reason = "selected_task_source_missing_from_m1690_l3_rows"
        elif str(source_row.get("task_family", "")) != expected_family:
            failure_reason = "task_family_mismatch"
        elif str(source_row.get("source_edge", "")) != expected_edge:
            failure_reason = "source_edge_mismatch"
        elif str(source_row.get("window_tag", "")) != expected_window:
            failure_reason = "window_tag_mismatch"
        elif prior_surface_excluded:
            failure_reason = "prior_surface_task_source_excluded"
        elif str(source_row.get("config_exists", "")) != "True":
            failure_reason = "profile_config_missing"
        elif str(source_row.get("checkpoint_exists", "")) != "True":
            failure_reason = "checkpoint_missing"
        elif _bool(source_row.get("profile_specific_tuning", False)):
            failure_reason = "profile_specific_tuning_detected"
        candidate_admitted = bool(source_row is not None and not failure_reason)
        rows.append(
            {
                "candidate_id": f"m2877-fresh-candidate-{index:04d}",
                "task_source_id": task_source_id,
                "workload_id": source_row.get("workload_id", "") if source_row else f"{task_source_id}::{CANONICAL_PROFILE}",
                "profile_name": source_row.get("profile_name", CANONICAL_PROFILE) if source_row else CANONICAL_PROFILE,
                "task_family": source_row.get("task_family", expected_family) if source_row else expected_family,
                "source_edge": source_row.get("source_edge", expected_edge) if source_row else expected_edge,
                "window_tag": source_row.get("window_tag", expected_window) if source_row else expected_window,
                "strata": source_row.get("strata", "") if source_row else "",
                "source_family_tag": source_family,
                "scenario_role_primary": scenario_role,
                "diagnostic_tags": ";".join(tags),
                "profile_config_path": source_row.get("profile_config_path", "") if source_row else "",
                "checkpoint_path": source_row.get("checkpoint_path", "") if source_row else "",
                "config_exists": _bool(source_row.get("config_exists", False)) if source_row else False,
                "checkpoint_exists": _bool(source_row.get("checkpoint_exists", False)) if source_row else False,
                "prior_surface_excluded": prior_surface_excluded,
                "candidate_admitted": candidate_admitted,
                "candidate_failure_reason": failure_reason,
                "actor_contract_shape_72_action_3": True,
                "hidden_oracle_actor_input_required": False,
                "package_labels_actor_visible": False,
                "blocker_labels_actor_visible": False,
                "diagnostic_labels_actor_visible": False,
                "route_labels_actor_visible": False,
                "success_progress_labels_actor_visible": False,
                "verdict_labels_actor_visible": False,
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
        resolution_id = f"m2877-resolution-{index:04d}"
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
            "window_tag": candidate["window_tag"],
            "source_family_tag": candidate["source_family_tag"],
            "scenario_role_primary": candidate["scenario_role_primary"],
            "diagnostic_tags": candidate["diagnostic_tags"],
            "resolution_status": "resolved_to_m1690_l3_workload" if execution_admitted else "accounted_by_failure",
            "profile_config_path": candidate["profile_config_path"],
            "checkpoint_path": candidate["checkpoint_path"],
            "execution_admitted": execution_admitted,
            "execution_planned": execution_admitted,
            "failure_reason": failure_reason,
            "actor_contract_shape_72_action_3": True,
            "hidden_oracle_actor_input_required": False,
            "package_labels_actor_visible": False,
            "blocker_labels_actor_visible": False,
            "diagnostic_labels_actor_visible": False,
            "route_labels_actor_visible": False,
            "success_progress_labels_actor_visible": False,
            "verdict_labels_actor_visible": False,
            "diagnostic_only_no_verdict": True,
            "ranking_run": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        rows.append(row)
        if execution_admitted and source_row is not None:
            resolved_sources[resolution_id] = source_row
    return rows, resolved_sources


def build_package_limitation_guard_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for evidence in source["m2873_latest_negative_evidence_rows"]:
        rows.append(
            package_guard(
                source_file="latest_negative_evidence_rows",
                source_row_id=str(evidence.get("negative_evidence_id", "")),
                blocker_or_limitation=str(evidence.get("negative_evidence_id", "")),
                source_milestone=str(evidence.get("source_milestone", "")),
                observed_value=str(evidence.get("observed_value", "")),
                blocked_interpretation=str(evidence.get("blocked_claims", "")),
                current_status=str(evidence.get("evidence_status", "")),
                index=len(rows) + 1,
            )
        )
    for blocker in source["m2873_known_blocker_disclosure_rows"]:
        rows.append(
            package_guard(
                source_file="known_blocker_disclosure_rows",
                source_row_id=str(blocker.get("blocker_id", "")),
                blocker_or_limitation=str(blocker.get("blocker_id", "")),
                source_milestone=str(blocker.get("source_milestone", "")),
                observed_value=str(blocker.get("blocker_status", "")),
                blocked_interpretation=str(blocker.get("blocked_claims", "")),
                current_status=str(blocker.get("blocker_status", "")),
                index=len(rows) + 1,
            )
        )
    for claim_row in source["m2873_claim_boundary_rows"]:
        if _bool(claim_row.get("allowed_in_m2873", False)):
            continue
        rows.append(
            package_guard(
                source_file="claim_boundary_rows",
                source_row_id=str(claim_row.get("claim_id", "")),
                blocker_or_limitation=str(claim_row.get("claim_family", "")),
                source_milestone="m2873",
                observed_value=str(claim_row.get("status_pass", "")),
                blocked_interpretation=str(claim_row.get("evidence_required_before_claim", "")),
                current_status="blocked_claim_boundary",
                index=len(rows) + 1,
            )
        )
    return rows


def package_guard(
    *,
    source_file: str,
    source_row_id: str,
    blocker_or_limitation: str,
    source_milestone: str,
    observed_value: str,
    blocked_interpretation: str,
    current_status: str,
    index: int,
) -> dict[str, Any]:
    return {
        "guard_id": f"m2877-package-limitation-guard-{index:04d}",
        "source_file": source_file,
        "source_row_id": source_row_id,
        "blocker_or_limitation": blocker_or_limitation,
        "source_milestone": source_milestone,
        "observed_value": observed_value,
        "blocked_interpretation": blocked_interpretation,
        "current_status": current_status,
        "execution_candidate": False,
        "execution_admitted": False,
        "execution_run": False,
        "ordinary_success_denominator_allowed": False,
        "actor_visible_allowed": False,
        "diagnostic_only_no_verdict": True,
        "claim_boundary": CLAIM_SCOPE,
    }


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
        except Exception as exc:  # noqa: BLE001 - every failed candidate is an artifact row.
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
        and len(episode_rows) == EXPECTED_CANDIDATE_COUNT
        and len(failure_rows) == 0
        and all_metrics_finite
        and not any(forbidden_execution_flag(row) for row in episode_rows + failure_rows)
    )
    summary = {
        "result_class": (
            "engineering_controller_route_a_post_package_refresh_fresh_closed_loop_evidence_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_post_package_refresh_fresh_closed_loop_evidence_preflight_incomplete_or_fail"
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
        "m2877_eval_seed": int(eval_seed),
        "resolution_id": resolution.get("resolution_id", ""),
        "candidate_id": resolution.get("candidate_id", ""),
        "bounded_post_package_refresh_fresh_closed_loop_evidence_preflight": True,
        "candidate_surface_count": EXPECTED_CANDIDATE_COUNT,
        "source_family_tag": resolution.get("source_family_tag", ""),
        "scenario_role_primary": resolution.get("scenario_role_primary", ""),
        "diagnostic_tags": resolution.get("diagnostic_tags", ""),
        "prior_surface_execution": False,
        "package_limitation_execution": False,
        "protected_blocker_execution": False,
        "hf3_blocker_execution": False,
        "ordinary_success_denominator_allowed": False,
        "hidden_oracle_actor_input_required": False,
        "package_labels_actor_visible": False,
        "blocker_labels_actor_visible": False,
        "diagnostic_labels_actor_visible": False,
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
        "window_tag": resolution.get("window_tag", ""),
        "source_family_tag": resolution.get("source_family_tag", ""),
        "scenario_role_primary": resolution.get("scenario_role_primary", ""),
        "diagnostic_tags": resolution.get("diagnostic_tags", ""),
        "m2877_eval_seed": int(eval_seed),
        "error_type": error_type,
        "error_message": error_message,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "prior_surface_execution": False,
        "package_limitation_execution": False,
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
        "package_labels_actor_visible": False,
        "blocker_labels_actor_visible": False,
        "diagnostic_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "ordinary_success_denominator_allowed": False,
        "diagnostic_only_no_verdict": True,
        "claim_boundary": CLAIM_SCOPE,
    }


def load_execution_artifact_rows(paths: dict[str, Path]) -> dict[str, list[dict[str, str]]]:
    return {
        "candidate_execution_rows": read_csv_rows(paths["candidate_execution_rows"]),
        "candidate_execution_failure_rows": read_csv_rows(paths["candidate_execution_failure_rows"]),
    }


def build_scenario_role_metric_rows(
    *,
    candidate_rows: list[dict[str, Any]],
    episode_rows: list[dict[str, str]],
    failure_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    episodes_by_candidate = _group_by(episode_rows, "candidate_id")
    failures_by_candidate = _group_by(failure_rows, "candidate_id")
    rows: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidate_rows, start=1):
        candidate_id = str(candidate["candidate_id"])
        candidate_episodes = episodes_by_candidate.get(candidate_id, [])
        candidate_failures = failures_by_candidate.get(candidate_id, [])
        first_episode = candidate_episodes[0] if candidate_episodes else {}
        rows.append(
            {
                "metric_id": f"m2877-scenario-role-metric-{index:04d}",
                "candidate_id": candidate_id,
                "task_source_id": candidate["task_source_id"],
                "scenario_role_primary": candidate["scenario_role_primary"],
                "source_family_tag": candidate["source_family_tag"],
                "task_family": candidate["task_family"],
                "source_edge": candidate["source_edge"],
                "episode_count": len(candidate_episodes),
                "failure_count": len(candidate_failures),
                "success_diagnostic": _episode_success(first_episode) if first_episode else "",
                "collision_diagnostic": _bool(first_episode.get("collision", False)) if first_episode else "",
                "termination_reason": first_episode.get("termination_reason", ""),
                "min_clearance_margin": first_episode.get("min_clearance_margin", ""),
                "return": first_episode.get("return", ""),
                "diagnostic_only_no_verdict": True,
                "ranking_claim_made": False,
                "actor_visible_allowed": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_failure_taxonomy_rows(
    *,
    candidate_rows: list[dict[str, Any]],
    episode_rows: list[dict[str, str]],
    failure_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    candidate_by_id = {str(row["candidate_id"]): row for row in candidate_rows}
    rows: list[dict[str, Any]] = []
    for episode in episode_rows:
        candidate = candidate_by_id.get(str(episode.get("candidate_id", "")), {})
        success = _episode_success(episode)
        collision = _bool(episode.get("collision", False))
        offtrack = str(episode.get("termination_reason", "")) == "off_track"
        if success:
            outcome_family = "diagnostic_success"
        elif collision:
            outcome_family = "diagnostic_collision"
        elif offtrack:
            outcome_family = "diagnostic_offtrack"
        else:
            outcome_family = "diagnostic_other"
        rows.append(
            {
                "failure_taxonomy_id": f"m2877-failure-taxonomy-{len(rows) + 1:04d}",
                "candidate_id": episode.get("candidate_id", ""),
                "task_source_id": episode.get("task_source_id", ""),
                "scenario_role_primary": candidate.get("scenario_role_primary", ""),
                "source_family_tag": episode.get("source_family_tag", candidate.get("source_family_tag", "")),
                "outcome_family": outcome_family,
                "termination_reason": episode.get("termination_reason", ""),
                "success": success,
                "collision": collision,
                "offtrack": offtrack,
                "execution_failure": False,
                "error_type": "",
                "diagnostic_only_no_verdict": True,
                "ranking_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    for failure in failure_rows:
        candidate = candidate_by_id.get(str(failure.get("candidate_id", "")), {})
        rows.append(
            {
                "failure_taxonomy_id": f"m2877-failure-taxonomy-{len(rows) + 1:04d}",
                "candidate_id": failure.get("candidate_id", ""),
                "task_source_id": failure.get("task_source_id", ""),
                "scenario_role_primary": candidate.get("scenario_role_primary", failure.get("scenario_role_primary", "")),
                "source_family_tag": failure.get("source_family_tag", candidate.get("source_family_tag", "")),
                "outcome_family": "execution_failure",
                "termination_reason": "",
                "success": False,
                "collision": False,
                "offtrack": False,
                "execution_failure": True,
                "error_type": failure.get("error_type", ""),
                "diagnostic_only_no_verdict": True,
                "ranking_claim_made": False,
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
    package_guard_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        actor_guard("p0_observation_dim", P0_OBSERVATION_DIM, 72),
        actor_guard("action_dim", ACTION_DIM, 3),
        actor_guard("hidden_oracle_actor_input_required", any_flag(candidate_rows, "hidden_oracle_actor_input_required"), False),
        actor_guard("actor_input_contract_changed", any_flag(episode_rows + failure_rows, "actor_input_contract_changed"), False),
        actor_guard("package_labels_actor_visible", any_flag(candidate_rows + episode_rows + failure_rows, "package_labels_actor_visible"), False),
        actor_guard("blocker_labels_actor_visible", any_flag(candidate_rows + episode_rows + failure_rows, "blocker_labels_actor_visible"), False),
        actor_guard("diagnostic_labels_actor_visible", any_flag(candidate_rows + episode_rows + failure_rows, "diagnostic_labels_actor_visible"), False),
        actor_guard("route_labels_actor_visible", any_flag(candidate_rows + episode_rows + failure_rows, "route_labels_actor_visible"), False),
        actor_guard("success_progress_labels_actor_visible", any_flag(candidate_rows + episode_rows + failure_rows, "success_progress_labels_actor_visible"), False),
        actor_guard("verdict_labels_actor_visible", any_flag(candidate_rows + episode_rows + failure_rows, "verdict_labels_actor_visible"), False),
        actor_guard("prior_surface_rows_actor_visible", any_flag(prior_exclusion_rows, "actor_visible_allowed"), False),
        actor_guard("package_guard_rows_actor_visible", any_flag(package_guard_rows, "actor_visible_allowed"), False),
        actor_guard("all_candidates_actor_contract_shape_72_action_3", all(_bool(row.get("actor_contract_shape_72_action_3", False)) for row in candidate_rows), True),
        actor_guard("all_resolutions_actor_contract_shape_72_action_3", all(_bool(row.get("actor_contract_shape_72_action_3", False)) for row in resolution_rows), True),
    ]


def actor_guard(field: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": f"m2877-actor-guard-{field}",
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
    all_candidates_accounted: bool,
) -> list[dict[str, Any]]:
    specs = [
        ("bounded_execution_artifact_completeness", "artifact", True, artifacts_present, "M2877 artifact set"),
        ("fresh_closed_loop_diagnostic_rows", "diagnostic_execution", True, episode_or_failure_rows_present, "candidate execution rows"),
        ("candidate_accounting", "lineage", True, all_candidates_accounted, "all 11 selected candidates accounted"),
        ("follow_up_result_audit_registered", "follow_up_route", True, follow_up_manifest_registered, "M2878 result-audit manifest"),
        ("package_publication", "package", False, False, "separate release gate"),
        ("repair_success", "repair", False, False, "future audited repair route"),
        ("recoverability_success", "recoverability", False, False, "future recoverability proof route"),
        ("localized_response_prediction_success", "diagnostic", False, False, "future audited route"),
        ("driver_performance", "performance", False, False, "future validation gate"),
        ("validation_readiness", "validation", False, False, "future validation-readiness manifest"),
        ("success_rate_verdict", "verdict", False, False, "future validation or promotion gate"),
        ("controller_ranking", "ranking", False, False, "future comparison gate"),
        ("source_family_ranking", "ranking", False, False, "future comparison gate"),
        ("scenario_role_ranking", "ranking", False, False, "future comparison gate"),
        ("winner_selection", "promotion", False, False, "future promotion gate"),
        ("checkpoint_promotion", "promotion", False, False, "future promotion gate"),
        ("paper_evidence", "paper", False, False, "Route B proof/generalization gates"),
        ("finite_window_vs_gru_conclusion", "paper", False, False, "Route B comparison gates"),
        ("current_response_sufficiency", "paper", False, False, "Route B comparison gates"),
        ("current_sim_verdict", "verdict", False, False, "future current-sim validation route"),
        ("high_fidelity_validation", "high_fidelity", False, False, "Route C source dependency and validation gates"),
        ("full_ideal_driver_completion", "goal", False, False, "full ideal driver gate"),
        ("level3_self_id", "self_id", False, False, "Route B self-ID proof gates"),
    ]
    return [claim(*spec) for spec in specs]


def claim(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m2877-claim-{claim_id}",
        "claim_family": family,
        "allowed_in_m2877": allowed,
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
    scenario_role_metric_rows: list[dict[str, Any]],
    failure_taxonomy_rows: list[dict[str, Any]],
    prior_exclusion_rows: list[dict[str, Any]],
    package_guard_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    episode_rows = artifact_rows["candidate_execution_rows"]
    failure_rows = artifact_rows["candidate_execution_failure_rows"]
    selected_ids = [row[0] for row in SELECTED_TASK_SOURCES]
    prior_unique_count = len({row["task_source_id"] for row in prior_exclusion_rows})
    checks = [
        ("source_artifacts_present", "lineage", all(source["source_exists"].values()), source["source_exists"], "all M2876/M2873/M1690/prior/spec/follow-up artifacts present", "lineage_invalid"),
        ("candidate_count", "candidate_surface", len(candidate_rows) == EXPECTED_CANDIDATE_COUNT, len(candidate_rows), EXPECTED_CANDIDATE_COUNT, "scenario_sampling_failure"),
        ("selected_task_source_ids_fixed", "candidate_surface", [row["task_source_id"] for row in candidate_rows] == selected_ids, [row["task_source_id"] for row in candidate_rows], selected_ids, "scenario_sampling_failure"),
        ("selected_l3_profile_only", "candidate_surface", {row["profile_name"] for row in candidate_rows} == {CANONICAL_PROFILE}, sorted({row["profile_name"] for row in candidate_rows}), CANONICAL_PROFILE, "contract_violation"),
        ("prior_surface_unique_count", "candidate_surface", prior_unique_count >= EXPECTED_PRIOR_SURFACE_UNIQUE_COUNT, prior_unique_count, f">={EXPECTED_PRIOR_SURFACE_UNIQUE_COUNT}", "lineage_invalid"),
        ("selected_prior_surface_execution_false", "candidate_surface", not any(_bool(row["prior_surface_excluded"]) for row in candidate_rows), [row["task_source_id"] for row in candidate_rows if _bool(row["prior_surface_excluded"])], [], "objective_overfit"),
        ("all_candidates_resolved", "execution", sum(1 for row in resolution_rows if _bool(row.get("execution_admitted", False))) == EXPECTED_CANDIDATE_COUNT, sum(1 for row in resolution_rows if _bool(row.get("execution_admitted", False))), EXPECTED_CANDIDATE_COUNT, "lineage_invalid"),
        ("all_candidates_accounted", "execution", len(episode_rows) + len(failure_rows) == len(resolution_rows), len(episode_rows) + len(failure_rows), len(resolution_rows), "lineage_invalid"),
        ("execution_rows", "execution", len(episode_rows) == EXPECTED_CANDIDATE_COUNT, len(episode_rows), EXPECTED_CANDIDATE_COUNT, "behavior_regression"),
        ("candidate_failure_rows_zero", "execution", len(failure_rows) == 0, len(failure_rows), 0, "behavior_regression"),
        ("all_selected_metrics_finite", "metric", selected_metrics_are_finite(episode_rows) if episode_rows else False, execution_summary.get("all_selected_metrics_finite"), True, "metric_artifact"),
        ("scenario_role_metric_rows", "metric", len(scenario_role_metric_rows) == EXPECTED_CANDIDATE_COUNT, len(scenario_role_metric_rows), EXPECTED_CANDIDATE_COUNT, "metric_artifact"),
        ("failure_taxonomy_rows", "metric", len(failure_taxonomy_rows) == len(episode_rows) + len(failure_rows), len(failure_taxonomy_rows), len(episode_rows) + len(failure_rows), "metric_artifact"),
        ("package_limitation_guard_rows", "boundary", bool(package_guard_rows), len(package_guard_rows), ">0", "lineage_invalid"),
        ("prior_surface_execution_false", "boundary", not any_flag(episode_rows + failure_rows, "prior_surface_execution"), any_flag(episode_rows + failure_rows, "prior_surface_execution"), False, "objective_overfit"),
        ("package_limitation_execution_false", "boundary", not any_flag(episode_rows + failure_rows, "package_limitation_execution"), any_flag(episode_rows + failure_rows, "package_limitation_execution"), False, "proof_washout"),
        ("protected_blocker_execution_false", "boundary", not any_flag(episode_rows + failure_rows, "protected_blocker_execution"), any_flag(episode_rows + failure_rows, "protected_blocker_execution"), False, "proof_washout"),
        ("hf3_blocker_execution_false", "boundary", not any_flag(episode_rows + failure_rows, "hf3_blocker_execution"), any_flag(episode_rows + failure_rows, "hf3_blocker_execution"), False, "proof_washout"),
        ("ordinary_denominator_false", "boundary", not any_flag(episode_rows + failure_rows + prior_exclusion_rows + package_guard_rows, "ordinary_success_denominator_allowed"), any_flag(episode_rows + failure_rows + prior_exclusion_rows + package_guard_rows, "ordinary_success_denominator_allowed"), False, "proof_washout"),
        ("actor_contract_guards_pass", "contract", all(_bool(row["status_pass"]) for row in actor_guard_rows), "all_pass" if all(_bool(row["status_pass"]) for row in actor_guard_rows) else actor_guard_rows, "all_pass", "contract_violation"),
        ("claim_boundary_rows_pass", "claim", all(_bool(row["status_pass"]) for row in claim_rows), "all_pass" if all(_bool(row["status_pass"]) for row in claim_rows) else claim_rows, "all_pass", "proof_washout"),
        ("ranking_false", "claim", not any_flag(episode_rows + failure_rows, "ranking_run"), any_flag(episode_rows + failure_rows, "ranking_run"), False, "objective_overfit"),
        ("driver_performance_claim_false", "claim", not any_flag(episode_rows + failure_rows, "driver_performance_claim_made"), any_flag(episode_rows + failure_rows, "driver_performance_claim_made"), False, "proof_washout"),
        ("paper_claim_false", "claim", not any_flag(episode_rows + failure_rows, "paper_claim_made"), any_flag(episode_rows + failure_rows, "paper_claim_made"), False, "proof_washout"),
        ("current_sim_verdict_false", "claim", not any_flag(episode_rows + failure_rows, "current_sim_verdict_claim_made"), any_flag(episode_rows + failure_rows, "current_sim_verdict_claim_made"), False, "proof_washout"),
        ("high_fidelity_validation_claim_false", "claim", not any_flag(episode_rows + failure_rows, "high_fidelity_validation_claim_made"), any_flag(episode_rows + failure_rows, "high_fidelity_validation_claim_made"), False, "proof_washout"),
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
        "gate_id": f"m2877-gate-{gate_id}",
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
    scenario_role_metric_rows: list[dict[str, Any]],
    failure_taxonomy_rows: list[dict[str, Any]],
    prior_exclusion_rows: list[dict[str, Any]],
    package_guard_rows: list[dict[str, Any]],
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
            "engineering_controller_route_a_post_package_refresh_fresh_closed_loop_evidence_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_post_package_refresh_fresh_closed_loop_evidence_preflight_fail"
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
        "scenario_role_metric_row_count": len(scenario_role_metric_rows),
        "failure_taxonomy_row_count": len(failure_taxonomy_rows),
        "prior_surface_exclusion_row_count": len(prior_exclusion_rows),
        "prior_surface_unique_task_source_count": len({row["task_source_id"] for row in prior_exclusion_rows}),
        "package_limitation_guard_row_count": len(package_guard_rows),
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
        "prior_surface_execution": any_flag(episode_rows + failure_rows, "prior_surface_execution"),
        "package_limitation_execution": any_flag(episode_rows + failure_rows, "package_limitation_execution"),
        "protected_blocker_execution": any_flag(episode_rows + failure_rows, "protected_blocker_execution"),
        "hf3_blocker_execution": any_flag(episode_rows + failure_rows, "hf3_blocker_execution"),
        "ordinary_success_denominator_allowed": any_flag(
            episode_rows + failure_rows + prior_exclusion_rows + package_guard_rows,
            "ordinary_success_denominator_allowed",
        ),
        "actor_input_contract_changed": any_flag(episode_rows + failure_rows, "actor_input_contract_changed"),
        "hidden_oracle_actor_input_required": any_flag(candidate_rows + episode_rows + failure_rows, "hidden_oracle_actor_input_required"),
        "package_labels_actor_visible": any_flag(candidate_rows + episode_rows + failure_rows, "package_labels_actor_visible"),
        "blocker_labels_actor_visible": any_flag(candidate_rows + episode_rows + failure_rows, "blocker_labels_actor_visible"),
        "diagnostic_labels_actor_visible": any_flag(candidate_rows + episode_rows + failure_rows, "diagnostic_labels_actor_visible"),
        "route_labels_actor_visible": any_flag(candidate_rows + episode_rows + failure_rows, "route_labels_actor_visible"),
        "success_progress_labels_actor_visible": any_flag(candidate_rows + episode_rows + failure_rows, "success_progress_labels_actor_visible"),
        "verdict_labels_actor_visible": any_flag(candidate_rows + episode_rows + failure_rows, "verdict_labels_actor_visible"),
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
        "# M2877 Engineering Controller Route A Post-Package Refresh Fresh Closed-Loop Evidence Preflight",
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
        f"- scenario-role metric rows: {summary['scenario_role_metric_row_count']}",
        f"- failure taxonomy rows: {summary['failure_taxonomy_row_count']}",
        f"- prior-surface exclusion rows: {summary['prior_surface_exclusion_row_count']}",
        f"- prior-surface unique task-source ids: {summary['prior_surface_unique_task_source_count']}",
        f"- package-limitation guard rows: {summary['package_limitation_guard_row_count']}",
        f"- actor-contract guard rows: {summary['actor_contract_guard_row_count']}",
        f"- gate matrix pass: {summary['gate_matrix_pass']}",
        f"- next blocker: `{summary['next_blocker']}`",
        f"- follow-up manifest: `{summary['follow_up_manifest']}`",
        "",
        "## Boundary",
        "",
        "M2877 is a bounded Route A diagnostic execution preflight. It records",
        "closed-loop diagnostic rows over the fixed 11-row post-package-refresh",
        "M1690 `L3_online_gru` surface selected by M2876. It does not publish a",
        "package, repair the controller, validate driver performance, rank",
        "families, or make paper/self-ID/current-sim/high-fidelity claims.",
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


def any_flag(rows: list[Mapping[str, Any]], key: str) -> bool:
    return any(_bool(row.get(key, False)) for row in rows)


def forbidden_execution_flag(row: Mapping[str, Any]) -> bool:
    return any(
        _bool(row.get(key, False))
        for key in (
            "prior_surface_execution",
            "package_limitation_execution",
            "protected_blocker_execution",
            "hf3_blocker_execution",
            "ordinary_success_denominator_allowed",
            "hidden_oracle_actor_input_required",
            "package_labels_actor_visible",
            "blocker_labels_actor_visible",
            "diagnostic_labels_actor_visible",
            "route_labels_actor_visible",
            "success_progress_labels_actor_visible",
            "verdict_labels_actor_visible",
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
    parser.add_argument("--m2876-design", type=Path, default=DEFAULT_M2876_DESIGN)
    parser.add_argument("--m2873-dir", type=Path, default=DEFAULT_M2873_DIR)
    parser.add_argument("--m2737-dir", type=Path, default=DEFAULT_M2737_DIR)
    parser.add_argument("--m2807-dir", type=Path, default=DEFAULT_M2807_DIR)
    parser.add_argument("--m2816-dir", type=Path, default=DEFAULT_M2816_DIR)
    parser.add_argument("--m2828-dir", type=Path, default=DEFAULT_M2828_DIR)
    parser.add_argument("--m2838-dir", type=Path, default=DEFAULT_M2838_DIR)
    parser.add_argument("--m2868-dir", type=Path, default=DEFAULT_M2868_DIR)
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
    summary = run_post_package_refresh_fresh_closed_loop_evidence_preflight(
        m1690_workload=args.m1690_workload,
        m2876_design=args.m2876_design,
        m2873_dir=args.m2873_dir,
        m2737_dir=args.m2737_dir,
        m2807_dir=args.m2807_dir,
        m2816_dir=args.m2816_dir,
        m2828_dir=args.m2828_dir,
        m2838_dir=args.m2838_dir,
        m2868_dir=args.m2868_dir,
        executable_specs=args.executable_specs,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        eval_seed_base=args.eval_seed_base,
        device=args.device,
        resume=not args.no_resume,
    )
    print(
        "M2877 post-package-refresh fresh closed-loop evidence preflight: "
        f"status={summary['status_pass']} "
        f"candidates={summary['candidate_count']} "
        f"episodes={summary['candidate_execution_row_count']} "
        f"failures={summary['candidate_execution_failure_row_count']} "
        f"next={summary['next_blocker']}"
    )


if __name__ == "__main__":
    main()
