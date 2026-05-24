"""Generate no-training extreme hidden-condition scenario corpora."""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import make_run_dir, read_json, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.dynamics import SingleTrackDriftModel, VehicleParams
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import load_env_config
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.matched_history_outcome_gate import OutcomeSnapshot, replay_outcome_variant
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import ActorCritic, resolve_device
from autodrift.trajectory_terminal_boundary_source_miner import assigned_split


@dataclass(frozen=True)
class FaultSpec:
    name: str
    family: str
    severity: str
    activation_step: int
    params: dict[str, float]
    fidelity_class: str = "current_model_fault"


@dataclass(frozen=True)
class PairingRule:
    preferred_family: str
    wrong_family: str
    preferred_severities: tuple[str, ...] = ()
    wrong_severities: tuple[str, ...] = ()


@dataclass
class ExtremeSnapshot:
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


NOMINAL_FAULT = FaultSpec(
    name="nominal",
    family="nominal",
    severity="nominal",
    activation_step=0,
    params={},
    fidelity_class="current_model_fault",
)

SUPPORTED_FAULT_FAMILIES = {
    "nominal",
    "global_mu_drop",
    "front_lateral_authority_drop",
    "rear_lateral_authority_drop",
    "brake_authority_drop",
    "drive_authority_drop",
    "steering_fault",
    "mass_cg_shift",
    "delay_noise_fault",
    "combined_fault",
}

DEFAULT_FUTURE_ONLY_FAULTS = [
    "single_wheel_grip_collapse",
    "single_wheel_puncture_or_blowout",
    "left_right_split_mu",
    "stuck_caliper_or_single_wheel_brake_pull",
    "true_asymmetric_half_shaft_torque_loss",
]


def _clamp_positive(value: float, minimum: float = 1e-6) -> float:
    return float(max(float(value), float(minimum)))


def fault_from_dict(data: dict[str, Any]) -> FaultSpec:
    name = str(data.get("name", "")).strip()
    family = str(data.get("family", "")).strip()
    severity = str(data.get("severity", "")).strip()
    fidelity_class = str(data.get("fidelity_class", "current_model_fault")).strip()
    if not name or not family or not severity:
        raise ValueError(f"fault spec must include name family and severity, got {data!r}")
    if family not in SUPPORTED_FAULT_FAMILIES:
        raise ValueError(f"unsupported current-model fault family {family!r}")
    raw_params = data.get("params", {})
    if not isinstance(raw_params, dict):
        raise ValueError(f"fault params must be an object for {name!r}")
    params = {str(key): float(value) for key, value in raw_params.items()}
    return FaultSpec(
        name=name,
        family=family,
        severity=severity,
        activation_step=int(data.get("activation_step", 0)),
        params=params,
        fidelity_class=fidelity_class,
    )


def pairing_rule_from_dict(data: dict[str, Any]) -> PairingRule:
    preferred_family = str(data.get("preferred_family", "")).strip()
    wrong_family = str(data.get("wrong_family", "")).strip()
    if not preferred_family or not wrong_family:
        raise ValueError(f"pairing rule must include preferred_family and wrong_family, got {data!r}")
    preferred_severities = tuple(str(item).strip() for item in data.get("preferred_severities", []) if str(item).strip())
    wrong_severities = tuple(str(item).strip() for item in data.get("wrong_severities", []) if str(item).strip())
    return PairingRule(
        preferred_family=preferred_family,
        wrong_family=wrong_family,
        preferred_severities=preferred_severities,
        wrong_severities=wrong_severities,
    )


def load_scenario_config(path: Path | str) -> dict[str, Any]:
    data = read_json(path)
    if not isinstance(data, dict):
        raise ValueError("extreme scenario config must be a JSON object")
    faults = [fault_from_dict(item) for item in data.get("faults", [])]
    if not faults:
        raise ValueError("extreme scenario config must define at least one current-model fault")
    return {
        **data,
        "faults": faults,
        "pairing_rules": [pairing_rule_from_dict(item) for item in data.get("pairing_rules", [])],
        "future_only_faults": [str(item) for item in data.get("future_only_faults", DEFAULT_FUTURE_ONLY_FAULTS)],
    }


def apply_fault_params(params: VehicleParams, fault: FaultSpec) -> VehicleParams:
    values = {
        "mass": params.mass,
        "iz": params.iz,
        "lf": params.lf,
        "lr": params.lr,
        "h_cg": params.h_cg,
        "mu": params.mu,
        "cf": params.cf,
        "cr": params.cr,
        "max_steer": params.max_steer,
        "max_steer_rate": params.max_steer_rate,
        "max_drive_force": params.max_drive_force,
        "max_brake_force": params.max_brake_force,
        "drive_tau": params.drive_tau,
        "steer_tau": params.steer_tau,
        "drag_coeff": params.drag_coeff,
        "rolling_resistance": params.rolling_resistance,
        "gravity": params.gravity,
    }
    scales = {
        "mu_scale": "mu",
        "cf_scale": "cf",
        "cr_scale": "cr",
        "mass_scale": "mass",
        "inertia_scale": "iz",
        "max_drive_force_scale": "max_drive_force",
        "max_brake_force_scale": "max_brake_force",
        "max_steer_scale": "max_steer",
        "max_steer_rate_scale": "max_steer_rate",
        "drive_tau_scale": "drive_tau",
        "steer_tau_scale": "steer_tau",
    }
    for scale_key, field in scales.items():
        if scale_key in fault.params:
            values[field] = _clamp_positive(values[field] * float(fault.params[scale_key]))
    if "mu_target" in fault.params:
        values["mu"] = _clamp_positive(float(fault.params["mu_target"]))
    if "cg_shift" in fault.params:
        wheelbase = params.wheelbase
        lf = float(np.clip(params.lf + float(fault.params["cg_shift"]), 0.9, wheelbase - 0.9))
        values["lf"] = lf
        values["lr"] = wheelbase - lf
    return VehicleParams(**values)


def apply_fault_to_env(env: AutoDriftEnv, fault: FaultSpec) -> None:
    if fault.name == "nominal":
        return
    env.params = apply_fault_params(env.params, fault)
    env.model = SingleTrackDriftModel(env.params)


def _frame_info(env: AutoDriftEnv) -> dict[str, Any]:
    return env._info(env.track.frame(env.state.x, env.state.y, env.state.psi))


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


def _margin(result: dict[str, Any]) -> float:
    return _finite_float(result.get("min_clearance_margin"))


def _risk(result: dict[str, Any]) -> float:
    margin = _margin(result)
    return float(max(0.0, -margin)) if np.isfinite(margin) else float("nan")


def _features(snapshot: ExtremeSnapshot) -> tuple[float, float, float, float, float, float]:
    obs = np.asarray(snapshot.observation, dtype=np.float32)
    vx = float(obs[0] * 20.0) if obs.shape[0] > 0 else float("nan")
    vy = float(obs[1] * 12.0) if obs.shape[0] > 1 else float("nan")
    yaw_rate = float(obs[2] * 2.5) if obs.shape[0] > 2 else float("nan")
    steer_state = float(obs[5]) if obs.shape[0] > 5 else float("nan")
    return (
        vx,
        vy,
        yaw_rate,
        steer_state,
        float(snapshot.obstacle_distance),
        float(snapshot.obstacle_lateral_offset),
    )


def _feature_distance(left: ExtremeSnapshot, right: ExtremeSnapshot) -> float:
    left_features = np.asarray(_features(left), dtype=np.float64)
    right_features = np.asarray(_features(right), dtype=np.float64)
    scales = np.asarray([2.0, 1.5, 0.5, 0.5, 10.0, 2.0], dtype=np.float64)
    diff = np.abs(left_features - right_features) / scales
    if not np.all(np.isfinite(diff)):
        return float("inf")
    return float(np.linalg.norm(diff))


def _within_match_window(left: ExtremeSnapshot, right: ExtremeSnapshot) -> bool:
    lvx, lvy, lyaw, _, lx, ly = _features(left)
    rvx, rvy, ryaw, _, rx, ry = _features(right)
    return (
        abs(lvx - rvx) <= 2.0
        and abs(lvy - rvy) <= 1.5
        and abs(lyaw - ryaw) <= 0.5
        and abs(lx - rx) <= 12.0
        and abs(ly - ry) <= 2.0
        and abs(int(left.step) - int(right.step)) <= 20
    )


def collect_fault_snapshots(
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
    device: torch.device,
) -> tuple[list[ExtremeSnapshot], dict[str, Any]]:
    env = AutoDriftEnv(env_config)
    scenario_id = f"seed{int(seed)}_{fault.name}"
    snapshots: list[ExtremeSnapshot] = []
    obs, info = env.reset(seed=int(seed))
    hidden = model.initial_hidden(1, device)
    fault_applied = False
    if int(fault.activation_step) <= 0:
        apply_fault_to_env(env, fault)
        fault_applied = True
        info = _frame_info(env)

    terminated = False
    truncated = False
    while not (terminated or truncated) and int(env.step_count) < int(max_steps):
        step = int(env.step_count)
        if not fault_applied and step >= int(fault.activation_step):
            apply_fault_to_env(env, fault)
            fault_applied = True
            info = _frame_info(env)
        obstacle_distance = _finite_float(info.get("obstacle_distance"))
        if (
            step >= int(min_step)
            and step % max(1, int(snapshot_stride)) == 0
            and len(snapshots) < int(max_snapshots_per_scenario)
            and np.isfinite(obstacle_distance)
            and float(obstacle_longitudinal_min) <= obstacle_distance <= float(obstacle_longitudinal_max)
        ):
            obstacle_path = env._obstacle_path_features(env.track.frame(env.state.x, env.state.y, env.state.psi))
            snapshots.append(
                ExtremeSnapshot(
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
        "mu": _finite_float(info.get("mu")),
        "front_tire_stiffness_scale": _finite_float(info.get("front_tire_stiffness_scale")),
        "rear_tire_stiffness_scale": _finite_float(info.get("rear_tire_stiffness_scale")),
        "drive_scale": _finite_float(info.get("drive_scale")),
        "brake_scale": _finite_float(info.get("brake_scale")),
        "steer_tau_scale": _finite_float(info.get("steer_tau_scale")),
        "drive_tau_scale": _finite_float(info.get("drive_tau_scale")),
    }
    env.close()
    return snapshots, scenario_row


def find_nominal_match(snapshot: ExtremeSnapshot, nominal_snapshots: list[ExtremeSnapshot]) -> tuple[ExtremeSnapshot | None, float]:
    best: ExtremeSnapshot | None = None
    best_distance = float("inf")
    for candidate in nominal_snapshots:
        if not _within_match_window(snapshot, candidate):
            continue
        distance = _feature_distance(snapshot, candidate)
        if distance < best_distance:
            best = candidate
            best_distance = distance
    return best, best_distance


def _rule_matches(rule: PairingRule, preferred: ExtremeSnapshot, wrong: ExtremeSnapshot) -> bool:
    if preferred.fault.family != rule.preferred_family or wrong.fault.family != rule.wrong_family:
        return False
    if rule.preferred_severities and preferred.fault.severity not in rule.preferred_severities:
        return False
    if rule.wrong_severities and wrong.fault.severity not in rule.wrong_severities:
        return False
    return True


def find_cross_fault_match(
    snapshot: ExtremeSnapshot,
    seed_snapshots: list[ExtremeSnapshot],
    pairing_rules: tuple[PairingRule, ...],
) -> tuple[ExtremeSnapshot | None, float, str]:
    best: ExtremeSnapshot | None = None
    best_distance = float("inf")
    best_rule = ""
    for candidate in seed_snapshots:
        if candidate.snapshot_id == snapshot.snapshot_id:
            continue
        if candidate.fault.name == "nominal":
            continue
        matching_rule = next((rule for rule in pairing_rules if _rule_matches(rule, snapshot, candidate)), None)
        if matching_rule is None:
            continue
        if not _within_match_window(snapshot, candidate):
            continue
        distance = _feature_distance(snapshot, candidate)
        if distance < best_distance:
            best = candidate
            best_distance = distance
            best_rule = f"{matching_rule.preferred_family}->{matching_rule.wrong_family}"
    return best, best_distance, best_rule


def _as_outcome_snapshot(snapshot: ExtremeSnapshot, hidden: torch.Tensor | None = None) -> OutcomeSnapshot:
    return OutcomeSnapshot(
        seed=snapshot.seed,
        step=snapshot.step,
        observation=snapshot.observation.copy(),
        hidden=(hidden if hidden is not None else snapshot.hidden).detach().clone(),
        env=snapshot.env,
        info=dict(snapshot.info),
    )


def _snapshot_row(snapshot: ExtremeSnapshot) -> dict[str, Any]:
    vx, vy, yaw_rate, steer_state, _, _ = _features(snapshot)
    return {
        "snapshot_id": int(snapshot.snapshot_id),
        "scenario_id": snapshot.scenario_id,
        "seed": int(snapshot.seed),
        "step": int(snapshot.step),
        "fault_name": snapshot.fault.name,
        "fault_family": snapshot.fault.family,
        "fault_severity": snapshot.fault.severity,
        "fidelity_class": snapshot.fault.fidelity_class,
        "obstacle_distance": float(snapshot.obstacle_distance),
        "obstacle_lateral_offset": float(snapshot.obstacle_lateral_offset),
        "vx": vx,
        "vy": vy,
        "yaw_rate": yaw_rate,
        "steer_state": steer_state,
        "mu": _finite_float(snapshot.info.get("mu")),
        "brake_scale": _finite_float(snapshot.info.get("brake_scale")),
        "drive_scale": _finite_float(snapshot.info.get("drive_scale")),
        "front_tire_stiffness_scale": _finite_float(snapshot.info.get("front_tire_stiffness_scale")),
        "rear_tire_stiffness_scale": _finite_float(snapshot.info.get("rear_tire_stiffness_scale")),
    }


def evaluate_matched_pair(
    *,
    pair_id: int,
    preferred: ExtremeSnapshot,
    wrong_history: ExtremeSnapshot,
    model: ActorCritic,
    env_config: DriftEnvConfig,
    response_dim: int,
    max_continuation_steps: int,
    min_normal_margin: float,
    min_history_margin_gap: float,
    min_action_l2_gap: float,
    device: torch.device,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any] | None, dict[str, Any] | None]:
    normal, normal_actions = replay_outcome_variant(
        model=model,
        snapshot=_as_outcome_snapshot(preferred),
        env_config=env_config,
        variant="normal",
        response_dim=response_dim,
        variant_hidden=None,
        normal_first_action=None,
        normal_actions=None,
        max_continuation_steps=max_continuation_steps,
        device=device,
    )
    normal_first_action = np.asarray(
        [
            normal.get("first_steer", float("nan")),
            normal.get("first_throttle", float("nan")),
            normal.get("first_brake", float("nan")),
        ],
        dtype=np.float32,
    )
    wrong, _ = replay_outcome_variant(
        model=model,
        snapshot=_as_outcome_snapshot(preferred),
        env_config=env_config,
        variant="wrong_matched_history",
        response_dim=response_dim,
        variant_hidden=wrong_history.hidden,
        normal_first_action=normal_first_action,
        normal_actions=normal_actions,
        max_continuation_steps=max_continuation_steps,
        device=device,
    )
    reset, _ = replay_outcome_variant(
        model=model,
        snapshot=_as_outcome_snapshot(preferred),
        env_config=env_config,
        variant="reset_hidden",
        response_dim=response_dim,
        variant_hidden=None,
        normal_first_action=normal_first_action,
        normal_actions=normal_actions,
        max_continuation_steps=max_continuation_steps,
        device=device,
    )
    normal_margin = _margin(normal)
    wrong_margin = _margin(wrong)
    reset_margin = _margin(reset)
    history_margin_gap = (
        float(normal_margin - wrong_margin) if np.isfinite(normal_margin) and np.isfinite(wrong_margin) else float("nan")
    )
    reset_margin_gap = (
        float(normal_margin - reset_margin) if np.isfinite(normal_margin) and np.isfinite(reset_margin) else float("nan")
    )
    success_drop = bool(normal.get("success", False) and not wrong.get("success", False))
    reset_success_drop = bool(normal.get("success", False) and not reset.get("success", False))
    action_l2_gap = _finite_float(wrong.get("first_action_distance"), default=0.0)
    reset_action_l2_gap = _finite_float(reset.get("first_action_distance"), default=0.0)
    normal_failed = (not bool(normal.get("success", False))) or normal_margin < float(min_normal_margin)
    history_action_critical = bool(
        not normal_failed
        and (
            success_drop
            or reset_success_drop
            or history_margin_gap >= float(min_history_margin_gap)
            or reset_margin_gap >= float(min_history_margin_gap)
        )
        and max(action_l2_gap, reset_action_l2_gap) >= float(min_action_l2_gap)
    )
    wrong_history_action_critical = bool(
        not normal_failed
        and (success_drop or history_margin_gap >= float(min_history_margin_gap))
        and action_l2_gap >= float(min_action_l2_gap)
    )
    reset_history_action_critical = bool(
        not normal_failed
        and (reset_success_drop or reset_margin_gap >= float(min_history_margin_gap))
        and reset_action_l2_gap >= float(min_action_l2_gap)
    )
    pair_row = {
        "pair_id": int(pair_id),
        "preferred_snapshot_id": int(preferred.snapshot_id),
        "wrong_snapshot_id": int(wrong_history.snapshot_id),
        "seed": int(preferred.seed),
        "step": int(preferred.step),
        "preferred_fault": preferred.fault.name,
        "preferred_fault_family": preferred.fault.family,
        "preferred_fault_severity": preferred.fault.severity,
        "wrong_fault": wrong_history.fault.name,
        "wrong_fault_family": wrong_history.fault.family,
        "wrong_fault_severity": wrong_history.fault.severity,
        "feature_distance": float(_feature_distance(preferred, wrong_history)),
        "normal_margin": normal_margin,
        "wrong_margin": wrong_margin,
        "reset_margin": reset_margin,
        "history_margin_gap": history_margin_gap,
        "reset_margin_gap": reset_margin_gap,
        "success_drop": success_drop,
        "reset_success_drop": reset_success_drop,
        "action_l2_gap": action_l2_gap,
        "reset_action_l2_gap": reset_action_l2_gap,
        "history_action_critical": history_action_critical,
        "wrong_history_action_critical": wrong_history_action_critical,
        "reset_history_action_critical": reset_history_action_critical,
        "assigned_split": assigned_split(int(preferred.seed), heldout_fraction=0.2),
    }
    rollout_rows: list[dict[str, Any]] = []
    for variant_result in (normal, wrong, reset):
        rollout_rows.append(
            {
                "pair_id": int(pair_id),
                "variant": str(variant_result.get("variant", "")),
                "success": bool(variant_result.get("success", False)),
                "collision": bool(variant_result.get("collision", False)),
                "terminal_reason": str(variant_result.get("terminal_reason", "")),
                "min_clearance_margin": _margin(variant_result),
                "risk": _risk(variant_result),
                "first_steer": _finite_float(variant_result.get("first_steer")),
                "first_throttle": _finite_float(variant_result.get("first_throttle")),
                "first_brake": _finite_float(variant_result.get("first_brake")),
                "first_action_distance": _finite_float(variant_result.get("first_action_distance")),
                "trajectory_l2_mean": _finite_float(variant_result.get("trajectory_l2_mean")),
                "trajectory_l2_max": _finite_float(variant_result.get("trajectory_l2_max")),
            }
        )
    if normal_failed:
        return pair_row, rollout_rows, None, {**pair_row, "rejection_reason": "normal_failed"}
    if not history_action_critical:
        return pair_row, rollout_rows, None, {**pair_row, "rejection_reason": "history_insensitive_too_mild"}
    return pair_row, rollout_rows, {**pair_row, "acceptance_reason": "history_action_critical"}, None


def _group_summary(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    if not rows:
        return []
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(str(row.get(key, "")), []).append(row)
    output: list[dict[str, Any]] = []
    for group_key, group_rows in sorted(groups.items()):
        accepted = [row for row in group_rows if bool(row.get("accepted", False))]
        output.append(
            {
                key: group_key,
                "rows": int(len(group_rows)),
                "accepted_rows": int(len(accepted)),
                "history_action_critical_rows": int(
                    sum(1 for row in group_rows if bool(row.get("history_action_critical", False)))
                ),
                "unique_seeds": int(len({int(row.get("seed", -1)) for row in group_rows})),
                "normal_margin_mean": float(np.mean([_finite_float(row.get("normal_margin")) for row in group_rows])),
                "history_margin_gap_mean": float(
                    np.nanmean([_finite_float(row.get("history_margin_gap")) for row in group_rows])
                ),
            }
        )
    return output


def _multi_group_summary(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    if not rows:
        return []
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in rows:
        group_key = tuple(str(row.get(key, "")) for key in keys)
        groups.setdefault(group_key, []).append(row)
    output: list[dict[str, Any]] = []
    for group_key, group_rows in sorted(groups.items()):
        accepted = [row for row in group_rows if bool(row.get("accepted", False))]
        reset_only = [row for row in group_rows if bool(row.get("reset_only", False))]
        item = {key: value for key, value in zip(keys, group_key, strict=True)}
        item.update(
            {
                "rows": int(len(group_rows)),
                "accepted_rows": int(len(accepted)),
                "reset_only_rows": int(len(reset_only)),
                "wrong_history_action_critical_rows": int(
                    sum(1 for row in group_rows if bool(row.get("wrong_history_action_critical", False)))
                ),
                "reset_history_action_critical_rows": int(
                    sum(1 for row in group_rows if bool(row.get("reset_history_action_critical", False)))
                ),
                "unique_seeds": int(len({int(row.get("seed", -1)) for row in group_rows})),
                "normal_margin_mean": float(np.nanmean([_finite_float(row.get("normal_margin")) for row in group_rows])),
                "history_margin_gap_mean": float(
                    np.nanmean([_finite_float(row.get("history_margin_gap")) for row in group_rows])
                ),
                "reset_margin_gap_mean": float(
                    np.nanmean([_finite_float(row.get("reset_margin_gap")) for row in group_rows])
                ),
            }
        )
        output.append(item)
    return output


def classify_extreme_result(
    *,
    matched_pair_count: int,
    accepted_rows: int,
    history_action_critical_rows: int,
    wrong_history_action_critical_rows: int,
    reset_history_action_critical_rows: int,
    unique_fault_families: int,
    unique_severities: int,
    unique_seeds: int,
    normal_failed_rejected: int,
    history_insensitive_rejected: int,
    model_fidelity_blocked: int,
    min_accepted_rows: int,
    min_history_rows: int,
    min_unique_fault_families: int,
    min_unique_severities: int,
    min_unique_seeds: int,
) -> str:
    if int(model_fidelity_blocked) > 0 and int(matched_pair_count) == 0:
        return "model_fidelity_blocked"
    if int(matched_pair_count) == 0:
        return "matched_state_empty"
    if int(accepted_rows) == 0 and int(normal_failed_rejected) >= int(matched_pair_count):
        return "all_failed_too_severe"
    if int(accepted_rows) == 0 and int(history_insensitive_rejected) > 0:
        return "history_insensitive_too_mild"
    if int(wrong_history_action_critical_rows) == 0 and int(reset_history_action_critical_rows) > 0:
        return "extreme_reset_sparse"
    positive = (
        int(accepted_rows) >= int(min_accepted_rows)
        and int(wrong_history_action_critical_rows) >= int(min_history_rows)
        and int(unique_fault_families) >= int(min_unique_fault_families)
        and int(unique_severities) >= int(min_unique_severities)
        and int(unique_seeds) >= int(min_unique_seeds)
    )
    return "extreme_source_positive" if positive else "extreme_source_sparse"


def classify_cross_fault_result(
    *,
    matched_pair_count: int,
    wrong_history_action_critical_rows: int,
    reset_history_action_critical_rows: int,
    normal_failed_rejected: int,
    history_insensitive_rejected: int,
    unique_preferred_fault_families: int,
    unique_wrong_fault_families: int,
    unique_severities: int,
    unique_seeds: int,
    min_accepted_rows: int,
    min_history_rows: int,
    min_unique_fault_families: int,
    min_unique_severities: int,
    min_unique_seeds: int,
) -> str:
    if int(matched_pair_count) == 0:
        return "matched_state_empty"
    if int(wrong_history_action_critical_rows) == 0 and int(reset_history_action_critical_rows) > 0:
        return "cross_fault_reset_only"
    if int(wrong_history_action_critical_rows) == 0 and int(normal_failed_rejected) >= int(matched_pair_count):
        return "normal_failed_too_severe"
    if int(wrong_history_action_critical_rows) == 0 and int(history_insensitive_rejected) > 0:
        return "history_insensitive_too_mild"
    positive = (
        int(wrong_history_action_critical_rows) >= int(min_history_rows)
        and int(wrong_history_action_critical_rows) >= int(min_accepted_rows)
        and int(unique_preferred_fault_families) >= int(min_unique_fault_families)
        and int(unique_wrong_fault_families) >= int(min_unique_fault_families)
        and int(unique_severities) >= int(min_unique_severities)
        and int(unique_seeds) >= int(min_unique_seeds)
    )
    return "cross_fault_wrong_positive" if positive else "cross_fault_wrong_sparse"


def run_extreme_dynamics_scenario_corpus(
    *,
    checkpoint_path: Path,
    config_path: Path,
    seed_start: int,
    seed_count: int,
    device: str,
    run_dir: Path,
    pairing_mode: str = "nominal",
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    config = load_scenario_config(config_path)
    if pairing_mode not in {"nominal", "cross_fault"}:
        raise ValueError(f"unknown pairing_mode {pairing_mode!r}")
    pairing_rules = tuple(config.get("pairing_rules", ()))
    if pairing_mode == "cross_fault" and not pairing_rules:
        raise ValueError("cross_fault pairing mode requires config pairing_rules")
    env_config = load_env_config(Path(config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    checksum_before = model_parameter_checksum(model)
    response_dim = response_feature_dim_for_model(model)
    faults: list[FaultSpec] = [NOMINAL_FAULT, *config["faults"]]
    max_steps = int(config.get("max_steps", 260))
    min_step = int(config.get("min_step", 35))
    snapshot_stride = int(config.get("snapshot_stride", 5))
    max_snapshots_per_scenario = int(config.get("max_snapshots_per_scenario", 4))
    obstacle_longitudinal_min = float(config.get("obstacle_longitudinal_min", -8.0))
    obstacle_longitudinal_max = float(config.get("obstacle_longitudinal_max", 90.0))
    max_pairs = int(config.get("max_pairs", 2048))
    max_continuation_steps = int(config.get("max_continuation_steps", 40))
    min_normal_margin = float(config.get("min_normal_margin", 0.0))
    min_history_margin_gap = float(config.get("min_history_margin_gap", 0.02))
    min_action_l2_gap = float(config.get("min_action_l2_gap", 0.015))

    snapshots: list[ExtremeSnapshot] = []
    scenario_rows: list[dict[str, Any]] = []
    for seed in range(int(seed_start), int(seed_start) + int(seed_count)):
        for fault in faults:
            scenario_snapshots, scenario_row = collect_fault_snapshots(
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
                device=resolved_device,
            )
            snapshots.extend(scenario_snapshots)
            scenario_rows.append(scenario_row)

    snapshots_by_seed: dict[int, list[ExtremeSnapshot]] = {}
    for snapshot in snapshots:
        snapshots_by_seed.setdefault(int(snapshot.seed), []).append(snapshot)

    pair_rows: list[dict[str, Any]] = []
    rollout_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    reset_only_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    unmatched_rows: list[dict[str, Any]] = []
    pair_id = 0
    for seed, seed_snapshots in sorted(snapshots_by_seed.items()):
        nominal_snapshots = [snapshot for snapshot in seed_snapshots if snapshot.fault.name == "nominal"]
        fault_snapshots = [snapshot for snapshot in seed_snapshots if snapshot.fault.name != "nominal"]
        for snapshot in fault_snapshots:
            if pair_id >= max_pairs:
                break
            if pairing_mode == "cross_fault":
                matched, match_distance, pairing_rule = find_cross_fault_match(snapshot, seed_snapshots, pairing_rules)
            else:
                matched, match_distance = find_nominal_match(snapshot, nominal_snapshots)
                pairing_rule = "fault->nominal"
            if matched is None:
                unmatched_rows.append(
                    {
                        "seed": int(seed),
                        "snapshot_id": int(snapshot.snapshot_id),
                        "fault_name": snapshot.fault.name,
                        "fault_family": snapshot.fault.family,
                        "fault_severity": snapshot.fault.severity,
                        "pairing_mode": pairing_mode,
                        "rejection_reason": "matched_state_empty",
                    }
                )
                continue
            pair_row, pair_rollouts, accepted, rejected = evaluate_matched_pair(
                pair_id=pair_id,
                preferred=snapshot,
                wrong_history=matched,
                model=model,
                env_config=env_config,
                response_dim=response_dim,
                max_continuation_steps=max_continuation_steps,
                min_normal_margin=min_normal_margin,
                min_history_margin_gap=min_history_margin_gap,
                min_action_l2_gap=min_action_l2_gap,
                device=resolved_device,
            )
            pair_row["match_distance"] = float(match_distance)
            pair_row["pairing_mode"] = pairing_mode
            pair_row["pairing_rule"] = pairing_rule
            accepted_is_wrong = bool(accepted is not None and accepted.get("wrong_history_action_critical", False))
            accepted_is_reset_only = bool(
                accepted is not None
                and not accepted.get("wrong_history_action_critical", False)
                and accepted.get("reset_history_action_critical", False)
            )
            if pairing_mode == "nominal":
                accepted_is_wrong = accepted is not None
                accepted_is_reset_only = False
            pair_row["accepted"] = accepted_is_wrong
            pair_row["reset_only"] = accepted_is_reset_only
            pair_rows.append(pair_row)
            rollout_rows.extend(pair_rollouts)
            if accepted_is_wrong and accepted is not None:
                accepted["match_distance"] = float(match_distance)
                accepted["pairing_mode"] = pairing_mode
                accepted["pairing_rule"] = pairing_rule
                accepted_rows.append(accepted)
            elif accepted_is_reset_only and accepted is not None:
                accepted["match_distance"] = float(match_distance)
                accepted["pairing_mode"] = pairing_mode
                accepted["pairing_rule"] = pairing_rule
                accepted["acceptance_reason"] = "reset_only_history_action_critical"
                reset_only_rows.append(accepted)
            if rejected is not None:
                rejected["match_distance"] = float(match_distance)
                rejected["pairing_mode"] = pairing_mode
                rejected["pairing_rule"] = pairing_rule
                rejected_rows.append(rejected)
            pair_id += 1
        if pair_id >= max_pairs:
            break

    accepted_fault_families = {str(row.get("preferred_fault_family", "")) for row in accepted_rows}
    accepted_wrong_fault_families = {str(row.get("wrong_fault_family", "")) for row in accepted_rows}
    accepted_severities = {str(row.get("preferred_fault_severity", "")) for row in accepted_rows}
    accepted_seeds = {int(row.get("seed", -1)) for row in accepted_rows}
    normal_failed_rejected = sum(1 for row in rejected_rows if row.get("rejection_reason") == "normal_failed")
    history_insensitive_rejected = sum(
        1 for row in rejected_rows if row.get("rejection_reason") == "history_insensitive_too_mild"
    )
    model_fidelity_blocked = len(config.get("future_only_faults", []))
    if pairing_mode == "cross_fault":
        result_class = classify_cross_fault_result(
            matched_pair_count=len(pair_rows),
            wrong_history_action_critical_rows=sum(
                1 for row in accepted_rows if bool(row.get("wrong_history_action_critical", False))
            ),
            reset_history_action_critical_rows=sum(
                1 for row in reset_only_rows if bool(row.get("reset_history_action_critical", False))
            ),
            normal_failed_rejected=normal_failed_rejected,
            history_insensitive_rejected=history_insensitive_rejected,
            unique_preferred_fault_families=len(accepted_fault_families),
            unique_wrong_fault_families=len(accepted_wrong_fault_families),
            unique_severities=len(accepted_severities),
            unique_seeds=len(accepted_seeds),
            min_accepted_rows=int(config.get("min_accepted_rows", 80)),
            min_history_rows=int(config.get("min_history_rows", 30)),
            min_unique_fault_families=int(config.get("min_unique_fault_families", 4)),
            min_unique_severities=int(config.get("min_unique_severities", 2)),
            min_unique_seeds=int(config.get("min_unique_seeds", 30)),
        )
    else:
        result_class = classify_extreme_result(
            matched_pair_count=len(pair_rows),
            accepted_rows=len(accepted_rows),
            history_action_critical_rows=sum(
                1 for row in accepted_rows if bool(row.get("history_action_critical", False))
            ),
            wrong_history_action_critical_rows=sum(
                1 for row in accepted_rows if bool(row.get("wrong_history_action_critical", False))
            ),
            reset_history_action_critical_rows=sum(
                1 for row in accepted_rows if bool(row.get("reset_history_action_critical", False))
            ),
            unique_fault_families=len(accepted_fault_families),
            unique_severities=len(accepted_severities),
            unique_seeds=len(accepted_seeds),
            normal_failed_rejected=normal_failed_rejected,
            history_insensitive_rejected=history_insensitive_rejected,
            model_fidelity_blocked=model_fidelity_blocked,
            min_accepted_rows=int(config.get("min_accepted_rows", 80)),
            min_history_rows=int(config.get("min_history_rows", 30)),
            min_unique_fault_families=int(config.get("min_unique_fault_families", 4)),
            min_unique_severities=int(config.get("min_unique_severities", 2)),
            min_unique_seeds=int(config.get("min_unique_seeds", 30)),
        )
    checksum_after = model_parameter_checksum(model)
    pair_summary_rows = []
    for row in pair_rows:
        pair_summary_rows.append(
            {
                "preferred_fault_family": row.get("preferred_fault_family"),
                "preferred_fault_severity": row.get("preferred_fault_severity"),
                "wrong_fault_family": row.get("wrong_fault_family"),
                "wrong_fault_severity": row.get("wrong_fault_severity"),
                "fault_family_pair": f"{row.get('preferred_fault_family')}->{row.get('wrong_fault_family')}",
                "severity_pair": f"{row.get('preferred_fault_severity')}->{row.get('wrong_fault_severity')}",
                "seed": row.get("seed"),
                "accepted": bool(row.get("accepted", False)),
                "reset_only": bool(row.get("reset_only", False)),
                "history_action_critical": bool(row.get("history_action_critical", False)),
                "wrong_history_action_critical": bool(row.get("wrong_history_action_critical", False)),
                "reset_history_action_critical": bool(row.get("reset_history_action_critical", False)),
                "normal_margin": row.get("normal_margin"),
                "history_margin_gap": row.get("history_margin_gap"),
                "reset_margin_gap": row.get("reset_margin_gap"),
            }
        )
    future_only_faults = config.get("future_only_faults", [])
    fidelity_text = [
        "# M704 Model Fidelity Limits",
        "",
        "Current generated rows use the single-track model and only claim current-model capability faults or proxies.",
        "",
        "Future four-wheel-only faults not generated as physically faithful current-model data:",
        "",
        *[f"- {item}" for item in future_only_faults],
        "",
    ]
    (run_dir / "model_fidelity_limits.md").write_text("\n".join(fidelity_text), encoding="utf-8")
    write_csv_rows(run_dir / "scenario_summary.csv", scenario_rows)
    write_csv_rows(run_dir / "snapshot_candidates.csv", [_snapshot_row(snapshot) for snapshot in snapshots])
    write_csv_rows(run_dir / "matched_hidden_condition_pairs.csv", pair_rows)
    write_csv_rows(run_dir / "matched_cross_fault_pairs.csv", pair_rows if pairing_mode == "cross_fault" else [])
    write_csv_rows(run_dir / "intervention_rollouts.csv", rollout_rows)
    write_csv_rows(run_dir / "accepted_rows.csv", accepted_rows)
    write_csv_rows(run_dir / "reset_only_rows.csv", reset_only_rows)
    write_csv_rows(run_dir / "rejected_rows.csv", [*rejected_rows, *unmatched_rows])
    write_csv_rows(run_dir / "fault_family_summary.csv", _group_summary(pair_summary_rows, "preferred_fault_family"))
    write_csv_rows(run_dir / "severity_summary.csv", _group_summary(pair_summary_rows, "preferred_fault_severity"))
    write_csv_rows(run_dir / "fault_family_pair_summary.csv", _multi_group_summary(pair_summary_rows, ("fault_family_pair",)))
    write_csv_rows(run_dir / "severity_pair_summary.csv", _multi_group_summary(pair_summary_rows, ("severity_pair",)))
    write_csv_rows(
        run_dir / "cross_fault_pair_summary.csv",
        _multi_group_summary(pair_summary_rows, ("fault_family_pair", "severity_pair")),
    )
    summary = {
        "run_type": "cross_fault_wrong_history_scenario"
        if pairing_mode == "cross_fault"
        else "extreme_dynamics_scenario_corpus",
        "checkpoint": checkpoint_path,
        "config": config_path,
        "env_config": config.get("env_config"),
        "pairing_mode": pairing_mode,
        "pairing_rules": [
            {
                "preferred_family": rule.preferred_family,
                "wrong_family": rule.wrong_family,
                "preferred_severities": list(rule.preferred_severities),
                "wrong_severities": list(rule.wrong_severities),
            }
            for rule in pairing_rules
        ],
        "seed_start": int(seed_start),
        "seed_count": int(seed_count),
        "fault_count": int(len(faults) - 1),
        "future_only_fault_count": int(len(future_only_faults)),
        "scenario_count": int(len(scenario_rows)),
        "snapshot_count": int(len(snapshots)),
        "matched_pair_count": int(len(pair_rows)),
        "unmatched_rows": int(len(unmatched_rows)),
        "accepted_rows": int(len(accepted_rows)),
        "reset_only_rows": int(len(reset_only_rows)),
        "rejected_rows": int(len(rejected_rows)),
        "normal_failed_rejected": int(normal_failed_rejected),
        "history_insensitive_rejected": int(history_insensitive_rejected),
        "history_action_critical_rows": int(
            sum(
                1
                for row in [*accepted_rows, *reset_only_rows]
                if bool(row.get("history_action_critical", False))
            )
        ),
        "wrong_history_action_critical_rows": int(
            sum(1 for row in accepted_rows if bool(row.get("wrong_history_action_critical", False)))
        ),
        "reset_history_action_critical_rows": int(
            sum(1 for row in reset_only_rows if bool(row.get("reset_history_action_critical", False)))
        ),
        "unique_accepted_fault_families": int(len(accepted_fault_families)),
        "unique_accepted_wrong_fault_families": int(len(accepted_wrong_fault_families)),
        "unique_accepted_severities": int(len(accepted_severities)),
        "unique_accepted_seeds": int(len(accepted_seeds)),
        "current_model_fault_families": sorted({fault.family for fault in config["faults"]}),
        "future_only_fault_families": future_only_faults,
        "actor_parameters_changed": bool(checksum_before != checksum_after),
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "result_class": result_class,
        "extreme_source_positive": bool(result_class == "extreme_source_positive"),
        "wrong_history_source_positive": bool(result_class == "cross_fault_wrong_positive"),
        "scenario_summary_csv": run_dir / "scenario_summary.csv",
        "fault_family_summary_csv": run_dir / "fault_family_summary.csv",
        "fault_family_pair_summary_csv": run_dir / "fault_family_pair_summary.csv",
        "severity_summary_csv": run_dir / "severity_summary.csv",
        "severity_pair_summary_csv": run_dir / "severity_pair_summary.csv",
        "cross_fault_pair_summary_csv": run_dir / "cross_fault_pair_summary.csv",
        "matched_hidden_condition_pairs_csv": run_dir / "matched_hidden_condition_pairs.csv",
        "matched_cross_fault_pairs_csv": run_dir / "matched_cross_fault_pairs.csv",
        "accepted_rows_csv": run_dir / "accepted_rows.csv",
        "reset_only_rows_csv": run_dir / "reset_only_rows.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
        "model_fidelity_limits_md": run_dir / "model_fidelity_limits.md",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate extreme hidden-condition scenario corpus.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--pairing-mode", choices=["nominal", "cross_fault"], default="nominal")
    parser.add_argument("--seed-start", type=int, default=40000)
    parser.add_argument("--seed-count", type=int, default=512)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="extreme_dynamics_scenario_corpus")
    summary = run_extreme_dynamics_scenario_corpus(
        checkpoint_path=args.checkpoint,
        config_path=args.config,
        seed_start=args.seed_start,
        seed_count=args.seed_count,
        device=args.device,
        run_dir=run_dir,
        pairing_mode=args.pairing_mode,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
