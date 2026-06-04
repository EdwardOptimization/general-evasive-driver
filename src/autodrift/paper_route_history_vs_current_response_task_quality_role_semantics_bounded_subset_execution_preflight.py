"""Run Route B role/task-quality bounded subset execution preflight.

M2684 consumes the 216-row M2682 proposed measured subset and executes only
those public current-sim cells. It records diagnostic rows and aggregates for a
later result audit. It does not train, replay, rank controller families, select
winners, promote checkpoints, compute verdicts, or claim paper/self-ID
evidence.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.controller_family_decisive_matrix_protocol import EXPECTED_PROFILE_NAMES
from autodrift.controller_family_executable_workload_materialization_preflight import (
    profile_artifact_rows,
)
from autodrift.controller_family_full_rollout_execution import (
    DEFAULT_EXECUTABLE_SPECS,
    DEFAULT_EXECUTABLE_WORKLOAD,
    aggregate_rows,
    append_csv_row,
    load_executable_specs,
    load_executable_workload,
    read_csv_rows,
    run_workload_cell,
    selected_metrics_are_finite,
    write_run_state,
)
from autodrift.controller_family_measured_routing_smoke import DEFAULT_M1674_RUN_DIR
from autodrift.paper_route_history_vs_current_response_comparison_protocol_materialization import (
    REQUIRED_CONTROLLER_IDS,
)


DEFAULT_MILESTONE = (
    "m2684-paper-route-history-vs-current-response-task-quality-role-semantics-"
    "bounded-subset-execution-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2685-paper-route-history-vs-current-response-task-quality-role-semantics-"
    "bounded-subset-execution-result-audit"
)
DEFAULT_M2682_DIR = Path(
    "runs/m2682_paper_route_history_vs_current_response_task_quality_role_semantics_repair_materialization"
)
DEFAULT_RUNTIME_ENFORCEMENT_DIR = Path(
    "runs/m2673_paper_route_history_vs_current_response_runtime_enforcement_materialization"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2684_paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2684-paper-route-history-vs-current-response-task-quality-role-semantics-"
    "bounded-subset-execution-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2685-paper-route-history-vs-current-response-task-quality-"
    "role-semantics-bounded-subset-execution-result-audit.json"
)
DEFAULT_EVAL_SEED_BASE = 268400
FULL_PUBLIC_MATRIX_COUNT = 864
TARGET_SUBSET_EPISODE_COUNT = 216
TARGET_SUBSET_SPEC_COUNT = 18
TARGET_PROFILE_COUNT = len(EXPECTED_PROFILE_NAMES)

CLAIM_SCOPE = (
    "Route B task-quality and role-semantics bounded subset execution "
    "preflight only; reset, step, rollout, and policy actions may be recorded "
    "for the pre-registered M2682 216-row subset or explicit failure rows, "
    "but no replay, training, PPO, private holdout, profile-specific tuning, "
    "controller-family ranking, winner selection, promotion, success-rate "
    "verdict, comparison-delta verdict, driver-performance, paper, finite-"
    "window-vs-GRU, current-response sufficiency, current-sim, high-fidelity "
    "validation, full ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "controller-family ranking, winner selection, checkpoint promotion, "
    "success-rate verdict, comparison-delta verdict, driver performance, "
    "validation readiness or result, paper-level evidence, finite-window-vs-"
    "GRU result, current-response sufficiency result, current-sim verdict, "
    "high-fidelity validation, full ideal driver completion, or level3 "
    "self-identification"
)

SUBSET_METADATA_FIELDNAMES = [
    "subset_row_id",
    "candidate_id",
    "task_source_id",
    "workload_id",
    "profile_name",
    "task_family",
    "source_edge",
    "role_semantics_proxy",
    "window_tag",
    "strata",
    "existing_outcome_bucket",
    "existing_termination_reason",
    "existing_profile_env_history_length",
    "future_execution_reason",
    "proposed_execution_stage",
    "diagnostic_only_no_verdict",
    "not_selected_from_success_only",
    "actor_input_contract_changed",
    "role_semantics_actor_visible",
    "hidden_oracle_actor_input_required",
]
FAILURE_FIELDNAMES = [
    *SUBSET_METADATA_FIELDNAMES,
    "error_type",
    "error_message",
    "bounded_subset_execution",
    "training_started",
    "replay_started",
    "ppo_used",
    "promoted",
    "private_holdout_used",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
    "claim_boundary",
]
RUNTIME_JOIN_FIELDNAMES = [
    "protocol_controller_family_id",
    "runtime_profile_name",
    "executed_profile_name",
    "target_subset_cell_count",
    "target_subset_spec_count",
    "executed_episode_count",
    "executed_spec_count",
    "failed_cell_count",
    "accounted_cell_count",
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
    "bounded_subset_policy_rollout_run",
    "policy_rollout_allowed",
    "training_started",
    "ppo_used",
    "replay_started",
    "profile_specific_tuning",
    "role_semantics_actor_visible",
    "success_rate_metric_recorded",
    "comparison_delta_metric_recorded",
    "success_rate_verdict_claim_made",
    "controller_family_ranking_claim_made",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2684",
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
    "subset_rollout_execution_summary",
    "episode_rows",
    "profile_aggregate",
    "spec_aggregate",
    "candidate_aggregate",
    "source_edge_aggregate",
    "role_semantics_aggregate",
    "outcome_aggregate",
    "termination_reason_aggregate",
    "runtime_enforcement_join_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "failure_rows",
    "run_state",
    "doc",
]


def run_bounded_subset_execution_preflight(
    *,
    m2682_dir: Path | str = DEFAULT_M2682_DIR,
    runtime_enforcement_dir: Path | str = DEFAULT_RUNTIME_ENFORCEMENT_DIR,
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
        m2682_dir=Path(m2682_dir),
        runtime_enforcement_dir=Path(runtime_enforcement_dir),
        executable_specs=Path(executable_specs),
        workload=Path(workload),
        m1674_run_dir=Path(m1674_run_dir),
        follow_up_manifest=Path(follow_up_manifest),
    )

    subset_summary = run_subset_rollout_execution(
        m2682_dir=Path(m2682_dir),
        output_dir=output,
        executable_specs_path=Path(executable_specs),
        workload_path=Path(workload),
        m1674_run_dir=Path(m1674_run_dir),
        eval_seed_base=int(eval_seed_base),
        device=str(device),
        resume=bool(resume),
        next_blocker=next_blocker,
    )
    write_json(paths["subset_rollout_execution_summary"], subset_summary)

    artifact_rows = load_execution_artifact_rows(paths)
    runtime_rows = read_csv_rows(source["paths"]["protocol_to_runtime_profile_rows"])
    subset_rows = read_csv_rows(source["paths"]["proposed_measured_subset_rows"])
    join_rows = build_runtime_enforcement_join_rows(
        runtime_rows=runtime_rows,
        subset_rows=subset_rows,
        episode_rows=artifact_rows["episode_rows"],
        failure_rows=artifact_rows["failure_rows"],
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=False,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        subset_summary=subset_summary,
        artifact_rows=artifact_rows,
        subset_rows=subset_rows,
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
        subset_summary=subset_summary,
        artifact_rows=artifact_rows,
        subset_rows=subset_rows,
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
        subset_summary=subset_summary,
        artifact_rows=artifact_rows,
        subset_rows=subset_rows,
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
        subset_summary=subset_summary,
        artifact_rows=artifact_rows,
        subset_rows=subset_rows,
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
        "subset_rollout_execution_summary": output_dir / "subset_rollout_execution_summary.json",
        "episode_rows": output_dir / "episode_rows.csv",
        "profile_aggregate": output_dir / "profile_aggregate.csv",
        "spec_aggregate": output_dir / "spec_aggregate.csv",
        "candidate_aggregate": output_dir / "candidate_aggregate.csv",
        "source_edge_aggregate": output_dir / "source_edge_aggregate.csv",
        "role_semantics_aggregate": output_dir / "role_semantics_aggregate.csv",
        "outcome_aggregate": output_dir / "outcome_aggregate.csv",
        "termination_reason_aggregate": output_dir / "termination_reason_aggregate.csv",
        "runtime_enforcement_join_rows": output_dir / "runtime_enforcement_join_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "failure_rows": output_dir / "failure_rows.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2682_dir: Path,
    runtime_enforcement_dir: Path,
    executable_specs: Path,
    workload: Path,
    m1674_run_dir: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2683_audit_doc": Path(
            "docs/m2683-paper-route-history-vs-current-response-task-quality-role-semantics-"
            "repair-materialization-result-audit.md"
        ),
        "m2682_summary": m2682_dir / "summary.json",
        "proposed_measured_subset_rows": m2682_dir / "proposed_measured_subset_rows.csv",
        "repair_candidate_rows": m2682_dir / "repair_candidate_rows.csv",
        "role_task_quality_blocker_rows": m2682_dir / "role_task_quality_blocker_rows.csv",
        "m2673_summary": runtime_enforcement_dir / "summary.json",
        "protocol_to_runtime_profile_rows": runtime_enforcement_dir / "protocol_to_runtime_profile_rows.csv",
        "m2673_gate_matrix": runtime_enforcement_dir / "gate_matrix.csv",
        "m1690_summary": executable_specs.parent / "summary.json",
        "executable_task_specs": executable_specs,
        "executable_workload_matrix": workload,
        "m1674_summary": m1674_run_dir / "summary.json",
        "m2684_manifest": Path(
            "experiments/manifests/m2684-paper-route-history-vs-current-response-task-quality-"
            "role-semantics-bounded-subset-execution-preflight.json"
        ),
        "follow_up_manifest": follow_up_manifest,
    }
    return {
        "paths": paths,
        "source_exists": {key: path.exists() for key, path in paths.items()},
        "m2682_summary": read_json(paths["m2682_summary"]) if paths["m2682_summary"].exists() else {},
        "m2673_summary": read_json(paths["m2673_summary"]) if paths["m2673_summary"].exists() else {},
        "m1690_summary": read_json(paths["m1690_summary"]) if paths["m1690_summary"].exists() else {},
        "m1674_summary": read_json(paths["m1674_summary"]) if paths["m1674_summary"].exists() else {},
    }


def load_execution_artifact_rows(paths: dict[str, Path]) -> dict[str, list[dict[str, str]]]:
    return {
        "episode_rows": read_csv_rows(paths["episode_rows"]),
        "profile_aggregate_rows": read_csv_rows(paths["profile_aggregate"]),
        "spec_aggregate_rows": read_csv_rows(paths["spec_aggregate"]),
        "candidate_aggregate_rows": read_csv_rows(paths["candidate_aggregate"]),
        "source_edge_aggregate_rows": read_csv_rows(paths["source_edge_aggregate"]),
        "role_semantics_aggregate_rows": read_csv_rows(paths["role_semantics_aggregate"]),
        "outcome_aggregate_rows": read_csv_rows(paths["outcome_aggregate"]),
        "termination_reason_aggregate_rows": read_csv_rows(paths["termination_reason_aggregate"]),
        "failure_rows": read_csv_rows(paths["failure_rows"]),
    }


def load_subset_rows(m2682_dir: Path | str) -> list[dict[str, str]]:
    rows = read_csv_rows(Path(m2682_dir) / "proposed_measured_subset_rows.csv")
    return sorted(rows, key=lambda row: str(row.get("subset_row_id", "")))


def build_subset_workload_rows(
    *,
    subset_rows: list[dict[str, str]],
    workload_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    workload_by_id = {str(row["workload_id"]): dict(row) for row in workload_rows}
    rows: list[dict[str, Any]] = []
    for subset in subset_rows:
        workload_id = str(subset.get("workload_id", ""))
        base = dict(workload_by_id.get(workload_id, {}))
        if not base:
            raise KeyError(f"M2682 subset workload_id not found in executable workload: {workload_id}")
        for key in ("task_source_id", "profile_name", "task_family", "source_edge", "window_tag", "strata"):
            if str(base.get(key, "")) != str(subset.get(key, "")):
                raise ValueError(
                    f"M2682 subset {workload_id} disagrees with executable workload for {key}: "
                    f"{subset.get(key, '')} != {base.get(key, '')}"
                )
        for key in SUBSET_METADATA_FIELDNAMES:
            base[key] = subset.get(key, "")
        rows.append(base)
    return rows


def validate_subset_rows(subset_rows: list[dict[str, str]]) -> dict[str, Any]:
    workload_ids = [str(row.get("workload_id", "")) for row in subset_rows]
    task_source_ids = {str(row.get("task_source_id", "")) for row in subset_rows}
    profiles = {str(row.get("profile_name", "")) for row in subset_rows}
    candidates = {str(row.get("candidate_id", "")) for row in subset_rows}
    return {
        "subset_row_count": len(subset_rows),
        "unique_workload_count": len(set(workload_ids)),
        "unique_task_source_count": len(task_source_ids),
        "unique_profile_count": len(profiles),
        "candidate_count": len(candidates),
        "task_family_count": len({str(row.get("task_family", "")) for row in subset_rows}),
        "role_semantics_actor_visible": any(_bool(row.get("role_semantics_actor_visible", False)) for row in subset_rows),
        "actor_input_contract_changed": any(_bool(row.get("actor_input_contract_changed", False)) for row in subset_rows),
        "hidden_oracle_actor_input_required": any(
            _bool(row.get("hidden_oracle_actor_input_required", False)) for row in subset_rows
        ),
        "diagnostic_only_no_verdict": all(_bool(row.get("diagnostic_only_no_verdict", False)) for row in subset_rows),
        "not_selected_from_success_only": all(_bool(row.get("not_selected_from_success_only", False)) for row in subset_rows),
        "duplicate_workload_count": len(workload_ids) - len(set(workload_ids)),
        "is_full_public_matrix": len(subset_rows) == FULL_PUBLIC_MATRIX_COUNT,
        "profiles": sorted(profiles),
    }


def _load_profile_cache(profile_rows: list[Mapping[str, Any]], *, device: str) -> dict[str, tuple[dict[str, Any], Any]]:
    cache: dict[str, tuple[dict[str, Any], Any]] = {}
    for row in profile_rows:
        config = read_json(row["config_path"])
        model, _ = load_actor_critic_checkpoint(row["checkpoint_path"], device=device)
        cache[str(row["profile_name"])] = (config, model)
    return cache


def _recorded_workload_ids(output_dir: Path) -> set[str]:
    ids = {str(row["workload_id"]) for row in read_csv_rows(output_dir / "episode_rows.csv") if row.get("workload_id")}
    ids.update(str(row["workload_id"]) for row in read_csv_rows(output_dir / "failure_rows.csv") if row.get("workload_id"))
    return ids


def run_subset_rollout_execution(
    *,
    m2682_dir: Path | str = DEFAULT_M2682_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    executable_specs_path: Path | str = DEFAULT_EXECUTABLE_SPECS,
    workload_path: Path | str = DEFAULT_EXECUTABLE_WORKLOAD,
    m1674_run_dir: Path | str = DEFAULT_M1674_RUN_DIR,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    device: str = "cpu",
    resume: bool = True,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    if not resume:
        for name in (
            "episode_rows.csv",
            "failure_rows.csv",
            "summary.json",
            "run_state.json",
            "profile_aggregate.csv",
            "spec_aggregate.csv",
            "candidate_aggregate.csv",
            "source_edge_aggregate.csv",
            "role_semantics_aggregate.csv",
            "outcome_aggregate.csv",
            "termination_reason_aggregate.csv",
            "subset_rollout_execution_summary.json",
        ):
            path = output / name
            if path.exists():
                path.unlink()

    subset_rows = load_subset_rows(m2682_dir)
    executable_specs = load_executable_specs(executable_specs_path)
    spec_by_id = {str(spec["task_source_id"]): spec for spec in executable_specs}
    workload_rows = build_subset_workload_rows(
        subset_rows=subset_rows,
        workload_rows=load_executable_workload(workload_path),
    )
    profile_rows = profile_artifact_rows(m1674_run_dir=m1674_run_dir)
    profile_by_name = {str(row["profile_name"]): row for row in profile_rows}
    profile_cache = _load_profile_cache(profile_rows, device=device)
    recorded = _recorded_workload_ids(output) if resume else set()
    if not (output / "failure_rows.csv").exists():
        write_csv_rows(output / "failure_rows.csv", [], fieldnames=FAILURE_FIELDNAMES)

    for cell_index, workload_row in enumerate(workload_rows):
        workload_id = str(workload_row["workload_id"])
        if workload_id in recorded:
            continue
        profile_name = str(workload_row["profile_name"])
        eval_seed = int(eval_seed_base) + int(cell_index)
        try:
            profile_config, model = profile_cache[profile_name]
            row = run_workload_cell(
                workload_row=workload_row,
                executable_spec=spec_by_id[str(workload_row["task_source_id"])],
                profile_config=profile_config,
                model=model,
                profile_row=profile_by_name[profile_name],
                eval_seed=eval_seed,
            )
            row.update({key: workload_row.get(key, "") for key in SUBSET_METADATA_FIELDNAMES})
            row.update(
                {
                    "bounded_subset_execution": True,
                    "target_subset_episode_count": len(workload_rows),
                    "target_subset_spec_count": len({str(item["task_source_id"]) for item in workload_rows}),
                    "role_semantics_actor_visible": False,
                    "hidden_oracle_actor_input_required": False,
                    "diagnostic_only_no_verdict": True,
                    "success_rate_verdict_claim_made": False,
                    "comparison_delta_verdict_claim_made": False,
                    "claim_boundary": CLAIM_SCOPE,
                }
            )
            append_csv_row(output / "episode_rows.csv", row)
            recorded.add(workload_id)
        except Exception as exc:  # noqa: BLE001 - failed cells must be recorded, not dropped.
            failure_row = {
                **{key: workload_row.get(key, "") for key in SUBSET_METADATA_FIELDNAMES},
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "bounded_subset_execution": True,
                "training_started": False,
                "replay_started": False,
                "ppo_used": False,
                "promoted": False,
                "private_holdout_used": False,
                "profile_specific_tuning": False,
                "controller_family_ranking_claim_made": False,
                "paper_level_claim_made": False,
                "level3_self_id_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
            append_csv_row(output / "failure_rows.csv", failure_row)
            recorded.add(workload_id)
        write_run_state(
            output / "run_state.json",
            {
                "target_workload_count": len(workload_rows),
                "completed_count": len(read_csv_rows(output / "episode_rows.csv")),
                "failure_count": len(read_csv_rows(output / "failure_rows.csv")),
                "accounted_count": len(_recorded_workload_ids(output)),
                "latest_workload_id": workload_id,
                "complete": False,
            },
        )

    return finalize_subset_outputs(
        output_dir=output,
        subset_rows=subset_rows,
        target_workload_count=len(workload_rows),
        next_blocker=next_blocker,
    )


def finalize_subset_outputs(
    *,
    output_dir: Path,
    subset_rows: list[dict[str, str]],
    target_workload_count: int,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    episode_rows = [dict(row) for row in read_csv_rows(output_dir / "episode_rows.csv")]
    failure_rows = [dict(row) for row in read_csv_rows(output_dir / "failure_rows.csv")]
    if not (output_dir / "failure_rows.csv").exists():
        write_csv_rows(output_dir / "failure_rows.csv", failure_rows, fieldnames=FAILURE_FIELDNAMES)

    profile_aggregate = aggregate_rows(episode_rows, "profile_name") if episode_rows else []
    spec_aggregate = aggregate_rows(episode_rows, "task_source_id") if episode_rows else []
    candidate_aggregate = aggregate_rows(episode_rows, "candidate_id") if episode_rows else []
    source_edge_aggregate = aggregate_rows(episode_rows, "source_edge") if episode_rows else []
    role_semantics_aggregate = aggregate_rows(episode_rows, "role_semantics_proxy") if episode_rows else []
    outcome_aggregate = (
        aggregate_rows(episode_rows, "outcome_bucket")
        if episode_rows and "outcome_bucket" in episode_rows[0]
        else []
    )
    termination_reason_aggregate = (
        aggregate_rows(episode_rows, "termination_reason")
        if episode_rows and "termination_reason" in episode_rows[0]
        else []
    )

    write_csv_rows(output_dir / "profile_aggregate.csv", profile_aggregate)
    write_csv_rows(output_dir / "spec_aggregate.csv", spec_aggregate)
    write_csv_rows(output_dir / "candidate_aggregate.csv", candidate_aggregate)
    write_csv_rows(output_dir / "source_edge_aggregate.csv", source_edge_aggregate)
    write_csv_rows(output_dir / "role_semantics_aggregate.csv", role_semantics_aggregate)
    write_csv_rows(output_dir / "outcome_aggregate.csv", outcome_aggregate)
    write_csv_rows(output_dir / "termination_reason_aggregate.csv", termination_reason_aggregate)

    subset_validation = validate_subset_rows(subset_rows)
    guardrail_flags = {
        "training_started": any(_bool(row.get("training_started", False)) for row in episode_rows),
        "replay_started": any(_bool(row.get("replay_started", False)) for row in episode_rows),
        "ppo_used": any(_bool(row.get("ppo_used", False)) for row in episode_rows),
        "promoted": any(_bool(row.get("promoted", False)) for row in episode_rows),
        "private_holdout_used": any(_bool(row.get("private_holdout_used", False)) for row in episode_rows),
        "actor_input_contract_changed": any(_bool(row.get("actor_input_contract_changed", False)) for row in episode_rows)
        or subset_validation["actor_input_contract_changed"],
        "role_semantics_actor_visible": any(_bool(row.get("role_semantics_actor_visible", False)) for row in episode_rows)
        or subset_validation["role_semantics_actor_visible"],
        "hidden_oracle_actor_input_required": any(
            _bool(row.get("hidden_oracle_actor_input_required", False)) for row in episode_rows
        )
        or subset_validation["hidden_oracle_actor_input_required"],
        "profile_specific_tuning": any(_bool(row.get("profile_specific_tuning", False)) for row in episode_rows),
        "controller_family_ranking_claim_made": any(
            _bool(row.get("controller_family_ranking_claim_made", False)) for row in episode_rows
        ),
        "paper_level_claim_made": any(_bool(row.get("paper_level_claim_made", False)) for row in episode_rows),
        "level3_self_id_claim_made": any(_bool(row.get("level3_self_id_claim_made", False)) for row in episode_rows),
        "success_rate_verdict_claim_made": any(
            _bool(row.get("success_rate_verdict_claim_made", False)) for row in episode_rows
        ),
        "comparison_delta_verdict_claim_made": any(
            _bool(row.get("comparison_delta_verdict_claim_made", False)) for row in episode_rows
        ),
        "full_public_matrix_expanded": subset_validation["is_full_public_matrix"],
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    all_selected_metrics_finite = selected_metrics_are_finite(episode_rows) if episode_rows else False
    accounted_count = len({row.get("workload_id", "") for row in episode_rows + failure_rows if row.get("workload_id")})
    result_pass = bool(
        len(episode_rows) == target_workload_count
        and accounted_count == target_workload_count
        and not failure_rows
        and all_selected_metrics_finite
        and guardrail_violation_count == 0
        and subset_validation["subset_row_count"] == TARGET_SUBSET_EPISODE_COUNT
        and subset_validation["unique_task_source_count"] == TARGET_SUBSET_SPEC_COUNT
        and subset_validation["unique_profile_count"] == TARGET_PROFILE_COUNT
        and subset_validation["duplicate_workload_count"] == 0
    )
    summary = {
        "result_class": (
            "controller_family_role_semantics_bounded_subset_rollout_execution_pass"
            if result_pass
            else "controller_family_role_semantics_bounded_subset_rollout_execution_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "episode_count": len(episode_rows),
        "target_episode_count": target_workload_count,
        "accounted_cell_count": accounted_count,
        "profile_count": len({row["profile_name"] for row in episode_rows}) if episode_rows else 0,
        "target_profile_count": TARGET_PROFILE_COUNT,
        "spec_count": len({row["task_source_id"] for row in episode_rows}) if episode_rows else 0,
        "target_spec_count": subset_validation["unique_task_source_count"],
        "candidate_count": len({row["candidate_id"] for row in episode_rows}) if episode_rows else 0,
        "target_candidate_count": subset_validation["candidate_count"],
        "source_edge_count": len({row["source_edge"] for row in episode_rows}) if episode_rows else 0,
        "role_semantics_count": len({row["role_semantics_proxy"] for row in episode_rows}) if episode_rows else 0,
        "failure_count": len(failure_rows),
        "all_selected_metrics_finite": bool(all_selected_metrics_finite),
        "profile_aggregate_rows": len(profile_aggregate),
        "spec_aggregate_rows": len(spec_aggregate),
        "candidate_aggregate_rows": len(candidate_aggregate),
        "source_edge_aggregate_rows": len(source_edge_aggregate),
        "role_semantics_aggregate_rows": len(role_semantics_aggregate),
        "outcome_aggregate_rows": len(outcome_aggregate),
        "termination_reason_aggregate_rows": len(termination_reason_aggregate),
        "subset_validation": subset_validation,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_rollout_started": bool(episode_rows or failure_rows),
        "bounded_subset_execution": True,
        "full_public_matrix_expanded": subset_validation["is_full_public_matrix"],
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "role_semantics_actor_visible": False,
        "hidden_oracle_actor_input_required": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "success_rate_verdict_claim_made": False,
        "comparison_delta_verdict_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": {
            "summary": str(output_dir / "summary.json"),
            "episode_rows": str(output_dir / "episode_rows.csv"),
            "profile_aggregate": str(output_dir / "profile_aggregate.csv"),
            "spec_aggregate": str(output_dir / "spec_aggregate.csv"),
            "candidate_aggregate": str(output_dir / "candidate_aggregate.csv"),
            "source_edge_aggregate": str(output_dir / "source_edge_aggregate.csv"),
            "role_semantics_aggregate": str(output_dir / "role_semantics_aggregate.csv"),
            "outcome_aggregate": str(output_dir / "outcome_aggregate.csv"),
            "termination_reason_aggregate": str(output_dir / "termination_reason_aggregate.csv"),
            "failure_rows": str(output_dir / "failure_rows.csv"),
            "run_state": str(output_dir / "run_state.json"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output_dir / "summary.json", summary)
    write_run_state(
        output_dir / "run_state.json",
        {
            "target_workload_count": target_workload_count,
            "completed_count": len(episode_rows),
            "failure_count": len(failure_rows),
            "accounted_count": accounted_count,
            "complete": accounted_count == target_workload_count,
            "status_pass": result_pass,
        },
    )
    return summary


def build_runtime_enforcement_join_rows(
    *,
    runtime_rows: list[dict[str, Any]],
    subset_rows: list[dict[str, Any]],
    episode_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    runtime_by_profile = {str(row.get("runtime_profile_name", "")): row for row in runtime_rows}
    target_count_by_profile = Counter(str(row.get("profile_name", "")) for row in subset_rows)
    target_spec_by_profile: dict[str, set[str]] = {}
    for row in subset_rows:
        target_spec_by_profile.setdefault(str(row.get("profile_name", "")), set()).add(str(row.get("task_source_id", "")))
    episode_count_by_profile = Counter(str(row.get("profile_name", "")) for row in episode_rows)
    failure_count_by_profile = Counter(str(row.get("profile_name", "")) for row in failure_rows)
    executed_spec_by_profile: dict[str, set[str]] = {}
    for row in episode_rows:
        executed_spec_by_profile.setdefault(str(row.get("profile_name", "")), set()).add(str(row.get("task_source_id", "")))

    rows: list[dict[str, Any]] = []
    for profile_name in EXPECTED_PROFILE_NAMES:
        runtime = dict(runtime_by_profile.get(profile_name, {}))
        row: dict[str, Any] = {
            "protocol_controller_family_id": runtime.get("protocol_controller_family_id", ""),
            "runtime_profile_name": runtime.get("runtime_profile_name", profile_name),
            "executed_profile_name": profile_name,
            "target_subset_cell_count": int(target_count_by_profile.get(profile_name, 0)),
            "target_subset_spec_count": len(target_spec_by_profile.get(profile_name, set())),
            "executed_episode_count": int(episode_count_by_profile.get(profile_name, 0)),
            "executed_spec_count": len(executed_spec_by_profile.get(profile_name, set())),
            "failed_cell_count": int(failure_count_by_profile.get(profile_name, 0)),
            "accounted_cell_count": int(episode_count_by_profile.get(profile_name, 0))
            + int(failure_count_by_profile.get(profile_name, 0)),
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
            "bounded_subset_policy_rollout_run": True,
            "policy_rollout_allowed": True,
            "training_started": _bool(runtime.get("training_started", False)),
            "ppo_used": _bool(runtime.get("ppo_used", False)),
            "replay_started": False,
            "profile_specific_tuning": False,
            "role_semantics_actor_visible": False,
            "success_rate_metric_recorded": True,
            "comparison_delta_metric_recorded": False,
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
    if int(row["target_subset_cell_count"]) != TARGET_SUBSET_SPEC_COUNT:
        return False
    if int(row["target_subset_spec_count"]) != TARGET_SUBSET_SPEC_COUNT:
        return False
    if int(row["executed_episode_count"]) != int(row["target_subset_cell_count"]):
        return False
    if int(row["executed_spec_count"]) != int(row["target_subset_spec_count"]):
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
    if _bool(row["success_rate_verdict_claim_made"]) or _bool(row["role_semantics_actor_visible"]):
        return False
    if not _bool(row["bounded_subset_policy_rollout_run"]) or not _bool(row["policy_rollout_allowed"]):
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
        claim("bounded_subset_execution_preflight", "execution", True, True, "M2684 summary and subset execution artifacts"),
        claim("episode_rows_materialized", "artifact", True, artifacts_present, "episode_rows.csv"),
        claim("profile_aggregate_materialized", "artifact", True, artifacts_present, "profile_aggregate.csv"),
        claim("spec_aggregate_materialized", "artifact", True, artifacts_present, "spec_aggregate.csv"),
        claim("candidate_aggregate_materialized", "artifact", True, artifacts_present, "candidate_aggregate.csv"),
        claim("source_edge_aggregate_materialized", "artifact", True, artifacts_present, "source_edge_aggregate.csv"),
        claim("role_semantics_aggregate_materialized", "artifact", True, artifacts_present, "role_semantics_aggregate.csv"),
        claim("outcome_aggregate_materialized", "artifact", True, artifacts_present, "outcome_aggregate.csv"),
        claim(
            "termination_reason_aggregate_materialized",
            "artifact",
            True,
            artifacts_present,
            "termination_reason_aggregate.csv",
        ),
        claim("runtime_enforcement_join_rows_materialized", "artifact", True, artifacts_present, "runtime_enforcement_join_rows.csv"),
        claim("claim_boundary_rows_materialized", "artifact", True, artifacts_present, "claim_boundary_rows.csv"),
        claim("gate_matrix_materialized", "artifact", True, artifacts_present, "gate_matrix.csv"),
        claim("failure_rows_materialized", "artifact", True, artifacts_present, "failure_rows.csv"),
        claim("run_state_materialized", "artifact", True, artifacts_present, "run_state.json"),
        claim("diagnostic_success_rate_metric_recorded", "diagnostic_metric", True, True, "diagnostic aggregate rows only, not verdict"),
        claim(
            "diagnostic_role_task_quality_metrics_recorded",
            "diagnostic_metric",
            True,
            True,
            "candidate/source-edge/role aggregates only, not actor input or verdict",
        ),
        claim("follow_up_audit_registered", "follow_up_route", True, follow_up_manifest_registered, "M2685 result-audit manifest"),
    ]
    blocked = [
        ("training_or_ppo", "execution", "future training manifest"),
        ("replay_execution", "execution", "future replay manifest"),
        ("private_holdout_tuning", "holdout_policy", "forbidden in Route B subset execution preflight"),
        ("profile_specific_tuning", "objective_overfit", "future controlled tuning protocol"),
        ("actor_visible_role_semantics", "actor_contract", "forbidden in M2684 actor input"),
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
    subset_summary: dict[str, Any],
    artifact_rows: dict[str, list[dict[str, Any]]],
    subset_rows: list[dict[str, Any]],
    runtime_join_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    episode_rows = artifact_rows["episode_rows"]
    failure_rows = artifact_rows["failure_rows"]
    profile_aggregate_rows = artifact_rows["profile_aggregate_rows"]
    spec_aggregate_rows = artifact_rows["spec_aggregate_rows"]
    candidate_aggregate_rows = artifact_rows["candidate_aggregate_rows"]
    source_edge_aggregate_rows = artifact_rows["source_edge_aggregate_rows"]
    role_semantics_aggregate_rows = artifact_rows["role_semantics_aggregate_rows"]
    outcome_aggregate_rows = artifact_rows["outcome_aggregate_rows"]
    termination_reason_aggregate_rows = artifact_rows["termination_reason_aggregate_rows"]
    subset_validation = validate_subset_rows(subset_rows)
    accounted_count = len({row.get("workload_id", "") for row in episode_rows + failure_rows if row.get("workload_id")})
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
    allowed_claim_rows = [row for row in claim_rows if _bool(row["allowed_in_m2684"])]
    blocked_claim_rows = [row for row in claim_rows if not _bool(row["allowed_in_m2684"])]
    return [
        gate("source_artifacts_present", "lineage", all(source["source_exists"].values()), source["source_exists"], "all M2682/M2683/M2673/M1690/M1674 source artifacts and M2685 follow-up manifest present", "lineage_invalid"),
        gate("m2682_status_pass", "lineage", _bool(source["m2682_summary"].get("status_pass", False)), source["m2682_summary"].get("status_pass", None), True, "lineage_invalid"),
        gate("m2673_status_pass", "lineage", _bool(source["m2673_summary"].get("status_pass", False)), source["m2673_summary"].get("status_pass", None), True, "lineage_invalid"),
        gate("m1690_workload_materialization_pass", "lineage", _bool(source["m1690_summary"].get("passes_public_smoke_gates", False)), source["m1690_summary"].get("result_class", ""), "controller_family_executable_workload_materialization_preflight_pass", "lineage_invalid"),
        gate("m2682_subset_rows_complete", "subset", subset_validation["subset_row_count"] == TARGET_SUBSET_EPISODE_COUNT and subset_validation["unique_workload_count"] == TARGET_SUBSET_EPISODE_COUNT, subset_validation, "216 unique subset workload rows", "metric_artifact"),
        gate("m2682_subset_not_full_matrix", "subset", not subset_validation["is_full_public_matrix"] and subset_validation["subset_row_count"] < FULL_PUBLIC_MATRIX_COUNT, subset_validation["subset_row_count"], f"< {FULL_PUBLIC_MATRIX_COUNT}", "objective_overfit"),
        gate("m2682_subset_profile_spec_coverage", "subset", subset_validation["unique_profile_count"] == TARGET_PROFILE_COUNT and subset_validation["unique_task_source_count"] == TARGET_SUBSET_SPEC_COUNT, f"profiles={subset_validation['unique_profile_count']} specs={subset_validation['unique_task_source_count']}", f"profiles={TARGET_PROFILE_COUNT} specs={TARGET_SUBSET_SPEC_COUNT}", "metric_artifact"),
        gate("role_semantics_analysis_only", "actor_contract", not subset_validation["role_semantics_actor_visible"] and not subset_validation["hidden_oracle_actor_input_required"] and not subset_validation["actor_input_contract_changed"], subset_validation, "role semantics actor invisible and no hidden/oracle actor input", "contract_violation"),
        gate("subset_rollout_runner_pass", "execution", subset_summary.get("result_class") == "controller_family_role_semantics_bounded_subset_rollout_execution_pass", subset_summary.get("result_class", ""), "controller_family_role_semantics_bounded_subset_rollout_execution_pass", "behavior_regression"),
        gate("subset_cells_accounted", "execution", accounted_count == TARGET_SUBSET_EPISODE_COUNT, accounted_count, TARGET_SUBSET_EPISODE_COUNT, "metric_artifact"),
        gate("episode_rows_complete", "execution", len(episode_rows) == TARGET_SUBSET_EPISODE_COUNT, len(episode_rows), TARGET_SUBSET_EPISODE_COUNT, "behavior_regression"),
        gate("failure_rows_empty", "execution", len(failure_rows) == 0 and int(subset_summary.get("failure_count", -1)) == 0, f"failure_rows={len(failure_rows)} summary={subset_summary.get('failure_count')}", "failure_rows=0 summary=0", "behavior_regression"),
        gate("profile_aggregate_complete", "artifact", len(profile_aggregate_rows) == TARGET_PROFILE_COUNT, len(profile_aggregate_rows), TARGET_PROFILE_COUNT, "metric_artifact"),
        gate("spec_aggregate_complete", "artifact", len(spec_aggregate_rows) == TARGET_SUBSET_SPEC_COUNT, len(spec_aggregate_rows), TARGET_SUBSET_SPEC_COUNT, "metric_artifact"),
        gate("candidate_aggregate_complete", "artifact", len(candidate_aggregate_rows) == subset_validation["candidate_count"] and subset_validation["candidate_count"] > 0, len(candidate_aggregate_rows), subset_validation["candidate_count"], "metric_artifact"),
        gate("source_edge_aggregate_present", "artifact", len(source_edge_aggregate_rows) > 0, len(source_edge_aggregate_rows), ">0", "metric_artifact"),
        gate("role_semantics_aggregate_present", "artifact", len(role_semantics_aggregate_rows) > 0, len(role_semantics_aggregate_rows), ">0", "metric_artifact"),
        gate("outcome_and_termination_aggregates_present", "artifact", bool(outcome_aggregate_rows and termination_reason_aggregate_rows), f"outcome={len(outcome_aggregate_rows)} termination={len(termination_reason_aggregate_rows)}", "both present", "metric_artifact"),
        gate("all_selected_metrics_finite", "metric", _all_selected_metrics_finite(subset_summary, profile_aggregate_rows, spec_aggregate_rows), subset_summary.get("all_selected_metrics_finite", None), True, "metric_artifact"),
        gate("runtime_join_rows_cover_profiles", "runtime_join", len(runtime_join_rows) == TARGET_PROFILE_COUNT and all(_bool(row["runtime_join_status_pass"]) for row in runtime_join_rows), f"rows={len(runtime_join_rows)} pass={sum(_bool(row['runtime_join_status_pass']) for row in runtime_join_rows)}", f"rows={TARGET_PROFILE_COUNT} pass={TARGET_PROFILE_COUNT}", "metric_artifact"),
        gate("required_protocol_ids_joined", "runtime_join", REQUIRED_CONTROLLER_IDS.issubset(protocol_ids) and REQUIRED_CONTROLLER_IDS.issubset(mapped_ids), sorted(mapped_ids), sorted(REQUIRED_CONTROLLER_IDS), "metric_artifact"),
        gate("current_tiled_runtime_observed", "runtime_join", len(current_tiled_rows) == 4 and all(_bool(row["current_tiled_runtime_observed"]) for row in current_tiled_rows), [row["runtime_profile_name"] for row in current_tiled_rows], "4 current-tiled runtime profiles observed", "metric_artifact"),
        gate("reset_truncated_policy_routing_ok", "runtime_join", len(reset_rows) == 1 and all(_bool(row["reset_policy_routing_ok"]) for row in reset_rows), [row.get("reset_hidden_policy", "") for row in reset_rows], ["every_step_control"], "metric_artifact"),
        gate("actor_action_contract_preserved", "actor_contract", all(_bool(row["actor_contract_shape_72_action_3"]) for row in runtime_join_rows) and not any(_bool(row["hidden_oracle_actor_input_detected"]) for row in runtime_join_rows), "all runtime-joined profiles preserve P0/action3/no-oracle boundary", "all runtime-joined profiles preserve P0/action3/no-oracle boundary", "contract_violation"),
        gate("no_private_holdout_or_profile_tuning", "holdout_policy", not any(_bool(row["private_holdout_used"]) or _bool(row["profile_specific_tuning"]) for row in runtime_join_rows), "all false", "all false", "objective_overfit"),
        gate("no_training_ppo_replay", "execution_guardrail", not any(_bool(row["training_started"]) or _bool(row["ppo_used"]) or _bool(row["replay_started"]) for row in runtime_join_rows), "all false", "all false", "objective_overfit"),
        gate("bounded_subset_execution_only", "execution_guardrail", _episode_rows_are_bounded_subset_only(episode_rows), "M2682 subset policy actions recorded", "M2682 subset policy actions recorded only", "scenario_sampling_failure"),
        gate("claim_boundary_blocks_overclaim", "claim_boundary", len(allowed_claim_rows) == 17 and all(_bool(row["status_pass"]) for row in allowed_claim_rows) and all(not _bool(row["claim_made"]) and _bool(row["status_pass"]) for row in blocked_claim_rows), f"allowed={len(allowed_claim_rows)} blocked={len(blocked_claim_rows)}", "allowed=17 blocked=20", "proof_washout"),
        gate("success_and_role_metrics_not_verdicts", "claim_boundary", any(row["claim_id"] == "diagnostic_success_rate_metric_recorded" for row in allowed_claim_rows) and any(row["claim_id"] == "diagnostic_role_task_quality_metrics_recorded" for row in allowed_claim_rows) and any(row["claim_id"] == "success_rate_verdict" for row in blocked_claim_rows) and any(row["claim_id"] == "actor_visible_role_semantics" for row in blocked_claim_rows), "diagnostic metrics present; verdict and actor-visible role claims blocked", "diagnostic metrics present; verdict and actor-visible role claims blocked", "proof_washout"),
        gate("required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True, "lineage_invalid"),
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    subset_summary: dict[str, Any],
    artifact_rows: dict[str, list[dict[str, Any]]],
    subset_rows: list[dict[str, Any]],
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
    subset_validation = validate_subset_rows(subset_rows)
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
    allowed_claim_rows = [row for row in claim_rows if _bool(row["allowed_in_m2684"])]
    blocked_claim_rows = [row for row in claim_rows if not _bool(row["allowed_in_m2684"])]
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    episode_rows = artifact_rows["episode_rows"]
    failure_rows = artifact_rows["failure_rows"]
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight_pass"
            if status_pass
            else "paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight_fail"
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
        "m2682_status_pass": _bool(source["m2682_summary"].get("status_pass", False)),
        "m2673_status_pass": _bool(source["m2673_summary"].get("status_pass", False)),
        "m1690_status_pass": _bool(source["m1690_summary"].get("passes_public_smoke_gates", False)),
        "subset_runner_result_class": subset_summary.get("result_class", ""),
        "subset_runner_pass": subset_summary.get("result_class")
        == "controller_family_role_semantics_bounded_subset_rollout_execution_pass",
        "episode_count": len(episode_rows),
        "target_episode_count": TARGET_SUBSET_EPISODE_COUNT,
        "accounted_cell_count": len({row.get("workload_id", "") for row in episode_rows + failure_rows if row.get("workload_id")}),
        "profile_count": len({str(row.get("profile_name", "")) for row in episode_rows}),
        "target_profile_count": TARGET_PROFILE_COUNT,
        "spec_count": len({str(row.get("task_source_id", "")) for row in episode_rows}),
        "target_spec_count": TARGET_SUBSET_SPEC_COUNT,
        "candidate_count": len({str(row.get("candidate_id", "")) for row in episode_rows}),
        "target_candidate_count": subset_validation["candidate_count"],
        "source_edge_count": len({str(row.get("source_edge", "")) for row in episode_rows}),
        "role_semantics_count": len({str(row.get("role_semantics_proxy", "")) for row in episode_rows}),
        "subset_row_count": subset_validation["subset_row_count"],
        "subset_unique_workload_count": subset_validation["unique_workload_count"],
        "subset_unique_task_source_count": subset_validation["unique_task_source_count"],
        "subset_unique_profile_count": subset_validation["unique_profile_count"],
        "subset_is_full_public_matrix": subset_validation["is_full_public_matrix"],
        "failure_count": len(failure_rows),
        "all_selected_metrics_finite": _all_selected_metrics_finite(
            subset_summary,
            artifact_rows["profile_aggregate_rows"],
            artifact_rows["spec_aggregate_rows"],
        ),
        "profile_aggregate_rows": len(artifact_rows["profile_aggregate_rows"]),
        "spec_aggregate_rows": len(artifact_rows["spec_aggregate_rows"]),
        "candidate_aggregate_rows": len(artifact_rows["candidate_aggregate_rows"]),
        "source_edge_aggregate_rows": len(artifact_rows["source_edge_aggregate_rows"]),
        "role_semantics_aggregate_rows": len(artifact_rows["role_semantics_aggregate_rows"]),
        "outcome_aggregate_rows": len(artifact_rows["outcome_aggregate_rows"]),
        "termination_reason_aggregate_rows": len(artifact_rows["termination_reason_aggregate_rows"]),
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
        "bounded_subset_policy_rollout_run": True,
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
        "role_semantics_actor_visible": False,
        "controller_family_labels_actor_visible": False,
        "taxonomy_or_route_labels_actor_visible": False,
        "ranking_run": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "success_rate_metric_recorded": True,
        "diagnostic_role_task_quality_metrics_recorded": True,
        "comparison_delta_metric_recorded": False,
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
            "# M2684 Paper Route History Vs Current Response Task Quality Role Semantics Bounded Subset Execution Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result_class: `{summary['result_class']}`",
            f"- generated_at_utc: `{summary['generated_at_utc']}`",
            f"- manifest: `experiments/manifests/{DEFAULT_MILESTONE}.json`",
            f"- summary: `{summary['paths']['summary']}`",
            f"- subset rollout runner summary: `{summary['paths']['subset_rollout_execution_summary']}`",
            f"- episode rows: `{summary['paths']['episode_rows']}`",
            f"- profile aggregate: `{summary['paths']['profile_aggregate']}`",
            f"- spec aggregate: `{summary['paths']['spec_aggregate']}`",
            f"- candidate aggregate: `{summary['paths']['candidate_aggregate']}`",
            f"- source-edge aggregate: `{summary['paths']['source_edge_aggregate']}`",
            f"- role-semantics aggregate: `{summary['paths']['role_semantics_aggregate']}`",
            f"- outcome aggregate: `{summary['paths']['outcome_aggregate']}`",
            f"- termination aggregate: `{summary['paths']['termination_reason_aggregate']}`",
            f"- runtime-enforcement join rows: `{summary['paths']['runtime_enforcement_join_rows']}`",
            f"- claim boundary rows: `{summary['paths']['claim_boundary_rows']}`",
            f"- gate matrix: `{summary['paths']['gate_matrix']}`",
            f"- failure rows: `{summary['paths']['failure_rows']}`",
            f"- run state: `{summary['paths']['run_state']}`",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            f"- next: `{summary['next_blocker']}`",
            "",
            "## Bounded Execution",
            "",
            f"- episode rows: {summary['episode_count']} / {summary['target_episode_count']}",
            f"- accounted cells: {summary['accounted_cell_count']} / {summary['target_episode_count']}",
            f"- profiles executed: {summary['profile_count']} / {summary['target_profile_count']}",
            f"- subset specs executed: {summary['spec_count']} / {summary['target_spec_count']}",
            f"- candidates executed: {summary['candidate_count']} / {summary['target_candidate_count']}",
            f"- source-edge aggregate rows: {summary['source_edge_aggregate_rows']}",
            f"- role-semantics aggregate rows: {summary['role_semantics_aggregate_rows']}",
            f"- failure rows: {summary['failure_count']}",
            f"- selected metrics finite: {summary['all_selected_metrics_finite']}",
            f"- subset full public matrix expanded: {summary['subset_is_full_public_matrix']}",
            "",
            "## Runtime Join",
            "",
            f"- M2682 status pass: {summary['m2682_status_pass']}",
            f"- M2673 status pass: {summary['m2673_status_pass']}",
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
            f"- bounded subset policy rollout run: {summary['bounded_subset_policy_rollout_run']}",
            f"- policy rollout allowed: {summary['policy_rollout_allowed']}",
            f"- measured validation run: {summary['measured_validation_run']}",
            f"- training run: {summary['training_run']}",
            f"- replay run: {summary['replay_run']}",
            f"- ppo run: {summary['ppo_run']}",
            f"- private holdout used: {summary['private_holdout_used']}",
            f"- profile-specific tuning: {summary['profile_specific_tuning']}",
            f"- actor/action boundary: P0 observation multiple action 3 preserved: {summary['actor_contract_shape_72_action_3']}",
            f"- hidden/oracle actor input detected: {summary['hidden_oracle_actor_input_detected']}",
            f"- role semantics actor visible: {summary['role_semantics_actor_visible']}",
            f"- diagnostic success-rate metric recorded: {summary['success_rate_metric_recorded']}",
            f"- diagnostic role/task-quality metrics recorded: {summary['diagnostic_role_task_quality_metrics_recorded']}",
            f"- success-rate verdict claim made: {summary['success_rate_verdict_claim_made']}",
            f"- comparison-delta verdict claim made: {summary['comparison_delta_verdict_claim_made']}",
            "",
            "## Claim Boundary",
            "",
            "Allowed:",
            "",
            "```text",
            "M2682 bounded subset execution preflight data and diagnostic role/task-quality metrics only.",
            "```",
            "",
            "Rejected:",
            "",
            "```text",
            summary["forbidden_interpretation"],
            "```",
            "",
            "M2684 executes only the M2682 proposed subset for diagnostic",
            "closed-loop rows. The success-rate and role/task-quality aggregate",
            "columns are not rankings, controller-family verdicts, paper",
            "evidence, finite-window-vs-GRU conclusions, current-response",
            "sufficiency results, current-sim verdicts, high-fidelity",
            "validation, full ideal driver completion, or level3 self-ID",
            "evidence.",
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
        "allowed_in_m2684": bool(allowed),
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
    subset_summary: dict[str, Any],
    profile_aggregate_rows: list[dict[str, Any]],
    spec_aggregate_rows: list[dict[str, Any]],
) -> bool:
    if not _bool(subset_summary.get("all_selected_metrics_finite", False)):
        return False
    return all(
        _bool(row.get("all_selected_metrics_finite", False))
        for row in list(profile_aggregate_rows) + list(spec_aggregate_rows)
    )


def _episode_rows_are_bounded_subset_only(rows: list[dict[str, Any]]) -> bool:
    if len(rows) != TARGET_SUBSET_EPISODE_COUNT:
        return False
    for row in rows:
        if not _bool(row.get("bounded_subset_execution", False)):
            return False
        if _bool(row.get("training_started", False)) or _bool(row.get("ppo_used", False)):
            return False
        if _bool(row.get("replay_started", False)) or _bool(row.get("private_holdout_used", False)):
            return False
        if _bool(row.get("actor_input_contract_changed", False)):
            return False
        if _bool(row.get("role_semantics_actor_visible", False)):
            return False
        if _bool(row.get("hidden_oracle_actor_input_required", False)):
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
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2682-dir", type=Path, default=DEFAULT_M2682_DIR)
    parser.add_argument("--runtime-enforcement-dir", type=Path, default=DEFAULT_RUNTIME_ENFORCEMENT_DIR)
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

    summary = run_bounded_subset_execution_preflight(
        m2682_dir=args.m2682_dir,
        runtime_enforcement_dir=args.runtime_enforcement_dir,
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
