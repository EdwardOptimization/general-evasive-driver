"""Checkpoint loading utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import torch

from autodrift.train_ppo import ActorCritic, adapt_actor_critic_state, resolve_device


def _infer_sequence_horizon(state_dict: dict[str, torch.Tensor], act_dim: int, config: dict[str, Any]) -> int:
    if "action_sequence_horizon" in config:
        return int(config["action_sequence_horizon"])
    tail = state_dict.get("sequence_tail.weight")
    if tail is None:
        return 1
    return int(tail.shape[0] // act_dim) + 1


def load_actor_critic_checkpoint(
    path: Path | str,
    device: str = "auto",
    obs_dim: int | None = None,
) -> tuple[ActorCritic, dict[str, Any]]:
    resolved_device = resolve_device(device)
    checkpoint = torch.load(Path(path), map_location=resolved_device)
    state_dict = checkpoint["model_state"]

    first_layer = state_dict["shared.0.weight"]
    actor_head = state_dict["actor_mean.weight"]
    source_obs_dim = int(first_layer.shape[1])
    hidden_size = int(first_layer.shape[0])
    act_dim = int(actor_head.shape[0])

    config = checkpoint.get("config", {})
    sequence_horizon = _infer_sequence_horizon(state_dict, act_dim, config)
    model = ActorCritic(
        obs_dim=int(obs_dim or source_obs_dim),
        act_dim=act_dim,
        hidden_size=hidden_size,
        log_std_init=float(config.get("log_std_init", -1.0)),
        log_std_min=float(config.get("log_std_min", -5.0)),
        log_std_max=float(config.get("log_std_max", -0.5)),
        action_sequence_horizon=sequence_horizon,
    ).to(resolved_device)
    adapt_actor_critic_state(model, state_dict)
    model.eval()
    return model, checkpoint
