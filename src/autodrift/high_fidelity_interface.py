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


def actor_view_from_p0_observation(
    observation: np.ndarray,
    *,
    dt: float,
    step_index: int,
    pose: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> ActorView:
    """Reconstruct an actor-visible view from a canonical current-sim P0 frame."""

    obs = np.asarray(observation, dtype=np.float32)
    if obs.shape != (P0_OBSERVATION_DIM,):
        raise ValueError(f"expected P0 observation shape {(P0_OBSERVATION_DIM,)}, got {obs.shape}")
    if not np.all(np.isfinite(obs)):
        raise ValueError("P0 observation contains non-finite values")

    road_start = 12
    right_start = road_start + ROAD_LOOKAHEAD_COUNT * 2
    obstacle_start = right_start + ROAD_LOOKAHEAD_COUNT * 2
    left = tuple(
        (float(obs[road_start + 2 * idx] * 80.0), float(obs[road_start + 2 * idx + 1] * 20.0))
        for idx in range(ROAD_LOOKAHEAD_COUNT)
    )
    right = tuple(
        (float(obs[right_start + 2 * idx] * 80.0), float(obs[right_start + 2 * idx + 1] * 20.0))
        for idx in range(ROAD_LOOKAHEAD_COUNT)
    )
    obstacles = []
    for slot_idx in range(OBSTACLE_SLOT_COUNT):
        base = obstacle_start + slot_idx * 7
        obstacles.append(
            ObstacleSlotView(
                present=float(obs[base]),
                x_body=float(obs[base + 1] * 80.0),
                y_body=float(obs[base + 2] * 20.0),
                vx_body=float(obs[base + 3] * 20.0),
                vy_body=float(obs[base + 4] * 12.0),
                half_width=float(obs[base + 5] * 5.0),
                half_length=float(obs[base + 6] * 5.0),
            )
        )

    return ActorView(
        dt=float(dt),
        step_index=int(step_index),
        ego=EgoView(
            x=float(pose[0]),
            y=float(pose[1]),
            psi=float(pose[2]),
            vx_body=float(obs[0] * 20.0),
            vy_body=float(obs[1] * 12.0),
            yaw_rate=float(obs[2] * 2.5),
            ax_body=float(obs[3] * 15.0),
            ay_body=float(obs[4] * 15.0),
        ),
        actuators=ActuatorView(
            steer_angle_normalized=float(obs[5]),
            steer_rate_normalized=float(obs[6]),
            throttle_state=float(obs[7]),
            brake_state=float(obs[8]),
            previous_steer_command=float(obs[9]),
            previous_throttle_command=float(obs[10]),
            previous_brake_command=float(obs[11]),
        ),
        road=RoadView(left_boundary_points_body=left, right_boundary_points_body=right),
        obstacles=tuple(obstacles),
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


class CurrentSimDynamicsBackend:
    """HF0 backend adapter over AutoDriftEnv for bounded local smoke tests."""

    backend_id = "current_sim_autodrift_hf0"

    def __init__(self, config: DriftEnvConfig | None = None):
        self.config = config or DriftEnvConfig()
        if not canonical_p0_config(self.config):
            raise ValueError("CurrentSimDynamicsBackend requires the canonical P0 config")
        self.env = AutoDriftEnv(self.config)
        self.dt = float(self.config.dt)
        self._step_index = 0
        self._extractor = P0ObservationExtractor()

    def reset(self, request: BackendResetRequest) -> BackendResetResult:
        obs, info = self.env.reset(seed=request.seed, options=dict(request.options) or None)
        self._step_index = 0
        actor_view = self._actor_view_from_observation(obs)
        backend_info = self._backend_info(obs, actor_view)
        backend_info.update(
            {
                "scenario_spec_id": request.scenario_spec_id,
                "role_family": request.role_family,
                "reset_seed": request.seed,
            }
        )
        return BackendResetResult(actor_view=actor_view, diagnostics=dict(info), backend_info=backend_info)

    def step(self, action: np.ndarray) -> BackendStepResult:
        clipped_action = validate_actor_action(action)
        obs, reward, terminated, truncated, info = self.env.step(clipped_action)
        self._step_index += 1
        actor_view = self._actor_view_from_observation(obs)
        diagnostics = dict(info)
        diagnostics["reward"] = float(reward)
        diagnostics["backend_info"] = self._backend_info(obs, actor_view)
        return BackendStepResult(
            actor_view=actor_view,
            diagnostics=diagnostics,
            terminated_by_backend=bool(terminated),
            truncated_by_backend=bool(truncated),
            backend_status=str(info.get("termination_reason") or "running"),
        )

    def close(self) -> None:
        close = getattr(self.env, "close", None)
        if callable(close):
            close()

    def _actor_view_from_observation(self, observation: np.ndarray) -> ActorView:
        state = self.env.state
        return actor_view_from_p0_observation(
            observation,
            dt=self.dt,
            step_index=self._step_index,
            pose=(float(state.x), float(state.y), float(state.psi)),
        )

    def _backend_info(self, observation: np.ndarray, actor_view: ActorView) -> dict[str, Any]:
        extracted = self._extractor.extract(actor_view)
        return {
            "backend_id": self.backend_id,
            "observation_shape": int(np.asarray(observation).shape[0]),
            "actor_observation_shape": int(extracted.shape[0]),
            "extractor_parity_max_abs_error": float(np.max(np.abs(extracted - np.asarray(observation)))),
        }


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


def run_current_sim_adapter_smoke(
    seeds: tuple[int, ...] = (2474, 2475, 2476),
    actions: tuple[tuple[float, float, float], ...] = (
        (0.0, 0.0, 0.0),
        (0.25, -0.25, -0.75),
    ),
) -> dict[str, Any]:
    """Exercise the HF0 backend boundary with current-sim over a bounded seed set."""

    config = DriftEnvConfig()
    flags = contract_flags(config)
    extractor = P0ObservationExtractor()
    seed_reports: list[dict[str, Any]] = []
    hidden_keys_seen: set[str] = set()
    max_parity_abs_error = 0.0
    reset_count = 0
    step_count = 0
    status_pass = True

    for seed in seeds:
        backend = CurrentSimDynamicsBackend(config)
        try:
            reset_result = backend.reset(
                BackendResetRequest(
                    seed=int(seed),
                    scenario_spec_id=f"m2474_seed_{int(seed)}",
                    role_family="current_sim_adapter_smoke",
                )
            )
            reset_count += 1
            reset_observation = extractor.extract(reset_result.actor_view)
            reset_backend_error = float(reset_result.backend_info["extractor_parity_max_abs_error"])
            max_parity_abs_error = max(max_parity_abs_error, reset_backend_error)
            hidden_keys_seen.update(DIAGNOSTIC_ONLY_KEYS.intersection(reset_result.diagnostics))

            step_shapes: list[int] = []
            step_statuses: list[str] = []
            terminated_or_truncated = False
            for action in actions:
                step_result = backend.step(np.asarray(action, dtype=np.float32))
                step_count += 1
                step_observation = extractor.extract(step_result.actor_view)
                step_shapes.append(int(step_observation.shape[0]))
                step_statuses.append(step_result.backend_status)
                backend_info = step_result.diagnostics.get("backend_info", {})
                max_parity_abs_error = max(
                    max_parity_abs_error,
                    float(backend_info.get("extractor_parity_max_abs_error", float("inf"))),
                )
                hidden_keys_seen.update(DIAGNOSTIC_ONLY_KEYS.intersection(step_result.diagnostics))
                terminated_or_truncated = terminated_or_truncated or bool(
                    step_result.terminated_by_backend or step_result.truncated_by_backend
                )

            seed_reports.append(
                {
                    "seed": int(seed),
                    "reset_observation_shape": int(reset_observation.shape[0]),
                    "step_observation_shapes": step_shapes,
                    "step_statuses": step_statuses,
                    "terminated_or_truncated": bool(terminated_or_truncated),
                }
            )
        finally:
            backend.close()

    if any(report["reset_observation_shape"] != P0_OBSERVATION_DIM for report in seed_reports):
        status_pass = False
    step_shapes_ok = all(
        shape == P0_OBSERVATION_DIM
        for report in seed_reports
        for shape in report["step_observation_shapes"]
    )
    if not step_shapes_ok:
        status_pass = False
    if max_parity_abs_error > 1e-6:
        status_pass = False
    if any(flags.values()):
        status_pass = False

    return {
        "result_class": "current_sim_adapter_smoke_pass" if status_pass else "current_sim_adapter_smoke_failed",
        "status_pass": bool(status_pass),
        "backend_id": CurrentSimDynamicsBackend.backend_id,
        "seed_count": len(seeds),
        "seeds": [int(seed) for seed in seeds],
        "actions_per_seed": len(actions),
        "canned_action_count": len(actions),
        "current_sim_reset_count": reset_count,
        "current_sim_step_count": step_count,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "p0_extractor_shape": P0_OBSERVATION_DIM,
        "canonical_p0_config": canonical_p0_config(config),
        "max_extractor_parity_abs_error": float(max_parity_abs_error),
        "seed_reports": seed_reports,
        "diagnostic_hidden_key_count": len(hidden_keys_seen),
        "diagnostic_hidden_keys_seen": sorted(hidden_keys_seen),
        "diagnostic_only_keys_checked": sorted(DIAGNOSTIC_ONLY_KEYS),
        "actor_view_source": "current_sim_p0_observation_denormalization",
        "external_high_fidelity_required": False,
        "external_high_fidelity_imported": False,
        "high_fidelity_simulation_run": False,
        "measured_validation_run": False,
        "policy_rollout_run": False,
        "training_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "verdict_claim_made": False,
        **flags,
    }


def _validate_actor_view(actor_view: ActorView) -> None:
    if len(actor_view.road.left_boundary_points_body) != ROAD_LOOKAHEAD_COUNT:
        raise ValueError(f"expected {ROAD_LOOKAHEAD_COUNT} left road points")
    if len(actor_view.road.right_boundary_points_body) != ROAD_LOOKAHEAD_COUNT:
        raise ValueError(f"expected {ROAD_LOOKAHEAD_COUNT} right road points")
    if len(actor_view.obstacles) != OBSTACLE_SLOT_COUNT:
        raise ValueError(f"expected {OBSTACLE_SLOT_COUNT} obstacle slots")
