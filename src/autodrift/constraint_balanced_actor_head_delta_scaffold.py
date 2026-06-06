"""Bounded residual actor-head delta scaffold for Route A.

This module is deliberately side-effect free: it does not load checkpoints,
touch environments, run rollouts, or decide whether a candidate is good. It only
wraps a parent actor with a deployable observation-only residual head.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable, Mapping
import re
from typing import Any

import torch
from torch import nn

from autodrift.train_ppo import HUMAN_VIEW_OBS_DIM


ACTION_DIM = 3
ACTION_CHANNELS = ("steer", "throttle", "brake")
ALLOWED_OBSERVATION_KEYS = ("observation", "obs", "actor_observation")

FORBIDDEN_ACTOR_INPUT_KEYS = frozenset(
    {
        "aeb_label",
        "aes_label",
        "beta_target",
        "brake_scale",
        "collision_label",
        "constraint_label",
        "controller_label",
        "controller_mode",
        "diagnostic_label",
        "drift_label",
        "evaluator_label",
        "failure_label",
        "future_target",
        "heading_error",
        "hidden_dynamics",
        "hidden_state",
        "mass",
        "mu",
        "objective_label",
        "offtrack_label",
        "oracle",
        "oracle_feasibility",
        "oracle_stopping_distance",
        "path_curvature",
        "path_error",
        "progress_label",
        "required_clearance",
        "route_label",
        "slip",
        "speed_ref",
        "success_label",
        "tire_force",
        "tire_stiffness",
        "ttc",
        "verdict_label",
    }
)


@dataclass(frozen=True)
class ActorHeadDeltaTrace:
    """Trace tensors for unit tests and later audits."""

    action: torch.Tensor
    parent_action: torch.Tensor
    residual_delta: torch.Tensor


def normalize_actor_input_key(key: str) -> str:
    token = re.sub(r"[^0-9A-Za-z]+", "_", str(key).strip().lower()).strip("_")
    while "__" in token:
        token = token.replace("__", "_")
    return token


def forbidden_actor_input_keys(keys: Iterable[str]) -> tuple[str, ...]:
    normalized = {normalize_actor_input_key(key) for key in keys}
    return tuple(sorted(normalized & FORBIDDEN_ACTOR_INPUT_KEYS))


def validate_actor_input_keys(keys: Iterable[str]) -> None:
    forbidden = forbidden_actor_input_keys(keys)
    if forbidden:
        joined = ", ".join(forbidden)
        raise ValueError(f"actor input contains forbidden evaluator or privileged keys: {joined}")


def _coerce_action_tensor(output: Any, *, action_dim: int) -> torch.Tensor:
    if isinstance(output, (tuple, list)):
        if not output:
            raise ValueError("actor output tuple/list cannot be empty")
        output = output[0]
    mean = getattr(output, "mean", None)
    if torch.is_tensor(mean):
        output = torch.tanh(mean)
    if not torch.is_tensor(output):
        raise TypeError("actor output must be a Tensor, distribution with Tensor mean, or tuple/list containing one")
    if output.shape[-1:] != (int(action_dim),):
        raise ValueError(f"actor output last dimension must be {action_dim}, got {tuple(output.shape)}")
    return output


def _vector_buffer(name: str, value: float | Iterable[float], *, dim: int) -> torch.Tensor:
    tensor = torch.as_tensor(value, dtype=torch.float32)
    if tensor.ndim == 0:
        tensor = tensor.repeat(int(dim))
    if tensor.shape != (int(dim),):
        raise ValueError(f"{name} must be scalar or shape ({dim},), got {tuple(tensor.shape)}")
    return tensor


class ConstraintBalancedActorHeadDeltaScaffold(nn.Module):
    """Apply a bounded residual head on top of a parent actor action."""

    def __init__(
        self,
        parent_actor: nn.Module,
        residual_head: nn.Module,
        *,
        residual_limit: float | Iterable[float] = 0.05,
        action_low: float | Iterable[float] = -1.0,
        action_high: float | Iterable[float] = 1.0,
        observation_dim: int = HUMAN_VIEW_OBS_DIM,
        action_dim: int = ACTION_DIM,
    ) -> None:
        super().__init__()
        self.parent_actor = parent_actor
        self.residual_head = residual_head
        self.observation_dim = int(observation_dim)
        self.action_dim = int(action_dim)

        limit = _vector_buffer("residual_limit", residual_limit, dim=self.action_dim)
        low = _vector_buffer("action_low", action_low, dim=self.action_dim)
        high = _vector_buffer("action_high", action_high, dim=self.action_dim)
        if torch.any(limit < 0.0):
            raise ValueError("residual_limit values must be non-negative")
        if torch.any(low >= high):
            raise ValueError("action_low values must be smaller than action_high values")
        self.register_buffer("residual_limit", limit)
        self.register_buffer("action_low", low)
        self.register_buffer("action_high", high)

    def observation_from_mapping(
        self,
        data: Mapping[str, Any],
        *,
        observation_key: str | None = None,
        strict_extra_keys: bool = True,
    ) -> torch.Tensor:
        validate_actor_input_keys(data.keys())
        if observation_key is None:
            available = [key for key in ALLOWED_OBSERVATION_KEYS if key in data]
            if len(available) != 1:
                raise ValueError("actor input mapping must contain exactly one deployable observation key")
            observation_key = available[0]
        if observation_key not in data:
            raise ValueError(f"actor input mapping missing observation key {observation_key!r}")
        if strict_extra_keys:
            extra = set(data) - {observation_key}
            if extra:
                joined = ", ".join(sorted(str(key) for key in extra))
                raise ValueError(f"actor input mapping contains non-observation keys: {joined}")
        observation = data[observation_key]
        if not torch.is_tensor(observation):
            observation = torch.as_tensor(observation, dtype=torch.float32)
        return observation

    def _validate_observation(self, observation: torch.Tensor) -> torch.Tensor:
        if not torch.is_tensor(observation):
            raise TypeError("observation must be a Tensor or deployable observation mapping")
        if observation.shape[-1:] != (self.observation_dim,):
            raise ValueError(f"observation last dimension must be {self.observation_dim}, got {tuple(observation.shape)}")
        return observation

    def _bounded_residual_delta(self, raw_delta: torch.Tensor) -> torch.Tensor:
        limit = self.residual_limit.to(device=raw_delta.device, dtype=raw_delta.dtype)
        return torch.maximum(torch.minimum(raw_delta, limit), -limit)

    def forward_with_trace(self, observation: torch.Tensor | Mapping[str, Any]) -> ActorHeadDeltaTrace:
        if isinstance(observation, Mapping):
            observation = self.observation_from_mapping(observation)
        observation = self._validate_observation(observation)
        parent_action = _coerce_action_tensor(self.parent_actor(observation), action_dim=self.action_dim)
        raw_delta = _coerce_action_tensor(self.residual_head(observation), action_dim=self.action_dim)
        residual_delta = self._bounded_residual_delta(raw_delta)
        low = self.action_low.to(device=parent_action.device, dtype=parent_action.dtype)
        high = self.action_high.to(device=parent_action.device, dtype=parent_action.dtype)
        action = torch.maximum(torch.minimum(parent_action + residual_delta, high), low)
        return ActorHeadDeltaTrace(action=action, parent_action=parent_action, residual_delta=residual_delta)

    def forward(self, observation: torch.Tensor | Mapping[str, Any]) -> torch.Tensor:
        return self.forward_with_trace(observation).action


__all__ = [
    "ACTION_CHANNELS",
    "ACTION_DIM",
    "ALLOWED_OBSERVATION_KEYS",
    "ActorHeadDeltaTrace",
    "ConstraintBalancedActorHeadDeltaScaffold",
    "FORBIDDEN_ACTOR_INPUT_KEYS",
    "forbidden_actor_input_keys",
    "normalize_actor_input_key",
    "validate_actor_input_keys",
]
