"""Materialize the Route A current-M1690 exact-executable reentry panel.

M2714 reads the M2713 design, M2693 executed anchor rows, M1690 executable
workload matrix, M2710 protected proposal artifacts, M2638 HF3 blocker, and
post-M2470 route split. It writes a no-execution exact executable candidate
panel plus protected proposal exclusion rows. It does not reset, step, roll out,
validate, train, rank, promote, or make driver-performance claims.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import DEFAULT_EXECUTABLE_WORKLOAD
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2714-engineering-controller-route-a-current-m1690-exact-executable-reentry-panel-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2715-engineering-controller-route-a-current-m1690-exact-executable-reentry-panel-materialization-result-audit"
)
DEFAULT_M2693_DIR = Path(
    "runs/m2693_engineering_controller_source_diverse_offtrack_protected_bounded_execution_preflight"
)
DEFAULT_M2710_DIR = Path(
    "runs/m2710_engineering_controller_protected_runner_current_m1690_workload_fixture_support"
)
DEFAULT_M2712_SYNTHESIS = Path(
    "docs/m2712-engineering-controller-protected-runner-current-m1690-workload-fixture-support-branch-synthesis.md"
)
DEFAULT_M2713_DESIGN = Path(
    "docs/m2713-engineering-controller-route-a-current-m1690-exact-executable-reentry-panel-design.md"
)
DEFAULT_M2638_BLOCKER = Path(
    "docs/m2638-engineering-controller-route-c-hf3-source-dependency-blocker-report-and-user-supplied-source-contract-design.md"
)
DEFAULT_ROUTE_PLAN = Path("docs/post-m2470-route-plan.md")
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2714_engineering_controller_route_a_current_m1690_exact_executable_reentry_panel"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2714-engineering-controller-route-a-current-m1690-exact-executable-reentry-panel-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/"
    "m2715-engineering-controller-route-a-current-m1690-exact-executable-reentry-panel-materialization-result-audit.json"
)

SELECTED_PROFILES = (
    "L0_current_masked",
    "L2_window_50_current_tiled",
    "L3_online_gru",
    "L3_reset_control_corrected",
)
PROFILE_ROLES = {
    "L0_current_masked": "current_response_baseline",
    "L2_window_50_current_tiled": "finite_window_current_tiled",
    "L3_online_gru": "online_gru_history",
    "L3_reset_control_corrected": "reset_truncated_control",
}

ADMITTED_EXISTING_STATUS = "exact_executable_reentry_admitted_existing_m1690_workload"
MISSING_WORKLOAD_STATUS = "exact_executable_reentry_rejected_missing_m1690_workload"
MISSING_CONFIG_STATUS = "exact_executable_reentry_rejected_missing_profile_config"
MISSING_CHECKPOINT_STATUS = "exact_executable_reentry_rejected_missing_checkpoint"
PROTECTED_EXCLUSION_STATUS = "exact_executable_reentry_excluded_m2710_proposed_protected_row"
HF3_EXCLUSION_STATUS = "exact_executable_reentry_excluded_hf3_dependency_blocked"
M2710_PROPOSED_NEW_STATUS = "workload_fixture_support_proposed_new_current_m1690_row"
M2710_EXACT_ABSENT_STATUS = "proposed_new_current_m1690_workload_row_not_existing_match"
M2710_BLOCKER_ABSENT_STATUS = "workload_fixture_support_blocker_existing_m1690_match_absent"

CLAIM_SCOPE = (
    "M2714 Route A current-M1690 exact-executable reentry panel materialization only; "
    "existing M1690 workload ids may be reassembled into exact executable candidate, "
    "profile context, protected proposal exclusion, HF3 blocker, actor-contract, "
    "claim-boundary, and gate rows, but no reset, step, rollout, replay, validation, "
    "training, PPO, private holdout, profile-specific tuning, ranking, winner selection, "
    "promotion, success-rate verdict, repair-success, driver-performance, paper, "
    "finite-window-vs-GRU, current-response, current-sim, high-fidelity validation, "
    "full ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "execution result, validation result, protected mitigation preservation result, "
    "repair success, driver performance, controller-family ranking, winner selection, "
    "checkpoint promotion, success-rate verdict, paper evidence, finite-window-vs-GRU "
    "conclusion, current-response sufficiency, current-sim verdict, high-fidelity "
    "validation readiness or result, full ideal driver completion, or level3 "
    "self-identification"
)

FALSE_CLAIM_FLAGS = {
    "environment_reset_run": False,
    "environment_step_run": False,
    "policy_action_run": False,
    "policy_rollout_run": False,
    "replay_run": False,
    "execution_run": False,
    "validation_run": False,
    "measured_validation_run": False,
    "training_run": False,
    "ppo_run": False,
    "private_holdout_used": False,
    "profile_specific_tuning": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_verdict_claim_made": False,
    "repair_success_claim_made": False,
    "driver_performance_claim_made": False,
    "validation_readiness_claim_made": False,
    "validation_result_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "current_response_sufficiency_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_simulation_run": False,
    "high_fidelity_validation_claim_made": False,
    "full_ideal_driver_gate_passed": False,
    "full_ideal_driver_completion_claim_made": False,
    "level3_self_id_claim_made": False,
}

INPUT_SOURCE_FIELDNAMES = [
    "source_artifact_id",
    "source_path",
    "source_exists",
    "required",
    "row_count_or_summary",
    "source_role",
    "claim_scope",
    "blocked_interpretation",
]
CANDIDATE_FIELDNAMES = [
    "candidate_id",
    "anchor_task_source_id",
    "anchor_workload_id",
    "workload_id",
    "task_source_id",
    "profile_name",
    "profile_role",
    "task_family",
    "source_edge",
    "window_tag",
    "executable_source_family",
    "env_template_family",
    "strata",
    "profile_config_path",
    "checkpoint_path",
    "config_exists",
    "checkpoint_exists",
    "environment_rollout_scheduled",
    "training_scheduled",
    "profile_specific_tuning",
    "anchor_termination_reason",
    "anchor_success",
    "anchor_target_family",
    "exact_executable_reentry_status",
    "existing_m1690_workload_id_source_backed",
    "execution_candidate",
    "execution_run",
    "materialization_only_no_execution",
    "diagnostic_only_no_verdict",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "target_labels_actor_visible",
    "protected_labels_actor_visible",
    "protected_rows_in_success_denominator",
    "claim_scope",
]
PROFILE_CONTEXT_FIELDNAMES = [
    "profile_context_id",
    "candidate_id",
    "anchor_task_source_id",
    "workload_id",
    "profile_name",
    "profile_role",
    "profile_context_status",
    "comparison_or_ranking_claim_allowed",
    "finite_window_vs_gru_claim_allowed",
    "current_response_sufficiency_claim_allowed",
    "execution_run",
    "materialization_only_no_execution",
    "diagnostic_only_no_verdict",
    "claim_scope",
]
PROTECTED_EXCLUSION_FIELDNAMES = [
    "exclusion_id",
    "workload_fixture_proposal_id",
    "support_candidate_id",
    "proposed_workload_id",
    "profile_name",
    "protected_task_family",
    "protected_source_edge",
    "workload_fixture_support_status",
    "exact_match_status",
    "blocker_type",
    "execution_admitted",
    "exact_existing_m1690_match",
    "ready_existing_current_m1690_row",
    "protected_rows_in_success_denominator",
    "exclusion_status",
    "actor_visible",
    "target_labels_actor_visible",
    "protected_labels_actor_visible",
    "hidden_oracle_actor_input_required",
    "materialization_only_no_execution",
    "diagnostic_only_no_verdict",
    "claim_scope",
]
HF3_BLOCKER_FIELDNAMES = [
    "hf3_blocker_id",
    "source_path",
    "source_exists",
    "availability_blocker",
    "hf3_route_paused",
    "execution_candidate",
    "exclusion_status",
    "required_follow_up",
    "actor_visible",
    "claim_scope",
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
    "allowed_in_m2714",
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
    "input_source_rows",
    "exact_executable_candidate_rows",
    "profile_context_rows",
    "protected_proposal_exclusion_rows",
    "hf3_dependency_blocker_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "doc",
]


def materialize_current_m1690_exact_executable_reentry_panel(
    *,
    m1690_workload: Path | str = DEFAULT_EXECUTABLE_WORKLOAD,
    m2693_dir: Path | str = DEFAULT_M2693_DIR,
    m2710_dir: Path | str = DEFAULT_M2710_DIR,
    m2712_synthesis: Path | str = DEFAULT_M2712_SYNTHESIS,
    m2713_design: Path | str = DEFAULT_M2713_DESIGN,
    m2638_blocker: Path | str = DEFAULT_M2638_BLOCKER,
    route_plan: Path | str = DEFAULT_ROUTE_PLAN,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path))
    source = load_source_artifacts(
        m1690_workload=Path(m1690_workload),
        m2693_dir=Path(m2693_dir),
        m2710_dir=Path(m2710_dir),
        m2712_synthesis=Path(m2712_synthesis),
        m2713_design=Path(m2713_design),
        m2638_blocker=Path(m2638_blocker),
        route_plan=Path(route_plan),
        follow_up_manifest=Path(follow_up_manifest),
    )

    input_source_rows = build_input_source_rows(source)
    candidate_rows = build_exact_executable_candidate_rows(source)
    profile_context_rows = build_profile_context_rows(candidate_rows)
    protected_exclusion_rows = build_protected_proposal_exclusion_rows(source)
    hf3_blocker_rows = build_hf3_dependency_blocker_rows(source)

    write_csv_rows(paths["input_source_rows"], input_source_rows, fieldnames=INPUT_SOURCE_FIELDNAMES)
    write_csv_rows(
        paths["exact_executable_candidate_rows"],
        candidate_rows,
        fieldnames=CANDIDATE_FIELDNAMES,
    )
    write_csv_rows(paths["profile_context_rows"], profile_context_rows, fieldnames=PROFILE_CONTEXT_FIELDNAMES)
    write_csv_rows(
        paths["protected_proposal_exclusion_rows"],
        protected_exclusion_rows,
        fieldnames=PROTECTED_EXCLUSION_FIELDNAMES,
    )
    write_csv_rows(paths["hf3_dependency_blocker_rows"], hf3_blocker_rows, fieldnames=HF3_BLOCKER_FIELDNAMES)

    status = evaluate_materialization(source, candidate_rows, protected_exclusion_rows, hf3_blocker_rows)
    actor_contract_guard_rows = build_actor_contract_guard_rows(source, status)
    claim_boundary_rows = build_claim_boundary_rows(status, follow_up_manifest=Path(follow_up_manifest))
    gate_rows = build_gate_matrix_rows(
        source=source,
        status=status,
        input_source_rows=input_source_rows,
        candidate_rows=candidate_rows,
        profile_context_rows=profile_context_rows,
        protected_exclusion_rows=protected_exclusion_rows,
        hf3_blocker_rows=hf3_blocker_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        required_artifacts_present=False,
    )
    write_csv_rows(paths["actor_contract_guard_rows"], actor_contract_guard_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_boundary_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"})
    gate_rows = build_gate_matrix_rows(
        source=source,
        status=status,
        input_source_rows=input_source_rows,
        candidate_rows=candidate_rows,
        profile_context_rows=profile_context_rows,
        protected_exclusion_rows=protected_exclusion_rows,
        hf3_blocker_rows=hf3_blocker_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        status=status,
        input_source_rows=input_source_rows,
        candidate_rows=candidate_rows,
        profile_context_rows=profile_context_rows,
        protected_exclusion_rows=protected_exclusion_rows,
        hf3_blocker_rows=hf3_blocker_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        follow_up_manifest=Path(follow_up_manifest),
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    gate_rows = build_gate_matrix_rows(
        source=source,
        status=status,
        input_source_rows=input_source_rows,
        candidate_rows=candidate_rows,
        profile_context_rows=profile_context_rows,
        protected_exclusion_rows=protected_exclusion_rows,
        hf3_blocker_rows=hf3_blocker_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        status=status,
        input_source_rows=input_source_rows,
        candidate_rows=candidate_rows,
        profile_context_rows=profile_context_rows,
        protected_exclusion_rows=protected_exclusion_rows,
        hf3_blocker_rows=hf3_blocker_rows,
        actor_contract_guard_rows=actor_contract_guard_rows,
        claim_boundary_rows=claim_boundary_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        follow_up_manifest=Path(follow_up_manifest),
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "input_source_rows": output_dir / "input_source_rows.csv",
        "exact_executable_candidate_rows": output_dir / "exact_executable_candidate_rows.csv",
        "profile_context_rows": output_dir / "profile_context_rows.csv",
        "protected_proposal_exclusion_rows": output_dir / "protected_proposal_exclusion_rows.csv",
        "hf3_dependency_blocker_rows": output_dir / "hf3_dependency_blocker_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m1690_workload: Path,
    m2693_dir: Path,
    m2710_dir: Path,
    m2712_synthesis: Path,
    m2713_design: Path,
    m2638_blocker: Path,
    route_plan: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2713_design": m2713_design,
        "m2712_synthesis": m2712_synthesis,
        "m1690_workload_matrix": m1690_workload,
        "m2693_summary": m2693_dir / "summary.json",
        "m2693_target_execution_rows": m2693_dir / "target_execution_rows.csv",
        "m2710_summary": m2710_dir / "summary.json",
        "m2710_protected_workload_fixture_proposal_rows": (
            m2710_dir / "protected_workload_fixture_proposal_rows.csv"
        ),
        "m2710_exact_match_admission_rows": m2710_dir / "exact_match_admission_rows.csv",
        "m2710_workload_fixture_support_blocker_rows": m2710_dir / "workload_fixture_support_blocker_rows.csv",
        "m2638_hf3_dependency_blocker": m2638_blocker,
        "post_m2470_route_plan": route_plan,
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2713_design_text": read_text(paths["m2713_design"]),
        "m2712_synthesis_text": read_text(paths["m2712_synthesis"]),
        "m2638_hf3_dependency_blocker_text": read_text(paths["m2638_hf3_dependency_blocker"]),
        "post_m2470_route_plan_text": read_text(paths["post_m2470_route_plan"]),
        "m1690_workload_matrix": read_csv_rows(paths["m1690_workload_matrix"]),
        "m2693_summary": read_json(paths["m2693_summary"]) if source_exists["m2693_summary"] else {},
        "m2693_target_execution_rows": read_csv_rows(paths["m2693_target_execution_rows"]),
        "m2710_summary": read_json(paths["m2710_summary"]) if source_exists["m2710_summary"] else {},
        "m2710_protected_workload_fixture_proposal_rows": read_csv_rows(
            paths["m2710_protected_workload_fixture_proposal_rows"]
        ),
        "m2710_exact_match_admission_rows": read_csv_rows(paths["m2710_exact_match_admission_rows"]),
        "m2710_workload_fixture_support_blocker_rows": read_csv_rows(
            paths["m2710_workload_fixture_support_blocker_rows"]
        ),
    }


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def build_input_source_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    source_roles = {
        "m2713_design": "exact-executable reentry design and output contract",
        "m2712_synthesis": "protected support branch closure and route decision",
        "m1690_workload_matrix": "existing source-backed current-M1690 workload id reference",
        "m2693_summary": "recent bounded current-sim execution summary",
        "m2693_target_execution_rows": "nine executed anchor task_source_id rows",
        "m2710_summary": "protected workload fixture support materialization summary",
        "m2710_protected_workload_fixture_proposal_rows": "protected proposal rows to exclude from execution",
        "m2710_exact_match_admission_rows": "protected proposal exact-match status rows",
        "m2710_workload_fixture_support_blocker_rows": "protected proposal blocker status rows",
        "m2638_hf3_dependency_blocker": "HF3 selected-platform dependency blocker",
        "post_m2470_route_plan": "Route A/B/C split and no-hidden-oracle boundary",
        "follow_up_manifest": "M2715 materialization result audit registration",
    }
    return [
        {
            "source_artifact_id": artifact_id,
            "source_path": str(path),
            "source_exists": source["source_exists"][artifact_id],
            "required": True,
            "row_count_or_summary": source_summary_value(source, artifact_id),
            "source_role": source_roles[artifact_id],
            "claim_scope": CLAIM_SCOPE,
            "blocked_interpretation": FORBIDDEN_INTERPRETATION,
        }
        for artifact_id, path in source["paths"].items()
    ]


def source_summary_value(source: dict[str, Any], artifact_id: str) -> str:
    if artifact_id == "m2713_design":
        return "decision_present=" + str(
            "admit_current_m1690_exact_executable_reentry_panel_materialization_preflight"
            in source["m2713_design_text"]
        )
    if artifact_id == "m2712_synthesis":
        return "mentions_m2713_or_m2714=" + str(
            "m2713" in source["m2712_synthesis_text"].lower()
            or "m2714" in source["m2712_synthesis_text"].lower()
        )
    if artifact_id == "post_m2470_route_plan":
        return "route_a_present=" + str("Route A: Engineering Controller Mainline" in source["post_m2470_route_plan_text"])
    if artifact_id == "m2638_hf3_dependency_blocker":
        text = source["m2638_hf3_dependency_blocker_text"].lower()
        return "hf3_dependency_blocker_present=" + str("dependency" in text or "source" in text)
    if artifact_id in {
        "m1690_workload_matrix",
        "m2693_target_execution_rows",
        "m2710_protected_workload_fixture_proposal_rows",
        "m2710_exact_match_admission_rows",
        "m2710_workload_fixture_support_blocker_rows",
    }:
        return f"rows={len(source[artifact_id])}"
    if artifact_id == "m2693_summary":
        summary = source["m2693_summary"]
        return f"status_pass={summary.get('status_pass', '')};target_rows={summary.get('target_execution_row_count', '')}"
    if artifact_id == "m2710_summary":
        summary = source["m2710_summary"]
        return (
            f"status_pass={summary.get('status_pass', '')};"
            f"protected_proposals={summary.get('workload_fixture_proposal_row_count', '')}"
        )
    if artifact_id == "follow_up_manifest":
        return f"exists={source['source_exists'][artifact_id]}"
    return ""


def build_exact_executable_candidate_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    workload_by_task_profile = {
        (str(row.get("task_source_id", "")), str(row.get("profile_name", ""))): row
        for row in source["m1690_workload_matrix"]
    }
    anchors_by_task_source: dict[str, dict[str, str]] = {}
    for row in source["m2693_target_execution_rows"]:
        task_source_id = str(row.get("task_source_id", ""))
        if task_source_id and task_source_id not in anchors_by_task_source:
            anchors_by_task_source[task_source_id] = row

    rows: list[dict[str, Any]] = []
    for anchor_index, task_source_id in enumerate(sorted(anchors_by_task_source), start=1):
        anchor = anchors_by_task_source[task_source_id]
        for profile_index, profile_name in enumerate(SELECTED_PROFILES, start=1):
            workload = workload_by_task_profile.get((task_source_id, profile_name), {})
            row_exists = bool(workload)
            config_exists = as_bool(workload.get("config_exists", False))
            checkpoint_exists = as_bool(workload.get("checkpoint_exists", False))
            environment_rollout_scheduled = as_bool(workload.get("environment_rollout_scheduled", False))
            training_scheduled = as_bool(workload.get("training_scheduled", False))
            profile_specific_tuning = as_bool(workload.get("profile_specific_tuning", False))
            status = ADMITTED_EXISTING_STATUS
            if not row_exists:
                status = MISSING_WORKLOAD_STATUS
            elif not config_exists:
                status = MISSING_CONFIG_STATUS
            elif not checkpoint_exists:
                status = MISSING_CHECKPOINT_STATUS

            rows.append(
                {
                    "candidate_id": f"m2714-exact-executable-candidate-{anchor_index:04d}-{profile_index:02d}",
                    "anchor_task_source_id": task_source_id,
                    "anchor_workload_id": anchor.get("workload_id", ""),
                    "workload_id": workload.get("workload_id", ""),
                    "task_source_id": workload.get("task_source_id", task_source_id),
                    "profile_name": profile_name,
                    "profile_role": PROFILE_ROLES[profile_name],
                    "task_family": workload.get("task_family", anchor.get("task_family", "")),
                    "source_edge": workload.get("source_edge", anchor.get("source_edge", "")),
                    "window_tag": workload.get("window_tag", anchor.get("window_tag", "")),
                    "executable_source_family": workload.get("executable_source_family", ""),
                    "env_template_family": workload.get("env_template_family", ""),
                    "strata": workload.get("strata", ""),
                    "profile_config_path": workload.get("profile_config_path", ""),
                    "checkpoint_path": workload.get("checkpoint_path", ""),
                    "config_exists": config_exists,
                    "checkpoint_exists": checkpoint_exists,
                    "environment_rollout_scheduled": environment_rollout_scheduled,
                    "training_scheduled": training_scheduled,
                    "profile_specific_tuning": profile_specific_tuning,
                    "anchor_termination_reason": anchor.get("termination_reason", ""),
                    "anchor_success": as_bool(anchor.get("success", False)),
                    "anchor_target_family": anchor.get("target_family", ""),
                    "exact_executable_reentry_status": status,
                    "existing_m1690_workload_id_source_backed": row_exists,
                    "execution_candidate": status == ADMITTED_EXISTING_STATUS
                    and not environment_rollout_scheduled
                    and not training_scheduled
                    and not profile_specific_tuning,
                    "execution_run": False,
                    "materialization_only_no_execution": True,
                    "diagnostic_only_no_verdict": True,
                    "actor_input_contract_changed": False,
                    "hidden_oracle_actor_input_required": False,
                    "target_labels_actor_visible": False,
                    "protected_labels_actor_visible": False,
                    "protected_rows_in_success_denominator": False,
                    "claim_scope": CLAIM_SCOPE,
                }
            )
    return rows


def build_profile_context_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "profile_context_id": f"m2714-profile-context-{index:04d}",
            "candidate_id": row["candidate_id"],
            "anchor_task_source_id": row["anchor_task_source_id"],
            "workload_id": row["workload_id"],
            "profile_name": row["profile_name"],
            "profile_role": row["profile_role"],
            "profile_context_status": "profile_context_materialized_no_comparison_claim",
            "comparison_or_ranking_claim_allowed": False,
            "finite_window_vs_gru_claim_allowed": False,
            "current_response_sufficiency_claim_allowed": False,
            "execution_run": False,
            "materialization_only_no_execution": True,
            "diagnostic_only_no_verdict": True,
            "claim_scope": CLAIM_SCOPE,
        }
        for index, row in enumerate(candidate_rows, start=1)
    ]


def build_protected_proposal_exclusion_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    admissions = {
        str(row.get("workload_fixture_proposal_id", "")): row
        for row in source["m2710_exact_match_admission_rows"]
    }
    blockers = {
        str(row.get("workload_fixture_proposal_id", "")): row
        for row in source["m2710_workload_fixture_support_blocker_rows"]
    }
    rows = []
    for index, proposal in enumerate(source["m2710_protected_workload_fixture_proposal_rows"], start=1):
        proposal_id = str(proposal.get("workload_fixture_proposal_id", ""))
        admission = admissions.get(proposal_id, {})
        blocker = blockers.get(proposal_id, {})
        exact_existing = as_bool(proposal.get("exact_existing_m1690_match", False))
        ready_existing = str(proposal.get("workload_fixture_support_status", "")) != M2710_PROPOSED_NEW_STATUS
        rows.append(
            {
                "exclusion_id": f"m2714-protected-proposal-exclusion-{index:04d}",
                "workload_fixture_proposal_id": proposal_id,
                "support_candidate_id": proposal.get("support_candidate_id", ""),
                "proposed_workload_id": proposal.get("proposed_workload_id", ""),
                "profile_name": proposal.get("profile_name", ""),
                "protected_task_family": proposal.get("protected_task_family", ""),
                "protected_source_edge": proposal.get("protected_source_edge", ""),
                "workload_fixture_support_status": proposal.get("workload_fixture_support_status", ""),
                "exact_match_status": admission.get("exact_match_status", ""),
                "blocker_type": blocker.get("blocker_type", ""),
                "execution_admitted": as_bool(admission.get("execution_admitted", False)),
                "exact_existing_m1690_match": exact_existing,
                "ready_existing_current_m1690_row": ready_existing,
                "protected_rows_in_success_denominator": as_bool(
                    proposal.get("protected_rows_in_success_denominator", False)
                ),
                "exclusion_status": PROTECTED_EXCLUSION_STATUS,
                "actor_visible": False,
                "target_labels_actor_visible": as_bool(proposal.get("target_labels_actor_visible", False)),
                "protected_labels_actor_visible": as_bool(proposal.get("protected_labels_actor_visible", False)),
                "hidden_oracle_actor_input_required": as_bool(
                    proposal.get("hidden_oracle_actor_input_required", False)
                ),
                "materialization_only_no_execution": True,
                "diagnostic_only_no_verdict": True,
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def build_hf3_dependency_blocker_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "hf3_blocker_id": "m2714-hf3-dependency-blocker-0001",
            "source_path": str(source["paths"]["m2638_hf3_dependency_blocker"]),
            "source_exists": source["source_exists"]["m2638_hf3_dependency_blocker"],
            "availability_blocker": "dependency_source_unavailable",
            "hf3_route_paused": True,
            "execution_candidate": False,
            "exclusion_status": HF3_EXCLUSION_STATUS,
            "required_follow_up": "user-supplied HF3 dependency source before selected-platform execution",
            "actor_visible": False,
            "claim_scope": CLAIM_SCOPE,
        }
    ]


def evaluate_materialization(
    source: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    protected_exclusion_rows: list[dict[str, Any]],
    hf3_blocker_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    anchor_task_source_ids = sorted({row.get("task_source_id", "") for row in source["m2693_target_execution_rows"] if row.get("task_source_id")})
    candidate_statuses = {row["exact_executable_reentry_status"] for row in candidate_rows}
    protected_support_statuses = {row["workload_fixture_support_status"] for row in protected_exclusion_rows}
    protected_exact_statuses = {row["exact_match_status"] for row in protected_exclusion_rows}
    protected_blocker_statuses = {row["blocker_type"] for row in protected_exclusion_rows}
    protected_execution_admitted_count = sum(as_bool(row["execution_admitted"]) for row in protected_exclusion_rows)
    ready_existing_count = sum(as_bool(row["ready_existing_current_m1690_row"]) for row in protected_exclusion_rows)
    exact_match_count = sum(as_bool(row["exact_existing_m1690_match"]) for row in protected_exclusion_rows)
    fabricated_match_count = sum(
        as_bool(row["exact_existing_m1690_match"]) and not str(row["proposed_workload_id"])
        for row in protected_exclusion_rows
    )
    missing_selected_profile_row_count = sum(
        row["exact_executable_reentry_status"] == MISSING_WORKLOAD_STATUS for row in candidate_rows
    )
    candidate_rows_all_existing_m1690 = bool(candidate_rows) and all(
        as_bool(row["existing_m1690_workload_id_source_backed"]) for row in candidate_rows
    )
    candidate_rows_all_clean_schedule = bool(candidate_rows) and all(
        not as_bool(row["environment_rollout_scheduled"])
        and not as_bool(row["training_scheduled"])
        and not as_bool(row["profile_specific_tuning"])
        for row in candidate_rows
    )
    return {
        "source_artifacts_all_present": all(source["source_exists"].values()),
        "m1690_existing_workload_row_count": len(source["m1690_workload_matrix"]),
        "m2693_anchor_task_source_ids": anchor_task_source_ids,
        "m2693_anchor_task_source_id_count": len(anchor_task_source_ids),
        "selected_profile_count": len(SELECTED_PROFILES),
        "expected_exact_executable_candidate_row_count": len(anchor_task_source_ids) * len(SELECTED_PROFILES),
        "candidate_rows_all_existing_m1690": candidate_rows_all_existing_m1690,
        "candidate_rows_all_clean_schedule": candidate_rows_all_clean_schedule,
        "candidate_rows_all_admitted_existing": candidate_statuses == {ADMITTED_EXISTING_STATUS},
        "missing_selected_profile_row_count": missing_selected_profile_row_count,
        "candidate_profile_set": sorted({row["profile_name"] for row in candidate_rows}),
        "candidate_workload_id_unique_count": len({row["workload_id"] for row in candidate_rows if row["workload_id"]}),
        "protected_support_statuses": sorted(protected_support_statuses),
        "protected_exact_statuses": sorted(protected_exact_statuses),
        "protected_blocker_statuses": sorted(protected_blocker_statuses),
        "protected_execution_admitted_row_count": protected_execution_admitted_count,
        "ready_existing_current_m1690_workload_row_count": ready_existing_count,
        "existing_exact_m1690_match_count": exact_match_count,
        "fabricated_existing_m1690_match_count": fabricated_match_count,
        "protected_exclusions_all_proposed_new": protected_support_statuses == {M2710_PROPOSED_NEW_STATUS},
        "protected_exclusions_all_exact_absent": protected_exact_statuses == {M2710_EXACT_ABSENT_STATUS},
        "protected_exclusions_all_blocked_absent": protected_blocker_statuses == {M2710_BLOCKER_ABSENT_STATUS},
        "protected_exclusions_all_no_execution": protected_execution_admitted_count == 0,
        "protected_exclusions_all_outside_denominator": all(
            not as_bool(row["protected_rows_in_success_denominator"]) for row in protected_exclusion_rows
        ),
        "protected_exclusions_actor_invisible": all(
            not as_bool(row["actor_visible"])
            and not as_bool(row["target_labels_actor_visible"])
            and not as_bool(row["protected_labels_actor_visible"])
            and not as_bool(row["hidden_oracle_actor_input_required"])
            for row in protected_exclusion_rows
        ),
        "hf3_blocker_row_count": len(hf3_blocker_rows),
        "hf3_dependency_blocker_present": any(as_bool(row["source_exists"]) for row in hf3_blocker_rows),
        "hidden_oracle_actor_input_detected": any(
            as_bool(row["hidden_oracle_actor_input_required"]) for row in candidate_rows + protected_exclusion_rows
        ),
        "target_labels_actor_visible_detected": any(
            as_bool(row.get("target_labels_actor_visible", False)) for row in candidate_rows + protected_exclusion_rows
        ),
        "protected_labels_actor_visible_detected": any(
            as_bool(row.get("protected_labels_actor_visible", False)) for row in candidate_rows + protected_exclusion_rows
        ),
        "protected_rows_in_success_denominator": any(
            as_bool(row.get("protected_rows_in_success_denominator", False))
            for row in candidate_rows + protected_exclusion_rows
        ),
    }


def build_actor_contract_guard_rows(source: dict[str, Any], status: dict[str, Any]) -> list[dict[str, Any]]:
    guards = [
        ("observation_shape", P0_OBSERVATION_DIM, 72),
        ("action_shape", ACTION_DIM, 3),
        ("action_mapping", "steer,throttle,brake", "steer,throttle,brake"),
        ("actor_input_contract_changed", False, False),
        ("hidden_oracle_actor_input_detected", status["hidden_oracle_actor_input_detected"], False),
        ("target_labels_actor_visible_detected", status["target_labels_actor_visible_detected"], False),
        ("protected_labels_actor_visible_detected", status["protected_labels_actor_visible_detected"], False),
        ("blocker_labels_actor_visible", False, False),
        ("route_labels_actor_visible", False, False),
        ("success_progress_verdict_labels_actor_visible", False, False),
        ("protected_rows_in_success_denominator", status["protected_rows_in_success_denominator"], False),
        ("post_m2470_route_a_boundary_present", "Route A: Engineering Controller Mainline" in source["post_m2470_route_plan_text"], True),
    ]
    return [
        {
            "guard_id": f"m2714-actor-guard-{index:04d}",
            "contract_field": field,
            "observed_value": observed,
            "expected_value": expected,
            "status_pass": observed == expected,
            "actor_visible": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (field, observed, expected) in enumerate(guards, start=1)
    ]


def build_claim_boundary_rows(status: dict[str, Any], *, follow_up_manifest: Path) -> list[dict[str, Any]]:
    rows = [
        {
            "claim_id": "m2714-claim-0001",
            "claim_family": "current_m1690_exact_executable_reentry_panel_materialization",
            "allowed_in_m2714": True,
            "claim_made": status["candidate_rows_all_existing_m1690"],
            "status_pass": status["candidate_rows_all_existing_m1690"],
            "evidence_required_before_claim": "36 source-backed existing M1690 workload candidate rows",
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "claim_id": "m2714-claim-0002",
            "claim_family": "protected_proposal_exclusion_accounting",
            "allowed_in_m2714": True,
            "claim_made": status["protected_exclusions_all_no_execution"],
            "status_pass": status["protected_exclusions_all_no_execution"],
            "evidence_required_before_claim": "all M2710 proposed protected rows excluded from execution",
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "claim_id": "m2714-claim-0003",
            "claim_family": "follow_up_result_audit_registered",
            "allowed_in_m2714": True,
            "claim_made": follow_up_manifest.exists(),
            "status_pass": follow_up_manifest.exists(),
            "evidence_required_before_claim": str(follow_up_manifest),
            "claim_boundary": CLAIM_SCOPE,
        },
    ]
    forbidden_claims = [
        "execution_result",
        "protected_execution_result",
        "protected_mitigation_preservation_result",
        "success_rate_verdict",
        "repair_success",
        "driver_performance",
        "validation_readiness",
        "validation_result",
        "paper_evidence",
        "finite_window_vs_gru",
        "current_response_sufficiency",
        "current_sim_verdict",
        "high_fidelity_validation",
        "full_ideal_driver_completion",
        "level3_self_identification",
        "controller_family_ranking",
        "winner_selection",
        "checkpoint_promotion",
        "private_holdout_result",
        "profile_specific_tuning_result",
        "training_result",
        "ppo_result",
        "replay_result",
        "measured_rollout_result",
        "hf3_selected_platform_execution",
    ]
    for index, claim_family in enumerate(forbidden_claims, start=4):
        rows.append(
            {
                "claim_id": f"m2714-claim-{index:04d}",
                "claim_family": claim_family,
                "allowed_in_m2714": False,
                "claim_made": False,
                "status_pass": True,
                "evidence_required_before_claim": "separate pre-registered execution or validation milestone",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    status: dict[str, Any],
    input_source_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    profile_context_rows: list[dict[str, Any]],
    protected_exclusion_rows: list[dict[str, Any]],
    hf3_blocker_rows: list[dict[str, Any]],
    actor_contract_guard_rows: list[dict[str, Any]],
    claim_boundary_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    gates = [
        ("required_source_artifacts_present", "lineage", status["source_artifacts_all_present"], True, "lineage_invalid"),
        ("required_artifacts_present", "artifact", required_artifacts_present, True, "metric_artifact"),
        ("input_source_rows_minimum", "artifact", len(input_source_rows) >= 8, ">=8", "metric_artifact"),
        ("m2693_anchor_count", "lineage", status["m2693_anchor_task_source_id_count"] == 9, 9, "scenario_sampling_failure"),
        ("selected_profile_count", "lineage", status["selected_profile_count"] == 4, 4, "lineage_invalid"),
        (
            "candidate_row_count",
            "artifact",
            len(candidate_rows) == status["expected_exact_executable_candidate_row_count"],
            status["expected_exact_executable_candidate_row_count"],
            "metric_artifact",
        ),
        ("candidate_row_count_36", "artifact", len(candidate_rows) == 36, 36, "metric_artifact"),
        ("profile_context_row_count", "artifact", len(profile_context_rows) == len(candidate_rows), len(candidate_rows), "metric_artifact"),
        ("candidate_rows_all_existing_m1690", "lineage", status["candidate_rows_all_existing_m1690"], True, "lineage_invalid"),
        ("missing_selected_profile_rows_zero", "lineage", status["missing_selected_profile_row_count"] == 0, 0, "lineage_invalid"),
        ("candidate_unique_workload_ids", "lineage", status["candidate_workload_id_unique_count"] == len(candidate_rows), len(candidate_rows), "lineage_invalid"),
        ("candidate_rows_clean_schedule", "contract", status["candidate_rows_all_clean_schedule"], True, "contract_violation"),
        ("protected_proposal_exclusion_count", "artifact", len(protected_exclusion_rows) == 12, 12, "metric_artifact"),
        ("protected_rows_all_proposed_new", "lineage", status["protected_exclusions_all_proposed_new"], True, "lineage_invalid"),
        ("protected_rows_all_exact_absent", "lineage", status["protected_exclusions_all_exact_absent"], True, "lineage_invalid"),
        ("protected_rows_all_blocked_absent", "lineage", status["protected_exclusions_all_blocked_absent"], True, "lineage_invalid"),
        ("protected_execution_admitted_zero", "contract", status["protected_execution_admitted_row_count"] == 0, 0, "contract_violation"),
        ("ready_existing_protected_zero", "lineage", status["ready_existing_current_m1690_workload_row_count"] == 0, 0, "lineage_invalid"),
        ("existing_exact_protected_matches_zero", "lineage", status["existing_exact_m1690_match_count"] == 0, 0, "lineage_invalid"),
        ("fabricated_protected_matches_zero", "lineage", status["fabricated_existing_m1690_match_count"] == 0, 0, "lineage_invalid"),
        ("protected_rows_outside_denominator", "contract", status["protected_exclusions_all_outside_denominator"], True, "contract_violation"),
        ("protected_rows_actor_invisible", "contract", status["protected_exclusions_actor_invisible"], True, "contract_violation"),
        ("hf3_blocker_present", "lineage", status["hf3_dependency_blocker_present"], True, "lineage_invalid"),
        ("hf3_blocker_row_count", "artifact", len(hf3_blocker_rows) >= 1, ">=1", "metric_artifact"),
        ("actor_guard_rows_minimum", "contract", len(actor_contract_guard_rows) >= 9, ">=9", "contract_violation"),
        ("actor_guard_rows_pass", "contract", all(as_bool(row["status_pass"]) for row in actor_contract_guard_rows), True, "contract_violation"),
        ("claim_boundary_rows_minimum", "contract", len(claim_boundary_rows) >= 24, ">=24", "contract_violation"),
        ("claim_boundary_rows_pass", "contract", all(as_bool(row["status_pass"]) for row in claim_boundary_rows), True, "contract_violation"),
        ("m2713_decision_present", "lineage", "admit_current_m1690_exact_executable_reentry_panel_materialization_preflight" in source["m2713_design_text"], True, "lineage_invalid"),
        ("route_a_boundary_present", "contract", "Route A: Engineering Controller Mainline" in source["post_m2470_route_plan_text"], True, "contract_violation"),
        ("execution_run_false", "contract", not FALSE_CLAIM_FLAGS["execution_run"], False, "contract_violation"),
        ("validation_run_false", "contract", not FALSE_CLAIM_FLAGS["validation_run"], False, "contract_violation"),
        ("training_run_false", "contract", not FALSE_CLAIM_FLAGS["training_run"], False, "contract_violation"),
        ("ranking_run_false", "contract", not FALSE_CLAIM_FLAGS["ranking_run"], False, "contract_violation"),
        ("driver_performance_claim_false", "contract", not FALSE_CLAIM_FLAGS["driver_performance_claim_made"], False, "contract_violation"),
    ]
    return [
        {
            "gate_id": f"m2714-gate-{index:04d}",
            "gate_family": gate_family,
            "status_pass": bool(status_pass),
            "observed": observed_value(gate_name, status_pass, source, candidate_rows, protected_exclusion_rows),
            "expected": expected,
            "failure_type": "" if status_pass else failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (gate_name, gate_family, status_pass, expected, failure_type) in enumerate(gates, start=1)
    ]


def observed_value(
    gate_name: str,
    status_pass: Any,
    source: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    protected_exclusion_rows: list[dict[str, Any]],
) -> Any:
    false_flag_by_gate = {
        "execution_run_false": "execution_run",
        "validation_run_false": "validation_run",
        "training_run_false": "training_run",
        "ranking_run_false": "ranking_run",
        "driver_performance_claim_false": "driver_performance_claim_made",
    }
    if gate_name in false_flag_by_gate:
        return FALSE_CLAIM_FLAGS[false_flag_by_gate[gate_name]]
    if gate_name == "candidate_row_count_36":
        return len(candidate_rows)
    if gate_name == "protected_proposal_exclusion_count":
        return len(protected_exclusion_rows)
    if gate_name == "required_source_artifacts_present":
        missing = [key for key, exists in source["source_exists"].items() if not exists]
        return "missing=" + ";".join(missing) if missing else True
    return status_pass


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    status: dict[str, Any],
    input_source_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    profile_context_rows: list[dict[str, Any]],
    protected_exclusion_rows: list[dict[str, Any]],
    hf3_blocker_rows: list[dict[str, Any]],
    actor_contract_guard_rows: list[dict[str, Any]],
    claim_boundary_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    gate_matrix_pass = all(as_bool(row["status_pass"]) for row in gate_rows)
    actor_guard_pass = all(as_bool(row["status_pass"]) for row in actor_contract_guard_rows)
    claim_boundary_pass = all(as_bool(row["status_pass"]) for row in claim_boundary_rows)
    status_pass = (
        required_artifacts_present
        and gate_matrix_pass
        and actor_guard_pass
        and claim_boundary_pass
        and status["candidate_rows_all_existing_m1690"]
        and status["missing_selected_profile_row_count"] == 0
        and status["protected_exclusions_all_no_execution"]
        and status["protected_exclusions_all_outside_denominator"]
        and status["protected_exclusions_actor_invisible"]
        and status["hf3_dependency_blocker_present"]
    )
    summary: dict[str, Any] = {
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_route_a_current_m1690_exact_executable_reentry_panel_materialization_pass"
            if status_pass
            else "engineering_controller_route_a_current_m1690_exact_executable_reentry_panel_materialization_fail"
        ),
        "output_dir": str(output_dir),
        "doc_path": str(paths["doc"]),
        "required_artifacts_present": required_artifacts_present,
        "gate_matrix_pass": gate_matrix_pass,
        "actor_contract_guard_rows_pass": actor_guard_pass,
        "claim_boundary_rows_pass": claim_boundary_pass,
        "source_artifacts_all_present": status["source_artifacts_all_present"],
        "input_source_row_count": len(input_source_rows),
        "m1690_existing_workload_row_count": status["m1690_existing_workload_row_count"],
        "m2693_anchor_task_source_ids": status["m2693_anchor_task_source_ids"],
        "m2693_anchor_task_source_id_count": status["m2693_anchor_task_source_id_count"],
        "selected_profiles": list(SELECTED_PROFILES),
        "selected_profile_count": status["selected_profile_count"],
        "exact_executable_candidate_row_count": len(candidate_rows),
        "profile_context_row_count": len(profile_context_rows),
        "candidate_rows_all_existing_m1690": status["candidate_rows_all_existing_m1690"],
        "candidate_rows_all_clean_schedule": status["candidate_rows_all_clean_schedule"],
        "missing_selected_profile_row_count": status["missing_selected_profile_row_count"],
        "candidate_workload_id_unique_count": status["candidate_workload_id_unique_count"],
        "m2710_protected_proposal_exclusion_row_count": len(protected_exclusion_rows),
        "protected_execution_admitted_row_count": status["protected_execution_admitted_row_count"],
        "ready_existing_current_m1690_workload_row_count": status["ready_existing_current_m1690_workload_row_count"],
        "existing_exact_m1690_match_count": status["existing_exact_m1690_match_count"],
        "fabricated_existing_m1690_match_count": status["fabricated_existing_m1690_match_count"],
        "protected_exclusions_all_proposed_new": status["protected_exclusions_all_proposed_new"],
        "protected_exclusions_all_exact_absent": status["protected_exclusions_all_exact_absent"],
        "protected_exclusions_all_blocked_absent": status["protected_exclusions_all_blocked_absent"],
        "protected_rows_in_success_denominator": status["protected_rows_in_success_denominator"],
        "hidden_oracle_actor_input_detected": status["hidden_oracle_actor_input_detected"],
        "target_labels_actor_visible_detected": status["target_labels_actor_visible_detected"],
        "protected_labels_actor_visible_detected": status["protected_labels_actor_visible_detected"],
        "actor_contract_shape_72_action_3": P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3,
        "hf3_dependency_blocker_row_count": len(hf3_blocker_rows),
        "hf3_dependency_blocker_present": status["hf3_dependency_blocker_present"],
        "actor_contract_guard_row_count": len(actor_contract_guard_rows),
        "claim_boundary_row_count": len(claim_boundary_rows),
        "gate_row_count": len(gate_rows),
        "follow_up_manifest": str(follow_up_manifest),
        "next_blocker": next_blocker,
        "next_manifest": str(follow_up_manifest),
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "artifact_paths": {key: str(path) for key, path in paths.items()},
    }
    summary.update(FALSE_CLAIM_FLAGS)
    return summary


def render_milestone_doc(summary: dict[str, Any]) -> str:
    status = "completed" if summary["status_pass"] else "failed"
    return f"""# M2714 Engineering Controller Route A Current-M1690 Exact-Executable Reentry Panel Materialization Preflight

## Metadata

- status: {status}
- decision: route_to_current_m1690_exact_executable_reentry_panel_result_audit
- manifest: `experiments/manifests/{DEFAULT_MILESTONE}.json`
- run dir: `{summary["output_dir"]}`
- next: `{summary["next_blocker"]}`
- follow-up manifest: `{summary["next_manifest"]}`

## Materialized Surface

```text
input source rows: {summary["input_source_row_count"]}
M1690 workload rows read: {summary["m1690_existing_workload_row_count"]}
M2693 anchor task_source_ids: {summary["m2693_anchor_task_source_id_count"]}
selected profiles per anchor: {summary["selected_profile_count"]}
exact executable candidate rows: {summary["exact_executable_candidate_row_count"]}
profile context rows: {summary["profile_context_row_count"]}
missing selected profile rows: {summary["missing_selected_profile_row_count"]}
candidate rows all existing M1690: {summary["candidate_rows_all_existing_m1690"]}
candidate rows clean schedule: {summary["candidate_rows_all_clean_schedule"]}
```

Selected profiles:

```text
{chr(10).join(summary["selected_profiles"])}
```

## Protected Proposal Exclusions

```text
M2710 protected proposal exclusion rows: {summary["m2710_protected_proposal_exclusion_row_count"]}
protected execution-admitted rows: {summary["protected_execution_admitted_row_count"]}
ready-existing protected rows: {summary["ready_existing_current_m1690_workload_row_count"]}
existing exact protected M1690 matches: {summary["existing_exact_m1690_match_count"]}
fabricated exact protected M1690 matches: {summary["fabricated_existing_m1690_match_count"]}
protected rows in success denominator: {summary["protected_rows_in_success_denominator"]}
```

## Actor And Claim Boundary

```text
actor contract 72/action 3: {summary["actor_contract_shape_72_action_3"]}
hidden oracle actor input detected: {summary["hidden_oracle_actor_input_detected"]}
target labels actor-visible: {summary["target_labels_actor_visible_detected"]}
protected labels actor-visible: {summary["protected_labels_actor_visible_detected"]}
execution_run: {summary["execution_run"]}
validation_run: {summary["validation_run"]}
training_run: {summary["training_run"]}
ranking_run: {summary["ranking_run"]}
driver_performance_claim_made: {summary["driver_performance_claim_made"]}
paper_claim_made: {summary["paper_claim_made"]}
current_sim_verdict_claim_made: {summary["current_sim_verdict_claim_made"]}
level3_self_id_claim_made: {summary["level3_self_id_claim_made"]}
```

M2714 is materialization only. It does not reset, step, roll out, replay,
validate, train, run PPO, rank profiles, select a winner, promote a checkpoint,
compute success-rate verdicts, or claim repair success, driver performance,
paper evidence, current-sim verdict, high-fidelity validation, full ideal driver
completion, or self-ID evidence.

## Gates

```text
required artifacts present: {summary["required_artifacts_present"]}
gate matrix pass: {summary["gate_matrix_pass"]}
actor contract guard rows: {summary["actor_contract_guard_row_count"]}
claim-boundary rows: {summary["claim_boundary_row_count"]}
gate rows: {summary["gate_row_count"]}
status_pass: {summary["status_pass"]}
```

## Follow-Up

If this artifact passes audit, the only admitted continuation is the M2715
materialization result audit. Any later bounded execution preflight must be
separately pre-registered and must keep M2710 proposed protected rows excluded
from execution denominators and performance claims.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m1690-workload", type=Path, default=DEFAULT_EXECUTABLE_WORKLOAD)
    parser.add_argument("--m2693-dir", type=Path, default=DEFAULT_M2693_DIR)
    parser.add_argument("--m2710-dir", type=Path, default=DEFAULT_M2710_DIR)
    parser.add_argument("--m2712-synthesis", type=Path, default=DEFAULT_M2712_SYNTHESIS)
    parser.add_argument("--m2713-design", type=Path, default=DEFAULT_M2713_DESIGN)
    parser.add_argument("--m2638-blocker", type=Path, default=DEFAULT_M2638_BLOCKER)
    parser.add_argument("--route-plan", type=Path, default=DEFAULT_ROUTE_PLAN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args(argv)

    summary = materialize_current_m1690_exact_executable_reentry_panel(
        m1690_workload=args.m1690_workload,
        m2693_dir=args.m2693_dir,
        m2710_dir=args.m2710_dir,
        m2712_synthesis=args.m2712_synthesis,
        m2713_design=args.m2713_design,
        m2638_blocker=args.m2638_blocker,
        route_plan=args.route_plan,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"{summary['result_class']} status_pass={summary['status_pass']} output_dir={summary['output_dir']}")
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
