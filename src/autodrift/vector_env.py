"""Synchronous vector environment for AutoDrift training."""

from __future__ import annotations

from dataclasses import dataclass
import multiprocessing as mp
from multiprocessing.connection import Connection
from typing import Any

import numpy as np

from autodrift.controller_profile_runtime import ObservationMaskSpec
from autodrift.env import DriftEnvConfig
from autodrift.observation_degradation_wrapper import make_env_from_config


@dataclass(frozen=True)
class VectorStep:
    observations: np.ndarray
    rewards: np.ndarray
    terminated: np.ndarray
    truncated: np.ndarray
    infos: list[dict[str, Any]]


def _env_worker(remote: Connection, config: DriftEnvConfig) -> None:
    env = make_env_from_config(config)
    try:
        while True:
            command, payload = remote.recv()
            if command == "reset":
                remote.send(env.reset(seed=payload))
            elif command == "step":
                remote.send(env.step(payload))
            elif command == "close":
                remote.close()
                return
            else:
                raise RuntimeError(f"unknown vector-env worker command: {command}")
    except EOFError:
        return


def _apply_observation_mask(mask_spec: ObservationMaskSpec | None, observation: np.ndarray) -> np.ndarray:
    if mask_spec is None or not mask_spec.enabled:
        return np.asarray(observation, dtype=np.float32)
    return mask_spec.apply(observation)


class SyncAutoDriftVectorEnv:
    """Small synchronous vector env.

    It keeps dependencies low while giving PPO batched observations and enough
    environment throughput for the circular drift milestone.
    """

    def __init__(
        self,
        num_envs: int,
        config: DriftEnvConfig | None = None,
        seed: int = 0,
        seed_sequence: list[int] | None = None,
        seed_sequence_probability: float = 1.0,
        observation_mask_spec: ObservationMaskSpec | None = None,
    ):
        if num_envs < 1:
            raise ValueError("num_envs must be at least 1")
        if seed_sequence is not None and not seed_sequence:
            raise ValueError("seed_sequence cannot be empty")
        if not 0.0 <= seed_sequence_probability <= 1.0:
            raise ValueError("seed_sequence_probability must be in [0, 1]")
        self.num_envs = int(num_envs)
        self.config = config or DriftEnvConfig()
        self.base_seed = int(seed)
        self.seed_sequence = [int(item) for item in seed_sequence] if seed_sequence is not None else None
        self.seed_sequence_probability = float(seed_sequence_probability)
        self.observation_mask_spec = observation_mask_spec
        self.seed_sequence_index = 0
        self.seed_rng = np.random.default_rng(self.base_seed + 1_000_003)
        self.envs = [make_env_from_config(self.config) for _ in range(self.num_envs)]
        self.single_observation_space = self.envs[0].observation_space
        self.single_action_space = self.envs[0].action_space
        self.episode_returns = np.zeros(self.num_envs, dtype=np.float64)
        self.episode_lengths = np.zeros(self.num_envs, dtype=np.int64)
        self.reset_counts = np.zeros(self.num_envs, dtype=np.int64)

    def _next_seed(self, env_index: int) -> int:
        default_seed = self.base_seed + env_index + self.num_envs * int(self.reset_counts[env_index])
        if self.seed_sequence is None:
            return default_seed
        if self.seed_sequence_probability <= 0.0:
            return default_seed
        if self.seed_sequence_probability < 1.0 and self.seed_rng.random() >= self.seed_sequence_probability:
            return default_seed
        seed = self.seed_sequence[self.seed_sequence_index % len(self.seed_sequence)]
        self.seed_sequence_index += 1
        return int(seed)

    def _reset_seed_state(self) -> None:
        self.seed_sequence_index = 0
        self.seed_rng = np.random.default_rng(self.base_seed + 1_000_003)

    def reset(self) -> tuple[np.ndarray, list[dict[str, Any]]]:
        observations = []
        infos = []
        self.episode_returns.fill(0.0)
        self.episode_lengths.fill(0)
        self.reset_counts.fill(0)
        self._reset_seed_state()
        for index, env in enumerate(self.envs):
            seed = self._next_seed(index)
            obs, info = env.reset(seed=seed)
            obs = _apply_observation_mask(self.observation_mask_spec, obs)
            info = dict(info)
            info["reset_seed"] = seed
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
            obs = _apply_observation_mask(self.observation_mask_spec, obs)
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
                seed = self._next_seed(index)
                obs, reset_info = env.reset(seed=seed)
                obs = _apply_observation_mask(self.observation_mask_spec, obs)
                reset_info = dict(reset_info)
                reset_info["reset_seed"] = seed
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

    def close(self) -> None:
        return None


class ParallelAutoDriftVectorEnv:
    """Process-based vector env for CPU-heavy rollout collection."""

    def __init__(
        self,
        num_envs: int,
        config: DriftEnvConfig | None = None,
        seed: int = 0,
        seed_sequence: list[int] | None = None,
        seed_sequence_probability: float = 1.0,
        start_method: str = "fork",
        observation_mask_spec: ObservationMaskSpec | None = None,
    ):
        if num_envs < 1:
            raise ValueError("num_envs must be at least 1")
        if seed_sequence is not None and not seed_sequence:
            raise ValueError("seed_sequence cannot be empty")
        if not 0.0 <= seed_sequence_probability <= 1.0:
            raise ValueError("seed_sequence_probability must be in [0, 1]")
        self.num_envs = int(num_envs)
        self.config = config or DriftEnvConfig()
        self.base_seed = int(seed)
        self.seed_sequence = [int(item) for item in seed_sequence] if seed_sequence is not None else None
        self.seed_sequence_probability = float(seed_sequence_probability)
        self.observation_mask_spec = observation_mask_spec
        self.seed_sequence_index = 0
        self.seed_rng = np.random.default_rng(self.base_seed + 1_000_003)
        self.closed = False

        sample_env = make_env_from_config(self.config)
        self.single_observation_space = sample_env.observation_space
        self.single_action_space = sample_env.action_space
        self.episode_returns = np.zeros(self.num_envs, dtype=np.float64)
        self.episode_lengths = np.zeros(self.num_envs, dtype=np.int64)
        self.reset_counts = np.zeros(self.num_envs, dtype=np.int64)

        context = mp.get_context(start_method)
        self.remotes: list[Connection] = []
        self.processes: list[mp.Process] = []
        for _ in range(self.num_envs):
            local_remote, worker_remote = context.Pipe()
            process = context.Process(target=_env_worker, args=(worker_remote, self.config), daemon=True)
            process.start()
            worker_remote.close()
            self.remotes.append(local_remote)
            self.processes.append(process)

    def _next_seed(self, env_index: int) -> int:
        default_seed = self.base_seed + env_index + self.num_envs * int(self.reset_counts[env_index])
        if self.seed_sequence is None:
            return default_seed
        if self.seed_sequence_probability <= 0.0:
            return default_seed
        if self.seed_sequence_probability < 1.0 and self.seed_rng.random() >= self.seed_sequence_probability:
            return default_seed
        seed = self.seed_sequence[self.seed_sequence_index % len(self.seed_sequence)]
        self.seed_sequence_index += 1
        return int(seed)

    def _reset_seed_state(self) -> None:
        self.seed_sequence_index = 0
        self.seed_rng = np.random.default_rng(self.base_seed + 1_000_003)

    def reset(self) -> tuple[np.ndarray, list[dict[str, Any]]]:
        observations = []
        infos = []
        self.episode_returns.fill(0.0)
        self.episode_lengths.fill(0)
        self.reset_counts.fill(0)
        self._reset_seed_state()
        seeds = []
        for index, remote in enumerate(self.remotes):
            seed = self._next_seed(index)
            seeds.append(seed)
            remote.send(("reset", seed))
        for index, remote in enumerate(self.remotes):
            obs, info = remote.recv()
            obs = _apply_observation_mask(self.observation_mask_spec, obs)
            info = dict(info)
            info["reset_seed"] = seeds[index]
            observations.append(obs)
            infos.append(info)
            self.reset_counts[index] = 1
        return np.stack(observations).astype(np.float32), infos

    def step(self, actions: np.ndarray) -> VectorStep:
        actions = np.asarray(actions, dtype=np.float32)
        if actions.shape != (self.num_envs, self.single_action_space.shape[0]):
            raise ValueError(f"expected actions shape {(self.num_envs, self.single_action_space.shape[0])}, got {actions.shape}")

        for remote, action in zip(self.remotes, actions, strict=True):
            remote.send(("step", action))

        observations = []
        rewards = np.zeros(self.num_envs, dtype=np.float32)
        terminated = np.zeros(self.num_envs, dtype=bool)
        truncated = np.zeros(self.num_envs, dtype=bool)
        infos: list[dict[str, Any]] = []
        for index, remote in enumerate(self.remotes):
            obs, reward, term, trunc, info = remote.recv()
            obs = _apply_observation_mask(self.observation_mask_spec, obs)
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
                seed = self._next_seed(index)
                remote.send(("reset", seed))
                obs, reset_info = remote.recv()
                obs = _apply_observation_mask(self.observation_mask_spec, obs)
                reset_info = dict(reset_info)
                reset_info["reset_seed"] = seed
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

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        for remote in self.remotes:
            try:
                remote.send(("close", None))
            except (BrokenPipeError, EOFError):
                pass
        for remote in self.remotes:
            remote.close()
        for process in self.processes:
            process.join(timeout=1.0)
            if process.is_alive():
                process.terminate()
                process.join(timeout=1.0)

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass
