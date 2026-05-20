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
from autodrift.tasks import CircleTrack, PathFrame


@dataclass(frozen=True)
class DriftEnvConfig:
    dt: float = 0.02
    max_steps: int = 800
    track_radius: float = 18.0
    track_width: float = 5.0
    speed_range: tuple[float, float] = (5.0, 12.0)
    beta_target_range: tuple[float, float] = (0.32, 0.70)
    friction_limited_speed: bool = True
    friction_speed_margin: float = 0.92
    history_length: int = 1
    include_privileged_params: bool = False
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

        self.base_obs_dim = 13 + (4 if self.config.include_privileged_params else 0)
        obs_dim = self.base_obs_dim * self.config.history_length
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32)

        self.track = CircleTrack(radius=self.config.track_radius)
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
        self.model = SingleTrackDriftModel(self.params)

        self.speed_ref = self._sample_speed_ref()
        self.beta_target = float(self.rng.uniform(*self.config.beta_target_range))
        initial_beta = float(self.rng.normal(0.0, 0.04))
        x, y, psi, vx, vy = self.track.reset_pose(self.rng, self.speed_ref, beta=initial_beta)
        self.state = VehicleState(
            x=x,
            y=y,
            psi=psi,
            vx=vx,
            vy=vy,
            yaw_rate=self.speed_ref / self.config.track_radius,
            steer=0.0,
            drive_force=0.0,
        )
        self.last_action = np.zeros(2, dtype=np.float64)
        self.last_forces = self.model.tire_forces(vx, vy, self.state.yaw_rate, 0.0, 0.0)
        base_observation = self._base_observation()
        self.obs_history = [base_observation.copy() for _ in range(self.config.history_length)]
        self.step_count = 0

        return self._observation(), self._info(self.track.frame(self.state.x, self.state.y, self.state.psi))

    def _sample_speed_ref(self) -> float:
        low, high = self.config.speed_range
        if self.config.friction_limited_speed:
            friction_speed = math.sqrt(max(self.params.mu * self.params.gravity * self.config.track_radius, 1e-6))
            high = min(high, friction_speed * self.config.friction_speed_margin)
        if high <= low:
            return float(max(high, 1.0))
        return float(self.rng.uniform(low, high))

    def step(self, action: np.ndarray) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        self.step_count += 1
        action64 = np.asarray(action, dtype=np.float64)
        self.state, self.last_forces = self.model.step(self.state, action64, self.config.dt)
        frame = self.track.frame(self.state.x, self.state.y, self.state.psi)
        reward, reward_terms = self._reward(frame, action64, self.last_forces)

        terminated = self._terminated(frame)
        truncated = self.step_count >= self.config.max_steps
        self.last_action = np.clip(action64, -1.0, 1.0)

        info = self._info(frame)
        info["reward_terms"] = reward_terms
        base_observation = self._base_observation()
        self.obs_history = [base_observation] + self.obs_history[: self.config.history_length - 1]
        return self._observation(), float(reward), terminated, truncated, info

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
            "mass": self.params.mass,
            "lf": self.params.lf,
            "lr": self.params.lr,
            "speed": speed,
            "beta": beta,
            "beta_target": self.beta_target,
            "speed_ref": self.speed_ref,
            "lateral_error": frame.lateral_error,
            "heading_error": frame.heading_error,
            "step": self.step_count,
        }
