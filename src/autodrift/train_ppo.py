"""Minimal PPO trainer for the AutoDrift environment.

This is intentionally small and dependency-light. It is good enough to start
experiments and produce baselines; if training becomes the main bottleneck, move
to a vectorized trainer such as Stable-Baselines3, CleanRL, or RL-Games.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, fields, replace
from pathlib import Path
import sys

import numpy as np
import torch
from torch import nn
from torch.distributions import Normal
from torch.optim import Adam

from autodrift.artifacts import make_run_dir, read_json, to_jsonable, write_csv_rows, write_json
from autodrift.config import build_curriculum, build_env_config, env_config_for_step
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.vector_env import SyncAutoDriftVectorEnv


@dataclass(frozen=True)
class PPOConfig:
    total_steps: int = 50_000
    rollout_steps: int = 1024
    num_envs: int = 1
    update_epochs: int = 6
    minibatch_size: int = 256
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_coef: float = 0.2
    ent_coef: float = 0.003
    vf_coef: float = 0.5
    max_grad_norm: float = 0.5
    learning_rate: float = 3e-4
    hidden_size: int = 128
    log_std_init: float = -1.0
    log_std_min: float = -5.0
    log_std_max: float = -0.5
    actor_encoder: str = "mlp"
    actor_history_length: int = 1
    action_sequence_horizon: int = 1
    sequence_aux_coef: float = 0.0
    recurrent_sequence_training: bool = False
    seed: int = 5
    device: str = "auto"


class ActorCritic(nn.Module):
    def __init__(
        self,
        obs_dim: int,
        act_dim: int,
        hidden_size: int = 128,
        log_std_init: float = -1.0,
        log_std_min: float = -5.0,
        log_std_max: float = -0.5,
        actor_encoder: str = "mlp",
        actor_history_length: int = 1,
        action_sequence_horizon: int = 1,
    ):
        super().__init__()
        if action_sequence_horizon < 1:
            raise ValueError("action_sequence_horizon must be at least 1")
        if actor_encoder not in {"mlp", "temporal_gru", "online_gru"}:
            raise ValueError("actor_encoder must be one of: mlp, temporal_gru, online_gru")
        if actor_history_length < 1:
            raise ValueError("actor_history_length must be at least 1")
        self.obs_dim = int(obs_dim)
        self.act_dim = int(act_dim)
        self.actor_encoder = actor_encoder
        self.actor_history_length = int(actor_history_length)
        self.action_sequence_horizon = int(action_sequence_horizon)
        self.log_std_min = float(log_std_min)
        self.log_std_max = float(log_std_max)
        self.frame_dim = int(obs_dim)
        if self.actor_encoder == "mlp":
            self.shared = nn.Sequential(
                nn.Linear(obs_dim, hidden_size),
                nn.Tanh(),
                nn.Linear(hidden_size, hidden_size),
                nn.Tanh(),
            )
            self.frame_encoder = None
            self.temporal_gru = None
            self.online_gru_cell = None
        else:
            if self.actor_encoder == "temporal_gru" and obs_dim % self.actor_history_length != 0:
                raise ValueError("temporal_gru actor requires obs_dim divisible by actor_history_length")
            self.frame_dim = (
                int(obs_dim // self.actor_history_length)
                if self.actor_encoder == "temporal_gru"
                else int(obs_dim)
            )
            self.shared = None
            self.frame_encoder = nn.Sequential(
                nn.Linear(self.frame_dim, hidden_size),
                nn.Tanh(),
            )
            self.temporal_gru = nn.GRU(hidden_size, hidden_size, batch_first=True) if self.actor_encoder == "temporal_gru" else None
            self.online_gru_cell = nn.GRUCell(hidden_size, hidden_size) if self.actor_encoder == "online_gru" else None
        self.actor_mean = nn.Linear(hidden_size, act_dim)
        self.critic = nn.Linear(hidden_size, 1)
        self.log_std = nn.Parameter(torch.full((act_dim,), float(log_std_init)))
        self.sequence_tail = (
            nn.Linear(hidden_size, (self.action_sequence_horizon - 1) * act_dim)
            if self.action_sequence_horizon > 1
            else None
        )

    def features_tensor(self, obs: torch.Tensor) -> torch.Tensor:
        if self.actor_encoder == "mlp":
            assert self.shared is not None
            return self.shared(obs)
        if self.actor_encoder == "online_gru":
            hidden = self.initial_hidden(obs.shape[0], obs.device)
            features, _ = self.recurrent_features_tensor(obs, hidden)
            return features
        assert self.frame_encoder is not None
        assert self.temporal_gru is not None
        frames = obs.reshape(obs.shape[0], self.actor_history_length, self.frame_dim)
        frames = torch.flip(frames, dims=[1])
        encoded_frames = self.frame_encoder(frames)
        _, hidden = self.temporal_gru(encoded_frames)
        return hidden[-1]

    def initial_hidden(self, batch_size: int, device: torch.device | None = None) -> torch.Tensor:
        resolved_device = device or next(self.parameters()).device
        return torch.zeros(int(batch_size), self.actor_mean.in_features, dtype=torch.float32, device=resolved_device)

    def recurrent_features_tensor(self, obs: torch.Tensor, hidden: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        if self.actor_encoder != "online_gru":
            raise RuntimeError("recurrent_features_tensor requires actor_encoder='online_gru'")
        assert self.frame_encoder is not None
        assert self.online_gru_cell is not None
        encoded = self.frame_encoder(obs)
        next_hidden = self.online_gru_cell(encoded, hidden)
        return next_hidden, next_hidden

    def forward_recurrent(self, obs: torch.Tensor, hidden: torch.Tensor) -> tuple[Normal, torch.Tensor, torch.Tensor]:
        features, next_hidden = self.recurrent_features_tensor(obs, hidden)
        mean = self.actor_mean(features)
        log_std = torch.clamp(self.log_std, self.log_std_min, self.log_std_max)
        std = torch.exp(log_std).expand_as(mean)
        return Normal(mean, std), self.critic(features).squeeze(-1), next_hidden

    def forward(self, obs: torch.Tensor) -> tuple[Normal, torch.Tensor]:
        features = self.features_tensor(obs)
        mean = self.actor_mean(features)
        log_std = torch.clamp(self.log_std, self.log_std_min, self.log_std_max)
        std = torch.exp(log_std).expand_as(mean)
        return Normal(mean, std), self.critic(features).squeeze(-1)

    def action_sequence_tensor(self, obs: torch.Tensor) -> torch.Tensor:
        features = self.features_tensor(obs)
        first_action = torch.tanh(self.actor_mean(features)).unsqueeze(1)
        if self.sequence_tail is None:
            return first_action
        tail = torch.tanh(self.sequence_tail(features)).reshape(
            obs.shape[0],
            self.action_sequence_horizon - 1,
            self.act_dim,
        )
        return torch.cat([first_action, tail], dim=1)

    def predict_sequence(self, obs: np.ndarray) -> np.ndarray:
        device = next(self.parameters()).device
        obs_t = torch.as_tensor(obs, dtype=torch.float32, device=device).unsqueeze(0)
        with torch.no_grad():
            sequence = self.action_sequence_tensor(obs_t)
        return sequence.squeeze(0).cpu().numpy().astype(np.float32)

    def _squashed_log_prob(self, dist: Normal, raw_action: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        correction = torch.log(torch.clamp(1.0 - action.pow(2), min=1e-6)).sum(dim=-1)
        return dist.log_prob(raw_action).sum(dim=-1) - correction

    def act(self, obs: np.ndarray, deterministic: bool = False) -> tuple[np.ndarray, float, float]:
        device = next(self.parameters()).device
        obs_t = torch.as_tensor(obs, dtype=torch.float32, device=device).unsqueeze(0)
        with torch.no_grad():
            dist, value = self.forward(obs_t)
            raw_action = dist.mean if deterministic else dist.sample()
            action = torch.tanh(raw_action)
            log_prob = self._squashed_log_prob(dist, raw_action, action)
        return action.squeeze(0).cpu().numpy().astype(np.float32), float(log_prob.item()), float(value.item())

    def act_recurrent(
        self,
        obs: np.ndarray,
        hidden: torch.Tensor | None = None,
        deterministic: bool = False,
    ) -> tuple[np.ndarray, float, float, torch.Tensor]:
        device = next(self.parameters()).device
        obs_t = torch.as_tensor(obs, dtype=torch.float32, device=device).unsqueeze(0)
        hidden_t = hidden if hidden is not None else self.initial_hidden(1, device)
        with torch.no_grad():
            dist, value, next_hidden = self.forward_recurrent(obs_t, hidden_t)
            raw_action = dist.mean if deterministic else dist.sample()
            action = torch.tanh(raw_action)
            log_prob = self._squashed_log_prob(dist, raw_action, action)
        return (
            action.squeeze(0).cpu().numpy().astype(np.float32),
            float(log_prob.item()),
            float(value.item()),
            next_hidden.detach(),
        )

    def act_batch(self, obs: np.ndarray, deterministic: bool = False) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        device = next(self.parameters()).device
        obs_t = torch.as_tensor(obs, dtype=torch.float32, device=device)
        with torch.no_grad():
            dist, value = self.forward(obs_t)
            raw_action = dist.mean if deterministic else dist.sample()
            action = torch.tanh(raw_action)
            log_prob = self._squashed_log_prob(dist, raw_action, action)
        return (
            action.cpu().numpy().astype(np.float32),
            log_prob.cpu().numpy().astype(np.float32),
            value.cpu().numpy().astype(np.float32),
        )

    def act_batch_recurrent(
        self,
        obs: np.ndarray,
        hidden: torch.Tensor,
        deterministic: bool = False,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, torch.Tensor]:
        device = next(self.parameters()).device
        obs_t = torch.as_tensor(obs, dtype=torch.float32, device=device)
        with torch.no_grad():
            dist, value, next_hidden = self.forward_recurrent(obs_t, hidden)
            raw_action = dist.mean if deterministic else dist.sample()
            action = torch.tanh(raw_action)
            log_prob = self._squashed_log_prob(dist, raw_action, action)
        return (
            action.cpu().numpy().astype(np.float32),
            log_prob.cpu().numpy().astype(np.float32),
            value.cpu().numpy().astype(np.float32),
            next_hidden.detach(),
        )

    def evaluate_actions(self, obs: torch.Tensor, actions: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        dist, value = self.forward(obs)
        clipped_actions = torch.clamp(actions, -1.0 + 1e-6, 1.0 - 1e-6)
        raw_actions = torch.atanh(clipped_actions)
        log_prob = self._squashed_log_prob(dist, raw_actions, clipped_actions)
        entropy = dist.entropy().sum(dim=-1)
        return log_prob, entropy, value

    def evaluate_actions_recurrent(
        self,
        obs: torch.Tensor,
        actions: torch.Tensor,
        hidden: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        dist, value, _ = self.forward_recurrent(obs, hidden)
        clipped_actions = torch.clamp(actions, -1.0 + 1e-6, 1.0 - 1e-6)
        raw_actions = torch.atanh(clipped_actions)
        log_prob = self._squashed_log_prob(dist, raw_actions, clipped_actions)
        entropy = dist.entropy().sum(dim=-1)
        return log_prob, entropy, value

    def evaluate_actions_recurrent_sequence(
        self,
        obs: torch.Tensor,
        actions: torch.Tensor,
        initial_hidden: torch.Tensor,
        dones: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        if self.actor_encoder != "online_gru":
            raise RuntimeError("evaluate_actions_recurrent_sequence requires actor_encoder='online_gru'")
        logps = []
        entropies = []
        values = []
        hidden = initial_hidden
        for t in range(obs.shape[0]):
            dist, value, next_hidden = self.forward_recurrent(obs[t], hidden)
            clipped_actions = torch.clamp(actions[t], -1.0 + 1e-6, 1.0 - 1e-6)
            raw_actions = torch.atanh(clipped_actions)
            logps.append(self._squashed_log_prob(dist, raw_actions, clipped_actions))
            entropies.append(dist.entropy().sum(dim=-1))
            values.append(value)
            hidden = next_hidden
            if t < obs.shape[0] - 1:
                done_t = dones[t].to(dtype=torch.bool, device=obs.device)
                hidden = hidden.clone()
                hidden[done_t] = 0.0
        return torch.stack(logps), torch.stack(entropies), torch.stack(values)


def adapt_actor_critic_state(model: ActorCritic, source_state: dict[str, torch.Tensor]) -> str:
    model.load_state_dict(source_state)
    return "strict"


def load_init_checkpoint_state(model: ActorCritic, checkpoint_path: Path, device: torch.device) -> str:
    checkpoint = torch.load(checkpoint_path, map_location=device)
    source_state = checkpoint["model_state"]
    return adapt_actor_critic_state(model, source_state)


def resolve_device(name: str) -> torch.device:
    if name == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    device = torch.device(name)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested, but torch.cuda.is_available() is false.")
    return device


def compute_gae(
    rewards: np.ndarray,
    dones: np.ndarray,
    values: np.ndarray,
    last_value: float,
    gamma: float,
    gae_lambda: float,
) -> tuple[np.ndarray, np.ndarray]:
    advantages = np.zeros_like(rewards, dtype=np.float32)
    last_gae = 0.0
    for t in reversed(range(len(rewards))):
        next_non_terminal = 1.0 - dones[t]
        next_value = last_value if t == len(rewards) - 1 else values[t + 1]
        delta = rewards[t] + gamma * next_value * next_non_terminal - values[t]
        last_gae = delta + gamma * gae_lambda * next_non_terminal * last_gae
        advantages[t] = last_gae
    returns = advantages + values
    return advantages, returns


def compute_gae_vectorized(
    rewards: np.ndarray,
    dones: np.ndarray,
    values: np.ndarray,
    last_values: np.ndarray,
    gamma: float,
    gae_lambda: float,
) -> tuple[np.ndarray, np.ndarray]:
    advantages = np.zeros_like(rewards, dtype=np.float32)
    last_gae = np.zeros(rewards.shape[1], dtype=np.float32)
    for t in reversed(range(rewards.shape[0])):
        next_non_terminal = 1.0 - dones[t]
        next_values = last_values if t == rewards.shape[0] - 1 else values[t + 1]
        delta = rewards[t] + gamma * next_values * next_non_terminal - values[t]
        last_gae = delta + gamma * gae_lambda * next_non_terminal * last_gae
        advantages[t] = last_gae
    returns = advantages + values
    return advantages, returns


def build_sequence_targets(
    actions: np.ndarray,
    dones: np.ndarray,
    horizon: int,
) -> tuple[np.ndarray, np.ndarray]:
    if horizon <= 1:
        target = np.zeros((*actions.shape[:2], 0, actions.shape[-1]), dtype=np.float32)
        mask = np.zeros((*actions.shape[:2], 0), dtype=np.float32)
        return target, mask
    rollout_n, num_envs, act_dim = actions.shape
    tail_horizon = horizon - 1
    target = np.zeros((rollout_n, num_envs, tail_horizon, act_dim), dtype=np.float32)
    mask = np.zeros((rollout_n, num_envs, tail_horizon), dtype=np.float32)
    for t in range(rollout_n):
        for env_index in range(num_envs):
            valid = True
            for tail_index in range(tail_horizon):
                future_t = t + tail_index + 1
                if future_t >= rollout_n:
                    break
                if dones[future_t - 1, env_index] > 0.0:
                    valid = False
                if not valid:
                    break
                target[t, env_index, tail_index] = actions[future_t, env_index]
                mask[t, env_index, tail_index] = 1.0
    return target, mask


def train(
    config: PPOConfig,
    save_path: Path | None = None,
    metrics_csv_path: Path | None = None,
    env_config: DriftEnvConfig | None = None,
    curriculum: list | None = None,
    checkpoint_metadata: dict | None = None,
    init_checkpoint_path: Path | None = None,
) -> ActorCritic:
    np.random.seed(config.seed)
    torch.manual_seed(config.seed)
    device = resolve_device(config.device)

    env_config = env_config or DriftEnvConfig()
    curriculum = curriculum or []
    active_env_config, active_stage = env_config_for_step(env_config, curriculum, 0)
    if config.actor_encoder == "temporal_gru" and config.actor_history_length != active_env_config.history_length:
        config = replace(config, actor_history_length=active_env_config.history_length)
    if config.actor_encoder == "online_gru" and active_env_config.history_length != 1:
        raise ValueError("online_gru actor requires env history_length=1; memory is carried in recurrent hidden state")
    if config.actor_encoder == "online_gru" and config.action_sequence_horizon > 1:
        raise ValueError("online_gru actor does not currently support action_sequence_horizon > 1")
    env = SyncAutoDriftVectorEnv(num_envs=config.num_envs, config=active_env_config, seed=config.seed)
    obs, infos = env.reset()
    model = ActorCritic(
        obs_dim=env.single_observation_space.shape[0],
        act_dim=env.single_action_space.shape[0],
        hidden_size=config.hidden_size,
        log_std_init=config.log_std_init,
        log_std_min=config.log_std_min,
        log_std_max=config.log_std_max,
        actor_encoder=config.actor_encoder,
        actor_history_length=config.actor_history_length,
        action_sequence_horizon=config.action_sequence_horizon,
    ).to(device)
    optimizer = Adam(model.parameters(), lr=config.learning_rate)
    if init_checkpoint_path is not None:
        load_mode = load_init_checkpoint_state(model, init_checkpoint_path, device)
        print(f"loaded_init_checkpoint={init_checkpoint_path} load_mode={load_mode}")
    print(f"training_device={device} num_envs={config.num_envs} curriculum_stage={active_stage}")

    global_step = 0
    update = 0
    metric_rows: list[dict[str, float | int]] = []
    recurrent_hidden = model.initial_hidden(config.num_envs, device) if config.actor_encoder == "online_gru" else None
    while global_step < config.total_steps:
        next_env_config, next_stage = env_config_for_step(env_config, curriculum, global_step)
        if next_stage != active_stage:
            if config.actor_encoder == "online_gru" and next_env_config.history_length != 1:
                raise ValueError("online_gru actor requires env history_length=1 in every curriculum stage")
            active_env_config = next_env_config
            active_stage = next_stage
            env = SyncAutoDriftVectorEnv(num_envs=config.num_envs, config=active_env_config, seed=config.seed + global_step)
            obs, infos = env.reset()
            recurrent_hidden = model.initial_hidden(config.num_envs, device) if config.actor_encoder == "online_gru" else None
            print(f"curriculum_stage={active_stage} step={global_step}")

        remaining = config.total_steps - global_step
        rollout_n = min(config.rollout_steps, max(1, int(np.ceil(remaining / config.num_envs))))
        obs_buf = np.zeros((rollout_n, config.num_envs, env.single_observation_space.shape[0]), dtype=np.float32)
        act_buf = np.zeros((rollout_n, config.num_envs, env.single_action_space.shape[0]), dtype=np.float32)
        logp_buf = np.zeros((rollout_n, config.num_envs), dtype=np.float32)
        rew_buf = np.zeros((rollout_n, config.num_envs), dtype=np.float32)
        done_buf = np.zeros((rollout_n, config.num_envs), dtype=np.float32)
        val_buf = np.zeros((rollout_n, config.num_envs), dtype=np.float32)
        hidden_buf = (
            np.zeros((rollout_n, config.num_envs, config.hidden_size), dtype=np.float32)
            if config.actor_encoder == "online_gru"
            else None
        )

        episode_returns: list[float] = []
        episode_lengths: list[int] = []
        episode_terminated: list[float] = []
        for t in range(rollout_n):
            if config.actor_encoder == "online_gru":
                assert recurrent_hidden is not None
                assert hidden_buf is not None
                hidden_buf[t] = recurrent_hidden.detach().cpu().numpy().astype(np.float32)
                action, logp, value, next_hidden = model.act_batch_recurrent(obs, recurrent_hidden)
            else:
                action, logp, value = model.act_batch(obs)
                next_hidden = None
            step = env.step(action)
            done = np.logical_or(step.terminated, step.truncated)
            obs_buf[t] = obs
            act_buf[t] = action
            logp_buf[t] = logp
            rew_buf[t] = step.rewards
            done_buf[t] = done.astype(np.float32)
            val_buf[t] = value

            for info in step.infos:
                episode = info.get("episode")
                if episode is not None:
                    episode_returns.append(float(episode["return"]))
                    episode_lengths.append(int(episode["length"]))
                    episode_terminated.append(float(episode["terminated"]))
            obs = step.observations
            if config.actor_encoder == "online_gru":
                assert next_hidden is not None
                done_t = torch.as_tensor(done, dtype=torch.bool, device=device)
                next_hidden = next_hidden.clone()
                next_hidden[done_t] = 0.0
                recurrent_hidden = next_hidden.detach()

        with torch.no_grad():
            if config.actor_encoder == "online_gru":
                assert recurrent_hidden is not None
                _, last_value_t, _ = model.forward_recurrent(
                    torch.as_tensor(obs, dtype=torch.float32, device=device),
                    recurrent_hidden,
                )
            else:
                _, last_value_t = model.forward(torch.as_tensor(obs, dtype=torch.float32, device=device))
        advantages, returns = compute_gae_vectorized(
            rew_buf,
            done_buf,
            val_buf,
            last_value_t.detach().cpu().numpy().astype(np.float32),
            config.gamma,
            config.gae_lambda,
        )
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        flat_obs = obs_buf.reshape((-1, obs_buf.shape[-1]))
        flat_act = act_buf.reshape((-1, act_buf.shape[-1]))
        flat_old_logp = logp_buf.reshape(-1)
        flat_adv = advantages.reshape(-1)
        flat_ret = returns.reshape(-1)
        flat_hidden = hidden_buf.reshape((-1, hidden_buf.shape[-1])) if hidden_buf is not None else None
        if config.action_sequence_horizon > 1:
            seq_target_buf, seq_mask_buf = build_sequence_targets(act_buf, done_buf, config.action_sequence_horizon)
            flat_seq_target = seq_target_buf.reshape((-1, *seq_target_buf.shape[2:]))
            flat_seq_mask = seq_mask_buf.reshape((-1, *seq_mask_buf.shape[2:]))
        else:
            flat_seq_target = None
            flat_seq_mask = None

        if config.actor_encoder == "online_gru" and config.recurrent_sequence_training:
            assert hidden_buf is not None
            obs_seq_t = torch.as_tensor(obs_buf, dtype=torch.float32, device=device)
            act_seq_t = torch.as_tensor(act_buf, dtype=torch.float32, device=device)
            old_logp_seq_t = torch.as_tensor(logp_buf, dtype=torch.float32, device=device)
            adv_seq_t = torch.as_tensor(advantages, dtype=torch.float32, device=device)
            ret_seq_t = torch.as_tensor(returns, dtype=torch.float32, device=device)
            done_seq_t = torch.as_tensor(done_buf, dtype=torch.float32, device=device)
            initial_hidden_t = torch.as_tensor(hidden_buf[0], dtype=torch.float32, device=device)
            env_indices = np.arange(config.num_envs)
            env_minibatch = max(1, min(config.num_envs, config.minibatch_size // max(1, rollout_n)))
            for _ in range(config.update_epochs):
                np.random.shuffle(env_indices)
                for start in range(0, len(env_indices), env_minibatch):
                    mb_env = env_indices[start : start + env_minibatch]
                    logp, entropy_values, value = model.evaluate_actions_recurrent_sequence(
                        obs_seq_t[:, mb_env],
                        act_seq_t[:, mb_env],
                        initial_hidden_t[mb_env],
                        done_seq_t[:, mb_env],
                    )
                    entropy = entropy_values.mean()
                    ratio = torch.exp(logp - old_logp_seq_t[:, mb_env])
                    mb_adv = adv_seq_t[:, mb_env]
                    mb_ret = ret_seq_t[:, mb_env]
                    pg_loss_1 = -mb_adv * ratio
                    pg_loss_2 = -mb_adv * torch.clamp(ratio, 1.0 - config.clip_coef, 1.0 + config.clip_coef)
                    pg_loss = torch.max(pg_loss_1, pg_loss_2).mean()
                    value_loss = 0.5 * torch.square(value - mb_ret).mean()
                    loss = pg_loss + config.vf_coef * value_loss - config.ent_coef * entropy

                    optimizer.zero_grad()
                    loss.backward()
                    nn.utils.clip_grad_norm_(model.parameters(), config.max_grad_norm)
                    optimizer.step()
        else:
            obs_t = torch.as_tensor(flat_obs, dtype=torch.float32, device=device)
            act_t = torch.as_tensor(flat_act, dtype=torch.float32, device=device)
            old_logp_t = torch.as_tensor(flat_old_logp, dtype=torch.float32, device=device)
            adv_t = torch.as_tensor(flat_adv, dtype=torch.float32, device=device)
            ret_t = torch.as_tensor(flat_ret, dtype=torch.float32, device=device)
            hidden_t = torch.as_tensor(flat_hidden, dtype=torch.float32, device=device) if flat_hidden is not None else None
            seq_target_t = torch.as_tensor(flat_seq_target, dtype=torch.float32, device=device) if flat_seq_target is not None else None
            seq_mask_t = torch.as_tensor(flat_seq_mask, dtype=torch.float32, device=device) if flat_seq_mask is not None else None

            indices = np.arange(len(flat_obs))
            for _ in range(config.update_epochs):
                np.random.shuffle(indices)
                for start in range(0, len(indices), config.minibatch_size):
                    mb = indices[start : start + config.minibatch_size]
                    if config.actor_encoder == "online_gru":
                        assert hidden_t is not None
                        logp, entropy_values, value = model.evaluate_actions_recurrent(obs_t[mb], act_t[mb], hidden_t[mb])
                    else:
                        logp, entropy_values, value = model.evaluate_actions(obs_t[mb], act_t[mb])
                    entropy = entropy_values.mean()
                    ratio = torch.exp(logp - old_logp_t[mb])

                    pg_loss_1 = -adv_t[mb] * ratio
                    pg_loss_2 = -adv_t[mb] * torch.clamp(ratio, 1.0 - config.clip_coef, 1.0 + config.clip_coef)
                    pg_loss = torch.max(pg_loss_1, pg_loss_2).mean()
                    value_loss = 0.5 * torch.square(value - ret_t[mb]).mean()
                    loss = pg_loss + config.vf_coef * value_loss - config.ent_coef * entropy
                    if config.action_sequence_horizon > 1 and config.sequence_aux_coef > 0.0:
                        assert seq_target_t is not None
                        assert seq_mask_t is not None
                        predicted_tail = model.action_sequence_tensor(obs_t[mb])[:, 1:, :]
                        sequence_error = torch.square(predicted_tail - seq_target_t[mb]).sum(dim=-1)
                        sequence_mask = seq_mask_t[mb]
                        sequence_loss = (sequence_error * sequence_mask).sum() / torch.clamp(sequence_mask.sum(), min=1.0)
                        loss = loss + config.sequence_aux_coef * sequence_loss

                    optimizer.zero_grad()
                    loss.backward()
                    nn.utils.clip_grad_norm_(model.parameters(), config.max_grad_norm)
                    optimizer.step()

        global_step += rollout_n * config.num_envs
        update += 1
        avg_return = float(np.mean(episode_returns)) if episode_returns else float("nan")
        row = {
            "step": global_step,
            "update": update,
            "num_envs": config.num_envs,
            "curriculum_stage": active_stage,
            "rollout_return_mean": avg_return,
            "reward_mean": float(rew_buf.mean()),
            "episode_count": len(episode_returns),
            "episode_length_mean": float(np.mean(episode_lengths)) if episode_lengths else float("nan"),
            "termination_rate": float(np.mean(episode_terminated)) if episode_terminated else float("nan"),
        }
        metric_rows.append(row)
        if update % 5 == 0 or global_step >= config.total_steps:
            print(
                f"step={global_step} update={update} "
                f"stage={active_stage} "
                f"rollout_return_mean={avg_return:.2f} "
                f"reward_mean={float(rew_buf.mean()):.3f} "
                f"episode_count={len(episode_returns)}"
            )

    if save_path is not None:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        state_dict = {key: value.detach().cpu() for key, value in model.state_dict().items()}
        torch.save(
            {
                "model_state": state_dict,
                "config": config.__dict__,
                "metadata": to_jsonable(checkpoint_metadata or {}),
            },
            save_path,
        )
    if metrics_csv_path is not None:
        write_csv_rows(metrics_csv_path, metric_rows)
    return model


def evaluate_actor(
    model: ActorCritic,
    episodes: int,
    seed: int,
    env_config: DriftEnvConfig | None = None,
) -> dict[str, float]:
    env = AutoDriftEnv(env_config or DriftEnvConfig())
    rows = []
    for episode in range(episodes):
        obs, info = env.reset(seed=seed + episode)
        rewards: list[float] = []
        lateral_errors: list[float] = []
        beta_errors: list[float] = []
        terminated = False
        truncated = False
        while not (terminated or truncated):
            action, _, _ = model.act(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            rewards.append(float(reward))
            lateral_errors.append(float(info["lateral_error"]))
            beta_errors.append(abs(float(info["beta"])) - float(info["beta_target"]))
        rows.append(
            {
                "return": float(np.sum(rewards)),
                "steps": float(info["step"]),
                "terminated": float(terminated),
                "lateral_rmse": float(np.sqrt(np.mean(np.square(lateral_errors)))) if lateral_errors else float("nan"),
                "beta_abs_error": float(np.mean(np.abs(beta_errors))) if beta_errors else float("nan"),
            }
        )
    return {
        "return_mean": float(np.mean([row["return"] for row in rows])),
        "steps_mean": float(np.mean([row["steps"] for row in rows])),
        "termination_rate": float(np.mean([row["terminated"] for row in rows])),
        "lateral_rmse_mean": float(np.mean([row["lateral_rmse"] for row in rows])),
        "beta_abs_error_mean": float(np.mean([row["beta_abs_error"] for row in rows])),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a PPO policy on AutoDrift.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--total-steps", type=int, default=None)
    parser.add_argument("--rollout-steps", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default=None)
    parser.add_argument("--save", type=Path, default=None)
    parser.add_argument("--init-checkpoint", type=Path, default=None)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--run-name", type=str, default="ppo")
    parser.add_argument("--eval-episodes", type=int, default=None)
    args = parser.parse_args()

    ppo_defaults = PPOConfig()
    config_data = {field.name: getattr(ppo_defaults, field.name) for field in fields(PPOConfig)}
    eval_episodes = 3
    raw_config = {}
    if args.config is not None:
        raw_config = read_json(args.config)
        ppo_config = raw_config.get("ppo", raw_config)
        for key in config_data:
            if key in ppo_config:
                config_data[key] = ppo_config[key]
        if "eval_episodes" in ppo_config:
            eval_episodes = int(ppo_config["eval_episodes"])

    cli_overrides = {
        "total_steps": args.total_steps,
        "rollout_steps": args.rollout_steps,
        "seed": args.seed,
        "device": args.device,
    }
    for key, value in cli_overrides.items():
        if value is not None:
            config_data[key] = value
    if args.eval_episodes is not None:
        eval_episodes = args.eval_episodes

    config = PPOConfig(**config_data)
    env_data = raw_config.get("env", {})
    env_config = build_env_config(env_data)
    curriculum = build_curriculum(env_data, raw_config.get("curriculum", []))
    run_dir = args.run_dir or make_run_dir(prefix=args.run_name, seed=config.seed)
    save_path = args.save or run_dir / "checkpoint.pt"
    train_metrics_csv = run_dir / "train_metrics.csv"
    write_json(
        run_dir / "config.json",
        {
            "run_type": "ppo_train",
            "command": sys.argv,
            "config_file": args.config,
            "ppo": config,
            "env": env_config,
            "curriculum": curriculum,
            "eval_episodes": eval_episodes,
            "save_path": save_path,
            "init_checkpoint": args.init_checkpoint,
        },
    )

    model = train(
        config,
        save_path=save_path,
        metrics_csv_path=train_metrics_csv,
        env_config=env_config,
        curriculum=curriculum,
        checkpoint_metadata={"env": env_config, "curriculum": curriculum},
        init_checkpoint_path=args.init_checkpoint,
    )
    summary = evaluate_actor(model, eval_episodes, config.seed + 10_000, env_config=env_config)
    write_json(run_dir / "eval_summary.json", summary)
    write_json(
        run_dir / "manifest.json",
        {
            "run_type": "ppo_train",
            "checkpoint": save_path,
            "train_metrics_csv": train_metrics_csv,
            "eval_summary_json": run_dir / "eval_summary.json",
        },
    )
    print(f"run_dir={run_dir}")
    print(f"saved={save_path}")
    print(f"eval_summary={summary}")


if __name__ == "__main__":
    main()
