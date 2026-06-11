"""Action-side degradation wrapper (S1 axis): actuator delay + slew-rate limit.

Pre-registered acceptance criteria:

1. Loud ValueError/TypeError validation of all parameters.
2. Defaults are a structural pass-through (the action object is forwarded
   untouched; trajectories bitwise identical to a bare AutoDriftEnv).
3. Actuator delay: the trajectory under ``action_delay_steps=k`` is bitwise
   identical to a bare env driven by the explicitly shifted command sequence
   (k leading neutral actions).
4. Slew-rate limit: the executed action ramps at most ``limit`` per step per
   channel; trajectory bitwise identical to a bare env driven by the manually
   slew-limited sequence; per-channel limits honored.
5. Delay + slew compose in the documented order (delay queue first, then slew).

Infrastructure tests only; no capability claim.
"""

from __future__ import annotations

from dataclasses import replace

import gymnasium as gym
import numpy as np
import pytest

from autodrift.action_degradation_wrapper import (
    ACTION_DIM,
    ActionDegradationWrapper,
    make_action_degradation_env,
)
from autodrift.env import AutoDriftEnv, DriftEnvConfig


def _base_config(**overrides) -> DriftEnvConfig:
    return replace(DriftEnvConfig(), **overrides)


def _action_sequence(steps: int, seed: int = 7, scale: float = 0.4) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    return [rng.uniform(-scale, scale, ACTION_DIM).astype(np.float64) for _ in range(steps)]


def _rollout(env, seed: int, actions: list[np.ndarray]):
    obs, _ = env.reset(seed=seed)
    frames = [np.asarray(obs, dtype=np.float32).copy()]
    rewards: list[float] = []
    for action in actions:
        obs, reward, terminated, truncated, _ = env.step(action)
        frames.append(np.asarray(obs, dtype=np.float32).copy())
        rewards.append(float(reward))
        if terminated or truncated:
            break
    return frames, rewards


def _assert_rollouts_bitwise_equal(result_a, result_b) -> None:
    frames_a, rewards_a = result_a
    frames_b, rewards_b = result_b
    assert rewards_a == rewards_b
    assert len(frames_a) == len(frames_b)
    for frame_a, frame_b in zip(frames_a, frames_b, strict=True):
        np.testing.assert_array_equal(frame_a, frame_b)


def _manual_slew(commands: list[np.ndarray], limit: np.ndarray) -> list[np.ndarray]:
    executed: list[np.ndarray] = []
    last = np.zeros(ACTION_DIM, dtype=np.float64)
    for command in commands:
        last = last + np.clip(np.asarray(command, dtype=np.float64) - last, -limit, limit)
        executed.append(last.copy())
    return executed


# ---------------------------------------------------------------------------
# 1. loud validation
# ---------------------------------------------------------------------------


def test_invalid_parameters_are_rejected() -> None:
    config = _base_config()
    with pytest.raises(ValueError, match="action_delay_steps must be non-negative"):
        make_action_degradation_env(config, action_delay_steps=-1)
    with pytest.raises(ValueError, match="action_delay_steps must be an integer"):
        make_action_degradation_env(config, action_delay_steps=1.5)
    with pytest.raises(ValueError, match="action_delay_steps must be an integer"):
        make_action_degradation_env(config, action_delay_steps=True)
    with pytest.raises(ValueError, match="finite and positive"):
        make_action_degradation_env(config, slew_rate_limit=0.0)
    with pytest.raises(ValueError, match="finite and positive"):
        make_action_degradation_env(config, slew_rate_limit=-0.1)
    with pytest.raises(ValueError, match="finite and positive"):
        make_action_degradation_env(config, slew_rate_limit=float("inf"))
    with pytest.raises(ValueError, match=f"length-{ACTION_DIM}"):
        make_action_degradation_env(config, slew_rate_limit=[0.1, 0.1])
    with pytest.raises(ValueError, match="slew_rate_limit"):
        make_action_degradation_env(config, slew_rate_limit=True)
    with pytest.raises(ValueError):
        make_action_degradation_env(config, slew_rate_limit="fast")

    class _NotAutoDrift(gym.Env):
        observation_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32)
        action_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32)

    with pytest.raises(TypeError, match="AutoDriftEnv"):
        ActionDegradationWrapper(_NotAutoDrift())


# ---------------------------------------------------------------------------
# 2. defaults: structural pass-through
# ---------------------------------------------------------------------------


def test_defaults_are_bitwise_passthrough_and_skip_transform_path() -> None:
    config = _base_config()
    actions = _action_sequence(30, seed=5)
    wrapper = make_action_degradation_env(config)
    assert wrapper._active is False
    _assert_rollouts_bitwise_equal(
        _rollout(wrapper, seed=404, actions=actions),
        _rollout(AutoDriftEnv(config), seed=404, actions=actions),
    )
    # structural guarantee: the transform state is never consulted by defaults
    assert len(wrapper._command_queue) == 0


# ---------------------------------------------------------------------------
# 3. actuator delay
# ---------------------------------------------------------------------------


def test_action_delay_matches_explicitly_shifted_command_sequence() -> None:
    config = _base_config()
    k = 3
    actions = _action_sequence(25, seed=9)
    shifted = [np.zeros(ACTION_DIM, dtype=np.float64)] * k + actions[: len(actions) - k]
    _assert_rollouts_bitwise_equal(
        _rollout(make_action_degradation_env(config, action_delay_steps=k), seed=606, actions=actions),
        _rollout(AutoDriftEnv(config), seed=606, actions=shifted),
    )


def test_action_delay_actually_changes_the_trajectory() -> None:
    config = _base_config()
    actions = _action_sequence(25, seed=9)
    delayed_frames, _ = _rollout(
        make_action_degradation_env(config, action_delay_steps=5), seed=606, actions=actions
    )
    bare_frames, _ = _rollout(AutoDriftEnv(config), seed=606, actions=actions)
    assert any(
        not np.array_equal(frame_a, frame_b)
        for frame_a, frame_b in zip(delayed_frames, bare_frames)
    )


# ---------------------------------------------------------------------------
# 4. slew-rate limit
# ---------------------------------------------------------------------------


def test_slew_rate_limits_executed_action_ramp() -> None:
    config = _base_config()
    limit = 0.05
    env = make_action_degradation_env(config, slew_rate_limit=limit)
    env.reset(seed=11)
    command = np.array([1.0, 1.0, 0.0], dtype=np.float64)
    previous = np.zeros(ACTION_DIM, dtype=np.float64)
    for step in range(1, 6):
        env.step(command)
        executed = env.last_executed_action
        np.testing.assert_allclose(executed - previous, np.clip(command - previous, -limit, limit))
        assert np.all(np.abs(executed - previous) <= limit + 1e-12)
        np.testing.assert_allclose(executed[:2], min(step * limit, 1.0))
        previous = executed.copy()


def test_slew_rate_trajectory_matches_manually_limited_sequence() -> None:
    config = _base_config()
    limit_vec = np.array([0.05, 0.2, 0.1], dtype=np.float64)
    actions = _action_sequence(25, seed=15)
    _assert_rollouts_bitwise_equal(
        _rollout(
            make_action_degradation_env(config, slew_rate_limit=limit_vec), seed=707, actions=actions
        ),
        _rollout(AutoDriftEnv(config), seed=707, actions=_manual_slew(actions, limit_vec)),
    )


def test_per_channel_slew_limits_are_honored_independently() -> None:
    config = _base_config()
    limit_vec = np.array([0.01, 0.5, 0.25], dtype=np.float64)
    env = make_action_degradation_env(config, slew_rate_limit=limit_vec)
    env.reset(seed=21)
    env.step(np.array([1.0, 1.0, 1.0], dtype=np.float64))
    np.testing.assert_allclose(env.last_executed_action, limit_vec)


# ---------------------------------------------------------------------------
# 5. composition: delay queue first, then slew limit
# ---------------------------------------------------------------------------


def test_delay_then_slew_composition_matches_manual_pipeline() -> None:
    config = _base_config()
    k = 2
    limit = np.full(ACTION_DIM, 0.07, dtype=np.float64)
    actions = _action_sequence(30, seed=33)
    shifted = [np.zeros(ACTION_DIM, dtype=np.float64)] * k + actions[: len(actions) - k]
    _assert_rollouts_bitwise_equal(
        _rollout(
            make_action_degradation_env(config, action_delay_steps=k, slew_rate_limit=limit),
            seed=909,
            actions=actions,
        ),
        _rollout(AutoDriftEnv(config), seed=909, actions=_manual_slew(shifted, limit)),
    )


def test_wrapper_is_deterministic_and_reset_clears_state() -> None:
    config = _base_config()
    actions = _action_sequence(20, seed=44)
    env = make_action_degradation_env(config, action_delay_steps=2, slew_rate_limit=0.1)
    first = _rollout(env, seed=123, actions=actions)
    second = _rollout(env, seed=123, actions=actions)  # same env object, fresh reset
    _assert_rollouts_bitwise_equal(first, second)
