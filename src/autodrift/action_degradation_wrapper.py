"""Action-side degradation wrapper for AutoDriftEnv (Phase-2 plan S1 axis).

Models two production actuation effects on the COMMAND path (the observation
path is untouched; combine with ``ObservationDegradationWrapper`` for sensing
degradation):

- **Actuator delay** (``action_delay_steps=k``): the env executes at step ``t``
  the command issued at step ``t-k``. Before the first issued command reaches
  the actuator, the NEUTRAL action ``[0, 0, 0]`` (zero steer, zero throttle,
  zero brake) is executed; this mirrors brake-hydraulics / drive-by-wire bus
  latency where the plant simply has not received the new command yet.
- **Slew-rate limit** (``slew_rate_limit``): the executed action can change by
  at most this amount PER ENV STEP on each channel (scalar or per-channel
  length-3 sequence), applied AFTER the delay queue. The executed-action state
  is initialized at the neutral action on every reset.

Interpretation contract (mirrors the observation wrapper): this defines a NEW
TASK FAMILY and must be applied identically at training and evaluation time.
The wrapper is deterministic (no RNG): identical seeds and command sequences
reproduce identical trajectories bit for bit.

Deployability note (plan WP0): enabling this axis weakens the dead-reckoning
legitimacy of the clean-sensing oracle anchor — re-examine WP1 anchors before
using it in regime measurements.

Defaults (``action_delay_steps=0``, ``slew_rate_limit=None``) are a structural
pass-through: ``step`` forwards the caller's action object to the inner env
untouched, so default behavior is bit-for-bit unchanged.

This wrapper is intentionally NOT part of the ``DriftEnvConfig`` /
``observation_degradation`` schema; wiring it into config-driven entry points
is a separate, explicitly registered decision.
"""

from __future__ import annotations

from collections import deque
from typing import Any

import gymnasium as gym
import numpy as np

from autodrift.env import AutoDriftEnv

ACTION_DIM = 3
NEUTRAL_ACTION: tuple[float, float, float] = (0.0, 0.0, 0.0)


def _slew_limit_vector(value: float | tuple | list | np.ndarray | None) -> np.ndarray | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("slew_rate_limit must be a positive number, a length-3 sequence, or None")
    values = np.asarray(value, dtype=np.float64)
    if values.ndim == 0:
        values = np.full(ACTION_DIM, float(values), dtype=np.float64)
    if values.shape != (ACTION_DIM,):
        raise ValueError(
            f"slew_rate_limit must be a scalar or a length-{ACTION_DIM} per-channel sequence, "
            f"got shape {values.shape}"
        )
    if not np.all(np.isfinite(values)) or np.any(values <= 0.0):
        raise ValueError(
            "slew_rate_limit values must be finite and positive (use None to disable)"
        )
    return values


class ActionDegradationWrapper(gym.Wrapper):
    """Actuator delay + slew-rate limit on the AutoDriftEnv command path."""

    def __init__(
        self,
        env: gym.Env,
        *,
        action_delay_steps: int = 0,
        slew_rate_limit: float | tuple | list | np.ndarray | None = None,
    ):
        super().__init__(env)
        base_env = env.unwrapped
        if not isinstance(base_env, AutoDriftEnv):
            raise TypeError("ActionDegradationWrapper requires an AutoDriftEnv")
        if isinstance(action_delay_steps, bool) or not isinstance(action_delay_steps, (int, np.integer)):
            raise ValueError("action_delay_steps must be an integer")
        if int(action_delay_steps) < 0:
            raise ValueError("action_delay_steps must be non-negative")

        self.action_delay_steps = int(action_delay_steps)
        self.slew_rate_limit = _slew_limit_vector(slew_rate_limit)
        # Structural pass-through flag: when False, step() forwards the action
        # object untouched (default behavior bit-for-bit unchanged).
        self._active = self.action_delay_steps > 0 or self.slew_rate_limit is not None

        self._neutral = np.asarray(NEUTRAL_ACTION, dtype=np.float64)
        self._command_queue: deque[np.ndarray] = deque()
        self.last_executed_action: np.ndarray = self._neutral.copy()

    # -- gym API ---------------------------------------------------------------

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        observation, info = self.env.reset(seed=seed, options=options)
        self._command_queue = deque(
            self._neutral.copy() for _ in range(self.action_delay_steps)
        )
        self.last_executed_action = self._neutral.copy()
        return observation, info

    def step(self, action: np.ndarray):
        if not self._active:
            return self.env.step(action)
        command = np.asarray(action, dtype=np.float64).reshape(ACTION_DIM).copy()
        self._command_queue.append(command)
        delayed = self._command_queue.popleft()
        if self.slew_rate_limit is None:
            executed = delayed
        else:
            delta = np.clip(
                delayed - self.last_executed_action,
                -self.slew_rate_limit,
                self.slew_rate_limit,
            )
            executed = self.last_executed_action + delta
        self.last_executed_action = executed.copy()
        return self.env.step(executed)


def make_action_degradation_env(
    config,
    *,
    action_delay_steps: int = 0,
    slew_rate_limit: float | tuple | list | np.ndarray | None = None,
) -> ActionDegradationWrapper:
    """Build an AutoDriftEnv wrapped with command-path degradation."""

    return ActionDegradationWrapper(
        AutoDriftEnv(config),
        action_delay_steps=action_delay_steps,
        slew_rate_limit=slew_rate_limit,
    )
