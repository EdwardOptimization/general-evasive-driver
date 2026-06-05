"""Run bounded repair execution for M2725 offtrack candidate rows.

M2728 consumes the accepted M2725 candidate materialization after M2727
execution design. It may reset, step, and run policy actions only for the 31
M2725 offtrack candidate rows, using temporary run-directory overlay snapshots.
The output is diagnostic repair preflight evidence only: no validation,
ranking, promotion, driver-performance, paper, current-sim, high-fidelity,
full-driver, or self-ID claim is made.
"""

from __future__ import annotations

import argparse
import copy
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
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
    "m2728-engineering-controller-route-a-current-m1690-exact-executable-reentry-"
    "offtrack-repair-bounded-execution-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2729-engineering-controller-route-a-current-m1690-exact-executable-reentry-"
    "offtrack-repair-bounded-execution-result-audit"
)
DEFAULT_M2725_DIR = Path(
    "runs/m2725_engineering_controller_route_a_current_m1690_exact_executable_reentry_"
    "offtrack_repair_candidate_materialization"
)
DEFAULT_M2727_DESIGN = Path(
    "docs/m2727-engineering-controller-route-a-current-m1690-exact-executable-reentry-"
    "offtrack-repair-bounded-execution-design.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2728_engineering_controller_route_a_current_m1690_exact_executable_reentry_"
    "offtrack_repair_bounded_execution_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2728-engineering-controller-route-a-current-m1690-exact-executable-reentry-"
    "offtrack-repair-bounded-execution-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/"
    "m2729-engineering-controller-route-a-current-m1690-exact-executable-reentry-"
    "offtrack-repair-bounded-execution-result-audit.json"
)
DEFAULT_EVAL_SEED_BASE = 272800
EXPECTED_CANDIDATE_COUNT = 31
EXPECTED_OVERLAY_ROW_COUNT = 15
EXPECTED_GUARDRAIL_ROW_COUNT = 17

CLAIM_SCOPE = (
    "M2728 Route A current-M1690 exact-executable reentry offtrack repair "
    "bounded execution preflight only; reset, step, rollout, and policy actions "
    "may be recorded for the 31 M2725 candidate target rows under temporary "
    "run-dir overlay snapshots, but no replay, validation, training, PPO, "
    "private holdout, active config overwrite, profile-specific tuning, "
    "ranking, winner selection, promotion, success-rate verdict, repair-success, "
    "driver-performance, paper, finite-window-vs-GRU, current-response, "
    "current-sim, high-fidelity validation, full ideal driver, or self-ID claim "
    "is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair success, driver performance, validation readiness or result, "
    "controller-family ranking, winner selection, checkpoint promotion, "
    "success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, "
    "current-response sufficiency, current-sim verdict, high-fidelity "
    "validation readiness or result, full ideal driver completion, or level3 "
    "self-identification"
)

FAILURE_FIELDNAMES = [
    "candidate_row_id",
    "source_panel_row_id",
    "source_candidate_id",
    "anchor_task_source_id",
    "workload_id",
    "task_source_id",
    "profile_name",
    "task_family",
    "error_type",
    "error_message",
    "eval_seed",
    "overlay_applied",
    "active_config_overwritten",
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
    "winner_selected",
    "protected_row_execution",
    "protected_rows_in_success_denominator",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "target_labels_actor_visible",
    "protected_labels_actor_visible",
    "profile_labels_actor_visible",
    "route_labels_actor_visible",
    "verdict_labels_actor_visible",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
OVERLAY_APPLICATION_FIELDNAMES = [
    "application_id",
    "candidate_row_id",
    "workload_id",
    "task_source_id",
    "profile_name",
    "overlay_row_id",
    "overlay_id",
    "overlay_family",
    "target_namespace",
    "target_key",
    "proposed_value",
    "applied_value",
    "application_mode",
    "config_snapshot_path",
    "preserves_parent_geometry",
    "active_config_overwritten",
    "profile_specific_tuning",
    "actor_input_change",
    "hidden_oracle_feature_injection",
    "claim_boundary",
]
GUARDRAIL_AUDIT_FIELDNAMES = [
    "audit_id",
    "guardrail_row_id",
    "guardrail_family",
    "source_panel_row_id",
    "source_candidate_id",
    "profile_name",
    "task_family",
    "taxonomy_family",
    "m2728_execution_candidate",
    "m2728_execution_run",
    "target_panel_admitted",
    "execution_scheduled",
    "protected_rows_in_success_denominator",
    "diagnostic_only_no_verdict",
    "actor_input_change",
    "hidden_oracle_feature_injection",
    "claim_boundary",
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
    "allowed_in_m2728",
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
    "repair_execution_rows",
    "candidate_execution_failure_rows",
    "profile_aggregate",
    "anchor_aggregate",
    "repair_overlay_application_rows",
    "guardrail_audit_rows",
    "actor_contract_join_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
]


def run_current_m1690_exact_executable_reentry_offtrack_repair_bounded_execution_preflight(
    *,
    m2725_dir: Path | str = DEFAULT_M2725_DIR,
    m2727_design: Path | str = DEFAULT_M2727_DESIGN,
    executable_specs: Path | str = DEFAULT_EXECUTABLE_SPECS,
    executable_workload: Path | str = DEFAULT_EXECUTABLE_WORKLOAD,
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
        m2725_dir=Path(m2725_dir),
        m2727_design=Path(m2727_design),
        executable_specs=Path(executable_specs),
        executable_workload=Path(executable_workload),
        follow_up_manifest=Path(follow_up_manifest),
    )
    execution_summary = run_candidate_repair_execution(
        m2725_dir=Path(m2725_dir),
        executable_specs_path=Path(executable_specs),
        executable_workload_path=Path(executable_workload),
        output_dir=output,
        eval_seed_base=int(eval_seed_base),
        device=device,
        resume=resume,
        next_blocker=next_blocker,
    )
    artifact_rows = load_execution_artifact_rows(paths)
    candidate_rows = source["candidate_target_rows"]
    overlay_rows = source["shared_repair_overlay_rows"]
    guardrail_rows = build_guardrail_audit_rows(source)
    profile_aggregate = build_aggregate_rows(
        candidate_rows=candidate_rows,
        episode_rows=artifact_rows["repair_execution_rows"],
        failure_rows=artifact_rows["candidate_execution_failure_rows"],
        group_key="profile_name",
        aggregate_family="profile",
    )
    anchor_aggregate = build_aggregate_rows(
        candidate_rows=candidate_rows,
        episode_rows=artifact_rows["repair_execution_rows"],
        failure_rows=artifact_rows["candidate_execution_failure_rows"],
        group_key="anchor_task_source_id",
        aggregate_family="anchor",
    )
    actor_join_rows = build_actor_contract_join_rows(source=source, artifact_rows=artifact_rows)
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=False,
        episode_or_failure_rows_present=bool(
            artifact_rows["repair_execution_rows"] or artifact_rows["candidate_execution_failure_rows"]
        ),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        execution_summary=execution_summary,
        artifact_rows=artifact_rows,
        candidate_rows=candidate_rows,
        overlay_rows=overlay_rows,
        guardrail_rows=guardrail_rows,
        profile_aggregate=profile_aggregate,
        anchor_aggregate=anchor_aggregate,
        actor_join_rows=actor_join_rows,
        claim_rows=claim_rows,
        required_artifacts_present=False,
    )
    write_csv_rows(paths["guardrail_audit_rows"], guardrail_rows, fieldnames=GUARDRAIL_AUDIT_FIELDNAMES)
    write_csv_rows(paths["profile_aggregate"], profile_aggregate, fieldnames=AGGREGATE_FIELDNAMES)
    write_csv_rows(paths["anchor_aggregate"], anchor_aggregate, fieldnames=AGGREGATE_FIELDNAMES)
    write_csv_rows(paths["actor_contract_join_rows"], actor_join_rows, fieldnames=ACTOR_JOIN_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    ensure_artifact_files(paths)
    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"})
    artifact_rows = load_execution_artifact_rows(paths)
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_artifacts_present,
        episode_or_failure_rows_present=bool(
            artifact_rows["repair_execution_rows"] or artifact_rows["candidate_execution_failure_rows"]
        ),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        execution_summary=execution_summary,
        artifact_rows=artifact_rows,
        candidate_rows=candidate_rows,
        overlay_rows=overlay_rows,
        guardrail_rows=guardrail_rows,
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
        artifact_rows=artifact_rows,
        candidate_rows=candidate_rows,
        overlay_rows=overlay_rows,
        guardrail_rows=guardrail_rows,
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
    gate_rows = build_gate_matrix_rows(
        source=source,
        execution_summary=execution_summary,
        artifact_rows=load_execution_artifact_rows(paths),
        candidate_rows=candidate_rows,
        overlay_rows=overlay_rows,
        guardrail_rows=guardrail_rows,
        profile_aggregate=profile_aggregate,
        anchor_aggregate=anchor_aggregate,
        actor_join_rows=actor_join_rows,
        claim_rows=claim_rows,
        required_artifacts_present=all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS),
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        execution_summary=execution_summary,
        artifact_rows=load_execution_artifact_rows(paths),
        candidate_rows=candidate_rows,
        overlay_rows=overlay_rows,
        guardrail_rows=guardrail_rows,
        profile_aggregate=profile_aggregate,
        anchor_aggregate=anchor_aggregate,
        actor_join_rows=actor_join_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS),
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
        "repair_execution_rows": output_dir / "repair_execution_rows.csv",
        "candidate_execution_failure_rows": output_dir / "candidate_execution_failure_rows.csv",
        "profile_aggregate": output_dir / "profile_aggregate.csv",
        "anchor_aggregate": output_dir / "anchor_aggregate.csv",
        "repair_overlay_application_rows": output_dir / "repair_overlay_application_rows.csv",
        "guardrail_audit_rows": output_dir / "guardrail_audit_rows.csv",
        "actor_contract_join_rows": output_dir / "actor_contract_join_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2725_dir: Path,
    m2727_design: Path,
    executable_specs: Path,
    executable_workload: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2727_design_doc": m2727_design,
        "m2725_summary": m2725_dir / "summary.json",
        "m2725_candidate_target_rows": m2725_dir / "candidate_target_rows.csv",
        "m2725_shared_repair_overlay_rows": m2725_dir / "shared_repair_overlay_rows.csv",
        "m2725_guardrail_rows": m2725_dir / "guardrail_rows.csv",
        "m2725_actor_contract_rows": m2725_dir / "actor_contract_rows.csv",
        "m2725_claim_boundary_rows": m2725_dir / "claim_boundary_rows.csv",
        "m2725_gate_matrix": m2725_dir / "gate_matrix.csv",
        "executable_task_specs": executable_specs,
        "executable_workload": executable_workload,
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2727_design_text": paths["m2727_design_doc"].read_text(encoding="utf-8")
        if source_exists["m2727_design_doc"]
        else "",
        "m2725_summary": read_json(paths["m2725_summary"]) if source_exists["m2725_summary"] else {},
        "candidate_target_rows": read_csv_rows(paths["m2725_candidate_target_rows"]),
        "shared_repair_overlay_rows": read_csv_rows(paths["m2725_shared_repair_overlay_rows"]),
        "guardrail_rows": read_csv_rows(paths["m2725_guardrail_rows"]),
        "actor_contract_rows": read_csv_rows(paths["m2725_actor_contract_rows"]),
        "claim_boundary_rows": read_csv_rows(paths["m2725_claim_boundary_rows"]),
        "gate_matrix": read_csv_rows(paths["m2725_gate_matrix"]),
    }


def load_execution_artifact_rows(paths: dict[str, Path]) -> dict[str, list[dict[str, str]]]:
    return {
        "repair_execution_rows": read_csv_rows(paths["repair_execution_rows"]),
        "candidate_execution_failure_rows": read_csv_rows(paths["candidate_execution_failure_rows"]),
        "repair_overlay_application_rows": read_csv_rows(paths["repair_overlay_application_rows"]),
        "guardrail_audit_rows": read_csv_rows(paths["guardrail_audit_rows"]),
        "profile_aggregate": read_csv_rows(paths["profile_aggregate"]),
        "anchor_aggregate": read_csv_rows(paths["anchor_aggregate"]),
    }


def run_candidate_repair_execution(
    *,
    m2725_dir: Path,
    executable_specs_path: Path,
    executable_workload_path: Path,
    output_dir: Path,
    eval_seed_base: int,
    device: str,
    resume: bool,
    next_blocker: str,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    if not resume:
        for name in (
            "repair_execution_rows.csv",
            "candidate_execution_failure_rows.csv",
            "repair_overlay_application_rows.csv",
            "profile_aggregate.csv",
            "anchor_aggregate.csv",
            "guardrail_audit_rows.csv",
            "actor_contract_join_rows.csv",
            "claim_boundary_rows.csv",
            "gate_matrix.csv",
            "summary.json",
            "run_state.json",
        ):
            path = output_dir / name
            if path.exists():
                path.unlink()

    candidate_rows = sorted(
        read_csv_rows(m2725_dir / "candidate_target_rows.csv"),
        key=lambda row: str(row.get("candidate_row_id", "")),
    )
    overlay_rows = sorted(
        read_csv_rows(m2725_dir / "shared_repair_overlay_rows.csv"),
        key=lambda row: str(row.get("overlay_row_id", "")),
    )
    specs = load_executable_specs(executable_specs_path)
    spec_by_id = {str(spec["task_source_id"]): spec for spec in specs}
    workload_rows = load_executable_workload(executable_workload_path)
    workload_by_id = {str(row["workload_id"]): row for row in workload_rows}
    if not (output_dir / "candidate_execution_failure_rows.csv").exists():
        write_csv_rows(output_dir / "candidate_execution_failure_rows.csv", [], fieldnames=FAILURE_FIELDNAMES)

    profile_cache: dict[tuple[str, str, str], tuple[dict[str, Any], Any, dict[str, str]]] = {}
    recorded = recorded_candidate_ids(output_dir)
    for index, candidate in enumerate(candidate_rows):
        candidate_id = str(candidate.get("candidate_row_id", ""))
        if candidate_id in recorded:
            continue
        eval_seed = int(eval_seed_base) + int(index)
        try:
            validate_candidate_row(candidate)
            workload_row = dict(workload_by_id[str(candidate["workload_id"])])
            validate_workload_join(candidate, workload_row)
            patched_spec, snapshot_path = patched_executable_spec_for_candidate(
                candidate=candidate,
                executable_spec=spec_by_id[str(candidate["task_source_id"])],
                overlay_rows=overlay_rows,
                output_dir=output_dir,
            )
            write_overlay_application_rows(
                output_dir=output_dir,
                candidate=candidate,
                overlay_rows=overlay_rows,
                snapshot_path=snapshot_path,
            )
            cache_key = (
                str(workload_row["profile_name"]),
                str(workload_row["profile_config_path"]),
                str(workload_row["checkpoint_path"]),
            )
            if cache_key not in profile_cache:
                profile_config = read_json(workload_row["profile_config_path"])
                model, _ = load_actor_critic_checkpoint(workload_row["checkpoint_path"], device=device)
                profile_cache[cache_key] = (
                    profile_config,
                    model,
                    {
                        "profile_name": str(workload_row["profile_name"]),
                        "config_path": str(workload_row["profile_config_path"]),
                        "checkpoint_path": str(workload_row["checkpoint_path"]),
                    },
                )
            profile_config, model, profile_row = profile_cache[cache_key]
            row = run_workload_cell(
                workload_row=workload_row,
                executable_spec=patched_spec,
                profile_config=profile_config,
                model=model,
                profile_row=profile_row,
                eval_seed=eval_seed,
            )
            row.update(candidate_execution_metadata(candidate, snapshot_path=snapshot_path, eval_seed=eval_seed))
            append_csv_row(output_dir / "repair_execution_rows.csv", row)
            recorded.add(candidate_id)
        except Exception as exc:  # noqa: BLE001 - every failed cell must be recorded.
            append_csv_row(
                output_dir / "candidate_execution_failure_rows.csv",
                failure_row(candidate, eval_seed=eval_seed, error_type=type(exc).__name__, error_message=str(exc)),
            )
            recorded.add(candidate_id)
        write_run_state(
            output_dir / "run_state.json",
            {
                "candidate_count": len(candidate_rows),
                "completed_execution_count": len(read_csv_rows(output_dir / "repair_execution_rows.csv")),
                "failure_count": len(read_csv_rows(output_dir / "candidate_execution_failure_rows.csv")),
                "accounted_count": len(recorded_candidate_ids(output_dir)),
                "latest_candidate_id": candidate_id,
                "complete": False,
            },
        )
    return finalize_candidate_repair_outputs(
        output_dir=output_dir,
        candidate_rows=candidate_rows,
        overlay_rows=overlay_rows,
        next_blocker=next_blocker,
    )


def validate_candidate_row(candidate: Mapping[str, Any]) -> None:
    required = ("candidate_row_id", "source_panel_row_id", "workload_id", "task_source_id", "profile_name")
    missing = [key for key in required if not str(candidate.get(key, ""))]
    if missing:
        raise ValueError(f"candidate row missing required fields: {missing}")
    if not bool_value(candidate.get("target_accounted", False)):
        raise ValueError("candidate target is not accounted")
    if bool_value(candidate.get("active_config_overwritten", False)):
        raise ValueError("candidate materialization overwrote active config")
    if bool_value(candidate.get("actor_input_change", False)):
        raise ValueError("candidate materialization changed actor input")
    if bool_value(candidate.get("hidden_oracle_feature_injection", False)):
        raise ValueError("candidate materialization injected hidden/oracle features")
    if bool_value(candidate.get("target_labels_actor_visible", False)):
        raise ValueError("candidate target labels are actor-visible")


def validate_workload_join(candidate: Mapping[str, Any], workload_row: Mapping[str, Any]) -> None:
    for key in ("workload_id", "task_source_id", "profile_name", "task_family"):
        if str(candidate.get(key, "")) != str(workload_row.get(key, "")):
            raise ValueError(f"candidate/workload mismatch for {key}")
    if not bool_value(workload_row.get("config_exists", False)):
        raise ValueError("profile config does not exist according to workload row")
    if not bool_value(workload_row.get("checkpoint_exists", False)):
        raise ValueError("checkpoint does not exist according to workload row")


def patched_executable_spec_for_candidate(
    *,
    candidate: Mapping[str, Any],
    executable_spec: Mapping[str, Any],
    overlay_rows: list[dict[str, str]],
    output_dir: Path,
) -> tuple[dict[str, Any], Path]:
    patched = copy.deepcopy(dict(executable_spec))
    patched["env_config"] = copy.deepcopy(dict(patched["env_config"]))
    for overlay in overlay_rows:
        namespace = str(overlay.get("target_namespace", ""))
        key = str(overlay.get("target_key", ""))
        proposed = str(overlay.get("proposed_value", ""))
        if proposed == "preserve_parent_value":
            continue
        value = parse_overlay_value(proposed)
        if namespace == "env":
            patched["env_config"][key] = value
        elif namespace == "env.obstacle":
            obstacle = copy.deepcopy(dict(patched["env_config"].get("obstacle") or {}))
            obstacle[key] = value
            patched["env_config"]["obstacle"] = obstacle
        else:
            raise ValueError(f"unsupported overlay namespace: {namespace}")
    snapshot_dir = output_dir / "config_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = snapshot_dir / f"{candidate['candidate_row_id']}.json"
    write_json(
        snapshot_path,
        {
            "candidate_row_id": candidate.get("candidate_row_id", ""),
            "workload_id": candidate.get("workload_id", ""),
            "task_source_id": candidate.get("task_source_id", ""),
            "profile_name": candidate.get("profile_name", ""),
            "application_mode": "temporary_run_dir_snapshot",
            "active_config_overwritten": False,
            "profile_specific_tuning": False,
            "env_config": patched["env_config"],
        },
    )
    return patched, snapshot_path


def parse_overlay_value(value: str) -> Any:
    text = value.strip()
    if text.lower() in {"true", "false"}:
        return text.lower() == "true"
    try:
        number = float(text)
    except ValueError:
        return value
    if number.is_integer() and "." not in text:
        return int(number)
    return number


def write_overlay_application_rows(
    *,
    output_dir: Path,
    candidate: Mapping[str, Any],
    overlay_rows: list[dict[str, str]],
    snapshot_path: Path,
) -> None:
    existing = {
        str(row.get("application_id", ""))
        for row in read_csv_rows(output_dir / "repair_overlay_application_rows.csv")
    }
    for overlay in overlay_rows:
        application_id = f"m2728-overlay-application-{candidate['candidate_row_id']}-{overlay['overlay_row_id']}"
        if application_id in existing:
            continue
        proposed = str(overlay.get("proposed_value", ""))
        append_csv_row(
            output_dir / "repair_overlay_application_rows.csv",
            {
                "application_id": application_id,
                "candidate_row_id": candidate.get("candidate_row_id", ""),
                "workload_id": candidate.get("workload_id", ""),
                "task_source_id": candidate.get("task_source_id", ""),
                "profile_name": candidate.get("profile_name", ""),
                "overlay_row_id": overlay.get("overlay_row_id", ""),
                "overlay_id": overlay.get("overlay_id", ""),
                "overlay_family": overlay.get("overlay_family", ""),
                "target_namespace": overlay.get("target_namespace", ""),
                "target_key": overlay.get("target_key", ""),
                "proposed_value": proposed,
                "applied_value": "preserved" if proposed == "preserve_parent_value" else proposed,
                "application_mode": "temporary_run_dir_snapshot",
                "config_snapshot_path": str(snapshot_path),
                "preserves_parent_geometry": overlay.get("preserves_parent_geometry", "True"),
                "active_config_overwritten": False,
                "profile_specific_tuning": False,
                "actor_input_change": False,
                "hidden_oracle_feature_injection": False,
                "claim_boundary": CLAIM_SCOPE,
            },
        )


def candidate_execution_metadata(
    candidate: Mapping[str, Any],
    *,
    snapshot_path: Path,
    eval_seed: int,
) -> dict[str, Any]:
    return {
        "candidate_row_id": candidate.get("candidate_row_id", ""),
        "source_panel_row_id": candidate.get("source_panel_row_id", ""),
        "source_candidate_id": candidate.get("source_candidate_id", ""),
        "anchor_task_source_id": candidate.get("anchor_task_source_id", ""),
        "m2728_eval_seed": int(eval_seed),
        "repair_overlay_id": candidate.get("repair_overlay_id", ""),
        "guardrail_overlay_id": candidate.get("guardrail_overlay_id", ""),
        "repair_config_snapshot_path": str(snapshot_path),
        "overlay_applied": True,
        "temporary_run_dir_snapshot": True,
        "active_config_overwritten": False,
        "bounded_offtrack_repair_execution_preflight": True,
        "protected_row_execution": False,
        "protected_rows_in_success_denominator": False,
        "target_labels_actor_visible": False,
        "protected_labels_actor_visible": False,
        "profile_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "hidden_oracle_actor_input_required": False,
        "actor_input_contract_changed": False,
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
        "candidate_row_id": candidate.get("candidate_row_id", ""),
        "source_panel_row_id": candidate.get("source_panel_row_id", ""),
        "source_candidate_id": candidate.get("source_candidate_id", ""),
        "anchor_task_source_id": candidate.get("anchor_task_source_id", ""),
        "workload_id": candidate.get("workload_id", ""),
        "task_source_id": candidate.get("task_source_id", ""),
        "profile_name": candidate.get("profile_name", ""),
        "task_family": candidate.get("task_family", ""),
        "error_type": error_type,
        "error_message": error_message,
        "eval_seed": int(eval_seed),
        "overlay_applied": False,
        "active_config_overwritten": False,
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
        "winner_selected": False,
        "protected_row_execution": False,
        "protected_rows_in_success_denominator": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_required": False,
        "target_labels_actor_visible": False,
        "protected_labels_actor_visible": False,
        "profile_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "diagnostic_only_no_verdict": True,
        "claim_boundary": CLAIM_SCOPE,
    }


def recorded_candidate_ids(output: Path) -> set[str]:
    rows = read_csv_rows(output / "repair_execution_rows.csv") + read_csv_rows(
        output / "candidate_execution_failure_rows.csv"
    )
    return {str(row.get("candidate_row_id", "")) for row in rows if row.get("candidate_row_id")}


def finalize_candidate_repair_outputs(
    *,
    output_dir: Path,
    candidate_rows: list[dict[str, str]],
    overlay_rows: list[dict[str, str]],
    next_blocker: str,
) -> dict[str, Any]:
    episode_rows = [dict(row) for row in read_csv_rows(output_dir / "repair_execution_rows.csv")]
    failure_rows = [dict(row) for row in read_csv_rows(output_dir / "candidate_execution_failure_rows.csv")]
    write_csv_rows(output_dir / "candidate_execution_failure_rows.csv", failure_rows, fieldnames=FAILURE_FIELDNAMES)
    if not (output_dir / "repair_overlay_application_rows.csv").exists():
        write_csv_rows(output_dir / "repair_overlay_application_rows.csv", [], fieldnames=OVERLAY_APPLICATION_FIELDNAMES)
    accounted_count = len(recorded_candidate_ids(output_dir))
    all_metrics_finite = selected_metrics_are_finite(episode_rows) if episode_rows else False
    status_pass = bool(
        len(candidate_rows) == EXPECTED_CANDIDATE_COUNT
        and len(overlay_rows) == EXPECTED_OVERLAY_ROW_COUNT
        and accounted_count == len(candidate_rows)
        and bool(episode_rows)
        and all_metrics_finite
        and not any(forbidden_execution_flag(row) for row in episode_rows + failure_rows)
    )
    summary = {
        "result_class": (
            "engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_bounded_candidate_execution_pass"
            if status_pass
            else "engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_bounded_candidate_execution_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "candidate_count": len(candidate_rows),
        "overlay_row_count": len(overlay_rows),
        "episode_count": len(episode_rows),
        "failure_count": len(failure_rows),
        "accounted_candidate_count": accounted_count,
        "all_selected_metrics_finite": bool(all_metrics_finite),
        "environment_reset_run": bool(episode_rows),
        "environment_step_run": bool(episode_rows),
        "policy_action_run": bool(episode_rows),
        "policy_rollout_run": bool(episode_rows),
        "repair_execution_started": bool(episode_rows),
        "active_config_overwritten": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "protected_row_execution": False,
        "protected_rows_in_success_denominator": False,
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "level3_self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "artifacts": {
            "repair_execution_rows": str(output_dir / "repair_execution_rows.csv"),
            "candidate_execution_failure_rows": str(output_dir / "candidate_execution_failure_rows.csv"),
            "repair_overlay_application_rows": str(output_dir / "repair_overlay_application_rows.csv"),
            "run_state": str(output_dir / "run_state.json"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output_dir / "candidate_repair_execution_summary.json", summary)
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


def build_guardrail_audit_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for index, guardrail in enumerate(source["guardrail_rows"], start=1):
        rows.append(
            {
                "audit_id": f"m2728-guardrail-audit-{index:04d}",
                "guardrail_row_id": guardrail.get("guardrail_row_id", ""),
                "guardrail_family": guardrail.get("guardrail_family", ""),
                "source_panel_row_id": guardrail.get("source_panel_row_id", ""),
                "source_candidate_id": guardrail.get("source_candidate_id", ""),
                "profile_name": guardrail.get("profile_name", ""),
                "task_family": guardrail.get("task_family", ""),
                "taxonomy_family": guardrail.get("taxonomy_family", ""),
                "m2728_execution_candidate": False,
                "m2728_execution_run": False,
                "target_panel_admitted": False,
                "execution_scheduled": False,
                "protected_rows_in_success_denominator": False,
                "diagnostic_only_no_verdict": True,
                "actor_input_change": False,
                "hidden_oracle_feature_injection": False,
                "claim_boundary": CLAIM_SCOPE,
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
                "aggregate_id": f"m2728-{aggregate_family}-aggregate-{index:04d}",
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
        actor_join("active_config_overwritten", active_config_overwritten(artifact_rows), False, False),
        actor_join("hidden_oracle_actor_input_detected", hidden_oracle_detected(artifact_rows), False, False),
        actor_join("target_labels_actor_visible", labels_visible(artifact_rows, "target_labels_actor_visible"), False, False),
        actor_join(
            "protected_labels_actor_visible",
            labels_visible(artifact_rows, "protected_labels_actor_visible"),
            False,
            False,
        ),
        actor_join("profile_labels_actor_visible", labels_visible(artifact_rows, "profile_labels_actor_visible"), False, False),
        actor_join("route_labels_actor_visible", labels_visible(artifact_rows, "route_labels_actor_visible"), False, False),
        actor_join("verdict_labels_actor_visible", labels_visible(artifact_rows, "verdict_labels_actor_visible"), False, False),
        actor_join("protected_rows_in_success_denominator", protected_denominator_used(artifact_rows), False, False),
        actor_join(
            "m2725_actor_contract_rows_pass",
            all(bool_value(row.get("status_pass")) for row in source["actor_contract_rows"]),
            True,
            False,
        ),
    ]
    return rows


def actor_join(field: str, observed: Any, expected: Any, actor_visible: bool) -> dict[str, Any]:
    return {
        "join_id": f"m2728-actor-join-{field}",
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
        ("bounded_repair_execution_preflight", "execution", episode_or_failure_rows_present, "M2728 repair execution/failure rows"),
        ("repair_execution_rows_materialized", "artifact", artifacts_present, "repair_execution_rows.csv"),
        ("candidate_failure_rows_materialized", "artifact", artifacts_present, "candidate_execution_failure_rows.csv"),
        ("overlay_application_rows_materialized", "artifact", artifacts_present, "repair_overlay_application_rows.csv"),
        ("guardrail_audit_rows_materialized", "artifact", artifacts_present, "guardrail_audit_rows.csv"),
        ("profile_aggregate_materialized", "artifact", artifacts_present, "profile_aggregate.csv"),
        ("anchor_aggregate_materialized", "artifact", artifacts_present, "anchor_aggregate.csv"),
        ("actor_contract_join_rows_materialized", "artifact", artifacts_present, "actor_contract_join_rows.csv"),
        ("claim_boundary_rows_materialized", "artifact", artifacts_present, "claim_boundary_rows.csv"),
        ("gate_matrix_materialized", "artifact", artifacts_present, "gate_matrix.csv"),
        ("run_state_materialized", "artifact", artifacts_present, "run_state.json"),
        ("diagnostic_metrics_recorded", "diagnostic_metric", episode_or_failure_rows_present, "diagnostic aggregate rows only"),
        ("temporary_overlay_application", "contract", episode_or_failure_rows_present, "temporary run-dir config snapshots"),
        ("guardrails_preserved", "contract", True, "guardrail_audit_rows.csv"),
        ("follow_up_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2729 result-audit manifest"),
    ]
    blocked = [
        ("guardrail_row_execution", "execution", "forbidden in M2728"),
        ("protected_row_execution", "execution", "forbidden in M2728"),
        ("active_config_overwrite", "contract", "forbidden in M2728"),
        ("replay_execution", "execution", "future replay manifest"),
        ("validation_execution", "validation", "future validation manifest"),
        ("training_or_ppo", "execution", "future training manifest"),
        ("private_holdout_tuning", "holdout_policy", "forbidden in M2728"),
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
    rows = [claim(claim_id, family, True, made, evidence) for claim_id, family, made, evidence in allowed]
    rows.extend(claim(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def claim(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m2728_{claim_id}",
        "claim_family": family,
        "allowed_in_m2728": allowed,
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
    overlay_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    profile_aggregate: list[dict[str, Any]],
    anchor_aggregate: list[dict[str, Any]],
    actor_join_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    episode_rows = artifact_rows["repair_execution_rows"]
    failure_rows = artifact_rows["candidate_execution_failure_rows"]
    overlay_application_rows = artifact_rows["repair_overlay_application_rows"]
    accounted_count = len({row.get("candidate_row_id", "") for row in episode_rows + failure_rows if row.get("candidate_row_id")})
    expected_profile_aggregate_count = len({str(row.get("profile_name", "")) for row in candidate_rows})
    expected_anchor_aggregate_count = len({str(row.get("anchor_task_source_id", "")) for row in candidate_rows})
    allowed_claims = [row for row in claim_rows if bool_value(row["allowed_in_m2728"])]
    blocked_claims = [row for row in claim_rows if not bool_value(row["allowed_in_m2728"])]
    gates = [
        ("source_artifacts_present", "lineage", all(source["source_exists"].values()), source["source_exists"], "all M2725/M2727/spec/workload/follow-up artifacts present", "lineage_invalid"),
        ("m2727_admits_execution_preflight", "lineage", "admit_current_m1690_exact_executable_reentry_offtrack_repair_bounded_execution_preflight" in source["m2727_design_text"], "decision present", "decision present", "lineage_invalid"),
        ("m2725_status_pass", "lineage", bool_value(source["m2725_summary"].get("status_pass", False)), source["m2725_summary"].get("status_pass", None), True, "lineage_invalid"),
        ("candidate_count", "lineage", len(candidate_rows) == EXPECTED_CANDIDATE_COUNT, len(candidate_rows), EXPECTED_CANDIDATE_COUNT, "metric_artifact"),
        ("overlay_row_count", "lineage", len(overlay_rows) == EXPECTED_OVERLAY_ROW_COUNT, len(overlay_rows), EXPECTED_OVERLAY_ROW_COUNT, "metric_artifact"),
        ("guardrail_row_count", "lineage", len(guardrail_rows) == EXPECTED_GUARDRAIL_ROW_COUNT, len(guardrail_rows), EXPECTED_GUARDRAIL_ROW_COUNT, "metric_artifact"),
        ("execution_accounted_all_candidates", "execution", accounted_count == len(candidate_rows), accounted_count, len(candidate_rows), "scenario_sampling_failure"),
        ("repair_execution_rows_present", "execution", bool(episode_rows), len(episode_rows), ">0", "scenario_sampling_failure"),
        ("all_selected_metrics_finite", "metric", selected_metrics_are_finite(episode_rows) if episode_rows else False, execution_summary.get("all_selected_metrics_finite"), True, "metric_artifact"),
        ("overlay_application_shape", "artifact", len(overlay_application_rows) == len(candidate_rows) * len(overlay_rows), len(overlay_application_rows), len(candidate_rows) * len(overlay_rows), "metric_artifact"),
        ("overlay_temporary_no_overwrite", "contract", not active_config_overwritten(artifact_rows) and all(not bool_value(row.get("active_config_overwritten")) for row in overlay_application_rows), "active config overwrite false", "all false", "contract_violation"),
        ("profile_aggregate_shape", "artifact", len(profile_aggregate) == expected_profile_aggregate_count, len(profile_aggregate), expected_profile_aggregate_count, "metric_artifact"),
        ("anchor_aggregate_shape", "artifact", len(anchor_aggregate) == expected_anchor_aggregate_count, len(anchor_aggregate), expected_anchor_aggregate_count, "metric_artifact"),
        ("guardrails_not_executed", "contract", all(not bool_value(row["m2728_execution_run"]) for row in guardrail_rows), "all guardrails not run", "all false", "contract_violation"),
        ("protected_not_success_denominator", "contract", not protected_denominator_used(artifact_rows) and all(not bool_value(row["protected_rows_in_success_denominator"]) for row in guardrail_rows), "protected rows outside denominator", "all false", "proof_washout"),
        ("actor_contract_preserved", "contract", all(bool_value(row["status_pass"]) for row in actor_join_rows), f"rows={len(actor_join_rows)} pass={sum(bool_value(row['status_pass']) for row in actor_join_rows)}", "all actor joins pass", "contract_violation"),
        ("labels_actor_invisible", "contract", not any(labels_visible(artifact_rows, key) for key in ("target_labels_actor_visible", "protected_labels_actor_visible", "profile_labels_actor_visible", "route_labels_actor_visible", "verdict_labels_actor_visible")), "all labels actor-invisible", "all false", "contract_violation"),
        ("no_hidden_oracle_actor_input", "contract", not hidden_oracle_detected(artifact_rows), "hidden/oracle actor input false", "all false", "contract_violation"),
        ("no_forbidden_execution", "execution_guardrail", not any(forbidden_execution_flag(row) for row in episode_rows + failure_rows), "no replay/train/PPO/private holdout/tuning/promotion/ranking", "all false", "objective_overfit"),
        ("claim_boundary_blocks_overclaim", "claim_boundary", all(bool_value(row["status_pass"]) for row in allowed_claims) and all(not bool_value(row["claim_made"]) and bool_value(row["status_pass"]) for row in blocked_claims), f"allowed={len(allowed_claims)} blocked={len(blocked_claims)}", "allowed claims pass and blocked claims not made", "proof_washout"),
        ("required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
    ]
    return [gate(gate_id, family, status_pass, observed, expected, failure_type) for gate_id, family, status_pass, observed, expected, failure_type in gates]


def gate(gate_id: str, family: str, status_pass: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m2728_{gate_id}",
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
    overlay_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
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
    episode_rows = artifact_rows["repair_execution_rows"]
    failure_rows = artifact_rows["candidate_execution_failure_rows"]
    accounted_count = len({row.get("candidate_row_id", "") for row in episode_rows + failure_rows if row.get("candidate_row_id")})
    gate_matrix_pass = all(bool_value(row["status_pass"]) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_bounded_execution_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_bounded_execution_preflight_fail"
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
        "m2725_status_pass": bool_value(source["m2725_summary"].get("status_pass", False)),
        "candidate_count": len(candidate_rows),
        "expected_candidate_count": EXPECTED_CANDIDATE_COUNT,
        "shared_repair_overlay_row_count": len(overlay_rows),
        "guardrail_audit_row_count": len(guardrail_rows),
        "repair_execution_row_count": len(episode_rows),
        "candidate_execution_failure_row_count": len(failure_rows),
        "accounted_candidate_count": accounted_count,
        "all_selected_metrics_finite": selected_metrics_are_finite(episode_rows) if episode_rows else False,
        "repair_overlay_application_row_count": len(artifact_rows["repair_overlay_application_rows"]),
        "profile_aggregate_row_count": len(profile_aggregate),
        "anchor_aggregate_row_count": len(anchor_aggregate),
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
        "bounded_offtrack_repair_execution_preflight": bool(episode_rows),
        "repair_execution_started": bool(episode_rows),
        "active_config_overwritten": active_config_overwritten(artifact_rows),
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
        "route_labels_actor_visible": labels_visible(artifact_rows, "route_labels_actor_visible"),
        "verdict_labels_actor_visible": labels_visible(artifact_rows, "verdict_labels_actor_visible"),
        "protected_row_execution": False,
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


def ensure_artifact_files(paths: dict[str, Path]) -> None:
    if not paths["candidate_execution_failure_rows"].exists():
        write_csv_rows(paths["candidate_execution_failure_rows"], [], fieldnames=FAILURE_FIELDNAMES)
    if not paths["repair_overlay_application_rows"].exists():
        write_csv_rows(paths["repair_overlay_application_rows"], [], fieldnames=OVERLAY_APPLICATION_FIELDNAMES)


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2728 Engineering Controller Route A Current-M1690 Exact-Executable Reentry Offtrack Repair Bounded Execution Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- candidate rows: {summary['candidate_count']}",
            f"- repair execution rows: {summary['repair_execution_row_count']}",
            f"- failure rows: {summary['candidate_execution_failure_row_count']}",
            f"- accounted candidates: {summary['accounted_candidate_count']}/{summary['candidate_count']}",
            f"- overlay application rows: {summary['repair_overlay_application_row_count']}",
            f"- guardrail audit rows: {summary['guardrail_audit_row_count']}",
            f"- profile aggregate rows: {summary['profile_aggregate_row_count']}",
            f"- anchor aggregate rows: {summary['anchor_aggregate_row_count']}",
            f"- active config overwritten: {summary['active_config_overwritten']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M2728 records bounded closed-loop diagnostic repair data only for the M2725 candidate target rows. Guardrail and protected rows remain excluded from execution and ordinary success denominators.",
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
            "active_config_overwritten",
            "profile_specific_tuning",
            "actor_input_contract_changed",
            "ranking_run",
            "winner_selected",
            "checkpoint_promoted",
            "success_rate_verdict_claim_made",
            "driver_performance_claim_made",
            "repair_success_claim_made",
            "paper_claim_made",
            "current_sim_verdict_claim_made",
            "level3_self_id_claim_made",
        )
    )


def labels_visible(artifact_rows: dict[str, list[dict[str, Any]]], key: str) -> bool:
    rows = (
        artifact_rows["repair_execution_rows"]
        + artifact_rows["candidate_execution_failure_rows"]
        + artifact_rows["guardrail_audit_rows"]
    )
    return any(bool_value(row.get(key, False)) for row in rows)


def hidden_oracle_detected(artifact_rows: dict[str, list[dict[str, Any]]]) -> bool:
    rows = (
        artifact_rows["repair_execution_rows"]
        + artifact_rows["candidate_execution_failure_rows"]
        + artifact_rows["guardrail_audit_rows"]
        + artifact_rows["repair_overlay_application_rows"]
    )
    return any(
        bool_value(row.get("hidden_oracle_actor_input_required", row.get("hidden_oracle_feature_injection", False)))
        for row in rows
    )


def active_config_overwritten(artifact_rows: dict[str, list[dict[str, Any]]]) -> bool:
    rows = (
        artifact_rows["repair_execution_rows"]
        + artifact_rows["candidate_execution_failure_rows"]
        + artifact_rows["repair_overlay_application_rows"]
    )
    return any(bool_value(row.get("active_config_overwritten", False)) for row in rows)


def protected_denominator_used(artifact_rows: dict[str, list[dict[str, Any]]]) -> bool:
    rows = (
        artifact_rows["repair_execution_rows"]
        + artifact_rows["candidate_execution_failure_rows"]
        + artifact_rows["guardrail_audit_rows"]
    )
    return any(bool_value(row.get("protected_rows_in_success_denominator", False)) for row in rows)


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
    parser.add_argument("--m2725-dir", type=Path, default=DEFAULT_M2725_DIR)
    parser.add_argument("--m2727-design", type=Path, default=DEFAULT_M2727_DESIGN)
    parser.add_argument("--executable-specs", type=Path, default=DEFAULT_EXECUTABLE_SPECS)
    parser.add_argument("--executable-workload", type=Path, default=DEFAULT_EXECUTABLE_WORKLOAD)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args(argv)

    summary = run_current_m1690_exact_executable_reentry_offtrack_repair_bounded_execution_preflight(
        m2725_dir=args.m2725_dir,
        m2727_design=args.m2727_design,
        executable_specs=args.executable_specs,
        executable_workload=args.executable_workload,
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
    print(f"repair_execution_row_count={summary['repair_execution_row_count']}")
    print(f"candidate_execution_failure_row_count={summary['candidate_execution_failure_row_count']}")
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
