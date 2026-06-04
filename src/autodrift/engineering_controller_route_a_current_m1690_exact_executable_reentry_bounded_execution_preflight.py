"""Run bounded execution for the current-M1690 exact-executable reentry panel.

M2716 consumes the M2714 exact executable candidate panel after M2715 audit. It
may reset, step, and roll out policy actions only for the 36 exact existing
M1690 workload rows. M2710 protected proposal rows remain explicit exclusions.
The output is diagnostic execution evidence only, with no ranking, validation,
promotion, performance, paper, current-sim, high-fidelity, full-driver, or
self-ID claim.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.controller_family_full_rollout_execution import (
    DEFAULT_EXECUTABLE_SPECS,
    append_csv_row,
    load_executable_specs,
    read_csv_rows,
    run_workload_cell,
    selected_metrics_are_finite,
    write_run_state,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = "m2716-engineering-controller-route-a-current-m1690-exact-executable-reentry-bounded-execution-preflight"
DEFAULT_NEXT_BLOCKER = (
    "m2717-engineering-controller-route-a-current-m1690-exact-executable-reentry-bounded-execution-result-audit"
)
DEFAULT_M2714_DIR = Path(
    "runs/m2714_engineering_controller_route_a_current_m1690_exact_executable_reentry_panel"
)
DEFAULT_M2715_AUDIT = Path(
    "docs/m2715-engineering-controller-route-a-current-m1690-exact-executable-reentry-panel-materialization-result-audit.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2716_engineering_controller_route_a_current_m1690_exact_executable_reentry_bounded_execution_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2716-engineering-controller-route-a-current-m1690-exact-executable-reentry-bounded-execution-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/"
    "m2717-engineering-controller-route-a-current-m1690-exact-executable-reentry-bounded-execution-result-audit.json"
)
DEFAULT_EVAL_SEED_BASE = 271600
DEFAULT_POLICY_SUBJECT_ID = "m2655_mitigation_preserving_policy"
EXPECTED_CANDIDATE_COUNT = 36
EXPECTED_PROTECTED_EXCLUSION_COUNT = 12

CLAIM_SCOPE = (
    "M2716 Route A current-M1690 exact-executable reentry bounded execution "
    "preflight only; reset, step, rollout, and policy actions may be recorded "
    "for the 36 M2714 exact executable candidate rows, but protected proposal "
    "rows remain excluded and no replay, validation, training, PPO, private "
    "holdout, profile-specific tuning, ranking, winner selection, promotion, "
    "success-rate verdict, repair-success, driver-performance, paper, "
    "finite-window-vs-GRU, current-response, current-sim, high-fidelity "
    "validation, full ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, "
    "controller-family ranking, winner selection, checkpoint promotion, "
    "success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, "
    "current-response sufficiency, current-sim verdict, high-fidelity "
    "validation readiness or result, full ideal driver completion, or level3 "
    "self-identification"
)
ADMITTED_EXISTING_STATUS = "exact_executable_reentry_admitted_existing_m1690_workload"
PROTECTED_EXCLUSION_STATUS = "exact_executable_reentry_excluded_m2710_proposed_protected_row"

FAILURE_FIELDNAMES = [
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
    "exact_executable_reentry_status",
    "error_type",
    "error_message",
    "eval_seed",
    "environment_reset_run",
    "environment_step_run",
    "policy_action_run",
    "policy_rollout_run",
    "training_started",
    "replay_started",
    "ppo_used",
    "promoted",
    "private_holdout_used",
    "profile_specific_tuning",
    "ranking_run",
    "protected_proposal_execution",
    "protected_rows_in_success_denominator",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "target_labels_actor_visible",
    "protected_labels_actor_visible",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
PROTECTED_AUDIT_FIELDNAMES = [
    "audit_id",
    "exclusion_id",
    "workload_fixture_proposal_id",
    "support_candidate_id",
    "proposed_workload_id",
    "profile_name",
    "workload_fixture_support_status",
    "exact_match_status",
    "blocker_type",
    "m2714_exclusion_status",
    "m2716_execution_candidate",
    "m2716_execution_admitted",
    "m2716_execution_run",
    "protected_rows_in_success_denominator",
    "actor_visible",
    "protected_labels_actor_visible",
    "hidden_oracle_actor_input_required",
    "claim_scope",
]
AGGREGATE_FIELDNAMES = [
    "aggregate_id",
    "aggregate_family",
    "group_key",
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
    "diagnostic_only_no_verdict",
    "ranking_claim_made",
    "success_rate_verdict_claim_made",
    "claim_scope",
]
ACTOR_JOIN_FIELDNAMES = [
    "join_id",
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
    "allowed_in_m2716",
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
    "exact_execution_rows",
    "profile_aggregate",
    "anchor_aggregate",
    "protected_proposal_exclusion_audit_rows",
    "actor_contract_join_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "failure_rows",
    "run_state",
    "doc",
]


def run_current_m1690_exact_executable_reentry_bounded_execution_preflight(
    *,
    m2714_dir: Path | str = DEFAULT_M2714_DIR,
    m2715_audit: Path | str = DEFAULT_M2715_AUDIT,
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
        m2714_dir=Path(m2714_dir),
        m2715_audit=Path(m2715_audit),
        executable_specs=Path(executable_specs),
        follow_up_manifest=Path(follow_up_manifest),
    )
    execution_summary = run_candidate_panel_execution(
        m2714_dir=Path(m2714_dir),
        output_dir=output,
        executable_specs_path=Path(executable_specs),
        eval_seed_base=int(eval_seed_base),
        device=device,
        resume=resume,
        next_blocker=next_blocker,
    )
    artifact_rows = load_execution_artifact_rows(paths)
    candidate_rows = source["exact_executable_candidate_rows"]
    protected_audit_rows = build_protected_proposal_exclusion_audit_rows(source)
    profile_aggregate = build_aggregate_rows(
        candidate_rows=candidate_rows,
        episode_rows=artifact_rows["exact_execution_rows"],
        failure_rows=artifact_rows["failure_rows"],
        group_key="profile_name",
        aggregate_family="profile",
    )
    anchor_aggregate = build_aggregate_rows(
        candidate_rows=candidate_rows,
        episode_rows=artifact_rows["exact_execution_rows"],
        failure_rows=artifact_rows["failure_rows"],
        group_key="anchor_task_source_id",
        aggregate_family="anchor",
    )
    actor_join_rows = build_actor_contract_join_rows(source=source, artifact_rows=artifact_rows)
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=False,
        episode_or_failure_rows_present=bool(artifact_rows["exact_execution_rows"] or artifact_rows["failure_rows"]),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        execution_summary=execution_summary,
        artifact_rows=artifact_rows,
        candidate_rows=candidate_rows,
        protected_audit_rows=protected_audit_rows,
        profile_aggregate=profile_aggregate,
        anchor_aggregate=anchor_aggregate,
        actor_join_rows=actor_join_rows,
        claim_rows=claim_rows,
        required_artifacts_present=False,
    )
    write_csv_rows(paths["protected_proposal_exclusion_audit_rows"], protected_audit_rows, fieldnames=PROTECTED_AUDIT_FIELDNAMES)
    write_csv_rows(paths["profile_aggregate"], profile_aggregate, fieldnames=AGGREGATE_FIELDNAMES)
    write_csv_rows(paths["anchor_aggregate"], anchor_aggregate, fieldnames=AGGREGATE_FIELDNAMES)
    write_csv_rows(paths["actor_contract_join_rows"], actor_join_rows, fieldnames=ACTOR_JOIN_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"})
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_artifacts_present,
        episode_or_failure_rows_present=bool(artifact_rows["exact_execution_rows"] or artifact_rows["failure_rows"]),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        execution_summary=execution_summary,
        artifact_rows=load_execution_artifact_rows(paths),
        candidate_rows=candidate_rows,
        protected_audit_rows=protected_audit_rows,
        profile_aggregate=profile_aggregate,
        anchor_aggregate=anchor_aggregate,
        actor_join_rows=actor_join_rows,
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
        candidate_rows=candidate_rows,
        protected_audit_rows=protected_audit_rows,
        profile_aggregate=profile_aggregate,
        anchor_aggregate=anchor_aggregate,
        actor_join_rows=actor_join_rows,
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
        candidate_rows=candidate_rows,
        protected_audit_rows=protected_audit_rows,
        profile_aggregate=profile_aggregate,
        anchor_aggregate=anchor_aggregate,
        actor_join_rows=actor_join_rows,
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
        candidate_rows=candidate_rows,
        protected_audit_rows=protected_audit_rows,
        profile_aggregate=profile_aggregate,
        anchor_aggregate=anchor_aggregate,
        actor_join_rows=actor_join_rows,
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
        "exact_execution_rows": output_dir / "exact_execution_rows.csv",
        "profile_aggregate": output_dir / "profile_aggregate.csv",
        "anchor_aggregate": output_dir / "anchor_aggregate.csv",
        "protected_proposal_exclusion_audit_rows": output_dir / "protected_proposal_exclusion_audit_rows.csv",
        "actor_contract_join_rows": output_dir / "actor_contract_join_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "failure_rows": output_dir / "failure_rows.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2714_dir: Path,
    m2715_audit: Path,
    executable_specs: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2715_audit_doc": m2715_audit,
        "m2714_summary": m2714_dir / "summary.json",
        "m2714_exact_executable_candidate_rows": m2714_dir / "exact_executable_candidate_rows.csv",
        "m2714_profile_context_rows": m2714_dir / "profile_context_rows.csv",
        "m2714_protected_proposal_exclusion_rows": m2714_dir / "protected_proposal_exclusion_rows.csv",
        "m2714_actor_contract_guard_rows": m2714_dir / "actor_contract_guard_rows.csv",
        "m2714_claim_boundary_rows": m2714_dir / "claim_boundary_rows.csv",
        "m2714_gate_matrix": m2714_dir / "gate_matrix.csv",
        "executable_task_specs": executable_specs,
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2715_audit_text": paths["m2715_audit_doc"].read_text(encoding="utf-8")
        if source_exists["m2715_audit_doc"]
        else "",
        "m2714_summary": read_json(paths["m2714_summary"]) if source_exists["m2714_summary"] else {},
        "exact_executable_candidate_rows": read_csv_rows(paths["m2714_exact_executable_candidate_rows"]),
        "profile_context_rows": read_csv_rows(paths["m2714_profile_context_rows"]),
        "protected_proposal_exclusion_rows": read_csv_rows(paths["m2714_protected_proposal_exclusion_rows"]),
        "actor_contract_guard_rows": read_csv_rows(paths["m2714_actor_contract_guard_rows"]),
        "claim_boundary_rows": read_csv_rows(paths["m2714_claim_boundary_rows"]),
        "gate_matrix": read_csv_rows(paths["m2714_gate_matrix"]),
    }


def load_execution_artifact_rows(paths: dict[str, Path]) -> dict[str, list[dict[str, str]]]:
    return {
        "exact_execution_rows": read_csv_rows(paths["exact_execution_rows"]),
        "failure_rows": read_csv_rows(paths["failure_rows"]),
        "profile_aggregate": read_csv_rows(paths["profile_aggregate"]),
        "anchor_aggregate": read_csv_rows(paths["anchor_aggregate"]),
        "protected_proposal_exclusion_audit_rows": read_csv_rows(paths["protected_proposal_exclusion_audit_rows"]),
    }


def run_candidate_panel_execution(
    *,
    m2714_dir: Path | str = DEFAULT_M2714_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    executable_specs_path: Path | str = DEFAULT_EXECUTABLE_SPECS,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    device: str = "cpu",
    resume: bool = True,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    if not resume:
        for name in (
            "exact_execution_rows.csv",
            "failure_rows.csv",
            "profile_aggregate.csv",
            "anchor_aggregate.csv",
            "protected_proposal_exclusion_audit_rows.csv",
            "actor_contract_join_rows.csv",
            "claim_boundary_rows.csv",
            "gate_matrix.csv",
            "summary.json",
            "run_state.json",
        ):
            path = output / name
            if path.exists():
                path.unlink()

    candidate_rows = sorted(
        read_csv_rows(Path(m2714_dir) / "exact_executable_candidate_rows.csv"),
        key=lambda row: str(row.get("candidate_id", "")),
    )
    specs = load_executable_specs(executable_specs_path)
    spec_by_id = {str(spec["task_source_id"]): spec for spec in specs}
    if not (output / "failure_rows.csv").exists():
        write_csv_rows(output / "failure_rows.csv", [], fieldnames=FAILURE_FIELDNAMES)
    profile_cache: dict[tuple[str, str, str], tuple[dict[str, Any], Any, dict[str, str]]] = {}
    recorded = recorded_candidate_ids(output)

    for cell_index, candidate in enumerate(candidate_rows):
        candidate_id = str(candidate.get("candidate_id", ""))
        if candidate_id in recorded:
            continue
        eval_seed = int(eval_seed_base) + int(cell_index)
        try:
            if str(candidate.get("exact_executable_reentry_status", "")) != ADMITTED_EXISTING_STATUS:
                raise ValueError("candidate row is not admitted as an exact existing M1690 workload")
            task_source_id = str(candidate["task_source_id"])
            profile_name = str(candidate["profile_name"])
            config_path = str(candidate["profile_config_path"])
            checkpoint_path = str(candidate["checkpoint_path"])
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
                workload_row=candidate,
                executable_spec=spec_by_id[task_source_id],
                profile_config=profile_config,
                model=model,
                profile_row=profile_row,
                eval_seed=eval_seed,
            )
            row.update(candidate_execution_metadata(candidate, eval_seed=eval_seed))
            append_csv_row(output / "exact_execution_rows.csv", row)
            recorded.add(candidate_id)
        except Exception as exc:  # noqa: BLE001 - failed candidate cells must be recorded.
            append_csv_row(
                output / "failure_rows.csv",
                failure_row(candidate, eval_seed=eval_seed, error_type=type(exc).__name__, error_message=str(exc)),
            )
            recorded.add(candidate_id)
        write_run_state(
            output / "run_state.json",
            {
                "candidate_count": len(candidate_rows),
                "completed_execution_count": len(read_csv_rows(output / "exact_execution_rows.csv")),
                "failure_count": len(read_csv_rows(output / "failure_rows.csv")),
                "accounted_count": len(recorded_candidate_ids(output)),
                "latest_candidate_id": candidate_id,
                "complete": False,
            },
        )
    return finalize_candidate_panel_outputs(output_dir=output, candidate_rows=candidate_rows, next_blocker=next_blocker)


def candidate_execution_metadata(candidate: Mapping[str, Any], *, eval_seed: int) -> dict[str, Any]:
    return {
        "candidate_id": candidate.get("candidate_id", ""),
        "anchor_task_source_id": candidate.get("anchor_task_source_id", ""),
        "anchor_workload_id": candidate.get("anchor_workload_id", ""),
        "profile_role": candidate.get("profile_role", ""),
        "exact_executable_reentry_status": candidate.get("exact_executable_reentry_status", ""),
        "m2716_eval_seed": int(eval_seed),
        "bounded_exact_executable_reentry_execution": True,
        "protected_proposal_execution": False,
        "candidate_panel_count": EXPECTED_CANDIDATE_COUNT,
        "target_labels_actor_visible": False,
        "protected_labels_actor_visible": False,
        "profile_labels_actor_visible": False,
        "blocker_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "hidden_oracle_actor_input_required": False,
        "protected_rows_in_success_denominator": False,
        "diagnostic_only_no_verdict": True,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_verdict_claim_made": False,
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
        "validation_readiness_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_response_sufficiency_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "level3_self_id_claim_made": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def failure_row(candidate: Mapping[str, Any], *, eval_seed: int, error_type: str, error_message: str) -> dict[str, Any]:
    return {
        "candidate_id": candidate.get("candidate_id", ""),
        "anchor_task_source_id": candidate.get("anchor_task_source_id", ""),
        "anchor_workload_id": candidate.get("anchor_workload_id", ""),
        "workload_id": candidate.get("workload_id", ""),
        "task_source_id": candidate.get("task_source_id", ""),
        "profile_name": candidate.get("profile_name", ""),
        "profile_role": candidate.get("profile_role", ""),
        "task_family": candidate.get("task_family", ""),
        "source_edge": candidate.get("source_edge", ""),
        "window_tag": candidate.get("window_tag", ""),
        "exact_executable_reentry_status": candidate.get("exact_executable_reentry_status", ""),
        "error_type": error_type,
        "error_message": error_message,
        "eval_seed": int(eval_seed),
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "ranking_run": False,
        "protected_proposal_execution": False,
        "protected_rows_in_success_denominator": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_required": False,
        "target_labels_actor_visible": False,
        "protected_labels_actor_visible": False,
        "diagnostic_only_no_verdict": True,
        "claim_boundary": CLAIM_SCOPE,
    }


def recorded_candidate_ids(output: Path) -> set[str]:
    return {
        str(row.get("candidate_id", ""))
        for row in read_csv_rows(output / "exact_execution_rows.csv") + read_csv_rows(output / "failure_rows.csv")
        if row.get("candidate_id")
    }


def finalize_candidate_panel_outputs(
    *,
    output_dir: Path,
    candidate_rows: list[dict[str, str]],
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    episode_rows = [dict(row) for row in read_csv_rows(output_dir / "exact_execution_rows.csv")]
    failure_rows = [dict(row) for row in read_csv_rows(output_dir / "failure_rows.csv")]
    write_csv_rows(output_dir / "failure_rows.csv", failure_rows, fieldnames=FAILURE_FIELDNAMES)
    accounted_count = len(recorded_candidate_ids(output_dir))
    all_metrics_finite = selected_metrics_are_finite(episode_rows) if episode_rows else False
    status_pass = bool(
        len(candidate_rows) == EXPECTED_CANDIDATE_COUNT
        and accounted_count == len(candidate_rows)
        and bool(episode_rows)
        and all_metrics_finite
        and not any(forbidden_execution_flag(row) for row in episode_rows + failure_rows)
    )
    summary = {
        "result_class": (
            "engineering_controller_route_a_current_m1690_exact_executable_reentry_bounded_candidate_execution_pass"
            if status_pass
            else "engineering_controller_route_a_current_m1690_exact_executable_reentry_bounded_candidate_execution_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "candidate_count": len(candidate_rows),
        "episode_count": len(episode_rows),
        "failure_count": len(failure_rows),
        "accounted_candidate_count": accounted_count,
        "all_selected_metrics_finite": bool(all_metrics_finite),
        "environment_reset_run": bool(episode_rows),
        "environment_step_run": bool(episode_rows),
        "policy_action_run": bool(episode_rows),
        "policy_rollout_run": bool(episode_rows),
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "protected_proposal_execution": False,
        "protected_rows_in_success_denominator": False,
        "driver_performance_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "level3_self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "artifacts": {
            "exact_execution_rows": str(output_dir / "exact_execution_rows.csv"),
            "failure_rows": str(output_dir / "failure_rows.csv"),
            "run_state": str(output_dir / "run_state.json"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output_dir / "candidate_panel_execution_summary.json", summary)
    write_run_state(
        output_dir / "run_state.json",
        {
            "candidate_count": len(candidate_rows),
            "completed_execution_count": len(episode_rows),
            "failure_count": len(failure_rows),
            "accounted_count": accounted_count,
            "complete": accounted_count == len(candidate_rows),
            "status_pass": status_pass,
        },
    )
    return summary


def build_protected_proposal_exclusion_audit_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for index, exclusion in enumerate(source["protected_proposal_exclusion_rows"], start=1):
        rows.append(
            {
                "audit_id": f"m2716-protected-exclusion-audit-{index:04d}",
                "exclusion_id": exclusion.get("exclusion_id", ""),
                "workload_fixture_proposal_id": exclusion.get("workload_fixture_proposal_id", ""),
                "support_candidate_id": exclusion.get("support_candidate_id", ""),
                "proposed_workload_id": exclusion.get("proposed_workload_id", ""),
                "profile_name": exclusion.get("profile_name", ""),
                "workload_fixture_support_status": exclusion.get("workload_fixture_support_status", ""),
                "exact_match_status": exclusion.get("exact_match_status", ""),
                "blocker_type": exclusion.get("blocker_type", ""),
                "m2714_exclusion_status": exclusion.get("exclusion_status", ""),
                "m2716_execution_candidate": False,
                "m2716_execution_admitted": False,
                "m2716_execution_run": False,
                "protected_rows_in_success_denominator": False,
                "actor_visible": False,
                "protected_labels_actor_visible": False,
                "hidden_oracle_actor_input_required": False,
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def build_aggregate_rows(
    *,
    candidate_rows: list[dict[str, Any]],
    episode_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    group_key: str,
    aggregate_family: str,
) -> list[dict[str, Any]]:
    candidates_by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    episodes_by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    failures_by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        candidates_by_group[str(row.get(group_key, ""))].append(row)
    for row in episode_rows:
        episodes_by_group[str(row.get(group_key, ""))].append(row)
    for row in failure_rows:
        failures_by_group[str(row.get(group_key, ""))].append(row)
    rows = []
    for index, group in enumerate(sorted(candidates_by_group), start=1):
        episodes = episodes_by_group.get(group, [])
        failures = failures_by_group.get(group, [])
        rows.append(
            {
                "aggregate_id": f"m2716-{aggregate_family}-aggregate-{index:04d}",
                "aggregate_family": aggregate_family,
                "group_key": group,
                "candidate_count": len(candidates_by_group[group]),
                "episode_count": len(episodes),
                "failure_count": len(failures),
                "accounted_count": len(episodes) + len(failures),
                "success_rate_diagnostic": mean_bool(episodes, "success"),
                "collision_rate_diagnostic": mean_bool(episodes, "collision"),
                "offtrack_rate_diagnostic": mean_eq(episodes, "termination_reason", "off_track"),
                "clearance_margin_mean": mean_float(episodes, "min_clearance_margin"),
                "return_mean": mean_float(episodes, "return"),
                "all_selected_metrics_finite": selected_metrics_are_finite(episodes) if episodes else "",
                "diagnostic_only_no_verdict": True,
                "ranking_claim_made": False,
                "success_rate_verdict_claim_made": False,
                "claim_scope": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_join_rows(
    *,
    source: dict[str, Any],
    artifact_rows: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows = [
        actor_join("observation_shape", P0_OBSERVATION_DIM, 72, False),
        actor_join("action_shape", ACTION_DIM, 3, False),
        actor_join("deployed_action_mapping", "[steer, throttle, brake]", "[steer, throttle, brake]", False),
        actor_join("hidden_oracle_actor_input_detected", hidden_oracle_detected(artifact_rows), False, False),
        actor_join("target_labels_actor_visible", labels_visible(artifact_rows, "target_labels_actor_visible"), False, False),
        actor_join("protected_labels_actor_visible", labels_visible(artifact_rows, "protected_labels_actor_visible"), False, False),
        actor_join("profile_labels_actor_visible", labels_visible(artifact_rows, "profile_labels_actor_visible"), False, False),
        actor_join("blocker_labels_actor_visible", labels_visible(artifact_rows, "blocker_labels_actor_visible"), False, False),
        actor_join("route_labels_actor_visible", labels_visible(artifact_rows, "route_labels_actor_visible"), False, False),
        actor_join("verdict_labels_actor_visible", labels_visible(artifact_rows, "verdict_labels_actor_visible"), False, False),
        actor_join("protected_rows_in_success_denominator", protected_denominator_used(artifact_rows), False, False),
        actor_join("m2714_actor_guards_pass", all(bool_value(row.get("status_pass")) for row in source["actor_contract_guard_rows"]), True, False),
    ]
    return rows


def actor_join(field: str, observed: Any, expected: Any, actor_visible: bool) -> dict[str, Any]:
    return {
        "join_id": f"m2716-actor-join-{field}",
        "contract_field": field,
        "observed_value": observed,
        "expected_value": expected,
        "status_pass": str(observed) == str(expected),
        "actor_visible": actor_visible,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_claim_boundary_rows(
    *,
    follow_up_manifest_registered: bool,
    artifacts_present: bool,
    episode_or_failure_rows_present: bool,
) -> list[dict[str, Any]]:
    allowed = [
        ("bounded_execution_preflight", "execution", episode_or_failure_rows_present, "M2716 exact execution/failure rows"),
        ("exact_execution_rows_materialized", "artifact", artifacts_present, "exact_execution_rows.csv"),
        ("profile_aggregate_materialized", "artifact", artifacts_present, "profile_aggregate.csv"),
        ("anchor_aggregate_materialized", "artifact", artifacts_present, "anchor_aggregate.csv"),
        ("protected_exclusion_audit_materialized", "artifact", artifacts_present, "protected_proposal_exclusion_audit_rows.csv"),
        ("actor_contract_join_rows_materialized", "artifact", artifacts_present, "actor_contract_join_rows.csv"),
        ("claim_boundary_rows_materialized", "artifact", artifacts_present, "claim_boundary_rows.csv"),
        ("gate_matrix_materialized", "artifact", artifacts_present, "gate_matrix.csv"),
        ("run_state_materialized", "artifact", artifacts_present, "run_state.json"),
        ("diagnostic_metrics_recorded", "diagnostic_metric", episode_or_failure_rows_present, "diagnostic aggregate rows only"),
        ("protected_proposals_remain_excluded", "contract", True, "protected exclusion audit rows"),
        ("follow_up_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2717 result-audit manifest"),
    ]
    blocked = [
        ("protected_proposal_execution", "execution", "forbidden in M2716"),
        ("replay_execution", "execution", "future replay manifest"),
        ("validation_execution", "validation", "future validation manifest"),
        ("training_or_ppo", "execution", "future training manifest"),
        ("private_holdout_tuning", "holdout_policy", "forbidden in M2716"),
        ("profile_specific_tuning", "objective_overfit", "future controlled tuning protocol"),
        ("controller_family_ranking", "ranking", "future audited comparison interpretation"),
        ("winner_selection", "promotion", "future promotion gate"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("success_rate_verdict", "verdict", "future result audit and verdict milestone"),
        ("repair_success", "verdict", "future repair audit and validation route"),
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
    rows: list[dict[str, Any]] = []
    for claim_id, family, made, evidence in allowed:
        rows.append(claim(claim_id, family, True, made, evidence))
    rows.extend(claim(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def claim(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m2716_{claim_id}",
        "claim_family": family,
        "allowed_in_m2716": allowed,
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
    candidate_rows: list[dict[str, Any]],
    protected_audit_rows: list[dict[str, Any]],
    profile_aggregate: list[dict[str, Any]],
    anchor_aggregate: list[dict[str, Any]],
    actor_join_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    episode_rows = artifact_rows["exact_execution_rows"]
    failure_rows = artifact_rows["failure_rows"]
    accounted_count = len({row.get("candidate_id", "") for row in episode_rows + failure_rows if row.get("candidate_id")})
    allowed_claims = [row for row in claim_rows if bool_value(row["allowed_in_m2716"])]
    blocked_claims = [row for row in claim_rows if not bool_value(row["allowed_in_m2716"])]
    expected_profile_aggregate_count = len({str(row.get("profile_name", "")) for row in candidate_rows})
    expected_anchor_aggregate_count = len({str(row.get("anchor_task_source_id", "")) for row in candidate_rows})
    gates = [
        ("source_artifacts_present", "lineage", all(source["source_exists"].values()), source["source_exists"], "all M2714/M2715/spec/follow-up artifacts present", "lineage_invalid"),
        ("m2715_accepts_m2714", "lineage", "accept_m2714_route_to_current_m1690_exact_executable_reentry_bounded_execution_preflight" in source["m2715_audit_text"], "decision present", "decision present", "lineage_invalid"),
        ("m2714_status_pass", "lineage", bool_value(source["m2714_summary"].get("status_pass", False)), source["m2714_summary"].get("status_pass", None), True, "lineage_invalid"),
        ("candidate_panel_shape", "lineage", len(candidate_rows) == EXPECTED_CANDIDATE_COUNT, len(candidate_rows), EXPECTED_CANDIDATE_COUNT, "metric_artifact"),
        ("candidate_rows_all_existing", "lineage", all(bool_value(row.get("existing_m1690_workload_id_source_backed", False)) for row in candidate_rows), "all source-backed", "all source-backed", "lineage_invalid"),
        ("candidate_rows_all_admitted", "lineage", all(row.get("exact_executable_reentry_status") == ADMITTED_EXISTING_STATUS for row in candidate_rows), "all admitted existing", ADMITTED_EXISTING_STATUS, "lineage_invalid"),
        ("execution_accounted_all_candidates", "execution", accounted_count == len(candidate_rows), accounted_count, len(candidate_rows), "scenario_sampling_failure"),
        ("execution_rows_present", "execution", bool(episode_rows), len(episode_rows), ">0", "scenario_sampling_failure"),
        ("all_selected_metrics_finite", "metric", selected_metrics_are_finite(episode_rows) if episode_rows else False, execution_summary.get("all_selected_metrics_finite"), True, "metric_artifact"),
        ("profile_aggregate_shape", "artifact", len(profile_aggregate) == expected_profile_aggregate_count, len(profile_aggregate), expected_profile_aggregate_count, "metric_artifact"),
        ("anchor_aggregate_shape", "artifact", len(anchor_aggregate) == expected_anchor_aggregate_count, len(anchor_aggregate), expected_anchor_aggregate_count, "metric_artifact"),
        ("protected_exclusion_count", "contract", len(protected_audit_rows) == EXPECTED_PROTECTED_EXCLUSION_COUNT, len(protected_audit_rows), EXPECTED_PROTECTED_EXCLUSION_COUNT, "contract_violation"),
        ("protected_exclusions_not_executed", "contract", all(not bool_value(row["m2716_execution_run"]) and not bool_value(row["m2716_execution_admitted"]) for row in protected_audit_rows), "all protected exclusions not run", "all false", "contract_violation"),
        ("protected_not_success_denominator", "contract", not protected_denominator_used(artifact_rows) and all(not bool_value(row["protected_rows_in_success_denominator"]) for row in protected_audit_rows), "protected rows outside success denominator", "all false", "proof_washout"),
        ("actor_contract_preserved", "contract", all(bool_value(row["status_pass"]) for row in actor_join_rows), f"rows={len(actor_join_rows)} pass={sum(bool_value(row['status_pass']) for row in actor_join_rows)}", "all actor joins pass", "contract_violation"),
        ("labels_actor_invisible", "contract", not any(labels_visible(artifact_rows, key) for key in ("target_labels_actor_visible", "protected_labels_actor_visible", "profile_labels_actor_visible", "blocker_labels_actor_visible", "route_labels_actor_visible", "verdict_labels_actor_visible")), "all labels actor-invisible", "all false", "contract_violation"),
        ("no_hidden_oracle_actor_input", "contract", not hidden_oracle_detected(artifact_rows), "hidden/oracle actor input false", "all false", "contract_violation"),
        ("no_forbidden_execution", "execution_guardrail", not any(forbidden_execution_flag(row) for row in episode_rows + failure_rows), "no replay/train/PPO/private holdout/tuning/promotion", "all false", "objective_overfit"),
        ("claim_boundary_blocks_overclaim", "claim_boundary", all(bool_value(row["status_pass"]) for row in allowed_claims) and all(not bool_value(row["claim_made"]) and bool_value(row["status_pass"]) for row in blocked_claims), f"allowed={len(allowed_claims)} blocked={len(blocked_claims)}", "allowed claims pass and blocked claims not made", "proof_washout"),
        ("required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
    ]
    return [
        gate(gate_id, family, status_pass, observed, expected, failure_type)
        for gate_id, family, status_pass, observed, expected, failure_type in gates
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
        "gate_id": f"m2716_{gate_id}",
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
    candidate_rows: list[dict[str, Any]],
    protected_audit_rows: list[dict[str, Any]],
    profile_aggregate: list[dict[str, Any]],
    anchor_aggregate: list[dict[str, Any]],
    actor_join_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
    eval_seed_base: int,
    device: str,
) -> dict[str, Any]:
    episode_rows = artifact_rows["exact_execution_rows"]
    failure_rows = artifact_rows["failure_rows"]
    accounted_count = len({row.get("candidate_id", "") for row in episode_rows + failure_rows if row.get("candidate_id")})
    gate_matrix_pass = all(bool_value(row["status_pass"]) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_route_a_current_m1690_exact_executable_reentry_bounded_execution_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_current_m1690_exact_executable_reentry_bounded_execution_preflight_fail"
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
        "m2714_status_pass": bool_value(source["m2714_summary"].get("status_pass", False)),
        "candidate_count": len(candidate_rows),
        "expected_candidate_count": EXPECTED_CANDIDATE_COUNT,
        "exact_execution_row_count": len(episode_rows),
        "failure_row_count": len(failure_rows),
        "accounted_candidate_count": accounted_count,
        "candidate_rows_all_existing_m1690": all(bool_value(row.get("existing_m1690_workload_id_source_backed", False)) for row in candidate_rows),
        "candidate_rows_all_admitted_existing": all(row.get("exact_executable_reentry_status") == ADMITTED_EXISTING_STATUS for row in candidate_rows),
        "all_selected_metrics_finite": selected_metrics_are_finite(episode_rows) if episode_rows else False,
        "profile_aggregate_row_count": len(profile_aggregate),
        "anchor_aggregate_row_count": len(anchor_aggregate),
        "protected_proposal_exclusion_audit_row_count": len(protected_audit_rows),
        "protected_execution_row_count": 0,
        "protected_exclusions_not_executed": all(not bool_value(row["m2716_execution_run"]) for row in protected_audit_rows),
        "actor_contract_join_row_count": len(actor_join_rows),
        "actor_contract_join_rows_pass": all(bool_value(row["status_pass"]) for row in actor_join_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "execution_summary_result_class": execution_summary.get("result_class", ""),
        "environment_reset_run": bool(episode_rows),
        "environment_step_run": bool(episode_rows),
        "policy_action_run": bool(episode_rows),
        "policy_rollout_run": bool(episode_rows),
        "bounded_exact_executable_reentry_execution": bool(episode_rows),
        "protected_proposal_execution": False,
        "measured_validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "actor_input_contract_changed": False,
        "actor_contract_shape_72_action_3": True,
        "hidden_oracle_actor_input_detected": hidden_oracle_detected(artifact_rows),
        "target_labels_actor_visible": labels_visible(artifact_rows, "target_labels_actor_visible"),
        "protected_labels_actor_visible": labels_visible(artifact_rows, "protected_labels_actor_visible"),
        "profile_labels_actor_visible": labels_visible(artifact_rows, "profile_labels_actor_visible"),
        "blocker_labels_actor_visible": labels_visible(artifact_rows, "blocker_labels_actor_visible"),
        "route_labels_actor_visible": labels_visible(artifact_rows, "route_labels_actor_visible"),
        "verdict_labels_actor_visible": labels_visible(artifact_rows, "verdict_labels_actor_visible"),
        "protected_rows_in_success_denominator": protected_denominator_used(artifact_rows),
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
        "current_response_sufficiency_claim_made": False,
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
            "# M2716 Engineering Controller Route A Current-M1690 Exact-Executable Reentry Bounded Execution Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- candidate rows: {summary['candidate_count']}",
            f"- exact execution rows: {summary['exact_execution_row_count']}",
            f"- failure rows: {summary['failure_row_count']}",
            f"- accounted candidates: {summary['accounted_candidate_count']}/{summary['candidate_count']}",
            f"- profile aggregate rows: {summary['profile_aggregate_row_count']}",
            f"- anchor aggregate rows: {summary['anchor_aggregate_row_count']}",
            f"- protected exclusion audit rows: {summary['protected_proposal_exclusion_audit_row_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M2716 records bounded closed-loop diagnostic data only for the M2714 exact executable candidate rows. M2710 protected proposal rows remain excluded from execution and ordinary success denominators.",
            "",
            "Rejected claims:",
            "",
            "```text",
            FORBIDDEN_INTERPRETATION,
            "```",
            "",
            "## Artifacts",
            "",
            *[f"- {key}: `{value}`" for key, value in summary["paths"].items()],
            "",
            "## Next",
            "",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            f"- next: `{summary['next_blocker']}`",
            "",
        ]
    )


def forbidden_execution_flag(row: Mapping[str, Any]) -> bool:
    return any(
        bool_value(row.get(key, False))
        for key in (
            "training_started",
            "training_run",
            "replay_started",
            "replay_run",
            "ppo_used",
            "promoted",
            "private_holdout_used",
            "profile_specific_tuning",
            "actor_input_contract_changed",
            "ranking_run",
            "winner_selected",
            "checkpoint_promoted",
            "success_rate_verdict_claim_made",
            "driver_performance_claim_made",
            "paper_claim_made",
            "current_sim_verdict_claim_made",
            "level3_self_id_claim_made",
        )
    )


def labels_visible(artifact_rows: dict[str, list[dict[str, Any]]], key: str) -> bool:
    return any(bool_value(row.get(key, False)) for row in artifact_rows["exact_execution_rows"] + artifact_rows["failure_rows"])


def hidden_oracle_detected(artifact_rows: dict[str, list[dict[str, Any]]]) -> bool:
    return any(
        bool_value(row.get("hidden_oracle_actor_input_required", False))
        for row in artifact_rows["exact_execution_rows"] + artifact_rows["failure_rows"]
    )


def protected_denominator_used(artifact_rows: dict[str, list[dict[str, Any]]]) -> bool:
    return any(
        bool_value(row.get("protected_rows_in_success_denominator", False))
        for row in artifact_rows["exact_execution_rows"]
        + artifact_rows["failure_rows"]
        + artifact_rows["protected_proposal_exclusion_audit_rows"]
    )


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def mean_bool(rows: Iterable[Mapping[str, Any]], key: str) -> float | str:
    values = [bool_value(row.get(key, False)) for row in rows]
    return float(np.mean(values)) if values else ""


def mean_eq(rows: Iterable[Mapping[str, Any]], key: str, expected: str) -> float | str:
    values = [str(row.get(key, "")) == expected for row in rows]
    return float(np.mean(values)) if values else ""


def mean_float(rows: Iterable[Mapping[str, Any]], key: str) -> float | str:
    values = []
    for row in rows:
        try:
            value = float(row.get(key, float("nan")))
        except (TypeError, ValueError):
            value = float("nan")
        if np.isfinite(value):
            values.append(value)
    return float(np.mean(values)) if values else ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2714-dir", type=Path, default=DEFAULT_M2714_DIR)
    parser.add_argument("--m2715-audit", type=Path, default=DEFAULT_M2715_AUDIT)
    parser.add_argument("--executable-specs", type=Path, default=DEFAULT_EXECUTABLE_SPECS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args(argv)

    summary = run_current_m1690_exact_executable_reentry_bounded_execution_preflight(
        m2714_dir=args.m2714_dir,
        m2715_audit=args.m2715_audit,
        executable_specs=args.executable_specs,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        eval_seed_base=int(args.eval_seed_base),
        device=str(args.device),
        resume=not bool(args.no_resume),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"exact_execution_row_count={summary['exact_execution_row_count']}")
    print(f"failure_row_count={summary['failure_row_count']}")
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
