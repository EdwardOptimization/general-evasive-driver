"""Materialize M2859 response-prediction trace instrumentation artifacts."""

from __future__ import annotations

import argparse
import copy
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import torch

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import (
    DEFAULT_EXECUTABLE_SPECS,
    DEFAULT_EXECUTABLE_WORKLOAD,
    env_config_for_executable_profile,
    load_executable_specs,
    read_csv_rows,
    write_run_state,
)
from autodrift.controller_profile_runtime import profile_runtime_summary, wrap_env_with_profile_mask
from autodrift.engineering_controller_route_a_response_predictive_recurrent_belief_candidate_closed_loop_delta_panel import (
    DEFAULT_BASELINE_CHECKPOINT,
    DEFAULT_CANDIDATE_CHECKPOINT,
    load_subject_registry,
)
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import ActorPolicy
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2859-engineering-controller-route-a-response-predictive-recurrent-belief-"
    "response-prediction-trace-instrumentation-repair-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2860-engineering-controller-route-a-response-predictive-recurrent-belief-"
    "response-prediction-trace-instrumentation-repair-result-audit"
)
DEFAULT_M2858_AUDIT = Path(
    "docs/m2858-engineering-controller-route-a-response-predictive-recurrent-belief-"
    "per-step-telemetry-panel-materialization-result-audit.md"
)
DEFAULT_M2857_SUMMARY = Path(
    "runs/m2857_engineering_controller_route_a_response_predictive_recurrent_belief_"
    "per_step_telemetry_panel_materialization/summary.json"
)
DEFAULT_M2857_SURFACE_ROWS = Path(
    "runs/m2857_engineering_controller_route_a_response_predictive_recurrent_belief_"
    "per_step_telemetry_panel_materialization/telemetry_surface_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2859_engineering_controller_route_a_response_predictive_recurrent_belief_"
    "response_prediction_trace_instrumentation_repair"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2859-engineering-controller-route-a-response-predictive-recurrent-belief-"
    "response-prediction-trace-instrumentation-repair-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2860-engineering-controller-route-a-response-predictive-"
    "recurrent-belief-response-prediction-trace-instrumentation-repair-result-audit.json"
)
DEFAULT_EVAL_SEED_BASE = 285900
DEFAULT_ROW_COUNT = 16
DEFAULT_HORIZON_STEPS = 96
CANONICAL_PROFILE = "L3_online_gru"
CHECKPOINT_SUBJECTS = ("baseline", "candidate")
TARGET_NAMES = (
    "vx_norm",
    "vy_norm",
    "yaw_rate_norm",
    "ax_norm",
    "ay_norm",
    "steer_actuator_norm",
    "steer_rate_norm",
    "throttle_actuator",
    "brake_actuator",
)

CLAIM_SCOPE = (
    "M2859 bounded response-prediction trace instrumentation repair only. It "
    "runs closed-loop reset, policy action, and step calls only on pre-registered "
    "M2857 diagnostic surfaces, then computes actor-invisible response-prediction "
    "targets and errors after execution. It does not train, run PPO, replay, "
    "validate, rank, select a winner, promote a checkpoint, compute success-rate "
    "verdicts, or claim repair success, driver performance, paper evidence, "
    "finite-window-vs-GRU evidence, current-sim verdict, high-fidelity validation, "
    "full ideal driver completion, or level3 self-identification."
)
FORBIDDEN_INTERPRETATION = (
    "validation readiness or result, checkpoint ranking, controller ranking, "
    "winner selection, checkpoint promotion, success-rate verdict, repair success, "
    "driver performance, paper evidence, finite-window-vs-GRU conclusion, "
    "current-sim verdict, high-fidelity validation, full ideal driver completion, "
    "or level3 self-identification"
)

TRACE_FIELDNAMES = [
    "trace_id",
    "surface_id",
    "pair_id",
    "task_source_id",
    "profile_name",
    "checkpoint_subject",
    "checkpoint_path",
    "eval_seed",
    "step_index",
    "horizon_index",
    "target_step_index",
    "response_prediction_available",
    "target_available",
    "response_prediction_dim",
    "response_prediction_horizon",
    "prediction_error_norm",
    "prediction_error_mean_abs",
    "prediction_error_max_abs",
    "done_before_target",
    "gap_reason",
    "predicted_values",
    "target_values",
    "diagnostic_only",
    "actor_visible_allowed",
    "future_label_actor_visible",
    "hidden_oracle_actor_input_required",
    "ranking_admissible",
    "ordinary_success_denominator_allowed",
]
EPISODE_FIELDNAMES = [
    "surface_id",
    "pair_id",
    "task_source_id",
    "checkpoint_subject",
    "steps",
    "execution_status",
    "error_type",
    "error_message",
    "response_prediction_available",
    "response_prediction_dim",
    "response_prediction_horizon",
    "trace_row_count",
    "valid_prediction_row_count",
    "gap_row_count",
    "prediction_error_norm_mean",
    "prediction_error_norm_max",
    "prediction_error_mean_abs_mean",
    "response_prediction_error_source",
    "diagnostic_only",
    "ranking_admissible",
    "ordinary_success_denominator_allowed",
]
GAP_FIELDNAMES = [
    "gap_id",
    "surface_id",
    "pair_id",
    "task_source_id",
    "checkpoint_subject",
    "step_index",
    "horizon_index",
    "gap_reason",
    "actor_visible_allowed",
    "future_label_actor_visible",
    "hidden_oracle_actor_input_required",
    "claim_boundary",
]
GUARD_FIELDNAMES = ["guard_id", "guard_family", "status_pass", "observed", "expected", "claim_boundary"]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2859",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
GATE_FIELDNAMES = [
    "gate_id",
    "gate_tier",
    "gate_family",
    "status_pass",
    "observed",
    "expected",
    "row_count",
    "failure_type",
    "claim_boundary",
]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _finite_float(value: Any, default: float = float("nan")) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if np.isfinite(result) else default


def _json_vector(values: np.ndarray) -> str:
    return "[" + ",".join(f"{float(value):.8g}" for value in values.tolist()) + "]"


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "response_prediction_trace_rows": output_dir / "response_prediction_trace_rows.csv",
        "response_prediction_episode_rows": output_dir / "response_prediction_episode_rows.csv",
        "instrumentation_gap_rows": output_dir / "instrumentation_gap_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_source_artifacts(
    *,
    m2858_audit: Path,
    m2857_summary: Path,
    m2857_surface_rows: Path,
    m1690_workload: Path,
    executable_specs: Path,
) -> dict[str, Any]:
    paths = {
        "m2858_audit": m2858_audit,
        "m2857_summary": m2857_summary,
        "m2857_surface_rows": m2857_surface_rows,
        "m1690_workload": m1690_workload,
        "executable_specs": executable_specs,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    m1690_rows = read_csv_rows(m1690_workload)
    m1690_l3 = {
        str(row.get("task_source_id", "")): row
        for row in m1690_rows
        if str(row.get("profile_name", "")) == CANONICAL_PROFILE
    }
    specs = load_executable_specs(executable_specs) if executable_specs.exists() else []
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2858_audit_text": m2858_audit.read_text(encoding="utf-8") if m2858_audit.exists() else "",
        "m2857_summary": read_json(m2857_summary) if m2857_summary.exists() else {},
        "m2857_surface_rows": read_csv_rows(m2857_surface_rows),
        "m1690_l3_by_task_source": m1690_l3,
        "executable_specs": specs,
        "executable_spec_by_task_source": {str(spec["task_source_id"]): spec for spec in specs},
    }


def select_surface_rows(surface_rows: list[dict[str, str]], *, row_count: int) -> list[dict[str, str]]:
    explanatory = [row for row in surface_rows if str(row.get("surface_id", "")) == "m2850_explanatory"]
    selected = explanatory[: int(row_count)]
    if len(selected) < int(row_count):
        selected.extend(surface_rows[: int(row_count) - len(selected)])
    return selected


def collect_prediction_artifacts(
    *,
    selected_rows: list[dict[str, str]],
    source: dict[str, Any],
    subject_registry: dict[str, dict[str, Any]],
    output_dir: Path,
    eval_seed_base: int,
    horizon_steps: int,
    device: str,
    next_blocker: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    trace_rows: list[dict[str, Any]] = []
    episode_rows: list[dict[str, Any]] = []
    gap_rows: list[dict[str, Any]] = []
    for pair_index, surface in enumerate(selected_rows):
        eval_seed = int(eval_seed_base) + pair_index
        for subject in CHECKPOINT_SUBJECTS:
            try:
                traces, episode, gaps = run_single_subject_prediction_trace(
                    surface_row=surface,
                    source=source,
                    subject_entry=subject_registry[subject],
                    eval_seed=eval_seed,
                    horizon_steps=int(horizon_steps),
                    device=device,
                )
            except Exception as exc:  # noqa: BLE001 - failed instrumentation is an artifact row.
                traces = []
                gaps = [
                    gap_row(
                        surface,
                        subject=subject,
                        step_index="",
                        horizon_index="",
                        reason=f"{type(exc).__name__}: {exc}",
                    )
                ]
                episode = failed_episode_row(
                    surface,
                    subject=subject,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                )
            trace_rows.extend(traces)
            episode_rows.append(episode)
            gap_rows.extend(gaps)
        write_run_state(
            output_dir / "run_state.json",
            {
                "surface_count": len(selected_rows),
                "trace_row_count": len(trace_rows),
                "episode_row_count": len(episode_rows),
                "gap_row_count": len(gap_rows),
                "latest_pair_id": surface.get("pair_id", ""),
                "complete": False,
                "next_blocker": next_blocker,
            },
        )
    return trace_rows, episode_rows, gap_rows


def run_single_subject_prediction_trace(
    *,
    surface_row: Mapping[str, Any],
    source: dict[str, Any],
    subject_entry: dict[str, Any],
    eval_seed: int,
    horizon_steps: int,
    device: str,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    del device
    task_source_id = str(surface_row["task_source_id"])
    if task_source_id not in source["m1690_l3_by_task_source"]:
        raise KeyError(f"task_source_id {task_source_id} missing from M1690 L3 rows")
    if task_source_id not in source["executable_spec_by_task_source"]:
        raise KeyError(f"task_source_id {task_source_id} missing from executable specs")
    source_row = source["m1690_l3_by_task_source"][task_source_id]
    spec = copy.deepcopy(source["executable_spec_by_task_source"][task_source_id])
    spec.setdefault("env_config", {})
    spec["env_config"] = dict(spec["env_config"])
    spec["env_config"]["max_steps"] = int(horizon_steps)
    profile_config = read_json(source_row["profile_config_path"])
    env_config = env_config_for_executable_profile(executable_spec=spec, profile_config=profile_config)
    env = wrap_env_with_profile_mask(AutoDriftEnv(env_config), profile_config)
    model = subject_entry["model"]
    if int(getattr(model, "obs_dim", -1)) != int(env.observation_space.shape[0]):
        env.close()
        raise ValueError(f"model obs_dim {getattr(model, 'obs_dim', -1)} does not match env obs_dim")
    runtime = profile_runtime_summary(profile_config)
    policy = ActorPolicy(model, env_config, reset_hidden_policy=str(runtime["reset_hidden_policy"]))
    observations: list[np.ndarray] = []
    actions: list[np.ndarray] = []
    dones: list[bool] = []
    try:
        obs, info = env.reset(seed=int(eval_seed))
        del info
        policy.reset()
        terminated = False
        truncated = False
        for _step_index in range(int(horizon_steps)):
            observations.append(np.asarray(obs, dtype=np.float32).copy())
            action = np.asarray(policy.act(obs, {}), dtype=np.float32)
            actions.append(action.copy())
            obs, _reward, terminated, truncated, _info = env.step(action)
            done = bool(terminated or truncated)
            dones.append(done)
            if done:
                break
    finally:
        env.close()
    trace_rows, gap_rows = prediction_rows_from_episode(
        surface_row=surface_row,
        subject_entry=subject_entry,
        eval_seed=eval_seed,
        observations=observations,
        actions=actions,
        dones=dones,
    )
    episode = episode_row_from_prediction_rows(surface_row, subject_entry, trace_rows, gap_rows)
    return trace_rows, episode, gap_rows


def prediction_rows_from_episode(
    *,
    surface_row: Mapping[str, Any],
    subject_entry: Mapping[str, Any],
    eval_seed: int,
    observations: list[np.ndarray],
    actions: list[np.ndarray],
    dones: list[bool],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    model = subject_entry["model"]
    if not getattr(model, "is_online_recurrent", False):
        raise RuntimeError("response prediction trace requires online recurrent model")
    if getattr(model, "response_prediction_head", None) is None:
        raise RuntimeError("response prediction head is not enabled")
    response_dim = int(getattr(model, "response_prediction_dim", 0))
    response_horizon = int(getattr(model, "response_prediction_horizon", 0))
    if response_dim <= 0 or response_horizon <= 0:
        raise RuntimeError("invalid response prediction dimensions")
    device = next(model.parameters()).device
    obs_tensor = torch.as_tensor(np.asarray(observations, dtype=np.float32)[:, None, :], device=device)
    action_tensor = torch.as_tensor(np.asarray(actions, dtype=np.float32)[:, None, :], device=device)
    done_tensor = torch.as_tensor(np.asarray(dones, dtype=np.bool_)[:, None], device=device)
    hidden = model.initial_hidden(1, device)
    with torch.no_grad():
        predictions = model.predict_response_recurrent_sequence(obs_tensor, action_tensor, hidden, done_tensor)
    prediction_array = predictions[:, 0].detach().cpu().numpy()
    obs_array = np.asarray(observations, dtype=np.float32)
    done_array = np.asarray(dones, dtype=np.bool_)
    trace_rows: list[dict[str, Any]] = []
    gap_rows: list[dict[str, Any]] = []
    for step_index in range(prediction_array.shape[0]):
        for horizon_index in range(response_horizon):
            target_step = step_index + horizon_index + 1
            done_before_target = bool(np.any(done_array[step_index:target_step])) if target_step <= len(done_array) else True
            target_available = target_step < len(obs_array) and not done_before_target
            gap_reason = "" if target_available else "future_target_unavailable_due_to_terminal_or_horizon_end"
            predicted = prediction_array[step_index, horizon_index, :response_dim]
            if target_available:
                target = obs_array[target_step, :response_dim]
                error = predicted - target
                error_norm = float(np.linalg.norm(error))
                error_mean_abs = float(np.mean(np.abs(error)))
                error_max_abs = float(np.max(np.abs(error)))
            else:
                target = np.full(response_dim, np.nan, dtype=np.float32)
                error_norm = ""
                error_mean_abs = ""
                error_max_abs = ""
                gap_rows.append(
                    gap_row(
                        surface_row,
                        subject=str(subject_entry["subject"]),
                        step_index=step_index,
                        horizon_index=horizon_index,
                        reason=gap_reason,
                    )
                )
            trace_rows.append(
                {
                    "trace_id": (
                        f"{surface_row['pair_id']}-{subject_entry['subject']}-"
                        f"step-{step_index:04d}-h{horizon_index + 1}"
                    ),
                    "surface_id": surface_row["surface_id"],
                    "pair_id": surface_row["pair_id"],
                    "task_source_id": surface_row["task_source_id"],
                    "profile_name": surface_row["profile_name"],
                    "checkpoint_subject": subject_entry["subject"],
                    "checkpoint_path": str(subject_entry["checkpoint_path"]),
                    "eval_seed": int(eval_seed),
                    "step_index": int(step_index),
                    "horizon_index": int(horizon_index + 1),
                    "target_step_index": int(target_step) if target_available else "",
                    "response_prediction_available": True,
                    "target_available": bool(target_available),
                    "response_prediction_dim": int(response_dim),
                    "response_prediction_horizon": int(response_horizon),
                    "prediction_error_norm": error_norm,
                    "prediction_error_mean_abs": error_mean_abs,
                    "prediction_error_max_abs": error_max_abs,
                    "done_before_target": bool(done_before_target),
                    "gap_reason": gap_reason,
                    "predicted_values": _json_vector(predicted),
                    "target_values": _json_vector(target) if target_available else "",
                    "diagnostic_only": True,
                    "actor_visible_allowed": False,
                    "future_label_actor_visible": False,
                    "hidden_oracle_actor_input_required": False,
                    "ranking_admissible": False,
                    "ordinary_success_denominator_allowed": False,
                }
            )
    return trace_rows, gap_rows


def gap_row(
    surface_row: Mapping[str, Any],
    *,
    subject: str,
    step_index: int | str,
    horizon_index: int | str,
    reason: str,
) -> dict[str, Any]:
    return {
        "gap_id": f"m2859-gap-{surface_row.get('pair_id', '')}-{subject}-{step_index}-{horizon_index}",
        "surface_id": surface_row.get("surface_id", ""),
        "pair_id": surface_row.get("pair_id", ""),
        "task_source_id": surface_row.get("task_source_id", ""),
        "checkpoint_subject": subject,
        "step_index": step_index,
        "horizon_index": horizon_index,
        "gap_reason": reason,
        "actor_visible_allowed": False,
        "future_label_actor_visible": False,
        "hidden_oracle_actor_input_required": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def episode_row_from_prediction_rows(
    surface_row: Mapping[str, Any],
    subject_entry: Mapping[str, Any],
    trace_rows: list[dict[str, Any]],
    gap_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    valid_errors = [
        _finite_float(row["prediction_error_norm"])
        for row in trace_rows
        if _bool(row.get("target_available", False)) and _finite_float(row.get("prediction_error_norm")) == _finite_float(row.get("prediction_error_norm"))
    ]
    mean_abs = [
        _finite_float(row["prediction_error_mean_abs"])
        for row in trace_rows
        if _bool(row.get("target_available", False)) and _finite_float(row.get("prediction_error_mean_abs")) == _finite_float(row.get("prediction_error_mean_abs"))
    ]
    return {
        "surface_id": surface_row["surface_id"],
        "pair_id": surface_row["pair_id"],
        "task_source_id": surface_row["task_source_id"],
        "checkpoint_subject": subject_entry["subject"],
        "steps": len({row["step_index"] for row in trace_rows}),
        "execution_status": "completed",
        "error_type": "",
        "error_message": "",
        "response_prediction_available": bool(trace_rows),
        "response_prediction_dim": trace_rows[0]["response_prediction_dim"] if trace_rows else "",
        "response_prediction_horizon": trace_rows[0]["response_prediction_horizon"] if trace_rows else "",
        "trace_row_count": len(trace_rows),
        "valid_prediction_row_count": len(valid_errors),
        "gap_row_count": len(gap_rows),
        "prediction_error_norm_mean": float(np.mean(valid_errors)) if valid_errors else "",
        "prediction_error_norm_max": float(np.max(valid_errors)) if valid_errors else "",
        "prediction_error_mean_abs_mean": float(np.mean(mean_abs)) if mean_abs else "",
        "response_prediction_error_source": "actor_invisible_post_episode_future_observation_targets",
        "diagnostic_only": True,
        "ranking_admissible": False,
        "ordinary_success_denominator_allowed": False,
    }


def failed_episode_row(
    surface_row: Mapping[str, Any],
    *,
    subject: str,
    error_type: str,
    error_message: str,
) -> dict[str, Any]:
    return {
        "surface_id": surface_row.get("surface_id", ""),
        "pair_id": surface_row.get("pair_id", ""),
        "task_source_id": surface_row.get("task_source_id", ""),
        "checkpoint_subject": subject,
        "steps": 0,
        "execution_status": "failed",
        "error_type": error_type,
        "error_message": error_message,
        "response_prediction_available": False,
        "response_prediction_dim": "",
        "response_prediction_horizon": "",
        "trace_row_count": 0,
        "valid_prediction_row_count": 0,
        "gap_row_count": 1,
        "prediction_error_norm_mean": "",
        "prediction_error_norm_max": "",
        "prediction_error_mean_abs_mean": "",
        "response_prediction_error_source": "instrumentation_failed_gap_row_written",
        "diagnostic_only": True,
        "ranking_admissible": False,
        "ordinary_success_denominator_allowed": False,
    }


def build_actor_contract_guard_rows(
    *,
    subject_registry: dict[str, dict[str, Any]],
    trace_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        guard("m2859-actor-observation-shape", "actor_contract", P0_OBSERVATION_DIM == 72, P0_OBSERVATION_DIM, 72),
        guard("m2859-actor-action-shape", "actor_contract", ACTION_DIM == 3, ACTION_DIM, 3),
        guard(
            "m2859-baseline-response-head-enabled",
            "actor_contract",
            getattr(subject_registry["baseline"]["model"], "response_prediction_head", None) is not None,
            "baseline response head present",
            "present",
        ),
        guard(
            "m2859-candidate-response-head-enabled",
            "actor_contract",
            getattr(subject_registry["candidate"]["model"], "response_prediction_head", None) is not None,
            "candidate response head present",
            "present",
        ),
        guard(
            "m2859-no-future-label-actor-visible",
            "actor_contract",
            all(not _bool(row["future_label_actor_visible"]) for row in trace_rows),
            "future_label_actor_visible false",
            "all trace rows false",
        ),
        guard(
            "m2859-no-hidden-oracle-actor-input",
            "actor_contract",
            all(not _bool(row["hidden_oracle_actor_input_required"]) for row in trace_rows),
            "hidden_oracle_actor_input_required false",
            "all trace rows false",
        ),
    ]


def build_claim_boundary_rows(*, required_artifacts_present: bool, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    specs = [
        ("response_prediction_trace_artifacts", "artifact", True, required_artifacts_present, "M2859 required artifact set"),
        ("follow_up_result_audit_registered", "follow_up_route", True, follow_up_manifest_registered, "M2860 result audit"),
        ("training", "training", False, False, "future training route"),
        ("ppo", "training", False, False, "future training route"),
        ("validation_result", "validation", False, False, "future validation gate"),
        ("ranking_result", "ranking", False, False, "future comparison gate"),
        ("winner_selection", "promotion", False, False, "future promotion gate"),
        ("checkpoint_promotion", "promotion", False, False, "future promotion gate"),
        ("success_rate_verdict", "verdict", False, False, "future validation or promotion gate"),
        ("repair_success", "repair", False, False, "future audited repair route"),
        ("driver_performance", "performance", False, False, "future validation route"),
        ("paper_result", "paper", False, False, "Route B proof/generalization gates"),
        ("current_sim_verdict", "verdict", False, False, "future current-sim validation route"),
        ("high_fidelity_validation", "high_fidelity", False, False, "Route C validation route"),
        ("full_ideal_driver_completion", "goal", False, False, "full ideal driver gate"),
        ("level3_self_id", "self_id", False, False, "Route B self-ID proof gates"),
    ]
    return [claim_row(*spec) for spec in specs]


def guard(guard_id: str, family: str, status: bool, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": guard_id,
        "guard_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "claim_boundary": CLAIM_SCOPE,
    }


def claim_row(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m2859-claim-{claim_id}",
        "claim_family": family,
        "allowed_in_m2859": allowed,
        "claim_made": made,
        "status_pass": made == allowed if allowed else not made,
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def gate(
    gate_id: str,
    tier: str,
    family: str,
    status: bool,
    observed: Any,
    expected: Any,
    row_count: int,
    failure_type: str,
) -> dict[str, Any]:
    return {
        "gate_id": f"m2859-{gate_id}",
        "gate_tier": tier,
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "row_count": int(row_count),
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_rows(
    *,
    source: dict[str, Any],
    selected_rows: list[dict[str, str]],
    trace_rows: list[dict[str, Any]],
    episode_rows: list[dict[str, Any]],
    gap_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    row_count: int,
) -> list[dict[str, Any]]:
    valid_trace_count = sum(1 for row in trace_rows if _bool(row.get("target_available", False)))
    expected_episode_rows = len(selected_rows) * len(CHECKPOINT_SUBJECTS)
    return [
        gate(
            "source-artifacts-present",
            "proof",
            "lineage",
            all(source["source_exists"].values()),
            source["source_exists"],
            "M2858 audit M2857 summary/surfaces M1690 workload and executable specs present",
            len(source["source_exists"]),
            "lineage_invalid",
        ),
        gate(
            "m2857-unresolved-response-prediction-preserved",
            "proof",
            "lineage",
            int(source["m2857_summary"].get("response_prediction_available_count", -1)) == 0,
            source["m2857_summary"].get("response_prediction_available_count", ""),
            0,
            1,
            "proof_washout",
        ),
        gate(
            "selected-surface-count",
            "proof",
            "artifact",
            len(selected_rows) == int(row_count),
            len(selected_rows),
            int(row_count),
            len(selected_rows),
            "metric_artifact",
        ),
        gate(
            "episode-rows-written",
            "proof",
            "artifact",
            len(episode_rows) == expected_episode_rows,
            len(episode_rows),
            expected_episode_rows,
            len(episode_rows),
            "metric_artifact",
        ),
        gate(
            "response-prediction-traces-written",
            "proof",
            "artifact",
            bool(trace_rows) and valid_trace_count > 0,
            {"trace_rows": len(trace_rows), "valid": valid_trace_count},
            "nonempty trace rows with valid future targets",
            len(trace_rows),
            "metric_artifact",
        ),
        gate(
            "instrumentation-gaps-accounted",
            "proof",
            "artifact",
            bool(gap_rows),
            len(gap_rows),
            ">=1 terminal/horizon gap row",
            len(gap_rows),
            "metric_artifact",
        ),
        gate(
            "actor-contract-guards-pass",
            "promotion",
            "actor_contract",
            all(_bool(row["status_pass"]) for row in actor_rows),
            f"{sum(1 for row in actor_rows if _bool(row['status_pass']))}/{len(actor_rows)}",
            "all actor guards pass",
            len(actor_rows),
            "contract_violation",
        ),
        gate(
            "claim-boundary-guards-pass",
            "promotion",
            "claim_boundary",
            all(_bool(row["status_pass"]) for row in claim_rows),
            f"{sum(1 for row in claim_rows if _bool(row['status_pass']))}/{len(claim_rows)}",
            "all claim guards pass",
            len(claim_rows),
            "contract_violation",
        ),
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    subject_registry: dict[str, dict[str, Any]],
    selected_rows: list[dict[str, str]],
    trace_rows: list[dict[str, Any]],
    episode_rows: list[dict[str, Any]],
    gap_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    eval_seed_base: int,
    row_count: int,
    horizon_steps: int,
    device: str,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    valid_errors = [
        _finite_float(row["prediction_error_norm"])
        for row in trace_rows
        if _bool(row.get("target_available", False)) and np.isfinite(_finite_float(row.get("prediction_error_norm")))
    ]
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    execution_counts = Counter(str(row["execution_status"]) for row in episode_rows)
    surface_counts = Counter(str(row.get("surface_id", "")) for row in selected_rows)
    return {
        "result_class": "m2859_response_prediction_trace_instrumentation_repair_pass"
        if gate_matrix_pass
        else "m2859_response_prediction_trace_instrumentation_repair_failed_or_incomplete",
        "generated_at_utc": utc_timestamp(),
        "status_pass": bool(gate_matrix_pass),
        "milestone": milestone,
        "next_blocker": next_blocker,
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "response_prediction_trace_rows": str(paths["response_prediction_trace_rows"]),
        "response_prediction_episode_rows": str(paths["response_prediction_episode_rows"]),
        "instrumentation_gap_rows": str(paths["instrumentation_gap_rows"]),
        "actor_contract_guard_rows": str(paths["actor_contract_guard_rows"]),
        "claim_boundary_rows": str(paths["claim_boundary_rows"]),
        "gate_matrix": str(paths["gate_matrix"]),
        "run_state": str(paths["run_state"]),
        "doc": str(paths["doc"]),
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "m2858_audit": str(source["paths"]["m2858_audit"]),
        "m2857_summary": str(source["paths"]["m2857_summary"]),
        "m2857_surface_rows": str(source["paths"]["m2857_surface_rows"]),
        "baseline_checkpoint": str(subject_registry["baseline"]["checkpoint_path"]),
        "candidate_checkpoint": str(subject_registry["candidate"]["checkpoint_path"]),
        "eval_seed_base": int(eval_seed_base),
        "row_count_requested": int(row_count),
        "horizon_steps": int(horizon_steps),
        "device": device,
        "selected_surface_row_count": len(selected_rows),
        "selected_surface_counts": dict(sorted(surface_counts.items())),
        "episode_row_count": len(episode_rows),
        "response_prediction_trace_row_count": len(trace_rows),
        "valid_prediction_row_count": sum(1 for row in trace_rows if _bool(row.get("target_available", False))),
        "instrumentation_gap_row_count": len(gap_rows),
        "execution_status_counts": dict(sorted(execution_counts.items())),
        "response_prediction_dim": int(getattr(subject_registry["baseline"]["model"], "response_prediction_dim", 0)),
        "response_prediction_horizon": int(
            getattr(subject_registry["baseline"]["model"], "response_prediction_horizon", 0)
        ),
        "prediction_error_norm_mean": float(np.mean(valid_errors)) if valid_errors else "",
        "prediction_error_norm_max": float(np.max(valid_errors)) if valid_errors else "",
        "actor_contract_shape_72_action_3": True,
        "hidden_oracle_actor_input_required": False,
        "future_label_actor_visible": False,
        "ordinary_success_denominator_allowed": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_verdict_computed": False,
        "training_run": False,
        "ppo_used": False,
        "validation_result_claim_made": False,
        "driver_performance_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "level3_self_id_claim_made": False,
        "actor_contract_guard_rows_pass": all(_bool(row["status_pass"]) for row in actor_rows),
        "claim_boundary_rows_pass": all(_bool(row["status_pass"]) for row in claim_rows),
        "gate_matrix_pass": bool(gate_matrix_pass),
        "failed_gate_ids": [row["gate_id"] for row in gate_rows if not _bool(row["status_pass"])],
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def build_m2860_follow_up_manifest() -> dict[str, Any]:
    task_id = DEFAULT_NEXT_BLOCKER
    doc_path = f"docs/{task_id}.md"
    return {
        "id": task_id,
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
        "lineage": {
            "parent_checkpoint": [str(DEFAULT_BASELINE_CHECKPOINT), str(DEFAULT_CANDIDATE_CHECKPOINT)],
            "parent_dataset": [
                str(DEFAULT_OUTPUT_DIR / "summary.json"),
                str(DEFAULT_OUTPUT_DIR / "response_prediction_trace_rows.csv"),
                str(DEFAULT_OUTPUT_DIR / "response_prediction_episode_rows.csv"),
                str(DEFAULT_OUTPUT_DIR / "instrumentation_gap_rows.csv"),
                str(DEFAULT_DOC_PATH),
                str(DEFAULT_M2858_AUDIT),
                str(DEFAULT_M2857_SUMMARY),
                str(DEFAULT_M2857_SURFACE_ROWS),
            ],
            "parent_config": [
                "experiments/manifests/m2859-engineering-controller-route-a-response-predictive-recurrent-belief-response-prediction-trace-instrumentation-repair-preflight.json",
                "experiments/manifests/m2858-engineering-controller-route-a-response-predictive-recurrent-belief-per-step-telemetry-panel-materialization-result-audit.json",
            ],
            "parent_objective": [
                "audit M2859 response-prediction trace instrumentation repair before recipe interpretation"
            ],
            "derived_from": [DEFAULT_MILESTONE],
            "blocked_by": [
                "M2860 must audit M2859 response-prediction trace and gap artifacts before training recipe changes",
                "M2860 must preserve actor-invisible future labels",
                "M2860 must reject validation ranking promotion performance paper current-sim high-fidelity full-driver and self-ID claims",
            ],
            "supersedes": ["unaudited M2859 response-prediction trace interpretation"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{task_id}.md",
        "public_gates": [
            "M2860 must audit M2859 summary response prediction trace episode gap actor claim and gate artifacts",
            "M2860 must verify response-prediction targets stayed actor-invisible and post-episode diagnostic only",
            "M2860 must preserve actor 72/action 3 no hidden/oracle actor inputs and M2850/M2857 diagnostic boundaries",
            "M2860 must not run training validation ranking promotion or success-rate verdict computation",
            "M2860 must register one bounded next route or stop decision if M2859 artifacts are accepted",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run training",
            "do not run validation",
            "do not rank baseline and candidate checkpoints",
            "do not select a winner",
            "do not promote a checkpoint",
            "do not compute success-rate verdict metrics",
            "do not expose future labels to actor input",
            "do not claim repair success driver performance validation paper current-sim high-fidelity full ideal driver completion or self-ID result",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_response_predictive_recurrent_belief_failure_localization_training_recipe_redesign",
            "evidence_axis": "response_prediction_trace_instrumentation_repair_result_audit",
            "evidence_increment": "audits M2859 response-prediction trace instrumentation before deciding recipe or synthesis route",
            "claim_scope": "Result audit only; no training validation ranking winner promotion success-rate verdict repair-success driver-performance paper current-sim high-fidelity validation self-ID or full-driver claim",
            "stop_condition": [
                "stop if M2859 response prediction artifacts are incomplete",
                "stop if future labels became actor-visible",
                "stop if M2859 traces are used as ranking validation or optimization evidence",
                "stop if response-prediction trace evidence remains inconclusive after this repair",
            ],
            "fallback_plan": [
                "route to branch synthesis if response prediction remains inconclusive",
                "route to training recipe design if response prediction traces are accepted",
                "route to instrumentation repair if only schema/lineage failed",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2859 has produced response-prediction trace artifacts requiring audit",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "audit M2859 response-prediction trace instrumentation repair",
            "admission_evidence": [
                "M2859 summary and trace artifacts are expected before M2860 runs",
                "M2859 gap rows require audit before recipe interpretation",
            ],
            "blocked_shortcuts": [
                "no training PPO validation ranking promotion or success-rate verdict",
                "no driver-performance paper current-sim high-fidelity full ideal driver or self-ID claim",
            ],
            "allowed_updates": [
                doc_path,
                "M2860 status queue scoreboard and review",
                "one bounded follow-up manifest if audit accepts a next route",
            ],
            "next_stage_criteria": [
                "M2859 artifacts are accepted or rejected",
                "response-prediction trace/gap interpretation is preserved",
                "one bounded next route or stop is registered",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2860 audits Route A response-prediction traces and does not test history necessity or current-frame substitution.",
            "history_necessity_tests": [
                "M2859 response-prediction traces are not level3 self-identification evidence."
            ],
            "temporal_evidence_window": "M2843-M2859 response-predictive recurrent-belief branch.",
            "negative_result_policy": "If response-prediction traces are inconclusive, preserve the result and route to synthesis rather than weakening gates.",
            "allowed_claims": [
                "M2859 response-prediction trace instrumentation accepted or rejected",
                "bounded follow-up route registration",
                "no driver-performance verdict paper result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits new response-prediction trace instrumentation",
            "paper_verdict_delta": "no paper verdict; audit governs Route A response-prediction trace interpretation before recipe changes",
            "must_synthesize_if": [
                "M2859 response-prediction artifacts are incomplete",
                "M2859 cannot resolve availability beyond M2857",
                "M2859 exposes future labels or hidden/oracle inputs to actor input",
                "M2859 results are used as validation performance self-ID or paper evidence",
            ],
        },
        "hypothesis": "A bounded result audit can accept or reject M2859 response-prediction trace artifacts before recipe interpretation.",
        "success_criteria": [
            f"{doc_path} exists",
            "audit checks M2859 summary trace episode gap actor claim and gate rows",
            "audit preserves actor 72/action 3 no hidden/oracle labels future-label invisibility and claim boundary",
            "audit registers one bounded follow-up route or stop decision",
        ],
        "failure_criteria": [
            "M2860 runs new training validation ranking promotion or success-rate verdict computation",
            "M2860 hides M2859 gate failures or weakens actor/claim boundaries",
            "M2860 claims repair success driver performance validation readiness/result high-fidelity validation paper current-sim verdict full ideal driver completion or self-ID result",
        ],
        "decision_rule": "Pass only if M2860 audits M2859 artifacts under unchanged actor and claim boundaries without new execution or overclaiming.",
        "commands": [{"name": "result_audit", "command": "true"}],
        "required_artifacts": [{"path": doc_path, "type": "md"}],
        "baseline_checkpoints": [str(DEFAULT_BASELINE_CHECKPOINT), str(DEFAULT_CANDIDATE_CHECKPOINT)],
        "baseline_artifacts": [str(DEFAULT_OUTPUT_DIR / "summary.json")],
        "scoreboard_checkpoint": doc_path,
        "next_blocker": "",
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2859 Engineering Controller Route A Response-Predictive Recurrent-Belief Response-Prediction Trace Instrumentation Repair Preflight",
            "",
            "## Metadata",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- selected surface rows: {summary['selected_surface_row_count']}",
            f"- episode rows: {summary['episode_row_count']}",
            f"- response prediction trace rows: {summary['response_prediction_trace_row_count']}",
            f"- valid prediction rows: {summary['valid_prediction_row_count']}",
            f"- instrumentation gap rows: {summary['instrumentation_gap_row_count']}",
            f"- response prediction dim: {summary['response_prediction_dim']}",
            f"- response prediction horizon: {summary['response_prediction_horizon']}",
            f"- prediction error norm mean: {summary['prediction_error_norm_mean']}",
            f"- prediction error norm max: {summary['prediction_error_norm_max']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            f"- failed gates: {summary['failed_gate_ids'] or 'none'}",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            f"- next blocker: `{summary['next_blocker']}`",
            "",
            "## Route Boundary",
            "",
            "M2859 repairs instrumentation only. It calls the existing training-only",
            "response-prediction head after collecting closed-loop observations/actions,",
            "then compares predictions with future observation channels 0..8 as",
            "actor-invisible evaluator labels. The future labels are never fed to the",
            "actor at action time.",
            "",
            "## Actor And Claim Boundary",
            "",
            f"- actor observation shape: {P0_OBSERVATION_DIM}",
            f"- action shape: {ACTION_DIM}",
            "- hidden/oracle actor input required: false",
            "- future label actor-visible: false",
            "- ranking admissible: false",
            "- ordinary success denominator allowed: false",
            "- checkpoint promoted: false",
            "- driver-performance/self-ID/paper claims: false",
            "",
            "## Interpretation",
            "",
            "Allowed claim: M2859 materialized response-prediction trace and gap artifacts",
            "for the selected M2857 diagnostic surfaces. These artifacts require M2860",
            "result audit before any training-recipe interpretation.",
            "",
            "Forbidden interpretation:",
            "",
            FORBIDDEN_INTERPRETATION,
        ]
    )


def run_response_prediction_trace_instrumentation_repair(
    *,
    m2858_audit: Path | str = DEFAULT_M2858_AUDIT,
    m2857_summary: Path | str = DEFAULT_M2857_SUMMARY,
    m2857_surface_rows: Path | str = DEFAULT_M2857_SURFACE_ROWS,
    m1690_workload: Path | str = DEFAULT_EXECUTABLE_WORKLOAD,
    executable_specs: Path | str = DEFAULT_EXECUTABLE_SPECS,
    baseline_checkpoint: Path | str = DEFAULT_BASELINE_CHECKPOINT,
    candidate_checkpoint: Path | str = DEFAULT_CANDIDATE_CHECKPOINT,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    eval_seed_base: int = DEFAULT_EVAL_SEED_BASE,
    row_count: int = DEFAULT_ROW_COUNT,
    horizon_steps: int = DEFAULT_HORIZON_STEPS,
    device: str = "cpu",
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path), follow_up_manifest=Path(follow_up_manifest))
    source = load_source_artifacts(
        m2858_audit=Path(m2858_audit),
        m2857_summary=Path(m2857_summary),
        m2857_surface_rows=Path(m2857_surface_rows),
        m1690_workload=Path(m1690_workload),
        executable_specs=Path(executable_specs),
    )
    subject_registry = load_subject_registry(
        baseline_checkpoint=Path(baseline_checkpoint),
        candidate_checkpoint=Path(candidate_checkpoint),
        device=device,
    )
    selected_rows = select_surface_rows(source["m2857_surface_rows"], row_count=int(row_count))
    trace_rows, episode_rows, gap_rows = collect_prediction_artifacts(
        selected_rows=selected_rows,
        source=source,
        subject_registry=subject_registry,
        output_dir=output,
        eval_seed_base=int(eval_seed_base),
        horizon_steps=int(horizon_steps),
        device=device,
        next_blocker=next_blocker,
    )
    write_csv_rows(paths["response_prediction_trace_rows"], trace_rows, fieldnames=TRACE_FIELDNAMES)
    write_csv_rows(paths["response_prediction_episode_rows"], episode_rows, fieldnames=EPISODE_FIELDNAMES)
    write_csv_rows(paths["instrumentation_gap_rows"], gap_rows, fieldnames=GAP_FIELDNAMES)
    write_json(paths["follow_up_manifest"], build_m2860_follow_up_manifest())
    required_present = all(
        paths[key].exists()
        for key in (
            "response_prediction_trace_rows",
            "response_prediction_episode_rows",
            "instrumentation_gap_rows",
            "follow_up_manifest",
        )
    )
    actor_rows = build_actor_contract_guard_rows(subject_registry=subject_registry, trace_rows=trace_rows)
    claim_rows = build_claim_boundary_rows(
        required_artifacts_present=required_present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    gate_rows = build_gate_rows(
        source=source,
        selected_rows=selected_rows,
        trace_rows=trace_rows,
        episode_rows=episode_rows,
        gap_rows=gap_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        row_count=int(row_count),
    )
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        subject_registry=subject_registry,
        selected_rows=selected_rows,
        trace_rows=trace_rows,
        episode_rows=episode_rows,
        gap_rows=gap_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        eval_seed_base=int(eval_seed_base),
        row_count=int(row_count),
        horizon_steps=int(horizon_steps),
        device=device,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    write_run_state(paths["run_state"], {**summary, "complete": True})
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2858-audit", type=Path, default=DEFAULT_M2858_AUDIT)
    parser.add_argument("--m2857-summary", type=Path, default=DEFAULT_M2857_SUMMARY)
    parser.add_argument("--m2857-surface-rows", type=Path, default=DEFAULT_M2857_SURFACE_ROWS)
    parser.add_argument("--m1690-workload", type=Path, default=DEFAULT_EXECUTABLE_WORKLOAD)
    parser.add_argument("--executable-specs", type=Path, default=DEFAULT_EXECUTABLE_SPECS)
    parser.add_argument("--baseline-checkpoint", type=Path, default=DEFAULT_BASELINE_CHECKPOINT)
    parser.add_argument("--candidate-checkpoint", type=Path, default=DEFAULT_CANDIDATE_CHECKPOINT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--eval-seed-base", type=int, default=DEFAULT_EVAL_SEED_BASE)
    parser.add_argument("--row-count", type=int, default=DEFAULT_ROW_COUNT)
    parser.add_argument("--horizon-steps", type=int, default=DEFAULT_HORIZON_STEPS)
    parser.add_argument("--device", default="cpu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_response_prediction_trace_instrumentation_repair(
        m2858_audit=args.m2858_audit,
        m2857_summary=args.m2857_summary,
        m2857_surface_rows=args.m2857_surface_rows,
        m1690_workload=args.m1690_workload,
        executable_specs=args.executable_specs,
        baseline_checkpoint=args.baseline_checkpoint,
        candidate_checkpoint=args.candidate_checkpoint,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        eval_seed_base=args.eval_seed_base,
        row_count=args.row_count,
        horizon_steps=args.horizon_steps,
        device=args.device,
    )
    print(f"summary={summary['summary']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"next_blocker={summary['next_blocker']}")


if __name__ == "__main__":
    main()
