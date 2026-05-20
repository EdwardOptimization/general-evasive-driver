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
class DriftEnvConfig:
    dt: float = 0.02
    max_steps: int = 800
    track_kind: str = "circle"
    track_radius: float = 18.0
    track_width: float = 5.0
    speed_range: tuple[float, float] = (5.0, 12.0)
    beta_target_range: tuple[float, float] = (0.32, 0.70)
    termination_penalty: float = 0.0
    friction_limited_speed: bool = True
    friction_speed_margin: float = 0.92
    history_length: int = 1
    include_privileged_params: bool = False
    friction_step: FrictionStepConfig = FrictionStepConfig()
    obstacle: ObstacleTaskConfig = ObstacleTaskConfig()
    randomization: RandomizationConfig = RandomizationConfig()


class AutoDriftEnv(gym.Env):
    """A compact drift-tracking environment.

    Observation excludes `mu` by default. This forces a policy to infer current
    friction and vehicle variation from response history, matching the intended
    research direction.
    """

    metadata = {"render_modes": []}

    def __init__(self, config: DriftEnvConfig | None = None):
        super().__init__()
        self.config = config or DriftEnvConfig()
        if self.config.history_length < 1:
            raise ValueError("history_length must be at least 1")
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(2,), dtype=np.float32)

        obstacle_obs_dim = 5 if self.config.obstacle.enabled else 0
        self.base_obs_dim = 13 + obstacle_obs_dim + (4 if self.config.include_privileged_params else 0)
        obs_dim = self.base_obs_dim * self.config.history_length
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32)

        self.track = make_track(self.config.track_kind, self.config.track_radius)
        self.rng = np.random.default_rng()
        self.model = SingleTrackDriftModel()
        self.params = self.model.params
        self.state = VehicleState(0.0, 0.0, 0.0, 8.0, 0.0, 0.0)
        self.last_action = np.zeros(2, dtype=np.float64)
        self.last_forces = self.model.tire_forces(8.0, 0.0, 0.0, 0.0, 0.0)
        self.obs_history: list[np.ndarray] = []
        self.speed_ref = 8.0
        self.beta_target = 0.45
        self.step_count = 0
        self.friction_step_at: int | None = None
        self.friction_step_applied = False
        self.initial_mu = self.params.mu
        self.obstacle_scenario: ObstacleScenario | None = None
        self.obstacle_position: np.ndarray | None = None
        self.min_obstacle_clearance = float("inf")
        self.collision = False
        self.obstacle_completed = False

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
        self.friction_step_at = self._sample_friction_step_at()
        self.friction_step_applied = False

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
        self._reset_obstacle(np.array([x, y], dtype=np.float64), initial_frame)
        self.last_action = np.zeros(2, dtype=np.float64)
        self.last_forces = self.model.tire_forces(vx, vy, self.state.yaw_rate, 0.0, 0.0)
        base_observation = self._base_observation()
        self.obs_history = [base_observation.copy() for _ in range(self.config.history_length)]
        self.step_count = 0

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
        self.state, self.last_forces = self.model.step(self.state, action64, self.config.dt)
        frame = self.track.frame(self.state.x, self.state.y, self.state.psi)
        reward, reward_terms = self._reward(frame, action64, self.last_forces)
        self._update_obstacle_status(frame)

        terminated = self._terminated(frame)
        self.obstacle_completed = self._obstacle_completed(frame) and not terminated
        if self.obstacle_completed and self.config.obstacle.pass_reward > 0.0:
            reward += self.config.obstacle.pass_reward
            reward_terms["pass_reward"] = self.config.obstacle.pass_reward
        if self.collision:
            reward -= self.config.obstacle.collision_penalty
            reward_terms["collision_penalty"] = self.config.obstacle.collision_penalty
        if terminated and self.config.termination_penalty > 0.0:
            reward -= self.config.termination_penalty
            reward_terms["termination_penalty"] = self.config.termination_penalty
        truncated = self.obstacle_completed or self.step_count >= self.config.max_steps
        self.last_action = np.clip(action64, -1.0, 1.0)

        info = self._info(frame)
        info["reward_terms"] = reward_terms
        base_observation = self._base_observation()
        self.obs_history = [base_observation] + self.obs_history[: self.config.history_length - 1]
        return self._observation(), float(reward), terminated, truncated, info

    def _sample_friction_step_at(self) -> int | None:
        if not self.config.friction_step.enabled:
            return None
        low, high = self.config.friction_step.step_range
        low = max(1, int(low))
        high = min(int(high), self.config.max_steps - 1)
        if high <= low:
            return low
        return int(self.rng.integers(low, high + 1))

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
        self.min_obstacle_clearance = float("inf")
        self.collision = False
        self.obstacle_completed = False
        if not self.config.obstacle.enabled:
            return
        scenario_config = self.config.obstacle.scenario_config(speed=self.speed_ref, mu=self.params.mu)
        scenario = None
        for _ in range(max(1, self.config.obstacle.max_sample_attempts)):
            obstacle_distance = float(self.rng.uniform(*self.config.obstacle.distance_range))
            obstacle_half_width = float(self.rng.uniform(*self.config.obstacle.half_width_range))
            scenario = classify_obstacle_scenario(
                speed=self.speed_ref,
                mu=self.params.mu,
                obstacle_distance=obstacle_distance,
                obstacle_half_width=obstacle_half_width,
                config=scenario_config,
            )
            if not self.config.obstacle.require_aeb_infeasible or scenario.label != "aeb_feasible":
                break
        if scenario is None or (self.config.obstacle.require_aeb_infeasible and scenario.label == "aeb_feasible"):
            raise RuntimeError("failed to sample an AEB-infeasible obstacle scenario")
        self.obstacle_scenario = scenario
        self.obstacle_position = position + frame.tangent * obstacle_distance
        self._update_obstacle_status(frame)

    def _obstacle_features(self, frame: PathFrame) -> tuple[float, float, float, float, float]:
        if self.obstacle_scenario is None or self.obstacle_position is None:
            return (0.0, 0.0, 0.0, 0.0, 0.0)
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
            self.obstacle_scenario.aeb_stop_distance / 80.0,
        )

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

    def _observation(self) -> np.ndarray:
        if not self.obs_history:
            base_observation = self._base_observation()
            return np.tile(base_observation, self.config.history_length).astype(np.float32)
        return np.concatenate(self.obs_history).astype(np.float32)

    def _base_observation(self) -> np.ndarray:
        frame = self.track.frame(self.state.x, self.state.y, self.state.psi)
        speed = math.hypot(self.state.vx, self.state.vy)
        beta = math.atan2(self.state.vy, max(self.state.vx, 1e-6))
        global_vx = self.state.vx * math.cos(self.state.psi) - self.state.vy * math.sin(self.state.psi)
        global_vy = self.state.vx * math.sin(self.state.psi) + self.state.vy * math.cos(self.state.psi)
        along_speed = float(np.dot(np.array([global_vx, global_vy]), frame.tangent))

        obs = [
            self.state.vx / 20.0,
            self.state.vy / 12.0,
            self.state.yaw_rate / 2.5,
            beta,
            self.state.steer / self.params.max_steer,
            self.state.drive_force / max(self.params.max_drive_force, self.params.max_brake_force),
            frame.lateral_error / self.config.track_width,
            frame.heading_error,
            frame.curvature * 20.0,
            along_speed / 20.0,
            self.speed_ref / 20.0,
            self.beta_target,
            self.last_action[1],
        ]
        if self.config.obstacle.enabled:
            obs.extend(self._obstacle_features(frame))
        if self.config.include_privileged_params:
            obs.extend(
                [
                    self.params.mu,
                    self.params.mass / VehicleParams().mass,
                    self.params.lf / VehicleParams().lf,
                    self.params.cr / VehicleParams().cr,
                ]
            )
        return np.asarray(obs, dtype=np.float32)

    def _reward(
        self,
        frame: PathFrame,
        action: np.ndarray,
        forces: TireForces,
    ) -> tuple[float, dict[str, float]]:
        speed = math.hypot(self.state.vx, self.state.vy)
        beta = math.atan2(self.state.vy, max(self.state.vx, 1e-6))
        global_vx = self.state.vx * math.cos(self.state.psi) - self.state.vy * math.sin(self.state.psi)
        global_vy = self.state.vx * math.sin(self.state.psi) + self.state.vy * math.cos(self.state.psi)
        along_speed = float(np.dot(np.array([global_vx, global_vy]), frame.tangent))

        track_cost = (frame.lateral_error / self.config.track_width) ** 2
        heading_cost = wrap_pi(frame.heading_error) ** 2
        speed_cost = ((speed - self.speed_ref) / max(self.speed_ref, 1.0)) ** 2
        beta_cost = (abs(beta) - self.beta_target) ** 2
        action_cost = float(np.sum(np.square(action)))
        action_rate_cost = float(np.sum(np.square(action - self.last_action)))
        rear_saturation = abs(forces.fx_rear) / max(self.params.mu * forces.fz_rear, 1.0)
        drift_bonus = min(abs(beta) / max(self.beta_target, 1e-3), 1.5)
        progress_reward = along_speed / max(self.speed_ref, 1.0)

        reward = (
            1.1 * progress_reward
            + 0.18 * drift_bonus
            + 0.10 * rear_saturation
            - 2.4 * track_cost
            - 0.25 * heading_cost
            - 0.40 * speed_cost
            - 0.70 * beta_cost
            - 0.030 * action_cost
            - 0.040 * action_rate_cost
        )
        terms = {
            "progress": progress_reward,
            "drift_bonus": drift_bonus,
            "rear_saturation": rear_saturation,
            "track_cost": track_cost,
            "heading_cost": heading_cost,
            "speed_cost": speed_cost,
            "beta_cost": beta_cost,
        }
        return reward, terms

    def _terminated(self, frame: PathFrame) -> bool:
        speed = math.hypot(self.state.vx, self.state.vy)
        values = self.state.as_array()
        if not np.all(np.isfinite(values)):
            return True
        if abs(frame.lateral_error) > self.config.track_width:
            return True
        if self.collision:
            return True
        if speed < 1.0 or speed > 32.0:
            return True
        if abs(self.state.yaw_rate) > 6.0:
            return True
        return False

    def _info(self, frame: PathFrame) -> dict[str, Any]:
        speed = math.hypot(self.state.vx, self.state.vy)
        beta = math.atan2(self.state.vy, max(self.state.vx, 1e-6))
        return {
            "mu": self.params.mu,
            "initial_mu": self.initial_mu,
            "mass": self.params.mass,
            "lf": self.params.lf,
            "lr": self.params.lr,
            "speed": speed,
            "beta": beta,
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
            "obstacle_label": self.obstacle_scenario.label if self.obstacle_scenario is not None else "",
            "obstacle_distance": self._obstacle_features(frame)[0] * 80.0 if self.config.obstacle.enabled else float("nan"),
            "obstacle_lateral_offset": (
                self._obstacle_features(frame)[1] * self.config.track_width if self.config.obstacle.enabled else float("nan")
            ),
            "obstacle_required_lateral_offset": (
                self.obstacle_scenario.required_lateral_offset if self.obstacle_scenario is not None else float("nan")
            ),
            "min_obstacle_clearance": self.min_obstacle_clearance if self.config.obstacle.enabled else float("nan"),
            "collision": self.collision,
            "obstacle_completed": self.obstacle_completed,
        }
