"""Checkpoint loading utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import torch

from autodrift.train_ppo import ActorCritic, adapt_actor_critic_state, resolve_device


REQUIRED_MODEL_CONFIG_KEYS = (
    "actor_encoder",
    "actor_history_length",
    "action_sequence_horizon",
    "response_prediction_dim",
    "log_std_init",
    "log_std_min",
    "log_std_max",
)


def _require_model_config(config: dict[str, Any]) -> None:
    missing = [key for key in REQUIRED_MODEL_CONFIG_KEYS if key not in config]
    if missing:
        raise RuntimeError(f"checkpoint config is missing required model keys: {missing}")


def load_actor_critic_checkpoint(
    path: Path | str,
    device: str = "auto",
    obs_dim: int | None = None,
) -> tuple[ActorCritic, dict[str, Any]]:
    resolved_device = resolve_device(device)
    checkpoint = torch.load(Path(path), map_location=resolved_device)
    state_dict = checkpoint["model_state"]
    config = checkpoint["config"]
    _require_model_config(config)
    actor_encoder = str(config["actor_encoder"])
    actor_history_length = int(config["actor_history_length"])

    actor_head = state_dict["actor_mean.weight"]
    hidden_size = int(actor_head.shape[1])
    act_dim = int(actor_head.shape[0])
    if "shared.0.weight" in state_dict:
        first_layer = state_dict["shared.0.weight"]
        source_obs_dim = int(first_layer.shape[1])
    elif "frame_encoder.0.weight" in state_dict:
        frame_layer = state_dict["frame_encoder.0.weight"]
        source_obs_dim = int(frame_layer.shape[1]) * actor_history_length
    else:
        raise RuntimeError("checkpoint does not contain a recognized actor encoder")

    model = ActorCritic(
        obs_dim=int(obs_dim or source_obs_dim),
        act_dim=act_dim,
        hidden_size=hidden_size,
        log_std_init=float(config["log_std_init"]),
        log_std_min=float(config["log_std_min"]),
        log_std_max=float(config["log_std_max"]),
        actor_encoder=actor_encoder,
        actor_history_length=actor_history_length,
        action_sequence_horizon=int(config["action_sequence_horizon"]),
        response_prediction_dim=int(config["response_prediction_dim"]),
    ).to(resolved_device)
    adapt_actor_critic_state(model, state_dict)
    model.eval()
    return model, checkpoint
