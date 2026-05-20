"""Baseline policies for sanity checks and early comparisons."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from autodrift.env import AutoDriftEnv


class Policy:
    def reset(self) -> None:
        pass

    def act(self, observation: np.ndarray, info: dict) -> np.ndarray:
        raise NotImplementedError


class RandomPolicy(Policy):
    def __init__(self, seed: int | None = None):
        self.rng = np.random.default_rng(seed)

    def act(self, observation: np.ndarray, info: dict) -> np.ndarray:
        return self.rng.uniform(-1.0, 1.0, size=2).astype(np.float32)


@dataclass
class HeuristicPolicy(Policy):
    """A weak controller used to verify the environment is not degenerate."""

    steer_gain_error: float = 0.95
    steer_gain_heading: float = 0.75
    steer_gain_beta: float = 0.55
    speed_gain: float = 0.75
    drift_bias: float = 0.18

    def act(self, observation: np.ndarray, info: dict) -> np.ndarray:
        vx = float(observation[0] * 20.0)
        vy = float(observation[1] * 12.0)
        beta = math.atan2(vy, max(vx, 1e-6))
        lateral_error = float(observation[5])
        heading_error = float(observation[6])
        speed_ref = float(info.get("speed_ref", 8.0))
        beta_target = float(info.get("beta_target", 0.4))
        speed = max(math.hypot(vx, vy), 1e-6)

        desired_beta_sign = -1.0 if heading_error > 0.0 else 1.0
        beta_error = beta - desired_beta_sign * beta_target
        steer = (
            -self.steer_gain_error * lateral_error
            - self.steer_gain_heading * heading_error
            - self.steer_gain_beta * beta_error
        )
        throttle = self.speed_gain * (speed_ref - speed) / max(speed_ref, 1.0) + self.drift_bias
        return np.array([np.clip(steer, -1.0, 1.0), np.clip(throttle, -1.0, 1.0)], dtype=np.float32)


class AEBPolicy(Policy):
    """Full braking baseline."""

    def act(self, observation: np.ndarray, info: dict) -> np.ndarray:
        del observation, info
        return np.array([0.0, -1.0], dtype=np.float32)


@dataclass
class HeuristicAESPolicy(Policy):
    """Simple emergency steering baseline with braking."""

    obstacle_trigger_distance: float = 35.0
    steer_gain: float = 1.2
    lateral_gain: float = 0.35

    def act(self, observation: np.ndarray, info: dict) -> np.ndarray:
        vx = float(observation[0] * 20.0)
        obstacle_distance = float(info.get("obstacle_distance", float("inf")))
        if not info.get("obstacle_enabled", False) or obstacle_distance <= 0.0:
            brake = -0.7
            return np.array([0.0, brake], dtype=np.float32)

        required_offset = float(info.get("obstacle_required_lateral_offset", 2.0))
        lateral_offset = float(info.get("obstacle_lateral_offset", 0.0))
        # Pick one side deterministically. If the obstacle is already left of
        # the ego vehicle, steer right; otherwise steer left.
        desired_lateral = -required_offset if lateral_offset > 0.0 else required_offset
        current_lateral = float(info.get("lateral_error", 0.0))
        urgency = np.clip(1.0 - obstacle_distance / max(self.obstacle_trigger_distance, 1.0), 0.0, 1.0)
        steer = self.steer_gain * urgency + self.lateral_gain * (desired_lateral - current_lateral)
        brake = -0.9 if vx > 6.0 else -0.3
        return np.array([np.clip(steer, -1.0, 1.0), np.clip(brake, -1.0, 1.0)], dtype=np.float32)


@dataclass
class EnvelopeAESPolicy(Policy):
    """Friction-envelope emergency steering baseline."""

    lateral_margin: float = 0.35
    max_ttc: float = 2.5

    def act(self, observation: np.ndarray, info: dict) -> np.ndarray:
        vx = float(observation[0] * 20.0)
        vy = float(observation[1] * 12.0)
        speed = max(math.hypot(vx, vy), 1.0)
        obstacle_distance = float(info.get("obstacle_distance", float("inf")))
        if not info.get("obstacle_enabled", False) or obstacle_distance <= 0.0:
            return np.array([0.0, -0.5], dtype=np.float32)

        mu = max(float(info.get("mu", 0.6)), 0.05)
        required_offset = float(info.get("obstacle_required_lateral_offset", 2.0)) + self.lateral_margin
        obstacle_lateral = float(info.get("obstacle_lateral_offset", 0.0))
        target_sign = -1.0 if obstacle_lateral > 0.0 else 1.0
        lateral_error = float(info.get("lateral_error", 0.0))
        desired_lateral = target_sign * required_offset
        ttc = np.clip(obstacle_distance / speed, 0.05, self.max_ttc)
        lateral_accel_need = 2.0 * abs(desired_lateral - lateral_error) / max(ttc**2, 1e-3)
        accel_fraction = np.clip(lateral_accel_need / max(mu * 9.81, 1e-6), 0.0, 1.5)
        steer = target_sign * np.clip(0.35 + 0.65 * accel_fraction, 0.0, 1.0)
        # Keep speed through drift-required cases; brake only when the envelope
        # says conventional steering should already be enough.
        label = str(info.get("obstacle_label", ""))
        throttle = -0.2 if label == "aes_feasible" else 0.15
        return np.array([np.clip(steer, -1.0, 1.0), np.clip(throttle, -1.0, 1.0)], dtype=np.float32)


def make_policy(name: str, env: AutoDriftEnv, seed: int | None = None) -> Policy:
    del env
    normalized = name.lower()
    if normalized == "random":
        return RandomPolicy(seed=seed)
    if normalized == "heuristic":
        return HeuristicPolicy()
    if normalized == "aeb":
        return AEBPolicy()
    if normalized in {"aes", "aes_heuristic"}:
        return HeuristicAESPolicy()
    if normalized in {"envelope_aes", "model_aes"}:
        return EnvelopeAESPolicy()
    raise ValueError(f"unknown policy: {name}")
