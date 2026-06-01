"""No-reset materialization for current-sim scenario task-family configs."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config
from autodrift.scenarios import ObstacleScenario, ObstacleScenarioConfig, classify_obstacle_scenario


DEFAULT_CONFIG_OUTPUT = Path("configs/paper_route_current_sim_scenario_task_family_v0.json")
DEFAULT_OUTPUT_DIR = Path("runs/m2277_paper_route_current_sim_scenario_task_family_config_materialization")
DEFAULT_NEXT_BLOCKER = "m2278-paper-route-current-sim-scenario-task-family-config-materialization-result-audit"
TARGET_ROLE_FAMILY_COUNT = 6
TARGET_SPECS_PER_ROLE = 12
TARGET_SCENARIO_SPEC_COUNT = TARGET_ROLE_FAMILY_COUNT * TARGET_SPECS_PER_ROLE
ACTOR_CONTRACT_ID = "P0_human_view_no_wheel_no_oracle"
TRACK_RADIUS_M = 80.0
TIMING_BUCKETS = {
    "early_far": {
        "distance_range": (34.0, 52.0),
        "speed_range": (8.0, 13.0),
        "representative_distance_m": 43.0,
        "representative_speed_mps": 10.5,
    },
    "mid": {
        "distance_range": (20.0, 34.0),
        "speed_range": (10.0, 16.0),
        "representative_distance_m": 27.0,
        "representative_speed_mps": 13.0,
    },
    "late_close": {
        "distance_range": (11.0, 22.0),
        "speed_range": (13.0, 19.0),
        "representative_distance_m": 16.5,
        "representative_speed_mps": 16.0,
    },
}
LATERAL_BUCKETS = {
    "centerline": 0.0,
    "left_offset": 1.2,
    "right_offset": -1.2,
}
RECOVERY_BUCKETS = {
    "none": 0.0,
    "short": 1.0,
    "medium": 2.0,
    "long": 3.0,
}
HIDDEN_DYNAMICS = {
    "nominal": {
        "mu_range": (0.55, 1.10),
        "brake_scale_range": (0.85, 1.15),
        "drive_scale_range": (0.85, 1.15),
        "tire_stiffness_scale_range": (0.85, 1.15),
        "actuator_tau_scale_range": (0.85, 1.30),
        "mass_scale_range": (0.95, 1.05),
        "inertia_scale_range": (0.95, 1.05),
    },
    "low_mu": {
        "mu_range": (0.25, 0.65),
        "brake_scale_range": (0.75, 1.10),
        "tire_stiffness_scale_range": (0.60, 1.20),
    },
    "weak_brake": {
        "mu_range": (0.35, 1.00),
        "brake_scale_range": (0.42, 0.78),
        "drive_scale_range": (0.75, 1.15),
    },
    "slow_steer_actuator": {
        "mu_range": (0.45, 1.05),
        "actuator_tau_scale_range": (1.75, 4.20),
    },
    "high_mass_or_inertia": {
        "mu_range": (0.40, 1.05),
        "mass_scale_range": (1.12, 1.30),
        "inertia_scale_range": (1.12, 1.35),
    },
    "tire_stiffness_shift": {
        "mu_range": (0.35, 1.05),
        "tire_stiffness_scale_range": (0.45, 1.55),
    },
}
ROLE_FAMILIES = (
    {
        "role_family": "R0_stable_avoidable",
        "scenario_family_id": "R0",
        "role_semantics": "pure braking is feasible before the obstacle",
        "sampled_obstacle_label": "aeb_feasible",
        "allowed_labels": ("aeb_feasible",),
        "hidden_buckets": ("nominal", "nominal", "slow_steer_actuator"),
        "recovery_buckets": ("none",),
        "track_width_m": 6.0,
        "half_width_m": 0.55,
        "finish_on_pass": True,
    },
    {
        "role_family": "R1_aeb_infeasible_stable_aes",
        "scenario_family_id": "R1",
        "role_semantics": "AEB infeasible, stable AES feasible",
        "sampled_obstacle_label": "aes_feasible",
        "allowed_labels": ("aes_feasible",),
        "require_aeb_infeasible": True,
        "hidden_buckets": ("nominal", "weak_brake", "slow_steer_actuator"),
        "recovery_buckets": ("none",),
        "track_width_m": 6.0,
        "half_width_m": 0.75,
        "finish_on_pass": True,
    },
    {
        "role_family": "R2_handling_limit_drift_capable_avoidance",
        "scenario_family_id": "R2",
        "role_semantics": "handling-limit or drift-like avoidance may be needed",
        "sampled_obstacle_label": "drift_required",
        "allowed_labels": ("drift_required",),
        "require_aeb_infeasible": True,
        "hidden_buckets": ("low_mu", "tire_stiffness_shift", "slow_steer_actuator"),
        "recovery_buckets": ("short", "medium"),
        "track_width_m": 6.5,
        "half_width_m": 1.05,
        "finish_on_pass": False,
    },
    {
        "role_family": "R3_recovery_after_limit",
        "scenario_family_id": "R3",
        "role_semantics": "post-maneuver recovery after handling-limit motion is the task",
        "sampled_obstacle_label": "drift_required",
        "allowed_labels": ("drift_required",),
        "require_aeb_infeasible": True,
        "hidden_buckets": ("low_mu", "slow_steer_actuator", "tire_stiffness_shift"),
        "recovery_buckets": ("short", "medium", "long"),
        "track_width_m": 6.0,
        "half_width_m": 0.95,
        "finish_on_pass": False,
    },
    {
        "role_family": "R4_unavoidable_mitigation",
        "scenario_family_id": "R4",
        "role_semantics": "collision may be unavoidable; mitigate impact and secondary departure",
        "sampled_obstacle_label": "unavoidable",
        "allowed_labels": ("unavoidable",),
        "require_aeb_infeasible": True,
        "hidden_buckets": ("low_mu", "weak_brake", "high_mass_or_inertia"),
        "recovery_buckets": ("none", "short"),
        "track_width_m": 5.5,
        "half_width_m": 1.25,
        "finish_on_pass": False,
    },
    {
        "role_family": "R5_hidden_dynamics_robustness",
        "scenario_family_id": "R5",
        "role_semantics": "same scene templates crossed with hidden dynamics buckets",
        "sampled_obstacle_label": "aes_feasible",
        "allowed_labels": ("aes_feasible", "drift_required"),
        "require_aeb_infeasible": True,
        "hidden_buckets": ("nominal", "low_mu", "weak_brake", "slow_steer_actuator"),
        "recovery_buckets": ("none", "medium"),
        "track_width_m": 6.0,
        "half_width_m": 0.90,
        "finish_on_pass": False,
    },
)
REQUIRED_METADATA_FIELDS = (
    "scenario_spec_id",
    "scenario_family_id",
    "role_family",
    "role_semantics",
    "sampled_obstacle_label",
    "allowed_labels_metadata_only",
    "labels_enter_actor_input",
    "same_scene_group_id",
    "hidden_dynamics_bucket",
    "obstacle_longitudinal_distance_m",
    "obstacle_longitudinal_timing_bucket",
    "obstacle_lateral_offset_m",
    "obstacle_lateral_offset_bucket",
    "obstacle_half_width_m",
    "initial_speed_mps",
    "initial_speed_bucket",
    "track_kind",
    "track_radius_m",
    "track_width_m",
    "road_curvature_bucket",
    "friction_bucket",
    "mu_range",
    "brake_scale_bucket",
    "brake_scale_range",
    "actuator_lag_bucket",
    "steer_tau_scale_range",
    "drive_tau_scale_range",
    "vehicle_mass_or_inertia_bucket",
    "mass_scale_range",
    "inertia_scale_range",
    "tire_stiffness_bucket",
    "front_tire_stiffness_scale_range",
    "rear_tire_stiffness_scale_range",
    "recovery_window_s",
    "recovery_window_bucket",
    "finish_on_pass",
    "obstacle_relative_velocity_mode",
    "wheel_observation_mode",
    "include_privileged_params",
    "history_length",
    "actor_contract_id",
    "diagnostic_only_no_ranking_claim",
    "ranking_admissible",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
    "env_config",
)
UNSUPPORTED_FUTURE_FAULTS = (
    (
        "single_wheel_blowout_or_puncture",
        "current model has front/rear lumped tire forces, not per-wheel tire state",
    ),
    (
        "wheel_specific_grip_loss",
        "current env randomizes vehicle-level friction, not wheel-specific grip patches",
    ),
    (
        "half_shaft_or_single_side_drive_torque_loss",
        "current RWD model exposes one longitudinal drive/brake force state",
    ),
    (
        "brake_side_imbalance",
        "current brake scale is vehicle-level, not side-specific",
    ),
    (
        "steering_deadzone_or_partial_actuator_fault",
        "current actuator stress supports delay scaling, not deadzone or partial lock",
    ),
    (
        "sensor_dropout_or_bias",
        "current observation noise/dropout is not represented in this scenario materializer",
    ),
)


def _range_around(center: float, width: float, *, floor: float = 0.01) -> tuple[float, float]:
    return (max(floor, center - width), max(floor, center + width))


def _range_text(value: tuple[float, float]) -> str:
    return f"{float(value[0]):.6g}:{float(value[1]):.6g}"


def _bucket_from_range(value: tuple[float, float], *, low: float, high: float, labels: tuple[str, str, str]) -> str:
    midpoint = 0.5 * (float(value[0]) + float(value[1]))
    if midpoint < low:
        return labels[0]
    if midpoint > high:
        return labels[2]
    return labels[1]


def _replace_nested(data: dict[str, Any], key: str, updates: Mapping[str, Any]) -> None:
    nested = deepcopy(dict(data.get(key) or {}))
    nested.update(dict(updates))
    data[key] = nested


def _linspace(low: float, high: float, count: int) -> tuple[float, ...]:
    if count <= 1 or math.isclose(float(low), float(high)):
        return (float(0.5 * (float(low) + float(high))),)
    step = (float(high) - float(low)) / float(count - 1)
    return tuple(float(low) + step * index for index in range(count))


@dataclass(frozen=True)
class SamplerTarget:
    speed_mps: float
    mu: float
    obstacle_distance_m: float
    obstacle_half_width_m: float
    scenario: ObstacleScenario
    margin_score: float


def _scenario_margin_score(scenario: ObstacleScenario) -> float:
    aeb_infeasible_margin = scenario.aeb_stop_distance - (scenario.obstacle_distance - 0.30)
    conventional_margin = scenario.conventional_lateral_capacity - scenario.required_lateral_offset
    drift_margin = scenario.drift_lateral_capacity - scenario.required_lateral_offset
    if scenario.label == "aeb_feasible":
        return float(-aeb_infeasible_margin)
    if scenario.label == "aes_feasible":
        return float(min(aeb_infeasible_margin, conventional_margin))
    if scenario.label == "drift_required":
        return float(min(aeb_infeasible_margin, -conventional_margin, drift_margin))
    if scenario.label == "unavoidable":
        return float(min(aeb_infeasible_margin, -drift_margin))
    return float("-inf")


def _speed_under_friction_cap(speed: float, mu: float, *, radius: float = TRACK_RADIUS_M) -> bool:
    cap = math.sqrt(max(float(mu) * 9.81 * float(radius), 1e-6)) * 0.92
    return float(speed) <= cap + 1e-9


def _reset_filter_compatible(env_config: Mapping[str, Any], scenario: ObstacleScenario) -> bool:
    obstacle = dict(env_config.get("obstacle") or {})
    allowed_labels = set(str(label) for label in obstacle.get("allowed_labels", ()))
    if allowed_labels and scenario.label not in allowed_labels:
        return False
    if bool(obstacle.get("require_aeb_infeasible", False)) and scenario.label == "aeb_feasible":
        return False

    speed_range = tuple(float(value) for value in env_config.get("speed_range", (scenario.speed, scenario.speed)))
    randomization = dict(env_config.get("randomization") or {})
    mu_range = tuple(float(value) for value in randomization.get("mu_range", (scenario.mu, scenario.mu)))
    track_radius = float(env_config.get("track_radius", TRACK_RADIUS_M))
    if bool(env_config.get("friction_limited_speed", True)):
        for speed in speed_range:
            for mu in mu_range:
                if not _speed_under_friction_cap(speed, mu, radius=track_radius):
                    return False

    friction_step = dict(env_config.get("friction_step") or {})
    if not bool(friction_step.get("enabled", False)):
        return True
    step_range = tuple(int(value) for value in friction_step.get("step_range", (250, 550)))
    max_steps = int(env_config.get("max_steps", 0))
    low = max(1, int(step_range[0]))
    high = min(int(step_range[1]), max_steps - 1)
    if high < low:
        return True
    dt = float(env_config.get("dt", 0.02))
    min_time_after_step = float(obstacle.get("min_time_after_friction_step", 0.0) or 0.0)
    latest_valid_step = int(math.floor((scenario.time_to_obstacle - min_time_after_step) / dt))
    return high <= latest_valid_step


def _candidate_half_widths(family: Mapping[str, Any]) -> tuple[float, ...]:
    base = float(family["half_width_m"])
    role_id = str(family["scenario_family_id"])
    values = {base, max(0.45, base - 0.35), base + 0.35}
    if role_id == "R4":
        values.update({1.25, 1.8, 2.6, 4.0, 7.0})
    elif role_id in {"R2", "R3"}:
        values.update({0.45, 0.65, 0.90, 1.25, 1.60, 2.20, 3.00})
    elif role_id in {"R1", "R5"}:
        values.update({0.45, 0.55, 0.75, 0.90, 1.05, 1.25})
    else:
        values.update({0.45, 0.55, 0.75, 0.90})
    return tuple(sorted(float(value) for value in values if float(value) > 0.0))


def _select_sampler_target(
    family: Mapping[str, Any],
    *,
    timing_bucket: str,
    hidden_bucket: str,
) -> SamplerTarget:
    timing = TIMING_BUCKETS[timing_bucket]
    hidden = HIDDEN_DYNAMICS[hidden_bucket]
    mu_low, mu_high = tuple(float(value) for value in hidden.get("mu_range", HIDDEN_DYNAMICS["nominal"]["mu_range"]))
    allowed_labels = set(str(label) for label in family["allowed_labels"])
    require_aeb_infeasible = bool(family.get("require_aeb_infeasible", False))
    scenario_config = ObstacleScenarioConfig()
    candidates: list[SamplerTarget] = []
    speed_values = tuple(
        sorted(
            {
                *_linspace(float(timing["speed_range"][0]), float(timing["speed_range"][1]), 11),
                *_linspace(8.0, 24.0, 17),
            }
        )
    )
    distance_values = _linspace(float(timing["distance_range"][0]), float(timing["distance_range"][1]), 19)
    mu_values = _linspace(mu_low, mu_high, 9)
    for mu in mu_values:
        for speed in speed_values:
            if not _speed_under_friction_cap(speed, mu):
                continue
            for distance in distance_values:
                for half_width in _candidate_half_widths(family):
                    scenario = classify_obstacle_scenario(
                        speed=speed,
                        mu=mu,
                        obstacle_distance=distance,
                        obstacle_half_width=half_width,
                        config=scenario_config,
                    )
                    if scenario.label not in allowed_labels:
                        continue
                    if require_aeb_infeasible and scenario.label == "aeb_feasible":
                        continue
                    margin_score = _scenario_margin_score(scenario)
                    if margin_score <= 0.02:
                        continue
                    width_penalty = 0.04 * abs(float(half_width) - float(family["half_width_m"]))
                    speed_penalty = 0.01 * abs(float(speed) - float(timing["representative_speed_mps"]))
                    distance_penalty = 0.003 * abs(float(distance) - float(timing["representative_distance_m"]))
                    score = float(margin_score - width_penalty - speed_penalty - distance_penalty)
                    candidates.append(
                        SamplerTarget(
                            speed_mps=float(speed),
                            mu=float(mu),
                            obstacle_distance_m=float(distance),
                            obstacle_half_width_m=float(half_width),
                            scenario=scenario,
                            margin_score=score,
                        )
                    )
    if not candidates:
        raise ValueError(
            "failed to find reset-valid sampler target for "
            f"{family['scenario_family_id']} timing={timing_bucket} hidden={hidden_bucket}"
        )
    return max(candidates, key=lambda candidate: candidate.margin_score)


def _base_env_config() -> dict[str, Any]:
    return {
        "dt": 0.02,
        "max_steps": 520,
        "track_kind": "circle",
        "track_radius": TRACK_RADIUS_M,
        "track_width": 6.0,
        "speed_range": (8.0, 14.0),
        "history_length": 1,
        "action_history_mode": "full",
        "include_privileged_params": False,
        "obstacle_relative_velocity_mode": "zero",
        "wheel_observation_mode": "none",
        "friction_limited_speed": True,
        "obstacle": {
            "enabled": True,
            "distance_range": (16.0, 40.0),
            "half_width_range": (0.65, 1.10),
            "allowed_labels": ("aes_feasible", "drift_required"),
            "require_aeb_infeasible": False,
            "finish_on_pass": False,
            "finish_pass_distance": 1.5,
            "max_sample_attempts": 360,
            "perception_reveal_step": 0,
            "clearance_margin_reward_scale": 0.0,
            "dense_clearance_margin_reward_scale": 0.0,
        },
        "randomization": deepcopy(HIDDEN_DYNAMICS["nominal"]),
        "friction_step": {"enabled": False},
    }


def _env_config_for_spec(
    family: Mapping[str, Any],
    *,
    timing_bucket: str,
    hidden_bucket: str,
    recovery_bucket: str,
    lateral_offset_m: float,
) -> tuple[dict[str, Any], SamplerTarget]:
    target = _select_sampler_target(family, timing_bucket=timing_bucket, hidden_bucket=hidden_bucket)
    hidden = deepcopy(HIDDEN_DYNAMICS[hidden_bucket])
    hidden["mu_range"] = (target.mu, target.mu)
    env = _base_env_config()
    env["speed_range"] = (target.speed_mps, target.speed_mps)
    env["track_width"] = float(family["track_width_m"])
    env["max_steps"] = 560 if recovery_bucket != "none" else 420
    _replace_nested(
        env,
        "obstacle",
        {
            "distance_range": (target.obstacle_distance_m, target.obstacle_distance_m),
            "half_width_range": (target.obstacle_half_width_m, target.obstacle_half_width_m),
            "lateral_offset_range": (float(lateral_offset_m), float(lateral_offset_m)),
            "allowed_labels": tuple(str(label) for label in family["allowed_labels"]),
            "require_aeb_infeasible": bool(family.get("require_aeb_infeasible", False)),
            "finish_on_pass": bool(family["finish_on_pass"]),
            "finish_pass_distance": 1.0 if recovery_bucket != "none" else 1.5,
        },
    )
    _replace_nested(env, "randomization", hidden)
    if not _reset_filter_compatible(env, target.scenario):
        raise ValueError(
            "selected target is not compatible with reset filters for "
            f"{family['scenario_family_id']} timing={timing_bucket} hidden={hidden_bucket}"
        )
    return env, target


def assert_p0_actor_contract(env_config: Mapping[str, Any]) -> None:
    """Reject deployable actor-input contract violations without resetting envs."""

    config = build_env_config(dict(env_config))
    if int(config.history_length) != 1:
        raise ValueError("history_length must remain 1 for P0 online-GRU frame contract")
    if config.action_history_mode != "full":
        raise ValueError("previous physical commands must remain available")
    if config.include_privileged_params:
        raise ValueError("privileged actor observation is forbidden")
    if config.obstacle_relative_velocity_mode != "zero":
        raise ValueError("obstacle relative velocity must stay zero in strict current-sim pack")
    if config.wheel_observation_mode != "none":
        raise ValueError("wheel or slip observations are forbidden")


def materialize_scenario_specs() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    specs: list[dict[str, Any]] = []
    contract_violations: list[dict[str, Any]] = []
    unsupported_rows: list[dict[str, Any]] = []
    timing_names = tuple(TIMING_BUCKETS)
    lateral_names = tuple(LATERAL_BUCKETS)
    for family in ROLE_FAMILIES:
        role = str(family["role_family"])
        role_id = str(family["scenario_family_id"])
        hidden_buckets = tuple(str(item) for item in family["hidden_buckets"])
        recovery_buckets = tuple(str(item) for item in family["recovery_buckets"])
        for index in range(TARGET_SPECS_PER_ROLE):
            if role_id == "R5":
                scene_index = index // len(hidden_buckets)
                hidden_bucket = hidden_buckets[index % len(hidden_buckets)]
                timing_bucket = timing_names[scene_index % len(timing_names)]
                lateral_bucket = lateral_names[scene_index % len(lateral_names)]
                same_scene_group_id = f"m2277_{role_id.lower()}_scene_{scene_index:02d}"
            else:
                hidden_bucket = hidden_buckets[(index // 4) % len(hidden_buckets)]
                timing_bucket = timing_names[index % len(timing_names)]
                lateral_bucket = lateral_names[(index // len(timing_names)) % len(lateral_names)]
                same_scene_group_id = f"m2277_{role_id.lower()}_{index:02d}"
            recovery_bucket = recovery_buckets[index % len(recovery_buckets)]
            lateral_offset = float(LATERAL_BUCKETS[lateral_bucket])
            env_config, sampler_target = _env_config_for_spec(
                family,
                timing_bucket=timing_bucket,
                hidden_bucket=hidden_bucket,
                recovery_bucket=recovery_bucket,
                lateral_offset_m=lateral_offset,
            )
            scenario_spec_id = f"m2277_{role_id.lower()}_{index:02d}"
            violation_messages: list[str] = []
            try:
                assert_p0_actor_contract(env_config)
            except Exception as exc:  # noqa: BLE001 - materializer records all contract failures.
                violation_messages.append(str(exc))
            hidden_for_metadata = dict(env_config.get("randomization") or {})
            mu_range = tuple(float(v) for v in hidden_for_metadata.get("mu_range", HIDDEN_DYNAMICS["nominal"]["mu_range"]))
            brake_range = tuple(
                float(v)
                for v in hidden_for_metadata.get("brake_scale_range", HIDDEN_DYNAMICS["nominal"]["brake_scale_range"])
            )
            tau_range = tuple(
                float(v)
                for v in hidden_for_metadata.get(
                    "actuator_tau_scale_range", HIDDEN_DYNAMICS["nominal"]["actuator_tau_scale_range"]
                )
            )
            mass_range = tuple(
                float(v)
                for v in hidden_for_metadata.get("mass_scale_range", HIDDEN_DYNAMICS["nominal"]["mass_scale_range"])
            )
            inertia_range = tuple(
                float(v)
                for v in hidden_for_metadata.get("inertia_scale_range", HIDDEN_DYNAMICS["nominal"]["inertia_scale_range"])
            )
            tire_range = tuple(
                float(v)
                for v in hidden_for_metadata.get(
                    "tire_stiffness_scale_range", HIDDEN_DYNAMICS["nominal"]["tire_stiffness_scale_range"]
                )
            )
            spec = {
                "scenario_spec_id": scenario_spec_id,
                "scenario_family_id": role_id,
                "role_family": role,
                "role_semantics": str(family["role_semantics"]),
                "sampled_obstacle_label": str(sampler_target.scenario.label),
                "allowed_labels_metadata_only": ";".join(str(label) for label in family["allowed_labels"]),
                "labels_enter_actor_input": False,
                "same_scene_group_id": same_scene_group_id,
                "hidden_dynamics_bucket": hidden_bucket,
                "obstacle_longitudinal_distance_m": float(sampler_target.obstacle_distance_m),
                "obstacle_longitudinal_timing_bucket": timing_bucket,
                "obstacle_lateral_offset_m": lateral_offset,
                "obstacle_lateral_offset_bucket": lateral_bucket,
                "obstacle_half_width_m": float(sampler_target.obstacle_half_width_m),
                "initial_speed_mps": float(sampler_target.speed_mps),
                "initial_speed_bucket": timing_bucket,
                "track_kind": "circle",
                "track_radius_m": TRACK_RADIUS_M,
                "track_width_m": float(family["track_width_m"]),
                "road_curvature_bucket": f"circle_r{int(TRACK_RADIUS_M)}",
                "friction_bucket": _bucket_from_range(
                    mu_range,
                    low=0.40,
                    high=0.80,
                    labels=("low_mu", "mixed_mu", "high_mu"),
                ),
                "mu_range": _range_text(mu_range),
                "brake_scale_bucket": _bucket_from_range(
                    brake_range,
                    low=0.70,
                    high=1.05,
                    labels=("weak_brake", "mixed_brake", "strong_brake"),
                ),
                "brake_scale_range": _range_text(brake_range),
                "actuator_lag_bucket": _bucket_from_range(
                    tau_range,
                    low=1.10,
                    high=2.00,
                    labels=("fast_actuator", "mixed_actuator", "slow_actuator"),
                ),
                "steer_tau_scale_range": _range_text(tau_range),
                "drive_tau_scale_range": _range_text(tau_range),
                "vehicle_mass_or_inertia_bucket": _bucket_from_range(
                    (0.5 * (mass_range[0] + inertia_range[0]), 0.5 * (mass_range[1] + inertia_range[1])),
                    low=0.95,
                    high=1.12,
                    labels=("light_or_low_inertia", "nominal_mass", "heavy_or_high_inertia"),
                ),
                "mass_scale_range": _range_text(mass_range),
                "inertia_scale_range": _range_text(inertia_range),
                "tire_stiffness_bucket": _bucket_from_range(
                    tire_range,
                    low=0.75,
                    high=1.20,
                    labels=("soft_tire", "mixed_tire", "stiff_tire"),
                ),
                "front_tire_stiffness_scale_range": _range_text(tire_range),
                "rear_tire_stiffness_scale_range": _range_text(tire_range),
                "recovery_window_s": float(RECOVERY_BUCKETS[recovery_bucket]),
                "recovery_window_bucket": recovery_bucket,
                "finish_on_pass": bool(family["finish_on_pass"]),
                "obstacle_relative_velocity_mode": "zero",
                "wheel_observation_mode": "none",
                "include_privileged_params": False,
                "history_length": 1,
                "actor_contract_id": ACTOR_CONTRACT_ID,
                "diagnostic_only_no_ranking_claim": True,
                "ranking_admissible": False,
                "paper_level_claim_made": False,
                "level3_self_id_claim_made": False,
                "env_config_supported": True,
                "execution_blocked_by_unsupported_capability": False,
                "contract_violation_count": len(violation_messages),
                "env_config": env_config,
            }
            specs.append(spec)
            for message in violation_messages:
                contract_violations.append(
                    {
                        "scenario_spec_id": scenario_spec_id,
                        "role_family": role,
                        "violation": message,
                    }
                )
    for capability, reason in UNSUPPORTED_FUTURE_FAULTS:
        unsupported_rows.append(
            {
                "scenario_spec_id": "future_capability",
                "capability": capability,
                "support_status": "unsupported_current_single_track_model",
                "requested_value": "",
                "silently_approximated": False,
                "blocks_execution": False,
                "recommended_next_route": "defer to higher-fidelity simulator or explicit model extension",
                "reason": reason,
            }
        )
    return specs, contract_violations, unsupported_rows


def _missing_required_field_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    missing: list[dict[str, Any]] = []
    for row in rows:
        spec_id = str(row.get("scenario_spec_id", ""))
        for field in REQUIRED_METADATA_FIELDS:
            value = row.get(field)
            if value is None or value == "" or (field == "env_config" and not value):
                missing.append({"scenario_spec_id": spec_id, "missing_field": field})
    return missing


def _duplicate_key_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(str(row.get("scenario_spec_id", "")) for row in rows)
    return [
        {"scenario_spec_id": spec_id, "duplicate_count": int(count)}
        for spec_id, count in sorted(counts.items())
        if spec_id and count > 1
    ]


def _counts_by_key(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _scenario_csv_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {key: row.get(key, "") for key in REQUIRED_METADATA_FIELDS if key != "env_config"} | {
        "env_config_supported": bool(row.get("env_config_supported", False)),
        "execution_blocked_by_unsupported_capability": bool(
            row.get("execution_blocked_by_unsupported_capability", False)
        ),
        "contract_violation_count": int(row.get("contract_violation_count", 0)),
    }


def materialized_config_matrix_rows(specs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in specs:
        rows.append(
            {
                "config_id": f"{row['scenario_spec_id']}::env_v0",
                "scenario_spec_id": str(row["scenario_spec_id"]),
                "scenario_family_id": str(row["scenario_family_id"]),
                "role_family": str(row["role_family"]),
                "same_scene_group_id": str(row["same_scene_group_id"]),
                "obstacle_longitudinal_timing_bucket": str(row["obstacle_longitudinal_timing_bucket"]),
                "obstacle_lateral_offset_bucket": str(row["obstacle_lateral_offset_bucket"]),
                "hidden_dynamics_bucket": str(row["hidden_dynamics_bucket"]),
                "env_config_supported": bool(row["env_config_supported"]),
                "execution_admissible_after_materialization": False,
                "environment_reset_scheduled": False,
                "environment_rollout_scheduled": False,
                "training_scheduled": False,
                "ranking_admissible": False,
            }
        )
    return rows


def metadata_schema_rows() -> list[dict[str, Any]]:
    actor_forbidden = {
        "role_family",
        "role_semantics",
        "sampled_obstacle_label",
        "allowed_labels_metadata_only",
        "same_scene_group_id",
        "hidden_dynamics_bucket",
        "obstacle_longitudinal_timing_bucket",
        "obstacle_lateral_offset_bucket",
        "friction_bucket",
        "mu_range",
        "brake_scale_bucket",
        "brake_scale_range",
        "actuator_lag_bucket",
        "vehicle_mass_or_inertia_bucket",
        "tire_stiffness_bucket",
    }
    return [
        {
            "field": field,
            "required": True,
            "allowed_in_actor_input": False,
            "metadata_only": field in actor_forbidden,
        }
        for field in REQUIRED_METADATA_FIELDS
    ]


def role_family_support_target_rows() -> list[dict[str, Any]]:
    return [
        {
            "role_family": str(family["role_family"]),
            "scenario_family_id": str(family["scenario_family_id"]),
            "target_specs": TARGET_SPECS_PER_ROLE,
            "sampled_obstacle_label": str(family["sampled_obstacle_label"]),
            "allowed_labels_metadata_only": ";".join(str(label) for label in family["allowed_labels"]),
            "min_future_public_episodes_before_training_claim": 64,
            "min_future_profile_seed_groups_before_profile_claim": 3,
        }
        for family in ROLE_FAMILIES
    ]


def claim_boundary_rows(unsupported_execution_blocker_count: int) -> list[dict[str, Any]]:
    execution_admissible = unsupported_execution_blocker_count == 0
    return [
        {
            "claim": "scenario_task_family_config_pack_materialized",
            "admissible": True,
            "reason": "materializer writes no-reset scenario specs, metadata schema, and config matrix",
        },
        {
            "claim": "execution_admissible_without_instrumentation",
            "admissible": execution_admissible,
            "reason": (
                "no materialized execution blockers remain"
                if execution_admissible
                else "blocked while emergency obstacle lateral offsets are unsupported"
            ),
        },
        {
            "claim": "reset_or_rollout_result",
            "admissible": False,
            "reason": "materialization does not reset or roll out the environment",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "materialization is infrastructure, not measured comparison",
        },
        {
            "claim": "paper_level_evidence",
            "admissible": False,
            "reason": "No measured current-sim benchmark result is produced",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "No history-necessity intervention is run",
        },
    ]


def run_config_materialization(
    *,
    config_output: Path | str = DEFAULT_CONFIG_OUTPUT,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    config_path = Path(config_output)
    specs, contract_violations, unsupported_rows = materialize_scenario_specs()
    missing_rows = _missing_required_field_rows(specs)
    duplicate_rows = _duplicate_key_rows(specs)
    matrix_rows = materialized_config_matrix_rows(specs)
    unsupported_execution_blockers = [
        row for row in unsupported_rows if str(row.get("capability")) == "emergency_obstacle_lateral_offset"
    ]
    labels_enter_actor_input_count = sum(bool(row["labels_enter_actor_input"]) for row in specs)
    ranking_admissible_count = sum(bool(row["ranking_admissible"]) for row in specs)
    guardrail_flags = {
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "winner_selected": False,
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    role_counts = _counts_by_key(specs, "role_family")
    timing_counts = _counts_by_key(specs, "obstacle_longitudinal_timing_bucket")
    lateral_counts = _counts_by_key(specs, "obstacle_lateral_offset_bucket")
    hidden_counts = _counts_by_key(specs, "hidden_dynamics_bucket")
    passes = (
        len(role_counts) == TARGET_ROLE_FAMILY_COUNT
        and len(specs) >= TARGET_SCENARIO_SPEC_COUNT
        and min(role_counts.values()) >= TARGET_SPECS_PER_ROLE
        and not missing_rows
        and not duplicate_rows
        and not contract_violations
        and labels_enter_actor_input_count == 0
        and ranking_admissible_count == 0
        and guardrail_violation_count == 0
    )
    generated_at = utc_timestamp()
    artifacts = {
        "config_output": str(config_path),
        "summary": str(output / "summary.json"),
        "scenario_family_specs_json": str(output / "scenario_family_specs.json"),
        "scenario_family_specs_csv": str(output / "scenario_family_specs.csv"),
        "materialized_config_matrix": str(output / "materialized_config_matrix.csv"),
        "metadata_schema": str(output / "metadata_schema.csv"),
        "role_family_support_targets": str(output / "role_family_support_targets.csv"),
        "unsupported_capability_rows": str(output / "unsupported_capability_rows.csv"),
        "contract_violations": str(output / "contract_violations.csv"),
        "missing_required_fields": str(output / "missing_required_fields.csv"),
        "duplicate_scenario_spec_ids": str(output / "duplicate_scenario_spec_ids.csv"),
        "claim_boundary": str(output / "claim_boundary.csv"),
    }
    config_payload = {
        "config_name": "paper_route_current_sim_scenario_task_family_v0",
        "generated_at_utc": generated_at,
        "actor_contract_id": ACTOR_CONTRACT_ID,
        "claim_scope": "no-reset scenario task-family materialization",
        "scenario_specs": specs,
        "required_metadata_fields": list(REQUIRED_METADATA_FIELDS),
        "unsupported_capabilities": unsupported_rows,
        "next_blocker": next_blocker,
    }
    summary = {
        "result_class": (
            "current_sim_scenario_task_family_config_materialization_pass"
            if passes
            else "current_sim_scenario_task_family_config_materialization_fail"
        ),
        "generated_at_utc": generated_at,
        "output_dir": str(output),
        "config_output": str(config_path),
        "scenario_family_count": len(role_counts),
        "target_scenario_family_count": TARGET_ROLE_FAMILY_COUNT,
        "scenario_spec_count": len(specs),
        "target_scenario_spec_count": TARGET_SCENARIO_SPEC_COUNT,
        "role_family_counts": role_counts,
        "min_specs_per_role": min(role_counts.values()) if role_counts else 0,
        "obstacle_timing_bucket_counts": timing_counts,
        "obstacle_lateral_offset_bucket_counts": lateral_counts,
        "hidden_dynamics_bucket_counts": hidden_counts,
        "metadata_missing_required_field_count": len(missing_rows),
        "duplicate_scenario_spec_id_count": len(duplicate_rows),
        "labels_enter_actor_input_count": labels_enter_actor_input_count,
        "actor_contract_violation_count": len(contract_violations),
        "ranking_admissible_count": ranking_admissible_count,
        "unsupported_capability_count": len(unsupported_rows),
        "unsupported_execution_blocker_count": len(unsupported_execution_blockers),
        "silent_unsupported_approximation_count": sum(bool(row["silently_approximated"]) for row in unsupported_rows),
        "execution_admissible_without_instrumentation": len(unsupported_execution_blockers) == 0,
        "primary_route": (
            "scenario_task_family_result_audit_route_to_instrumentation_repair"
            if unsupported_execution_blockers
            else "scenario_task_family_result_audit_route_to_reset_validation_design"
        ),
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "passes_public_materialization_gates": bool(passes),
        "artifacts": artifacts,
        "next_blocker": next_blocker,
    }
    write_json(config_path, config_payload)
    write_json(output / "scenario_family_specs.json", {"generated_at_utc": generated_at, "scenario_specs": specs})
    write_csv_rows(output / "scenario_family_specs.csv", [_scenario_csv_row(row) for row in specs])
    write_csv_rows(output / "materialized_config_matrix.csv", matrix_rows)
    write_csv_rows(output / "metadata_schema.csv", metadata_schema_rows())
    write_csv_rows(output / "role_family_support_targets.csv", role_family_support_target_rows())
    write_csv_rows(output / "unsupported_capability_rows.csv", unsupported_rows)
    write_csv_rows(
        output / "contract_violations.csv",
        contract_violations,
        fieldnames=["scenario_spec_id", "role_family", "violation"],
    )
    write_csv_rows(
        output / "missing_required_fields.csv",
        missing_rows,
        fieldnames=["scenario_spec_id", "missing_field"],
    )
    write_csv_rows(
        output / "duplicate_scenario_spec_ids.csv",
        duplicate_rows,
        fieldnames=["scenario_spec_id", "duplicate_count"],
    )
    write_csv_rows(output / "claim_boundary.csv", claim_boundary_rows(len(unsupported_execution_blockers)))
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize no-reset current-sim scenario task-family configs.")
    parser.add_argument("--config-output", type=Path, default=DEFAULT_CONFIG_OUTPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", type=str, default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()

    summary = run_config_materialization(
        config_output=args.config_output,
        output_dir=args.output_dir,
        next_blocker=args.next_blocker,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"scenario_family_count={summary['scenario_family_count']}")
    print(f"scenario_spec_count={summary['scenario_spec_count']}")
    print(f"unsupported_execution_blocker_count={summary['unsupported_execution_blocker_count']}")
    print(f"passes_public_materialization_gates={summary['passes_public_materialization_gates']}")


if __name__ == "__main__":
    main()
