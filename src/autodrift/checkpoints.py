"""Checkpoint loading utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import torch

from autodrift.train_ppo import ActorCritic, resolve_device


def load_actor_critic_checkpoint(path: Path | str, device: str = "auto") -> tuple[ActorCritic, dict[str, Any]]:
    resolved_device = resolve_device(device)
    checkpoint = torch.load(Path(path), map_location=resolved_device)
    state_dict = checkpoint["model_state"]

    first_layer = state_dict["shared.0.weight"]
    actor_head = state_dict["actor_mean.weight"]
    obs_dim = int(first_layer.shape[1])
    hidden_size = int(first_layer.shape[0])
    act_dim = int(actor_head.shape[0])

    model = ActorCritic(obs_dim=obs_dim, act_dim=act_dim, hidden_size=hidden_size).to(resolved_device)
    model.load_state_dict(state_dict)
    model.eval()
    return model, checkpoint
