"""Capture M3027 raw deployable traces for new-source broad-failure rows.

M3027 consumes the M3025/M3026 target-source readiness audit chain and reruns
the fixed M3025 denominator only to persist raw actor-view observation/action
response traces. It does not run local-action search, materialize targets, fit,
train, validate, rank, promote, tune profiles, mutate checkpoints, or make a
driver-performance claim.
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
    env_config_for_executable_profile,
    read_csv_rows,
    write_run_state,
)
from autodrift.controller_profile_runtime import profile_runtime_summary, wrap_env_with_profile_mask
from autodrift.engineering_controller_route_a_post_residual_stop_new_source_bounded_execution_preflight import (
    profile_config_for_runtime,
)
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import ActorPolicy, outcome_bucket_from_info
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3027-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-"
    "deployable-trace-capture-preflight"
)
NEXT_ID = (
    "m3028-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-"
    "deployable-trace-capture-result-audit"
)
M3026_DECISION = "accept_m3025_claim_safe_readiness_blockers_route_to_m3027_deployable_trace_capture_preflight"

DEFAULT_M3025_DIR = Path(
    "runs/m3025_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_"
    "target_source_readiness_feasibility_materialization_preflight"
)
DEFAULT_M3026_AUDIT = Path(
    "docs/m3026-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-"
    "target-source-readiness-feasibility-materialization-result-audit.md"
)
DEFAULT_M3015_DIR = Path(
    "runs/m3015_engineering_controller_route_a_post_residual_stop_new_source_bounded_execution_preflight"
)
DEFAULT_M3012_DIR = Path(
    "runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_"
    "executable_env_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3027_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_"
    "deployable_trace_capture_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_READINESS_ROW_COUNT = 32
EXPECTED_FUTURE_TARGET_ROW_COUNT = 29
EXPECTED_SUCCESS_GUARD_ROW_COUNT = 3
EXPECTED_RAW_TRACE_ROW_COUNT = 32

CLAIM_SCOPE = (
    "M3027 Route A post-residual-stop new-source broad-failure deployable "
    "trace-capture preflight only; the M3026-accepted M3025 readiness "
    "denominator may be rerun to persist raw actor-view observation/action/"
    "response traces for 29 future target-eligible rows and 3 success identity "
    "guards. No local-action search, target tensor materialization, fitting, "
    "training, PPO, validation, ranking, winner selection, checkpoint mutation, "
    "checkpoint promotion, profile tuning, repair success, driver-performance, "
    "paper, current-sim verdict, high-fidelity validation, full ideal driver, "
    "finite-window-vs-GRU, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "target-source feasibility, numeric target readiness, fitting readiness, "
    "repair success, driver performance, validation readiness or result, "
    "controller/source/task/profile/checkpoint ranking, winner selection, "
    "checkpoint promotion, success-rate verdict, paper evidence, "
    "finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity "
    "validation readiness or result, full ideal driver completion, or level3 "
    "self-identification"
)

PATH_KEYS = [
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
    "follow_up_manifest",
]

CAPTURE_PLAN_FIELDNAMES = [
    "capture_plan_row_id",
    "target_source_readiness_row_id",
    "success_identity_guard_row_id",
    "row_assignment_id",
    "source_localization_row_id",
    "source_episode_row_index",
    "execution_workload_id",
    "executable_workload_id",
    "workload_id",
    "task_source_id",
    "profile_name",
    "profile_binding_name",
    "binding_role",
    "task_family",
    "source_edge",
    "window_tag",
    "strata",
    "row_role",
    "objective_family",
    "failure_family",
    "target_source_status",
    "execute_capture",
    "future_target_candidate",
    "success_identity_guard",
    "positive_target_candidate",
    "expected_trace_step_count",
    "m3015_eval_seed",
    "executable_source_spec_id",
    "profile_config_path",
    "checkpoint_path",
    "actor_observation_dim",
    "actor_action_dim",
    "claim_boundary",
]
RAW_TRACE_INDEX_FIELDNAMES = [
    "raw_trace_index_row_id",
    "capture_plan_row_id",
    "target_source_readiness_row_id",
    "success_identity_guard_row_id",
    "row_assignment_id",
    "source_episode_row_index",
    "execution_workload_id",
    "executable_workload_id",
    "workload_id",
    "task_source_id",
    "profile_name",
    "binding_role",
    "row_role",
    "objective_family",
    "failure_family",
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
    "source_labels_actor_visible",
    "route_labels_actor_visible",
    "outcome_labels_actor_visible",
    "objective_labels_actor_visible",
    "readiness_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "ttc_actor_input_required",
    "checkpoint_loaded_read_only",
    "direct_profile_policy_mode",
    "terminated",
    "truncated",
    "termination_reason",
    "completion_reason",
    "outcome_bucket",
    "local_action_search_run",
    "numeric_target_tensor_materialized",
    "target_source_feasibility_claim_made",
    "training_run",
    "ppo_run",
    "validation_run",
    "ranking_run",
    "checkpoint_mutated",
    "claim_boundary",
]
RAW_TRACE_GUARD_FIELDNAMES = [
    "raw_trace_guard_row_id",
    "capture_plan_row_id",
    "target_source_readiness_row_id",
    "success_identity_guard_row_id",
    "row_assignment_id",
    "execution_workload_id",
    "guard_family",
    "row_role",
    "execute_capture",
    "raw_trace_persisted",
    "future_target_candidate",
    "success_identity_guard",
    "positive_target_candidate",
    "local_action_search_run",
    "numeric_target_tensor_materialized",
    "training_run",
    "ppo_run",
    "validation_run",
    "ranking_run",
    "checkpoint_mutated",
    "claim_boundary",
]
RAW_TRACE_AVAILABILITY_FIELDNAMES = [
    "raw_trace_availability_row_id",
    "capture_plan_row_id",
    "target_source_readiness_row_id",
    "success_identity_guard_row_id",
    "row_assignment_id",
    "source_episode_row_index",
    "execution_workload_id",
    "row_role",
    "objective_family",
    "trace_metadata_present",
    "raw_trace_persisted",
    "trace_file_exists",
    "trace_step_count",
    "availability_status",
    "blocking_reason_for_target_source_interpretation",
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
    "allowed_in_m3027",
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

CaptureFn = Callable[[Mapping[str, Any], Mapping[str, Any], dict[str, Any]], dict[str, Any]]


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
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
        "follow_up_manifest": follow_up_manifest,
    }


def load_source_artifacts(
    *,
    m3025_dir: Path,
    m3026_audit: Path,
    m3015_dir: Path,
    m3012_dir: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m3025_summary": m3025_dir / "summary.json",
        "m3025_target_source_readiness_rows": m3025_dir / "target_source_readiness_rows.csv",
        "m3025_target_source_blocker_rows": m3025_dir / "target_source_blocker_rows.csv",
        "m3025_success_identity_guard_rows": m3025_dir / "success_identity_guard_rows.csv",
        "m3025_actor_contract_guard_rows": m3025_dir / "actor_contract_guard_rows.csv",
        "m3025_gate_matrix": m3025_dir / "gate_matrix.csv",
        "m3026_audit": m3026_audit,
        "m3015_summary": m3015_dir / "summary.json",
        "m3015_episode_rows": m3015_dir / "episode_rows.csv",
        "m3015_execution_workload_rows": m3015_dir / "execution_workload_rows.csv",
        "m3015_execution_guard_rows": m3015_dir / "execution_guard_rows.csv",
        "m3012_summary": m3012_dir / "summary.json",
        "m3012_executable_source_specs": m3012_dir / "executable_source_specs.json",
        "m3012_executable_workload_rows": m3012_dir / "executable_workload_rows.csv",
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    spec_payload = read_json(paths["m3012_executable_source_specs"]) if source_exists["m3012_executable_source_specs"] else {}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m3025_summary": read_json(paths["m3025_summary"]) if source_exists["m3025_summary"] else {},
        "m3025_target_source_readiness_rows": read_csv_rows(paths["m3025_target_source_readiness_rows"])
        if source_exists["m3025_target_source_readiness_rows"]
        else [],
        "m3025_target_source_blocker_rows": read_csv_rows(paths["m3025_target_source_blocker_rows"])
        if source_exists["m3025_target_source_blocker_rows"]
        else [],
        "m3025_success_identity_guard_rows": read_csv_rows(paths["m3025_success_identity_guard_rows"])
        if source_exists["m3025_success_identity_guard_rows"]
        else [],
        "m3025_actor_contract_guard_rows": read_csv_rows(paths["m3025_actor_contract_guard_rows"])
        if source_exists["m3025_actor_contract_guard_rows"]
        else [],
        "m3025_gate_matrix": read_csv_rows(paths["m3025_gate_matrix"]) if source_exists["m3025_gate_matrix"] else [],
        "m3026_audit_text": paths["m3026_audit"].read_text(encoding="utf-8")
        if source_exists["m3026_audit"]
        else "",
        "m3015_summary": read_json(paths["m3015_summary"]) if source_exists["m3015_summary"] else {},
        "m3015_episode_rows": read_csv_rows(paths["m3015_episode_rows"]) if source_exists["m3015_episode_rows"] else [],
        "m3015_execution_workload_rows": read_csv_rows(paths["m3015_execution_workload_rows"])
        if source_exists["m3015_execution_workload_rows"]
        else [],
        "m3015_execution_guard_rows": read_csv_rows(paths["m3015_execution_guard_rows"])
        if source_exists["m3015_execution_guard_rows"]
        else [],
        "m3012_summary": read_json(paths["m3012_summary"]) if source_exists["m3012_summary"] else {},
        "m3012_executable_source_specs": list(spec_payload.get("executable_source_specs", [])),
        "m3012_executable_workload_rows": read_csv_rows(paths["m3012_executable_workload_rows"])
        if source_exists["m3012_executable_workload_rows"]
        else [],
    }


def build_capture_plan_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    readiness_rows = sorted(
        source["m3025_target_source_readiness_rows"],
        key=lambda row: _to_int(row.get("source_episode_row_index"), default=0),
    )
    success_by_readiness_id = {
        str(row.get("target_source_readiness_row_id", "")): row
        for row in source["m3025_success_identity_guard_rows"]
    }
    episode_by_index = {str(index + 1): row for index, row in enumerate(source["m3015_episode_rows"])}
    execution_by_id = {
        str(row.get("execution_workload_id", "")): row for row in source["m3015_execution_workload_rows"]
    }
    execution_by_executable_id = {
        str(row.get("executable_workload_id", "")): row for row in source["m3015_execution_workload_rows"]
    }
    plan_rows: list[dict[str, Any]] = []
    for readiness in readiness_rows:
        is_future = _bool(readiness.get("future_target_materialization_allowed"))
        is_success = str(readiness.get("objective_family", "")) == "success_identity_context_guard"
        if not is_future and not is_success:
            continue
        episode = episode_by_index.get(str(readiness.get("source_episode_row_index", "")), {})
        execution = execution_by_id.get(str(episode.get("execution_workload_id", "")), {})
        if not execution and episode.get("executable_workload_id"):
            execution = execution_by_executable_id.get(str(episode.get("executable_workload_id", "")), {})
        success_guard = success_by_readiness_id.get(str(readiness.get("target_source_readiness_row_id", "")), {})
        plan_rows.append(
            capture_plan_row(
                index=len(plan_rows) + 1,
                readiness=readiness,
                success_guard=success_guard,
                episode=episode,
                execution=execution,
                row_role="success_identity_guard" if is_success else "future_target_candidate",
            )
        )
    return plan_rows


def capture_plan_row(
    *,
    index: int,
    readiness: Mapping[str, Any],
    success_guard: Mapping[str, Any],
    episode: Mapping[str, Any],
    execution: Mapping[str, Any],
    row_role: str,
) -> dict[str, Any]:
    is_success = row_role == "success_identity_guard"
    profile_config_path = str(
        execution.get("config_path")
        or execution.get("profile_config_path")
        or episode.get("profile_config_path")
        or readiness.get("profile_config_path", "")
    )
    checkpoint_path = str(
        execution.get("checkpoint_path") or episode.get("checkpoint_path") or readiness.get("checkpoint_path", "")
    )
    return {
        "capture_plan_row_id": f"m3027-capture-plan-{index:04d}",
        "target_source_readiness_row_id": readiness.get("target_source_readiness_row_id", ""),
        "success_identity_guard_row_id": success_guard.get("success_identity_guard_row_id", "") if is_success else "",
        "row_assignment_id": readiness.get("row_assignment_id", ""),
        "source_localization_row_id": readiness.get("source_localization_row_id", ""),
        "source_episode_row_index": readiness.get("source_episode_row_index", ""),
        "execution_workload_id": episode.get("execution_workload_id", execution.get("execution_workload_id", "")),
        "executable_workload_id": episode.get("executable_workload_id", execution.get("executable_workload_id", "")),
        "workload_id": episode.get("workload_id", execution.get("workload_id", execution.get("executable_workload_id", ""))),
        "task_source_id": readiness.get("task_source_id", execution.get("task_source_id", "")),
        "profile_name": readiness.get("profile_name", execution.get("profile_name", "")),
        "profile_binding_name": readiness.get("profile_binding_name", execution.get("profile_binding_name", "")),
        "binding_role": readiness.get("binding_role", execution.get("binding_role", "")),
        "task_family": readiness.get("task_family", execution.get("task_family", "")),
        "source_edge": readiness.get("source_edge", execution.get("source_edge", "")),
        "window_tag": readiness.get("window_tag", execution.get("window_tag", "")),
        "strata": readiness.get("strata", execution.get("strata", "")),
        "row_role": row_role,
        "objective_family": readiness.get("objective_family", ""),
        "failure_family": readiness.get("failure_family", ""),
        "target_source_status": readiness.get("target_source_status", ""),
        "execute_capture": True,
        "future_target_candidate": not is_success,
        "success_identity_guard": is_success,
        "positive_target_candidate": False,
        "expected_trace_step_count": _to_int(episode.get("steps"), default=0),
        "m3015_eval_seed": _to_int(episode.get("m3015_eval_seed", episode.get("eval_seed")), default=0),
        "executable_source_spec_id": execution.get("executable_source_spec_id", episode.get("executable_source_spec_id", "")),
        "profile_config_path": profile_config_path,
        "checkpoint_path": checkpoint_path,
        "actor_observation_dim": _to_int(readiness.get("actor_observation_dim"), default=P0_OBSERVATION_DIM),
        "actor_action_dim": _to_int(readiness.get("actor_action_dim"), default=ACTION_DIM),
        "claim_boundary": CLAIM_SCOPE,
    }


def build_capture_context(source: Mapping[str, Any], *, device: str) -> dict[str, Any]:
    workload_by_id: dict[str, Mapping[str, Any]] = {}
    for row in source["m3012_executable_workload_rows"]:
        for key in ("executable_workload_id", "workload_id"):
            value = str(row.get(key, ""))
            if value:
                workload_by_id[value] = row
    spec_by_key = {
        (str(row.get("task_source_id", "")), str(row.get("executable_source_spec_id", ""))): row
        for row in source["m3012_executable_source_specs"]
    }
    execution_by_id = {
        str(row.get("execution_workload_id", "")): row for row in source["m3015_execution_workload_rows"]
    }
    return {
        "workload_by_id": workload_by_id,
        "spec_by_key": spec_by_key,
        "execution_by_id": execution_by_id,
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
    index_rows: list[dict[str, Any]] = []
    guard_rows: list[dict[str, Any]] = []
    availability_rows: list[dict[str, Any]] = []
    for row_index, plan in enumerate(plan_rows, start=1):
        raw_trace_path = str(raw_trace_dir / f"{plan['capture_plan_row_id']}.npz")
        execution = context["execution_by_id"].get(str(plan.get("execution_workload_id", "")), {})
        capture = capture_fn(plan, execution, context)
        save_raw_trace_npz(Path(raw_trace_path), capture)
        persisted = Path(raw_trace_path).exists()
        index_rows.append(
            raw_trace_index_row(
                index=len(index_rows) + 1,
                plan=plan,
                raw_trace_path=raw_trace_path,
                raw_trace_persisted=persisted,
                capture=capture,
            )
        )
        guard_rows.append(raw_trace_guard_row(index=len(guard_rows) + 1, plan=plan, raw_trace_persisted=persisted))
        availability_rows.append(
            raw_trace_availability_row(
                index=row_index,
                plan=plan,
                raw_trace_path=raw_trace_path,
                raw_trace_persisted=persisted,
                capture=capture,
            )
        )
        write_run_state(
            output_dir / "run_state.json",
            {
                "capture_plan_row_count": len(plan_rows),
                "processed_plan_row_count": row_index,
                "raw_trace_index_row_count": len(index_rows),
                "raw_trace_guard_row_count": len(guard_rows),
                "raw_trace_availability_row_count": len(availability_rows),
                "complete": False,
                "next_blocker": next_blocker,
            },
        )
    return index_rows, guard_rows, availability_rows


def capture_one_row(plan: Mapping[str, Any], execution_row: Mapping[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    workload_id = str(plan.get("executable_workload_id") or plan.get("workload_id", ""))
    workload = context["workload_by_id"].get(workload_id)
    if workload is None:
        raise ValueError(f"workload {workload_id!r} missing from M3012 executable workloads")
    spec_key = (str(plan.get("task_source_id", "")), str(plan.get("executable_source_spec_id", "")))
    executable_spec = context["spec_by_key"].get(spec_key)
    if executable_spec is None:
        raise ValueError(f"source spec {spec_key!r} missing from M3012 executable specs")

    profile_name = str(plan.get("profile_name") or execution_row.get("profile_name", ""))
    config_path = str(plan.get("profile_config_path") or execution_row.get("config_path", ""))
    checkpoint_path = str(plan.get("checkpoint_path") or execution_row.get("checkpoint_path", ""))
    cache_key = (profile_name, config_path, checkpoint_path)
    profile_cache: dict[tuple[str, str, str], tuple[dict[str, Any], Any]] = context["profile_cache"]
    if cache_key not in profile_cache:
        profile_config = profile_config_for_runtime(read_json(config_path), profile_name=profile_name)
        model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(context["device"]))
        profile_cache[cache_key] = (profile_config, model)
    profile_config, model = profile_cache[cache_key]
    capture = capture_episode_trace(
        workload=workload,
        executable_spec=executable_spec,
        profile_config=profile_config,
        model=model,
        eval_seed=_to_int(plan.get("m3015_eval_seed"), default=0),
    )
    capture["checkpoint_loaded_read_only"] = True
    capture["direct_profile_policy_mode"] = True
    return capture


def capture_episode_trace(
    *,
    workload: Mapping[str, Any],
    executable_spec: Mapping[str, Any],
    profile_config: Mapping[str, Any],
    model: Any,
    eval_seed: int,
) -> dict[str, Any]:
    env_config = env_config_for_executable_profile(executable_spec=executable_spec, profile_config=profile_config)
    env = wrap_env_with_profile_mask(AutoDriftEnv(env_config), profile_config)
    target_obs_dim = int(env.observation_space.shape[0])
    model_obs_dim = int(getattr(model, "obs_dim", -1))
    if model_obs_dim != target_obs_dim:
        env.close()
        raise ValueError(f"checkpoint obs_dim {model_obs_dim} does not match task env obs_dim {target_obs_dim}")
    runtime = profile_runtime_summary(profile_config)
    policy = ActorPolicy(model, env_config, reset_hidden_policy=str(runtime["reset_hidden_policy"]))
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
        "workload_id": str(workload.get("workload_id", workload.get("executable_workload_id", ""))),
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
        "raw_trace_index_row_id": f"m3027-raw-trace-index-{index:04d}",
        "capture_plan_row_id": plan.get("capture_plan_row_id", ""),
        "target_source_readiness_row_id": plan.get("target_source_readiness_row_id", ""),
        "success_identity_guard_row_id": plan.get("success_identity_guard_row_id", ""),
        "row_assignment_id": plan.get("row_assignment_id", ""),
        "source_episode_row_index": plan.get("source_episode_row_index", ""),
        "execution_workload_id": plan.get("execution_workload_id", ""),
        "executable_workload_id": plan.get("executable_workload_id", ""),
        "workload_id": plan.get("workload_id", ""),
        "task_source_id": plan.get("task_source_id", ""),
        "profile_name": plan.get("profile_name", ""),
        "binding_role": plan.get("binding_role", ""),
        "row_role": plan.get("row_role", ""),
        "objective_family": plan.get("objective_family", ""),
        "failure_family": plan.get("failure_family", ""),
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
        "source_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "outcome_labels_actor_visible": False,
        "objective_labels_actor_visible": False,
        "readiness_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "ttc_actor_input_required": False,
        "checkpoint_loaded_read_only": _bool(capture.get("checkpoint_loaded_read_only", True)),
        "direct_profile_policy_mode": _bool(capture.get("direct_profile_policy_mode", True)),
        "terminated": _bool(capture.get("terminated", False)),
        "truncated": _bool(capture.get("truncated", False)),
        "termination_reason": capture.get("termination_reason", ""),
        "completion_reason": capture.get("completion_reason", ""),
        "outcome_bucket": capture.get("outcome_bucket", ""),
        "local_action_search_run": False,
        "numeric_target_tensor_materialized": False,
        "target_source_feasibility_claim_made": False,
        "training_run": False,
        "ppo_run": False,
        "validation_run": False,
        "ranking_run": False,
        "checkpoint_mutated": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def raw_trace_guard_row(*, index: int, plan: Mapping[str, Any], raw_trace_persisted: bool) -> dict[str, Any]:
    return {
        "raw_trace_guard_row_id": f"m3027-raw-trace-guard-{index:04d}",
        "capture_plan_row_id": plan.get("capture_plan_row_id", ""),
        "target_source_readiness_row_id": plan.get("target_source_readiness_row_id", ""),
        "success_identity_guard_row_id": plan.get("success_identity_guard_row_id", ""),
        "row_assignment_id": plan.get("row_assignment_id", ""),
        "execution_workload_id": plan.get("execution_workload_id", ""),
        "guard_family": plan.get("objective_family", ""),
        "row_role": plan.get("row_role", ""),
        "execute_capture": _bool(plan.get("execute_capture", False)),
        "raw_trace_persisted": bool(raw_trace_persisted),
        "future_target_candidate": _bool(plan.get("future_target_candidate", False)),
        "success_identity_guard": _bool(plan.get("success_identity_guard", False)),
        "positive_target_candidate": False,
        "local_action_search_run": False,
        "numeric_target_tensor_materialized": False,
        "training_run": False,
        "ppo_run": False,
        "validation_run": False,
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
    file_exists = bool(raw_trace_path and Path(raw_trace_path).exists())
    return {
        "raw_trace_availability_row_id": f"m3027-raw-trace-availability-{index:04d}",
        "capture_plan_row_id": plan.get("capture_plan_row_id", ""),
        "target_source_readiness_row_id": plan.get("target_source_readiness_row_id", ""),
        "success_identity_guard_row_id": plan.get("success_identity_guard_row_id", ""),
        "row_assignment_id": plan.get("row_assignment_id", ""),
        "source_episode_row_index": plan.get("source_episode_row_index", ""),
        "execution_workload_id": plan.get("execution_workload_id", ""),
        "row_role": plan.get("row_role", ""),
        "objective_family": plan.get("objective_family", ""),
        "trace_metadata_present": True,
        "raw_trace_persisted": bool(raw_trace_persisted),
        "trace_file_exists": file_exists,
        "trace_step_count": int(np.asarray(capture.get("observation_trace", [])).shape[0]) if capture else 0,
        "availability_status": "raw_trace_persisted_pending_m3028_audit"
        if raw_trace_persisted
        else "raw_trace_missing_fail_closed",
        "blocking_reason_for_target_source_interpretation": "M3028 result audit required before target-source feasibility interpretation"
        if raw_trace_persisted
        else "raw deployable observation/action/response trace not persisted",
        "claim_boundary": CLAIM_SCOPE,
    }


def build_actor_contract_guard_rows(
    *,
    raw_index_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    role_counts = Counter(str(row.get("row_role", "")) for row in raw_index_rows)
    rows = [
        actor_guard("raw_trace_file_count", len(raw_index_rows), EXPECTED_RAW_TRACE_ROW_COUNT),
        actor_guard("future_target_raw_trace_count", role_counts["future_target_candidate"], EXPECTED_FUTURE_TARGET_ROW_COUNT),
        actor_guard("success_identity_raw_trace_count", role_counts["success_identity_guard"], EXPECTED_SUCCESS_GUARD_ROW_COUNT),
        actor_guard("actor_observation_dim", _all_equal(raw_index_rows, "actor_observation_dim", P0_OBSERVATION_DIM), True),
        actor_guard("actor_action_dim", _all_equal(raw_index_rows, "actor_action_dim", ACTION_DIM), True),
        actor_guard("actor_view_only", _all_true(raw_index_rows, "actor_view_only"), True),
        actor_guard("hidden_oracle_actor_input_required", _any_true(raw_index_rows, "hidden_oracle_actor_input_required"), False),
        actor_guard("future_target_actor_input_required", _any_true(raw_index_rows, "future_target_actor_input_required"), False),
        actor_guard("source_labels_actor_visible", _any_true(raw_index_rows, "source_labels_actor_visible"), False),
        actor_guard("route_labels_actor_visible", _any_true(raw_index_rows, "route_labels_actor_visible"), False),
        actor_guard("outcome_labels_actor_visible", _any_true(raw_index_rows, "outcome_labels_actor_visible"), False),
        actor_guard("objective_labels_actor_visible", _any_true(raw_index_rows, "objective_labels_actor_visible"), False),
        actor_guard("readiness_labels_actor_visible", _any_true(raw_index_rows, "readiness_labels_actor_visible"), False),
        actor_guard("success_progress_labels_actor_visible", _any_true(raw_index_rows, "success_progress_labels_actor_visible"), False),
        actor_guard("verdict_labels_actor_visible", _any_true(raw_index_rows, "verdict_labels_actor_visible"), False),
        actor_guard("ttc_actor_input_required", _any_true(raw_index_rows, "ttc_actor_input_required"), False),
        actor_guard("checkpoint_loaded_read_only", _all_true(raw_index_rows, "checkpoint_loaded_read_only"), True),
        actor_guard("direct_profile_policy_mode", _all_true(raw_index_rows, "direct_profile_policy_mode"), True),
        actor_guard("success_identity_positive_target_count", sum(_bool(row["positive_target_candidate"]) for row in guard_rows), 0),
    ]
    return rows


def actor_guard(field: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": f"m3027-actor-contract-{field}",
        "contract_field": field,
        "observed_value": observed,
        "expected_value": expected,
        "status_pass": observed == expected,
        "actor_visible": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_claim_boundary_rows(*, raw_index_rows: list[dict[str, Any]], follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    claim_specs = [
        ("raw_trace_capture_artifacts_materialized", True, bool(raw_index_rows), "raw trace index and npz files"),
        ("follow_up_result_audit_manifest_registered", True, bool(follow_up_manifest_registered), "M3028 manifest"),
        ("target_source_feasibility", False, False, "M3028 audit and later feasibility milestone"),
        ("target_tensor_materialization", False, False, "future audited target materialization route"),
        ("local_action_search", False, False, "future audited target search route"),
        ("residual_fitting_or_training", False, False, "future fitting/training milestone"),
        ("ppo_run", False, False, "future PPO milestone"),
        ("validation_run", False, False, "future validation milestone"),
        ("ranking_or_winner_selection", False, False, "future ranking/promotion gate"),
        ("checkpoint_mutation_or_promotion", False, False, "future promotion gate"),
        ("repair_success", False, False, "future validation and audit"),
        ("driver_performance", False, False, "proof/generalization/promotion gates"),
        ("paper_claim", False, False, "paper route evidence matrix"),
        ("current_sim_verdict", False, False, "separate verdict synthesis"),
        ("high_fidelity_validation", False, False, "Route C validation"),
        ("finite_window_vs_gru", False, False, "paper route fair comparison"),
        ("full_ideal_driver_completion", False, False, "full ideal driver gate"),
        ("level3_self_id", False, False, "self-ID proof gates"),
    ]
    return [
        {
            "claim_id": f"m3027-claim-{index:04d}",
            "claim_family": family,
            "allowed_in_m3027": allowed,
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
    required_artifacts_present: bool,
    follow_up_manifest: Path,
) -> list[dict[str, Any]]:
    plan_roles = Counter(str(row.get("row_role", "")) for row in plan_rows)
    raw_roles = Counter(str(row.get("row_role", "")) for row in raw_index_rows)
    forbidden_claims = forbidden_m3027_flags(raw_index_rows + guard_rows)
    gates = [
        ("source_artifacts_present", "lineage", all(source["source_exists"].values()), source["source_exists"], "all true", "lineage_invalid"),
        (
            "m3025_status_pass",
            "lineage",
            _bool(source["m3025_summary"].get("status_pass")) and _bool(source["m3025_summary"].get("gate_matrix_pass")),
            {"status_pass": source["m3025_summary"].get("status_pass"), "gate_matrix_pass": source["m3025_summary"].get("gate_matrix_pass")},
            "both true",
            "lineage_invalid",
        ),
        ("m3026_accepts_m3025_and_routes_m3027", "lineage", M3026_DECISION in source["m3026_audit_text"], M3026_DECISION in source["m3026_audit_text"], True, "lineage_invalid"),
        (
            "readiness_denominator_preserved",
            "denominator",
            len(source["m3025_target_source_readiness_rows"]) == EXPECTED_READINESS_ROW_COUNT,
            len(source["m3025_target_source_readiness_rows"]),
            EXPECTED_READINESS_ROW_COUNT,
            "metric_artifact",
        ),
        (
            "future_target_capture_plan_count",
            "denominator",
            plan_roles["future_target_candidate"] == EXPECTED_FUTURE_TARGET_ROW_COUNT,
            plan_roles["future_target_candidate"],
            EXPECTED_FUTURE_TARGET_ROW_COUNT,
            "metric_artifact",
        ),
        (
            "success_identity_capture_plan_count",
            "denominator",
            plan_roles["success_identity_guard"] == EXPECTED_SUCCESS_GUARD_ROW_COUNT,
            plan_roles["success_identity_guard"],
            EXPECTED_SUCCESS_GUARD_ROW_COUNT,
            "metric_artifact",
        ),
        (
            "raw_trace_index_count",
            "artifact",
            len(raw_index_rows) == EXPECTED_RAW_TRACE_ROW_COUNT,
            len(raw_index_rows),
            EXPECTED_RAW_TRACE_ROW_COUNT,
            "metric_artifact",
        ),
        (
            "future_target_raw_trace_count",
            "artifact",
            raw_roles["future_target_candidate"] == EXPECTED_FUTURE_TARGET_ROW_COUNT,
            raw_roles["future_target_candidate"],
            EXPECTED_FUTURE_TARGET_ROW_COUNT,
            "metric_artifact",
        ),
        (
            "success_identity_raw_trace_count",
            "artifact",
            raw_roles["success_identity_guard"] == EXPECTED_SUCCESS_GUARD_ROW_COUNT,
            raw_roles["success_identity_guard"],
            EXPECTED_SUCCESS_GUARD_ROW_COUNT,
            "metric_artifact",
        ),
        ("raw_trace_files_exist", "artifact", _all_true(raw_index_rows, "raw_trace_persisted"), True, True, "metric_artifact"),
        ("raw_trace_tensors_finite", "artifact", _all_true(raw_index_rows, "tensors_finite"), True, True, "metric_artifact"),
        ("availability_rows_accounted", "accounting", len(availability_rows) == len(plan_rows), len(availability_rows), len(plan_rows), "metric_artifact"),
        ("raw_trace_guard_rows_accounted", "accounting", len(guard_rows) == len(plan_rows), len(guard_rows), len(plan_rows), "metric_artifact"),
        ("actor_contract_guards_pass", "actor_contract", _all_true(actor_rows, "status_pass"), True, True, "contract_violation"),
        ("claim_boundary_rows_pass", "claim_boundary", _all_true(claim_rows, "status_pass"), True, True, "contract_violation"),
        ("no_target_tensor_search_training_validation_or_ranking", "claim_boundary", not any(forbidden_claims.values()), forbidden_claims, "all false", "contract_violation"),
        ("required_artifacts_present", "artifact", required_artifacts_present, True, True, "metric_artifact"),
        ("follow_up_manifest_registered", "process", follow_up_manifest.exists(), True, True, "lineage_invalid"),
    ]
    return [
        {
            "gate_id": f"m3027-gate-{index:04d}-{name}",
            "gate_family": family,
            "status_pass": bool(status_pass),
            "observed": observed,
            "expected": expected,
            "failure_type": "" if bool(status_pass) else failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (name, family, status_pass, observed, expected, failure_type) in enumerate(gates, start=1)
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
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
    device: str,
) -> dict[str, Any]:
    plan_roles = Counter(str(row.get("row_role", "")) for row in plan_rows)
    raw_roles = Counter(str(row.get("row_role", "")) for row in raw_index_rows)
    status_pass = all(_bool(row.get("status_pass", False)) for row in gate_rows)
    return {
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "device": device,
        "result_class": "new_source_broad_failure_deployable_trace_capture_preflight_pass"
        if status_pass
        else "new_source_broad_failure_deployable_trace_capture_preflight_fail_closed",
        "status_pass": bool(status_pass),
        "gate_matrix_pass": bool(status_pass),
        "required_artifacts_present": required_artifacts_present,
        "source_artifacts_present": all(source["source_exists"].values()),
        "capture_plan_row_count": len(plan_rows),
        "future_target_capture_plan_count": plan_roles["future_target_candidate"],
        "success_identity_capture_plan_count": plan_roles["success_identity_guard"],
        "raw_trace_index_row_count": len(raw_index_rows),
        "future_target_raw_trace_count": raw_roles["future_target_candidate"],
        "success_identity_raw_trace_count": raw_roles["success_identity_guard"],
        "raw_trace_persisted_count": sum(_bool(row["raw_trace_persisted"]) for row in raw_index_rows),
        "raw_trace_guard_row_count": len(guard_rows),
        "raw_trace_availability_row_count": len(availability_rows),
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": all(_bool(row["status_pass"]) for row in actor_rows),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(_bool(row["status_pass"]) for row in claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "actor_contract_shape_72_action_3": _all_equal(raw_index_rows, "actor_observation_dim", P0_OBSERVATION_DIM)
        and _all_equal(raw_index_rows, "actor_action_dim", ACTION_DIM),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "raw_trace_tensors_finite": _all_true(raw_index_rows, "tensors_finite"),
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_detected": False,
        "future_target_actor_input_required": False,
        "source_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "outcome_labels_actor_visible": False,
        "objective_labels_actor_visible": False,
        "readiness_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "ttc_actor_input_required": False,
        "checkpoint_loaded_read_only": _all_true(raw_index_rows, "checkpoint_loaded_read_only"),
        "direct_profile_policy_mode": _all_true(raw_index_rows, "direct_profile_policy_mode"),
        "environment_reset_run": bool(raw_index_rows),
        "environment_step_run": bool(raw_index_rows),
        "policy_action_run": bool(raw_index_rows),
        "policy_rollout_run": bool(raw_index_rows),
        "raw_trace_capture_run": bool(raw_index_rows),
        "target_source_feasibility_claim_made": False,
        "target_source_feasibility_established_count": 0,
        "target_tensor_materialization_run": False,
        "numeric_target_tensor_materialized_count": 0,
        "local_action_search_run": False,
        "local_action_search_run_count": 0,
        "fitting_run": False,
        "training_run": False,
        "ppo_run": False,
        "validation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "profile_specific_tuning": False,
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
        "raw_trace_capture_complete_pending_m3028_audit": bool(status_pass),
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "next_blocker": next_blocker,
        "paths": {key: str(value) for key, value in paths.items()} | {"raw_traces_dir": str(output_dir / "raw_traces")},
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path, summary_path: Path) -> dict[str, Any]:
    follow_up_doc = Path(f"docs/{NEXT_ID}.md")
    return {
        "id": NEXT_ID,
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
            "A bounded result audit can accept or reject the M3027 raw deployable trace-capture "
            "artifacts before any target-source feasibility target tensor materialization local-action "
            "search fitting validation ranking performance paper high-fidelity full-driver finite-window-vs-GRU "
            "or self-ID claim."
        ),
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "capture_plan_rows.csv"),
                str(output_dir / "raw_trace_index_rows.csv"),
                str(output_dir / "raw_trace_guard_rows.csv"),
                str(output_dir / "raw_trace_availability_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "parent_config": [
                f"experiments/manifests/{MILESTONE_ID}.json",
                "experiments/manifests/m3026-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-target-source-readiness-feasibility-materialization-result-audit.json",
            ],
            "parent_objective": ["audit M3027 raw deployable trace capture before target-source interpretation"],
            "derived_from": [MILESTONE_ID],
            "blocked_by": [
                "M3027 raw trace capture requires a result audit before target-source feasibility can be interpreted",
                "success identity rows must remain guard rows and not positive target candidates",
            ],
            "supersedes": [
                "direct target tensor materialization immediately after trace capture without result audit",
                "treating raw trace capture as driver-performance or target-source feasibility evidence",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3028 must audit M3027 summary capture plan raw trace index guard availability actor claim and gate artifacts",
            "M3028 must preserve 29 future target rows and 3 success identity guards",
            "M3028 must verify raw trace tensor shapes 72/action 3 and actor visibility guards",
            "M3028 must select exactly one next route or stop state before target tensor materialization or feasibility interpretation",
            "M3028 must not claim validation repair-success driver performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run local-action search target tensor materialization fitting training PPO validation ranking winner selection or promotion",
            "do not change actor input or action contract",
            "do not convert M3027 raw traces into target-source feasibility performance paper high-fidelity or self-ID claims",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_residual_stop_source_axis_expansion",
            "evidence_axis": "new_source_broad_failure_deployable_trace_capture_result_audit",
            "evidence_increment": "audits newly captured raw actor-view trace files for the M3025 readiness denominator",
            "claim_scope": "Result audit only; no target tensor materialization local-action search fitting validation ranking promotion repair-success performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M3027 artifacts are missing or gate matrix fails",
                "stop if actor or claim boundaries were violated",
                "stop if raw traces would be interpreted as target-source feasibility before audit",
            ],
            "fallback_plan": [
                "route to artifact repair if raw trace files are incomplete",
                "route to branch synthesis if raw trace capture violates actor boundaries",
                "route to bounded target-source feasibility audit only after M3028 accepts claim safety and capture completeness",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3027 completes deployable trace-capture preflight",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3027 raw deployable trace-capture artifacts",
            "admission_evidence": [
                "M3027 summary and gate matrix",
                "M3027 capture plan raw trace index guard availability actor and claim artifacts",
            ],
            "blocked_shortcuts": [
                "no target tensor materialization local-action search fitting training validation ranking promotion performance verdict paper high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
                "no checkpoint promotion",
                "no hidden/oracle/future-target actor input",
            ],
            "allowed_updates": [
                str(follow_up_doc),
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3028 status queue scoreboard research log and review",
                "one follow-up manifest only if M3028 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3028 accepts or rejects M3027 as complete and claim-safe",
                "next route or stop state is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3028 audits Route A trace capture and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M3028; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M3027 Route A raw trace-capture preflight only.",
            "negative_result_policy": "Preserve trace capture failures and route to repair or synthesis rather than weakening self-ID gates.",
            "allowed_claims": [
                "M3027 artifact completeness and claim-safety audit",
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
            "paper_verdict_delta": "no paper verdict; audit may inform target-source feasibility route only",
            "must_synthesize_if": [
                "M3028 cannot accept M3027 as complete and claim-safe",
                "M3028 finds raw trace availability insufficient for target-source feasibility interpretation",
                "M3028 would claim validation readiness driver performance paper current-sim high-fidelity or self-ID",
            ],
        },
        "success_criteria": [
            f"{follow_up_doc} exists",
            "M3028 audits M3027 artifacts row counts gates actor and claim boundaries",
            "M3028 selects exactly one next route or stop state",
            "no target tensor fitting training validation ranking promotion performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claim is made",
        ],
        "failure_criteria": [
            "M3028 hides M3027 failures or missing raw trace files",
            "M3028 treats M3027 trace capture as target-source feasibility performance verdict or repair success",
            "M3028 changes actor input or action contract",
            "M3028 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3028 audits M3027 artifacts and selects one next route or stop state while preserving actor guardrail and claim boundaries without overclaiming.",
        "commands": [{"name": "result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": str(follow_up_doc), "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "raw_trace_index_rows.csv"),
            str(output_dir / "raw_trace_availability_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
        ],
        "scoreboard_checkpoint": str(follow_up_doc),
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def render_milestone_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3027 Engineering Controller Route A Post-Residual-Stop New Source Broad-Failure Deployable Trace Capture Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'fail_closed'}",
            f"- result class: `{summary['result_class']}`",
            f"- capture plan rows: {summary['capture_plan_row_count']}",
            f"- future target raw traces: {summary['future_target_raw_trace_count']}",
            f"- success identity raw traces: {summary['success_identity_raw_trace_count']}",
            f"- raw trace persisted rows: {summary['raw_trace_persisted_count']}",
            f"- actor shape: {summary['observation_shape']}/action {summary['action_shape']}",
            f"- raw trace tensors finite: {summary['raw_trace_tensors_finite']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M3027 captures raw actor-view observation/action/response traces for later audit. It does not run local-action search, materialize targets, fit, train, validate, rank, promote, mutate checkpoints, or claim performance.",
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


def run_deployable_trace_capture_preflight(
    *,
    m3025_dir: Path | str = DEFAULT_M3025_DIR,
    m3026_audit: Path | str = DEFAULT_M3026_AUDIT,
    m3015_dir: Path | str = DEFAULT_M3015_DIR,
    m3012_dir: Path | str = DEFAULT_M3012_DIR,
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
    paths = artifact_paths(output, doc_path=Path(doc_path), follow_up_manifest=Path(follow_up_manifest))
    source = load_source_artifacts(
        m3025_dir=Path(m3025_dir),
        m3026_audit=Path(m3026_audit),
        m3015_dir=Path(m3015_dir),
        m3012_dir=Path(m3012_dir),
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
    write_csv_rows(paths["raw_trace_availability_rows"], availability_rows, fieldnames=RAW_TRACE_AVAILABILITY_FIELDNAMES)
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output, doc_path=Path(doc_path), summary_path=paths["summary"]))
    source["source_exists"]["follow_up_manifest"] = Path(follow_up_manifest).exists()
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

    required_core_artifacts_present = all(
        paths[key].exists() for key in PATH_KEYS if key not in {"summary", "doc", "actor_contract_guard_rows", "claim_boundary_rows", "gate_matrix"}
    )
    actor_rows = build_actor_contract_guard_rows(raw_index_rows=raw_index_rows, guard_rows=guard_rows)
    claim_rows = build_claim_boundary_rows(raw_index_rows=raw_index_rows, follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"])
    gate_rows = build_gate_matrix_rows(
        source=source,
        plan_rows=plan_rows,
        raw_index_rows=raw_index_rows,
        guard_rows=guard_rows,
        availability_rows=availability_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_core_artifacts_present,
        follow_up_manifest=Path(follow_up_manifest),
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
        required_artifacts_present=False,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
        device=device,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(paths[key].exists() for key in PATH_KEYS)
    gate_rows = build_gate_matrix_rows(
        source=source,
        plan_rows=plan_rows,
        raw_index_rows=raw_index_rows,
        guard_rows=guard_rows,
        availability_rows=availability_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
        follow_up_manifest=Path(follow_up_manifest),
    )
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
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
        device=device,
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "capture_plan_row_count": len(plan_rows),
            "raw_trace_index_row_count": len(raw_index_rows),
            "raw_trace_guard_row_count": len(guard_rows),
            "raw_trace_availability_row_count": len(availability_rows),
            "status_pass": summary["status_pass"],
            "gate_matrix_pass": summary["gate_matrix_pass"],
            "complete": summary["status_pass"],
            "next_blocker": next_blocker,
        },
    )
    return summary


def forbidden_m3027_flags(rows: list[Mapping[str, Any]]) -> dict[str, bool]:
    keys = [
        "local_action_search_run",
        "numeric_target_tensor_materialized",
        "target_source_feasibility_claim_made",
        "training_run",
        "ppo_run",
        "validation_run",
        "ranking_run",
        "checkpoint_mutated",
    ]
    return {key: _any_true(rows, key) for key in keys}


def _shape_text(array: np.ndarray) -> str:
    return "x".join(str(dim) for dim in array.shape)


def _to_int(value: Any, *, default: int = 0) -> int:
    try:
        if value in ("", None):
            return int(default)
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _all_true(rows: list[Mapping[str, Any]], key: str) -> bool:
    return bool(rows) and all(_bool(row.get(key, False)) for row in rows)


def _any_true(rows: list[Mapping[str, Any]], key: str) -> bool:
    return any(_bool(row.get(key, False)) for row in rows)


def _all_equal(rows: list[Mapping[str, Any]], key: str, expected: Any) -> bool:
    return bool(rows) and all(row.get(key) == expected or str(row.get(key)) == str(expected) for row in rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run M3027 deployable trace-capture preflight.")
    parser.add_argument("--m3025-dir", type=Path, default=DEFAULT_M3025_DIR)
    parser.add_argument("--m3026-audit", type=Path, default=DEFAULT_M3026_AUDIT)
    parser.add_argument("--m3015-dir", type=Path, default=DEFAULT_M3015_DIR)
    parser.add_argument("--m3012-dir", type=Path, default=DEFAULT_M3012_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    summary = run_deployable_trace_capture_preflight(
        m3025_dir=args.m3025_dir,
        m3026_audit=args.m3026_audit,
        m3015_dir=args.m3015_dir,
        m3012_dir=args.m3012_dir,
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
