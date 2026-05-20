"""Minimal PPO trainer for the AutoDrift environment.

This is intentionally small and dependency-light. It is good enough to start
experiments and produce baselines; if training becomes the main bottleneck, move
to a vectorized trainer such as Stable-Baselines3, CleanRL, or RL-Games.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.distributions import Normal
from torch.optim import Adam

from autodrift.env import AutoDriftEnv


@dataclass(frozen=True)
class PPOConfig:
    total_steps: int = 50_000
    rollout_steps: int = 1024
    update_epochs: int = 6
    minibatch_size: int = 256
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_coef: float = 0.2
    ent_coef: float = 0.003
    vf_coef: float = 0.5
    max_grad_norm: float = 0.5
    learning_rate: float = 3e-4
    seed: int = 5


class ActorCritic(nn.Module):
    def __init__(self, obs_dim: int, act_dim: int, hidden_size: int = 128):
        super().__init__()
        self.shared = nn.Sequential(
            nn.Linear(obs_dim, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, hidden_size),
            nn.Tanh(),
        )
        self.actor_mean = nn.Linear(hidden_size, act_dim)
        self.critic = nn.Linear(hidden_size, 1)
        self.log_std = nn.Parameter(torch.full((act_dim,), -0.5))

    def forward(self, obs: torch.Tensor) -> tuple[Normal, torch.Tensor]:
        features = self.shared(obs)
        mean = torch.tanh(self.actor_mean(features))
        std = torch.exp(self.log_std).expand_as(mean)
        return Normal(mean, std), self.critic(features).squeeze(-1)

    def act(self, obs: np.ndarray, deterministic: bool = False) -> tuple[np.ndarray, float, float]:
        obs_t = torch.as_tensor(obs, dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            dist, value = self.forward(obs_t)
            raw_action = dist.mean if deterministic else dist.sample()
            log_prob = dist.log_prob(raw_action).sum(dim=-1)
            action = torch.clamp(raw_action, -1.0, 1.0)
        return action.squeeze(0).cpu().numpy().astype(np.float32), float(log_prob.item()), float(value.item())


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


def train(config: PPOConfig, save_path: Path | None = None) -> ActorCritic:
    np.random.seed(config.seed)
    torch.manual_seed(config.seed)

    env = AutoDriftEnv()
    obs, info = env.reset(seed=config.seed)
    model = ActorCritic(obs_dim=env.observation_space.shape[0], act_dim=env.action_space.shape[0])
    optimizer = Adam(model.parameters(), lr=config.learning_rate)

    global_step = 0
    update = 0
    while global_step < config.total_steps:
        rollout_n = min(config.rollout_steps, config.total_steps - global_step)
        obs_buf = np.zeros((rollout_n, env.observation_space.shape[0]), dtype=np.float32)
        act_buf = np.zeros((rollout_n, env.action_space.shape[0]), dtype=np.float32)
        logp_buf = np.zeros(rollout_n, dtype=np.float32)
        rew_buf = np.zeros(rollout_n, dtype=np.float32)
        done_buf = np.zeros(rollout_n, dtype=np.float32)
        val_buf = np.zeros(rollout_n, dtype=np.float32)

        episode_returns: list[float] = []
        episode_return = 0.0
        for t in range(rollout_n):
            action, logp, value = model.act(obs)
            next_obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated

            obs_buf[t] = obs
            act_buf[t] = action
            logp_buf[t] = logp
            rew_buf[t] = reward
            done_buf[t] = float(done)
            val_buf[t] = value

            episode_return += reward
            obs = next_obs
            if done:
                episode_returns.append(episode_return)
                episode_return = 0.0
                obs, info = env.reset()

        with torch.no_grad():
            _, last_value_t = model.forward(torch.as_tensor(obs, dtype=torch.float32).unsqueeze(0))
        advantages, returns = compute_gae(
            rew_buf,
            done_buf,
            val_buf,
            float(last_value_t.item()),
            config.gamma,
            config.gae_lambda,
        )
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        obs_t = torch.as_tensor(obs_buf, dtype=torch.float32)
        act_t = torch.as_tensor(act_buf, dtype=torch.float32)
        old_logp_t = torch.as_tensor(logp_buf, dtype=torch.float32)
        adv_t = torch.as_tensor(advantages, dtype=torch.float32)
        ret_t = torch.as_tensor(returns, dtype=torch.float32)

        indices = np.arange(rollout_n)
        for _ in range(config.update_epochs):
            np.random.shuffle(indices)
            for start in range(0, rollout_n, config.minibatch_size):
                mb = indices[start : start + config.minibatch_size]
                dist, value = model.forward(obs_t[mb])
                logp = dist.log_prob(act_t[mb]).sum(dim=-1)
                entropy = dist.entropy().sum(dim=-1).mean()
                ratio = torch.exp(logp - old_logp_t[mb])

                pg_loss_1 = -adv_t[mb] * ratio
                pg_loss_2 = -adv_t[mb] * torch.clamp(ratio, 1.0 - config.clip_coef, 1.0 + config.clip_coef)
                pg_loss = torch.max(pg_loss_1, pg_loss_2).mean()
                value_loss = 0.5 * torch.square(value - ret_t[mb]).mean()
                loss = pg_loss + config.vf_coef * value_loss - config.ent_coef * entropy

                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), config.max_grad_norm)
                optimizer.step()

        global_step += rollout_n
        update += 1
        if update % 5 == 0 or global_step >= config.total_steps:
            avg_return = float(np.mean(episode_returns)) if episode_returns else float("nan")
            print(
                f"step={global_step} update={update} "
                f"rollout_return_mean={avg_return:.2f} "
                f"reward_mean={float(rew_buf.mean()):.3f}"
            )

    if save_path is not None:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"model_state": model.state_dict(), "config": config.__dict__}, save_path)
    return model


def evaluate_actor(model: ActorCritic, episodes: int, seed: int) -> dict[str, float]:
    env = AutoDriftEnv()
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
    parser.add_argument("--total-steps", type=int, default=50_000)
    parser.add_argument("--rollout-steps", type=int, default=1024)
    parser.add_argument("--seed", type=int, default=5)
    parser.add_argument("--save", type=Path, default=Path("runs/ppo_autodrift.pt"))
    parser.add_argument("--eval-episodes", type=int, default=3)
    args = parser.parse_args()

    config = PPOConfig(total_steps=args.total_steps, rollout_steps=args.rollout_steps, seed=args.seed)
    model = train(config, save_path=args.save)
    summary = evaluate_actor(model, args.eval_episodes, args.seed + 10_000)
    print(f"saved={args.save}")
    print(f"eval_summary={summary}")


if __name__ == "__main__":
    main()
