"""Gymnasium environment for friction-adaptive drift tracking."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

import gymnasium as gym
from gymnasium import spaces
import numpy as np

from autodrift.dynamics import (
    RandomizationConfig,
    SingleTrackDriftModel,
    TireForces,
    VehicleParams,
    VehicleState,
    sample_vehicle_params,
)
from autodrift.math_utils import wrap_pi
from autodrift.scenarios import ObstacleScenario, ObstacleScenarioConfig, classify_obstacle_scenario
from autodrift.tasks import PathFrame, make_track


EGO_OBS_DIM = 9
LAST_ACTION_OBS_DIM = 3
FRONT_REAR_WHEEL_OBS_DIM = 13
ROAD_POINT_DIM = 2
OBSTACLE_SLOT_DIM = 7
DEFAULT_ROAD_LOOKAHEAD_COUNT = 8
DEFAULT_OBSTACLE_SLOTS = 4
BASIC_PRIVILEGED_OBS_DIM = 4
FULL_DYNAMICS_PRIVILEGED_OBS_DIM = 10
PRIVILEGED_OBSERVATION_MODES = ("basic", "full_dynamics")
OBSTACLE_RELATIVE_VELOCITY_MODES = ("ego", "zero")
OBSTACLE_MOTION_MODES = ("static", "constant_velocity_crosser")
RAW_FRONT_REAR_WHEEL_OBSERVATION_MODES = (
    "front_rear_raw",
    "front_rear_omega",
    "front_rear_omega_ground",
    "front_rear_omega_ground_error",
)
FRONT_REAR_WHEEL_OBSERVATION_MODES = ("front_rear", *RAW_FRONT_REAR_WHEEL_OBSERVATION_MODES)
WHEEL_OBSERVATION_MODES = ("none", *FRONT_REAR_WHEEL_OBSERVATION_MODES)


@dataclass(frozen=True)
class FrictionStepConfig:
    enabled: bool = False
    step_range: tuple[int, int] = (250, 550)
    mu_range: tuple[float, float] = (0.25, 1.15)
    resample_speed_ref: bool = True


@dataclass(frozen=True)
class ObstacleTaskConfig:
    enabled: bool = False
    distance_range: tuple[float, float] = (16.0, 55.0)
    half_width_range: tuple[float, float] = (0.45, 1.15)
    lateral_offset_range: tuple[float, float] = (0.0, 0.0)
    ego_half_width: float = 0.90
    safety_margin: float = 0.30
    brake_mu_fraction: float = 0.90
    conventional_lateral_mu_fraction: float = 0.42
    drift_lateral_mu_fraction: float = 0.85
    collision_penalty: float = 20.0
    require_aeb_infeasible: bool = False
    max_sample_attempts: int = 100
    finish_on_pass: bool = False
    finish_pass_distance: float = 2.0
    pass_reward: float = 10.0
    allowed_labels: tuple[str, ...] = ("aeb_feasible", "aes_feasible", "drift_required", "unavoidable")
    stable_aes_beta_limit: float = 0.24
    stable_aes_sideslip_penalty: float = 0.0
    stable_aes_drift_bonus_scale: float = 1.0
    max_threshold_score: float | None = None
    min_time_after_friction_step: float = 0.0
    perception_reveal_step: int = 0
    perception_reveal_distance: float | None = None
    clearance_margin_reward_scale: float = 0.0
    clearance_margin_reward_clip: float = 0.25
    dense_clearance_margin_reward_scale: float = 0.0
    dense_clearance_margin_reward_clip: float = 0.25
    dense_clearance_margin_reward_window: float = 8.0
    motion_mode: str = "static"
    crosser_lateral_velocity_range: tuple[float, float] = (0.0, 0.0)

    def __post_init__(self) -> None:
        if self.lateral_offset_range[1] < self.lateral_offset_range[0]:
            raise ValueError("lateral_offset_range must be ordered")
        if self.motion_mode not in OBSTACLE_MOTION_MODES:
            raise ValueError("obstacle motion_mode must be one of: " + ", ".join(OBSTACLE_MOTION_MODES))
        if self.crosser_lateral_velocity_range[1] < self.crosser_lateral_velocity_range[0]:
            raise ValueError("crosser_lateral_velocity_range must be ordered")
        if self.clearance_margin_reward_clip <= 0.0:
            raise ValueError("clearance_margin_reward_clip must be positive")
        if self.dense_clearance_margin_reward_clip <= 0.0:
            raise ValueError("dense_clearance_margin_reward_clip must be positive")
        if self.dense_clearance_margin_reward_window <= 0.0:
            raise ValueError("dense_clearance_margin_reward_window must be positive")
        if self.perception_reveal_step < 0:
            raise ValueError("perception_reveal_step must be non-negative")
        if self.perception_reveal_distance is not None and self.perception_reveal_distance <= 0.0:
            raise ValueError("perception_reveal_distance must be positive when set")

    def scenario_config(self, speed: float, mu: float) -> ObstacleScenarioConfig:
        return ObstacleScenarioConfig(
            speed_range=(speed, speed),
            mu_range=(mu, mu),
            obstacle_distance_range=self.distance_range,
            obstacle_half_width_range=self.half_width_range,
            ego_half_width=self.ego_half_width,
            safety_margin=self.safety_margin,
            brake_mu_fraction=self.brake_mu_fraction,
            conventional_lateral_mu_fraction=self.conventional_lateral_mu_fraction,
            drift_lateral_mu_fraction=self.drift_lateral_mu_fraction,
        )


@dataclass(frozen=True)
class WarmupGateConfig:
    enabled: bool = False
    distance_range: tuple[float, float] = (12.0, 30.0)
    lateral_offset_range: tuple[float, float] = (-1.2, 1.2)
    half_width_range: tuple[float, float] = (0.35, 0.85)
    reveal_step: int = 0
    max_active_steps: int = 64
    finish_pass_distance: float = 2.0

    def __post_init__(self) -> None:
        if self.distance_range[0] <= 0.0 or self.distance_range[1] <= 0.0:
            raise ValueError("warmup_gate distance_range values must be positive")
        if self.distance_range[1] < self.distance_range[0]:
            raise ValueError("warmup_gate distance_range must be ordered")
        if self.half_width_range[0] <= 0.0 or self.half_width_range[1] <= 0.0:
            raise ValueError("warmup_gate half_width_range values must be positive")
        if self.half_width_range[1] < self.half_width_range[0]:
            raise ValueError("warmup_gate half_width_range must be ordered")
        if self.reveal_step < 0:
            raise ValueError("warmup_gate reveal_step must be non-negative")
        if self.max_active_steps <= 0:
            raise ValueError("warmup_gate max_active_steps must be positive")
        if self.finish_pass_distance < 0.0:
            raise ValueError("warmup_gate finish_pass_distance must be non-negative")


@dataclass(frozen=True)
class ObservationDegradationConfig:
    """Degraded-response TASK FAMILY parameters (ego channels 0-8 only).

    Consumed by ``autodrift.observation_degradation_wrapper.make_env_from_config``;
    ``AutoDriftEnv`` itself ignores this block, so entry points that build envs
    from a ``DriftEnvConfig`` must go through that factory for the degradation
    to apply. ``noise_seed_stream`` default must stay equal to
    ``observation_degradation_wrapper.DEFAULT_NOISE_SEED_STREAM``.

    Modes (semantics defined in ``observation_degradation_wrapper``):

    - ``delay_steps`` + ``noise_std``: original M3214 behavior (constant integer
      delay + i.i.d. Gaussian noise); when only these are set the wrapper runs
      the original code path bit-for-bit.
    - AR(1) correlated noise (``ar1_rho``, ``ar1_sigma``): per-channel process
      ``n_t = ar1_rho * n_{t-1} + ar1_sigma * eps_t`` with ``eps_t ~ N(0, I)``,
      zero-initialized at episode start. ``ar1_sigma`` is the INNOVATION std
      (scalar or length-9); stationary std = ``ar1_sigma / sqrt(1 - ar1_rho^2)``.
      With ``ar1_rho = 0`` the process is bit-identical to the iid ``noise_std``
      path (same per-frame RNG draw), so ``noise_std`` and ``ar1_sigma`` are
      mutually exclusive (loud ValueError instead of silently correlated sums).
    - Frame dropout (``dropout_prob``): each frame after the episode's first is
      dropped independently with this probability; dropped frames HOLD THE LAST
      DEGRADED VALUE on the ego channels. Deterministic per-episode substream
      ``[stream, seed_root, episode, 1]``.
    - Time-varying delay (``delay_profile``): "constant" = ``delay_steps``
      everywhere (original behavior); "episode_random" = one delay drawn
      uniformly from ``[delay_lo, delay_hi]`` per episode; "piecewise" = 2-3
      segments per episode with per-segment delays from ``[delay_lo, delay_hi]``
      (adjacent segments differ), segment cut points seed-derived. Substream
      ``[stream, seed_root, episode, 2]``. Non-constant profiles require
      ``delay_steps == 0`` (no competing delay specifications).
    """

    delay_steps: int = 0
    noise_std: float | tuple[float, ...] = 0.0
    noise_seed_stream: int = 20260610
    ar1_rho: float = 0.0
    ar1_sigma: float | tuple[float, ...] = 0.0
    dropout_prob: float = 0.0
    delay_profile: str = "constant"
    delay_lo: int = 0
    delay_hi: int = 0

    def __post_init__(self) -> None:
        if isinstance(self.delay_steps, bool) or not isinstance(self.delay_steps, int):
            raise ValueError("observation_degradation delay_steps must be an integer")
        if self.delay_steps < 0:
            raise ValueError("observation_degradation delay_steps must be non-negative")
        if isinstance(self.noise_seed_stream, bool) or not isinstance(self.noise_seed_stream, int):
            raise ValueError("observation_degradation noise_seed_stream must be an integer")
        if isinstance(self.noise_std, (list, tuple, np.ndarray)):
            values = tuple(float(item) for item in self.noise_std)
            if len(values) != EGO_OBS_DIM:
                raise ValueError(
                    "observation_degradation noise_std must be a scalar or a "
                    f"length-{EGO_OBS_DIM} per-channel sequence, got length {len(values)}"
                )
            object.__setattr__(self, "noise_std", values)
        elif isinstance(self.noise_std, (int, float)) and not isinstance(self.noise_std, bool):
            values = (float(self.noise_std),)
            object.__setattr__(self, "noise_std", float(self.noise_std))
        else:
            raise ValueError("observation_degradation noise_std must be a number or a sequence of numbers")
        if any((not math.isfinite(value)) or value < 0.0 for value in values):
            raise ValueError("observation_degradation noise_std values must be finite and non-negative")
        noise_values = values

        # -- AR(1) correlated noise -------------------------------------------
        if isinstance(self.ar1_rho, bool) or not isinstance(self.ar1_rho, (int, float)):
            raise ValueError("observation_degradation ar1_rho must be a number")
        object.__setattr__(self, "ar1_rho", float(self.ar1_rho))
        if not math.isfinite(self.ar1_rho) or self.ar1_rho < 0.0 or self.ar1_rho >= 1.0:
            raise ValueError("observation_degradation ar1_rho must satisfy 0 <= ar1_rho < 1")
        if isinstance(self.ar1_sigma, (list, tuple, np.ndarray)):
            ar1_values = tuple(float(item) for item in self.ar1_sigma)
            if len(ar1_values) != EGO_OBS_DIM:
                raise ValueError(
                    "observation_degradation ar1_sigma must be a scalar or a "
                    f"length-{EGO_OBS_DIM} per-channel sequence, got length {len(ar1_values)}"
                )
            object.__setattr__(self, "ar1_sigma", ar1_values)
        elif isinstance(self.ar1_sigma, (int, float)) and not isinstance(self.ar1_sigma, bool):
            ar1_values = (float(self.ar1_sigma),)
            object.__setattr__(self, "ar1_sigma", float(self.ar1_sigma))
        else:
            raise ValueError("observation_degradation ar1_sigma must be a number or a sequence of numbers")
        if any((not math.isfinite(value)) or value < 0.0 for value in ar1_values):
            raise ValueError("observation_degradation ar1_sigma values must be finite and non-negative")
        if self.ar1_rho > 0.0 and not any(value > 0.0 for value in ar1_values):
            raise ValueError("observation_degradation ar1_rho > 0 requires a positive ar1_sigma")
        if any(value > 0.0 for value in ar1_values) and any(value > 0.0 for value in noise_values):
            raise ValueError(
                "observation_degradation noise_std and ar1_sigma are mutually exclusive; "
                "AR(1) noise with ar1_rho=0 reproduces the iid noise_std path bit-for-bit"
            )

        # -- frame dropout ------------------------------------------------------
        if isinstance(self.dropout_prob, bool) or not isinstance(self.dropout_prob, (int, float)):
            raise ValueError("observation_degradation dropout_prob must be a number")
        object.__setattr__(self, "dropout_prob", float(self.dropout_prob))
        if not math.isfinite(self.dropout_prob) or self.dropout_prob < 0.0 or self.dropout_prob >= 1.0:
            raise ValueError("observation_degradation dropout_prob must satisfy 0 <= dropout_prob < 1")

        # -- time-varying delay profile -----------------------------------------
        if self.delay_profile not in ("constant", "episode_random", "piecewise"):
            raise ValueError(
                "observation_degradation delay_profile must be one of: "
                "constant, episode_random, piecewise"
            )
        for name in ("delay_lo", "delay_hi"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"observation_degradation {name} must be an integer")
            if value < 0:
                raise ValueError(f"observation_degradation {name} must be non-negative")
        if self.delay_profile == "constant":
            if self.delay_lo != 0 or self.delay_hi != 0:
                raise ValueError(
                    "observation_degradation delay_lo/delay_hi require delay_profile "
                    "'episode_random' or 'piecewise'"
                )
        else:
            if self.delay_steps != 0:
                raise ValueError(
                    "observation_degradation delay_steps must stay 0 when delay_profile is "
                    f"'{self.delay_profile}'; the delay comes from [delay_lo, delay_hi]"
                )
            if self.delay_hi < self.delay_lo:
                raise ValueError("observation_degradation delay_hi must be >= delay_lo")
            if self.delay_profile == "piecewise" and self.delay_hi <= self.delay_lo:
                raise ValueError(
                    "observation_degradation delay_profile 'piecewise' requires delay_hi > delay_lo"
                )
            if self.delay_profile == "episode_random" and self.delay_hi == 0:
                raise ValueError(
                    "observation_degradation delay_profile 'episode_random' requires delay_hi > 0"
                )


@dataclass(frozen=True)
class DriftEnvConfig:
    dt: float = 0.02
    max_steps: int = 800
    track_kind: str = "circle"
    track_radius: float = 18.0
    track_width: float = 5.0
    speed_range: tuple[float, float] = (5.0, 12.0)
    beta_target_range: tuple[float, float] = (0.32, 0.70)
    track_cost_scale: float = 2.4
    heading_cost_scale: float = 0.25
    road_margin_cost_scale: float = 0.0
    road_margin_warning_fraction: float = 0.70
    off_track_penalty: float = 0.0
    soft_offtrack_metric_enabled: bool = False
    soft_offtrack_tolerance_m: float = 0.0
    termination_penalty: float = 0.0
    friction_limited_speed: bool = True
    friction_speed_margin: float = 0.92
    history_length: int = 1
    action_history_mode: str = "full"
    include_privileged_params: bool = False
    privileged_observation_mode: str = "basic"
    obstacle_relative_velocity_mode: str = "ego"
    wheel_observation_mode: str = "none"
    road_lookahead_count: int = DEFAULT_ROAD_LOOKAHEAD_COUNT
    road_lookahead_spacing: float = 5.0
    obstacle_slots: int = DEFAULT_OBSTACLE_SLOTS
    friction_step: FrictionStepConfig = FrictionStepConfig()
    obstacle: ObstacleTaskConfig = ObstacleTaskConfig()
    warmup_gate: WarmupGateConfig = WarmupGateConfig()
    randomization: RandomizationConfig = RandomizationConfig()
    # Optional degraded-response task family block. None keeps every existing
    # entry point bit-for-bit unchanged (bare AutoDriftEnv, no wrapper).
    observation_degradation: ObservationDegradationConfig | None = None

    def __post_init__(self) -> None:
        if self.history_length < 1:
            raise ValueError("history_length must be at least 1")
        if self.action_history_mode not in {"full", "none"}:
            raise ValueError("action_history_mode must be one of: full, none")
        if self.privileged_observation_mode not in PRIVILEGED_OBSERVATION_MODES:
            raise ValueError(
                "privileged_observation_mode must be one of: "
                + ", ".join(PRIVILEGED_OBSERVATION_MODES)
            )
        if self.obstacle_relative_velocity_mode not in OBSTACLE_RELATIVE_VELOCITY_MODES:
            raise ValueError(
                "obstacle_relative_velocity_mode must be one of: "
                + ", ".join(OBSTACLE_RELATIVE_VELOCITY_MODES)
            )
        if self.wheel_observation_mode not in WHEEL_OBSERVATION_MODES:
            raise ValueError(
                "wheel_observation_mode must be one of: "
                + ", ".join(WHEEL_OBSERVATION_MODES)
            )
        if self.road_lookahead_count < 1:
            raise ValueError("road_lookahead_count must be at least 1")
        if self.road_lookahead_spacing <= 0.0:
            raise ValueError("road_lookahead_spacing must be positive")
        if self.obstacle_slots < 1:
            raise ValueError("obstacle_slots must be at least 1")
        if self.track_cost_scale < 0.0:
            raise ValueError("track_cost_scale must be non-negative")
        if self.heading_cost_scale < 0.0:
            raise ValueError("heading_cost_scale must be non-negative")
        if self.road_margin_cost_scale < 0.0:
            raise ValueError("road_margin_cost_scale must be non-negative")
        if not (0.0 <= self.road_margin_warning_fraction < 1.0):
            raise ValueError("road_margin_warning_fraction must be in [0, 1)")
        if self.off_track_penalty < 0.0:
            raise ValueError("off_track_penalty must be non-negative")
        if self.soft_offtrack_tolerance_m < 0.0:
            raise ValueError("soft_offtrack_tolerance_m must be non-negative")


class AutoDriftEnv(gym.Env):
    """A compact drift-tracking environment.

    Observation excludes `mu` by default. This forces a policy to infer current
    friction and vehicle variation from response history. It also excludes
    model-derived obstacle feasibility quantities such as AEB stopping distance.
    """

    metadata = {"render_modes": []}

    def __init__(self, config: DriftEnvConfig | None = None):
        super().__init__()
        self.config = config or DriftEnvConfig()
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32)

        action_obs_dim = {"none": 0, "full": LAST_ACTION_OBS_DIM}[self.config.action_history_mode]
        wheel_obs_dim = self._wheel_observation_dim()
        road_obs_dim = 2 * self.config.road_lookahead_count * ROAD_POINT_DIM
        obstacle_obs_dim = self.config.obstacle_slots * OBSTACLE_SLOT_DIM
        self.base_obs_dim = (
            EGO_OBS_DIM
            + action_obs_dim
            + wheel_obs_dim
            + road_obs_dim
            + obstacle_obs_dim
            + self._privileged_observation_dim()
        )
        obs_dim = self.base_obs_dim * self.config.history_length
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32)

        self.track = make_track(self.config.track_kind, self.config.track_radius)
        self.rng = np.random.default_rng()
        self.model = SingleTrackDriftModel()
        self.params = self.model.params
        self.state = VehicleState(0.0, 0.0, 0.0, 8.0, 0.0, 0.0)
        self.last_action = np.array([0.0, -1.0, -1.0], dtype=np.float64)
        self.last_control = np.zeros(3, dtype=np.float64)
        self.last_steer_rate = 0.0
        self.last_forces = self.model.tire_forces(8.0, 0.0, 0.0, 0.0, 0.0)
        self.front_wheel_speed = float(self.state.vx)
        self.rear_wheel_speed = float(self.state.vx)
        self.last_front_wheel_speed = float(self.state.vx)
        self.last_rear_wheel_speed = float(self.state.vx)
        self.obs_history: list[np.ndarray] = []
        self.speed_ref = 8.0
        self.beta_target = 0.45
        self.step_count = 0
        self.friction_step_at: int | None = None
        self.friction_step_applied = False
        self.initial_mu = self.params.mu
        self.obstacle_scenario: ObstacleScenario | None = None
        self.obstacle_position: np.ndarray | None = None
        self.obstacle_velocity = np.zeros(2, dtype=np.float64)
        self.obstacle_lateral_velocity = 0.0
        self.min_obstacle_clearance = float("inf")
        self.collision = False
        self.obstacle_completed = False
        self.obstacle_passed_raw = False
        self.termination_reason = ""
        self.completion_reason = ""
        self.max_off_track_overshoot = 0.0
        self.soft_offtrack_step_count = 0
        self.first_soft_offtrack_step: int | None = None
        self.warmup_gate_position: np.ndarray | None = None
        self.warmup_gate_half_width = float("nan")
        self.warmup_gate_active = False
        self.warmup_gate_passed = False
        self.warmup_gate_collision = False
        self.warmup_gate_min_clearance = float("inf")

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        super().reset(seed=seed)
        if seed is not None:
            self.rng = np.random.default_rng(seed)

        options = options or {}
        base_params = options.get("base_params")
        self.params = sample_vehicle_params(self.rng, base=base_params, config=self.config.randomization)
        self.initial_mu = self.params.mu
        self.model = SingleTrackDriftModel(self.params)
        self.friction_step_at = None if self._uses_obstacle_aligned_friction_step() else self._sample_friction_step_at()
        self.friction_step_applied = False
        self.step_count = 0
        self.termination_reason = ""
        self.completion_reason = ""
        self.max_off_track_overshoot = 0.0
        self.soft_offtrack_step_count = 0
        self.first_soft_offtrack_step = None
        self.obstacle_passed_raw = False

        self.speed_ref = self._sample_speed_ref()
        self.beta_target = float(self.rng.uniform(*self.config.beta_target_range))
        initial_beta = float(self.rng.normal(0.0, 0.04))
        x, y, psi, vx, vy = self.track.reset_pose(self.rng, self.speed_ref, beta=initial_beta)
        initial_frame = self.track.frame(x, y, psi)
        self.state = VehicleState(
            x=x,
            y=y,
            psi=psi,
            vx=vx,
            vy=vy,
            yaw_rate=self.speed_ref * initial_frame.curvature,
            steer=0.0,
            drive_force=0.0,
        )
        self._reset_warmup_gate(np.array([x, y], dtype=np.float64), initial_frame)
        self._reset_obstacle(np.array([x, y], dtype=np.float64), initial_frame)
        self.last_action = np.array([0.0, -1.0, -1.0], dtype=np.float64)
        self.last_control = np.zeros(3, dtype=np.float64)
        self.last_steer_rate = 0.0
        self.last_forces = self.model.tire_forces(vx, vy, self.state.yaw_rate, 0.0, 0.0)
        self._reset_raw_wheel_state()
        base_observation = self._base_observation()
        self.obs_history = [base_observation.copy() for _ in range(self.config.history_length)]

        return self._observation(), self._info(self.track.frame(self.state.x, self.state.y, self.state.psi))

    def _sample_speed_ref(self) -> float:
        low, high = self.config.speed_range
        if self.config.friction_limited_speed:
            friction_speed = math.sqrt(max(self.params.mu * self.params.gravity * self.track.reference_radius, 1e-6))
            high = min(high, friction_speed * self.config.friction_speed_margin)
        if high <= low:
            return float(max(high, 1.0))
        return float(self.rng.uniform(low, high))

    def step(self, action: np.ndarray) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        self.step_count += 1
        self._maybe_apply_friction_step()
        action64 = np.asarray(action, dtype=np.float64)
        if action64.shape != (3,):
            raise ValueError(f"expected action shape (3,), got {action64.shape}")
        control = self._control_from_action(action64)
        previous_steer = self.state.steer
        self.state, self.last_forces = self.model.step(self.state, action64, self.config.dt)
        self.last_steer_rate = (self.state.steer - previous_steer) / self.config.dt
        self._update_raw_wheel_state()
        self._advance_obstacle()
        frame = self.track.frame(self.state.x, self.state.y, self.state.psi)
        reward, reward_terms = self._reward(frame, control, self.last_forces)
        self._update_warmup_gate_status(frame)
        self._update_obstacle_status(frame)
        self._update_soft_offtrack_status(frame)

        self.termination_reason = self._termination_reason(frame) or ""
        terminated = bool(self.termination_reason)
        self.obstacle_passed_raw = self._obstacle_completed(frame)
        self.obstacle_completed = self.obstacle_passed_raw and not terminated
        dense_margin_reward, dense_margin_terms = self._dense_clearance_margin_reward(frame)
        if dense_margin_terms:
            reward += dense_margin_reward
            reward_terms.update(dense_margin_terms)
        if self.obstacle_completed and self.config.obstacle.pass_reward > 0.0:
            reward += self.config.obstacle.pass_reward
            reward_terms["pass_reward"] = self.config.obstacle.pass_reward
        if self.collision:
            reward -= self.config.obstacle.collision_penalty
            reward_terms["collision_penalty"] = self.config.obstacle.collision_penalty
        margin_reward, margin_terms = self._terminal_clearance_margin_reward()
        if margin_terms:
            reward += margin_reward
            reward_terms.update(margin_terms)
        if terminated and self.config.termination_penalty > 0.0:
            reward -= self.config.termination_penalty
            reward_terms["termination_penalty"] = self.config.termination_penalty
        if self.termination_reason == "off_track" and self.config.off_track_penalty > 0.0:
            reward -= self.config.off_track_penalty
            reward_terms["off_track_penalty"] = self.config.off_track_penalty
        truncated = self.obstacle_completed or self.step_count >= self.config.max_steps
        if self.obstacle_completed:
            self.completion_reason = "obstacle_pass"
        elif terminated:
            self.completion_reason = self.termination_reason
        elif truncated:
            self.completion_reason = "max_steps"
        else:
            self.completion_reason = ""
        self.last_action = np.clip(action64, -1.0, 1.0)
        self.last_control = control

        info = self._info(frame)
        info["reward_terms"] = reward_terms
        base_observation = self._base_observation()
        self.obs_history = [base_observation] + self.obs_history[: self.config.history_length - 1]
        return self._observation(), float(reward), terminated, truncated, info

    def _sample_friction_step_at(self) -> int | None:
        if not self.config.friction_step.enabled:
            return None
        valid_range = self._friction_step_range()
        if valid_range is None:
            return None
        low, high = valid_range
        if high <= low:
            return low
        return int(self.rng.integers(low, high + 1))

    def _friction_step_range(self) -> tuple[int, int] | None:
        low, high = self.config.friction_step.step_range
        low = max(1, int(low))
        high = min(int(high), self.config.max_steps - 1)
        if high < low:
            return None
        return low, high

    def _uses_obstacle_aligned_friction_step(self) -> bool:
        return (
            self.config.friction_step.enabled
            and self.config.obstacle.enabled
            and self.config.obstacle.min_time_after_friction_step > 0.0
        )

    def _maybe_apply_friction_step(self) -> None:
        if self.friction_step_at is None or self.friction_step_applied:
            return
        if self.step_count < self.friction_step_at:
            return
        new_mu = float(self.rng.uniform(*self.config.friction_step.mu_range))
        self.params = VehicleParams(
            mass=self.params.mass,
            iz=self.params.iz,
            lf=self.params.lf,
            lr=self.params.lr,
            h_cg=self.params.h_cg,
            mu=new_mu,
            cf=self.params.cf,
            cr=self.params.cr,
            max_steer=self.params.max_steer,
            max_steer_rate=self.params.max_steer_rate,
            max_drive_force=self.params.max_drive_force,
            max_brake_force=self.params.max_brake_force,
            drive_tau=self.params.drive_tau,
            steer_tau=self.params.steer_tau,
            drag_coeff=self.params.drag_coeff,
            rolling_resistance=self.params.rolling_resistance,
            gravity=self.params.gravity,
        )
        self.model = SingleTrackDriftModel(self.params)
        if self.config.friction_step.resample_speed_ref:
            self.speed_ref = self._sample_speed_ref()
        self.friction_step_applied = True

    def _reset_obstacle(self, position: np.ndarray, frame: PathFrame) -> None:
        self.obstacle_scenario = None
        self.obstacle_position = None
        self.obstacle_velocity = np.zeros(2, dtype=np.float64)
        self.obstacle_lateral_velocity = 0.0
        self.min_obstacle_clearance = float("inf")
        self.collision = False
        self.obstacle_completed = False
        self.obstacle_passed_raw = False
        if not self.config.obstacle.enabled:
            return
        scenario_config = self.config.obstacle.scenario_config(speed=self.speed_ref, mu=self.params.mu)
        scenario = None
        accepted = False
        accepted_friction_step_at = None
        allowed_labels = set(self.config.obstacle.allowed_labels)
        for _ in range(max(1, self.config.obstacle.max_sample_attempts)):
            obstacle_distance = float(self.rng.uniform(*self.config.obstacle.distance_range))
            obstacle_lateral_offset = float(self.rng.uniform(*self.config.obstacle.lateral_offset_range))
            obstacle_half_width = float(self.rng.uniform(*self.config.obstacle.half_width_range))
            obstacle_lateral_velocity = (
                float(self.rng.uniform(*self.config.obstacle.crosser_lateral_velocity_range))
                if self.config.obstacle.motion_mode == "constant_velocity_crosser"
                else 0.0
            )
            scenario = classify_obstacle_scenario(
                speed=self.speed_ref,
                mu=self.params.mu,
                obstacle_distance=obstacle_distance,
                obstacle_half_width=obstacle_half_width,
                config=scenario_config,
                obstacle_lateral_offset=obstacle_lateral_offset,
                obstacle_lateral_velocity=obstacle_lateral_velocity,
            )
            is_allowed = scenario.label in allowed_labels
            is_aeb_valid = not self.config.obstacle.require_aeb_infeasible or scenario.label != "aeb_feasible"
            is_near_threshold = (
                self.config.obstacle.max_threshold_score is None
                or self._obstacle_threshold_score(scenario) <= self.config.obstacle.max_threshold_score
            )
            aligned_step_range = self._obstacle_aligned_friction_step_range(scenario)
            has_time_after_step = (
                aligned_step_range is not None
                if self._uses_obstacle_aligned_friction_step()
                else self._obstacle_time_after_friction_step(scenario) >= self.config.obstacle.min_time_after_friction_step
            )
            if is_allowed and is_aeb_valid and is_near_threshold and has_time_after_step:
                if aligned_step_range is not None:
                    low, high = aligned_step_range
                    accepted_friction_step_at = low if high <= low else int(self.rng.integers(low, high + 1))
                accepted = True
                break
        if scenario is None or not accepted:
            raise RuntimeError("failed to sample an obstacle scenario matching the configured filters")
        if self.config.obstacle.require_aeb_infeasible and scenario.label == "aeb_feasible":
            raise RuntimeError("failed to sample an AEB-infeasible obstacle scenario")
        if accepted_friction_step_at is not None:
            self.friction_step_at = accepted_friction_step_at
        self.obstacle_scenario = scenario
        normal_left = np.array([-frame.tangent[1], frame.tangent[0]], dtype=np.float64)
        self.obstacle_position = position + frame.tangent * obstacle_distance + normal_left * obstacle_lateral_offset
        self.obstacle_lateral_velocity = float(scenario.obstacle_lateral_velocity)
        self.obstacle_velocity = normal_left * self.obstacle_lateral_velocity
        self._update_obstacle_status(frame)

    def _reset_warmup_gate(self, position: np.ndarray, frame: PathFrame) -> None:
        self.warmup_gate_position = None
        self.warmup_gate_half_width = float("nan")
        self.warmup_gate_active = False
        self.warmup_gate_passed = False
        self.warmup_gate_collision = False
        self.warmup_gate_min_clearance = float("inf")
        if not self.config.warmup_gate.enabled:
            return
        gate = self.config.warmup_gate
        distance = float(self.rng.uniform(*gate.distance_range))
        lateral = float(self.rng.uniform(*gate.lateral_offset_range))
        half_width = float(self.rng.uniform(*gate.half_width_range))
        normal_left = np.array([-frame.tangent[1], frame.tangent[0]], dtype=np.float64)
        self.warmup_gate_position = position + frame.tangent * distance + normal_left * lateral
        self.warmup_gate_half_width = half_width
        self.warmup_gate_active = True
        self._update_warmup_gate_status(frame)

    def _obstacle_aligned_friction_step_range(self, scenario: ObstacleScenario) -> tuple[int, int] | None:
        if not self._uses_obstacle_aligned_friction_step():
            return None
        valid_range = self._friction_step_range()
        if valid_range is None:
            return None
        low, high = valid_range
        latest_step = int(math.floor((scenario.time_to_obstacle - self.config.obstacle.min_time_after_friction_step) / self.config.dt))
        high = min(high, latest_step)
        if high < low:
            return None
        return low, high

    def _obstacle_threshold_score(self, scenario: ObstacleScenario) -> float:
        required = max(float(scenario.required_lateral_offset), 1e-6)
        aes_margin = float(scenario.conventional_lateral_capacity - scenario.required_lateral_offset) / required
        drift_margin = float(scenario.drift_lateral_capacity - scenario.required_lateral_offset) / required
        return min(abs(aes_margin), abs(drift_margin))

    def _obstacle_time_after_friction_step(self, scenario: ObstacleScenario) -> float:
        if self.friction_step_at is None:
            return float("inf")
        return float(scenario.time_to_obstacle - self.friction_step_at * self.config.dt)

    def _obstacle_path_features(self, frame: PathFrame) -> tuple[float, float, float, float]:
        if self.obstacle_scenario is None or self.obstacle_position is None:
            return (0.0, 0.0, 0.0, 0.0)
        ego_position = np.array([self.state.x, self.state.y], dtype=np.float64)
        delta = self.obstacle_position - ego_position
        longitudinal = float(np.dot(delta, frame.tangent))
        lateral = float(frame.tangent[0] * delta[1] - frame.tangent[1] * delta[0])
        time_to_obstacle = longitudinal / max(math.hypot(self.state.vx, self.state.vy), 1.0)
        return (
            longitudinal / 80.0,
            lateral / max(self.config.track_width, 1e-6),
            self.obstacle_scenario.required_lateral_offset / max(self.config.track_width, 1e-6),
            time_to_obstacle / 5.0,
        )

    def _body_point(self, point: np.ndarray) -> np.ndarray:
        delta = np.asarray(point, dtype=np.float64) - np.array([self.state.x, self.state.y], dtype=np.float64)
        return self._body_vector(delta)

    def _body_vector(self, vector: np.ndarray) -> np.ndarray:
        delta = np.asarray(vector, dtype=np.float64)
        cos_psi = math.cos(self.state.psi)
        sin_psi = math.sin(self.state.psi)
        return np.array(
            [
                cos_psi * delta[0] + sin_psi * delta[1],
                -sin_psi * delta[0] + cos_psi * delta[1],
            ],
            dtype=np.float64,
        )

    def _advance_obstacle(self) -> None:
        if self.obstacle_position is None:
            return
        if self.config.obstacle.motion_mode == "static":
            return
        self.obstacle_position = self.obstacle_position + self.obstacle_velocity * self.config.dt

    def _warmup_gate_visible(self) -> bool:
        return bool(
            self.config.warmup_gate.enabled
            and self.warmup_gate_active
            and self.warmup_gate_position is not None
            and self.step_count >= self.config.warmup_gate.reveal_step
        )

    def _warmup_gate_longitudinal_distance(self, frame: PathFrame) -> float:
        if self.warmup_gate_position is None:
            return float("inf")
        ego_position = np.array([self.state.x, self.state.y], dtype=np.float64)
        return float(np.dot(self.warmup_gate_position - ego_position, frame.tangent))

    def _update_warmup_gate_status(self, frame: PathFrame) -> None:
        if not self.config.warmup_gate.enabled or self.warmup_gate_position is None:
            return
        ego_position = np.array([self.state.x, self.state.y], dtype=np.float64)
        clearance = float(np.linalg.norm(self.warmup_gate_position - ego_position))
        self.warmup_gate_min_clearance = min(self.warmup_gate_min_clearance, clearance)
        collision_radius = self.config.obstacle.ego_half_width + self.warmup_gate_half_width
        self.warmup_gate_collision = clearance <= collision_radius
        longitudinal = self._warmup_gate_longitudinal_distance(frame)
        if longitudinal <= -self.config.warmup_gate.finish_pass_distance:
            self.warmup_gate_passed = True
            self.warmup_gate_active = False
        elif self.step_count >= self.config.warmup_gate.max_active_steps:
            self.warmup_gate_active = False

    def _warmup_gate_collision_radius(self) -> float:
        if self.warmup_gate_position is None or not np.isfinite(self.warmup_gate_half_width):
            return float("nan")
        return float(self.config.obstacle.ego_half_width + self.warmup_gate_half_width)

    def _active_obstacle_slot_geometry(self) -> tuple[str, np.ndarray | None, float]:
        if self._warmup_gate_visible() and self.warmup_gate_position is not None:
            return "warmup_gate", self.warmup_gate_position, self.warmup_gate_half_width
        if self.config.obstacle.enabled and self.obstacle_scenario is not None and self.obstacle_position is not None:
            body = self._body_point(self.obstacle_position)
            if self._obstacle_perception_visible(longitudinal_distance=float(body[0])):
                return "emergency_obstacle", self.obstacle_position, float(self.obstacle_scenario.obstacle_half_width)
        return "none", None, float("nan")

    def _control_from_action(self, action: np.ndarray) -> np.ndarray:
        action = np.asarray(action, dtype=np.float64)
        steer = float(np.clip(action[0], -1.0, 1.0))
        throttle = 0.5 * (float(np.clip(action[1], -1.0, 1.0)) + 1.0)
        brake = 0.5 * (float(np.clip(action[2], -1.0, 1.0)) + 1.0)
        return np.array([steer, throttle, brake], dtype=np.float64)

    def _body_acceleration(self, forces: TireForces) -> tuple[float, float]:
        drag = self.params.drag_coeff * self.state.vx * abs(self.state.vx)
        rolling = self.params.rolling_resistance * math.tanh(self.state.vx)
        fx_body = forces.fx_rear - forces.fy_front * math.sin(self.state.steer) - drag - rolling
        fy_body = forces.fy_front * math.cos(self.state.steer) + forces.fy_rear
        ax_body = fx_body / self.params.mass + self.state.yaw_rate * self.state.vy
        ay_body = fy_body / self.params.mass - self.state.yaw_rate * self.state.vx
        return float(ax_body), float(ay_body)

    def _drive_actuator_states(self) -> tuple[float, float]:
        if self.state.drive_force >= 0.0:
            return float(self.state.drive_force / max(self.params.max_drive_force, 1e-6)), 0.0
        return 0.0, float(-self.state.drive_force / max(self.params.max_brake_force, 1e-6))

    def _wheel_observation_dim(self) -> int:
        if self.config.wheel_observation_mode == "none":
            return 0
        if self.config.wheel_observation_mode in FRONT_REAR_WHEEL_OBSERVATION_MODES:
            return FRONT_REAR_WHEEL_OBS_DIM
        raise ValueError(f"unknown wheel observation mode: {self.config.wheel_observation_mode}")

    def _reset_raw_wheel_state(self) -> None:
        self.front_wheel_speed = float(self.state.vx)
        self.rear_wheel_speed = float(self.state.vx)
        self.last_front_wheel_speed = float(self.state.vx)
        self.last_rear_wheel_speed = float(self.state.vx)

    def _update_raw_wheel_state(self) -> None:
        if self.config.wheel_observation_mode not in RAW_FRONT_REAR_WHEEL_OBSERVATION_MODES:
            return
        dt = max(float(self.config.dt), 1e-6)
        self.last_front_wheel_speed = self.front_wheel_speed
        self.last_rear_wheel_speed = self.rear_wheel_speed

        sensor_tau = max(0.04, 0.5 * float(self.params.drive_tau))
        front_relaxation = (float(self.state.vx) - self.front_wheel_speed) / sensor_tau
        self.front_wheel_speed += dt * front_relaxation

        wheel_inertia_proxy = max(0.08 * self.params.mass, 1.0)
        rear_torque_balance = (float(self.state.drive_force) - float(self.last_forces.fx_rear)) / wheel_inertia_proxy
        rear_relaxation = (float(self.state.vx) - self.rear_wheel_speed) / sensor_tau
        self.rear_wheel_speed += dt * (rear_relaxation + rear_torque_balance)

        speed_bound = max(45.0, 2.5 * abs(float(self.state.vx)) + 10.0)
        self.front_wheel_speed = float(np.clip(self.front_wheel_speed, -speed_bound, speed_bound))
        self.rear_wheel_speed = float(np.clip(self.rear_wheel_speed, -speed_bound, speed_bound))

    def _front_rear_local_ground_speeds(self) -> tuple[float, float]:
        front_lateral_speed = float(self.state.vy + self.state.yaw_rate * self.params.lf)
        front_parallel = float(
            self.state.vx * math.cos(self.state.steer) + front_lateral_speed * math.sin(self.state.steer)
        )
        rear_parallel = float(self.state.vx)
        return front_parallel, rear_parallel

    def _wheel_response_features(self, ax_body: float) -> list[float]:
        if self.config.wheel_observation_mode == "none":
            return []
        if self.config.wheel_observation_mode in RAW_FRONT_REAR_WHEEL_OBSERVATION_MODES:
            throttle_state, brake_state = self._drive_actuator_states()
            dt = max(float(self.config.dt), 1e-6)
            front_wheel_accel = (self.front_wheel_speed - self.last_front_wheel_speed) / dt
            rear_wheel_accel = (self.rear_wheel_speed - self.last_rear_wheel_speed) / dt
            features = [
                float(self.front_wheel_speed / 20.0),
                float(self.rear_wheel_speed / 20.0),
                float(np.clip(front_wheel_accel / 30.0, -2.0, 2.0)),
                float(np.clip(rear_wheel_accel / 30.0, -2.0, 2.0)),
                0.0,
                0.0,
                0.0,
                brake_state,
                brake_state,
                throttle_state,
                0.0,
                0.0,
                0.0,
            ]
            if self.config.wheel_observation_mode == "front_rear_raw":
                return features

            front_ground, rear_ground = self._front_rear_local_ground_speeds()
            features[2] = float(front_ground / 20.0)
            features[3] = float(rear_ground / 20.0)
            if self.config.wheel_observation_mode == "front_rear_omega":
                features[2] = 0.0
                features[3] = 0.0
                return features
            if self.config.wheel_observation_mode == "front_rear_omega_ground":
                return features
            if self.config.wheel_observation_mode == "front_rear_omega_ground_error":
                fixed_speed_scale = 20.0
                features[4] = float((self.front_wheel_speed - front_ground) / fixed_speed_scale)
                features[5] = float((self.rear_wheel_speed - rear_ground) / fixed_speed_scale)
                return features
        if self.config.wheel_observation_mode != "front_rear":
            raise ValueError(f"unknown wheel observation mode: {self.config.wheel_observation_mode}")

        throttle_state, brake_state = self._drive_actuator_states()
        force_scale = max(self.params.max_drive_force, self.params.max_brake_force, 1.0)
        rear_force_error = self.state.drive_force - self.last_forces.fx_rear
        rear_slip = float(np.tanh(rear_force_error / max(0.25 * force_scale, 1.0)))
        front_slip = 0.0
        rear_minus_front_slip = rear_slip - front_slip
        speed_scale = max(abs(self.state.vx), 2.0)
        front_wheel_speed = self.state.vx
        rear_wheel_speed = self.state.vx + rear_slip * speed_scale
        wheel_inertia_proxy = max(0.08 * self.params.mass, 1.0)
        front_wheel_accel = float(ax_body)
        rear_wheel_accel = float(ax_body + rear_force_error / wheel_inertia_proxy)
        abs_active = 1.0 if brake_state > 0.2 and rear_slip < -0.25 else 0.0
        tcs_active = 1.0 if throttle_state > 0.2 and rear_slip > 0.25 else 0.0

        return [
            float(front_wheel_speed / 20.0),
            float(rear_wheel_speed / 20.0),
            float(np.clip(front_wheel_accel / 30.0, -2.0, 2.0)),
            float(np.clip(rear_wheel_accel / 30.0, -2.0, 2.0)),
            front_slip,
            rear_slip,
            rear_minus_front_slip,
            brake_state,
            brake_state,
            throttle_state,
            abs_active,
            abs_active,
            tcs_active,
        ]

    def _road_boundary_features(self) -> list[float]:
        distances = self.config.road_lookahead_spacing * np.arange(1, self.config.road_lookahead_count + 1)
        center_points, tangents = self.track.lookahead_centerline(self.state.x, self.state.y, distances)
        half_width = 0.5 * self.config.track_width
        left_features: list[float] = []
        right_features: list[float] = []
        for point, tangent in zip(center_points, tangents, strict=True):
            normal_left = np.array([-tangent[1], tangent[0]], dtype=np.float64)
            left_body = self._body_point(point + normal_left * half_width)
            right_body = self._body_point(point - normal_left * half_width)
            left_features.extend([float(left_body[0] / 80.0), float(left_body[1] / 20.0)])
            right_features.extend([float(right_body[0] / 80.0), float(right_body[1] / 20.0)])
        return left_features + right_features

    def _obstacle_slot_features(self) -> list[float]:
        slots = np.zeros((self.config.obstacle_slots, OBSTACLE_SLOT_DIM), dtype=np.float64)
        obstacle_kind, obstacle_position, half_width = self._active_obstacle_slot_geometry()
        if obstacle_position is not None and np.isfinite(half_width):
            body = self._body_point(obstacle_position)
            if self.config.obstacle_relative_velocity_mode == "ego":
                obstacle_velocity_body = (
                    self._body_vector(self.obstacle_velocity)
                    if obstacle_kind == "emergency_obstacle"
                    else np.zeros(2, dtype=np.float64)
                )
                rel_vx = obstacle_velocity_body[0] - self.state.vx + self.state.yaw_rate * body[1]
                rel_vy = obstacle_velocity_body[1] - self.state.vy - self.state.yaw_rate * body[0]
            else:
                rel_vx = 0.0
                rel_vy = 0.0
            slots[0] = np.array(
                [
                    1.0,
                    body[0] / 80.0,
                    body[1] / 20.0,
                    rel_vx / 20.0,
                    rel_vy / 12.0,
                    half_width / 5.0,
                    half_width / 5.0,
                ],
                dtype=np.float64,
            )
        return slots.reshape(-1).astype(float).tolist()

    def _obstacle_perception_visible(self, longitudinal_distance: float | None = None) -> bool:
        if not self.config.obstacle.enabled or self.obstacle_scenario is None or self.obstacle_position is None:
            return False
        if self.step_count < self.config.obstacle.perception_reveal_step:
            return False
        reveal_distance = self.config.obstacle.perception_reveal_distance
        if reveal_distance is not None:
            if longitudinal_distance is None:
                frame = self.track.frame(self.state.x, self.state.y, self.state.psi)
                longitudinal_distance = self._obstacle_longitudinal_distance(frame)
            if float(longitudinal_distance) > reveal_distance:
                return False
        return True

    def _privileged_observation_dim(self) -> int:
        if not self.config.include_privileged_params:
            return 0
        if self.config.privileged_observation_mode == "basic":
            return BASIC_PRIVILEGED_OBS_DIM
        if self.config.privileged_observation_mode == "full_dynamics":
            return FULL_DYNAMICS_PRIVILEGED_OBS_DIM
        raise ValueError(f"unknown privileged observation mode: {self.config.privileged_observation_mode}")

    def _privileged_param_features(self) -> list[float]:
        base = VehicleParams()
        if self.config.privileged_observation_mode == "basic":
            return [
                self.params.mu,
                self.params.mass / base.mass,
                self.params.lf / base.lf,
                self.params.cr / base.cr,
            ]
        if self.config.privileged_observation_mode == "full_dynamics":
            return [
                self.params.mu,
                self.params.mass / base.mass,
                self.params.iz / base.iz,
                (self.params.lf - base.lf) / 0.25,
                self.params.cf / base.cf,
                self.params.cr / base.cr,
                self.params.max_drive_force / base.max_drive_force,
                self.params.max_brake_force / base.max_brake_force,
                self.params.steer_tau / base.steer_tau,
                self.params.drive_tau / base.drive_tau,
            ]
        raise ValueError(f"unknown privileged observation mode: {self.config.privileged_observation_mode}")

    def _obstacle_longitudinal_distance(self, frame: PathFrame) -> float:
        if self.obstacle_scenario is None or self.obstacle_position is None:
            return float("inf")
        ego_position = np.array([self.state.x, self.state.y], dtype=np.float64)
        return float(np.dot(self.obstacle_position - ego_position, frame.tangent))

    def _obstacle_completed(self, frame: PathFrame) -> bool:
        if not self.config.obstacle.enabled or not self.config.obstacle.finish_on_pass:
            return False
        if self.obstacle_scenario is None or self.obstacle_position is None:
            return False
        return self._obstacle_longitudinal_distance(frame) <= -self.config.obstacle.finish_pass_distance

    def _update_obstacle_status(self, frame: PathFrame) -> None:
        del frame
        if self.obstacle_scenario is None or self.obstacle_position is None:
            return
        ego_position = np.array([self.state.x, self.state.y], dtype=np.float64)
        clearance = float(np.linalg.norm(self.obstacle_position - ego_position))
        self.min_obstacle_clearance = min(self.min_obstacle_clearance, clearance)
        collision_radius = self.config.obstacle.ego_half_width + self.obstacle_scenario.obstacle_half_width
        self.collision = clearance <= collision_radius

    def _obstacle_collision_radius(self) -> float:
        if self.obstacle_scenario is None:
            return float("nan")
        return float(self.config.obstacle.ego_half_width + self.obstacle_scenario.obstacle_half_width)

    def _clearance_margin(self) -> float:
        obstacle_collision_radius = self._obstacle_collision_radius()
        if not self.config.obstacle.enabled or not np.isfinite(obstacle_collision_radius):
            return float("nan")
        return float(self.min_obstacle_clearance - obstacle_collision_radius)

    def _warmup_gate_clearance_margin(self) -> float:
        collision_radius = self._warmup_gate_collision_radius()
        if not self.config.warmup_gate.enabled or not np.isfinite(collision_radius):
            return float("nan")
        return float(self.warmup_gate_min_clearance - collision_radius)

    def _terminal_clearance_margin_reward(self) -> tuple[float, dict[str, float]]:
        scale = float(self.config.obstacle.clearance_margin_reward_scale)
        if scale == 0.0 or not (self.obstacle_completed or self.collision):
            return 0.0, {}
        margin = self._clearance_margin()
        if not np.isfinite(margin):
            return 0.0, {}
        clip = float(self.config.obstacle.clearance_margin_reward_clip)
        normalized_margin = float(np.clip(margin / clip, -1.0, 1.0))
        reward = scale * normalized_margin
        return reward, {
            "clearance_margin_reward": reward,
            "clearance_margin_reward_normalized": normalized_margin,
        }

    def _dense_clearance_margin_reward(self, frame: PathFrame) -> tuple[float, dict[str, float]]:
        scale = float(self.config.obstacle.dense_clearance_margin_reward_scale)
        if scale == 0.0 or self.obstacle_scenario is None or self.obstacle_position is None:
            return 0.0, {}
        longitudinal = self._obstacle_longitudinal_distance(frame)
        if longitudinal > self.config.obstacle.dense_clearance_margin_reward_window:
            return 0.0, {}
        if longitudinal < -self.config.obstacle.finish_pass_distance:
            return 0.0, {}
        margin = self._clearance_margin()
        if not np.isfinite(margin):
            return 0.0, {}
        clip = float(self.config.obstacle.dense_clearance_margin_reward_clip)
        normalized_margin = float(np.clip(margin / clip, -1.0, 1.0))
        reward = scale * normalized_margin
        return reward, {
            "dense_clearance_margin_reward": reward,
            "dense_clearance_margin_reward_normalized": normalized_margin,
        }

    def _observation(self) -> np.ndarray:
        if not self.obs_history:
            base_observation = self._base_observation()
            return np.tile(base_observation, self.config.history_length).astype(np.float32)
        return np.concatenate(self.obs_history).astype(np.float32)

    def _base_observation(self) -> np.ndarray:
        frame = self.track.frame(self.state.x, self.state.y, self.state.psi)
        del frame
        ax_body, ay_body = self._body_acceleration(self.last_forces)
        throttle_state, brake_state = self._drive_actuator_states()

        obs = [
            self.state.vx / 20.0,
            self.state.vy / 12.0,
            self.state.yaw_rate / 2.5,
            ax_body / 15.0,
            ay_body / 15.0,
            self.state.steer / self.params.max_steer,
            self.last_steer_rate / max(self.params.max_steer_rate, 1e-6),
            throttle_state,
            brake_state,
        ]
        if self.config.action_history_mode == "full":
            obs.extend(self.last_control.tolist())
        obs.extend(self._wheel_response_features(ax_body))
        obs.extend(self._road_boundary_features())
        obs.extend(self._obstacle_slot_features())
        if self.config.include_privileged_params:
            obs.extend(self._privileged_param_features())
        return np.asarray(obs, dtype=np.float32)

    def _reward(
        self,
        frame: PathFrame,
        control: np.ndarray,
        forces: TireForces,
    ) -> tuple[float, dict[str, float]]:
        speed = math.hypot(self.state.vx, self.state.vy)
        beta = math.atan2(self.state.vy, max(self.state.vx, 1e-6))
        global_vx = self.state.vx * math.cos(self.state.psi) - self.state.vy * math.sin(self.state.psi)
        global_vy = self.state.vx * math.sin(self.state.psi) + self.state.vy * math.cos(self.state.psi)
        along_speed = float(np.dot(np.array([global_vx, global_vy]), frame.tangent))

        track_cost = (frame.lateral_error / self.config.track_width) ** 2
        heading_cost = wrap_pi(frame.heading_error) ** 2
        margin_fraction = abs(frame.lateral_error) / max(self.config.track_width, 1e-6)
        road_margin_excess = max(margin_fraction - self.config.road_margin_warning_fraction, 0.0)
        road_margin_cost = 0.0
        if self.config.road_margin_cost_scale > 0.0:
            road_margin_cost = (
                road_margin_excess / max(1.0 - self.config.road_margin_warning_fraction, 1e-6)
            ) ** 2
        speed_cost = ((speed - self.speed_ref) / max(self.speed_ref, 1.0)) ** 2
        beta_cost = (abs(beta) - self.beta_target) ** 2
        action_cost = float(np.sum(np.square(control)))
        action_rate_cost = float(np.sum(np.square(control - self.last_control)))
        rear_saturation = abs(forces.fx_rear) / max(self.params.mu * forces.fz_rear, 1.0)
        drift_bonus = min(abs(beta) / max(self.beta_target, 1e-3), 1.5)
        stable_aes_sideslip_cost = 0.0
        if self.obstacle_scenario is not None and self.obstacle_scenario.label == "aes_feasible":
            drift_bonus *= self.config.obstacle.stable_aes_drift_bonus_scale
            stable_aes_sideslip_cost = max(abs(beta) - self.config.obstacle.stable_aes_beta_limit, 0.0) ** 2
        progress_reward = along_speed / max(self.speed_ref, 1.0)

        reward = (
            1.1 * progress_reward
            + 0.18 * drift_bonus
            + 0.10 * rear_saturation
            - self.config.track_cost_scale * track_cost
            - self.config.heading_cost_scale * heading_cost
            - self.config.road_margin_cost_scale * road_margin_cost
            - 0.40 * speed_cost
            - 0.70 * beta_cost
            - 0.030 * action_cost
            - 0.040 * action_rate_cost
            - self.config.obstacle.stable_aes_sideslip_penalty * stable_aes_sideslip_cost
        )
        terms = {
            "progress": progress_reward,
            "drift_bonus": drift_bonus,
            "rear_saturation": rear_saturation,
            "track_cost": track_cost,
            "heading_cost": heading_cost,
            "road_margin_fraction": margin_fraction,
            "speed_cost": speed_cost,
            "beta_cost": beta_cost,
        }
        if road_margin_cost > 0.0 or self.config.road_margin_cost_scale > 0.0:
            terms["road_margin_cost"] = road_margin_cost
        if stable_aes_sideslip_cost > 0.0 or self.config.obstacle.stable_aes_sideslip_penalty > 0.0:
            terms["stable_aes_sideslip_cost"] = stable_aes_sideslip_cost
        return reward, terms

    def _termination_reason(self, frame: PathFrame) -> str | None:
        speed = math.hypot(self.state.vx, self.state.vy)
        values = self.state.as_array()
        if not np.all(np.isfinite(values)):
            return "non_finite_state"
        if self._hard_offtrack_failure(frame):
            return "off_track"
        if self.collision:
            return "obstacle_collision"
        if speed < 1.0:
            return "speed_too_low"
        if speed > 32.0:
            return "speed_too_high"
        if abs(self.state.yaw_rate) > 6.0:
            return "yaw_rate_limit"
        return None

    def _terminated(self, frame: PathFrame) -> bool:
        return self._termination_reason(frame) is not None

    def _off_track_overshoot(self, frame: PathFrame) -> float:
        return float(max(abs(frame.lateral_error) - self.config.track_width, 0.0))

    def _soft_offtrack_violation(self, frame: PathFrame) -> bool:
        overshoot = self._off_track_overshoot(frame)
        return bool(
            self.config.soft_offtrack_metric_enabled
            and overshoot > 0.0
            and overshoot <= self.config.soft_offtrack_tolerance_m
        )

    def _hard_offtrack_failure(self, frame: PathFrame) -> bool:
        overshoot = self._off_track_overshoot(frame)
        if self.config.soft_offtrack_metric_enabled:
            return bool(overshoot > self.config.soft_offtrack_tolerance_m)
        return bool(overshoot > 0.0)

    def _update_soft_offtrack_status(self, frame: PathFrame) -> None:
        overshoot = self._off_track_overshoot(frame)
        self.max_off_track_overshoot = max(self.max_off_track_overshoot, overshoot)
        if self._soft_offtrack_violation(frame):
            self.soft_offtrack_step_count += 1
            if self.first_soft_offtrack_step is None:
                self.first_soft_offtrack_step = self.step_count

    def _info(self, frame: PathFrame) -> dict[str, Any]:
        speed = math.hypot(self.state.vx, self.state.vy)
        beta = math.atan2(self.state.vy, max(self.state.vx, 1e-6))
        base_params = VehicleParams()
        obstacle_path = self._obstacle_path_features(frame)
        obstacle_distance = obstacle_path[0] * 80.0 if self.config.obstacle.enabled else float("nan")
        obstacle_collision_radius = self._obstacle_collision_radius()
        min_clearance_margin = self._clearance_margin()
        active_obstacle_kind, active_obstacle_position, active_obstacle_half_width = self._active_obstacle_slot_geometry()
        if active_obstacle_position is None:
            active_body = np.array([float("nan"), float("nan")], dtype=np.float64)
        else:
            active_body = self._body_point(active_obstacle_position)
        warmup_gate_distance = self._warmup_gate_longitudinal_distance(frame)
        warmup_gate_collision_radius = self._warmup_gate_collision_radius()
        off_track_overshoot = self._off_track_overshoot(frame)
        soft_offtrack_violation = self._soft_offtrack_violation(frame)
        hard_offtrack_failure = self._hard_offtrack_failure(frame)
        return {
            "mu": self.params.mu,
            "initial_mu": self.initial_mu,
            "mass": self.params.mass,
            "mass_scale": self.params.mass / base_params.mass,
            "inertia_scale": self.params.iz / base_params.iz,
            "cg_shift": self.params.lf - base_params.lf,
            "lf": self.params.lf,
            "lr": self.params.lr,
            "front_tire_stiffness_scale": self.params.cf / base_params.cf,
            "rear_tire_stiffness_scale": self.params.cr / base_params.cr,
            "tire_stiffness_scale": 0.5 * (self.params.cf / base_params.cf + self.params.cr / base_params.cr),
            "drive_scale": self.params.max_drive_force / base_params.max_drive_force,
            "brake_scale": self.params.max_brake_force / base_params.max_brake_force,
            "steer_tau_scale": self.params.steer_tau / base_params.steer_tau,
            "drive_tau_scale": self.params.drive_tau / base_params.drive_tau,
            "speed": speed,
            "beta": beta,
            "yaw_rate": self.state.yaw_rate,
            "dt": self.config.dt,
            "track_width": self.config.track_width,
            "soft_offtrack_metric_enabled": self.config.soft_offtrack_metric_enabled,
            "soft_offtrack_tolerance_m": self.config.soft_offtrack_tolerance_m,
            "off_track_overshoot": off_track_overshoot,
            "max_off_track_overshoot_env": self.max_off_track_overshoot,
            "soft_offtrack_violation": soft_offtrack_violation,
            "soft_offtrack_step_count": self.soft_offtrack_step_count,
            "soft_offtrack_duration_s": self.soft_offtrack_step_count * self.config.dt,
            "first_soft_offtrack_step": (
                self.first_soft_offtrack_step if self.first_soft_offtrack_step is not None else float("nan")
            ),
            "hard_offtrack_failure": hard_offtrack_failure,
            "metric_selected_termination_reason": "off_track" if hard_offtrack_failure else self.termination_reason,
            "beta_target": self.beta_target,
            "speed_ref": self.speed_ref,
            "lateral_error": frame.lateral_error,
            "heading_error": frame.heading_error,
            "curvature": frame.curvature,
            "progress": frame.progress,
            "step": self.step_count,
            "friction_step_at": self.friction_step_at,
            "friction_step_applied": self.friction_step_applied,
            "track_kind": self.config.track_kind,
            "obstacle_enabled": self.config.obstacle.enabled,
            "obstacle_perception_visible": self._obstacle_perception_visible(
                longitudinal_distance=obstacle_distance if self.config.obstacle.enabled else None
            ),
            "obstacle_label": self.obstacle_scenario.label if self.obstacle_scenario is not None else "",
            "obstacle_motion_mode": self.config.obstacle.motion_mode,
            "obstacle_lateral_velocity": (
                self.obstacle_lateral_velocity if self.config.obstacle.enabled else float("nan")
            ),
            "obstacle_velocity_x": (
                float(self.obstacle_velocity[0]) if self.config.obstacle.enabled else float("nan")
            ),
            "obstacle_velocity_y": (
                float(self.obstacle_velocity[1]) if self.config.obstacle.enabled else float("nan")
            ),
            "obstacle_predicted_lateral_offset_at_arrival": (
                self.obstacle_scenario.predicted_lateral_offset_at_arrival
                if self.obstacle_scenario is not None
                else float("nan")
            ),
            "obstacle_distance": obstacle_distance,
            "obstacle_lateral_offset": (
                obstacle_path[1] * self.config.track_width if self.config.obstacle.enabled else float("nan")
            ),
            "obstacle_required_lateral_offset": (
                self.obstacle_scenario.required_lateral_offset if self.obstacle_scenario is not None else float("nan")
            ),
            "obstacle_threshold_score": (
                self._obstacle_threshold_score(self.obstacle_scenario) if self.obstacle_scenario is not None else float("nan")
            ),
            "obstacle_time_after_friction_step": (
                self._obstacle_time_after_friction_step(self.obstacle_scenario)
                if self.obstacle_scenario is not None
                else float("nan")
            ),
            "min_obstacle_clearance": self.min_obstacle_clearance if self.config.obstacle.enabled else float("nan"),
            "obstacle_collision_radius": (
                obstacle_collision_radius if self.config.obstacle.enabled else float("nan")
            ),
            "min_clearance_margin": min_clearance_margin,
            "collision": self.collision,
            "obstacle_completed": self.obstacle_completed,
            "obstacle_passed_raw": self.obstacle_passed_raw,
            "termination_reason": self.termination_reason,
            "completion_reason": self.completion_reason,
            "active_obstacle_kind": active_obstacle_kind,
            "active_obstacle_body_x": float(active_body[0]),
            "active_obstacle_body_y": float(active_body[1]),
            "active_obstacle_half_width": float(active_obstacle_half_width),
            "warmup_gate_enabled": self.config.warmup_gate.enabled,
            "warmup_gate_active": self.warmup_gate_active,
            "warmup_gate_visible": self._warmup_gate_visible(),
            "warmup_gate_passed": self.warmup_gate_passed,
            "warmup_gate_collision": self.warmup_gate_collision,
            "warmup_gate_distance": warmup_gate_distance,
            "warmup_gate_half_width": self.warmup_gate_half_width,
            "warmup_gate_collision_radius": warmup_gate_collision_radius,
            "warmup_gate_min_clearance": (
                self.warmup_gate_min_clearance if self.config.warmup_gate.enabled else float("nan")
            ),
            "warmup_gate_clearance_margin": self._warmup_gate_clearance_margin(),
        }
