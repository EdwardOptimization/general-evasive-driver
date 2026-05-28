from pathlib import Path

import numpy as np

from autodrift.artifacts import read_json
from autodrift.config import build_env_config
from autodrift.controller_profile_runtime import (
    CURRENT_TILED_HISTORY,
    ControllerProfileObservationWrapper,
    apply_runtime_observation_mask,
    assert_profile_mask_matches_scaffold,
    mask_spec_from_config,
    mask_spec_from_profile_name,
    profile_runtime_summary,
    wrap_env_with_profile_mask,
)
from autodrift.controller_profiles import HUMAN_VIEW_OBS_DIM, PREVIOUS_COMMAND_INDICES, get_profile
from autodrift.env import AutoDriftEnv


L0_CONFIG = "configs/paper_route_profiles/m1190_l0_current_masked_smoke.json"
L1_CONFIG = "configs/paper_route_profiles/m1190_l1_one_step_smoke.json"
L2_CONFIG = "configs/paper_route_profiles/m1190_l2_window_25_smoke.json"
PROFILE_CONFIGS = sorted(Path("configs/paper_route_profiles").glob("m1190_*_smoke.json"))


def test_l0_runtime_mask_zeros_previous_command_fields() -> None:
    config = read_json(L0_CONFIG)
    obs = np.arange(HUMAN_VIEW_OBS_DIM, dtype=np.float32)
    masked = apply_runtime_observation_mask(config, obs)

    for index in PREVIOUS_COMMAND_INDICES:
        assert masked[index] == 0.0
    assert masked[0] == obs[0]
    assert masked[8] == obs[8]
    assert masked[12] == obs[12]


def test_runtime_mask_handles_stacked_frames() -> None:
    config = read_json(L0_CONFIG)
    obs = np.arange(HUMAN_VIEW_OBS_DIM * 2, dtype=np.float32)
    masked = apply_runtime_observation_mask(config, obs)

    for frame_index in range(2):
        offset = frame_index * HUMAN_VIEW_OBS_DIM
        for index in PREVIOUS_COMMAND_INDICES:
            assert masked[offset + index] == 0.0
    assert masked[HUMAN_VIEW_OBS_DIM + 12] == obs[HUMAN_VIEW_OBS_DIM + 12]


def test_unmasked_l1_runtime_leaves_observation_unchanged() -> None:
    config = read_json(L1_CONFIG)
    obs = np.arange(HUMAN_VIEW_OBS_DIM, dtype=np.float32)
    masked = apply_runtime_observation_mask(config, obs)
    assert np.array_equal(masked, obs)
    assert masked is not obs


def test_profile_runtime_wrapper_masks_env_reset_and_step() -> None:
    config = read_json(L0_CONFIG)
    env = AutoDriftEnv(build_env_config(config["env"]))
    wrapped = wrap_env_with_profile_mask(env, config)
    assert isinstance(wrapped, ControllerProfileObservationWrapper)

    obs, _ = wrapped.reset(seed=1191)
    assert np.all(obs[list(PREVIOUS_COMMAND_INDICES)] == 0.0)
    obs, *_ = wrapped.step(np.array([0.5, 0.2, -0.3], dtype=np.float32))
    assert np.all(obs[list(PREVIOUS_COMMAND_INDICES)] == 0.0)


def test_unmasked_profile_returns_original_env_instance() -> None:
    config = read_json(L1_CONFIG)
    env = AutoDriftEnv(build_env_config(config["env"]))
    wrapped = wrap_env_with_profile_mask(env, config)
    assert wrapped is env


def test_l2_unmasked_stacked_profile_is_unchanged() -> None:
    config = read_json(L2_CONFIG)
    profile = get_profile("L2_window_25")
    obs = np.arange(profile.observation_dim, dtype=np.float32)
    masked = apply_runtime_observation_mask(config, obs)
    assert np.array_equal(masked, obs)


def test_current_tiled_history_transform_repeats_current_frame() -> None:
    config = read_json(L2_CONFIG)
    config["controller_profile"]["history_transform"] = CURRENT_TILED_HISTORY
    profile = get_profile("L2_window_25")
    obs = np.arange(profile.observation_dim, dtype=np.float32)

    transformed = apply_runtime_observation_mask(config, obs)
    frames = transformed.reshape(profile.env_history_length, HUMAN_VIEW_OBS_DIM)
    expected_current = obs[:HUMAN_VIEW_OBS_DIM]

    assert transformed.shape == obs.shape
    assert np.array_equal(frames[0], expected_current)
    for frame_index in range(1, profile.env_history_length):
        assert np.array_equal(frames[frame_index], expected_current)


def test_current_tiled_history_transform_handles_batched_observations() -> None:
    config = read_json(L2_CONFIG)
    config["controller_profile"]["history_transform"] = CURRENT_TILED_HISTORY
    profile = get_profile("L2_window_25")
    obs = np.arange(profile.observation_dim * 2, dtype=np.float32).reshape(2, profile.observation_dim)

    transformed = apply_runtime_observation_mask(config, obs)
    frames = transformed.reshape(2, profile.env_history_length, HUMAN_VIEW_OBS_DIM)

    assert transformed.shape == obs.shape
    for batch_index in range(2):
        for frame_index in range(1, profile.env_history_length):
            assert np.array_equal(frames[batch_index, frame_index], frames[batch_index, 0])


def test_mask_spec_matches_scaffold_profiles() -> None:
    for path in PROFILE_CONFIGS:
        config = read_json(path)
        assert_profile_mask_matches_scaffold(config)
        spec = mask_spec_from_config(config)
        from_name = mask_spec_from_profile_name(spec.profile_name)
        assert spec == from_name


def test_all_unmasked_generated_profiles_leave_observation_unchanged() -> None:
    for path in PROFILE_CONFIGS:
        config = read_json(path)
        spec = mask_spec_from_config(config)
        if spec.enabled:
            continue
        profile = get_profile(spec.profile_name)
        obs = np.arange(profile.observation_dim, dtype=np.float32)
        masked = apply_runtime_observation_mask(config, obs)
        assert np.array_equal(masked, obs)


def test_runtime_summary_reports_no_training_or_oracle_inputs() -> None:
    summary = profile_runtime_summary(read_json(L0_CONFIG))
    assert summary["mask_enabled"] is True
    assert summary["history_transform"] == "none"
    assert summary["history_transform_enabled"] is False
    assert summary["reset_hidden_policy"] == "not_applicable"
    assert summary["hidden_or_oracle_actor_inputs"] is False
    assert summary["wheel_or_slip_actor_inputs"] is False
    assert summary["training_started"] is False
    assert summary["ppo_used"] is False
    assert summary["private_holdout_used"] is False


def test_runtime_summary_reports_l3_reset_hidden_policy() -> None:
    summary = profile_runtime_summary(read_json("configs/paper_route_profiles/m1190_l3_reset_control_smoke.json"))
    assert summary["reset_hidden_policy"] == "every_step_control"
