"""Baseline policies for sanity checks and early comparisons."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from autodrift.env import AutoDriftEnv


def split_drive_brake_action(steer: float, drive_brake: float) -> np.ndarray:
    steer_cmd = float(np.clip(steer, -1.0, 1.0))
    drive_brake_cmd = float(np.clip(drive_brake, -1.0, 1.0))
    if drive_brake_cmd >= 0.0:
        throttle = 2.0 * drive_brake_cmd - 1.0
        brake = -1.0
    else:
        throttle = -1.0
        brake = 2.0 * (-drive_brake_cmd) - 1.0
    return np.array([steer_cmd, float(np.clip(throttle, -1.0, 1.0)), float(np.clip(brake, -1.0, 1.0))], dtype=np.float32)


class Policy:
    def reset(self) -> None:
        pass

    def act(self, observation: np.ndarray, info: dict) -> np.ndarray:
        raise NotImplementedError


class RandomPolicy(Policy):
    def __init__(self, seed: int | None = None):
        self.rng = np.random.default_rng(seed)

    def act(self, observation: np.ndarray, info: dict) -> np.ndarray:
        return self.rng.uniform(-1.0, 1.0, size=3).astype(np.float32)


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
        lateral_error = float(info.get("lateral_error", 0.0)) / 5.0
        heading_error = float(info.get("heading_error", 0.0))
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
        return split_drive_brake_action(steer, throttle)


class AEBPolicy(Policy):
    """Full braking baseline."""

    def act(self, observation: np.ndarray, info: dict) -> np.ndarray:
        del observation, info
        return np.array([0.0, -1.0, 1.0], dtype=np.float32)


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
            return split_drive_brake_action(0.0, brake)

        required_offset = float(info.get("obstacle_required_lateral_offset", 2.0))
        lateral_offset = float(info.get("obstacle_lateral_offset", 0.0))
        # Pick one side deterministically. If the obstacle is already left of
        # the ego vehicle, steer right; otherwise steer left.
        desired_lateral = -required_offset if lateral_offset > 0.0 else required_offset
        current_lateral = float(info.get("lateral_error", 0.0))
        urgency = np.clip(1.0 - obstacle_distance / max(self.obstacle_trigger_distance, 1.0), 0.0, 1.0)
        steer = self.steer_gain * urgency + self.lateral_gain * (desired_lateral - current_lateral)
        brake = -0.9 if vx > 6.0 else -0.3
        return split_drive_brake_action(steer, brake)


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
            return split_drive_brake_action(0.0, -0.5)

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
        return split_drive_brake_action(steer, throttle)


@dataclass
class HonestAESPolicy(Policy):
    """HONEST production-style emergency braking+steering, using ONLY realistic inputs.

    Unlike EnvelopeAESPolicy (which reads the TRUE mu, the precomputed exact
    required-offset, AND the ground-truth obstacle_label), this baseline mirrors
    what a real ESC/AEB/AES stack actually has:
      - perception of the obstacle's CURRENT position (distance + lateral offset),
        which a radar/camera genuinely measures;
      - the ego's own lane error and speed;
      - a FIXED ASSUMED friction (it does NOT know the true mu);
      - NO scenario label.
    Crucially it is GRIP-RESPECTING: the commanded lateral accel is capped at the
    assumed friction budget, so it NEVER intentionally drifts (real active safety
    prevents slip). On cells that genuinely require exceeding the conventional
    envelope (true drift_required), it cannot succeed -- by construction.
    """

    assumed_mu: float = 0.55         # a fixed conservative assumption; NOT the true mu
    conventional_grip_fraction: float = 0.50   # only HALF the assumed grip -> stays below slip (ESC-like)
    steer_cap: float = 0.55          # hard cap on steering -> never aggressive enough to break traction
    lateral_margin: float = 0.35
    max_ttc: float = 2.5

    def act(self, observation: np.ndarray, info: dict) -> np.ndarray:
        vx = float(observation[0] * 20.0)
        vy = float(observation[1] * 12.0)
        speed = max(math.hypot(vx, vy), 1.0)
        obstacle_distance = float(info.get("obstacle_distance", float("inf")))
        # RIGOROUS perception contract: react to the obstacle ONLY when it is perception-visible
        # (same gate the RL's observation uses, env._obstacle_perception_visible). Forbidden fields
        # (never read here): mu (true friction), obstacle_label, obstacle_required_lateral_offset,
        # obstacle_predicted_lateral_offset_at_arrival.
        perceived = bool(info.get("obstacle_perception_visible", info.get("obstacle_enabled", False)))
        if not perceived or obstacle_distance <= 0.0 or not math.isfinite(obstacle_distance):
            return split_drive_brake_action(0.0, -0.6)   # no obstacle perceived -> ease off
        # realistic perception of the obstacle's current lateral position + own lane error
        obstacle_lateral = float(info.get("obstacle_lateral_offset", 0.0))
        lateral_error = float(info.get("lateral_error", 0.0))
        # steer toward the open side; target a clearance from the perceived obstacle (own width + margin)
        target_sign = -1.0 if obstacle_lateral >= 0.0 else 1.0
        desired_lateral = target_sign * (1.0 + self.lateral_margin)  # ~ego half-width + margin (perceived)
        ttc = float(np.clip(obstacle_distance / speed, 0.05, self.max_ttc))
        lateral_accel_need = 2.0 * abs(desired_lateral - lateral_error) / max(ttc ** 2, 1e-3)
        grip_budget = self.conventional_grip_fraction * self.assumed_mu * 9.81   # ASSUMED, grip-respecting
        # GRIP CAP at 1.0 -> never command beyond the (assumed) friction limit -> never drifts
        accel_fraction = float(np.clip(lateral_accel_need / max(grip_budget, 1e-6), 0.0, 1.0))
        steer = target_sign * float(np.clip(0.30 + 0.70 * accel_fraction, 0.0, self.steer_cap))  # hard cap -> stays stable
        brake = -0.9 if vx > 6.0 else -0.4   # always brake hard (production AEB), never keep throttle to drift
        return split_drive_brake_action(steer, brake)


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
    if normalized in {"honest_aes", "honest"}:
        return HonestAESPolicy()
    raise ValueError(f"unknown policy: {name}")
