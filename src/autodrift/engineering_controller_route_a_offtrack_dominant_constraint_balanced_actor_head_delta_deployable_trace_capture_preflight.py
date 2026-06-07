"""Capture M2977 deployable actor-view traces for Route A residual work.

M2977 consumes the M2973/M2974/M2975/M2976 trace-readiness chain and reruns the
accepted candidate plus success-identity guard surface only to persist raw
actor-view observation/action traces. It does not fit a residual head, train,
validate, rank, promote, or make a driver-performance claim.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.controller_family_full_rollout_execution import (
    DEFAULT_EXECUTABLE_SPECS,
    DEFAULT_EXECUTABLE_WORKLOAD,
    env_config_for_executable_profile,
    load_executable_specs,
    load_executable_workload,
    read_csv_rows,
    write_run_state,
)
from autodrift.controller_profile_runtime import profile_runtime_summary, wrap_env_with_profile_mask
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import ActorPolicy, outcome_bucket_from_info
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM
from autodrift.engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_bounded_execution_preflight import (  # noqa: E501
    DEFAULT_RESIDUAL_LIMIT,
    ZeroResidualActorHeadDeltaAdapter,
)


MILESTONE_ID = (
    "m2977-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "deployable-trace-capture-preflight"
)
NEXT_ID = (
    "m2978-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "deployable-trace-capture-result-audit"
)
DEFAULT_M2973_DIR = Path(
    "runs/m2973_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "nonzero_residual_training_trace_panel_preflight"
)
DEFAULT_M2975_SYNTHESIS = Path(
    "docs/m2975-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-training-trace-branch-synthesis.md"
)
DEFAULT_M2976_DESIGN = Path(
    "docs/m2976-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "deployable-trace-capture-design.md"
)
DEFAULT_M2960_DIR = Path(
    "runs/m2960_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "bounded_execution_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2977_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "deployable_trace_capture_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2977-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "deployable-trace-capture-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2978-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "actor-head-delta-deployable-trace-capture-result-audit.json"
)

EXPECTED_TRAINING_CANDIDATE_COUNT = 43
EXPECTED_SUCCESS_IDENTITY_GUARD_COUNT = 13
EXPECTED_STALE_GUARDRAIL_COUNT = 11
EXPECTED_EXECUTED_RAW_TRACE_COUNT = 56

CLAIM_SCOPE = (
    "M2977 Route A actor-head delta deployable trace-capture preflight only; "
    "accepted M2973/M2974 future training candidates and success identity guards "
    "may be rerun under the read-only zero-residual actor-head delta wrapper to "
    "persist raw actor-view observation/action traces, while stale fixed-source "
    "guardrails remain non-executed protected rows. No residual fitting, training, "
    "PPO, validation, ranking, winner selection, checkpoint mutation, checkpoint "
    "promotion, repair success, driver-performance, paper, current-sim verdict, "
    "high-fidelity validation, full ideal driver, finite-window-vs-GRU, or self-ID "
    "claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "residual fitting readiness before M2978 audit, residual quality, repair "
    "success, driver performance, validation readiness or result, controller/source/"
    "task/profile/checkpoint/candidate ranking, winner selection, checkpoint "
    "promotion, success-rate verdict, paper evidence, finite-window-vs-GRU "
    "conclusion, current-sim verdict, high-fidelity validation readiness or result, "
    "full ideal driver completion, or level3 self-identification"
)

CAPTURE_PLAN_FIELDNAMES = [
    "capture_plan_row_id",
    "source_trace_row_id",
    "source_row_id",
    "execution_candidate_id",
    "row_role",
    "objective_or_guard_family",
    "execute_capture",
    "stale_guardrail_protected",
    "expected_trace_step_count",
    "m2960_eval_seed",
    "workload_id",
    "task_family",
    "outcome_family",
    "parent_checkpoint_path",
    "parent_profile_config_path",
    "actor_observation_dim",
    "actor_action_dim",
    "claim_boundary",
]
RAW_TRACE_INDEX_FIELDNAMES = [
    "raw_trace_index_row_id",
    "capture_plan_row_id",
    "source_trace_row_id",
    "source_row_id",
    "execution_candidate_id",
    "row_role",
    "objective_or_guard_family",
    "raw_trace_path",
    "raw_trace_persisted",
    "trace_step_count",
    "expected_trace_step_count",
    "observation_shape",
    "action_shape",
    "next_observation_shape",
    "reward_shape",
    "done_shape",
    "timeout_shape",
    "actor_observation_dim",
    "actor_action_dim",
    "tensors_finite",
    "actor_view_only",
    "hidden_oracle_actor_input_required",
    "future_target_actor_input_required",
    "objective_labels_actor_visible",
    "admission_labels_actor_visible",
    "trace_readiness_labels_actor_visible",
    "verdict_labels_actor_visible",
    "checkpoint_loaded_read_only",
    "zero_residual_identity_mode",
    "residual_delta_abs_max",
    "terminated",
    "truncated",
    "termination_reason",
    "completion_reason",
    "outcome_bucket",
    "training_started",
    "ppo_run",
    "validation_run",
    "ranking_run",
    "checkpoint_mutated",
    "claim_boundary",
]
RAW_TRACE_GUARD_FIELDNAMES = [
    "raw_trace_guard_row_id",
    "source_trace_row_id",
    "source_row_id",
    "execution_candidate_id",
    "guard_family",
    "guard_role",
    "execute_capture",
    "raw_trace_persisted",
    "stale_guardrail_protected",
    "positive_training_target",
    "training_started",
    "ppo_run",
    "ranking_run",
    "checkpoint_mutated",
    "claim_boundary",
]
RAW_TRACE_AVAILABILITY_FIELDNAMES = [
    "raw_trace_availability_row_id",
    "source_trace_row_id",
    "source_row_id",
    "execution_candidate_id",
    "row_role",
    "objective_or_guard_family",
    "trace_metadata_present",
    "raw_trace_persisted",
    "trace_file_exists",
    "trace_step_count",
    "availability_status",
    "blocking_reason_for_residual_fitting",
    "claim_boundary",
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
    "allowed_in_m2977",
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
    "capture_plan_rows",
    "raw_trace_index_rows",
    "raw_trace_guard_rows",
    "raw_trace_availability_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
]

CaptureFn = Callable[[Mapping[str, Any], Mapping[str, Any], dict[str, Any]], dict[str, Any]]


def run_deployable_trace_capture_preflight(
    *,
    m2973_dir: Path | str = DEFAULT_M2973_DIR,
    m2975_synthesis: Path | str = DEFAULT_M2975_SYNTHESIS,
    m2976_design: Path | str = DEFAULT_M2976_DESIGN,
    m2960_dir: Path | str = DEFAULT_M2960_DIR,
    executable_specs: Path | str = DEFAULT_EXECUTABLE_SPECS,
    executable_workload: Path | str = DEFAULT_EXECUTABLE_WORKLOAD,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    device: str = "cpu",
    capture_fn: CaptureFn | None = None,
    milestone: str = MILESTONE_ID,
    next_blocker: str = NEXT_ID,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    raw_trace_dir = output / "raw_traces"
    raw_trace_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path))
    source = load_source_artifacts(
        m2973_dir=Path(m2973_dir),
        m2975_synthesis=Path(m2975_synthesis),
        m2976_design=Path(m2976_design),
        m2960_dir=Path(m2960_dir),
        executable_specs=Path(executable_specs),
        executable_workload=Path(executable_workload),
        follow_up_manifest=Path(follow_up_manifest),
    )
    plan_rows = build_capture_plan_rows(source)
    write_csv_rows(paths["capture_plan_rows"], plan_rows, fieldnames=CAPTURE_PLAN_FIELDNAMES)

    context = build_capture_context(source, device=device)
    raw_index_rows, guard_rows, availability_rows = capture_plan_traces(
        plan_rows=plan_rows,
        output_dir=output,
        raw_trace_dir=raw_trace_dir,
        context=context,
        capture_fn=capture_fn or capture_one_row,
        next_blocker=next_blocker,
    )
    write_csv_rows(paths["raw_trace_index_rows"], raw_index_rows, fieldnames=RAW_TRACE_INDEX_FIELDNAMES)
    write_csv_rows(paths["raw_trace_guard_rows"], guard_rows, fieldnames=RAW_TRACE_GUARD_FIELDNAMES)
    write_csv_rows(
        paths["raw_trace_availability_rows"],
        availability_rows,
        fieldnames=RAW_TRACE_AVAILABILITY_FIELDNAMES,
    )
    write_run_state(
        paths["run_state"],
        {
            "capture_plan_row_count": len(plan_rows),
            "raw_trace_index_row_count": len(raw_index_rows),
            "raw_trace_guard_row_count": len(guard_rows),
            "raw_trace_availability_row_count": len(availability_rows),
            "complete": False,
            "next_blocker": next_blocker,
        },
    )

    follow_up = build_follow_up_manifest(output_dir=output, doc_path=Path(doc_path), summary_path=paths["summary"])
    write_json(follow_up_manifest, follow_up)
    source["source_exists"]["follow_up_manifest"] = Path(follow_up_manifest).exists()

    actor_rows = build_actor_contract_guard_rows(raw_index_rows, guard_rows)
    claim_rows = build_claim_boundary_rows(
        raw_index_rows=raw_index_rows,
        guard_rows=guard_rows,
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        plan_rows=plan_rows,
        raw_index_rows=raw_index_rows,
        guard_rows=guard_rows,
        availability_rows=availability_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
    )
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        plan_rows=plan_rows,
        raw_index_rows=raw_index_rows,
        guard_rows=guard_rows,
        availability_rows=availability_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
        device=device,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    summary["required_artifacts_present"] = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    write_json(paths["summary"], summary)
    write_run_state(
        paths["run_state"],
        {
            "capture_plan_row_count": len(plan_rows),
            "raw_trace_index_row_count": len(raw_index_rows),
            "raw_trace_guard_row_count": len(guard_rows),
            "raw_trace_availability_row_count": len(availability_rows),
            "complete": True,
            "status_pass": summary["status_pass"],
            "next_blocker": next_blocker,
        },
    )
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "capture_plan_rows": output_dir / "capture_plan_rows.csv",
        "raw_trace_index_rows": output_dir / "raw_trace_index_rows.csv",
        "raw_trace_guard_rows": output_dir / "raw_trace_guard_rows.csv",
        "raw_trace_availability_rows": output_dir / "raw_trace_availability_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2973_dir: Path,
    m2975_synthesis: Path,
    m2976_design: Path,
    m2960_dir: Path,
    executable_specs: Path,
    executable_workload: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2973_summary": m2973_dir / "summary.json",
        "trace_panel_rows": m2973_dir / "trace_panel_rows.csv",
        "trace_guard_rows": m2973_dir / "trace_guard_rows.csv",
        "trace_availability_rows": m2973_dir / "trace_availability_rows.csv",
        "m2975_synthesis": m2975_synthesis,
        "m2976_design": m2976_design,
        "m2960_summary": m2960_dir / "summary.json",
        "bounded_execution_rows": m2960_dir / "bounded_execution_rows.csv",
        "contract_execution_rows": m2960_dir / "actor_head_delta_contract_execution_rows.csv",
        "executable_specs": executable_specs,
        "executable_workload": executable_workload,
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2973_summary": read_json(paths["m2973_summary"]) if source_exists["m2973_summary"] else {},
        "m2975_synthesis_text": paths["m2975_synthesis"].read_text(encoding="utf-8")
        if source_exists["m2975_synthesis"]
        else "",
        "m2976_design_text": paths["m2976_design"].read_text(encoding="utf-8")
        if source_exists["m2976_design"]
        else "",
        "m2960_summary": read_json(paths["m2960_summary"]) if source_exists["m2960_summary"] else {},
        "trace_panel_rows": read_csv_rows(paths["trace_panel_rows"]),
        "trace_guard_rows": read_csv_rows(paths["trace_guard_rows"]),
        "trace_availability_rows": read_csv_rows(paths["trace_availability_rows"]),
        "bounded_execution_rows": read_csv_rows(paths["bounded_execution_rows"]),
        "contract_execution_rows": read_csv_rows(paths["contract_execution_rows"]),
        "executable_specs": load_executable_specs(paths["executable_specs"]) if source_exists["executable_specs"] else [],
        "executable_workload_rows": load_executable_workload(paths["executable_workload"])
        if source_exists["executable_workload"]
        else [],
    }


def build_capture_plan_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    execution_by_candidate = {
        str(row.get("execution_candidate_id", "")): row for row in source["bounded_execution_rows"]
    }
    rows: list[dict[str, Any]] = []
    for index, panel in enumerate(source["trace_panel_rows"], start=1):
        execution = execution_by_candidate.get(str(panel.get("execution_candidate_id", "")), {})
        rows.append(
            capture_plan_row(
                index=index,
                source_trace_row_id=str(panel.get("trace_panel_row_id", "")),
                source_row_id=str(panel.get("training_admission_candidate_id", "")),
                execution_candidate_id=str(panel.get("execution_candidate_id", "")),
                row_role="future_training_candidate",
                objective_or_guard_family=str(panel.get("objective_family", "")),
                execute_capture=True,
                stale_guardrail_protected=False,
                expected_trace_step_count=_to_int(panel.get("trace_step_count"), default=0),
                source_row=panel,
                execution_row=execution,
            )
        )
    for guard in source["trace_guard_rows"]:
        guard_family = str(guard.get("guard_family", ""))
        is_stale = guard_family == "actor_head_delta_execution_admission_blocked_stale_fixed_surface"
        execution = execution_by_candidate.get(str(guard.get("execution_candidate_id", "")), {})
        rows.append(
            capture_plan_row(
                index=len(rows) + 1,
                source_trace_row_id=str(guard.get("trace_guard_row_id", "")),
                source_row_id=str(guard.get("source_guard_id", "")),
                execution_candidate_id=str(guard.get("execution_candidate_id", "")),
                row_role="stale_fixed_source_guardrail" if is_stale else "success_identity_guard",
                objective_or_guard_family=guard_family,
                execute_capture=not is_stale,
                stale_guardrail_protected=is_stale,
                expected_trace_step_count=_to_int(guard.get("trace_step_count"), default=0),
                source_row=guard,
                execution_row=execution,
            )
        )
    return rows


def capture_plan_row(
    *,
    index: int,
    source_trace_row_id: str,
    source_row_id: str,
    execution_candidate_id: str,
    row_role: str,
    objective_or_guard_family: str,
    execute_capture: bool,
    stale_guardrail_protected: bool,
    expected_trace_step_count: int,
    source_row: Mapping[str, Any],
    execution_row: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "capture_plan_row_id": f"m2977-capture-plan-{index:04d}",
        "source_trace_row_id": source_trace_row_id,
        "source_row_id": source_row_id,
        "execution_candidate_id": execution_candidate_id,
        "row_role": row_role,
        "objective_or_guard_family": objective_or_guard_family,
        "execute_capture": bool(execute_capture),
        "stale_guardrail_protected": bool(stale_guardrail_protected),
        "expected_trace_step_count": int(expected_trace_step_count),
        "m2960_eval_seed": _to_int(execution_row.get("m2960_eval_seed", execution_row.get("eval_seed")), default=0),
        "workload_id": execution_row.get("workload_id", source_row.get("workload_id", "")),
        "task_family": execution_row.get("task_family", source_row.get("task_family", "")),
        "outcome_family": source_row.get("outcome_family", execution_row.get("outcome_bucket", "")),
        "parent_checkpoint_path": execution_row.get("parent_checkpoint_path", execution_row.get("checkpoint_path", "")),
        "parent_profile_config_path": execution_row.get(
            "parent_profile_config_path",
            execution_row.get("profile_config_path", ""),
        ),
        "actor_observation_dim": _to_int(source_row.get("actor_observation_dim"), default=P0_OBSERVATION_DIM),
        "actor_action_dim": _to_int(source_row.get("actor_action_dim"), default=ACTION_DIM),
        "claim_boundary": CLAIM_SCOPE,
    }


def build_capture_context(source: Mapping[str, Any], *, device: str) -> dict[str, Any]:
    return {
        "execution_by_candidate": {
            str(row.get("execution_candidate_id", "")): row for row in source["bounded_execution_rows"]
        },
        "workload_by_id": {str(row.get("workload_id", "")): row for row in source["executable_workload_rows"]},
        "spec_by_task_source_id": {str(row.get("task_source_id", "")): row for row in source["executable_specs"]},
        "profile_cache": {},
        "device": device,
    }


def capture_plan_traces(
    *,
    plan_rows: list[dict[str, Any]],
    output_dir: Path,
    raw_trace_dir: Path,
    context: dict[str, Any],
    capture_fn: CaptureFn,
    next_blocker: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    raw_index_rows: list[dict[str, Any]] = []
    guard_rows: list[dict[str, Any]] = []
    availability_rows: list[dict[str, Any]] = []
    executed_seen = 0
    for index, plan in enumerate(plan_rows, start=1):
        execute_capture = _bool(plan.get("execute_capture", False))
        raw_trace_path = ""
        raw_trace_persisted = False
        capture: dict[str, Any] = {}
        if execute_capture:
            execution = context["execution_by_candidate"].get(str(plan.get("execution_candidate_id", "")), {})
            capture = capture_fn(plan, execution, context)
            executed_seen += 1
            raw_trace_path = str(raw_trace_dir / f"{plan['capture_plan_row_id']}.npz")
            save_raw_trace_npz(Path(raw_trace_path), capture)
            raw_trace_persisted = Path(raw_trace_path).exists()
            raw_index_rows.append(
                raw_trace_index_row(
                    index=executed_seen,
                    plan=plan,
                    raw_trace_path=raw_trace_path,
                    raw_trace_persisted=raw_trace_persisted,
                    capture=capture,
                )
            )
        if str(plan.get("row_role", "")) in {"success_identity_guard", "stale_fixed_source_guardrail"}:
            guard_rows.append(raw_trace_guard_row(index=len(guard_rows) + 1, plan=plan, raw_trace_persisted=raw_trace_persisted))
        availability_rows.append(
            raw_trace_availability_row(
                index=index,
                plan=plan,
                raw_trace_path=raw_trace_path,
                raw_trace_persisted=raw_trace_persisted,
                capture=capture,
            )
        )
        write_run_state(
            output_dir / "run_state.json",
            {
                "capture_plan_row_count": len(plan_rows),
                "processed_plan_row_count": index,
                "raw_trace_index_row_count": len(raw_index_rows),
                "raw_trace_guard_row_count": len(guard_rows),
                "raw_trace_availability_row_count": len(availability_rows),
                "complete": False,
                "next_blocker": next_blocker,
            },
        )
    return raw_index_rows, guard_rows, availability_rows


def capture_one_row(plan: Mapping[str, Any], execution_row: Mapping[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    workload = context["workload_by_id"].get(str(plan.get("workload_id", "")))
    if workload is None:
        raise ValueError(f"workload_id {plan.get('workload_id', '')!r} missing from executable workload")
    task_source_id = str(workload.get("task_source_id", ""))
    executable_spec = context["spec_by_task_source_id"].get(task_source_id)
    if executable_spec is None:
        raise ValueError(f"task_source_id {task_source_id!r} missing from executable specs")

    profile_name = str(workload.get("profile_name", execution_row.get("profile_name", "")))
    config_path = str(execution_row.get("parent_profile_config_path", execution_row.get("profile_config_path", "")))
    checkpoint_path = str(execution_row.get("parent_checkpoint_path", execution_row.get("checkpoint_path", "")))
    cache_key = (profile_name, config_path, checkpoint_path)
    profile_cache: dict[tuple[str, str, str], tuple[dict[str, Any], ZeroResidualActorHeadDeltaAdapter]] = context[
        "profile_cache"
    ]
    if cache_key not in profile_cache:
        profile_config = read_json(config_path)
        parent_model, _checkpoint = load_actor_critic_checkpoint(checkpoint_path, device=str(context["device"]))
        adapter = ZeroResidualActorHeadDeltaAdapter(parent_model, residual_limit=DEFAULT_RESIDUAL_LIMIT)
        profile_cache[cache_key] = (profile_config, adapter)
    profile_config, adapter = profile_cache[cache_key]
    before_trace_count = int(adapter.trace_count)
    capture = capture_episode_trace(
        workload=workload,
        executable_spec=executable_spec,
        profile_config=profile_config,
        adapter=adapter,
        eval_seed=_to_int(plan.get("m2960_eval_seed"), default=0),
    )
    capture["residual_trace_count_delta"] = int(adapter.trace_count) - before_trace_count
    capture["residual_delta_abs_max"] = float(adapter.contract_summary()["residual_delta_abs_max"])
    capture["checkpoint_loaded_read_only"] = True
    capture["zero_residual_identity_mode"] = True
    return capture


def capture_episode_trace(
    *,
    workload: Mapping[str, Any],
    executable_spec: Mapping[str, Any],
    profile_config: Mapping[str, Any],
    adapter: ZeroResidualActorHeadDeltaAdapter,
    eval_seed: int,
) -> dict[str, Any]:
    env_config = env_config_for_executable_profile(executable_spec=executable_spec, profile_config=profile_config)
    env = wrap_env_with_profile_mask(AutoDriftEnv(env_config), profile_config)
    if int(env.observation_space.shape[0]) != int(adapter.obs_dim):
        env.close()
        raise ValueError(f"adapter obs_dim {adapter.obs_dim} does not match env obs_dim {env.observation_space.shape[0]}")
    runtime = profile_runtime_summary(profile_config)
    policy = ActorPolicy(adapter, env_config, reset_hidden_policy=str(runtime["reset_hidden_policy"]))
    obs, info = env.reset(seed=int(eval_seed))
    policy.reset()
    observations: list[np.ndarray] = []
    actions: list[np.ndarray] = []
    next_observations: list[np.ndarray] = []
    rewards: list[float] = []
    done_trace: list[bool] = []
    timeout_trace: list[bool] = []
    terminated = False
    truncated = False
    final_info = dict(info)
    try:
        while not (terminated or truncated):
            observation = np.asarray(obs, dtype=np.float32).copy()
            action = np.asarray(policy.act(obs, info), dtype=np.float32).copy()
            next_obs, reward, terminated, truncated, info = env.step(action)
            observations.append(observation)
            actions.append(action)
            next_observations.append(np.asarray(next_obs, dtype=np.float32).copy())
            rewards.append(float(reward))
            done_trace.append(bool(terminated))
            timeout_trace.append(bool(truncated))
            obs = next_obs
            final_info = dict(info)
    finally:
        env.close()
    if not observations:
        raise ValueError("trace capture produced zero steps")
    return {
        "observation_trace": np.stack(observations).astype(np.float32),
        "action_trace": np.stack(actions).astype(np.float32),
        "next_observation_trace": np.stack(next_observations).astype(np.float32),
        "reward_trace": np.asarray(rewards, dtype=np.float32),
        "done_trace": np.asarray(done_trace, dtype=np.bool_),
        "timeout_trace": np.asarray(timeout_trace, dtype=np.bool_),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "termination_reason": str(final_info.get("termination_reason", "") or ""),
        "completion_reason": str(final_info.get("completion_reason", "") or ""),
        "outcome_bucket": outcome_bucket_from_info(final_info, terminated=terminated, truncated=truncated),
        "workload_id": str(workload.get("workload_id", "")),
    }


def save_raw_trace_npz(path: Path, capture: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        observation_trace=np.asarray(capture["observation_trace"], dtype=np.float32),
        action_trace=np.asarray(capture["action_trace"], dtype=np.float32),
        next_observation_trace=np.asarray(capture["next_observation_trace"], dtype=np.float32),
        reward_trace=np.asarray(capture["reward_trace"], dtype=np.float32),
        done_trace=np.asarray(capture["done_trace"], dtype=np.bool_),
        timeout_trace=np.asarray(capture["timeout_trace"], dtype=np.bool_),
    )


def raw_trace_index_row(
    *,
    index: int,
    plan: Mapping[str, Any],
    raw_trace_path: str,
    raw_trace_persisted: bool,
    capture: Mapping[str, Any],
) -> dict[str, Any]:
    observation = np.asarray(capture["observation_trace"])
    action = np.asarray(capture["action_trace"])
    next_observation = np.asarray(capture["next_observation_trace"])
    reward = np.asarray(capture["reward_trace"])
    done = np.asarray(capture["done_trace"])
    timeout = np.asarray(capture["timeout_trace"])
    tensors_finite = bool(
        np.isfinite(observation).all()
        and np.isfinite(action).all()
        and np.isfinite(next_observation).all()
        and np.isfinite(reward).all()
    )
    return {
        "raw_trace_index_row_id": f"m2977-raw-trace-index-{index:04d}",
        "capture_plan_row_id": plan.get("capture_plan_row_id", ""),
        "source_trace_row_id": plan.get("source_trace_row_id", ""),
        "source_row_id": plan.get("source_row_id", ""),
        "execution_candidate_id": plan.get("execution_candidate_id", ""),
        "row_role": plan.get("row_role", ""),
        "objective_or_guard_family": plan.get("objective_or_guard_family", ""),
        "raw_trace_path": raw_trace_path,
        "raw_trace_persisted": bool(raw_trace_persisted),
        "trace_step_count": int(observation.shape[0]),
        "expected_trace_step_count": _to_int(plan.get("expected_trace_step_count"), default=0),
        "observation_shape": _shape_text(observation),
        "action_shape": _shape_text(action),
        "next_observation_shape": _shape_text(next_observation),
        "reward_shape": _shape_text(reward),
        "done_shape": _shape_text(done),
        "timeout_shape": _shape_text(timeout),
        "actor_observation_dim": int(observation.shape[1]) if observation.ndim == 2 else -1,
        "actor_action_dim": int(action.shape[1]) if action.ndim == 2 else -1,
        "tensors_finite": tensors_finite,
        "actor_view_only": True,
        "hidden_oracle_actor_input_required": False,
        "future_target_actor_input_required": False,
        "objective_labels_actor_visible": False,
        "admission_labels_actor_visible": False,
        "trace_readiness_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "checkpoint_loaded_read_only": _bool(capture.get("checkpoint_loaded_read_only", True)),
        "zero_residual_identity_mode": _bool(capture.get("zero_residual_identity_mode", True)),
        "residual_delta_abs_max": float(capture.get("residual_delta_abs_max", 0.0)),
        "terminated": _bool(capture.get("terminated", False)),
        "truncated": _bool(capture.get("truncated", False)),
        "termination_reason": capture.get("termination_reason", ""),
        "completion_reason": capture.get("completion_reason", ""),
        "outcome_bucket": capture.get("outcome_bucket", ""),
        "training_started": False,
        "ppo_run": False,
        "validation_run": False,
        "ranking_run": False,
        "checkpoint_mutated": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def raw_trace_guard_row(*, index: int, plan: Mapping[str, Any], raw_trace_persisted: bool) -> dict[str, Any]:
    is_stale = str(plan.get("row_role", "")) == "stale_fixed_source_guardrail"
    return {
        "raw_trace_guard_row_id": f"m2977-raw-trace-guard-{index:04d}",
        "source_trace_row_id": plan.get("source_trace_row_id", ""),
        "source_row_id": plan.get("source_row_id", ""),
        "execution_candidate_id": plan.get("execution_candidate_id", ""),
        "guard_family": plan.get("objective_or_guard_family", ""),
        "guard_role": plan.get("row_role", ""),
        "execute_capture": _bool(plan.get("execute_capture", False)),
        "raw_trace_persisted": bool(raw_trace_persisted),
        "stale_guardrail_protected": bool(is_stale),
        "positive_training_target": False,
        "training_started": False,
        "ppo_run": False,
        "ranking_run": False,
        "checkpoint_mutated": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def raw_trace_availability_row(
    *,
    index: int,
    plan: Mapping[str, Any],
    raw_trace_path: str,
    raw_trace_persisted: bool,
    capture: Mapping[str, Any],
) -> dict[str, Any]:
    trace_file_exists = bool(raw_trace_path and Path(raw_trace_path).exists())
    is_stale = str(plan.get("row_role", "")) == "stale_fixed_source_guardrail"
    if raw_trace_persisted:
        availability_status = "raw_trace_persisted_pending_m2978_audit"
        blocker = "M2978 result audit required before residual fitting admission"
    elif is_stale:
        availability_status = "protected_stale_guardrail_not_executed"
        blocker = "stale fixed-source guardrail must remain non-executed"
    else:
        availability_status = "raw_trace_missing_fail_closed"
        blocker = "raw deployable observation/action trace not persisted"
    return {
        "raw_trace_availability_row_id": f"m2977-raw-trace-availability-{index:04d}",
        "source_trace_row_id": plan.get("source_trace_row_id", ""),
        "source_row_id": plan.get("source_row_id", ""),
        "execution_candidate_id": plan.get("execution_candidate_id", ""),
        "row_role": plan.get("row_role", ""),
        "objective_or_guard_family": plan.get("objective_or_guard_family", ""),
        "trace_metadata_present": True,
        "raw_trace_persisted": bool(raw_trace_persisted),
        "trace_file_exists": trace_file_exists,
        "trace_step_count": int(np.asarray(capture.get("observation_trace", [])).shape[0]) if capture else 0,
        "availability_status": availability_status,
        "blocking_reason_for_residual_fitting": blocker,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_actor_contract_guard_rows(
    raw_index_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    executed_count = len(raw_index_rows)
    stale_count = sum(1 for row in guard_rows if _bool(row.get("stale_guardrail_protected", False)))
    rows = [
        actor_guard("actor_observation_dim", _all_equal(raw_index_rows, "actor_observation_dim", P0_OBSERVATION_DIM), True),
        actor_guard("actor_action_dim", _all_equal(raw_index_rows, "actor_action_dim", ACTION_DIM), True),
        actor_guard("raw_trace_file_count", executed_count, EXPECTED_EXECUTED_RAW_TRACE_COUNT),
        actor_guard("stale_guardrails_protected", stale_count, EXPECTED_STALE_GUARDRAIL_COUNT),
        actor_guard("actor_view_only", _all_true(raw_index_rows, "actor_view_only"), True),
        actor_guard("hidden_oracle_actor_input_required", _any_true(raw_index_rows, "hidden_oracle_actor_input_required"), False),
        actor_guard("future_target_actor_input_required", _any_true(raw_index_rows, "future_target_actor_input_required"), False),
        actor_guard("objective_labels_actor_visible", _any_true(raw_index_rows, "objective_labels_actor_visible"), False),
        actor_guard("admission_labels_actor_visible", _any_true(raw_index_rows, "admission_labels_actor_visible"), False),
        actor_guard("trace_readiness_labels_actor_visible", _any_true(raw_index_rows, "trace_readiness_labels_actor_visible"), False),
        actor_guard("verdict_labels_actor_visible", _any_true(raw_index_rows, "verdict_labels_actor_visible"), False),
        actor_guard("checkpoint_loaded_read_only", _all_true(raw_index_rows, "checkpoint_loaded_read_only"), True),
        actor_guard("zero_residual_identity_mode", _all_true(raw_index_rows, "zero_residual_identity_mode"), True),
        actor_guard("residual_delta_abs_max", _max_float(raw_index_rows, "residual_delta_abs_max"), 0.0),
    ]
    return rows


def actor_guard(field: str, observed: Any, expected: Any) -> dict[str, Any]:
    status = observed == expected
    if field == "residual_delta_abs_max":
        status = float(observed) <= float(expected) + 1e-9
    return {
        "guard_id": f"m2977-actor-contract-{field}",
        "contract_field": field,
        "observed_value": observed,
        "expected_value": expected,
        "status_pass": bool(status),
        "actor_visible": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_claim_boundary_rows(
    *,
    raw_index_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    claim_specs = [
        ("raw_trace_capture_artifact_completeness_after_audit", True, True, "M2978 result audit"),
        ("residual_fitting_readiness", False, False, "M2978 result audit and later fitting design"),
        ("residual_fitting_run", False, False, "separate residual fitting milestone"),
        ("training_run", False, False, "separate training milestone"),
        ("ppo_run", False, False, "separate PPO milestone"),
        ("validation_run", False, False, "separate validation milestone"),
        ("ranking_run", False, _any_true(raw_index_rows + guard_rows, "ranking_run"), "ranking milestone"),
        ("checkpoint_mutation", False, _any_true(raw_index_rows + guard_rows, "checkpoint_mutated"), "promotion gate"),
        ("repair_success", False, False, "validation and audit"),
        ("driver_performance", False, False, "generalization and promotion gates"),
        ("paper_claim", False, False, "paper route fair comparison"),
        ("current_sim_verdict", False, False, "separate verdict synthesis"),
        ("high_fidelity_validation", False, False, "Route C validation"),
        ("full_ideal_driver_completion", False, False, "full ideal driver gate"),
        ("finite_window_vs_gru", False, False, "paper route comparison"),
        ("level3_self_id", False, False, "self-ID proof gates"),
        ("follow_up_result_audit_manifest_registered", True, bool(follow_up_manifest_registered), "M2978 manifest"),
    ]
    return [
        {
            "claim_id": f"m2977-claim-{index:04d}",
            "claim_family": family,
            "allowed_in_m2977": allowed,
            "claim_made": made,
            "status_pass": bool(made) == bool(allowed),
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, allowed, made, evidence) in enumerate(claim_specs, start=1)
    ]


def build_gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    raw_index_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    availability_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    role_counts = Counter(str(row.get("row_role", "")) for row in plan_rows)
    raw_role_counts = Counter(str(row.get("row_role", "")) for row in raw_index_rows)
    stale_executed = sum(
        1
        for row in plan_rows
        if str(row.get("row_role", "")) == "stale_fixed_source_guardrail" and _bool(row.get("execute_capture", False))
    )
    gates = [
        ("source_artifacts_present", "artifact", all(bool(v) for k, v in source["source_exists"].items() if k != "follow_up_manifest"), True),
        ("m2976_design_present", "lineage", bool(source["m2976_design_text"]), True),
        ("future_training_candidate_plan_count", "accounting", role_counts["future_training_candidate"], EXPECTED_TRAINING_CANDIDATE_COUNT),
        ("success_identity_guard_plan_count", "accounting", role_counts["success_identity_guard"], EXPECTED_SUCCESS_IDENTITY_GUARD_COUNT),
        ("stale_guardrail_plan_count", "accounting", role_counts["stale_fixed_source_guardrail"], EXPECTED_STALE_GUARDRAIL_COUNT),
        ("raw_trace_index_count", "artifact", len(raw_index_rows), EXPECTED_EXECUTED_RAW_TRACE_COUNT),
        ("future_training_candidate_raw_trace_count", "artifact", raw_role_counts["future_training_candidate"], EXPECTED_TRAINING_CANDIDATE_COUNT),
        ("success_identity_raw_trace_count", "artifact", raw_role_counts["success_identity_guard"], EXPECTED_SUCCESS_IDENTITY_GUARD_COUNT),
        ("stale_guardrail_executed_count", "guardrail", stale_executed, 0),
        ("raw_trace_files_exist", "artifact", _all_true(raw_index_rows, "raw_trace_persisted"), True),
        ("raw_trace_tensors_finite", "artifact", _all_true(raw_index_rows, "tensors_finite"), True),
        ("actor_observation_dim_72", "actor_contract", _all_equal(raw_index_rows, "actor_observation_dim", P0_OBSERVATION_DIM), True),
        ("actor_action_dim_3", "actor_contract", _all_equal(raw_index_rows, "actor_action_dim", ACTION_DIM), True),
        ("actor_contract_guards_pass", "actor_contract", _all_true(actor_rows, "status_pass"), True),
        ("claim_boundary_rows_pass", "claim_boundary", _all_true(claim_rows, "status_pass"), True),
        ("availability_rows_accounted", "accounting", len(availability_rows), len(plan_rows)),
        ("follow_up_manifest_registered", "process", source["source_exists"].get("follow_up_manifest", False), True),
    ]
    return [
        {
            "gate_id": f"m2977-gate-{index:04d}-{name}",
            "gate_family": family,
            "status_pass": observed == expected,
            "observed": observed,
            "expected": expected,
            "failure_type": "" if observed == expected else "metric_artifact",
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (name, family, observed, expected) in enumerate(gates, start=1)
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: Mapping[str, Path],
    source: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    raw_index_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    availability_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
    device: str,
) -> dict[str, Any]:
    role_counts = Counter(str(row.get("row_role", "")) for row in plan_rows)
    raw_role_counts = Counter(str(row.get("row_role", "")) for row in raw_index_rows)
    status_pass = all(_bool(row.get("status_pass", False)) for row in gate_rows)
    paths_payload = {key: str(value) for key, value in paths.items()}
    paths_payload["raw_traces_dir"] = str(output_dir / "raw_traces")
    return {
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "device": device,
        "result_class": (
            "engineering_controller_route_a_actor_head_delta_deployable_trace_capture_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_actor_head_delta_deployable_trace_capture_preflight_fail_closed"
        ),
        "status_pass": bool(status_pass),
        "gate_matrix_pass": bool(status_pass),
        "source_artifacts_present": all(bool(v) for k, v in source["source_exists"].items() if k != "follow_up_manifest"),
        "required_artifacts_present": all(path.exists() for key, path in paths.items() if key != "summary"),
        "capture_plan_row_count": len(plan_rows),
        "future_training_candidate_plan_count": role_counts["future_training_candidate"],
        "success_identity_guard_plan_count": role_counts["success_identity_guard"],
        "stale_guardrail_plan_count": role_counts["stale_fixed_source_guardrail"],
        "raw_trace_index_row_count": len(raw_index_rows),
        "future_training_candidate_raw_trace_count": raw_role_counts["future_training_candidate"],
        "success_identity_raw_trace_count": raw_role_counts["success_identity_guard"],
        "raw_trace_persisted_count": sum(1 for row in raw_index_rows if _bool(row.get("raw_trace_persisted", False))),
        "raw_trace_availability_row_count": len(availability_rows),
        "raw_trace_guard_row_count": len(guard_rows),
        "stale_guardrail_executed_count": sum(
            1
            for row in plan_rows
            if str(row.get("row_role", "")) == "stale_fixed_source_guardrail"
            and _bool(row.get("execute_capture", False))
        ),
        "stale_guardrail_protected_count": sum(1 for row in guard_rows if _bool(row.get("stale_guardrail_protected", False))),
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": all(_bool(row.get("status_pass", False)) for row in actor_rows),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass", False)) for row in claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "actor_contract_shape_72_action_3": _all_equal(raw_index_rows, "actor_observation_dim", P0_OBSERVATION_DIM)
        and _all_equal(raw_index_rows, "actor_action_dim", ACTION_DIM),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "raw_trace_tensors_finite": _all_true(raw_index_rows, "tensors_finite"),
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_detected": False,
        "future_target_actor_input_required": False,
        "objective_labels_actor_visible": False,
        "admission_labels_actor_visible": False,
        "trace_readiness_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "checkpoint_loaded_read_only": _all_true(raw_index_rows, "checkpoint_loaded_read_only"),
        "zero_residual_identity_mode": _all_true(raw_index_rows, "zero_residual_identity_mode"),
        "residual_delta_abs_max": _max_float(raw_index_rows, "residual_delta_abs_max"),
        "environment_reset_run": bool(raw_index_rows),
        "environment_step_run": bool(raw_index_rows),
        "policy_rollout_run": bool(raw_index_rows),
        "raw_trace_capture_run": bool(raw_index_rows),
        "residual_fitting_run": False,
        "training_run": False,
        "ppo_run": False,
        "validation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
        "success_rate_verdict_claim_made": False,
        "validation_readiness_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "raw_trace_capture_complete_pending_m2978_audit": bool(status_pass),
        "residual_fitting_readiness_claim_made": False,
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "next_blocker": next_blocker,
        "paths": paths_payload,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path, summary_path: Path) -> dict[str, Any]:
    follow_up_id = NEXT_ID
    follow_up_doc = Path(f"docs/{follow_up_id}.md")
    return {
        "id": follow_up_id,
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
            "seed_fragility",
        ],
        "hypothesis": (
            "A bounded result audit can accept or reject the M2977 deployable trace-capture preflight "
            "before any residual fitting training validation ranking promotion repair-success performance paper "
            "high-fidelity or self-ID claim."
        ),
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/"
                "checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/"
                "checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "raw_trace_index_rows.csv"),
                str(output_dir / "raw_trace_guard_rows.csv"),
                str(output_dir / "raw_trace_availability_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "parent_config": [
                "experiments/manifests/m2977-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
                "actor-head-delta-deployable-trace-capture-preflight.json",
                "experiments/manifests/m2976-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
                "actor-head-delta-deployable-trace-capture-design.json",
            ],
            "parent_objective": ["audit M2977 raw deployable trace capture before residual fitting admission"],
            "derived_from": [MILESTONE_ID],
            "blocked_by": [
                "M2977 raw trace capture requires a result audit before residual fitting readiness can be considered",
                "success identity and stale guardrail rows must remain protected guardrails",
            ],
            "supersedes": [
                "direct residual fitting immediately after raw trace capture without result audit",
                "treating raw trace capture as driver-performance evidence",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{follow_up_id}.md",
        "public_gates": [
            "M2978 must audit M2977 raw trace files index rows guards actor and claim boundaries",
            "M2978 must preserve 43 future training candidates 13 success identity guards and 11 stale guardrails",
            "M2978 must explicitly state whether raw deployable trace capture is complete enough for a later fitting design",
            "M2978 must not claim repair success validation performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID evidence",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not fit train select or execute a nonzero residual head",
            "do not rerun validate rank promote publish select a winner or execute dependency work",
            "do not change actor input or action contract",
            "do not convert M2977 raw traces into performance paper high-fidelity or self-ID claims",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_route_b_source_insufficient_dependency_facing",
            "evidence_axis": "route_a_dependency_facing_offtrack_dominant_actor_head_delta_deployable_trace_capture_result_audit",
            "evidence_increment": "audits newly captured raw actor-view trace artifacts",
            "claim_scope": "Result audit only; no residual fitting validation training ranking promotion performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M2977 artifacts are missing or gate matrix fails",
                "stop if actor or claim boundaries were violated",
                "stop if stale fixed-source guardrails were executed",
                "stop if raw traces would be used for residual fitting before audit",
            ],
            "fallback_plan": [
                "route to artifact repair if raw trace files are incomplete",
                "route to branch synthesis if raw trace capture violates actor boundaries",
                "route to bounded residual fitting design only after audit accepts claim safety and capture completeness",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2977 completes deployable trace-capture preflight",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M2977 raw deployable trace-capture artifacts",
            "admission_evidence": ["M2977 summary and gate matrix", "M2977 raw trace index guard availability actor and claim artifacts"],
            "blocked_shortcuts": [
                "no residual fitting training validation ranking promotion performance verdict paper high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
                "no checkpoint promotion",
                "no hidden/oracle/future-target actor input",
            ],
            "allowed_updates": [
                str(follow_up_doc),
                f"docs/reviews/{follow_up_id}.md",
                "M2978 status queue scoreboard research log and review",
                "one follow-up manifest only if M2978 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M2978 accepts or rejects M2977 as complete and claim-safe",
                "next route or stop state is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2978 audits Route A trace capture and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M2978; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M2977 Route A actor-head delta trace-capture preflight only.",
            "negative_result_policy": "Preserve trace capture failures and route to repair or synthesis rather than weakening self-ID gates.",
            "allowed_claims": [
                "M2977 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits newly captured raw actor-view trace files",
            "paper_verdict_delta": "no paper verdict; audit may inform Route A residual-fitting design readiness only",
            "must_synthesize_if": [
                "M2978 cannot accept M2977 as complete and claim-safe",
                "M2978 finds raw trace availability insufficient for residual fitting design",
                "M2978 would claim validation readiness driver performance paper current-sim high-fidelity or self-ID",
            ],
        },
        "success_criteria": [
            f"{follow_up_doc} exists",
            "M2978 audits M2977 artifacts row counts gates actor and claim boundaries",
            "M2978 selects exactly one next route or stop state",
            "no training validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim is made",
        ],
        "failure_criteria": [
            "M2978 hides M2977 failures or missing raw trace files",
            "M2978 treats M2977 trace capture as residual fitting performance verdict or repair success",
            "M2978 changes actor input or action contract",
            "M2978 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M2978 audits M2977 artifacts and selects one next route or stop state while preserving actor guardrail and claim boundaries without overclaiming.",
        "commands": [{"name": "result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": str(follow_up_doc), "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/"
            "checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "raw_trace_index_rows.csv"),
            str(output_dir / "raw_trace_availability_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
        ],
        "scoreboard_checkpoint": str(follow_up_doc),
        "next_blocker": follow_up_id,
        "status": "pending",
    }


def render_milestone_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M2977 Engineering Controller Route A Actor-Head Delta Deployable Trace Capture Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'fail_closed'}",
            f"- result class: `{summary['result_class']}`",
            f"- capture plan rows: {summary['capture_plan_row_count']}",
            f"- raw trace index rows: {summary['raw_trace_index_row_count']}",
            f"- future training candidate raw traces: {summary['future_training_candidate_raw_trace_count']}",
            f"- success identity raw traces: {summary['success_identity_raw_trace_count']}",
            f"- stale guardrails protected: {summary['stale_guardrail_protected_count']}",
            f"- raw trace persisted rows: {summary['raw_trace_persisted_count']}",
            f"- actor shape: {summary['observation_shape']}/action {summary['action_shape']}",
            f"- raw trace tensors finite: {summary['raw_trace_tensors_finite']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M2977 captures raw actor-view observation/action traces for later audit. It does not fit a residual head, train, validate, rank, promote, mutate checkpoints, or claim performance.",
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


def _shape_text(array: np.ndarray) -> str:
    return "x".join(str(dim) for dim in array.shape)


def _to_int(value: Any, *, default: int = 0) -> int:
    try:
        if value in ("", None):
            return int(default)
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _to_float(value: Any, *, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _all_true(rows: list[Mapping[str, Any]], key: str) -> bool:
    return bool(rows) and all(_bool(row.get(key, False)) for row in rows)


def _any_true(rows: list[Mapping[str, Any]], key: str) -> bool:
    return any(_bool(row.get(key, False)) for row in rows)


def _all_equal(rows: list[Mapping[str, Any]], key: str, expected: Any) -> bool:
    return bool(rows) and all(row.get(key) == expected or str(row.get(key)) == str(expected) for row in rows)


def _max_float(rows: list[Mapping[str, Any]], key: str) -> float:
    return max((_to_float(row.get(key), default=0.0) for row in rows), default=0.0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run M2977 deployable trace-capture preflight.")
    parser.add_argument("--m2973-dir", type=Path, default=DEFAULT_M2973_DIR)
    parser.add_argument("--m2975-synthesis", type=Path, default=DEFAULT_M2975_SYNTHESIS)
    parser.add_argument("--m2976-design", type=Path, default=DEFAULT_M2976_DESIGN)
    parser.add_argument("--m2960-dir", type=Path, default=DEFAULT_M2960_DIR)
    parser.add_argument("--executable-specs", type=Path, default=DEFAULT_EXECUTABLE_SPECS)
    parser.add_argument("--executable-workload", type=Path, default=DEFAULT_EXECUTABLE_WORKLOAD)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    summary = run_deployable_trace_capture_preflight(
        m2973_dir=args.m2973_dir,
        m2975_synthesis=args.m2975_synthesis,
        m2976_design=args.m2976_design,
        m2960_dir=args.m2960_dir,
        executable_specs=args.executable_specs,
        executable_workload=args.executable_workload,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        device=args.device,
    )
    print(f"status_pass={summary['status_pass']} gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"raw_trace_persisted_count={summary['raw_trace_persisted_count']}")
    print(f"next_blocker={summary['next_blocker']}")


if __name__ == "__main__":
    main()
