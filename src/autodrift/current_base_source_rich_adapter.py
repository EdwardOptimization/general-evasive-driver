"""No-residual source-rich adapter for the current public-gate actor.

This module is intentionally narrower than the older v4 source-rich routes:
it evaluates the loaded actor directly and emits source-rich metadata for later
smoke runs. It does not require or load a residual head, does not train, and
does not convert rows into a proof corpus.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import time
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import (
    FaultSpec,
    NOMINAL_FAULT,
    _frame_info,
    _terminal_reason,
    apply_fault_to_env,
    load_scenario_config,
)
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.hidden_swap_gate import terminal_reason
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.temporal_action_boundary_outcome_miner import _base_half_width
from autodrift.temporal_action_response_mismatch import DELAY_STEPS, TemporalSnapshot
from autodrift.train_ppo import resolve_device
from autodrift.v4_low_margin_boundary_window_retarget import _append_progress, _snapshot_obstacle_body
from autodrift.v4_low_margin_new_data_route import (
    DEFAULT_HALF_WIDTH_DELTAS,
    DEFAULT_LATERAL_DELTAS,
    DEFAULT_OBSTACLE_TIMING_DELTAS,
    DEFAULT_TARGET_MARGINS,
    PLAN_FIELDS,
    SOURCE_GROUP_FIELDS,
    WARMUP_MODES,
    WARMUP_PROBE_FIELDS,
    build_fault_variants,
    build_source_groups,
    plan_boundary_candidates,
    warmup_action_delta,
)


POLICY_LABEL = "current_base_no_residual"

SOURCE_RICH_EXTRA_FIELDS = [
    "policy_label",
    "residual_head_required",
    "preferred_fault_fidelity_class",
    "wrong_fault_fidelity_class",
    "fault_onset_bucket",
    "source_vx",
    "source_vy",
    "source_yaw_rate",
    "source_ax",
    "source_ay",
    "current_frame_match_status",
    "action_divergence_status",
    "terminal_margin_sensitivity_status",
]

SOURCE_RICH_PLAN_FIELDS = [*PLAN_FIELDS, *SOURCE_RICH_EXTRA_FIELDS]

REQUIRED_SOURCE_RICH_METADATA_FIELDS = (
    "policy_label",
    "residual_head_required",
    "seed",
    "step",
    "warmup_mode",
    "preferred_fault",
    "preferred_fault_family",
    "preferred_fault_severity",
    "preferred_fault_fidelity_class",
    "wrong_fault",
    "wrong_fault_family",
    "wrong_fault_fidelity_class",
    "fault_family_pair",
    "source_axis",
    "fault_onset_bucket",
    "source_obstacle_body_x",
    "source_obstacle_body_y",
    "source_obstacle_half_width",
    "target_obstacle_body_x",
    "target_obstacle_body_y",
    "target_obstacle_half_width",
    "boundary_axis",
    "source_margin",
    "source_success",
    "source_collision",
    "source_terminal_reason",
    "current_frame_match_status",
    "action_divergence_status",
    "terminal_margin_sensitivity_status",
)


def parse_float_list(raw: str) -> tuple[float, ...]:
    values = [part.strip() for part in str(raw).split(",") if part.strip()]
    if not values:
        raise argparse.ArgumentTypeError("expected at least one comma-separated float")
    return tuple(float(value) for value in values)


def parse_int_list(raw: str) -> tuple[int, ...]:
    values = [part.strip() for part in str(raw).split(",") if part.strip()]
    if not values:
        raise argparse.ArgumentTypeError("expected at least one comma-separated integer")
    return tuple(int(value) for value in values)


def _bucket(value: float, width: float) -> str:
    if not np.isfinite(float(value)) or float(width) <= 0.0:
        return "missing"
    return str(int(np.floor(float(value) / float(width))))


def _fault_onset_bucket(fault: FaultSpec) -> str:
    step = int(fault.activation_step)
    if step <= 0:
        return "initial"
    if step <= 20:
        return "early"
    if step <= 60:
        return "mid"
    return "late"


def _apply_warmup(action: np.ndarray, delta: np.ndarray) -> np.ndarray:
    return np.clip(np.asarray(action, dtype=np.float32) + np.asarray(delta, dtype=np.float32), -1.0, 1.0).astype(np.float32)


def missing_required_metadata_fields(rows: list[dict[str, Any]]) -> list[str]:
    """Return required source-rich fields missing from at least one row."""

    missing: set[str] = set()
    for row in rows:
        for field in REQUIRED_SOURCE_RICH_METADATA_FIELDS:
            if field not in row:
                missing.add(field)
    if not rows:
        missing.update(REQUIRED_SOURCE_RICH_METADATA_FIELDS)
    return sorted(missing)


def enrich_source_group(group: dict[str, Any], *, preferred_fault: FaultSpec, wrong_fault: FaultSpec = NOMINAL_FAULT) -> dict[str, Any]:
    """Add source-rich fault metadata to an existing v4 source group row."""

    return {
        **group,
        "preferred_fault_fidelity_class": str(preferred_fault.fidelity_class),
        "wrong_fault_fidelity_class": str(wrong_fault.fidelity_class),
        "fault_onset_bucket": _fault_onset_bucket(preferred_fault),
    }


def source_rich_snapshot_meta(
    source_group: dict[str, Any],
    snapshot: TemporalSnapshot,
    *,
    source_index: int,
) -> dict[str, Any]:
    """Build source-rich metadata for a snapshot without residual-head state."""

    body_x, body_y = _snapshot_obstacle_body(snapshot)
    half_width = _base_half_width(snapshot)
    obs = np.asarray(snapshot.observation, dtype=np.float32)
    source_vx = float(obs[0] * 20.0) if obs.shape[0] > 0 else float("nan")
    source_vy = float(obs[1] * 12.0) if obs.shape[0] > 1 else float("nan")
    source_yaw_rate = float(obs[2] * 2.5) if obs.shape[0] > 2 else float("nan")
    source_ax = float(obs[3] * 12.0) if obs.shape[0] > 3 else float("nan")
    source_ay = float(obs[4] * 12.0) if obs.shape[0] > 4 else float("nan")
    source_group_id = int(source_group["source_group_id"])
    return {
        "source_group_id": source_group_id,
        "snapshot_uid": f"{source_group_id}:{int(snapshot.snapshot_id)}:{int(snapshot.step)}",
        "source_index": int(source_index),
        "seed": int(snapshot.seed),
        "step": int(snapshot.step),
        "warmup_mode": str(source_group["warmup_mode"]),
        "preferred_fault": str(source_group["preferred_fault"]),
        "preferred_fault_family": str(source_group["preferred_fault_family"]),
        "preferred_fault_severity": str(source_group["preferred_fault_severity"]),
        "preferred_fault_fidelity_class": str(source_group.get("preferred_fault_fidelity_class", "")),
        "wrong_fault": str(source_group["wrong_fault"]),
        "wrong_fault_family": str(source_group["wrong_fault_family"]),
        "wrong_fault_fidelity_class": str(source_group.get("wrong_fault_fidelity_class", "")),
        "fault_family_pair": str(source_group["fault_family_pair"]),
        "source_axis": str(source_group["source_axis"]),
        "fault_onset_bucket": str(source_group.get("fault_onset_bucket", "")),
        "horizon": 6,
        "source_obstacle_body_x": float(body_x),
        "source_obstacle_body_y": float(body_y),
        "source_obstacle_half_width": float(half_width),
        "fault_activation_step_delta": int(source_group.get("fault_activation_step_delta", 0)),
        "fault_severity_delta": float(source_group.get("fault_severity_delta", 0.0)),
        "fault_param_key": str(source_group.get("fault_param_key", "")),
        "road_curvature_bucket": "current_track",
        "initial_speed_bucket": _bucket(source_vx, 5.0),
        "policy_label": POLICY_LABEL,
        "residual_head_required": False,
        "source_vx": source_vx,
        "source_vy": source_vy,
        "source_yaw_rate": source_yaw_rate,
        "source_ax": source_ax,
        "source_ay": source_ay,
        "current_frame_match_status": "not_computed_in_adapter",
        "action_divergence_status": "not_computed_in_adapter",
        "terminal_margin_sensitivity_status": "not_computed_in_adapter",
    }


def replay_current_base_normal(
    *,
    model: Any,
    snapshot: TemporalSnapshot,
    env_config: Any,
    max_continuation_steps: int,
    device: torch.device,
) -> tuple[dict[str, Any], list[np.ndarray]]:
    """Replay a snapshot with the checkpoint actor directly, with no residual head."""

    env = copy.deepcopy(snapshot.env)
    obs = np.asarray(snapshot.observation, dtype=np.float32).copy()
    hidden = snapshot.hidden.detach().clone()
    max_steps = int(max_continuation_steps)
    if max_steps <= 0:
        max_steps = max(1, int(env_config.max_steps) - int(snapshot.step))
    actions: list[np.ndarray] = []
    rewards: list[float] = []
    betas: list[float] = []
    terminated = False
    truncated = False
    info = dict(snapshot.info)
    for _ in range(max_steps):
        action, next_hidden = deterministic_action_from_hidden(model, obs, hidden, device)
        actions.append(np.asarray(action, dtype=np.float32))
        hidden = next_hidden
        obs, reward, terminated, truncated, info = env.step(action)
        rewards.append(float(reward))
        betas.append(float(info.get("beta", float("nan"))))
        if terminated or truncated:
            break
    beta_abs_peak = float(np.nanmax(np.abs(betas))) if betas else float("nan")
    return {
        "steps": len(rewards),
        "return": float(np.sum(rewards)),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "success": not bool(terminated),
        "collision": bool(info.get("collision", False)),
        "terminal_reason": terminal_reason(info, terminated, truncated, env_config),
        "obstacle_completed": bool(info.get("obstacle_completed", False)),
        "min_obstacle_clearance": _finite_float(info.get("min_obstacle_clearance")),
        "obstacle_collision_radius": _finite_float(info.get("obstacle_collision_radius")),
        "min_clearance_margin": _finite_float(info.get("min_clearance_margin")),
        "beta_abs_peak": beta_abs_peak,
        "first_steer": float(actions[0][0]) if actions else float("nan"),
        "first_throttle": float(actions[0][1]) if actions else float("nan"),
        "first_brake": float(actions[0][2]) if actions else float("nan"),
    }, actions


def collect_current_base_warmup_snapshots(
    *,
    model: Any,
    env_config: Any,
    fault: FaultSpec,
    source_group: dict[str, Any],
    min_step: int,
    max_steps: int,
    snapshot_stride: int,
    max_snapshots_per_group: int,
    obstacle_longitudinal_min: float,
    obstacle_longitudinal_max: float,
    history_window_steps: int,
    warmup_steps: int,
    steer_amplitude: float,
    brake_amplitude: float,
    period_steps: int,
    start_snapshot_id: int,
    device: torch.device,
) -> tuple[list[TemporalSnapshot], dict[str, Any], dict[str, Any]]:
    """Collect source-rich snapshots with the actor's direct deterministic policy."""

    env = AutoDriftEnv(env_config)
    seed = int(source_group["seed"])
    warmup_mode = str(source_group["warmup_mode"])
    scenario_id = f"current_base_seed{seed}_{fault.name}_{warmup_mode}"
    snapshots: list[TemporalSnapshot] = []
    obs, info = env.reset(seed=seed)
    hidden = model.initial_hidden(1, device)
    fault_applied = False
    if int(fault.activation_step) <= 0:
        apply_fault_to_env(env, fault)
        fault_applied = True
        info = _frame_info(env)

    observation_by_step: dict[int, np.ndarray] = {}
    hidden_by_step: dict[int, torch.Tensor] = {}
    probe_steps = 0
    probe_steer_abs_sum = 0.0
    probe_brake_sum = 0.0
    min_probe_obstacle_distance = float("inf")
    terminated = False
    truncated = False
    while not (terminated or truncated) and int(env.step_count) < int(max_steps):
        step = int(env.step_count)
        if not fault_applied and step >= int(fault.activation_step):
            apply_fault_to_env(env, fault)
            fault_applied = True
            info = _frame_info(env)
        observation_by_step[step] = np.asarray(obs, dtype=np.float32).copy()
        hidden_by_step[step] = hidden.detach().clone()
        obstacle_distance = _finite_float(info.get("obstacle_distance"))
        if (
            step >= int(min_step)
            and step % max(1, int(snapshot_stride)) == 0
            and len(snapshots) < int(max_snapshots_per_group)
            and np.isfinite(obstacle_distance)
            and float(obstacle_longitudinal_min) <= obstacle_distance <= float(obstacle_longitudinal_max)
        ):
            history_start = max(0, step - int(history_window_steps))
            history_steps = tuple(item for item in range(history_start, step) if item in observation_by_step)
            history_observations = tuple(observation_by_step[item].copy() for item in history_steps)
            history_start_hidden = hidden_by_step.get(history_start, hidden_by_step[min(hidden_by_step)])
            delayed_hiddens = {
                int(delay): hidden_by_step[step - int(delay)].detach().clone()
                for delay in DELAY_STEPS
                if step - int(delay) in hidden_by_step
            }
            pre_fault_hidden = None
            if int(fault.activation_step) > 0 and step > int(fault.activation_step):
                pre_fault_step = max(0, int(fault.activation_step) - 1)
                if pre_fault_step in hidden_by_step:
                    pre_fault_hidden = hidden_by_step[pre_fault_step].detach().clone()
            try:
                obstacle_lateral = float(
                    env._obstacle_path_features(env.track.frame(env.state.x, env.state.y, env.state.psi))[1]
                    * env.config.track_width
                )
            except Exception:
                obstacle_lateral = float("nan")
            snapshots.append(
                TemporalSnapshot(
                    snapshot_id=start_snapshot_id + len(snapshots),
                    scenario_id=scenario_id,
                    seed=seed,
                    fault=fault,
                    step=step,
                    observation=np.asarray(obs, dtype=np.float32).copy(),
                    hidden=hidden.detach().clone(),
                    env=copy.deepcopy(env),
                    info=dict(info),
                    obstacle_distance=obstacle_distance,
                    obstacle_lateral_offset=obstacle_lateral,
                    history_steps=history_steps,
                    history_observations=history_observations,
                    history_start_hidden=history_start_hidden.detach().clone(),
                    delayed_hiddens=delayed_hiddens,
                    pre_fault_hidden=pre_fault_hidden,
                )
            )
        action, next_hidden = deterministic_action_from_hidden(model, np.asarray(obs, dtype=np.float32), hidden, device)
        if int(step) < int(warmup_steps):
            delta = warmup_action_delta(
                warmup_mode,
                step_index=step,
                steer_amplitude=float(steer_amplitude),
                brake_amplitude=float(brake_amplitude),
                period_steps=int(period_steps),
            )
            if np.any(np.abs(delta) > 0.0):
                probe_steps += 1
                probe_steer_abs_sum += float(abs(delta[0]))
                probe_brake_sum += float(max(delta[2], 0.0))
                if np.isfinite(obstacle_distance):
                    min_probe_obstacle_distance = min(min_probe_obstacle_distance, float(obstacle_distance))
                action = _apply_warmup(action, delta)
        obs, _, terminated, truncated, info = env.step(action)
        hidden = next_hidden

    terminal = _terminal_reason(info, terminated, truncated)
    beta = _finite_float(info.get("beta"))
    warmup_artifact = bool(
        warmup_mode != "natural_policy"
        and int(probe_steps) > 0
        and (bool(info.get("collision", False)) or terminal == "off_road" or (np.isfinite(beta) and abs(beta) > 1.2))
        and int(env.step_count) <= int(warmup_steps) + 5
    )
    source_row = {
        **source_group,
        "snapshots_collected": int(len(snapshots)),
        "terminal_reason": terminal,
        "success": not bool(terminated),
        "collision": bool(info.get("collision", False)),
        "probe_steps": int(probe_steps),
        "probe_steer_abs_sum": float(probe_steer_abs_sum),
        "probe_brake_sum": float(probe_brake_sum),
        "warmup_artifact": bool(warmup_artifact),
    }
    probe_row = {
        "source_group_id": int(source_group["source_group_id"]),
        "seed": seed,
        "warmup_mode": warmup_mode,
        "preferred_fault": fault.name,
        "probe_steps": int(probe_steps),
        "probe_steer_abs_sum": float(probe_steer_abs_sum),
        "probe_brake_sum": float(probe_brake_sum),
        "min_probe_obstacle_distance": float(min_probe_obstacle_distance) if np.isfinite(min_probe_obstacle_distance) else float("nan"),
        "terminal_reason": terminal,
        "collision": bool(info.get("collision", False)),
        "off_road": terminal == "off_road",
        "spin_out": bool(np.isfinite(beta) and abs(beta) > 1.2),
        "warmup_artifact": bool(warmup_artifact),
    }
    env.close()
    return snapshots, source_row, probe_row


def classify_adapter_result(
    *,
    actor_changed: bool,
    warmup_artifact_rows: int,
    source_snapshots: int,
    plan_rows: int,
    missing_metadata_fields: list[str],
) -> str:
    if bool(actor_changed):
        return "current_base_source_rich_adapter_contract_violation"
    if int(warmup_artifact_rows) > 0:
        return "current_base_source_rich_adapter_warmup_artifact"
    if missing_metadata_fields:
        return "current_base_source_rich_adapter_missing_metadata"
    if int(source_snapshots) <= 0 or int(plan_rows) <= 0:
        return "current_base_source_rich_adapter_sparse"
    return "current_base_source_rich_adapter_metadata_ready"


def _source_group_fieldnames() -> list[str]:
    return [*SOURCE_GROUP_FIELDS, "preferred_fault_fidelity_class", "wrong_fault_fidelity_class", "fault_onset_bucket"]


def run_current_base_source_rich_adapter(
    *,
    checkpoint_path: Path,
    scenario_config_path: Path,
    run_dir: Path,
    device: str,
    seed_start: int,
    seed_count: int,
    max_base_faults: int,
    max_fault_specs: int,
    max_source_groups: int,
    max_snapshots_per_group: int,
    max_candidates_per_snapshot: int,
    max_steps: int,
    min_step: int,
    snapshot_stride: int,
    warmup_steps: int,
    steer_amplitude: float,
    brake_amplitude: float,
    warmup_period_steps: int,
    max_continuation_steps: int,
    obstacle_timing_deltas: tuple[float, ...],
    lateral_deltas: tuple[float, ...],
    half_width_deltas: tuple[float, ...],
    target_margins: tuple[float, ...],
) -> dict[str, Any]:
    """Run the metadata adapter without residual-head loading or training."""

    start = time.time()
    run_dir.mkdir(parents=True, exist_ok=True)
    progress_path = run_dir / "progress.jsonl"
    if progress_path.exists():
        progress_path.unlink()
    scenario_config = load_scenario_config(scenario_config_path)
    env_config = load_env_config(Path(scenario_config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    if not model.is_online_recurrent:
        raise ValueError("current-base source-rich adapter requires an online recurrent checkpoint")
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    actor_checksum_before = model_parameter_checksum(model)

    fault_specs = build_fault_variants(
        list(scenario_config["faults"]),
        max_base_faults=int(max_base_faults),
        max_fault_specs=int(max_fault_specs),
        activation_deltas=(-3, 3),
        severity_deltas=(-0.04, 0.04),
    )
    fault_by_name = {fault.name: fault for fault in [NOMINAL_FAULT, *fault_specs]}
    source_groups = build_source_groups(
        seed_start=int(seed_start),
        seed_count=int(seed_count),
        fault_specs=fault_specs,
        warmup_modes=WARMUP_MODES,
        max_source_groups=int(max_source_groups),
    )

    source_group_rows: list[dict[str, Any]] = []
    warmup_rows: list[dict[str, Any]] = []
    source_result_rows: list[dict[str, Any]] = []
    plan_rows: list[dict[str, Any]] = []
    snapshot_index = 0
    for raw_group in source_groups:
        fault = fault_by_name[str(raw_group["preferred_fault"])]
        group = enrich_source_group(raw_group, preferred_fault=fault)
        group_start = time.time()
        snapshots, source_row, probe_row = collect_current_base_warmup_snapshots(
            model=model,
            env_config=env_config,
            fault=fault,
            source_group=group,
            min_step=int(min_step),
            max_steps=int(max_steps),
            snapshot_stride=int(snapshot_stride),
            max_snapshots_per_group=int(max_snapshots_per_group),
            obstacle_longitudinal_min=float(scenario_config.get("obstacle_longitudinal_min", -14.0)),
            obstacle_longitudinal_max=float(scenario_config.get("obstacle_longitudinal_max", 115.0)),
            history_window_steps=int(scenario_config.get("temporal_history_window_steps", 30)),
            warmup_steps=int(warmup_steps),
            steer_amplitude=float(steer_amplitude),
            brake_amplitude=float(brake_amplitude),
            period_steps=int(warmup_period_steps),
            start_snapshot_id=snapshot_index,
            device=resolved_device,
        )
        snapshot_index += len(snapshots)
        source_group_rows.append(source_row)
        warmup_rows.append(probe_row)
        _append_progress(
            progress_path,
            {
                "source_group_id": int(group["source_group_id"]),
                "stage": "collect",
                "snapshots": len(snapshots),
                "warmup_artifact": bool(source_row.get("warmup_artifact", False)),
                "elapsed_seconds": time.time() - group_start,
            },
        )
        for snapshot in snapshots:
            source_meta = source_rich_snapshot_meta(group, snapshot, source_index=len(source_result_rows))
            source_result, _ = replay_current_base_normal(
                model=model,
                snapshot=snapshot,
                env_config=env_config,
                max_continuation_steps=int(max_continuation_steps),
                device=resolved_device,
            )
            source_result_rows.append({**source_meta, **source_result})
            local_plan = plan_boundary_candidates(
                source_meta,
                source_result,
                alpha=0.0,
                target_margins=target_margins,
                obstacle_timing_deltas=obstacle_timing_deltas,
                lateral_deltas=lateral_deltas,
                half_width_deltas=half_width_deltas,
                collision_margin_floor=-0.05,
                safe_margin_ceiling=0.001,
                diagnostic_safe_margin_ceiling=0.02,
                max_candidates_per_snapshot=int(max_candidates_per_snapshot),
            )
            for row in local_plan:
                row["candidate_id"] = len(plan_rows)
                row.update({field: source_meta.get(field, "") for field in SOURCE_RICH_EXTRA_FIELDS})
                plan_rows.append(row)

    actor_checksum_after = model_parameter_checksum(model)
    warmup_artifact_rows = sum(1 for row in warmup_rows if bool(row.get("warmup_artifact", False)))
    missing_metadata = missing_required_metadata_fields(plan_rows)
    result_class = classify_adapter_result(
        actor_changed=bool(actor_checksum_before != actor_checksum_after),
        warmup_artifact_rows=int(warmup_artifact_rows),
        source_snapshots=int(len(source_result_rows)),
        plan_rows=int(len(plan_rows)),
        missing_metadata_fields=missing_metadata,
    )

    write_csv_rows(run_dir / "source_group_rows.csv", source_group_rows, fieldnames=_source_group_fieldnames())
    write_csv_rows(run_dir / "warmup_probe_rows.csv", warmup_rows, fieldnames=WARMUP_PROBE_FIELDS)
    write_csv_rows(run_dir / "source_result_rows.csv", source_result_rows)
    write_csv_rows(run_dir / "boundary_search_plan_rows.csv", plan_rows, fieldnames=SOURCE_RICH_PLAN_FIELDS)
    _write_proxy_limitations(run_dir / "fault_proxy_limitations.md", scenario_config)

    summary = {
        "run_type": "current_base_source_rich_adapter",
        "policy_label": POLICY_LABEL,
        "checkpoint": checkpoint_path,
        "scenario_config": scenario_config_path,
        "residual_head_required": False,
        "source_groups": int(len(source_groups)),
        "source_group_rows": int(len(source_group_rows)),
        "warmup_probe_rows": int(len(warmup_rows)),
        "warmup_artifact_rows": int(warmup_artifact_rows),
        "source_result_rows": int(len(source_result_rows)),
        "boundary_search_plan_rows": int(len(plan_rows)),
        "missing_required_metadata_fields": missing_metadata,
        "required_metadata_pass": not bool(missing_metadata),
        "actor_backbone_changed": bool(actor_checksum_before != actor_checksum_after),
        "base_actor_checksum_before": actor_checksum_before,
        "base_actor_checksum_after": actor_checksum_after,
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "result_class": result_class,
        "elapsed_seconds": float(time.time() - start),
        "summary_json": run_dir / "summary.json",
        "source_group_rows_csv": run_dir / "source_group_rows.csv",
        "warmup_probe_rows_csv": run_dir / "warmup_probe_rows.csv",
        "source_result_rows_csv": run_dir / "source_result_rows.csv",
        "boundary_search_plan_rows_csv": run_dir / "boundary_search_plan_rows.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def _write_proxy_limitations(path: Path, config: dict[str, Any]) -> None:
    future_only = config.get("future_only_faults", [])
    lines = [
        "# Current-Base Source-Rich Fault Proxy Limitations",
        "",
        "This adapter uses the current single-track model and current-model or",
        "current-model-proxy faults only. It does not make high-fidelity claims.",
        "",
        "Allowed claim:",
        "",
        "- metadata-ready source-rich current-base scenario generation.",
        "",
        "Forbidden claim:",
        "",
        "- physically faithful single-wheel, split-mu, halfshaft, stuck-caliper,",
        "  suspension, tire-temperature, or wheel-speed failure dynamics.",
        "",
        "Future high-fidelity-only faults listed by the scenario config:",
        "",
        *[f"- {item}" for item in future_only],
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emit current-base no-residual source-rich metadata.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seed-start", type=int, default=118300)
    parser.add_argument("--seed-count", type=int, default=2)
    parser.add_argument("--max-base-faults", type=int, default=4)
    parser.add_argument("--max-fault-specs", type=int, default=6)
    parser.add_argument("--max-source-groups", type=int, default=6)
    parser.add_argument("--max-snapshots-per-group", type=int, default=1)
    parser.add_argument("--max-candidates-per-snapshot", type=int, default=4)
    parser.add_argument("--max-steps", type=int, default=120)
    parser.add_argument("--min-step", type=int, default=25)
    parser.add_argument("--snapshot-stride", type=int, default=10)
    parser.add_argument("--warmup-steps", type=int, default=30)
    parser.add_argument("--steer-amplitude", type=float, default=0.04)
    parser.add_argument("--brake-amplitude", type=float, default=0.06)
    parser.add_argument("--warmup-period-steps", type=int, default=12)
    parser.add_argument("--max-continuation-steps", type=int, default=50)
    parser.add_argument("--obstacle-timing-deltas", type=parse_float_list, default=",".join(str(v) for v in DEFAULT_OBSTACLE_TIMING_DELTAS))
    parser.add_argument("--lateral-deltas", type=parse_float_list, default=",".join(str(v) for v in DEFAULT_LATERAL_DELTAS))
    parser.add_argument("--half-width-deltas", type=parse_float_list, default=",".join(str(v) for v in DEFAULT_HALF_WIDTH_DELTAS))
    parser.add_argument("--target-margins", type=parse_float_list, default=",".join(str(v) for v in DEFAULT_TARGET_MARGINS))
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = run_current_base_source_rich_adapter(
        checkpoint_path=args.checkpoint,
        scenario_config_path=args.scenario_config,
        run_dir=args.run_dir,
        device=args.device,
        seed_start=args.seed_start,
        seed_count=args.seed_count,
        max_base_faults=args.max_base_faults,
        max_fault_specs=args.max_fault_specs,
        max_source_groups=args.max_source_groups,
        max_snapshots_per_group=args.max_snapshots_per_group,
        max_candidates_per_snapshot=args.max_candidates_per_snapshot,
        max_steps=args.max_steps,
        min_step=args.min_step,
        snapshot_stride=args.snapshot_stride,
        warmup_steps=args.warmup_steps,
        steer_amplitude=args.steer_amplitude,
        brake_amplitude=args.brake_amplitude,
        warmup_period_steps=args.warmup_period_steps,
        max_continuation_steps=args.max_continuation_steps,
        obstacle_timing_deltas=args.obstacle_timing_deltas,
        lateral_deltas=args.lateral_deltas,
        half_width_deltas=args.half_width_deltas,
        target_margins=args.target_margins,
    )
    print(json.dumps({"result_class": summary["result_class"], "summary_json": str(summary["summary_json"])}, sort_keys=True))


if __name__ == "__main__":
    main()
