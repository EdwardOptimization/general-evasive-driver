"""Capture M3059 raw actor-view traces for offtrack behavior blockers.

M3059 consumes the M3058-accepted M3057 fail-closed target tensor blocker
denominator. It reruns only the matching M3050/M3012 executable rows to persist
raw actor-view observation/action/response traces for later audited target
tensor materialization. It does not run target tensor materialization, fitting,
training, validation, ranking, promotion, high-fidelity simulation, architecture
comparison, full-driver evaluation, or self-ID testing.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.controller_family_full_rollout_execution import (
    env_config_for_executable_profile,
    read_csv_rows,
    write_run_state,
)
from autodrift.controller_profile_runtime import profile_runtime_summary, wrap_env_with_profile_mask
from autodrift.engineering_controller_active_safety_driver_v1_actuation_aware_residual_repair_closed_loop_measurement_preflight import (
    ResidualActorPolicy,
    load_residual_artifact,
    profile_config_for_runtime,
)
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import ActorPolicy, outcome_bucket_from_info
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3059-engineering-controller-active-safety-driver-v1-offtrack-dominant-"
    "behavior-raw-trace-capture-preflight"
)
NEXT_ID = (
    "m3060-engineering-controller-active-safety-driver-v1-offtrack-dominant-"
    "behavior-raw-trace-capture-result-audit"
)
M3058_ID = (
    "m3058-engineering-controller-active-safety-driver-v1-offtrack-dominant-"
    "behavior-target-tensor-materialization-result-audit"
)

DEFAULT_M3058_AUDIT = Path(f"docs/{M3058_ID}.md")
DEFAULT_M3057_DIR = Path(
    "runs/m3057_engineering_controller_active_safety_driver_v1_offtrack_"
    "dominant_behavior_target_tensor_materialization_preflight"
)
DEFAULT_M3055_DIR = Path(
    "runs/m3055_engineering_controller_active_safety_driver_v1_offtrack_"
    "dominant_behavior_fitting_contract_materialization_preflight"
)
DEFAULT_M3053_DIR = Path(
    "runs/m3053_engineering_controller_active_safety_driver_v1_offtrack_"
    "dominant_behavior_target_materialization_preflight"
)
DEFAULT_M3050_DIR = Path(
    "runs/m3050_engineering_controller_active_safety_driver_v1_actuation_aware_"
    "residual_repair_closed_loop_measurement_preflight"
)
DEFAULT_M3012_DIR = Path(
    "runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_"
    "executable_env_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3059_engineering_controller_active_safety_driver_v1_offtrack_"
    "dominant_behavior_raw_trace_capture_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_BLOCKER_ROWS = 24
EXPECTED_ACTION_COMPONENTS = "steer;throttle;brake"

CLAIM_SCOPE = (
    "M3059 Active Safety Driver v1 offtrack-dominant behavior raw trace "
    "capture preflight only; M3058 audit, M3057 target tensor blocker rows, "
    "M3055 fitting contract, M3053 behavior target-source rows, M3050 "
    "measurement rows, and M3012 executable workload/spec artifacts may be "
    "used to persist raw actor-view observation/action/next-observation/"
    "reward/done/timeout traces for the M3057 blocker denominator. No numeric "
    "target tensor materialization, fitting, fitted policy quality, local "
    "action search, PPO, training, validation, ranking, winner selection, "
    "checkpoint mutation, checkpoint promotion, repair success, "
    "driver-performance verdict, current-sim verdict, high-fidelity "
    "validation, paper evidence, finite-window-vs-GRU evidence, full ideal "
    "driver completion, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "numeric target tensor quality, fitted policy quality, repair success, "
    "validation result, driver-performance verdict, current-sim verdict, "
    "checkpoint ranking, winner selection, checkpoint promotion, high-fidelity "
    "validation readiness or result, paper evidence, finite-window-vs-GRU "
    "conclusion, full ideal driver completion, or level3 self-identification"
)
M3058_DECISION_MARKER = "continue_to_m3059_offtrack_dominant_behavior_raw_trace_capture_preflight"

RAW_TRACE_INDEX_FIELDNAMES = [
    "raw_trace_index_row_id",
    "raw_trace_capture_plan_row_id",
    "target_tensor_row_id",
    "source_offtrack_target_source_id",
    "measurement_episode_id",
    "baseline_measurement_row_id",
    "executable_workload_id",
    "task_source_id",
    "executable_source_spec_id",
    "base_profile_name",
    "residual_profile_name",
    "binding_role",
    "task_family",
    "source_edge",
    "window_tag",
    "eval_seed",
    "raw_trace_path",
    "raw_trace_persisted",
    "trace_step_count",
    "expected_trace_step_count",
    "trace_step_count_matches_m3050",
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
    "output_components",
    "hidden_oracle_actor_input_required",
    "target_labels_actor_visible",
    "target_provenance_actor_visible",
    "source_labels_actor_visible",
    "route_labels_actor_visible",
    "outcome_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "ttc_actor_input_required",
    "checkpoint_loaded_read_only",
    "residual_adapter_applied",
    "terminated",
    "truncated",
    "termination_reason",
    "completion_reason",
    "outcome_bucket",
    "environment_reset_run",
    "environment_step_run",
    "policy_action_run",
    "policy_rollout_run",
    "replay_run",
    "local_action_search_run",
    "numeric_target_tensor_materialized",
    "target_tensor_quality_claim_made",
    "fitting_run",
    "training_run",
    "validation_run",
    "ranking_run",
    "winner_selected",
    "checkpoint_mutated",
    "checkpoint_promoted",
    "driver_performance_claim_made",
    "current_sim_verdict_claim_made",
    "high_fidelity_validation_claim_made",
    "paper_claim_made",
    "finite_window_vs_gru_claim_made",
    "full_ideal_driver_completion_claim_made",
    "level3_self_id_claim_made",
    "claim_boundary",
]
AVAILABILITY_FIELDNAMES = [
    "raw_trace_availability_row_id",
    "raw_trace_capture_plan_row_id",
    "target_tensor_row_id",
    "measurement_episode_id",
    "raw_trace_path",
    "raw_trace_persisted",
    "trace_file_exists",
    "trace_step_count",
    "expected_trace_step_count",
    "availability_status",
    "blocking_reason_for_target_tensor_materialization",
    "error_type",
    "error_message",
    "claim_boundary",
]
RAW_TRACE_GUARD_FIELDNAMES = [
    "raw_trace_guard_row_id",
    "raw_trace_capture_plan_row_id",
    "target_tensor_row_id",
    "measurement_episode_id",
    "guard_family",
    "raw_trace_persisted",
    "actor_view_only",
    "observation_shape_72",
    "action_shape_3",
    "target_labels_actor_visible",
    "target_provenance_actor_visible",
    "hidden_oracle_actor_input_required",
    "ttc_actor_input_required",
    "local_action_search_run",
    "numeric_target_tensor_materialized",
    "fitting_run",
    "training_run",
    "validation_run",
    "ranking_run",
    "checkpoint_mutated",
    "status_pass",
    "claim_boundary",
]
ACTOR_GUARD_FIELDNAMES = [
    "actor_guard_id",
    "guard_family",
    "observed",
    "expected",
    "status_pass",
    "actor_visible",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3059",
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


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _shape_text(value: np.ndarray) -> str:
    return "x".join(str(int(dim)) for dim in value.shape)


def _all_true(rows: Iterable[Mapping[str, Any]], field: str) -> bool:
    rows = list(rows)
    return bool(rows) and all(_bool(row.get(field)) for row in rows)


def _any_true(rows: Iterable[Mapping[str, Any]], field: str) -> bool:
    return any(_bool(row.get(field)) for row in rows)


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    return read_json(path) if path.exists() else {}


def _read_csv_if_exists(path: Path) -> list[dict[str, str]]:
    return read_csv_rows(path) if path.exists() else []


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "raw_trace_index_rows": output_dir / "raw_trace_index_rows.csv",
        "raw_trace_availability_rows": output_dir / "raw_trace_availability_rows.csv",
        "raw_trace_guard_rows": output_dir / "raw_trace_guard_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(
    *,
    m3058_audit: Path,
    m3057_dir: Path,
    m3055_dir: Path,
    m3053_dir: Path,
    m3050_dir: Path,
    m3012_dir: Path,
) -> dict[str, Any]:
    paths = {
        "m3058_audit": m3058_audit,
        "m3057_summary": m3057_dir / "summary.json",
        "m3057_behavior_target_tensor_rows": m3057_dir / "behavior_target_tensor_rows.csv",
        "m3057_gate_matrix": m3057_dir / "gate_matrix.csv",
        "m3055_summary": m3055_dir / "summary.json",
        "m3053_summary": m3053_dir / "summary.json",
        "m3053_offtrack_rows": m3053_dir / "offtrack_behavior_target_source_rows.csv",
        "m3050_summary": m3050_dir / "summary.json",
        "m3050_measurement_rows": m3050_dir / "measurement_episode_rows.csv",
        "m3012_summary": m3012_dir / "summary.json",
        "m3012_executable_specs": m3012_dir / "executable_source_specs.json",
        "m3012_workload_rows": m3012_dir / "executable_workload_rows.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    spec_payload = _read_json_if_exists(paths["m3012_executable_specs"])
    return {
        "paths": paths,
        "source_exists": exists,
        "m3058_audit_text": paths["m3058_audit"].read_text(encoding="utf-8") if exists["m3058_audit"] else "",
        "m3057_summary": _read_json_if_exists(paths["m3057_summary"]),
        "m3057_behavior_target_tensor_rows": _read_csv_if_exists(paths["m3057_behavior_target_tensor_rows"]),
        "m3057_gate_rows": _read_csv_if_exists(paths["m3057_gate_matrix"]),
        "m3055_summary": _read_json_if_exists(paths["m3055_summary"]),
        "m3053_summary": _read_json_if_exists(paths["m3053_summary"]),
        "m3053_offtrack_rows": _read_csv_if_exists(paths["m3053_offtrack_rows"]),
        "m3050_summary": _read_json_if_exists(paths["m3050_summary"]),
        "m3050_measurement_rows": _read_csv_if_exists(paths["m3050_measurement_rows"]),
        "m3012_summary": _read_json_if_exists(paths["m3012_summary"]),
        "m3012_executable_specs": list(spec_payload.get("executable_source_specs", [])),
        "m3012_workload_rows": _read_csv_if_exists(paths["m3012_workload_rows"]),
    }


def build_capture_plan(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    measurements = {
        str(row.get("measurement_episode_id", "")): row for row in source["m3050_measurement_rows"]
    }
    workloads = {
        str(row.get("executable_workload_id", "")): row for row in source["m3012_workload_rows"]
    }
    specs = {
        (str(row.get("task_source_id", "")), str(row.get("executable_source_spec_id", ""))): row
        for row in source["m3012_executable_specs"]
    }
    plan_rows: list[dict[str, Any]] = []
    for index, target_row in enumerate(source["m3057_behavior_target_tensor_rows"], start=1):
        measurement_id = str(target_row.get("measurement_episode_id", ""))
        measurement = measurements.get(measurement_id, {})
        workload_id = str(measurement.get("executable_workload_id", ""))
        workload = workloads.get(workload_id, {})
        spec_key = (str(measurement.get("task_source_id", "")), str(measurement.get("executable_source_spec_id", "")))
        executable_spec = specs.get(spec_key, {})
        hidden_label_violation = any(
            _bool(row.get(field, False))
            for row in (target_row, measurement, workload)
            for field in (
                "hidden_oracle_actor_input_required",
                "target_labels_actor_visible",
                "target_provenance_actor_visible",
                "source_labels_actor_visible",
                "route_labels_actor_visible",
                "outcome_labels_actor_visible",
                "success_progress_labels_actor_visible",
                "verdict_labels_actor_visible",
                "ttc_actor_input_required",
                "future_target_actor_input_required",
            )
        )
        config_path = str(measurement.get("config_path") or workload.get("config_path", ""))
        checkpoint_path = str(measurement.get("checkpoint_path") or workload.get("checkpoint_path", ""))
        expected_steps = _int(target_row.get("steps"), default=_int(measurement.get("steps"), default=0))
        if expected_steps == 0:
            expected_steps = _int(measurement.get("steps"), default=0)
        status_pass = bool(
            _bool(target_row.get("raw_actor_view_trace_required", False))
            and not _bool(target_row.get("raw_actor_view_trace_available", False))
            and bool(measurement)
            and bool(workload)
            and bool(executable_spec)
            and Path(config_path).exists()
            and Path(checkpoint_path).exists()
            and _int(target_row.get("actor_observation_shape"), default=-1) == P0_OBSERVATION_DIM
            and _int(target_row.get("actor_action_shape"), default=-1) == ACTION_DIM
            and _int(workload.get("actor_observation_dim"), default=-1) == P0_OBSERVATION_DIM
            and _int(workload.get("actor_action_dim"), default=-1) == ACTION_DIM
            and not hidden_label_violation
        )
        plan_rows.append(
            {
                "raw_trace_capture_plan_row_id": f"m3059-raw-trace-plan-{index:04d}",
                "target_tensor_row_id": target_row.get("target_tensor_row_id", ""),
                "source_offtrack_target_source_id": target_row.get("source_offtrack_target_source_id", ""),
                "measurement_episode_id": measurement_id,
                "baseline_measurement_row_id": target_row.get("baseline_measurement_row_id", ""),
                "executable_workload_id": workload_id,
                "task_source_id": measurement.get("task_source_id", ""),
                "executable_source_spec_id": measurement.get("executable_source_spec_id", ""),
                "base_profile_name": measurement.get("base_profile_name") or workload.get("profile_binding_name", ""),
                "residual_profile_name": measurement.get("residual_profile_name", ""),
                "binding_role": target_row.get("binding_role", ""),
                "task_family": target_row.get("task_family", ""),
                "source_edge": target_row.get("source_edge", ""),
                "window_tag": target_row.get("window_tag", ""),
                "eval_seed": _int(target_row.get("eval_seed"), default=_int(measurement.get("eval_seed"), default=0)),
                "expected_trace_step_count": expected_steps,
                "config_path": config_path,
                "checkpoint_path": checkpoint_path,
                "measurement_row_present": bool(measurement),
                "workload_row_present": bool(workload),
                "executable_spec_present": bool(executable_spec),
                "hidden_label_violation": hidden_label_violation,
                "status_pass": status_pass,
            }
        )
    return plan_rows


def capture_episode_trace(
    *,
    executable_spec: Mapping[str, Any],
    profile_config: Mapping[str, Any],
    model: Any,
    residual: Mapping[str, Any],
    eval_seed: int,
) -> dict[str, Any]:
    env_config = env_config_for_executable_profile(executable_spec=executable_spec, profile_config=profile_config)
    env = wrap_env_with_profile_mask(AutoDriftEnv(env_config), profile_config)
    try:
        target_obs_dim = int(env.observation_space.shape[0])
        target_action_dim = int(env.action_space.shape[0])
        model_obs_dim = int(getattr(model, "obs_dim", -1))
        if target_obs_dim != P0_OBSERVATION_DIM:
            raise ValueError(f"env observation dim {target_obs_dim} != {P0_OBSERVATION_DIM}")
        if target_action_dim != ACTION_DIM:
            raise ValueError(f"env action dim {target_action_dim} != {ACTION_DIM}")
        if model_obs_dim != P0_OBSERVATION_DIM:
            raise ValueError(f"checkpoint obs_dim {model_obs_dim} != {P0_OBSERVATION_DIM}")
        runtime = profile_runtime_summary(profile_config)
        base_policy = ActorPolicy(model, env_config, reset_hidden_policy=str(runtime["reset_hidden_policy"]))
        policy = ResidualActorPolicy(
            base_policy,
            weight=residual["weight"],
            bias=residual["bias"],
            residual_limit=float(residual["residual_limit"]),
            action_low=np.asarray(env.action_space.low, dtype=np.float32),
            action_high=np.asarray(env.action_space.high, dtype=np.float32),
        )
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


def capture_plan_rows(
    *,
    source: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    residual: Mapping[str, Any],
    output_dir: Path,
    device: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    specs = {
        (str(row.get("task_source_id", "")), str(row.get("executable_source_spec_id", ""))): row
        for row in source["m3012_executable_specs"]
    }
    cache: dict[tuple[str, str, str], tuple[dict[str, Any], Any]] = {}
    index_rows: list[dict[str, Any]] = []
    availability_rows: list[dict[str, Any]] = []
    guard_rows: list[dict[str, Any]] = []
    for index, plan in enumerate(plan_rows, start=1):
        raw_trace_rel_path = (
            output_dir
            / "raw_traces"
            / f"{plan['raw_trace_capture_plan_row_id']}_{plan['measurement_episode_id']}.npz"
        )
        capture: dict[str, Any] | None = None
        error_type = ""
        error_message = ""
        raw_trace_persisted = False
        try:
            if not _bool(plan.get("status_pass", False)):
                raise ValueError("capture plan row failed pre-execution guards")
            if not _bool(residual.get("contract_pass", False)):
                raise ValueError("residual adapter contract failed")
            spec_key = (str(plan["task_source_id"]), str(plan["executable_source_spec_id"]))
            executable_spec = specs[spec_key]
            profile_name = str(plan["base_profile_name"])
            config_path = str(plan["config_path"])
            checkpoint_path = str(plan["checkpoint_path"])
            cache_key = (profile_name, config_path, checkpoint_path)
            if cache_key not in cache:
                profile_config = profile_config_for_runtime(read_json(Path(config_path)), profile_name=profile_name)
                model, _ = load_actor_critic_checkpoint(checkpoint_path, device=device)
                cache[cache_key] = (profile_config, model)
            profile_config, model = cache[cache_key]
            capture = capture_episode_trace(
                executable_spec=executable_spec,
                profile_config=profile_config,
                model=model,
                residual=residual,
                eval_seed=int(plan["eval_seed"]),
            )
            capture["checkpoint_loaded_read_only"] = True
            capture["residual_adapter_applied"] = True
            save_raw_trace_npz(raw_trace_rel_path, capture)
            raw_trace_persisted = raw_trace_rel_path.exists()
            if raw_trace_persisted:
                index_rows.append(raw_trace_index_row(index=index, plan=plan, raw_trace_path=raw_trace_rel_path, capture=capture))
        except Exception as exc:  # noqa: BLE001 - every denominator row is accounted.
            error_type = type(exc).__name__
            error_message = str(exc)
        availability_rows.append(
            raw_trace_availability_row(
                index=index,
                plan=plan,
                raw_trace_path=raw_trace_rel_path,
                raw_trace_persisted=raw_trace_persisted,
                capture=capture,
                error_type=error_type,
                error_message=error_message,
            )
        )
        guard_rows.append(raw_trace_guard_row(index=index, plan=plan, raw_trace_persisted=raw_trace_persisted, capture=capture))
        write_run_state(
            output_dir / "run_state.json",
            {
                "milestone": MILESTONE_ID,
                "scheduled_capture_row_count": len(plan_rows),
                "raw_trace_index_row_count": len(index_rows),
                "raw_trace_availability_row_count": len(availability_rows),
                "raw_trace_guard_row_count": len(guard_rows),
                "latest_capture_plan_row_id": plan.get("raw_trace_capture_plan_row_id", ""),
                "complete": False,
                "next_blocker": NEXT_ID,
            },
        )
    return index_rows, availability_rows, guard_rows


def raw_trace_index_row(
    *,
    index: int,
    plan: Mapping[str, Any],
    raw_trace_path: Path,
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
    expected_steps = _int(plan.get("expected_trace_step_count"), default=0)
    trace_step_count = int(observation.shape[0])
    return {
        "raw_trace_index_row_id": f"m3059-raw-trace-index-{index:04d}",
        "raw_trace_capture_plan_row_id": plan.get("raw_trace_capture_plan_row_id", ""),
        "target_tensor_row_id": plan.get("target_tensor_row_id", ""),
        "source_offtrack_target_source_id": plan.get("source_offtrack_target_source_id", ""),
        "measurement_episode_id": plan.get("measurement_episode_id", ""),
        "baseline_measurement_row_id": plan.get("baseline_measurement_row_id", ""),
        "executable_workload_id": plan.get("executable_workload_id", ""),
        "task_source_id": plan.get("task_source_id", ""),
        "executable_source_spec_id": plan.get("executable_source_spec_id", ""),
        "base_profile_name": plan.get("base_profile_name", ""),
        "residual_profile_name": plan.get("residual_profile_name", ""),
        "binding_role": plan.get("binding_role", ""),
        "task_family": plan.get("task_family", ""),
        "source_edge": plan.get("source_edge", ""),
        "window_tag": plan.get("window_tag", ""),
        "eval_seed": plan.get("eval_seed", ""),
        "raw_trace_path": str(raw_trace_path),
        "raw_trace_persisted": True,
        "trace_step_count": trace_step_count,
        "expected_trace_step_count": expected_steps,
        "trace_step_count_matches_m3050": trace_step_count == expected_steps,
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
        "output_components": EXPECTED_ACTION_COMPONENTS,
        "hidden_oracle_actor_input_required": False,
        "target_labels_actor_visible": False,
        "target_provenance_actor_visible": False,
        "source_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "outcome_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "ttc_actor_input_required": False,
        "checkpoint_loaded_read_only": _bool(capture.get("checkpoint_loaded_read_only", True)),
        "residual_adapter_applied": _bool(capture.get("residual_adapter_applied", True)),
        "terminated": _bool(capture.get("terminated", False)),
        "truncated": _bool(capture.get("truncated", False)),
        "termination_reason": capture.get("termination_reason", ""),
        "completion_reason": capture.get("completion_reason", ""),
        "outcome_bucket": capture.get("outcome_bucket", ""),
        "environment_reset_run": True,
        "environment_step_run": True,
        "policy_action_run": True,
        "policy_rollout_run": True,
        "replay_run": False,
        "local_action_search_run": False,
        "numeric_target_tensor_materialized": False,
        "target_tensor_quality_claim_made": False,
        "fitting_run": False,
        "training_run": False,
        "validation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "driver_performance_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def raw_trace_availability_row(
    *,
    index: int,
    plan: Mapping[str, Any],
    raw_trace_path: Path,
    raw_trace_persisted: bool,
    capture: Mapping[str, Any] | None,
    error_type: str,
    error_message: str,
) -> dict[str, Any]:
    trace_step_count = int(np.asarray(capture.get("observation_trace", [])).shape[0]) if capture else 0
    return {
        "raw_trace_availability_row_id": f"m3059-raw-trace-availability-{index:04d}",
        "raw_trace_capture_plan_row_id": plan.get("raw_trace_capture_plan_row_id", ""),
        "target_tensor_row_id": plan.get("target_tensor_row_id", ""),
        "measurement_episode_id": plan.get("measurement_episode_id", ""),
        "raw_trace_path": str(raw_trace_path),
        "raw_trace_persisted": raw_trace_persisted,
        "trace_file_exists": raw_trace_path.exists(),
        "trace_step_count": trace_step_count,
        "expected_trace_step_count": plan.get("expected_trace_step_count", ""),
        "availability_status": "raw_trace_persisted_pending_m3060_audit"
        if raw_trace_persisted
        else "raw_trace_missing_fail_closed",
        "blocking_reason_for_target_tensor_materialization": "M3060 result audit required before target tensor rerun"
        if raw_trace_persisted
        else "raw actor-view observation/action/response trace not persisted",
        "error_type": error_type,
        "error_message": error_message,
        "claim_boundary": CLAIM_SCOPE,
    }


def raw_trace_guard_row(
    *,
    index: int,
    plan: Mapping[str, Any],
    raw_trace_persisted: bool,
    capture: Mapping[str, Any] | None,
) -> dict[str, Any]:
    observation = np.asarray(capture.get("observation_trace", [])) if capture else np.asarray([])
    action = np.asarray(capture.get("action_trace", [])) if capture else np.asarray([])
    observation_shape_72 = bool(observation.ndim == 2 and observation.shape[1] == P0_OBSERVATION_DIM)
    action_shape_3 = bool(action.ndim == 2 and action.shape[1] == ACTION_DIM)
    status_pass = bool(raw_trace_persisted and observation_shape_72 and action_shape_3)
    return {
        "raw_trace_guard_row_id": f"m3059-raw-trace-guard-{index:04d}",
        "raw_trace_capture_plan_row_id": plan.get("raw_trace_capture_plan_row_id", ""),
        "target_tensor_row_id": plan.get("target_tensor_row_id", ""),
        "measurement_episode_id": plan.get("measurement_episode_id", ""),
        "guard_family": "raw_actor_view_trace_capture",
        "raw_trace_persisted": raw_trace_persisted,
        "actor_view_only": True,
        "observation_shape_72": observation_shape_72,
        "action_shape_3": action_shape_3,
        "target_labels_actor_visible": False,
        "target_provenance_actor_visible": False,
        "hidden_oracle_actor_input_required": False,
        "ttc_actor_input_required": False,
        "local_action_search_run": False,
        "numeric_target_tensor_materialized": False,
        "fitting_run": False,
        "training_run": False,
        "validation_run": False,
        "ranking_run": False,
        "checkpoint_mutated": False,
        "status_pass": status_pass,
        "claim_boundary": CLAIM_SCOPE,
    }


def actor_guard(field: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "actor_guard_id": f"m3059-actor-contract-{field}",
        "guard_family": field,
        "observed": observed,
        "expected": expected,
        "status_pass": observed == expected,
        "actor_visible": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_actor_contract_guard_rows(
    *,
    source: Mapping[str, Any],
    residual: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    index_rows: list[dict[str, Any]],
    availability_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        actor_guard("m3057_blocker_denominator_count", len(source["m3057_behavior_target_tensor_rows"]), EXPECTED_BLOCKER_ROWS),
        actor_guard("capture_plan_row_count", len(plan_rows), EXPECTED_BLOCKER_ROWS),
        actor_guard("raw_trace_index_row_count", len(index_rows), EXPECTED_BLOCKER_ROWS),
        actor_guard("raw_trace_availability_row_count", len(availability_rows), EXPECTED_BLOCKER_ROWS),
        actor_guard("raw_trace_guard_row_count", len(guard_rows), EXPECTED_BLOCKER_ROWS),
        actor_guard("all_actor_observation_dim_72", all(_int(row.get("actor_observation_dim"), -1) == P0_OBSERVATION_DIM for row in index_rows), True),
        actor_guard("all_actor_action_dim_3", all(_int(row.get("actor_action_dim"), -1) == ACTION_DIM for row in index_rows), True),
        actor_guard("output_components", EXPECTED_ACTION_COMPONENTS, EXPECTED_ACTION_COMPONENTS),
        actor_guard("residual_adapter_contract_pass", _bool(residual.get("contract_pass", False)), True),
        actor_guard("actor_view_only", _all_true(index_rows, "actor_view_only"), True),
        actor_guard("checkpoint_loaded_read_only", _all_true(index_rows, "checkpoint_loaded_read_only"), True),
        actor_guard("hidden_oracle_actor_input_required", _any_true(index_rows, "hidden_oracle_actor_input_required"), False),
        actor_guard("target_labels_actor_visible", _any_true(index_rows, "target_labels_actor_visible"), False),
        actor_guard("target_provenance_actor_visible", _any_true(index_rows, "target_provenance_actor_visible"), False),
        actor_guard("source_labels_actor_visible", _any_true(index_rows, "source_labels_actor_visible"), False),
        actor_guard("route_labels_actor_visible", _any_true(index_rows, "route_labels_actor_visible"), False),
        actor_guard("outcome_labels_actor_visible", _any_true(index_rows, "outcome_labels_actor_visible"), False),
        actor_guard("success_progress_labels_actor_visible", _any_true(index_rows, "success_progress_labels_actor_visible"), False),
        actor_guard("verdict_labels_actor_visible", _any_true(index_rows, "verdict_labels_actor_visible"), False),
        actor_guard("ttc_actor_input_required", _any_true(index_rows, "ttc_actor_input_required"), False),
    ]


def build_claim_rows(*, index_rows: list[dict[str, Any]], follow_up_manifest_exists: bool) -> list[dict[str, Any]]:
    specs = [
        ("raw_trace_capture_artifacts_materialized", True, bool(index_rows), "raw trace index, availability, guard, and npz files"),
        ("follow_up_result_audit_manifest_registered", True, follow_up_manifest_exists, "M3060 manifest"),
        ("numeric_target_tensor_materialization", False, False, "future M3060 audit and target tensor rerun"),
        ("target_tensor_quality", False, False, "future audited target tensor materialization"),
        ("local_action_search", False, False, "future audited target generation route"),
        ("fitting_or_training", False, False, "future fitting/training milestone"),
        ("validation_result", False, False, "future validation route"),
        ("ranking_or_winner_selection", False, False, "future ranking/promotion gate"),
        ("checkpoint_mutation_or_promotion", False, False, "future promotion gate"),
        ("repair_success", False, False, "future closed-loop measurement and audit"),
        ("driver_performance", False, False, "proof/generalization/promotion gates"),
        ("current_sim_verdict", False, False, "separate verdict synthesis"),
        ("high_fidelity_validation", False, False, "future high-fidelity validation"),
        ("paper_claim", False, False, "paper route evidence matrix"),
        ("finite_window_vs_gru", False, False, "future same-case architecture comparison"),
        ("full_ideal_driver_completion", False, False, "future full-driver gate"),
        ("level3_self_id", False, False, "self-ID proof gates"),
    ]
    return [
        {
            "claim_id": f"m3059-claim-{index:04d}",
            "claim_family": family,
            "allowed_in_m3059": allowed,
            "claim_made": made,
            "status_pass": (allowed and made) or ((not allowed) and (not made)),
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, allowed, made, evidence) in enumerate(specs, start=1)
    ]


def forbidden_flags(rows: Iterable[Mapping[str, Any]]) -> dict[str, bool]:
    fields = [
        "numeric_target_tensor_materialized",
        "target_tensor_quality_claim_made",
        "local_action_search_run",
        "fitting_run",
        "training_run",
        "validation_run",
        "ranking_run",
        "winner_selected",
        "checkpoint_mutated",
        "checkpoint_promoted",
        "driver_performance_claim_made",
        "current_sim_verdict_claim_made",
        "high_fidelity_validation_claim_made",
        "paper_claim_made",
        "finite_window_vs_gru_claim_made",
        "full_ideal_driver_completion_claim_made",
        "level3_self_id_claim_made",
    ]
    return {field: _any_true(rows, field) for field in fields}


def gate(name: str, family: str, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    status = observed == expected
    return {
        "gate_id": f"m3059-{name}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": "" if status else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_rows(
    *,
    source: Mapping[str, Any],
    residual: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    index_rows: list[dict[str, Any]],
    availability_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_exists: bool,
) -> list[dict[str, Any]]:
    m3057_summary = source["m3057_summary"]
    m3055_summary = source["m3055_summary"]
    m3050_summary = source["m3050_summary"]
    forbidden = forbidden_flags(index_rows + guard_rows)
    return [
        gate("source_artifacts_present", "lineage", all(source["source_exists"].values()), True, "lineage_invalid"),
        gate("m3058_routes_to_m3059", "lineage", M3058_DECISION_MARKER in source["m3058_audit_text"], True, "lineage_invalid"),
        gate("m3057_fail_closed_status", "lineage", _bool(m3057_summary.get("status_pass")), False, "lineage_invalid"),
        gate("m3057_fail_closed_gate_matrix", "lineage", _bool(m3057_summary.get("gate_matrix_pass")), False, "lineage_invalid"),
        gate(
            "m3057_missing_raw_trace_count",
            "lineage",
            _int(m3057_summary.get("raw_actor_view_trace_missing_count"), default=-1),
            EXPECTED_BLOCKER_ROWS,
            "metric_artifact",
        ),
        gate("m3055_direct_action", "contract", m3055_summary.get("output_semantics"), "direct_action", "contract_violation"),
        gate(
            "m3055_base_policy_required_false",
            "contract",
            _bool(m3055_summary.get("base_policy_required_at_runtime")),
            False,
            "contract_violation",
        ),
        gate("m3050_status_pass", "lineage", _bool(m3050_summary.get("status_pass")), True, "lineage_invalid"),
        gate("residual_adapter_contract_pass", "contract", _bool(residual.get("contract_pass", False)), True, "contract_violation"),
        gate("capture_plan_row_count", "denominator", len(plan_rows), EXPECTED_BLOCKER_ROWS, "metric_artifact"),
        gate("capture_plan_rows_prechecked", "contract", all(_bool(row.get("status_pass")) for row in plan_rows), True, "contract_violation"),
        gate("raw_trace_index_row_count", "artifact", len(index_rows), EXPECTED_BLOCKER_ROWS, "metric_artifact"),
        gate("raw_trace_availability_row_count", "artifact", len(availability_rows), EXPECTED_BLOCKER_ROWS, "metric_artifact"),
        gate("raw_trace_guard_row_count", "artifact", len(guard_rows), EXPECTED_BLOCKER_ROWS, "metric_artifact"),
        gate("raw_trace_files_exist", "artifact", _all_true(index_rows, "raw_trace_persisted"), True, "metric_artifact"),
        gate("raw_trace_tensors_finite", "artifact", _all_true(index_rows, "tensors_finite"), True, "metric_artifact"),
        gate("trace_step_counts_match_m3050", "artifact", _all_true(index_rows, "trace_step_count_matches_m3050"), True, "metric_artifact"),
        gate("actor_contract_guards_pass", "contract", _all_true(actor_rows, "status_pass"), True, "contract_violation"),
        gate("raw_trace_guards_pass", "contract", _all_true(guard_rows, "status_pass"), True, "contract_violation"),
        gate("claim_boundary_rows_pass", "claim_boundary", _all_true(claim_rows, "status_pass"), True, "contract_violation"),
        gate("forbidden_flags_clear", "claim_boundary", any(forbidden.values()), False, "contract_violation"),
        gate("required_artifacts_present", "artifact", required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_exists, True, "lineage_invalid"),
    ]


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path, summary_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 30550,
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
        "hypothesis": "A bounded result audit can accept or reject the M3059 raw actor-view trace capture artifacts before any numeric target tensor rerun fitting rollout validation ranking promotion driver-performance current-sim high-fidelity paper finite-window-vs-GRU full-driver or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "raw_trace_index_rows.csv"),
                str(output_dir / "raw_trace_availability_rows.csv"),
                str(output_dir / "raw_trace_guard_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "parent_config": [
                f"experiments/manifests/{MILESTONE_ID}.json",
                f"experiments/manifests/{M3058_ID}.json",
            ],
            "parent_objective": [
                "audit raw actor-view traces before target tensor materialization rerun"
            ],
            "derived_from": [MILESTONE_ID, M3058_ID],
            "blocked_by": [
                "M3059 raw trace capture artifacts require audit before target tensor rerun",
                "raw trace capture is not target tensor quality fitted policy quality repair-success or driver-performance evidence",
            ],
            "supersedes": ["target tensor rerun immediately after raw trace capture without result audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3060 must audit M3059 summary raw trace index availability guard actor claim and gate artifacts",
            "M3060 must preserve actor observation 72 action 3 direct [steer throttle brake] and no hidden oracle TTC target provenance source route outcome progress or verdict actor inputs",
            "M3060 must reject numeric target tensor quality fitting execution fitted policy quality repair-success validation ranking promotion performance current-sim high-fidelity paper finite-window-vs-GRU full-driver and self-ID claims",
            "M3060 must choose exactly one next target tensor rerun artifact repair synthesis or stop route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run target tensor materialization fitting rollout validation ranking promotion high-fidelity or finite-window-vs-GRU comparison",
            "do not convert raw trace rows into target tensor quality fitted policy quality repair-success driver-performance current-sim paper high-fidelity full-driver or self-ID claims",
            "do not mutate parent checkpoints configs profiles residual artifacts or actor contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_v1_offtrack_dominant_behavior_repair",
            "evidence_axis": "active_safety_driver_v1_offtrack_behavior_raw_trace_capture_result_audit",
            "evidence_increment": "audits M3059 raw actor-view trace capture artifacts before target tensor materialization rerun",
            "claim_scope": "Result audit only; no target tensor rerun fitting rollout validation ranking promotion performance current-sim high-fidelity paper finite-window-vs-GRU full-driver or self-ID claim",
            "stop_condition": [
                "stop if M3059 artifact set is incomplete",
                "stop if actor contract or claim-boundary guards fail",
                "stop if raw traces are treated as target tensor quality or performance evidence",
            ],
            "fallback_plan": [
                "route to target tensor rerun only if raw trace capture is complete and claim-safe",
                "route to artifact repair if trace index availability or guard rows are incomplete",
                "route to synthesis or stop if trace capture is not admissible",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3059 captures or fail-closed records raw actor-view traces",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit offtrack-dominant behavior raw actor-view trace capture artifacts",
            "admission_evidence": [
                "M3059 summary and gate matrix",
                "M3059 raw trace index availability guard actor and claim rows",
            ],
            "blocked_shortcuts": [
                "no target tensor materialization fitting rollout validation ranking promotion or checkpoint mutation",
                "no hidden oracle target TTC source route outcome progress or verdict actor inputs",
                "no driver-performance current-sim high-fidelity finite-window-vs-GRU paper full-driver or self-ID claim",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3060 status queue scoreboard research log and review",
                "one follow-up manifest only if M3060 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3059 raw trace capture artifacts are accepted or rejected",
                "one next target tensor rerun artifact repair synthesis or stop route is selected",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3060 audits engineering raw trace artifacts and cannot prove or disprove history necessity.",
            "history_necessity_tests": [
                "None in M3060; finite-window and GRU comparison remains a later same-case engineering ablation."
            ],
            "temporal_evidence_window": "M3059 raw trace capture artifacts only.",
            "negative_result_policy": "Self-ID diagnostics remain auxiliary and cannot replace active-safety trace audit gates.",
            "allowed_claims": [
                "M3059 artifact audit completeness",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits raw actor-view trace capture before target tensor repair",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3060 prepares a claim-safe engineering continuation decision",
            "must_synthesize_if": [
                "M3060 cannot select target tensor rerun repair synthesis or stop route",
                "M3060 would require another materialization-only loop without changing evidence",
                "M3060 would claim validation driver-performance paper high-fidelity finite-window-vs-GRU current-sim verdict or self-ID evidence",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3060 audits M3059 raw trace index availability guard actor claim and gate artifacts",
            "M3060 rejects target tensor quality fitting execution fitted policy quality repair-success validation ranking promotion performance high-fidelity paper finite-window-vs-GRU and self-ID claims",
            "M3060 selects exactly one next target tensor rerun repair synthesis or stop route",
        ],
        "failure_criteria": [
            "M3060 treats raw trace rows as target tensor quality or driver performance",
            "M3060 omits actor or claim-boundary audits",
            "M3060 runs target tensor materialization fitting validation ranking promotion high-fidelity or architecture comparison",
            "M3060 leaves the next route ambiguous",
        ],
        "decision_rule": "Pass only if M3060 audits M3059 raw trace evidence and selects exactly one target tensor rerun repair synthesis or stop route without overclaiming.",
        "commands": [
            {
                "name": "active_safety_driver_v1_offtrack_dominant_behavior_raw_trace_capture_result_audit_doc",
                "command": "true",
            }
        ],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
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
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "follow_up_manifest": "",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def build_summary(
    *,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
    source: Mapping[str, Any],
    residual: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    index_rows: list[dict[str, Any]],
    availability_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    device: str,
) -> dict[str, Any]:
    gate_matrix_pass = _all_true(gate_rows, "status_pass")
    status_pass = bool(gate_matrix_pass and len(index_rows) == EXPECTED_BLOCKER_ROWS)
    termination_counts = Counter(str(row.get("termination_reason", "")) for row in index_rows)
    profile_counts = Counter(str(row.get("base_profile_name", "")) for row in index_rows)
    raw_trace_step_count_total = sum(_int(row.get("trace_step_count"), default=0) for row in index_rows)
    return {
        "milestone": MILESTONE_ID,
        "generated_at_utc": utc_timestamp(),
        "result_class": "active_safety_driver_v1_offtrack_behavior_raw_trace_capture_preflight_pass"
        if status_pass
        else "active_safety_driver_v1_offtrack_behavior_raw_trace_capture_preflight_fail_closed",
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "decision": "active_safety_driver_v1_offtrack_behavior_raw_trace_capture_route_to_m3060_result_audit"
        if status_pass
        else "active_safety_driver_v1_offtrack_behavior_raw_trace_capture_fail_closed_route_to_m3060_result_audit",
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "output_dir": str(output_dir),
        "device": device,
        "source_artifacts_present": all(source["source_exists"].values()),
        "m3057_status_pass": _bool(source["m3057_summary"].get("status_pass")),
        "m3057_gate_matrix_pass": _bool(source["m3057_summary"].get("gate_matrix_pass")),
        "m3057_raw_actor_view_trace_required_count": _int(source["m3057_summary"].get("raw_actor_view_trace_required_count")),
        "m3057_raw_actor_view_trace_missing_count": _int(source["m3057_summary"].get("raw_actor_view_trace_missing_count")),
        "m3050_status_pass": _bool(source["m3050_summary"].get("status_pass")),
        "m3050_gate_matrix_pass": _bool(source["m3050_summary"].get("gate_matrix_pass")),
        "candidate_residual_reflex_layer": source["m3050_summary"].get("candidate_residual_reflex_layer", ""),
        "residual_adapter_contract_pass": _bool(residual.get("contract_pass", False)),
        "residual_limit": float(residual.get("residual_limit", 0.0)),
        "capture_plan_row_count": len(plan_rows),
        "capture_plan_status_pass_count": sum(_bool(row.get("status_pass")) for row in plan_rows),
        "raw_trace_index_row_count": len(index_rows),
        "raw_trace_availability_row_count": len(availability_rows),
        "raw_trace_guard_row_count": len(guard_rows),
        "raw_trace_persisted_count": sum(_bool(row.get("raw_trace_persisted")) for row in index_rows),
        "raw_trace_missing_count": len(plan_rows) - len(index_rows),
        "raw_trace_step_count_total": raw_trace_step_count_total,
        "raw_trace_termination_counts": dict(sorted(termination_counts.items())),
        "raw_trace_profile_counts": dict(sorted(profile_counts.items())),
        "trace_step_counts_match_m3050": _all_true(index_rows, "trace_step_count_matches_m3050"),
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": _all_true(actor_rows, "status_pass"),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": _all_true(claim_rows, "status_pass"),
        "gate_matrix_row_count": len(gate_rows),
        "required_artifacts_present": required_artifacts_present,
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "environment_reset_run": bool(index_rows),
        "environment_step_run": bool(index_rows),
        "policy_action_run": bool(index_rows),
        "policy_rollout_run": bool(index_rows),
        "replay_run": False,
        "local_action_search_run": False,
        "numeric_target_tensor_materialized": False,
        "target_tensor_quality_claim_made": False,
        "fitting_run": False,
        "training_run": False,
        "validation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "actor_contract_shape_72_action_3": _all_true(actor_rows, "status_pass"),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "output_semantics": "direct_action",
        "output_components": ["steer", "throttle", "brake"],
        "hidden_oracle_actor_input_detected": _any_true(index_rows, "hidden_oracle_actor_input_required"),
        "target_labels_actor_visible": _any_true(index_rows, "target_labels_actor_visible"),
        "target_provenance_actor_visible": _any_true(index_rows, "target_provenance_actor_visible"),
        "ttc_actor_input_required": _any_true(index_rows, "ttc_actor_input_required"),
        "driver_performance_claim_made": False,
        "driver_performance_verdict_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "validation_result_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "next_blocker": NEXT_ID,
        "paths": {
            "summary": str(output_dir / "summary.json"),
            "raw_trace_index_rows": str(output_dir / "raw_trace_index_rows.csv"),
            "raw_trace_availability_rows": str(output_dir / "raw_trace_availability_rows.csv"),
            "raw_trace_guard_rows": str(output_dir / "raw_trace_guard_rows.csv"),
            "actor_contract_guard_rows": str(output_dir / "actor_contract_guard_rows.csv"),
            "claim_boundary_rows": str(output_dir / "claim_boundary_rows.csv"),
            "gate_matrix": str(output_dir / "gate_matrix.csv"),
            "doc": str(doc_path),
            "follow_up_manifest": str(follow_up_manifest),
        },
    }


def write_doc(path: Path, summary: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    status = "pass" if _bool(summary.get("status_pass")) else "fail_closed"
    path.write_text(
        f"""# M3059 Active Safety Driver v1 Offtrack-Dominant Behavior Raw Trace Capture Preflight

## Summary

- status: {status}
- result class: `{summary['result_class']}`
- decision: `{summary['decision']}`
- next blocker: `{NEXT_ID}`
- follow-up manifest: `experiments/manifests/{NEXT_ID}.json`

M3059 reruns the M3057 offtrack target tensor blocker denominator only to
persist raw actor-view observation/action/next-observation/reward/done/timeout
traces. The replay uses the same M3050 executable workload lineage and the same
M3048 action-headroom-constrained residual adapter recorded by M3050.

## Artifact Summary

```text
capture plan rows: {summary['capture_plan_row_count']}
capture plan rows passing precheck: {summary['capture_plan_status_pass_count']}
raw trace index rows: {summary['raw_trace_index_row_count']}
raw traces persisted: {summary['raw_trace_persisted_count']}
raw traces missing: {summary['raw_trace_missing_count']}
raw trace availability rows: {summary['raw_trace_availability_row_count']}
raw trace guard rows: {summary['raw_trace_guard_row_count']}
total captured steps: {summary['raw_trace_step_count_total']}
trace step counts match M3050: {summary['trace_step_counts_match_m3050']}
actor-contract guard rows: {summary['actor_contract_guard_row_count']}
claim-boundary rows: {summary['claim_boundary_row_count']}
gate rows: {summary['gate_matrix_row_count']}
```

## Supported Claims

M3059 supports only these bounded claims:

```text
raw actor-view trace capture was attempted for the 24 M3057 blocker rows
persisted trace files contain observation/action/next-observation/reward/done/timeout arrays
actor observation 72 and action 3 direct [steer, throttle, brake] contract is preserved
target labels, target provenance, source labels, route labels, outcome labels, progress labels, verdict labels, TTC, and oracle values remain outside actor inputs
M3060 result-audit manifest was registered
```

## Rejected Claims

M3059 rejects:

```text
numeric target tensor quality
target tensor materialization
fitting execution
fitted policy quality
repair success
driver performance
validation ranking promotion current-sim high-fidelity paper finite-window-vs-GRU full-driver or self-ID evidence
```

## Boundary

M3059 is raw trace capture only. It writes no target tensors, fitted weights, or
policy checkpoints and runs no local-action search, fitting, training,
validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU
comparison, paper evaluation, full-driver evaluation, or self-ID testing.
""",
        encoding="utf-8",
    )


def run(
    *,
    m3058_audit: Path,
    m3057_dir: Path,
    m3055_dir: Path,
    m3053_dir: Path,
    m3050_dir: Path,
    m3012_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
    device: str,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(
        m3058_audit=m3058_audit,
        m3057_dir=m3057_dir,
        m3055_dir=m3055_dir,
        m3053_dir=m3053_dir,
        m3050_dir=m3050_dir,
        m3012_dir=m3012_dir,
    )
    residual_path = Path(str(source["m3050_summary"].get("candidate_residual_reflex_layer", "")))
    residual = load_residual_artifact(residual_path)
    plan_rows = build_capture_plan(source)
    index_rows, availability_rows, guard_rows = capture_plan_rows(
        source=source,
        plan_rows=plan_rows,
        residual=residual,
        output_dir=output_dir,
        device=device,
    )
    write_json(
        follow_up_manifest,
        build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path, summary_path=paths["summary"]),
    )
    actor_rows = build_actor_contract_guard_rows(
        source=source,
        residual=residual,
        plan_rows=plan_rows,
        index_rows=index_rows,
        availability_rows=availability_rows,
        guard_rows=guard_rows,
    )
    claim_rows = build_claim_rows(index_rows=index_rows, follow_up_manifest_exists=follow_up_manifest.exists())

    write_csv_rows(paths["raw_trace_index_rows"], index_rows, fieldnames=RAW_TRACE_INDEX_FIELDNAMES)
    write_csv_rows(paths["raw_trace_availability_rows"], availability_rows, fieldnames=AVAILABILITY_FIELDNAMES)
    write_csv_rows(paths["raw_trace_guard_rows"], guard_rows, fieldnames=RAW_TRACE_GUARD_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)

    gate_rows = build_gate_rows(
        source=source,
        residual=residual,
        plan_rows=plan_rows,
        index_rows=index_rows,
        availability_rows=availability_rows,
        guard_rows=guard_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=False,
        follow_up_manifest_exists=follow_up_manifest.exists(),
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
        source=source,
        residual=residual,
        plan_rows=plan_rows,
        index_rows=index_rows,
        availability_rows=availability_rows,
        guard_rows=guard_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=False,
        device=device,
    )
    write_doc(doc_path, summary)
    write_json(paths["summary"], summary)

    required_artifacts_present = all(path.exists() for path in paths.values())
    gate_rows = build_gate_rows(
        source=source,
        residual=residual,
        plan_rows=plan_rows,
        index_rows=index_rows,
        availability_rows=availability_rows,
        guard_rows=guard_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
        follow_up_manifest_exists=follow_up_manifest.exists(),
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
        source=source,
        residual=residual,
        plan_rows=plan_rows,
        index_rows=index_rows,
        availability_rows=availability_rows,
        guard_rows=guard_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        device=device,
    )
    write_doc(doc_path, summary)
    write_json(paths["summary"], summary)
    write_run_state(
        paths["run_state"],
        {
            "milestone": MILESTONE_ID,
            "completed_at_utc": summary["generated_at_utc"],
            "output_dir": str(output_dir),
            "status_pass": summary["status_pass"],
            "gate_matrix_pass": summary["gate_matrix_pass"],
            "raw_trace_index_row_count": summary["raw_trace_index_row_count"],
            "raw_trace_persisted_count": summary["raw_trace_persisted_count"],
            "status": "completed" if summary["status_pass"] else "completed_fail_closed",
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3058-audit", type=Path, default=DEFAULT_M3058_AUDIT)
    parser.add_argument("--m3057-dir", type=Path, default=DEFAULT_M3057_DIR)
    parser.add_argument("--m3055-dir", type=Path, default=DEFAULT_M3055_DIR)
    parser.add_argument("--m3053-dir", type=Path, default=DEFAULT_M3053_DIR)
    parser.add_argument("--m3050-dir", type=Path, default=DEFAULT_M3050_DIR)
    parser.add_argument("--m3012-dir", type=Path, default=DEFAULT_M3012_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    summary = run(
        m3058_audit=args.m3058_audit,
        m3057_dir=args.m3057_dir,
        m3055_dir=args.m3055_dir,
        m3053_dir=args.m3053_dir,
        m3050_dir=args.m3050_dir,
        m3012_dir=args.m3012_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        device=args.device,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"raw_trace_index_row_count={summary['raw_trace_index_row_count']}")
    print(f"raw_trace_persisted_count={summary['raw_trace_persisted_count']}")
    print(f"raw_trace_missing_count={summary['raw_trace_missing_count']}")
    print(f"next_blocker={summary['next_blocker']}")


if __name__ == "__main__":
    main()
