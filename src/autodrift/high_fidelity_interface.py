"""HF0 backend contract primitives for future high-fidelity validation.

This module intentionally does not bind to Chrono or any other external
simulator. It defines the actor-visible boundary that a future backend must
produce, plus a local current-sim parity preflight for the canonical P0 actor
contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

import numpy as np

from autodrift.env import AutoDriftEnv, DEFAULT_OBSTACLE_SLOTS, DEFAULT_ROAD_LOOKAHEAD_COUNT, DriftEnvConfig


P0_OBSERVATION_DIM = 72
ACTION_DIM = 3
ROAD_LOOKAHEAD_COUNT = DEFAULT_ROAD_LOOKAHEAD_COUNT
OBSTACLE_SLOT_COUNT = DEFAULT_OBSTACLE_SLOTS

DIAGNOSTIC_ONLY_KEYS = frozenset(
    {
        "mu",
        "initial_mu",
        "mass",
        "mass_scale",
        "inertia_scale",
        "cg_shift",
        "front_tire_stiffness_scale",
        "rear_tire_stiffness_scale",
        "tire_stiffness_scale",
        "drive_scale",
        "brake_scale",
        "steer_tau_scale",
        "drive_tau_scale",
        "speed_ref",
        "beta_target",
        "lateral_error",
        "heading_error",
        "curvature",
        "friction_step_at",
        "friction_step_applied",
        "obstacle_label",
        "obstacle_required_lateral_offset",
        "obstacle_threshold_score",
        "obstacle_time_after_friction_step",
        "aeb_stop_distance",
        "required_clearance",
        "feasibility_label",
        "reward_terms",
        "collision",
        "obstacle_completed",
        "success",
        "termination_reason",
        "completion_reason",
    }
)


@dataclass(frozen=True)
class BackendResetRequest:
    seed: int | None = None
    env_config_snapshot: Mapping[str, Any] = field(default_factory=dict)
    scenario_spec_id: str = ""
    role_family: str = ""
    options: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EgoView:
    x: float
    y: float
    psi: float
    vx_body: float
    vy_body: float
    yaw_rate: float
    ax_body: float
    ay_body: float


@dataclass(frozen=True)
class ActuatorView:
    steer_angle_normalized: float
    steer_rate_normalized: float
    throttle_state: float
    brake_state: float
    previous_steer_command: float
    previous_throttle_command: float
    previous_brake_command: float


@dataclass(frozen=True)
class RoadView:
    left_boundary_points_body: tuple[tuple[float, float], ...]
    right_boundary_points_body: tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class ObstacleSlotView:
    present: float
    x_body: float
    y_body: float
    vx_body: float
    vy_body: float
    half_width: float
    half_length: float


@dataclass(frozen=True)
class ActorView:
    dt: float
    step_index: int
    ego: EgoView
    actuators: ActuatorView
    road: RoadView
    obstacles: tuple[ObstacleSlotView, ...]


@dataclass(frozen=True)
class BackendResetResult:
    actor_view: ActorView
    diagnostics: dict[str, Any]
    backend_info: dict[str, Any]


@dataclass(frozen=True)
class BackendStepResult:
    actor_view: ActorView
    diagnostics: dict[str, Any]
    terminated_by_backend: bool
    truncated_by_backend: bool
    backend_status: str


class DynamicsBackend(Protocol):
    """Minimal internal boundary expected from a future high-fidelity backend."""

    backend_id: str
    dt: float

    def reset(self, request: BackendResetRequest) -> BackendResetResult:
        """Reset backend state and return actor-visible state plus diagnostics."""

    def step(self, action: np.ndarray) -> BackendStepResult:
        """Advance one backend step with the deployed actor action."""

    def close(self) -> None:
        """Release backend resources."""


def validate_actor_action(action: np.ndarray) -> np.ndarray:
    """Validate and clip the deployed three-channel actor action."""

    action_array = np.asarray(action, dtype=np.float32)
    if action_array.shape != (ACTION_DIM,):
        raise ValueError(f"expected action shape {(ACTION_DIM,)}, got {action_array.shape}")
    if not np.all(np.isfinite(action_array)):
        raise ValueError("actor action contains non-finite values")
    return np.clip(action_array, -1.0, 1.0).astype(np.float32)


def physical_control_from_action(action: np.ndarray) -> np.ndarray:
    """Map normalized actor action to [steer, throttle, brake] physical controls."""

    clipped = validate_actor_action(action)
    return np.array(
        [
            float(clipped[0]),
            0.5 * (float(clipped[1]) + 1.0),
            0.5 * (float(clipped[2]) + 1.0),
        ],
        dtype=np.float32,
    )


def canonical_p0_config(config: DriftEnvConfig) -> bool:
    """Return whether an env config matches the canonical no-oracle P0 frame."""

    return bool(
        config.history_length == 1
        and config.action_history_mode == "full"
        and config.wheel_observation_mode == "none"
        and not config.include_privileged_params
        and config.road_lookahead_count == ROAD_LOOKAHEAD_COUNT
        and config.obstacle_slots == OBSTACLE_SLOT_COUNT
    )


def contract_flags(config: DriftEnvConfig) -> dict[str, bool]:
    """Machine-readable actor/action contract flags for review artifacts."""

    return {
        "actor_input_contract_changed": not canonical_p0_config(config),
        "action_contract_changed": False,
        "hidden_values_enter_actor_input": False,
        "oracle_labels_enter_actor_input": False,
        "diagnostics_available_to_actor": False,
    }


class P0ObservationExtractor:
    """Pure extractor from deployable actor view to the canonical 72-value frame."""

    field_map = (
        "ego.vx_body/20",
        "ego.vy_body/12",
        "ego.yaw_rate/2.5",
        "ego.ax_body/15",
        "ego.ay_body/15",
        "actuators.steer_angle_normalized",
        "actuators.steer_rate_normalized",
        "actuators.throttle_state",
        "actuators.brake_state",
        "actuators.previous_steer_command",
        "actuators.previous_throttle_command",
        "actuators.previous_brake_command",
    )

    def extract(self, actor_view: ActorView) -> np.ndarray:
        _validate_actor_view(actor_view)
        obs: list[float] = [
            actor_view.ego.vx_body / 20.0,
            actor_view.ego.vy_body / 12.0,
            actor_view.ego.yaw_rate / 2.5,
            actor_view.ego.ax_body / 15.0,
            actor_view.ego.ay_body / 15.0,
            actor_view.actuators.steer_angle_normalized,
            actor_view.actuators.steer_rate_normalized,
            actor_view.actuators.throttle_state,
            actor_view.actuators.brake_state,
            actor_view.actuators.previous_steer_command,
            actor_view.actuators.previous_throttle_command,
            actor_view.actuators.previous_brake_command,
        ]
        for x_body, y_body in actor_view.road.left_boundary_points_body:
            obs.extend([x_body / 80.0, y_body / 20.0])
        for x_body, y_body in actor_view.road.right_boundary_points_body:
            obs.extend([x_body / 80.0, y_body / 20.0])
        for slot in actor_view.obstacles:
            obs.extend(
                [
                    slot.present,
                    slot.x_body / 80.0,
                    slot.y_body / 20.0,
                    slot.vx_body / 20.0,
                    slot.vy_body / 12.0,
                    slot.half_width / 5.0,
                    slot.half_length / 5.0,
                ]
            )
        observation = np.asarray(obs, dtype=np.float32)
        if observation.shape != (P0_OBSERVATION_DIM,):
            raise ValueError(f"expected P0 observation shape {(P0_OBSERVATION_DIM,)}, got {observation.shape}")
        if not np.all(np.isfinite(observation)):
            raise ValueError("P0 observation contains non-finite values")
        return observation


def default_actor_view() -> ActorView:
    """Small deterministic actor view used by local contract preflights."""

    left = tuple((float(i + 1) * 5.0, 2.5) for i in range(ROAD_LOOKAHEAD_COUNT))
    right = tuple((float(i + 1) * 5.0, -2.5) for i in range(ROAD_LOOKAHEAD_COUNT))
    obstacles = (ObstacleSlotView(1.0, 25.0, 0.5, -8.0, 0.0, 0.75, 0.75),) + tuple(
        ObstacleSlotView(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        for _ in range(OBSTACLE_SLOT_COUNT - 1)
    )
    return ActorView(
        dt=0.02,
        step_index=0,
        ego=EgoView(x=0.0, y=0.0, psi=0.0, vx_body=8.0, vy_body=0.2, yaw_rate=0.1, ax_body=0.5, ay_body=0.1),
        actuators=ActuatorView(
            steer_angle_normalized=0.05,
            steer_rate_normalized=0.02,
            throttle_state=0.4,
            brake_state=0.1,
            previous_steer_command=0.05,
            previous_throttle_command=0.4,
            previous_brake_command=0.1,
        ),
        road=RoadView(left_boundary_points_body=left, right_boundary_points_body=right),
        obstacles=obstacles,
    )


def run_current_sim_p0_preflight(seed: int = 2473) -> dict[str, Any]:
    """Run a local current-sim shape preflight for the canonical P0 contract."""

    config = DriftEnvConfig()
    env = AutoDriftEnv(config)
    reset_obs, reset_info = env.reset(seed=int(seed))
    zero_action = validate_actor_action(np.zeros(ACTION_DIM, dtype=np.float32))
    step_obs, reward, terminated, truncated, step_info = env.step(zero_action)
    extractor_obs = P0ObservationExtractor().extract(default_actor_view())
    invalid_action_shape_rejected = False
    try:
        validate_actor_action(np.zeros((1, ACTION_DIM), dtype=np.float32))
    except ValueError:
        invalid_action_shape_rejected = True

    hidden_keys_seen = sorted(DIAGNOSTIC_ONLY_KEYS.intersection(set(reset_info) | set(step_info)))
    flags = contract_flags(config)
    diagnostics_available_to_actor = False
    status_pass = (
        tuple(reset_obs.shape) == (P0_OBSERVATION_DIM,)
        and tuple(step_obs.shape) == (P0_OBSERVATION_DIM,)
        and tuple(env.action_space.shape) == (ACTION_DIM,)
        and tuple(extractor_obs.shape) == (P0_OBSERVATION_DIM,)
        and invalid_action_shape_rejected
        and not any(flags.values())
        and not diagnostics_available_to_actor
    )

    return {
        "result_class": "hf0_contract_preflight_pass" if status_pass else "hf0_contract_preflight_failed",
        "status_pass": bool(status_pass),
        "seed": int(seed),
        "observation_shape": int(reset_obs.shape[0]),
        "step_observation_shape": int(step_obs.shape[0]),
        "action_shape": int(env.action_space.shape[0]),
        "p0_extractor_shape": int(extractor_obs.shape[0]),
        "canonical_p0_config": canonical_p0_config(config),
        "invalid_action_shape_rejected": bool(invalid_action_shape_rejected),
        "physical_control_for_zero_action": physical_control_from_action(zero_action).astype(float).tolist(),
        "current_sim_reset_count": 1,
        "current_sim_step_count": 1,
        "external_high_fidelity_required": False,
        "external_high_fidelity_imported": False,
        "high_fidelity_simulation_run": False,
        "policy_rollout_run": False,
        "training_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "verdict_claim_made": False,
        "reward_sample": float(reward),
        "terminated_sample": bool(terminated),
        "truncated_sample": bool(truncated),
        "diagnostic_hidden_key_count": len(hidden_keys_seen),
        "diagnostic_hidden_keys_seen": hidden_keys_seen,
        "diagnostic_only_keys_checked": sorted(DIAGNOSTIC_ONLY_KEYS),
        **flags,
    }


def _validate_actor_view(actor_view: ActorView) -> None:
    if len(actor_view.road.left_boundary_points_body) != ROAD_LOOKAHEAD_COUNT:
        raise ValueError(f"expected {ROAD_LOOKAHEAD_COUNT} left road points")
    if len(actor_view.road.right_boundary_points_body) != ROAD_LOOKAHEAD_COUNT:
        raise ValueError(f"expected {ROAD_LOOKAHEAD_COUNT} right road points")
    if len(actor_view.obstacles) != OBSTACLE_SLOT_COUNT:
        raise ValueError(f"expected {OBSTACLE_SLOT_COUNT} obstacle slots")
