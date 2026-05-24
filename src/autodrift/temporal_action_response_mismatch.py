"""No-training temporal command-response mismatch interventions."""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import (
    NOMINAL_FAULT,
    FaultSpec,
    _feature_distance,
    _frame_info,
    _terminal_reason,
    apply_fault_to_env,
    find_cross_fault_match,
    load_scenario_config,
)
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.hidden_swap_gate import action_trajectory_distances, terminal_reason, zero_action_trajectory_distances
from autodrift.matched_history_intervention_gate import (
    PREVIOUS_COMMAND_INDICES,
    action_distance,
    deterministic_action_from_hidden,
)
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import ActorCritic, resolve_device
from autodrift.trajectory_terminal_boundary_source_miner import assigned_split


DELAY_STEPS = (5, 10, 20)
TEMPORAL_VARIANTS = {
    "delayed_hidden_5",
    "delayed_hidden_10",
    "delayed_hidden_20",
    "pre_fault_stale_hidden",
    "mismatch_zero_command_history",
    "mismatch_command_shift_1",
    "mismatch_response_delay_5",
    "mismatch_response_delay_10",
}


@dataclass
class TemporalSnapshot:
    snapshot_id: int
    scenario_id: str
    seed: int
    fault: FaultSpec
    step: int
    observation: np.ndarray
    hidden: torch.Tensor
    env: AutoDriftEnv
    info: dict[str, Any]
    obstacle_distance: float
    obstacle_lateral_offset: float
    history_steps: tuple[int, ...]
    history_observations: tuple[np.ndarray, ...]
    history_start_hidden: torch.Tensor
    delayed_hiddens: dict[int, torch.Tensor]
    pre_fault_hidden: torch.Tensor | None


def _finite_mean(values: list[float]) -> float:
    finite = [float(value) for value in values if np.isfinite(float(value))]
    return float(np.mean(finite)) if finite else float("nan")


def _finite_percentile(values: list[float], percentile: float) -> float:
    finite = sorted(float(value) for value in values if np.isfinite(float(value)))
    if not finite:
        return float("nan")
    index = int(round((len(finite) - 1) * float(percentile)))
    return float(finite[min(max(index, 0), len(finite) - 1)])


def classify_temporal_mismatch_result(
    *,
    row_count: int,
    temporal_action_critical_rows: int,
    temporal_outcome_critical_rows: int,
    reset_action_critical_rows: int,
    reset_outcome_critical_rows: int,
    normal_history_retention_pass: bool,
    unique_temporal_fault_families: int,
    unique_temporal_seeds: int,
    temporal_artifact_rows: int = 0,
    min_temporal_action_rows: int = 30,
    min_temporal_outcome_rows: int = 10,
    min_unique_fault_families: int = 4,
    min_unique_seeds: int = 20,
) -> str:
    if int(row_count) == 0 or int(temporal_artifact_rows) > 0:
        return "temporal_artifact"
    if (
        bool(normal_history_retention_pass)
        and int(temporal_action_critical_rows) >= int(min_temporal_action_rows)
        and int(temporal_outcome_critical_rows) >= int(min_temporal_outcome_rows)
        and int(unique_temporal_fault_families) >= int(min_unique_fault_families)
        and int(unique_temporal_seeds) >= int(min_unique_seeds)
    ):
        return "temporal_mismatch_positive"
    if bool(normal_history_retention_pass) and int(temporal_action_critical_rows) >= int(min_temporal_action_rows):
        return "temporal_action_only"
    if int(reset_action_critical_rows) > 0 or int(reset_outcome_critical_rows) > 0:
        return "temporal_reset_only"
    return "temporal_neutral"


def _history_corrupted_hidden(
    *,
    model: ActorCritic,
    snapshot: TemporalSnapshot,
    response_dim: int,
    device: torch.device,
    corrupt: Callable[[int, tuple[np.ndarray, ...]], np.ndarray],
) -> torch.Tensor | None:
    if not snapshot.history_observations:
        return None
    hidden = snapshot.history_start_hidden.detach().clone()
    history = snapshot.history_observations
    for index, _ in enumerate(history):
        obs = corrupt(index, history)
        _, hidden = deterministic_action_from_hidden(model, obs, hidden, device)
    if hidden.shape != snapshot.hidden.shape:
        return None
    return hidden


def _zero_command_history_hidden(
    *,
    model: ActorCritic,
    snapshot: TemporalSnapshot,
    response_dim: int,
    device: torch.device,
) -> torch.Tensor | None:
    def corrupt(index: int, history: tuple[np.ndarray, ...]) -> np.ndarray:
        obs = np.asarray(history[index], dtype=np.float32).copy()
        for command_index in PREVIOUS_COMMAND_INDICES:
            if command_index < obs.shape[0]:
                obs[command_index] = 0.0
        return obs

    return _history_corrupted_hidden(model=model, snapshot=snapshot, response_dim=response_dim, device=device, corrupt=corrupt)


def _command_shift_history_hidden(
    *,
    model: ActorCritic,
    snapshot: TemporalSnapshot,
    response_dim: int,
    device: torch.device,
) -> torch.Tensor | None:
    def corrupt(index: int, history: tuple[np.ndarray, ...]) -> np.ndarray:
        obs = np.asarray(history[index], dtype=np.float32).copy()
        source = history[max(0, index - 1)]
        for command_index in PREVIOUS_COMMAND_INDICES:
            if command_index < obs.shape[0] and command_index < source.shape[0]:
                obs[command_index] = source[command_index]
        return obs

    return _history_corrupted_hidden(model=model, snapshot=snapshot, response_dim=response_dim, device=device, corrupt=corrupt)


def _response_delay_history_hidden(
    *,
    model: ActorCritic,
    snapshot: TemporalSnapshot,
    response_dim: int,
    delay: int,
    device: torch.device,
) -> torch.Tensor | None:
    def corrupt(index: int, history: tuple[np.ndarray, ...]) -> np.ndarray:
        obs = np.asarray(history[index], dtype=np.float32).copy()
        source = history[max(0, index - int(delay))]
        limit = min(int(response_dim), obs.shape[0], source.shape[0])
        obs[:limit] = source[:limit]
        return obs

    return _history_corrupted_hidden(model=model, snapshot=snapshot, response_dim=response_dim, device=device, corrupt=corrupt)


def build_temporal_variant_hiddens(
    *,
    model: ActorCritic,
    snapshot: TemporalSnapshot,
    wrong_snapshot: TemporalSnapshot,
    response_dim: int,
    device: torch.device,
) -> dict[str, torch.Tensor]:
    variants: dict[str, torch.Tensor] = {
        "normal": snapshot.hidden.detach().clone(),
        "reset_hidden": model.initial_hidden(1, device),
        "cross_fault_wrong_hidden": wrong_snapshot.hidden.detach().clone(),
    }
    for delay in DELAY_STEPS:
        delayed = snapshot.delayed_hiddens.get(int(delay))
        if delayed is not None:
            variants[f"delayed_hidden_{int(delay)}"] = delayed.detach().clone()
    if snapshot.pre_fault_hidden is not None:
        variants["pre_fault_stale_hidden"] = snapshot.pre_fault_hidden.detach().clone()
    zero_command = _zero_command_history_hidden(
        model=model,
        snapshot=snapshot,
        response_dim=response_dim,
        device=device,
    )
    if zero_command is not None:
        variants["mismatch_zero_command_history"] = zero_command
    command_shift = _command_shift_history_hidden(
        model=model,
        snapshot=snapshot,
        response_dim=response_dim,
        device=device,
    )
    if command_shift is not None:
        variants["mismatch_command_shift_1"] = command_shift
    for delay in (5, 10):
        response_delay = _response_delay_history_hidden(
            model=model,
            snapshot=snapshot,
            response_dim=response_dim,
            delay=delay,
            device=device,
        )
        if response_delay is not None:
            variants[f"mismatch_response_delay_{int(delay)}"] = response_delay
    return variants


def replay_temporal_variant(
    *,
    model: ActorCritic,
    snapshot: TemporalSnapshot,
    env_config: DriftEnvConfig,
    variant: str,
    variant_hidden: torch.Tensor,
    normal_first_action: np.ndarray | None,
    normal_actions: list[np.ndarray] | None,
    max_continuation_steps: int,
    device: torch.device,
) -> tuple[dict[str, Any], list[np.ndarray]]:
    env = copy.deepcopy(snapshot.env)
    obs = snapshot.observation.copy()
    hidden = variant_hidden.detach().clone()
    max_steps = int(max_continuation_steps)
    if max_steps <= 0:
        max_steps = max(1, env_config.max_steps - snapshot.step)
    rewards: list[float] = []
    actions: list[np.ndarray] = []
    betas: list[float] = []
    terminated = False
    truncated = False
    info = dict(snapshot.info)
    for _ in range(max_steps):
        action, next_hidden = deterministic_action_from_hidden(model, np.asarray(obs, dtype=np.float32), hidden, device)
        actions.append(action)
        hidden = next_hidden
        obs, reward, terminated, truncated, info = env.step(action)
        rewards.append(float(reward))
        betas.append(float(info.get("beta", float("nan"))))
        if terminated or truncated:
            break

    first_action = actions[0] if actions else np.full(3, float("nan"), dtype=np.float32)
    if variant == "normal":
        first_action_distance = 0.0
        trajectory_distances = zero_action_trajectory_distances(len(actions))
    else:
        first_action_distance = (
            action_distance(first_action, normal_first_action)
            if normal_first_action is not None and np.all(np.isfinite(first_action))
            else float("nan")
        )
        trajectory_distances = action_trajectory_distances(actions, normal_actions)
    beta_abs_peak = float(np.nanmax(np.abs(betas))) if betas else float("nan")
    reason = terminal_reason(info, terminated, truncated, env_config)
    return {
        "variant": variant,
        "steps": len(rewards),
        "return": float(np.sum(rewards)),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "success": not bool(terminated),
        "collision": bool(info.get("collision", False)),
        "off_road": reason == "off_road",
        "spin_out": bool(np.isfinite(beta_abs_peak) and beta_abs_peak > 1.2),
        "terminal_reason": reason,
        "obstacle_completed": bool(info.get("obstacle_completed", False)),
        "min_obstacle_clearance": _finite_float(info.get("min_obstacle_clearance")),
        "obstacle_collision_radius": _finite_float(info.get("obstacle_collision_radius")),
        "min_clearance_margin": _finite_float(info.get("min_clearance_margin")),
        "beta_abs_peak": beta_abs_peak,
        "first_steer": float(first_action[0]),
        "first_throttle": float(first_action[1]),
        "first_brake": float(first_action[2]),
        "first_action_distance": first_action_distance,
        **trajectory_distances,
    }, actions


def collect_temporal_snapshots(
    *,
    model: ActorCritic,
    env_config: DriftEnvConfig,
    fault: FaultSpec,
    seed: int,
    start_snapshot_id: int,
    min_step: int,
    max_steps: int,
    snapshot_stride: int,
    max_snapshots_per_scenario: int,
    obstacle_longitudinal_min: float,
    obstacle_longitudinal_max: float,
    history_window_steps: int,
    device: torch.device,
) -> tuple[list[TemporalSnapshot], dict[str, Any]]:
    env = AutoDriftEnv(env_config)
    scenario_id = f"seed{int(seed)}_{fault.name}"
    snapshots: list[TemporalSnapshot] = []
    obs, info = env.reset(seed=int(seed))
    hidden = model.initial_hidden(1, device)
    fault_applied = False
    if int(fault.activation_step) <= 0:
        apply_fault_to_env(env, fault)
        fault_applied = True
        info = _frame_info(env)

    observation_by_step: dict[int, np.ndarray] = {}
    hidden_by_step: dict[int, torch.Tensor] = {}
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
            and len(snapshots) < int(max_snapshots_per_scenario)
            and np.isfinite(obstacle_distance)
            and float(obstacle_longitudinal_min) <= obstacle_distance <= float(obstacle_longitudinal_max)
        ):
            obstacle_path = env._obstacle_path_features(env.track.frame(env.state.x, env.state.y, env.state.psi))
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
            snapshots.append(
                TemporalSnapshot(
                    snapshot_id=start_snapshot_id + len(snapshots),
                    scenario_id=scenario_id,
                    seed=int(seed),
                    fault=fault,
                    step=step,
                    observation=np.asarray(obs, dtype=np.float32).copy(),
                    hidden=hidden.detach().clone(),
                    env=copy.deepcopy(env),
                    info=dict(info),
                    obstacle_distance=obstacle_distance,
                    obstacle_lateral_offset=float(obstacle_path[1] * env.config.track_width),
                    history_steps=history_steps,
                    history_observations=history_observations,
                    history_start_hidden=history_start_hidden.detach().clone(),
                    delayed_hiddens=delayed_hiddens,
                    pre_fault_hidden=pre_fault_hidden,
                )
            )
        action, next_hidden = deterministic_action_from_hidden(model, np.asarray(obs, dtype=np.float32), hidden, device)
        obs, _, terminated, truncated, info = env.step(action)
        hidden = next_hidden

    scenario_row = {
        "scenario_id": scenario_id,
        "seed": int(seed),
        "fault_name": fault.name,
        "fault_family": fault.family,
        "fault_severity": fault.severity,
        "fidelity_class": fault.fidelity_class,
        "activation_step": int(fault.activation_step),
        "fault_applied": bool(fault_applied),
        "snapshots_collected": int(len(snapshots)),
        "steps": int(env.step_count),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "terminal_reason": _terminal_reason(info, terminated, truncated),
        "success": not bool(terminated),
        "collision": bool(info.get("collision", False)),
        "obstacle_completed": bool(info.get("obstacle_completed", False)),
        "terminal_margin": _finite_float(info.get("min_clearance_margin")),
    }
    env.close()
    return snapshots, scenario_row


def _pair_metadata(pair_id: int, preferred: TemporalSnapshot, wrong: TemporalSnapshot, match_distance: float, rule: str) -> dict[str, Any]:
    return {
        "pair_id": int(pair_id),
        "seed": int(preferred.seed),
        "step": int(preferred.step),
        "preferred_snapshot_id": int(preferred.snapshot_id),
        "wrong_snapshot_id": int(wrong.snapshot_id),
        "preferred_fault": preferred.fault.name,
        "preferred_fault_family": preferred.fault.family,
        "preferred_fault_severity": preferred.fault.severity,
        "wrong_fault": wrong.fault.name,
        "wrong_fault_family": wrong.fault.family,
        "wrong_fault_severity": wrong.fault.severity,
        "fault_family_pair": f"{preferred.fault.family}->{wrong.fault.family}",
        "severity_pair": f"{preferred.fault.severity}->{wrong.fault.severity}",
        "pairing_rule": rule,
        "feature_distance": float(_feature_distance(preferred, wrong)),
        "match_distance": float(match_distance),
        "assigned_split": assigned_split(int(preferred.seed), heldout_fraction=0.2),
    }


def _source_pool(pair_id: int, pair_meta: dict[str, Any], reset_pair_ids: set[int], low_alpha_fault_pairs: set[str]) -> str:
    if int(pair_id) in reset_pair_ids:
        return "m716_reset_only"
    if str(pair_meta.get("fault_family_pair", "")) in low_alpha_fault_pairs:
        return "m713_low_alpha_family"
    return "m716_general"


def _load_reset_pair_ids(path: Path) -> set[int]:
    if not path.exists():
        return set()
    import csv

    with path.open(newline="", encoding="utf-8") as handle:
        return {int(row["pair_id"]) for row in csv.DictReader(handle) if str(row.get("pair_id", "")).strip()}


def _load_low_alpha_fault_pairs(path: Path, max_alpha: float = 4.0) -> set[str]:
    if not path.exists():
        return set()
    import csv

    output: set[str] = set()
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("variant") != "normal_vs_wrong_history":
                continue
            try:
                alpha = float(row.get("alpha_to_action_threshold", ""))
            except ValueError:
                continue
            if np.isfinite(alpha) and alpha <= float(max_alpha):
                output.add(str(row.get("fault_family_pair", "")))
    return output


def _row_for_variant(
    *,
    pair_meta: dict[str, Any],
    source_pool: str,
    variant: str,
    result: dict[str, Any],
    normal: dict[str, Any],
    action_threshold: float,
    margin_threshold: float,
) -> dict[str, Any]:
    normal_margin = _finite_float(normal.get("min_clearance_margin"))
    variant_margin = _finite_float(result.get("min_clearance_margin"))
    margin_gap = normal_margin - variant_margin if np.isfinite(normal_margin) and np.isfinite(variant_margin) else float("nan")
    normal_success = bool(normal.get("success", False))
    success_drop = bool(normal_success and not bool(result.get("success", False)))
    normal_ok = bool(normal_success or (np.isfinite(normal_margin) and normal_margin >= 0.0))
    first_action_distance = _finite_float(result.get("first_action_distance"), default=0.0)
    action_critical = bool(normal_ok and variant != "normal" and first_action_distance >= float(action_threshold))
    outcome_critical = bool(
        normal_ok
        and variant != "normal"
        and (success_drop or (np.isfinite(margin_gap) and margin_gap >= float(margin_threshold)))
    )
    temporal_variant = variant in TEMPORAL_VARIANTS
    row = dict(pair_meta)
    row.update(
        {
            "source_pool": source_pool,
            "variant": variant,
            "temporal_variant": bool(temporal_variant),
            "normal_success": normal_success,
            "normal_margin": normal_margin,
            "variant_success": bool(result.get("success", False)),
            "variant_margin": variant_margin,
            "margin_gap_from_normal": margin_gap,
            "success_drop_from_normal": success_drop,
            "first_action_distance_from_normal": first_action_distance,
            "trajectory_l2_mean": _finite_float(
                result.get("trajectory_l2_mean", result.get("action_trajectory_distance_mean"))
            ),
            "trajectory_l2_max": _finite_float(
                result.get("trajectory_l2_max", result.get("action_trajectory_distance_max"))
            ),
            "first_steer": _finite_float(result.get("first_steer")),
            "first_throttle": _finite_float(result.get("first_throttle")),
            "first_brake": _finite_float(result.get("first_brake")),
            "terminal_reason": str(result.get("terminal_reason", "")),
            "action_critical": action_critical,
            "outcome_critical": outcome_critical,
            "temporal_action_critical": bool(temporal_variant and action_critical),
            "temporal_outcome_critical": bool(temporal_variant and outcome_critical),
            "reset_action_critical": bool(variant == "reset_hidden" and action_critical),
            "reset_outcome_critical": bool(variant == "reset_hidden" and outcome_critical),
        }
    )
    return row


def _group_summary(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(tuple(str(row.get(key, "")) for key in keys), []).append(row)
    output: list[dict[str, Any]] = []
    for key_values, group_rows in sorted(groups.items()):
        item = {key: value for key, value in zip(keys, key_values, strict=True)}
        distances = [_finite_float(row.get("first_action_distance_from_normal")) for row in group_rows]
        margins = [_finite_float(row.get("margin_gap_from_normal")) for row in group_rows]
        item.update(
            {
                "rows": int(len(group_rows)),
                "action_critical_rows": int(sum(1 for row in group_rows if bool(row.get("action_critical", False)))),
                "outcome_critical_rows": int(sum(1 for row in group_rows if bool(row.get("outcome_critical", False)))),
                "temporal_action_critical_rows": int(
                    sum(1 for row in group_rows if bool(row.get("temporal_action_critical", False)))
                ),
                "temporal_outcome_critical_rows": int(
                    sum(1 for row in group_rows if bool(row.get("temporal_outcome_critical", False)))
                ),
                "unique_seeds": int(len({int(row.get("seed", -1)) for row in group_rows})),
                "first_action_distance_mean": _finite_mean(distances),
                "first_action_distance_p95": _finite_percentile(distances, 0.95),
                "first_action_distance_max": max([value for value in distances if np.isfinite(value)], default=float("nan")),
                "margin_gap_mean": _finite_mean(margins),
                "margin_gap_p95": _finite_percentile(margins, 0.95),
                "margin_gap_max": max([value for value in margins if np.isfinite(value)], default=float("nan")),
            }
        )
        output.append(item)
    return output


def run_temporal_action_response_mismatch(
    *,
    checkpoint_path: Path,
    config_path: Path,
    seed_start: int,
    seed_count: int,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    config = load_scenario_config(config_path)
    pairing_rules = tuple(config.get("pairing_rules", ()))
    if not pairing_rules:
        raise ValueError("temporal mismatch runner requires config pairing_rules")
    env_config = load_env_config(Path(config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    if not model.is_online_recurrent:
        raise ValueError("temporal mismatch runner requires an online recurrent checkpoint")
    checksum_before = model_parameter_checksum(model)
    response_dim = response_feature_dim_for_model(model)

    max_steps = int(config.get("max_steps", 260))
    min_step = int(config.get("min_step", 35))
    snapshot_stride = int(config.get("snapshot_stride", 5))
    max_snapshots_per_scenario = int(config.get("max_snapshots_per_scenario", 4))
    obstacle_longitudinal_min = float(config.get("obstacle_longitudinal_min", -8.0))
    obstacle_longitudinal_max = float(config.get("obstacle_longitudinal_max", 90.0))
    max_pairs = int(config.get("max_pairs", 2048))
    max_continuation_steps = int(config.get("max_continuation_steps", 40))
    min_action_l2_gap = float(config.get("min_action_l2_gap", 0.015))
    min_history_margin_gap = float(config.get("min_history_margin_gap", 0.02))
    min_temporal_action_rows = int(config.get("min_temporal_action_rows", 30))
    min_temporal_outcome_rows = int(config.get("min_temporal_outcome_rows", 10))
    min_unique_fault_families = int(config.get("min_unique_fault_families", 4))
    min_unique_seeds = int(config.get("min_unique_seeds", 20))
    history_window_steps = int(config.get("temporal_history_window_steps", 30))

    reset_pair_ids = _load_reset_pair_ids(Path("runs/m716_extreme_fault_coverage_refresh/reset_only_rows.csv"))
    low_alpha_pairs = _load_low_alpha_fault_pairs(Path("runs/m713_actor_head_history_signal_coupling/row_actor_head_coupling.csv"))

    faults = [NOMINAL_FAULT, *config["faults"]]
    snapshots: list[TemporalSnapshot] = []
    scenario_rows: list[dict[str, Any]] = []
    for seed in range(int(seed_start), int(seed_start) + int(seed_count)):
        for fault in faults:
            scenario_snapshots, scenario_row = collect_temporal_snapshots(
                model=model,
                env_config=env_config,
                fault=fault,
                seed=int(seed),
                start_snapshot_id=len(snapshots),
                min_step=min_step,
                max_steps=max_steps,
                snapshot_stride=snapshot_stride,
                max_snapshots_per_scenario=max_snapshots_per_scenario,
                obstacle_longitudinal_min=obstacle_longitudinal_min,
                obstacle_longitudinal_max=obstacle_longitudinal_max,
                history_window_steps=history_window_steps,
                device=resolved_device,
            )
            snapshots.extend(scenario_snapshots)
            scenario_rows.append(scenario_row)

    snapshots_by_seed: dict[int, list[TemporalSnapshot]] = {}
    for snapshot in snapshots:
        snapshots_by_seed.setdefault(int(snapshot.seed), []).append(snapshot)

    source_rows: list[dict[str, Any]] = []
    rollout_rows: list[dict[str, Any]] = []
    temporal_critical_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    pair_id = 0
    for seed, seed_snapshots in sorted(snapshots_by_seed.items()):
        fault_snapshots = [snapshot for snapshot in seed_snapshots if snapshot.fault.name != "nominal"]
        for snapshot in fault_snapshots:
            if pair_id >= max_pairs:
                break
            matched, match_distance, pairing_rule = find_cross_fault_match(snapshot, seed_snapshots, pairing_rules)
            if matched is None:
                rejected_rows.append(
                    {
                        "seed": int(seed),
                        "snapshot_id": int(snapshot.snapshot_id),
                        "fault_name": snapshot.fault.name,
                        "fault_family": snapshot.fault.family,
                        "fault_severity": snapshot.fault.severity,
                        "rejection_reason": "matched_state_empty",
                    }
                )
                continue
            pair_meta = _pair_metadata(pair_id, snapshot, matched, match_distance, pairing_rule)
            source_pool = _source_pool(pair_id, pair_meta, reset_pair_ids, low_alpha_pairs)
            variant_hiddens = build_temporal_variant_hiddens(
                model=model,
                snapshot=snapshot,
                wrong_snapshot=matched,
                response_dim=response_dim,
                device=resolved_device,
            )
            normal, normal_actions = replay_temporal_variant(
                model=model,
                snapshot=snapshot,
                env_config=env_config,
                variant="normal",
                variant_hidden=variant_hiddens["normal"],
                normal_first_action=None,
                normal_actions=None,
                max_continuation_steps=max_continuation_steps,
                device=resolved_device,
            )
            normal_first_action = np.asarray(
                [normal["first_steer"], normal["first_throttle"], normal["first_brake"]],
                dtype=np.float32,
            )
            source_row = dict(pair_meta)
            source_row.update(
                {
                    "source_pool": source_pool,
                    "available_variant_count": int(len(variant_hiddens)),
                    "available_variants": "|".join(sorted(variant_hiddens)),
                    "normal_margin": _finite_float(normal.get("min_clearance_margin")),
                    "normal_success": bool(normal.get("success", False)),
                }
            )
            source_rows.append(source_row)
            for variant, variant_hidden in variant_hiddens.items():
                if variant == "normal":
                    result = normal
                else:
                    result, _ = replay_temporal_variant(
                        model=model,
                        snapshot=snapshot,
                        env_config=env_config,
                        variant=variant,
                        variant_hidden=variant_hidden,
                        normal_first_action=normal_first_action,
                        normal_actions=normal_actions,
                        max_continuation_steps=max_continuation_steps,
                        device=resolved_device,
                    )
                row = _row_for_variant(
                    pair_meta=pair_meta,
                    source_pool=source_pool,
                    variant=variant,
                    result=result,
                    normal=normal,
                    action_threshold=min_action_l2_gap,
                    margin_threshold=min_history_margin_gap,
                )
                rollout_rows.append(row)
                if bool(row.get("temporal_action_critical", False)) or bool(row.get("temporal_outcome_critical", False)):
                    temporal_critical_rows.append(row)
            pair_id += 1
        if pair_id >= max_pairs:
            break

    reset_action_critical = [row for row in rollout_rows if bool(row.get("reset_action_critical", False))]
    reset_outcome_critical = [row for row in rollout_rows if bool(row.get("reset_outcome_critical", False))]
    temporal_action_critical = [row for row in rollout_rows if bool(row.get("temporal_action_critical", False))]
    temporal_outcome_critical = [row for row in rollout_rows if bool(row.get("temporal_outcome_critical", False))]
    temporal_positive_rows = [row for row in temporal_critical_rows if bool(row.get("temporal_variant", False))]
    unique_temporal_fault_families = len({str(row.get("preferred_fault_family", "")) for row in temporal_positive_rows})
    unique_temporal_seeds = len({int(row.get("seed", -1)) for row in temporal_positive_rows})
    normal_rows = [row for row in rollout_rows if row.get("variant") == "normal"]
    normal_history_retention_pass = bool(
        normal_rows
        and all(np.isfinite(_finite_float(row.get("first_steer"))) for row in normal_rows)
        and not any(str(row.get("terminal_reason", "")) == "artifact" for row in normal_rows)
    )
    result_class = classify_temporal_mismatch_result(
        row_count=len(rollout_rows),
        temporal_action_critical_rows=len(temporal_action_critical),
        temporal_outcome_critical_rows=len(temporal_outcome_critical),
        reset_action_critical_rows=len(reset_action_critical),
        reset_outcome_critical_rows=len(reset_outcome_critical),
        normal_history_retention_pass=normal_history_retention_pass,
        unique_temporal_fault_families=unique_temporal_fault_families,
        unique_temporal_seeds=unique_temporal_seeds,
        temporal_artifact_rows=0,
        min_temporal_action_rows=min_temporal_action_rows,
        min_temporal_outcome_rows=min_temporal_outcome_rows,
        min_unique_fault_families=min_unique_fault_families,
        min_unique_seeds=min_unique_seeds,
    )

    variant_summary = _group_summary(rollout_rows, ("variant",))
    fault_family_summary = _group_summary(rollout_rows, ("fault_family_pair", "variant"))
    source_pool_summary = _group_summary(rollout_rows, ("source_pool", "variant"))
    write_csv_rows(run_dir / "scenario_summary.csv", scenario_rows)
    write_csv_rows(run_dir / "source_rows.csv", source_rows)
    write_csv_rows(run_dir / "intervention_rollouts.csv", rollout_rows)
    write_csv_rows(run_dir / "temporal_critical_rows.csv", temporal_critical_rows)
    write_csv_rows(run_dir / "variant_summary.csv", variant_summary)
    write_csv_rows(run_dir / "fault_family_summary.csv", fault_family_summary)
    write_csv_rows(run_dir / "source_pool_summary.csv", source_pool_summary)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)

    checksum_after = model_parameter_checksum(model)
    summary = {
        "run_type": "temporal_action_response_mismatch",
        "checkpoint": checkpoint_path,
        "config": config_path,
        "env_config": config.get("env_config"),
        "seed_start": int(seed_start),
        "seed_count": int(seed_count),
        "fault_count": int(len(faults) - 1),
        "scenario_count": int(len(scenario_rows)),
        "snapshot_count": int(len(snapshots)),
        "matched_pair_count": int(len(source_rows)),
        "unmatched_rows": int(len(rejected_rows)),
        "row_count": int(len(rollout_rows)),
        "temporal_critical_rows": int(len(temporal_critical_rows)),
        "temporal_action_critical_rows": int(len(temporal_action_critical)),
        "temporal_outcome_critical_rows": int(len(temporal_outcome_critical)),
        "reset_action_critical_rows": int(len(reset_action_critical)),
        "reset_outcome_critical_rows": int(len(reset_outcome_critical)),
        "unique_temporal_fault_families": int(unique_temporal_fault_families),
        "unique_temporal_seeds": int(unique_temporal_seeds),
        "normal_history_retention_pass": bool(normal_history_retention_pass),
        "source_pool_counts": {
            pool: int(sum(1 for row in source_rows if row.get("source_pool") == pool))
            for pool in sorted({str(row.get("source_pool", "")) for row in source_rows})
        },
        "thresholds": {
            "min_action_l2_gap": min_action_l2_gap,
            "min_history_margin_gap": min_history_margin_gap,
            "min_temporal_action_rows": min_temporal_action_rows,
            "min_temporal_outcome_rows": min_temporal_outcome_rows,
            "min_unique_fault_families": min_unique_fault_families,
            "min_unique_seeds": min_unique_seeds,
            "history_window_steps": history_window_steps,
        },
        "actor_parameters_changed": bool(checksum_before != checksum_after),
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "promoted": False,
        "result_class": result_class,
        "temporal_mismatch_positive": bool(result_class == "temporal_mismatch_positive"),
        "summary_json": run_dir / "summary.json",
        "source_rows_csv": run_dir / "source_rows.csv",
        "intervention_rollouts_csv": run_dir / "intervention_rollouts.csv",
        "temporal_critical_rows_csv": run_dir / "temporal_critical_rows.csv",
        "variant_summary_csv": run_dir / "variant_summary.csv",
        "fault_family_summary_csv": run_dir / "fault_family_summary.csv",
        "source_pool_summary_csv": run_dir / "source_pool_summary.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training temporal action-response mismatch interventions.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=72000)
    parser.add_argument("--seed-count", type=int, default=512)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="temporal_action_response_mismatch")
    summary = run_temporal_action_response_mismatch(
        checkpoint_path=args.checkpoint,
        config_path=args.config,
        seed_start=args.seed_start,
        seed_count=args.seed_count,
        device=args.device,
        run_dir=run_dir,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
