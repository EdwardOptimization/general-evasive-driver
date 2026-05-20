"""Synchronous vector environment for AutoDrift training."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from autodrift.env import AutoDriftEnv, DriftEnvConfig


@dataclass(frozen=True)
class VectorStep:
    observations: np.ndarray
    rewards: np.ndarray
    terminated: np.ndarray
    truncated: np.ndarray
    infos: list[dict[str, Any]]


class SyncAutoDriftVectorEnv:
    """Small synchronous vector env.

    It keeps dependencies low while giving PPO batched observations and enough
    environment throughput for the circular drift milestone.
    """

    def __init__(self, num_envs: int, config: DriftEnvConfig | None = None, seed: int = 0):
        if num_envs < 1:
            raise ValueError("num_envs must be at least 1")
        self.num_envs = int(num_envs)
        self.config = config or DriftEnvConfig()
        self.base_seed = int(seed)
        self.envs = [AutoDriftEnv(self.config) for _ in range(self.num_envs)]
        self.single_observation_space = self.envs[0].observation_space
        self.single_action_space = self.envs[0].action_space
        self.episode_returns = np.zeros(self.num_envs, dtype=np.float64)
        self.episode_lengths = np.zeros(self.num_envs, dtype=np.int64)
        self.reset_counts = np.zeros(self.num_envs, dtype=np.int64)

    def reset(self) -> tuple[np.ndarray, list[dict[str, Any]]]:
        observations = []
        infos = []
        self.episode_returns.fill(0.0)
        self.episode_lengths.fill(0)
        for index, env in enumerate(self.envs):
            obs, info = env.reset(seed=self.base_seed + index)
            observations.append(obs)
            infos.append(info)
            self.reset_counts[index] = 1
        return np.stack(observations).astype(np.float32), infos

    def step(self, actions: np.ndarray) -> VectorStep:
        actions = np.asarray(actions, dtype=np.float32)
        if actions.shape != (self.num_envs, self.single_action_space.shape[0]):
            raise ValueError(f"expected actions shape {(self.num_envs, self.single_action_space.shape[0])}, got {actions.shape}")

        observations = []
        rewards = np.zeros(self.num_envs, dtype=np.float32)
        terminated = np.zeros(self.num_envs, dtype=bool)
        truncated = np.zeros(self.num_envs, dtype=bool)
        infos: list[dict[str, Any]] = []
        for index, (env, action) in enumerate(zip(self.envs, actions, strict=True)):
            obs, reward, term, trunc, info = env.step(action)
            done = term or trunc
            self.episode_returns[index] += reward
            self.episode_lengths[index] += 1
            rewards[index] = reward
            terminated[index] = term
            truncated[index] = trunc

            if done:
                info = dict(info)
                info["episode"] = {
                    "return": float(self.episode_returns[index]),
                    "length": int(self.episode_lengths[index]),
                    "terminated": bool(term),
                    "truncated": bool(trunc),
                }
                seed = self.base_seed + index + self.num_envs * int(self.reset_counts[index])
                obs, reset_info = env.reset(seed=seed)
                info["reset_info"] = reset_info
                self.episode_returns[index] = 0.0
                self.episode_lengths[index] = 0
                self.reset_counts[index] += 1

            observations.append(obs)
            infos.append(info)

        return VectorStep(
            observations=np.stack(observations).astype(np.float32),
            rewards=rewards,
            terminated=terminated,
            truncated=truncated,
            infos=infos,
        )
