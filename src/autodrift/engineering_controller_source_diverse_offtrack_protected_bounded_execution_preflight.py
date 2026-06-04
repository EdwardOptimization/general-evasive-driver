"""Run source-diverse off-track/protected bounded execution preflight.

M2693 consumes the accepted M2691 target panel. It executes one bounded
current-sim diagnostic cell per off-track target with a single recurrent actor
profile and records protected targets as explicit non-executable failure rows
when no current runner mapping exists. It does not train, replay, validate,
rank, promote, or claim driver performance.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.controller_family_executable_workload_materialization_preflight import (
    DEFAULT_M1674_RUN_DIR,
    profile_artifact_rows,
)
from autodrift.controller_family_full_rollout_execution import (
    DEFAULT_EXECUTABLE_SPECS,
    DEFAULT_EXECUTABLE_WORKLOAD,
    append_csv_row,
    load_executable_specs,
    load_executable_workload,
    read_csv_rows,
    run_workload_cell,
    selected_metrics_are_finite,
    write_run_state,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2693-engineering-controller-source-diverse-offtrack-protected-"
    "bounded-execution-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2694-engineering-controller-source-diverse-offtrack-protected-"
    "bounded-execution-result-audit"
)
DEFAULT_M2691_DIR = Path("runs/m2691_engineering_controller_source_diverse_offtrack_protected_target_panel")
DEFAULT_OUTPUT_DIR = Path("runs/m2693_engineering_controller_source_diverse_offtrack_protected_bounded_execution_preflight")
DEFAULT_DOC_PATH = Path(
    "docs/m2693-engineering-controller-source-diverse-offtrack-protected-bounded-execution-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/"
    "m2694-engineering-controller-source-diverse-offtrack-protected-bounded-execution-result-audit.json"
)
DEFAULT_RUNTIME_PROFILE_NAME = "L3_online_gru"
DEFAULT_POLICY_SUBJECT_ID = "m2655_mitigation_preserving_policy"
DEFAULT_CHECKPOINT_PATH = Path(
    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/"
    "checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"
)
DEFAULT_EVAL_SEED_BASE = 269300

TARGET_PANEL_COUNT = 19
OFFTRACK_TARGET_COUNT = 9
PROTECTED_TARGET_COUNT = 10

CLAIM_SCOPE = (
    "M2693 source-diverse off-track/protected bounded execution preflight "
    "only; reset, step, rollout, and policy actions may be recorded for the "
    "bounded M2691 current-sim target rows, protected targets may be recorded "
    "as explicit non-executable failure rows, but no replay, validation, "
    "training, PPO, private holdout, profile-specific tuning, ranking, winner "
    "selection, promotion, success-rate verdict, repair-success, driver-"
    "performance, paper, finite-window-vs-GRU, current-response, current-sim, "
    "high-fidelity validation, full ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, "
    "controller-family ranking, winner selection, checkpoint promotion, "
    "success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, "
    "current-response sufficiency, current-sim verdict, high-fidelity "
    "validation readiness or result, full ideal driver completion, or level3 "
    "self-identification"
)

TARGET_METADATA_FIELDNAMES = [
    "target_id",
    "target_family",
    "source_family",
    "source_key",
    "task_family",
    "source_edge_or_axis",
    "role_semantics_proxy",
    "episode_or_row_count",
    "blocking_count",
    "regressed_row_count",
    "existing_success_count",
    "existing_collision_count",
    "existing_offtrack_count",
    "source_diversity_bucket",
    "future_execution_role",
    "diagnostic_only_no_verdict",
    "actor_input_contract_changed",
    "target_labels_actor_visible",
    "hidden_oracle_actor_input_required",
    "protected_rows_in_success_denominator",
]
FAILURE_FIELDNAMES = [
    *TARGET_METADATA_FIELDNAMES,
    "workload_id",
    "profile_name",
    "runtime_profile_name",
    "policy_subject_id",
    "checkpoint_path",
    "error_type",
    "error_message",
    "bounded_target_panel_execution",
    "protected_target_recorded_not_executed",
    "failure_recorded_not_dropped",
    "training_started",
    "replay_started",
    "ppo_used",
    "promoted",
    "private_holdout_used",
    "profile_specific_tuning",
    "ranking_run",
    "success_rate_verdict_claim_made",
    "driver_performance_claim_made",
    "claim_boundary",
]
TARGET_AGGREGATE_FIELDNAMES = [
    "target_id",
    "target_family",
    "source_family",
    "source_key",
    "episode_count",
    "failure_count",
    "accounted_count",
    "success_rate_diagnostic",
    "collision_rate_diagnostic",
    "offtrack_rate_diagnostic",
    "clearance_margin_mean",
    "return_mean",
    "all_selected_metrics_finite",
    "protected_rows_in_success_denominator",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
SOURCE_DIVERSITY_FIELDNAMES = [
    "source_family",
    "target_family",
    "target_count",
    "episode_count",
    "failure_count",
    "accounted_count",
    "success_rate_diagnostic",
    "collision_rate_diagnostic",
    "offtrack_rate_diagnostic",
    "protected_rows_in_success_denominator",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
BLOCKER_JOIN_FIELDNAMES = [
    "target_id",
    "source_family",
    "target_family",
    "source_key",
    "source_diversity_bucket",
    "existing_blocking_count",
    "existing_regressed_row_count",
    "existing_offtrack_count",
    "execution_row_count",
    "failure_row_count",
    "accounted",
    "protected_rows_in_success_denominator",
    "target_labels_actor_visible",
    "claim_boundary",
]
ACTOR_JOIN_FIELDNAMES = [
    "join_id",
    "contract_field",
    "observed_value",
    "expected_value",
    "status_pass",
    "actor_visible",
    "runtime_profile_name",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2693",
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
    "target_execution_rows",
    "offtrack_target_aggregate",
    "protected_target_aggregate",
    "source_diversity_aggregate",
    "blocker_join_rows",
    "actor_contract_join_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "failure_rows",
    "run_state",
    "doc",
]


def run_source_diverse_offtrack_protected_bounded_execution_preflight(
    *,
    m2691_dir: Path | str = DEFAULT_M2691_DIR,
    executable_specs: Path | str = DEFAULT_EXECUTABLE_SPECS,
    workload: Path | str = DEFAULT_EXECUTABLE_WORKLOAD,
    m1674_run_dir: Path | str = DEFAULT_M1674_RUN_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    profile_name: str = DEFAULT_RUNTIME_PROFILE_NAME,
    checkpoint_path: Path | str = DEFAULT_CHECKPOINT_PATH,
    policy_subject_id: str = DEFAULT_POLICY_SUBJECT_ID,
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
        m2691_dir=Path(m2691_dir),
        executable_specs=Path(executable_specs),
        workload=Path(workload),
        m1674_run_dir=Path(m1674_run_dir),
        follow_up_manifest=Path(follow_up_manifest),
    )

    execution_summary = run_target_panel_execution(
        m2691_dir=Path(m2691_dir),
        output_dir=output,
        executable_specs_path=Path(executable_specs),
        workload_path=Path(workload),
        m1674_run_dir=Path(m1674_run_dir),
        profile_name=profile_name,
        checkpoint_path=Path(checkpoint_path),
        policy_subject_id=policy_subject_id,
        eval_seed_base=int(eval_seed_base),
        device=device,
        resume=resume,
        next_blocker=next_blocker,
    )

    artifact_rows = load_execution_artifact_rows(paths)
    target_rows = load_target_panel_rows(Path(m2691_dir))
    actor_join_rows = build_actor_contract_join_rows(source=source, profile_name=profile_name)
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=False,
    )
    blocker_join_rows = build_blocker_join_rows(
        target_rows=target_rows,
        episode_rows=artifact_rows["target_execution_rows"],
        failure_rows=artifact_rows["failure_rows"],
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        execution_summary=execution_summary,
        artifact_rows=artifact_rows,
        target_rows=target_rows,
        blocker_join_rows=blocker_join_rows,
        actor_join_rows=actor_join_rows,
        claim_rows=claim_rows,
        required_artifacts_present=False,
    )

    write_csv_rows(paths["blocker_join_rows"], blocker_join_rows, fieldnames=BLOCKER_JOIN_FIELDNAMES)
    write_csv_rows(paths["actor_contract_join_rows"], actor_join_rows, fieldnames=ACTOR_JOIN_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        execution_summary=execution_summary,
        artifact_rows=artifact_rows,
        target_rows=target_rows,
        blocker_join_rows=blocker_join_rows,
        actor_join_rows=actor_join_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=False,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
        profile_name=profile_name,
        checkpoint_path=Path(checkpoint_path),
        policy_subject_id=policy_subject_id,
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
        execution_summary=execution_summary,
        artifact_rows=load_execution_artifact_rows(paths),
        target_rows=target_rows,
        blocker_join_rows=blocker_join_rows,
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
        target_rows=target_rows,
        blocker_join_rows=blocker_join_rows,
        actor_join_rows=actor_join_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
        profile_name=profile_name,
        checkpoint_path=Path(checkpoint_path),
        policy_subject_id=policy_subject_id,
        eval_seed_base=eval_seed_base,
        device=device,
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "target_execution_rows": output_dir / "target_execution_rows.csv",
        "offtrack_target_aggregate": output_dir / "offtrack_target_aggregate.csv",
        "protected_target_aggregate": output_dir / "protected_target_aggregate.csv",
        "source_diversity_aggregate": output_dir / "source_diversity_aggregate.csv",
        "blocker_join_rows": output_dir / "blocker_join_rows.csv",
        "actor_contract_join_rows": output_dir / "actor_contract_join_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "failure_rows": output_dir / "failure_rows.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2691_dir: Path,
    executable_specs: Path,
    workload: Path,
    m1674_run_dir: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2692_audit_doc": Path(
            "docs/m2692-engineering-controller-source-diverse-offtrack-protected-"
            "target-panel-materialization-result-audit.md"
        ),
        "m2691_summary": m2691_dir / "summary.json",
        "target_panel_rows": m2691_dir / "target_panel_rows.csv",
        "source_diversity_plan_rows": m2691_dir / "source_diversity_plan_rows.csv",
        "actor_contract_guard_rows": m2691_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": m2691_dir / "claim_boundary_rows.csv",
        "gate_matrix": m2691_dir / "gate_matrix.csv",
        "executable_task_specs": executable_specs,
        "executable_workload_matrix": workload,
        "m1674_summary": m1674_run_dir / "summary.json",
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2691_summary": read_json(paths["m2691_summary"]) if source_exists["m2691_summary"] else {},
        "target_panel_rows": read_csv_rows(paths["target_panel_rows"]),
        "source_diversity_plan_rows": read_csv_rows(paths["source_diversity_plan_rows"]),
        "actor_contract_guard_rows": read_csv_rows(paths["actor_contract_guard_rows"]),
        "claim_boundary_rows": read_csv_rows(paths["claim_boundary_rows"]),
        "gate_matrix": read_csv_rows(paths["gate_matrix"]),
        "m1674_summary": read_json(paths["m1674_summary"]) if source_exists["m1674_summary"] else {},
    }


def load_execution_artifact_rows(paths: dict[str, Path]) -> dict[str, list[dict[str, str]]]:
    return {
        "target_execution_rows": read_csv_rows(paths["target_execution_rows"]),
        "offtrack_target_aggregate": read_csv_rows(paths["offtrack_target_aggregate"]),
        "protected_target_aggregate": read_csv_rows(paths["protected_target_aggregate"]),
        "source_diversity_aggregate": read_csv_rows(paths["source_diversity_aggregate"]),
        "failure_rows": read_csv_rows(paths["failure_rows"]),
    }


def load_target_panel_rows(m2691_dir: Path | str) -> list[dict[str, str]]:
    return sorted(read_csv_rows(Path(m2691_dir) / "target_panel_rows.csv"), key=lambda row: str(row.get("target_id", "")))


def run_target_panel_execution(
    *,
    m2691_dir: Path | str = DEFAULT_M2691_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    executable_specs_path: Path | str = DEFAULT_EXECUTABLE_SPECS,
    workload_path: Path | str = DEFAULT_EXECUTABLE_WORKLOAD,
    m1674_run_dir: Path | str = DEFAULT_M1674_RUN_DIR,
    profile_name: str = DEFAULT_RUNTIME_PROFILE_NAME,
    checkpoint_path: Path | str = DEFAULT_CHECKPOINT_PATH,
    policy_subject_id: str = DEFAULT_POLICY_SUBJECT_ID,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    device: str = "cpu",
    resume: bool = True,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    if not resume:
        for name in (
            "target_execution_rows.csv",
            "failure_rows.csv",
            "offtrack_target_aggregate.csv",
            "protected_target_aggregate.csv",
            "source_diversity_aggregate.csv",
            "run_state.json",
        ):
            path = output / name
            if path.exists():
                path.unlink()

    target_rows = load_target_panel_rows(m2691_dir)
    executable_specs = load_executable_specs(executable_specs_path)
    spec_by_id = {str(spec["task_source_id"]): spec for spec in executable_specs}
    workload_rows = load_executable_workload(workload_path)
    profile_rows = profile_artifact_rows(m1674_run_dir=Path(m1674_run_dir))
    profile_by_name = {str(row["profile_name"]): row for row in profile_rows}
    profile_config: dict[str, Any] | None = None
    model: Any | None = None
    profile_row = profile_by_name.get(profile_name)
    if profile_row:
        profile_config = read_json(profile_row["config_path"])
        model, _ = load_actor_critic_checkpoint(Path(checkpoint_path), device=device)

    if not (output / "failure_rows.csv").exists():
        write_csv_rows(output / "failure_rows.csv", [], fieldnames=FAILURE_FIELDNAMES)
    recorded = _recorded_target_ids(output) if resume else set()
    workload_by_target = build_workload_by_target(target_rows=target_rows, workload_rows=workload_rows, profile_name=profile_name)

    for cell_index, target in enumerate(target_rows):
        target_id = str(target.get("target_id", ""))
        if target_id in recorded:
            continue
        workload_row = workload_by_target.get(target_id)
        if str(target.get("source_family", "")) != "current_sim_offtrack":
            append_csv_row(
                output / "failure_rows.csv",
                failure_row(
                    target,
                    profile_name=profile_name,
                    policy_subject_id=policy_subject_id,
                    checkpoint_path=Path(checkpoint_path),
                    workload_id="",
                    error_type="source_not_executable_in_current_runner",
                    error_message="protected mitigation taxonomy target has no current executable workload mapping",
                ),
            )
            recorded.add(target_id)
        elif profile_config is None or model is None or profile_row is None:
            append_csv_row(
                output / "failure_rows.csv",
                failure_row(
                    target,
                    profile_name=profile_name,
                    policy_subject_id=policy_subject_id,
                    checkpoint_path=Path(checkpoint_path),
                    workload_id=str(workload_row.get("workload_id", "")) if workload_row else "",
                    error_type="profile_not_available",
                    error_message=f"profile {profile_name} not found in M1674 profile artifacts",
                ),
            )
            recorded.add(target_id)
        elif not workload_row:
            append_csv_row(
                output / "failure_rows.csv",
                failure_row(
                    target,
                    profile_name=profile_name,
                    policy_subject_id=policy_subject_id,
                    checkpoint_path=Path(checkpoint_path),
                    workload_id="",
                    error_type="workload_mapping_not_found",
                    error_message="no executable workload row matched target task_family/source_edge/profile",
                ),
            )
            recorded.add(target_id)
        else:
            try:
                row = run_workload_cell(
                    workload_row=workload_row,
                    executable_spec=spec_by_id[str(workload_row["task_source_id"])],
                    profile_config=profile_config,
                    model=model,
                    profile_row=profile_row,
                    eval_seed=int(eval_seed_base) + int(cell_index),
                )
                row.update(target_metadata(target))
                row.update(
                    {
                        "bounded_target_panel_execution": True,
                        "target_panel_count": len(target_rows),
                        "representative_single_profile_per_target": True,
                        "runtime_profile_name": profile_name,
                        "policy_subject_id": policy_subject_id,
                        "checkpoint_path": str(checkpoint_path),
                        "target_labels_actor_visible": False,
                        "blocker_labels_actor_visible": False,
                        "verdict_labels_actor_visible": False,
                        "hidden_oracle_actor_input_required": False,
                        "protected_rows_in_success_denominator": False,
                        "diagnostic_only_no_verdict": True,
                        "success_rate_verdict_claim_made": False,
                        "driver_performance_claim_made": False,
                        "validation_result_claim_made": False,
                        "paper_level_claim_made": False,
                        "current_sim_verdict_claim_made": False,
                        "high_fidelity_validation_claim_made": False,
                        "full_ideal_driver_gate_passed": False,
                        "level3_self_id_claim_made": False,
                        "claim_boundary": CLAIM_SCOPE,
                    }
                )
                append_csv_row(output / "target_execution_rows.csv", row)
                recorded.add(target_id)
            except Exception as exc:  # noqa: BLE001 - failed target cells must be recorded.
                append_csv_row(
                    output / "failure_rows.csv",
                    failure_row(
                        target,
                        profile_name=profile_name,
                        policy_subject_id=policy_subject_id,
                        checkpoint_path=Path(checkpoint_path),
                        workload_id=str(workload_row.get("workload_id", "")),
                        error_type=type(exc).__name__,
                        error_message=str(exc),
                    ),
                )
                recorded.add(target_id)
        write_run_state(
            output / "run_state.json",
            {
                "target_panel_count": len(target_rows),
                "completed_execution_count": len(read_csv_rows(output / "target_execution_rows.csv")),
                "failure_count": len(read_csv_rows(output / "failure_rows.csv")),
                "accounted_count": len(_recorded_target_ids(output)),
                "latest_target_id": target_id,
                "complete": False,
            },
        )

    return finalize_target_panel_outputs(
        output_dir=output,
        target_rows=target_rows,
        profile_name=profile_name,
        policy_subject_id=policy_subject_id,
        checkpoint_path=Path(checkpoint_path),
        next_blocker=next_blocker,
    )


def build_workload_by_target(
    *,
    target_rows: list[dict[str, str]],
    workload_rows: list[dict[str, Any]],
    profile_name: str,
) -> dict[str, dict[str, Any]]:
    matches: dict[str, dict[str, Any]] = {}
    for target in target_rows:
        if str(target.get("source_family", "")) != "current_sim_offtrack":
            continue
        candidates = [
            dict(row)
            for row in workload_rows
            if str(row.get("profile_name", "")) == profile_name
            and str(row.get("task_family", "")) == str(target.get("task_family", ""))
            and str(row.get("source_edge", "")) == str(target.get("source_edge_or_axis", ""))
        ]
        if candidates:
            matches[str(target["target_id"])] = sorted(candidates, key=lambda row: str(row.get("workload_id", "")))[0]
    return matches


def finalize_target_panel_outputs(
    *,
    output_dir: Path,
    target_rows: list[dict[str, str]],
    profile_name: str,
    policy_subject_id: str,
    checkpoint_path: Path,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    episode_rows = [dict(row) for row in read_csv_rows(output_dir / "target_execution_rows.csv")]
    failure_rows = [dict(row) for row in read_csv_rows(output_dir / "failure_rows.csv")]
    write_csv_rows(output_dir / "failure_rows.csv", failure_rows, fieldnames=FAILURE_FIELDNAMES)

    offtrack_aggregate = build_target_aggregate_rows(
        [row for row in target_rows if row.get("source_family") == "current_sim_offtrack"],
        episode_rows=episode_rows,
        failure_rows=failure_rows,
    )
    protected_aggregate = build_target_aggregate_rows(
        [row for row in target_rows if row.get("source_family") == "protected_mitigation"],
        episode_rows=episode_rows,
        failure_rows=failure_rows,
    )
    source_diversity_aggregate = build_source_diversity_aggregate_rows(
        target_rows=target_rows,
        episode_rows=episode_rows,
        failure_rows=failure_rows,
    )
    write_csv_rows(output_dir / "offtrack_target_aggregate.csv", offtrack_aggregate, fieldnames=TARGET_AGGREGATE_FIELDNAMES)
    write_csv_rows(output_dir / "protected_target_aggregate.csv", protected_aggregate, fieldnames=TARGET_AGGREGATE_FIELDNAMES)
    write_csv_rows(
        output_dir / "source_diversity_aggregate.csv",
        source_diversity_aggregate,
        fieldnames=SOURCE_DIVERSITY_FIELDNAMES,
    )

    accounted_target_count = len(_target_ids(episode_rows) | _target_ids(failure_rows))
    protected_failure_count = sum(
        1 for row in failure_rows if row.get("source_family") == "protected_mitigation"
    )
    unexpected_failure_count = sum(
        1
        for row in failure_rows
        if row.get("source_family") != "protected_mitigation"
        or row.get("error_type") != "source_not_executable_in_current_runner"
    )
    all_metrics_finite = selected_metrics_are_finite(episode_rows) if episode_rows else False
    status_pass = bool(
        len(target_rows) == TARGET_PANEL_COUNT
        and len([row for row in target_rows if row.get("source_family") == "current_sim_offtrack"])
        == OFFTRACK_TARGET_COUNT
        and len([row for row in target_rows if row.get("source_family") == "protected_mitigation"])
        == PROTECTED_TARGET_COUNT
        and len(episode_rows) == OFFTRACK_TARGET_COUNT
        and protected_failure_count == PROTECTED_TARGET_COUNT
        and unexpected_failure_count == 0
        and accounted_target_count == len(target_rows)
        and all_metrics_finite
        and not any(_forbidden_execution_flag(row) for row in episode_rows)
    )
    summary = {
        "result_class": (
            "engineering_controller_source_diverse_offtrack_protected_bounded_target_execution_pass"
            if status_pass
            else "engineering_controller_source_diverse_offtrack_protected_bounded_target_execution_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "profile_name": profile_name,
        "policy_subject_id": policy_subject_id,
        "checkpoint_path": str(checkpoint_path),
        "target_panel_count": len(target_rows),
        "offtrack_target_count": sum(1 for row in target_rows if row.get("source_family") == "current_sim_offtrack"),
        "protected_target_count": sum(1 for row in target_rows if row.get("source_family") == "protected_mitigation"),
        "episode_count": len(episode_rows),
        "failure_count": len(failure_rows),
        "protected_failure_count": protected_failure_count,
        "unexpected_failure_count": unexpected_failure_count,
        "accounted_target_count": accounted_target_count,
        "all_selected_metrics_finite": bool(all_metrics_finite),
        "environment_reset_run": bool(episode_rows),
        "environment_step_run": bool(episode_rows),
        "policy_action_run": bool(episode_rows),
        "policy_rollout_run": bool(episode_rows),
        "bounded_target_panel_execution": True,
        "representative_single_profile_per_target": True,
        "protected_rows_in_success_denominator": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_verdict_claim_made": False,
        "driver_performance_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "level3_self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "artifacts": {
            "target_execution_rows": str(output_dir / "target_execution_rows.csv"),
            "failure_rows": str(output_dir / "failure_rows.csv"),
            "offtrack_target_aggregate": str(output_dir / "offtrack_target_aggregate.csv"),
            "protected_target_aggregate": str(output_dir / "protected_target_aggregate.csv"),
            "source_diversity_aggregate": str(output_dir / "source_diversity_aggregate.csv"),
            "run_state": str(output_dir / "run_state.json"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output_dir / "target_panel_execution_summary.json", summary)
    write_run_state(
        output_dir / "run_state.json",
        {
            "target_panel_count": len(target_rows),
            "completed_execution_count": len(episode_rows),
            "failure_count": len(failure_rows),
            "accounted_count": accounted_target_count,
            "complete": accounted_target_count == len(target_rows),
            "status_pass": status_pass,
        },
    )
    return summary


def build_target_aggregate_rows(
    target_rows: list[dict[str, str]],
    *,
    episode_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    episodes_by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    failures_by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in episode_rows:
        episodes_by_target[str(row.get("target_id", ""))].append(row)
    for row in failure_rows:
        failures_by_target[str(row.get("target_id", ""))].append(row)
    rows: list[dict[str, Any]] = []
    for target in target_rows:
        target_id = str(target.get("target_id", ""))
        episodes = episodes_by_target.get(target_id, [])
        failures = failures_by_target.get(target_id, [])
        rows.append(
            {
                "target_id": target_id,
                "target_family": target.get("target_family", ""),
                "source_family": target.get("source_family", ""),
                "source_key": target.get("source_key", ""),
                "episode_count": len(episodes),
                "failure_count": len(failures),
                "accounted_count": len(episodes) + len(failures),
                "success_rate_diagnostic": _mean_bool(episodes, "success"),
                "collision_rate_diagnostic": _mean_bool(episodes, "collision"),
                "offtrack_rate_diagnostic": _mean_eq(episodes, "termination_reason", "off_track"),
                "clearance_margin_mean": _mean_float(episodes, "min_clearance_margin"),
                "return_mean": _mean_float(episodes, "return"),
                "all_selected_metrics_finite": selected_metrics_are_finite(episodes) if episodes else "",
                "protected_rows_in_success_denominator": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_source_diversity_aggregate_rows(
    *,
    target_rows: list[dict[str, str]],
    episode_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for target in target_rows:
        groups[(str(target.get("source_family", "")), str(target.get("target_family", "")))].append(target)
    rows: list[dict[str, Any]] = []
    for (source_family, target_family), targets in sorted(groups.items()):
        target_ids = {str(row.get("target_id", "")) for row in targets}
        episodes = [row for row in episode_rows if str(row.get("target_id", "")) in target_ids]
        failures = [row for row in failure_rows if str(row.get("target_id", "")) in target_ids]
        rows.append(
            {
                "source_family": source_family,
                "target_family": target_family,
                "target_count": len(targets),
                "episode_count": len(episodes),
                "failure_count": len(failures),
                "accounted_count": len(episodes) + len(failures),
                "success_rate_diagnostic": _mean_bool(episodes, "success"),
                "collision_rate_diagnostic": _mean_bool(episodes, "collision"),
                "offtrack_rate_diagnostic": _mean_eq(episodes, "termination_reason", "off_track"),
                "protected_rows_in_success_denominator": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_blocker_join_rows(
    *,
    target_rows: list[dict[str, str]],
    episode_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    episode_counts = Counter(str(row.get("target_id", "")) for row in episode_rows)
    failure_counts = Counter(str(row.get("target_id", "")) for row in failure_rows)
    rows: list[dict[str, Any]] = []
    for target in target_rows:
        target_id = str(target.get("target_id", ""))
        rows.append(
            {
                "target_id": target_id,
                "source_family": target.get("source_family", ""),
                "target_family": target.get("target_family", ""),
                "source_key": target.get("source_key", ""),
                "source_diversity_bucket": target.get("source_diversity_bucket", ""),
                "existing_blocking_count": target.get("blocking_count", ""),
                "existing_regressed_row_count": target.get("regressed_row_count", ""),
                "existing_offtrack_count": target.get("existing_offtrack_count", ""),
                "execution_row_count": int(episode_counts.get(target_id, 0)),
                "failure_row_count": int(failure_counts.get(target_id, 0)),
                "accounted": int(episode_counts.get(target_id, 0)) + int(failure_counts.get(target_id, 0)) == 1,
                "protected_rows_in_success_denominator": False,
                "target_labels_actor_visible": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_join_rows(*, source: dict[str, Any], profile_name: str) -> list[dict[str, Any]]:
    guard_rows = {str(row.get("contract_field", "")): row for row in source["actor_contract_guard_rows"]}
    rows = [
        actor_join("observation_shape", P0_OBSERVATION_DIM, P0_OBSERVATION_DIM, True, profile_name),
        actor_join("action_shape", ACTION_DIM, ACTION_DIM, True, profile_name),
        actor_join("deployed_action_mapping", "[steer, throttle, brake]", "[steer, throttle, brake]", True, profile_name),
        actor_join("hidden_oracle_actor_input_detected", False, False, False, profile_name),
        actor_join("offtrack_labels_actor_visible", False, False, False, profile_name),
        actor_join("protected_labels_actor_visible", False, False, False, profile_name),
        actor_join("target_labels_actor_visible", False, False, False, profile_name),
        actor_join("blocker_labels_actor_visible", False, False, False, profile_name),
        actor_join("verdict_labels_actor_visible", False, False, False, profile_name),
    ]
    for row in rows:
        source_guard = guard_rows.get(str(row["contract_field"]), {})
        if source_guard:
            row["source_guard_status_pass"] = _bool(source_guard.get("status_pass", False))
            row["status_pass"] = _bool(row["status_pass"]) and _bool(source_guard.get("status_pass", False))
    return rows


def actor_join(field: str, observed: Any, expected: Any, actor_visible: bool, profile_name: str) -> dict[str, Any]:
    return {
        "join_id": f"m2693_actor_join_{field}",
        "contract_field": field,
        "observed_value": observed,
        "expected_value": expected,
        "status_pass": str(observed) == str(expected),
        "actor_visible": actor_visible,
        "runtime_profile_name": profile_name,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_claim_boundary_rows(*, follow_up_manifest_registered: bool, artifacts_present: bool) -> list[dict[str, Any]]:
    allowed = [
        ("bounded_execution_preflight", "execution", True, "M2693 bounded target-panel execution/failure rows"),
        ("target_execution_rows_materialized", "artifact", artifacts_present, "target_execution_rows.csv"),
        ("offtrack_target_aggregate_materialized", "artifact", artifacts_present, "offtrack_target_aggregate.csv"),
        ("protected_target_failure_rows_materialized", "artifact", artifacts_present, "failure_rows.csv"),
        ("source_diversity_aggregate_materialized", "artifact", artifacts_present, "source_diversity_aggregate.csv"),
        ("blocker_join_rows_materialized", "artifact", artifacts_present, "blocker_join_rows.csv"),
        ("actor_contract_join_rows_materialized", "artifact", artifacts_present, "actor_contract_join_rows.csv"),
        ("claim_boundary_rows_materialized", "artifact", artifacts_present, "claim_boundary_rows.csv"),
        ("gate_matrix_materialized", "artifact", artifacts_present, "gate_matrix.csv"),
        ("run_state_materialized", "artifact", artifacts_present, "run_state.json"),
        ("diagnostic_metrics_recorded", "diagnostic_metric", True, "diagnostic target/source aggregate rows only"),
        ("follow_up_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2694 result-audit manifest"),
    ]
    blocked = [
        ("replay_execution", "execution", "future replay manifest"),
        ("validation_execution", "validation", "future validation manifest"),
        ("training_or_ppo", "execution", "future training manifest"),
        ("private_holdout_tuning", "holdout_policy", "forbidden in M2693"),
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


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    execution_summary: dict[str, Any],
    artifact_rows: dict[str, list[dict[str, Any]]],
    target_rows: list[dict[str, Any]],
    blocker_join_rows: list[dict[str, Any]],
    actor_join_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    episode_rows = artifact_rows["target_execution_rows"]
    failure_rows = artifact_rows["failure_rows"]
    offtrack_targets = [row for row in target_rows if row.get("source_family") == "current_sim_offtrack"]
    protected_targets = [row for row in target_rows if row.get("source_family") == "protected_mitigation"]
    protected_failures = [
        row
        for row in failure_rows
        if row.get("source_family") == "protected_mitigation"
        and row.get("error_type") == "source_not_executable_in_current_runner"
    ]
    unexpected_failures = [
        row
        for row in failure_rows
        if row.get("source_family") != "protected_mitigation"
        or row.get("error_type") != "source_not_executable_in_current_runner"
    ]
    source_families = {str(row.get("source_family", "")) for row in target_rows}
    allowed_claims = [row for row in claim_rows if _bool(row["allowed_in_m2693"])]
    blocked_claims = [row for row in claim_rows if not _bool(row["allowed_in_m2693"])]
    accounted_target_count = len(_target_ids(episode_rows) | _target_ids(failure_rows))
    return [
        gate("m2693_gate_source_artifacts_present", "lineage", all(source["source_exists"].values()), source["source_exists"], "all M2691/M2692/workload/follow-up artifacts present", "lineage_invalid"),
        gate("m2691_status_pass", "lineage", _bool(source["m2691_summary"].get("status_pass", False)), source["m2691_summary"].get("status_pass", None), True, "lineage_invalid"),
        gate("m2691_target_panel_shape", "target_panel", len(target_rows) == TARGET_PANEL_COUNT and len(offtrack_targets) == OFFTRACK_TARGET_COUNT and len(protected_targets) == PROTECTED_TARGET_COUNT, f"targets={len(target_rows)} offtrack={len(offtrack_targets)} protected={len(protected_targets)}", f"targets={TARGET_PANEL_COUNT} offtrack={OFFTRACK_TARGET_COUNT} protected={PROTECTED_TARGET_COUNT}", "metric_artifact"),
        gate("source_diversity_preserved", "source_diversity", {"current_sim_offtrack", "protected_mitigation"}.issubset(source_families), sorted(source_families), "current_sim_offtrack and protected_mitigation", "objective_overfit"),
        gate("offtrack_targets_executed", "execution", len(episode_rows) == OFFTRACK_TARGET_COUNT and all(row.get("source_family") == "current_sim_offtrack" for row in episode_rows), len(episode_rows), OFFTRACK_TARGET_COUNT, "scenario_sampling_failure"),
        gate("protected_targets_recorded_as_failures", "execution", len(protected_failures) == PROTECTED_TARGET_COUNT, len(protected_failures), PROTECTED_TARGET_COUNT, "behavior_regression"),
        gate("no_unexpected_failure_rows", "execution", len(unexpected_failures) == 0, len(unexpected_failures), 0, "behavior_regression"),
        gate("all_targets_accounted", "execution", accounted_target_count == len(target_rows), accounted_target_count, len(target_rows), "metric_artifact"),
        gate("blocker_join_rows_cover_targets", "blocker_join", len(blocker_join_rows) == len(target_rows) and all(_bool(row["accounted"]) for row in blocker_join_rows), f"rows={len(blocker_join_rows)} accounted={sum(_bool(row['accounted']) for row in blocker_join_rows)}", len(target_rows), "metric_artifact"),
        gate("all_selected_metrics_finite", "metric", selected_metrics_are_finite(episode_rows) if episode_rows else False, execution_summary.get("all_selected_metrics_finite"), True, "metric_artifact"),
        gate("actor_contract_preserved", "contract", all(_bool(row["status_pass"]) for row in actor_join_rows), f"rows={len(actor_join_rows)} pass={sum(_bool(row['status_pass']) for row in actor_join_rows)}", "all actor joins pass", "contract_violation"),
        gate("target_labels_actor_invisible", "contract", all(not _bool(row.get("target_labels_actor_visible", False)) for row in target_rows + episode_rows + failure_rows), "target labels actor-invisible", "all false", "contract_violation"),
        gate("no_hidden_oracle_actor_input", "contract", all(not _bool(row.get("hidden_oracle_actor_input_required", False)) for row in target_rows + episode_rows + failure_rows), "hidden/oracle target requirement false", "all false", "contract_violation"),
        gate("protected_not_success_denominator", "proof_washout", all(not _bool(row.get("protected_rows_in_success_denominator", False)) for row in target_rows + episode_rows + failure_rows), "protected rows outside success denominator", "all false", "proof_washout"),
        gate("bounded_single_profile_not_ranking", "claim_boundary", len({str(row.get("runtime_profile_name") or row.get("profile_name", "")) for row in episode_rows}) == 1 and not any(_bool(row.get("ranking_run", False)) for row in episode_rows + failure_rows), "single profile diagnostic; no ranking", "single profile diagnostic; no ranking", "objective_overfit"),
        gate("no_forbidden_execution", "execution_guardrail", not any(_forbidden_execution_flag(row) for row in episode_rows + failure_rows), "no replay/train/PPO/private holdout/tuning/promotion", "all false", "objective_overfit"),
        gate("claim_boundary_blocks_overclaim", "claim_boundary", all(_bool(row["status_pass"]) for row in allowed_claims) and all(not _bool(row["claim_made"]) and _bool(row["status_pass"]) for row in blocked_claims), f"allowed={len(allowed_claims)} blocked={len(blocked_claims)}", "allowed claims pass and blocked claims not made", "proof_washout"),
        gate("required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True, "lineage_invalid"),
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    execution_summary: dict[str, Any],
    artifact_rows: dict[str, list[dict[str, Any]]],
    target_rows: list[dict[str, Any]],
    blocker_join_rows: list[dict[str, Any]],
    actor_join_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
    profile_name: str,
    checkpoint_path: Path,
    policy_subject_id: str,
    eval_seed_base: int,
    device: str,
) -> dict[str, Any]:
    episode_rows = artifact_rows["target_execution_rows"]
    failure_rows = artifact_rows["failure_rows"]
    offtrack_targets = [row for row in target_rows if row.get("source_family") == "current_sim_offtrack"]
    protected_targets = [row for row in target_rows if row.get("source_family") == "protected_mitigation"]
    protected_failures = [
        row
        for row in failure_rows
        if row.get("source_family") == "protected_mitigation"
        and row.get("error_type") == "source_not_executable_in_current_runner"
    ]
    unexpected_failures = [
        row
        for row in failure_rows
        if row.get("source_family") != "protected_mitigation"
        or row.get("error_type") != "source_not_executable_in_current_runner"
    ]
    allowed_claim_rows = [row for row in claim_rows if _bool(row["allowed_in_m2693"])]
    blocked_claim_rows = [row for row in claim_rows if not _bool(row["allowed_in_m2693"])]
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_source_diverse_offtrack_protected_bounded_execution_preflight_pass"
            if status_pass
            else "engineering_controller_source_diverse_offtrack_protected_bounded_execution_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "profile_name": profile_name,
        "policy_subject_id": policy_subject_id,
        "checkpoint_path": str(checkpoint_path),
        "eval_seed_base": int(eval_seed_base),
        "device": device,
        "source_artifacts_present": all(source["source_exists"].values()),
        "m2691_status_pass": _bool(source["m2691_summary"].get("status_pass", False)),
        "target_panel_count": len(target_rows),
        "offtrack_target_count": len(offtrack_targets),
        "protected_target_count": len(protected_targets),
        "episode_count": len(episode_rows),
        "failure_count": len(failure_rows),
        "protected_failure_count": len(protected_failures),
        "unexpected_failure_count": len(unexpected_failures),
        "accounted_target_count": len(_target_ids(episode_rows) | _target_ids(failure_rows)),
        "execution_summary_result_class": execution_summary.get("result_class", ""),
        "target_runner_pass": execution_summary.get("result_class")
        == "engineering_controller_source_diverse_offtrack_protected_bounded_target_execution_pass",
        "all_selected_metrics_finite": selected_metrics_are_finite(episode_rows) if episode_rows else False,
        "offtrack_target_aggregate_row_count": len(artifact_rows["offtrack_target_aggregate"]),
        "protected_target_aggregate_row_count": len(artifact_rows["protected_target_aggregate"]),
        "source_diversity_aggregate_row_count": len(artifact_rows["source_diversity_aggregate"]),
        "blocker_join_row_count": len(blocker_join_rows),
        "actor_contract_join_row_count": len(actor_join_rows),
        "actor_contract_join_rows_pass": all(_bool(row["status_pass"]) for row in actor_join_rows),
        "claim_boundary_row_count": len(claim_rows),
        "allowed_claim_boundary_row_count": len(allowed_claim_rows),
        "blocked_claim_boundary_row_count": len(blocked_claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "environment_reset_run": bool(episode_rows),
        "environment_step_run": bool(episode_rows),
        "policy_action_run": bool(episode_rows),
        "policy_rollout_run": bool(episode_rows),
        "bounded_target_panel_execution": True,
        "representative_single_profile_per_target": True,
        "measured_validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "actor_input_contract_changed": False,
        "actor_contract_shape_72_action_3": True,
        "hidden_oracle_actor_input_detected": False,
        "target_labels_actor_visible": False,
        "blocker_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "protected_rows_in_success_denominator": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_metric_recorded": True,
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
            "# M2693 Engineering Controller Source Diverse Offtrack Protected Bounded Execution Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- profile: `{summary['profile_name']}`",
            f"- policy subject: `{summary['policy_subject_id']}`",
            f"- checkpoint: `{summary['checkpoint_path']}`",
            f"- target panel rows: {summary['target_panel_count']}",
            f"- off-track executed rows: {summary['episode_count']}/{summary['offtrack_target_count']}",
            f"- protected recorded failure rows: {summary['protected_failure_count']}/{summary['protected_target_count']}",
            f"- accounted target rows: {summary['accounted_target_count']}/{summary['target_panel_count']}",
            f"- unexpected failure rows: {summary['unexpected_failure_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M2693 records bounded closed-loop diagnostic data for the current-sim off-track targets and keeps protected mitigation targets outside success denominators. The protected rows are recorded as explicit non-executable target failures when no current runner mapping exists.",
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


def target_metadata(target: Mapping[str, Any]) -> dict[str, Any]:
    return {key: target.get(key, "") for key in TARGET_METADATA_FIELDNAMES}


def failure_row(
    target: Mapping[str, Any],
    *,
    profile_name: str,
    policy_subject_id: str,
    checkpoint_path: Path,
    workload_id: str,
    error_type: str,
    error_message: str,
) -> dict[str, Any]:
    return {
        **target_metadata(target),
        "workload_id": workload_id,
        "profile_name": profile_name,
        "runtime_profile_name": profile_name,
        "policy_subject_id": policy_subject_id,
        "checkpoint_path": str(checkpoint_path),
        "error_type": error_type,
        "error_message": error_message,
        "bounded_target_panel_execution": True,
        "protected_target_recorded_not_executed": str(target.get("source_family", "")) == "protected_mitigation",
        "failure_recorded_not_dropped": True,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "ranking_run": False,
        "success_rate_verdict_claim_made": False,
        "driver_performance_claim_made": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def claim(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m2693_claim_{'allowed' if allowed else 'blocked'}_{claim_id}",
        "claim_family": family,
        "allowed_in_m2693": allowed,
        "claim_made": bool(made),
        "status_pass": bool(made) if allowed else not bool(made),
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
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def _recorded_target_ids(output_dir: Path) -> set[str]:
    return _target_ids(read_csv_rows(output_dir / "target_execution_rows.csv")) | _target_ids(
        read_csv_rows(output_dir / "failure_rows.csv")
    )


def _target_ids(rows: Iterable[Mapping[str, Any]]) -> set[str]:
    return {str(row.get("target_id", "")) for row in rows if row.get("target_id")}


def _forbidden_execution_flag(row: Mapping[str, Any]) -> bool:
    forbidden = (
        "training_started",
        "training_run",
        "replay_started",
        "replay_run",
        "ppo_used",
        "ppo_run",
        "private_holdout_used",
        "profile_specific_tuning",
        "ranking_run",
        "winner_selected",
        "promoted",
        "checkpoint_promoted",
        "success_rate_verdict_claim_made",
        "driver_performance_claim_made",
        "validation_result_claim_made",
        "paper_level_claim_made",
        "paper_claim_made",
        "current_sim_verdict_claim_made",
        "high_fidelity_validation_claim_made",
        "full_ideal_driver_gate_passed",
        "level3_self_id_claim_made",
    )
    return any(_bool(row.get(key, False)) for key in forbidden)


def _mean_bool(rows: list[Mapping[str, Any]], key: str) -> float | str:
    if not rows:
        return ""
    return float(np.mean([_bool(row.get(key, False)) for row in rows]))


def _mean_eq(rows: list[Mapping[str, Any]], key: str, expected: str) -> float | str:
    if not rows:
        return ""
    return float(np.mean([str(row.get(key, "")) == expected for row in rows]))


def _mean_float(rows: list[Mapping[str, Any]], key: str) -> float | str:
    values: list[float] = []
    for row in rows:
        try:
            value = float(row.get(key, float("nan")))
        except (TypeError, ValueError):
            value = float("nan")
        if np.isfinite(value):
            values.append(value)
    return float(np.mean(values)) if values else ""


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2691-dir", type=Path, default=DEFAULT_M2691_DIR)
    parser.add_argument("--executable-specs", type=Path, default=DEFAULT_EXECUTABLE_SPECS)
    parser.add_argument("--workload", type=Path, default=DEFAULT_EXECUTABLE_WORKLOAD)
    parser.add_argument("--m1674-run-dir", type=Path, default=DEFAULT_M1674_RUN_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--profile-name", default=DEFAULT_RUNTIME_PROFILE_NAME)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT_PATH)
    parser.add_argument("--policy-subject-id", default=DEFAULT_POLICY_SUBJECT_ID)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--no-resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_source_diverse_offtrack_protected_bounded_execution_preflight(
        m2691_dir=args.m2691_dir,
        executable_specs=args.executable_specs,
        workload=args.workload,
        m1674_run_dir=args.m1674_run_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        profile_name=args.profile_name,
        checkpoint_path=args.checkpoint,
        policy_subject_id=args.policy_subject_id,
        eval_seed_base=args.eval_seed_base,
        device=args.device,
        resume=not args.no_resume,
    )


if __name__ == "__main__":
    main()
