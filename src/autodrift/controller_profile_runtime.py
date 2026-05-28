"""Runtime observation-mask support for controller-profile configs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gymnasium as gym
import numpy as np

from autodrift.controller_profiles import (
    HUMAN_VIEW_OBS_DIM,
    NO_MASK,
    ZERO_PREVIOUS_COMMANDS,
    apply_observation_mask,
    get_profile,
)


NO_HISTORY_TRANSFORM = "none"
CURRENT_TILED_HISTORY = "current_tiled"


@dataclass(frozen=True)
class ObservationMaskSpec:
    """Runtime mask declared by a controller-profile config."""

    profile_name: str
    observation_mask: str = NO_MASK
    previous_command_mask_indices: tuple[int, ...] = ()
    frame_dim: int = HUMAN_VIEW_OBS_DIM
    history_transform: str = NO_HISTORY_TRANSFORM
    reset_hidden_policy: str = "not_applicable"

    @property
    def enabled(self) -> bool:
        return self.observation_mask != NO_MASK or self.history_transform != NO_HISTORY_TRANSFORM

    def apply(self, observation: np.ndarray) -> np.ndarray:
        obs = np.asarray(observation, dtype=np.float32).copy()
        if self.observation_mask not in {NO_MASK, ZERO_PREVIOUS_COMMANDS}:
            raise ValueError(f"unknown observation mask: {self.observation_mask}")
        if obs.shape[-1] % self.frame_dim != 0:
            raise ValueError("observation length must be divisible by frame_dim")
        frame_count = obs.shape[-1] // self.frame_dim
        if self.observation_mask == ZERO_PREVIOUS_COMMANDS:
            for frame_index in range(frame_count):
                offset = frame_index * self.frame_dim
                for index in self.previous_command_mask_indices:
                    obs[..., offset + int(index)] = 0.0
        if self.history_transform == NO_HISTORY_TRANSFORM:
            return obs
        if self.history_transform != CURRENT_TILED_HISTORY:
            raise ValueError(f"unknown history transform: {self.history_transform}")
        if frame_count <= 1:
            return obs
        frames = obs.reshape(*obs.shape[:-1], frame_count, self.frame_dim)
        frames[..., 1:, :] = frames[..., 0:1, :]
        return obs


def mask_spec_from_profile_name(profile_name: str) -> ObservationMaskSpec:
    profile = get_profile(profile_name)
    return ObservationMaskSpec(
        profile_name=profile.name,
        observation_mask=profile.observation_mask,
        previous_command_mask_indices=tuple(int(index) for index in profile.previous_command_mask_indices),
        reset_hidden_policy=profile.reset_hidden_policy,
    )


def mask_spec_from_config(config: dict[str, Any]) -> ObservationMaskSpec:
    profile = config.get("controller_profile", {})
    if not isinstance(profile, dict):
        raise ValueError("controller_profile must be an object")
    profile_name = str(profile.get("name", "")).strip()
    if not profile_name:
        raise ValueError("controller_profile.name is required")
    return ObservationMaskSpec(
        profile_name=profile_name,
        observation_mask=str(profile.get("observation_mask", NO_MASK)),
        previous_command_mask_indices=tuple(int(index) for index in profile.get("previous_command_mask_indices", [])),
        history_transform=str(profile.get("history_transform", NO_HISTORY_TRANSFORM)),
        reset_hidden_policy=str(profile.get("reset_hidden_policy", "not_applicable")),
    )


def apply_runtime_observation_mask(config: dict[str, Any], observation: np.ndarray) -> np.ndarray:
    return mask_spec_from_config(config).apply(observation)


class ControllerProfileObservationWrapper(gym.ObservationWrapper):
    """Apply a controller-profile observation mask at env reset/step time."""

    def __init__(self, env: gym.Env, mask_spec: ObservationMaskSpec):
        super().__init__(env)
        self.mask_spec = mask_spec
        self.observation_space = env.observation_space

    def observation(self, observation: np.ndarray) -> np.ndarray:
        return self.mask_spec.apply(observation)


def wrap_env_with_profile_mask(env: gym.Env, config: dict[str, Any]) -> gym.Env:
    spec = mask_spec_from_config(config)
    if not spec.enabled:
        return env
    return ControllerProfileObservationWrapper(env, spec)


def profile_runtime_summary(config: dict[str, Any]) -> dict[str, Any]:
    spec = mask_spec_from_config(config)
    return {
        "profile_name": spec.profile_name,
        "observation_mask": spec.observation_mask,
        "previous_command_mask_indices": list(spec.previous_command_mask_indices),
        "mask_enabled": spec.enabled,
        "history_transform": spec.history_transform,
        "history_transform_enabled": spec.history_transform != NO_HISTORY_TRANSFORM,
        "reset_hidden_policy": spec.reset_hidden_policy,
        "hidden_or_oracle_actor_inputs": False,
        "wheel_or_slip_actor_inputs": False,
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "candidate_replay_started": False,
        "private_holdout_used": False,
        "promoted": False,
        "actor_input_contract_changed": False,
    }


def assert_profile_mask_matches_scaffold(config: dict[str, Any]) -> None:
    """Validate runtime mask metadata against the canonical scaffold profile."""

    spec = mask_spec_from_config(config)
    profile = get_profile(spec.profile_name)
    if spec.history_transform != NO_HISTORY_TRANSFORM:
        return
    scaffold = apply_observation_mask(profile, np.ones((profile.observation_dim,), dtype=np.float32))
    runtime = spec.apply(np.ones((profile.observation_dim,), dtype=np.float32))
    if not np.array_equal(scaffold, runtime):
        raise ValueError(f"runtime mask does not match scaffold profile: {spec.profile_name}")
