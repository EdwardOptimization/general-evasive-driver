"""Smoke tests for the observation-degradation task wrapper and self-ID positive-control configs.

These tests verify infrastructure correctness only (delay indexing, noise
determinism, channel isolation, config executability). They make no
self-identification or capability claim.
"""

from __future__ import annotations

import json
from dataclasses import fields, replace
from pathlib import Path

import gymnasium as gym
import numpy as np
import pytest

from autodrift.config import build_env_config
from autodrift.env import AutoDriftEnv, DriftEnvConfig, EGO_OBS_DIM, ObstacleTaskConfig
from autodrift.observation_degradation_wrapper import (
    DEGRADED_EGO_RESPONSE_INDICES,
    OBS72_INDEX_TABLE,
    ObservationDegradationWrapper,
    make_observation_degradation_env,
)
from autodrift.train_ppo import PPOConfig, train

REPO_ROOT = Path(__file__).resolve().parents[1]
PRIVILEGED_CONFIG = REPO_ROOT / "configs" / "selfid_positive_control_privileged_smoke.json"
P0_CONFIG = REPO_ROOT / "configs" / "selfid_positive_control_p0_smoke.json"


def _base_config(**overrides) -> DriftEnvConfig:
    return replace(DriftEnvConfig(), **overrides)


def _action_sequence(steps: int, seed: int = 7) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    return [rng.uniform(-0.4, 0.4, 3).astype(np.float64) for _ in range(steps)]


def _rollout(env, seed: int, actions: list[np.ndarray]) -> list[np.ndarray]:
    obs, _ = env.reset(seed=seed)
    frames = [np.asarray(obs, dtype=np.float32).copy()]
    for action in actions:
        obs, _, terminated, truncated, _ = env.step(action)
        frames.append(np.asarray(obs, dtype=np.float32).copy())
        if terminated or truncated:
            break
    return frames


def test_index_table_matches_default_env_layout() -> None:
    env = AutoDriftEnv(_base_config())
    assert env.base_obs_dim == 72
    assert DEGRADED_EGO_RESPONSE_INDICES == tuple(range(9))
    assert OBS72_INDEX_TABLE["ego_response"]["indices"] == list(range(0, 9))
    assert OBS72_INDEX_TABLE["previous_command"]["indices"] == list(range(9, 12))
    assert OBS72_INDEX_TABLE["road_boundary_left"]["indices"][0] == 12
    assert OBS72_INDEX_TABLE["obstacle_slots"]["indices"][-1] == 71
    assert EGO_OBS_DIM == 9

    privileged = AutoDriftEnv(_base_config(include_privileged_params=True))
    assert privileged.base_obs_dim == 76
    assert OBS72_INDEX_TABLE["privileged_basic_optional"]["indices"] == list(range(72, 76))


def test_delay_returns_ego_channels_from_k_steps_ago() -> None:
    config = _base_config()
    k = 3
    actions = _action_sequence(12)
    raw_frames = _rollout(AutoDriftEnv(config), seed=123, actions=actions)
    degraded_frames = _rollout(
        make_observation_degradation_env(config, delay_steps=k, noise_std=0.0),
        seed=123,
        actions=actions,
    )
    assert len(raw_frames) == len(degraded_frames)
    for t, frame in enumerate(degraded_frames):
        source = raw_frames[max(t - k, 0)]
        np.testing.assert_array_equal(frame[:EGO_OBS_DIM], source[:EGO_OBS_DIM])


def test_noise_is_deterministic_for_same_seed() -> None:
    config = _base_config()
    actions = _action_sequence(10)
    frames_a = _rollout(
        make_observation_degradation_env(config, delay_steps=2, noise_std=0.05),
        seed=321,
        actions=actions,
    )
    frames_b = _rollout(
        make_observation_degradation_env(config, delay_steps=2, noise_std=0.05),
        seed=321,
        actions=actions,
    )
    assert len(frames_a) == len(frames_b)
    for frame_a, frame_b in zip(frames_a, frames_b, strict=True):
        np.testing.assert_array_equal(frame_a, frame_b)

    frames_c = _rollout(
        make_observation_degradation_env(config, delay_steps=2, noise_std=0.05),
        seed=322,
        actions=actions,
    )
    assert any(
        not np.array_equal(frame_a[:EGO_OBS_DIM], frame_c[:EGO_OBS_DIM])
        for frame_a, frame_c in zip(frames_a, frames_c)
    )


def test_noise_actually_perturbs_ego_channels() -> None:
    config = _base_config()
    actions = _action_sequence(6)
    raw_frames = _rollout(AutoDriftEnv(config), seed=55, actions=actions)
    noisy_frames = _rollout(
        make_observation_degradation_env(config, delay_steps=0, noise_std=0.05),
        seed=55,
        actions=actions,
    )
    assert any(
        not np.array_equal(noisy[:EGO_OBS_DIM], raw[:EGO_OBS_DIM])
        for noisy, raw in zip(noisy_frames, raw_frames, strict=True)
    )


def test_non_degraded_channels_are_bitwise_identical() -> None:
    config = _base_config()
    actions = _action_sequence(12)
    raw_frames = _rollout(AutoDriftEnv(config), seed=99, actions=actions)
    degraded_frames = _rollout(
        make_observation_degradation_env(config, delay_steps=5, noise_std=0.1),
        seed=99,
        actions=actions,
    )
    for raw, degraded in zip(raw_frames, degraded_frames, strict=True):
        np.testing.assert_array_equal(degraded[EGO_OBS_DIM:], raw[EGO_OBS_DIM:])


def _geometry_obstacle_config() -> DriftEnvConfig:
    return _base_config(
        speed_range=(10.0, 10.0),
        friction_limited_speed=False,
        obstacle=ObstacleTaskConfig(
            enabled=True,
            distance_range=(24.0, 24.0),
            half_width_range=(0.8, 0.8),
            allowed_labels=("aeb_feasible", "aes_feasible", "drift_required", "unavoidable"),
            max_sample_attempts=50,
        ),
    )


def test_geometry_noise_perturbs_scene_channels_only() -> None:
    config = _geometry_obstacle_config()
    actions = _action_sequence(8)
    raw_frames = _rollout(AutoDriftEnv(config), seed=9901, actions=actions)
    degraded_frames = _rollout(
        make_observation_degradation_env(
            config,
            geometry_scope="road_and_obstacle",
            geometry_noise_std=0.04,
        ),
        seed=9901,
        actions=actions,
    )

    assert len(raw_frames) == len(degraded_frames)
    road_slice = slice(12, 44)
    slot0 = slice(44, 51)
    for raw, degraded in zip(raw_frames, degraded_frames, strict=True):
        np.testing.assert_array_equal(degraded[:12], raw[:12])
        assert np.max(np.abs(degraded[road_slice] - raw[road_slice])) > 0.0
        assert degraded[44] == raw[44] == 1.0
        assert np.max(np.abs(degraded[45:49] - raw[45:49])) > 0.0
        np.testing.assert_array_equal(degraded[49:51], raw[49:51])
        for start in (51, 58, 65):
            # Empty obstacle slots keep present/geometry/size exact-zero.
            np.testing.assert_array_equal(degraded[start:start + 7], raw[start:start + 7])
        assert degraded[slot0].shape == (7,)


def test_geometry_noise_is_deterministic_for_same_seed() -> None:
    config = _geometry_obstacle_config()
    actions = _action_sequence(6)
    env_a = make_observation_degradation_env(
        config,
        geometry_scope="road_and_obstacle",
        geometry_noise_std=0.03,
    )
    env_b = make_observation_degradation_env(
        config,
        geometry_scope="road_and_obstacle",
        geometry_noise_std=0.03,
    )
    frames_a = _rollout(env_a, seed=9902, actions=actions)
    frames_b = _rollout(env_b, seed=9902, actions=actions)

    for frame_a, frame_b in zip(frames_a, frames_b, strict=True):
        np.testing.assert_array_equal(frame_a, frame_b)


def test_geometry_degradation_rejects_invalid_scope_and_scope_less_noise() -> None:
    config = _base_config()
    with pytest.raises(ValueError, match="geometry_scope"):
        make_observation_degradation_env(config, geometry_scope="camera", geometry_noise_std=0.01)
    with pytest.raises(ValueError, match="geometry_noise_std"):
        make_observation_degradation_env(config, geometry_scope="none", geometry_noise_std=0.01)


def test_observation_shape_dtype_and_finiteness() -> None:
    config = _base_config()
    env = make_observation_degradation_env(config, delay_steps=4, noise_std=0.05)
    assert env.observation_space.shape == (72,)
    obs, _ = env.reset(seed=5)
    assert obs.shape == (72,)
    assert obs.dtype == np.float32
    assert np.all(np.isfinite(obs))
    for action in _action_sequence(10):
        obs, _, terminated, truncated, _ = env.step(action)
        assert obs.shape == (72,)
        assert np.all(np.isfinite(obs))
        if terminated or truncated:
            break


def test_history_stack_frames_are_degraded_per_frame() -> None:
    config = _base_config(history_length=3)
    base_dim = AutoDriftEnv(config).base_obs_dim
    env = make_observation_degradation_env(config, delay_steps=2, noise_std=0.02)
    actions = _action_sequence(8)
    frames = _rollout(env, seed=777, actions=actions)
    for t in range(1, len(frames)):
        for slot in range(1, 3):
            reference_t = max(t - slot, 0)
            start = slot * base_dim
            np.testing.assert_array_equal(
                frames[t][start : start + EGO_OBS_DIM],
                frames[reference_t][:EGO_OBS_DIM],
            )


def test_wheel_observation_mode_is_rejected() -> None:
    config = _base_config(wheel_observation_mode="front_rear")
    with pytest.raises(ValueError, match="wheel_observation_mode"):
        make_observation_degradation_env(config, delay_steps=1)


def test_invalid_noise_and_delay_are_rejected() -> None:
    config = _base_config()
    with pytest.raises(ValueError, match="delay_steps"):
        make_observation_degradation_env(config, delay_steps=-1)
    with pytest.raises(ValueError, match="noise_std"):
        make_observation_degradation_env(config, noise_std=[0.1, 0.1])
    with pytest.raises(ValueError, match="noise_std"):
        make_observation_degradation_env(config, noise_std=-0.1)
    class _NotAutoDrift(gym.Env):
        observation_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32)
        action_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32)

    with pytest.raises(TypeError, match="AutoDriftEnv"):
        ObservationDegradationWrapper(_NotAutoDrift())


def _smoke_train_from_config(config_path: Path, tmp_path: Path, expected_obs_dim: int) -> None:
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    assert "ppo" in raw and "env" in raw
    env_config = build_env_config(raw["env"])
    assert AutoDriftEnv(env_config).observation_space.shape == (expected_obs_dim,)

    field_names = {field.name for field in fields(PPOConfig)}
    ppo = PPOConfig(**{key: value for key, value in raw["ppo"].items() if key in field_names})
    smoke = replace(
        ppo,
        total_steps=64,
        rollout_steps=32,
        num_envs=2,
        minibatch_size=64,
        update_epochs=1,
        device="cpu",
    )
    model = train(
        smoke,
        save_path=tmp_path / f"{config_path.stem}.pt",
        metrics_csv_path=tmp_path / f"{config_path.stem}_metrics.csv",
        env_config=env_config,
    )
    assert model.is_online_recurrent
    assert (tmp_path / f"{config_path.stem}.pt").exists()


def test_privileged_positive_control_config_trains_64_steps(tmp_path: Path) -> None:
    _smoke_train_from_config(PRIVILEGED_CONFIG, tmp_path, expected_obs_dim=76)


def test_p0_positive_control_config_trains_64_steps(tmp_path: Path) -> None:
    _smoke_train_from_config(P0_CONFIG, tmp_path, expected_obs_dim=72)
