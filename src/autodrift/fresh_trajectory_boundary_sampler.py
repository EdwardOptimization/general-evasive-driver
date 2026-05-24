"""Fresh scenario sampler for terminal-boundary trajectory rows."""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import load_env_config
from autodrift.grounded_capability_action_target_miner import SurfaceConfig, parse_surface_config, risk_score
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.matched_history_outcome_gate import OutcomeSnapshot
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.terminal_margin_recovery_anchor import _rollout_first_action_override, parse_float_list
from autodrift.train_ppo import ActorCritic, resolve_device
from autodrift.trajectory_terminal_boundary_source_miner import (
    assigned_split,
    build_first_action_perturbations,
)


@dataclass
class FreshSnapshot:
    snapshot_id: int
    surface: str
    seed: int
    step: int
    observation: np.ndarray
    hidden: torch.Tensor
    env: AutoDriftEnv
    info: dict[str, Any]
    obstacle_distance: float
    obstacle_lateral_offset: float
    obstacle_visible: bool


EPISODE_FIELDNAMES = [
    "surface",
    "seed",
    "steps",
    "terminated",
    "truncated",
    "terminal_reason",
    "terminal_margin",
    "collision",
    "obstacle_completed",
    "snapshots_collected",
    "obstacle_label",
    "mu",
    "mass_scale",
    "tire_stiffness_scale",
    "brake_scale",
    "steer_tau_scale",
    "drive_tau_scale",
]

SNAPSHOT_FIELDNAMES = [
    "snapshot_id",
    "surface",
    "seed",
    "step",
    "obstacle_distance",
    "obstacle_lateral_offset",
    "obstacle_visible",
    "vx",
    "vy",
    "yaw_rate",
    "speed",
    "beta",
    "mu",
    "obstacle_label",
]

PREPASS_FIELDNAMES = [
    "snapshot_id",
    "surface",
    "seed",
    "step",
    "normal_success",
    "normal_collision",
    "normal_off_road",
    "normal_spin_out",
    "normal_terminal_reason",
    "normal_margin",
    "normal_risk",
    "normal_failed_rejected",
    "too_safe_rejected",
    "boundary_bucket",
    "base_steer",
    "base_throttle",
    "base_brake",
    "matched_snapshot_id",
    "matched_seed",
    "matched_step",
    "matched_distance",
]

PERTURBATION_FIELDNAMES = [
    "snapshot_id",
    "candidate_id",
    "surface",
    "seed",
    "step",
    "steer_delta",
    "throttle_delta",
    "brake_delta",
    "action_l2",
    "candidate_steer",
    "candidate_throttle",
    "candidate_brake",
    "success",
    "collision",
    "off_road",
    "spin_out",
    "terminal_reason",
    "margin",
    "risk",
    "return",
]

ACCEPTED_FIELDNAMES = [
    "snapshot_id",
    "surface",
    "seed",
    "step",
    "assigned_split",
    "boundary_bucket",
    "obstacle_distance",
    "obstacle_lateral_offset",
    "normal_margin",
    "normal_risk",
    "margin_sensitivity",
    "risk_sensitivity",
    "success_flip_count",
    "collision_flip_count",
    "off_road_flip_count",
    "spin_flip_count",
    "trajectory_boundary",
    "terminal_cliff",
    "matched_snapshot_id",
    "matched_seed",
    "matched_step",
    "history_margin_gap",
    "history_risk_gap",
    "history_action_critical",
    "acceptance_reason",
]


def _finite_float(value: Any, default: float = float("nan")) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    return parsed if np.isfinite(parsed) else float(default)


def _margin(result: dict[str, Any]) -> float:
    return _finite_float(result.get("min_clearance_margin"))


def _result_bool(result: dict[str, Any], key: str) -> bool:
    return bool(result.get(key, False))


def _terminal_reason(info: dict[str, Any], terminated: bool, truncated: bool) -> str:
    if bool(info.get("collision", False)):
        return "collision"
    if bool(info.get("obstacle_completed", False)):
        return "obstacle_completed"
    if bool(terminated):
        return "terminated"
    if bool(truncated):
        return "truncated"
    return "running"


def _as_outcome_snapshot(snapshot: FreshSnapshot, hidden: torch.Tensor | None = None) -> OutcomeSnapshot:
    return OutcomeSnapshot(
        seed=snapshot.seed,
        step=snapshot.step,
        observation=snapshot.observation.copy(),
        hidden=(hidden if hidden is not None else snapshot.hidden).detach().clone(),
        env=snapshot.env,
        info=dict(snapshot.info),
    )


def _snapshot_features(snapshot: FreshSnapshot) -> tuple[float, float, float, float, float, float]:
    obs = np.asarray(snapshot.observation, dtype=np.float32)
    vx = float(obs[0] * 20.0) if obs.shape[0] > 0 else float("nan")
    vy = float(obs[1] * 12.0) if obs.shape[0] > 1 else float("nan")
    yaw_rate = float(obs[2] * 2.5) if obs.shape[0] > 2 else float("nan")
    return (
        vx,
        vy,
        yaw_rate,
        float(snapshot.obstacle_distance),
        float(snapshot.obstacle_lateral_offset),
        float(snapshot.step),
    )


def _candidate_window(
    *,
    info: dict[str, Any],
    step: int,
    min_step: int,
    max_step: int,
    obstacle_longitudinal_min: float,
    obstacle_longitudinal_max: float,
) -> tuple[bool, str]:
    if int(step) < int(min_step) or int(step) > int(max_step):
        return False, "outside_step_window"
    obstacle_distance = _finite_float(info.get("obstacle_distance"))
    if not np.isfinite(obstacle_distance):
        return False, "obstacle_distance_not_finite"
    if obstacle_distance < float(obstacle_longitudinal_min) or obstacle_distance > float(obstacle_longitudinal_max):
        return False, "outside_distance_window"
    return True, "candidate"


def collect_surface_snapshots(
    *,
    model: ActorCritic,
    env_config: DriftEnvConfig,
    surface: str,
    seeds: list[int],
    min_step: int,
    max_step: int,
    snapshot_stride: int,
    max_snapshots_per_episode: int,
    target_obstacle_distance: float,
    obstacle_longitudinal_min: float,
    obstacle_longitudinal_max: float,
    device: torch.device,
    start_snapshot_id: int,
) -> tuple[list[FreshSnapshot], list[dict[str, Any]], list[dict[str, Any]]]:
    snapshots: list[FreshSnapshot] = []
    episode_rows: list[dict[str, Any]] = []
    skipped_rows: list[dict[str, Any]] = []
    snapshot_id = int(start_snapshot_id)
    env = AutoDriftEnv(env_config)
    try:
        for seed in seeds:
            obs, info = env.reset(seed=int(seed))
            hidden = model.initial_hidden(1, device)
            terminated = False
            truncated = False
            episode_candidates: list[FreshSnapshot] = []
            last_info = dict(info)
            while not (terminated or truncated):
                step = int(env.step_count)
                in_window, reason = _candidate_window(
                    info=info,
                    step=step,
                    min_step=min_step,
                    max_step=max_step,
                    obstacle_longitudinal_min=obstacle_longitudinal_min,
                    obstacle_longitudinal_max=obstacle_longitudinal_max,
                )
                stride_ok = step % max(int(snapshot_stride), 1) == 0
                if in_window and stride_ok:
                    obstacle_distance = _finite_float(info.get("obstacle_distance"))
                    episode_candidates.append(
                        FreshSnapshot(
                            snapshot_id=-1,
                            surface=str(surface),
                            seed=int(seed),
                            step=step,
                            observation=np.asarray(obs, dtype=np.float32).copy(),
                            hidden=hidden.detach().clone(),
                            env=copy.deepcopy(env),
                            info=dict(info),
                            obstacle_distance=obstacle_distance,
                            obstacle_lateral_offset=_finite_float(info.get("obstacle_lateral_offset")),
                            obstacle_visible=bool(info.get("obstacle_perception_visible", False)),
                        )
                    )
                elif step >= int(min_step) and step % max(int(snapshot_stride), 1) == 0:
                    skipped_rows.append(
                        {
                            "surface": str(surface),
                            "seed": int(seed),
                            "step": step,
                            "skip_reason": reason,
                            "obstacle_distance": _finite_float(info.get("obstacle_distance")),
                        }
                    )
                action, next_hidden = deterministic_action_from_hidden(model, np.asarray(obs, dtype=np.float32), hidden, device)
                obs, _, terminated, truncated, info = env.step(action)
                hidden = next_hidden
                last_info = dict(info)
            episode_candidates.sort(
                key=lambda item: (
                    abs(float(item.obstacle_distance) - float(target_obstacle_distance)),
                    abs(float(item.obstacle_lateral_offset)),
                    int(item.step),
                )
            )
            selected_candidates = episode_candidates[: int(max_snapshots_per_episode)]
            selected_keys = {(int(item.seed), int(item.step)) for item in selected_candidates}
            for candidate in selected_candidates:
                candidate.snapshot_id = snapshot_id
                snapshots.append(candidate)
                snapshot_id += 1
            for candidate in episode_candidates[int(max_snapshots_per_episode) :]:
                skipped_rows.append(
                    {
                        "surface": str(surface),
                        "seed": int(seed),
                        "step": int(candidate.step),
                        "skip_reason": "snapshot_budget_exceeded",
                        "obstacle_distance": float(candidate.obstacle_distance),
                    }
                )
            episode_rows.append(
                {
                    "surface": str(surface),
                    "seed": int(seed),
                    "steps": int(last_info.get("step", env.step_count)),
                    "terminated": bool(terminated),
                    "truncated": bool(truncated),
                    "terminal_reason": _terminal_reason(last_info, terminated, truncated),
                    "terminal_margin": _finite_float(last_info.get("min_clearance_margin")),
                    "collision": bool(last_info.get("collision", False)),
                    "obstacle_completed": bool(last_info.get("obstacle_completed", False)),
                    "snapshots_collected": int(len(selected_keys)),
                    "obstacle_label": str(last_info.get("obstacle_label", "")),
                    "mu": _finite_float(last_info.get("mu")),
                    "mass_scale": _finite_float(last_info.get("mass_scale")),
                    "tire_stiffness_scale": _finite_float(last_info.get("tire_stiffness_scale")),
                    "brake_scale": _finite_float(last_info.get("brake_scale")),
                    "steer_tau_scale": _finite_float(last_info.get("steer_tau_scale")),
                    "drive_tau_scale": _finite_float(last_info.get("drive_tau_scale")),
                }
            )
    finally:
        env.close()
    return snapshots, episode_rows, skipped_rows


def find_matched_snapshot(
    snapshot: FreshSnapshot,
    candidates: list[FreshSnapshot],
    *,
    max_vx_gap: float,
    max_vy_gap: float,
    max_yaw_rate_gap: float,
    max_obstacle_x_gap: float,
    max_obstacle_y_gap: float,
    max_step_gap: int,
) -> tuple[FreshSnapshot | None, float]:
    source = _snapshot_features(snapshot)
    best: FreshSnapshot | None = None
    best_distance = float("inf")
    for candidate in candidates:
        if candidate.seed == snapshot.seed or candidate.surface != snapshot.surface:
            continue
        other = _snapshot_features(candidate)
        gaps = np.abs(np.asarray(source, dtype=float) - np.asarray(other, dtype=float))
        if (
            gaps[0] <= float(max_vx_gap)
            and gaps[1] <= float(max_vy_gap)
            and gaps[2] <= float(max_yaw_rate_gap)
            and gaps[3] <= float(max_obstacle_x_gap)
            and gaps[4] <= float(max_obstacle_y_gap)
            and gaps[5] <= float(max_step_gap)
        ):
            normalized = np.asarray(
                [
                    gaps[0] / max(max_vx_gap, 1e-6),
                    gaps[1] / max(max_vy_gap, 1e-6),
                    gaps[2] / max(max_yaw_rate_gap, 1e-6),
                    gaps[3] / max(max_obstacle_x_gap, 1e-6),
                    gaps[4] / max(max_obstacle_y_gap, 1e-6),
                    gaps[5] / max(max_step_gap, 1e-6),
                ],
                dtype=float,
            )
            distance = float(np.linalg.norm(normalized))
            if distance < best_distance:
                best = candidate
                best_distance = distance
    return best, best_distance


def boundary_bucket(normal_margin: float, terminal_cliff_margin: float, near_boundary_margin: float, max_prepass_margin: float) -> str:
    if not np.isfinite(normal_margin):
        return "non_finite"
    if normal_margin < 0.0:
        return "failed"
    if normal_margin <= float(terminal_cliff_margin):
        return "terminal_cliff"
    if normal_margin <= float(near_boundary_margin):
        return "near_boundary"
    if normal_margin <= float(max_prepass_margin):
        return "wide_but_sensitive"
    return "too_safe"


def evaluate_snapshot(
    *,
    model: ActorCritic,
    snapshot: FreshSnapshot,
    matched_snapshot: FreshSnapshot | None,
    matched_distance: float,
    steer_deltas: tuple[float, ...],
    throttle_deltas: tuple[float, ...],
    brake_deltas: tuple[float, ...],
    terminal_cliff_margin: float,
    near_boundary_margin: float,
    max_prepass_margin: float,
    min_margin_sensitivity: float,
    min_risk_sensitivity: float,
    min_history_margin_gap: float,
    min_history_risk_gap: float,
    max_continuation_steps: int,
    heldout_fraction: float,
    device: torch.device,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any] | None, dict[str, Any] | None]:
    base_action, _ = deterministic_action_from_hidden(model, snapshot.observation, snapshot.hidden, device)
    baseline = _rollout_first_action_override(
        model=model,
        snapshot=_as_outcome_snapshot(snapshot),
        first_action=base_action,
        max_continuation_steps=max_continuation_steps,
        device=device,
    )
    normal_margin = _margin(baseline)
    normal_risk = risk_score(baseline)
    failed = (
        not _result_bool(baseline, "success")
        or _result_bool(baseline, "collision")
        or _result_bool(baseline, "off_road")
        or _result_bool(baseline, "spin_out")
        or not np.isfinite(normal_margin)
        or normal_margin < 0.0
    )
    bucket = boundary_bucket(normal_margin, terminal_cliff_margin, near_boundary_margin, max_prepass_margin)
    too_safe = bool(not failed and bucket == "too_safe")

    matched_seed = int(matched_snapshot.seed) if matched_snapshot is not None else -1
    matched_step = int(matched_snapshot.step) if matched_snapshot is not None else -1
    prepass = {
        "snapshot_id": int(snapshot.snapshot_id),
        "surface": str(snapshot.surface),
        "seed": int(snapshot.seed),
        "step": int(snapshot.step),
        "normal_success": _result_bool(baseline, "success"),
        "normal_collision": _result_bool(baseline, "collision"),
        "normal_off_road": _result_bool(baseline, "off_road"),
        "normal_spin_out": _result_bool(baseline, "spin_out"),
        "normal_terminal_reason": str(baseline.get("terminal_reason", "")),
        "normal_margin": normal_margin,
        "normal_risk": normal_risk,
        "normal_failed_rejected": bool(failed),
        "too_safe_rejected": bool(too_safe),
        "boundary_bucket": bucket,
        "base_steer": float(base_action[0]),
        "base_throttle": float(base_action[1]),
        "base_brake": float(base_action[2]),
        "matched_snapshot_id": int(matched_snapshot.snapshot_id) if matched_snapshot is not None else -1,
        "matched_seed": matched_seed,
        "matched_step": matched_step,
        "matched_distance": float(matched_distance) if matched_snapshot is not None else float("nan"),
    }

    if failed or too_safe:
        rejected = {
            "snapshot_id": int(snapshot.snapshot_id),
            "surface": str(snapshot.surface),
            "seed": int(snapshot.seed),
            "step": int(snapshot.step),
            "rejection_reason": "normal_failed_rejected" if failed else "too_safe_rejected",
            "normal_margin": normal_margin,
            "normal_risk": normal_risk,
            "boundary_bucket": bucket,
        }
        return prepass, [], None, rejected

    perturbation_rows: list[dict[str, Any]] = []
    for item in build_first_action_perturbations(
        base_action,
        steer_deltas=steer_deltas,
        throttle_deltas=throttle_deltas,
        brake_deltas=brake_deltas,
    ):
        result = _rollout_first_action_override(
            model=model,
            snapshot=_as_outcome_snapshot(snapshot),
            first_action=item["action"],
            max_continuation_steps=max_continuation_steps,
            device=device,
        )
        perturbation_rows.append(
            {
                "snapshot_id": int(snapshot.snapshot_id),
                "candidate_id": int(item["candidate_id"]),
                "surface": str(snapshot.surface),
                "seed": int(snapshot.seed),
                "step": int(snapshot.step),
                "steer_delta": float(item["steer_delta"]),
                "throttle_delta": float(item["throttle_delta"]),
                "brake_delta": float(item["brake_delta"]),
                "action_l2": float(item["action_l2"]),
                "candidate_steer": float(item["action"][0]),
                "candidate_throttle": float(item["action"][1]),
                "candidate_brake": float(item["action"][2]),
                "success": _result_bool(result, "success"),
                "collision": _result_bool(result, "collision"),
                "off_road": _result_bool(result, "off_road"),
                "spin_out": _result_bool(result, "spin_out"),
                "terminal_reason": str(result.get("terminal_reason", "")),
                "margin": _margin(result),
                "risk": risk_score(result),
                "return": _finite_float(result.get("return")),
            }
        )

    margins = np.asarray([_finite_float(row["margin"]) for row in perturbation_rows], dtype=float)
    risks = np.asarray([_finite_float(row["risk"]) for row in perturbation_rows], dtype=float)
    finite_margins = margins[np.isfinite(margins)]
    finite_risks = risks[np.isfinite(risks)]
    margin_sensitivity = float(np.max(finite_margins) - np.min(finite_margins)) if len(finite_margins) else float("nan")
    risk_sensitivity = float(np.max(finite_risks) - np.min(finite_risks)) if len(finite_risks) else float("nan")
    success_flip_count = sum(bool(row["success"]) != _result_bool(baseline, "success") for row in perturbation_rows)
    collision_flip_count = sum(bool(row["collision"]) != _result_bool(baseline, "collision") for row in perturbation_rows)
    off_road_flip_count = sum(bool(row["off_road"]) != _result_bool(baseline, "off_road") for row in perturbation_rows)
    spin_flip_count = sum(bool(row["spin_out"]) != _result_bool(baseline, "spin_out") for row in perturbation_rows)
    trajectory_boundary = bool(
        (np.isfinite(margin_sensitivity) and margin_sensitivity >= float(min_margin_sensitivity))
        or (np.isfinite(risk_sensitivity) and risk_sensitivity >= float(min_risk_sensitivity))
        or success_flip_count > 0
        or collision_flip_count > 0
        or off_road_flip_count > 0
        or spin_flip_count > 0
    )
    terminal_cliff = bool(np.isfinite(normal_margin) and normal_margin <= float(terminal_cliff_margin))

    history_margin_gap = float("nan")
    history_risk_gap = float("nan")
    history_action_critical = False
    if matched_snapshot is not None:
        matched_action, _ = deterministic_action_from_hidden(model, snapshot.observation, matched_snapshot.hidden, device)
        matched_result = _rollout_first_action_override(
            model=model,
            snapshot=_as_outcome_snapshot(snapshot, hidden=matched_snapshot.hidden),
            first_action=matched_action,
            max_continuation_steps=max_continuation_steps,
            device=device,
        )
        matched_margin = _margin(matched_result)
        matched_risk = risk_score(matched_result)
        history_margin_gap = normal_margin - matched_margin if np.isfinite(normal_margin) and np.isfinite(matched_margin) else float("nan")
        history_risk_gap = matched_risk - normal_risk if np.isfinite(matched_risk) and np.isfinite(normal_risk) else float("nan")
        history_worse = (
            (_result_bool(baseline, "success") and not _result_bool(matched_result, "success"))
            or (not _result_bool(baseline, "collision") and _result_bool(matched_result, "collision"))
            or (not _result_bool(baseline, "off_road") and _result_bool(matched_result, "off_road"))
            or (not _result_bool(baseline, "spin_out") and _result_bool(matched_result, "spin_out"))
        )
        history_action_critical = bool(
            history_worse
            or (np.isfinite(history_margin_gap) and history_margin_gap >= float(min_history_margin_gap))
            or (np.isfinite(history_risk_gap) and history_risk_gap >= float(min_history_risk_gap))
        )

    accepted = bool(trajectory_boundary or history_action_critical)
    if history_action_critical:
        acceptance_reason = "history_action_critical"
    elif trajectory_boundary:
        acceptance_reason = "trajectory_boundary"
    elif terminal_cliff:
        acceptance_reason = "terminal_cliff_not_sensitive"
    else:
        acceptance_reason = "insensitive"
    row = {
        "snapshot_id": int(snapshot.snapshot_id),
        "surface": str(snapshot.surface),
        "seed": int(snapshot.seed),
        "step": int(snapshot.step),
        "assigned_split": assigned_split(int(snapshot.snapshot_id), heldout_fraction),
        "boundary_bucket": bucket,
        "obstacle_distance": float(snapshot.obstacle_distance),
        "obstacle_lateral_offset": float(snapshot.obstacle_lateral_offset),
        "normal_margin": normal_margin,
        "normal_risk": normal_risk,
        "margin_sensitivity": margin_sensitivity,
        "risk_sensitivity": risk_sensitivity,
        "success_flip_count": int(success_flip_count),
        "collision_flip_count": int(collision_flip_count),
        "off_road_flip_count": int(off_road_flip_count),
        "spin_flip_count": int(spin_flip_count),
        "trajectory_boundary": trajectory_boundary,
        "terminal_cliff": terminal_cliff,
        "matched_snapshot_id": int(matched_snapshot.snapshot_id) if matched_snapshot is not None else -1,
        "matched_seed": matched_seed,
        "matched_step": matched_step,
        "history_margin_gap": history_margin_gap,
        "history_risk_gap": history_risk_gap,
        "history_action_critical": history_action_critical,
        "acceptance_reason": acceptance_reason,
    }
    if accepted:
        return prepass, perturbation_rows, row, None
    rejected = dict(row)
    rejected["rejection_reason"] = acceptance_reason
    return prepass, perturbation_rows, None, rejected


def classify_fresh_result(
    *,
    accepted_rows: int,
    trajectory_boundary_rows: int,
    history_action_critical_rows: int,
    prepass_rows: int,
    normal_failed_rejected: int,
    too_safe_rejected: int,
    unique_seeds: int,
    unique_step_buckets: int,
    unique_distance_buckets: int,
    max_seed_dominance: float,
    max_bucket_dominance: float,
    min_accepted_rows: int,
    min_trajectory_rows: int,
    min_history_rows: int,
    min_unique_seeds: int,
    min_unique_step_buckets: int,
    min_unique_distance_buckets: int,
    max_seed_dominance_threshold: float,
    max_bucket_dominance_threshold: float,
) -> str:
    if int(prepass_rows) == 0:
        return "fresh_surface_empty"
    if int(normal_failed_rejected) == int(prepass_rows):
        return "normal_failed_only"
    if int(normal_failed_rejected) + int(too_safe_rejected) == int(prepass_rows):
        return "too_safe_only" if int(too_safe_rejected) > 0 else "normal_failed_only"
    if int(accepted_rows) == 0:
        return "fresh_surface_empty"
    if int(history_action_critical_rows) <= 0 and int(trajectory_boundary_rows) > 0:
        return "history_insensitive"
    volume_ok = (
        int(accepted_rows) >= int(min_accepted_rows)
        and int(trajectory_boundary_rows) >= int(min_trajectory_rows)
        and int(history_action_critical_rows) >= int(min_history_rows)
    )
    diversity_ok = (
        int(unique_seeds) >= int(min_unique_seeds)
        and int(unique_step_buckets) >= int(min_unique_step_buckets)
        and int(unique_distance_buckets) >= int(min_unique_distance_buckets)
        and float(max_seed_dominance) <= float(max_seed_dominance_threshold)
        and float(max_bucket_dominance) <= float(max_bucket_dominance_threshold)
    )
    if volume_ok and diversity_ok:
        return "fresh_source_positive"
    return "fresh_source_sparse"


def _bucket(value: float, width: float) -> int:
    if not np.isfinite(value):
        return -1
    return int(np.floor(float(value) / max(float(width), 1e-9)))


def summarize_sampling(
    *,
    episode_rows: list[dict[str, Any]],
    snapshot_rows: list[dict[str, Any]],
    prepass_rows: list[dict[str, Any]],
    accepted_rows: list[dict[str, Any]],
    rejected_rows: list[dict[str, Any]],
    min_accepted_rows: int,
    min_trajectory_rows: int,
    min_history_rows: int,
    min_unique_seeds: int,
    min_unique_step_buckets: int,
    min_unique_distance_buckets: int,
    max_seed_dominance: float,
    max_bucket_dominance: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    accepted_frame = pd.DataFrame(accepted_rows)
    prepass_frame = pd.DataFrame(prepass_rows)
    rejected_frame = pd.DataFrame(rejected_rows)
    normal_failed_rejected = int(prepass_frame["normal_failed_rejected"].astype(bool).sum()) if not prepass_frame.empty else 0
    too_safe_rejected = int(prepass_frame["too_safe_rejected"].astype(bool).sum()) if not prepass_frame.empty else 0
    trajectory_boundary_rows = int(accepted_frame["trajectory_boundary"].astype(bool).sum()) if not accepted_frame.empty else 0
    history_action_critical_rows = int(accepted_frame["history_action_critical"].astype(bool).sum()) if not accepted_frame.empty else 0
    terminal_cliff_rows = int(accepted_frame["terminal_cliff"].astype(bool).sum()) if not accepted_frame.empty else 0
    if accepted_frame.empty:
        unique_seeds = 0
        unique_step_buckets = 0
        unique_distance_buckets = 0
        seed_dominance = 0.0
        bucket_dominance = 0.0
        source_summary: list[dict[str, Any]] = []
        split_summary: list[dict[str, Any]] = []
    else:
        step_bucket = accepted_frame["step"].astype(int).map(lambda item: _bucket(float(item), 10.0))
        distance_bucket = accepted_frame["obstacle_distance"].astype(float).map(lambda item: _bucket(float(item), 5.0))
        seed_counts = accepted_frame["seed"].value_counts()
        bucket_counts = pd.DataFrame({"step": step_bucket, "distance": distance_bucket}).value_counts()
        unique_seeds = int(accepted_frame["seed"].nunique())
        unique_step_buckets = int(step_bucket.nunique())
        unique_distance_buckets = int(distance_bucket.nunique())
        seed_dominance = float(seed_counts.max() / max(len(accepted_frame), 1))
        bucket_dominance = float(bucket_counts.max() / max(len(accepted_frame), 1))
        source_summary = (
            accepted_frame.assign(step_bucket=step_bucket, distance_bucket=distance_bucket)
            .groupby(["surface", "boundary_bucket"], observed=True)
            .agg(
                rows=("snapshot_id", "count"),
                trajectory_boundary_rows=("trajectory_boundary", "sum"),
                history_action_critical_rows=("history_action_critical", "sum"),
                terminal_cliff_rows=("terminal_cliff", "sum"),
            )
            .reset_index()
            .to_dict(orient="records")
        )
        split_summary = (
            accepted_frame.groupby("assigned_split", observed=True)
            .agg(
                rows=("snapshot_id", "count"),
                trajectory_boundary_rows=("trajectory_boundary", "sum"),
                history_action_critical_rows=("history_action_critical", "sum"),
                terminal_cliff_rows=("terminal_cliff", "sum"),
            )
            .reset_index()
            .to_dict(orient="records")
        )
    evaluated_frames = []
    if not accepted_frame.empty and "margin_sensitivity" in accepted_frame.columns:
        evaluated_frames.append(accepted_frame)
    if not rejected_frame.empty and "margin_sensitivity" in rejected_frame.columns:
        evaluated_frames.append(rejected_frame[rejected_frame["margin_sensitivity"].notna()].copy())
    evaluated_frame = pd.concat(evaluated_frames, ignore_index=True) if evaluated_frames else pd.DataFrame()
    margin_sensitivity = (
        evaluated_frame["margin_sensitivity"].astype(float)
        if not evaluated_frame.empty and "margin_sensitivity" in evaluated_frame.columns
        else pd.Series(dtype=float)
    )
    risk_sensitivity = (
        evaluated_frame["risk_sensitivity"].astype(float)
        if not evaluated_frame.empty and "risk_sensitivity" in evaluated_frame.columns
        else pd.Series(dtype=float)
    )
    result_class = classify_fresh_result(
        accepted_rows=len(accepted_rows),
        trajectory_boundary_rows=trajectory_boundary_rows,
        history_action_critical_rows=history_action_critical_rows,
        prepass_rows=len(prepass_rows),
        normal_failed_rejected=normal_failed_rejected,
        too_safe_rejected=too_safe_rejected,
        unique_seeds=unique_seeds,
        unique_step_buckets=unique_step_buckets,
        unique_distance_buckets=unique_distance_buckets,
        max_seed_dominance=seed_dominance,
        max_bucket_dominance=bucket_dominance,
        min_accepted_rows=min_accepted_rows,
        min_trajectory_rows=min_trajectory_rows,
        min_history_rows=min_history_rows,
        min_unique_seeds=min_unique_seeds,
        min_unique_step_buckets=min_unique_step_buckets,
        min_unique_distance_buckets=min_unique_distance_buckets,
        max_seed_dominance_threshold=max_seed_dominance,
        max_bucket_dominance_threshold=max_bucket_dominance,
    )
    summary = {
        "episodes_attempted": int(len(episode_rows)),
        "episodes_completed": int(len(episode_rows)),
        "snapshots_collected": int(len(snapshot_rows)),
        "prepass_rows": int(len(prepass_rows)),
        "normal_failed_rejected": int(normal_failed_rejected),
        "too_safe_rejected": int(too_safe_rejected),
        "trajectory_boundary_rows": int(trajectory_boundary_rows),
        "history_action_critical_rows": int(history_action_critical_rows),
        "terminal_cliff_rows": int(terminal_cliff_rows),
        "accepted_rows": int(len(accepted_rows)),
        "perturbation_evaluated_rows": int(len(evaluated_frame)),
        "heldout_rows": (
            int(accepted_frame["assigned_split"].astype(str).eq("heldout").sum()) if not accepted_frame.empty else 0
        ),
        "unique_seeds": int(unique_seeds),
        "unique_step_buckets": int(unique_step_buckets),
        "unique_distance_buckets": int(unique_distance_buckets),
        "max_seed_dominance": float(seed_dominance),
        "max_bucket_dominance": float(bucket_dominance),
        "margin_sensitivity_mean": float(margin_sensitivity.mean()) if len(margin_sensitivity) else float("nan"),
        "margin_sensitivity_p95": float(np.nanpercentile(margin_sensitivity.to_numpy(), 95)) if len(margin_sensitivity) else float("nan"),
        "risk_sensitivity_mean": float(risk_sensitivity.mean()) if len(risk_sensitivity) else float("nan"),
        "risk_sensitivity_p95": float(np.nanpercentile(risk_sensitivity.to_numpy(), 95)) if len(risk_sensitivity) else float("nan"),
        "success_flip_count": int(evaluated_frame["success_flip_count"].astype(int).sum()) if not evaluated_frame.empty else 0,
        "collision_flip_count": int(evaluated_frame["collision_flip_count"].astype(int).sum()) if not evaluated_frame.empty else 0,
        "off_road_flip_count": int(evaluated_frame["off_road_flip_count"].astype(int).sum()) if not evaluated_frame.empty else 0,
        "spin_flip_count": int(evaluated_frame["spin_flip_count"].astype(int).sum()) if not evaluated_frame.empty else 0,
        "rejected_rows": int(len(rejected_rows)),
        "rejection_counts": (
            rejected_frame["rejection_reason"].value_counts().to_dict() if not rejected_frame.empty else {}
        ),
        "result_class": result_class,
        "fresh_source_positive": bool(result_class == "fresh_source_positive"),
    }
    return source_summary, split_summary, summary


def _snapshot_row(snapshot: FreshSnapshot) -> dict[str, Any]:
    vx, vy, yaw_rate, _, _, _ = _snapshot_features(snapshot)
    return {
        "snapshot_id": int(snapshot.snapshot_id),
        "surface": str(snapshot.surface),
        "seed": int(snapshot.seed),
        "step": int(snapshot.step),
        "obstacle_distance": float(snapshot.obstacle_distance),
        "obstacle_lateral_offset": float(snapshot.obstacle_lateral_offset),
        "obstacle_visible": bool(snapshot.obstacle_visible),
        "vx": vx,
        "vy": vy,
        "yaw_rate": yaw_rate,
        "speed": _finite_float(snapshot.info.get("speed")),
        "beta": _finite_float(snapshot.info.get("beta")),
        "mu": _finite_float(snapshot.info.get("mu")),
        "obstacle_label": str(snapshot.info.get("obstacle_label", "")),
    }


def run_fresh_trajectory_boundary_sampler(
    *,
    checkpoint_path: Path,
    surface_configs: tuple[SurfaceConfig, ...],
    seed_start: int,
    seed_count: int,
    min_step: int,
    max_step: int,
    snapshot_stride: int,
    max_snapshots_per_episode: int,
    target_obstacle_distance: float,
    obstacle_longitudinal_min: float,
    obstacle_longitudinal_max: float,
    steer_deltas: tuple[float, ...],
    throttle_deltas: tuple[float, ...],
    brake_deltas: tuple[float, ...],
    terminal_cliff_margin: float,
    near_boundary_margin: float,
    max_prepass_margin: float,
    min_margin_sensitivity: float,
    min_risk_sensitivity: float,
    min_history_margin_gap: float,
    min_history_risk_gap: float,
    max_continuation_steps: int,
    heldout_fraction: float,
    max_vx_gap: float,
    max_vy_gap: float,
    max_yaw_rate_gap: float,
    max_obstacle_x_gap: float,
    max_obstacle_y_gap: float,
    max_match_step_gap: int,
    min_accepted_rows: int,
    min_trajectory_rows: int,
    min_history_rows: int,
    min_unique_seeds: int,
    min_unique_step_buckets: int,
    min_unique_distance_buckets: int,
    max_seed_dominance: float,
    max_bucket_dominance: float,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    checksum_before = model_parameter_checksum(model)

    snapshots: list[FreshSnapshot] = []
    episode_rows: list[dict[str, Any]] = []
    skipped_rows: list[dict[str, Any]] = []
    seeds = list(range(int(seed_start), int(seed_start) + int(seed_count)))
    for surface_index, surface_config in enumerate(surface_configs):
        surface_seeds = seeds[surface_index :: max(len(surface_configs), 1)]
        env_config = load_env_config(surface_config.env_config_path)
        surface_snapshots, surface_episodes, surface_skipped = collect_surface_snapshots(
            model=model,
            env_config=env_config,
            surface=surface_config.surface,
            seeds=surface_seeds,
            min_step=min_step,
            max_step=max_step if max_step > 0 else env_config.max_steps - 2,
            snapshot_stride=snapshot_stride,
            max_snapshots_per_episode=max_snapshots_per_episode,
            target_obstacle_distance=target_obstacle_distance,
            obstacle_longitudinal_min=obstacle_longitudinal_min,
            obstacle_longitudinal_max=obstacle_longitudinal_max,
            device=resolved_device,
            start_snapshot_id=len(snapshots),
        )
        snapshots.extend(surface_snapshots)
        episode_rows.extend(surface_episodes)
        skipped_rows.extend(surface_skipped)

    snapshot_rows = [_snapshot_row(snapshot) for snapshot in snapshots]
    prepass_rows: list[dict[str, Any]] = []
    perturbation_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    for snapshot in snapshots:
        matched, matched_distance = find_matched_snapshot(
            snapshot,
            snapshots,
            max_vx_gap=max_vx_gap,
            max_vy_gap=max_vy_gap,
            max_yaw_rate_gap=max_yaw_rate_gap,
            max_obstacle_x_gap=max_obstacle_x_gap,
            max_obstacle_y_gap=max_obstacle_y_gap,
            max_step_gap=max_match_step_gap,
        )
        prepass, perturbations, accepted, rejected = evaluate_snapshot(
            model=model,
            snapshot=snapshot,
            matched_snapshot=matched,
            matched_distance=matched_distance,
            steer_deltas=steer_deltas,
            throttle_deltas=throttle_deltas,
            brake_deltas=brake_deltas,
            terminal_cliff_margin=terminal_cliff_margin,
            near_boundary_margin=near_boundary_margin,
            max_prepass_margin=max_prepass_margin,
            min_margin_sensitivity=min_margin_sensitivity,
            min_risk_sensitivity=min_risk_sensitivity,
            min_history_margin_gap=min_history_margin_gap,
            min_history_risk_gap=min_history_risk_gap,
            max_continuation_steps=max_continuation_steps,
            heldout_fraction=heldout_fraction,
            device=resolved_device,
        )
        prepass_rows.append(prepass)
        perturbation_rows.extend(perturbations)
        if accepted is not None:
            accepted_rows.append(accepted)
        if rejected is not None:
            rejected_rows.append(rejected)

    source_summary, split_summary, aggregate = summarize_sampling(
        episode_rows=episode_rows,
        snapshot_rows=snapshot_rows,
        prepass_rows=prepass_rows,
        accepted_rows=accepted_rows,
        rejected_rows=rejected_rows,
        min_accepted_rows=min_accepted_rows,
        min_trajectory_rows=min_trajectory_rows,
        min_history_rows=min_history_rows,
        min_unique_seeds=min_unique_seeds,
        min_unique_step_buckets=min_unique_step_buckets,
        min_unique_distance_buckets=min_unique_distance_buckets,
        max_seed_dominance=max_seed_dominance,
        max_bucket_dominance=max_bucket_dominance,
    )
    checksum_after = model_parameter_checksum(model)
    summary = {
        "run_type": "fresh_trajectory_boundary_sampler",
        "checkpoint": checkpoint_path,
        "surface_configs": {item.surface: item.env_config_path for item in surface_configs},
        "seed_start": int(seed_start),
        "seed_count": int(seed_count),
        "min_step": int(min_step),
        "max_step": int(max_step),
        "snapshot_stride": int(snapshot_stride),
        "max_snapshots_per_episode": int(max_snapshots_per_episode),
        "target_obstacle_distance": float(target_obstacle_distance),
        "obstacle_longitudinal_min": float(obstacle_longitudinal_min),
        "obstacle_longitudinal_max": float(obstacle_longitudinal_max),
        "steer_deltas": steer_deltas,
        "throttle_deltas": throttle_deltas,
        "brake_deltas": brake_deltas,
        "terminal_cliff_margin": float(terminal_cliff_margin),
        "near_boundary_margin": float(near_boundary_margin),
        "max_prepass_margin": float(max_prepass_margin),
        "min_margin_sensitivity": float(min_margin_sensitivity),
        "min_risk_sensitivity": float(min_risk_sensitivity),
        "min_history_margin_gap": float(min_history_margin_gap),
        "min_history_risk_gap": float(min_history_risk_gap),
        "max_continuation_steps": int(max_continuation_steps),
        "device": str(resolved_device),
        "episode_summary_csv": run_dir / "episode_summary.csv",
        "snapshot_candidates_csv": run_dir / "snapshot_candidates.csv",
        "prepass_rows_csv": run_dir / "prepass_rows.csv",
        "perturbation_rollouts_csv": run_dir / "perturbation_rollouts.csv",
        "accepted_rows_csv": run_dir / "accepted_rows.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
        "source_summary_csv": run_dir / "source_summary.csv",
        "split_summary_csv": run_dir / "split_summary.csv",
        "skipped_windows_csv": run_dir / "skipped_windows.csv",
        "model_checksum_before": checksum_before,
        "model_checksum_after": checksum_after,
        "actor_parameters_changed": bool(checksum_before != checksum_after),
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        **aggregate,
    }

    write_csv_rows(run_dir / "episode_summary.csv", episode_rows, fieldnames=EPISODE_FIELDNAMES)
    write_csv_rows(run_dir / "snapshot_candidates.csv", snapshot_rows, fieldnames=SNAPSHOT_FIELDNAMES)
    write_csv_rows(run_dir / "prepass_rows.csv", prepass_rows, fieldnames=PREPASS_FIELDNAMES)
    write_csv_rows(run_dir / "perturbation_rollouts.csv", perturbation_rows, fieldnames=PERTURBATION_FIELDNAMES)
    write_csv_rows(run_dir / "accepted_rows.csv", accepted_rows, fieldnames=ACCEPTED_FIELDNAMES)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
    write_csv_rows(run_dir / "source_summary.csv", source_summary)
    write_csv_rows(run_dir / "split_summary.csv", split_summary)
    write_csv_rows(run_dir / "skipped_windows.csv", skipped_rows)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Sample fresh terminal-boundary trajectory rows.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--surface-config", type=parse_surface_config, action="append", required=True)
    parser.add_argument("--seed-start", type=int, default=30000)
    parser.add_argument("--seed-count", type=int, default=512)
    parser.add_argument("--min-step", type=int, default=10)
    parser.add_argument("--max-step", type=int, default=0)
    parser.add_argument("--snapshot-stride", type=int, default=3)
    parser.add_argument("--max-snapshots-per-episode", type=int, default=8)
    parser.add_argument("--target-obstacle-distance", type=float, default=2.0)
    parser.add_argument("--obstacle-longitudinal-min", type=float, default=-5.0)
    parser.add_argument("--obstacle-longitudinal-max", type=float, default=80.0)
    parser.add_argument("--steer-deltas", type=parse_float_list, default=(-0.04, -0.02, -0.01, 0.01, 0.02, 0.04))
    parser.add_argument("--throttle-deltas", type=parse_float_list, default=(-0.06, -0.03, 0.03, 0.06))
    parser.add_argument("--brake-deltas", type=parse_float_list, default=(-0.06, -0.03, 0.03, 0.06))
    parser.add_argument("--terminal-cliff-margin", type=float, default=0.02)
    parser.add_argument("--near-boundary-margin", type=float, default=0.15)
    parser.add_argument("--max-prepass-margin", type=float, default=0.50)
    parser.add_argument("--min-margin-sensitivity", type=float, default=0.02)
    parser.add_argument("--min-risk-sensitivity", type=float, default=0.02)
    parser.add_argument("--min-history-margin-gap", type=float, default=0.01)
    parser.add_argument("--min-history-risk-gap", type=float, default=0.01)
    parser.add_argument("--max-continuation-steps", type=int, default=40)
    parser.add_argument("--heldout-fraction", type=float, default=0.2)
    parser.add_argument("--max-vx-gap", type=float, default=1.0)
    parser.add_argument("--max-vy-gap", type=float, default=0.8)
    parser.add_argument("--max-yaw-rate-gap", type=float, default=0.25)
    parser.add_argument("--max-obstacle-x-gap", type=float, default=8.0)
    parser.add_argument("--max-obstacle-y-gap", type=float, default=1.0)
    parser.add_argument("--max-match-step-gap", type=int, default=8)
    parser.add_argument("--min-accepted-rows", type=int, default=80)
    parser.add_argument("--min-trajectory-rows", type=int, default=50)
    parser.add_argument("--min-history-rows", type=int, default=20)
    parser.add_argument("--min-unique-seeds", type=int, default=30)
    parser.add_argument("--min-unique-step-buckets", type=int, default=4)
    parser.add_argument("--min-unique-distance-buckets", type=int, default=4)
    parser.add_argument("--max-seed-dominance", type=float, default=0.08)
    parser.add_argument("--max-bucket-dominance", type=float, default=0.25)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="fresh_trajectory_boundary_sampler")
    summary = run_fresh_trajectory_boundary_sampler(
        checkpoint_path=args.checkpoint,
        surface_configs=tuple(args.surface_config),
        seed_start=args.seed_start,
        seed_count=args.seed_count,
        min_step=args.min_step,
        max_step=args.max_step,
        snapshot_stride=args.snapshot_stride,
        max_snapshots_per_episode=args.max_snapshots_per_episode,
        target_obstacle_distance=args.target_obstacle_distance,
        obstacle_longitudinal_min=args.obstacle_longitudinal_min,
        obstacle_longitudinal_max=args.obstacle_longitudinal_max,
        steer_deltas=args.steer_deltas,
        throttle_deltas=args.throttle_deltas,
        brake_deltas=args.brake_deltas,
        terminal_cliff_margin=args.terminal_cliff_margin,
        near_boundary_margin=args.near_boundary_margin,
        max_prepass_margin=args.max_prepass_margin,
        min_margin_sensitivity=args.min_margin_sensitivity,
        min_risk_sensitivity=args.min_risk_sensitivity,
        min_history_margin_gap=args.min_history_margin_gap,
        min_history_risk_gap=args.min_history_risk_gap,
        max_continuation_steps=args.max_continuation_steps,
        heldout_fraction=args.heldout_fraction,
        max_vx_gap=args.max_vx_gap,
        max_vy_gap=args.max_vy_gap,
        max_yaw_rate_gap=args.max_yaw_rate_gap,
        max_obstacle_x_gap=args.max_obstacle_x_gap,
        max_obstacle_y_gap=args.max_obstacle_y_gap,
        max_match_step_gap=args.max_match_step_gap,
        min_accepted_rows=args.min_accepted_rows,
        min_trajectory_rows=args.min_trajectory_rows,
        min_history_rows=args.min_history_rows,
        min_unique_seeds=args.min_unique_seeds,
        min_unique_step_buckets=args.min_unique_step_buckets,
        min_unique_distance_buckets=args.min_unique_distance_buckets,
        max_seed_dominance=args.max_seed_dominance,
        max_bucket_dominance=args.max_bucket_dominance,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
