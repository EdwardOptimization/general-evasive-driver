"""Minimal PPO trainer for the AutoDrift environment.

This is intentionally small and dependency-light. It is good enough to start
experiments and produce baselines; if training becomes the main bottleneck, move
to a vectorized trainer such as Stable-Baselines3, CleanRL, or RL-Games.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, field, fields, replace
from pathlib import Path
import sys
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.distributions import Normal
from torch.optim import Adam

from autodrift.artifacts import make_run_dir, read_json, to_jsonable, write_csv_rows, write_json
from autodrift.config import build_curriculum, build_env_config, env_config_for_step
from autodrift.controller_profile_runtime import (
    ControllerProfileObservationWrapper,
    ObservationMaskSpec,
    mask_spec_from_config,
    profile_runtime_summary,
)
from autodrift.env import AutoDriftEnv, DriftEnvConfig, FRONT_REAR_WHEEL_OBS_DIM
from autodrift.history_baselines import build_history_baseline_spec, history_baseline_spec_to_dict
from autodrift.intervention_objectives import (
    action_mean_margin_contrast_loss,
    baseline_action_anchor_loss,
    build_snippet_action_anchor,
    load_outcome_intervention_snippets,
    load_paired_hidden_snapshots,
    load_rejected_history_preference_snippets,
    load_trajectory_action_anchor,
    logprob_intervention_contrast_loss,
    outcome_weighted_intervention_loss,
    paired_hidden_action_contrast_loss,
    rejected_history_preference_loss,
    snippet_action_anchor_loss,
    trajectory_action_anchor_loss,
)
from autodrift.vector_env import ParallelAutoDriftVectorEnv, SyncAutoDriftVectorEnv


HUMAN_VIEW_OBS_DIM = 72
HUMAN_VIEW_RESPONSE_FEATURE_DIM = 12
WHEEL_HUMAN_VIEW_OBS_DIM = HUMAN_VIEW_OBS_DIM + FRONT_REAR_WHEEL_OBS_DIM
WHEEL_HUMAN_VIEW_RESPONSE_FEATURE_DIM = HUMAN_VIEW_RESPONSE_FEATURE_DIM + FRONT_REAR_WHEEL_OBS_DIM
FULL_DYNAMICS_PRIVILEGED_FEATURE_DIM = 10
PRIVILEGED_HUMAN_VIEW_OBS_DIM = HUMAN_VIEW_OBS_DIM + FULL_DYNAMICS_PRIVILEGED_FEATURE_DIM
HUMAN_VIEW_ONLINE_RECURRENT_ENCODERS = {"response_critical_online_gru", "human_view_online_gru"}
WHEEL_HUMAN_VIEW_ONLINE_RECURRENT_ENCODER = "wheel_human_view_online_gru"
PRIVILEGED_HUMAN_VIEW_ONLINE_RECURRENT_ENCODER = "privileged_human_view_online_gru"
ONLINE_RECURRENT_ENCODERS = {
    "online_gru",
    *HUMAN_VIEW_ONLINE_RECURRENT_ENCODERS,
    WHEEL_HUMAN_VIEW_ONLINE_RECURRENT_ENCODER,
    PRIVILEGED_HUMAN_VIEW_ONLINE_RECURRENT_ENCODER,
}
FRICTION_BUCKET_AUX_OBSERVATION_MASKS = ("none", "wheel_only")
FRICTION_BUCKET_AUX_FEATURE_SOURCES = ("policy_features", "response_hidden")


def is_online_recurrent_encoder(actor_encoder: str) -> bool:
    return actor_encoder in ONLINE_RECURRENT_ENCODERS


def _metric_token(name: str) -> str:
    token = "".join(character.lower() if character.isalnum() else "_" for character in name).strip("_")
    while "__" in token:
        token = token.replace("__", "_")
    if not token:
        raise ValueError("outcome intervention source loss name must contain at least one alphanumeric character")
    return token


def normalize_outcome_intervention_source_losses(raw_sources: Any) -> list[dict[str, Any]]:
    if raw_sources in (None, ""):
        return []
    if not isinstance(raw_sources, list):
        raise ValueError("outcome_intervention_source_losses must be a list")

    normalized: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    for index, raw_source in enumerate(raw_sources):
        if not isinstance(raw_source, dict):
            raise ValueError(f"outcome_intervention_source_losses[{index}] must be an object")
        name = str(raw_source.get("name", "")).strip()
        if not name:
            raise ValueError(f"outcome_intervention_source_losses[{index}].name is required")
        metric_token = _metric_token(name)
        if metric_token in seen_names:
            raise ValueError(f"duplicate outcome intervention source loss name: {name}")
        seen_names.add(metric_token)
        snapshot_npz = str(raw_source.get("snapshot_npz", "")).strip()
        if not snapshot_npz:
            raise ValueError(f"outcome_intervention_source_losses[{index}].snapshot_npz is required")
        coef = float(raw_source.get("coef", 0.0))
        if coef <= 0.0:
            raise ValueError(f"outcome_intervention_source_losses[{index}].coef must be positive")
        batch_size = int(raw_source.get("batch_size", 128))
        if batch_size < 1:
            raise ValueError(f"outcome_intervention_source_losses[{index}].batch_size must be positive")
        logprob_margin = float(raw_source.get("logprob_margin", 0.05))
        if logprob_margin < 0.0:
            raise ValueError(f"outcome_intervention_source_losses[{index}].logprob_margin cannot be negative")
        normalized.append(
            {
                "name": name,
                "metric_token": metric_token,
                "snapshot_npz": snapshot_npz,
                "coef": coef,
                "batch_size": batch_size,
                "logprob_margin": logprob_margin,
            }
        )
    return normalized


def validate_rejected_history_preference_aux_config(
    config: "PPOConfig",
    *,
    uses_online_recurrent: bool,
) -> None:
    if config.rejected_history_preference_aux_coef < 0.0:
        raise ValueError("rejected_history_preference_aux_coef cannot be negative")
    if config.rejected_history_preference_aux_coef <= 0.0:
        return
    if not uses_online_recurrent or not config.recurrent_sequence_training:
        raise ValueError("rejected-history preference auxiliary loss requires online recurrent sequence training")
    if not str(config.rejected_history_preference_snapshot_npz).strip():
        raise ValueError(
            "rejected_history_preference_snapshot_npz is required when rejected-history preference auxiliary loss is enabled"
        )
    if config.rejected_history_preference_batch_size < 1:
        raise ValueError("rejected_history_preference_batch_size must be positive")
    if config.rejected_history_preference_preferred_logprob_margin < 0.0:
        raise ValueError("rejected_history_preference_preferred_logprob_margin cannot be negative")
    if config.rejected_history_preference_wrong_logprob_margin < 0.0:
        raise ValueError("rejected_history_preference_wrong_logprob_margin cannot be negative")
    if config.rejected_history_preference_wrong_preference_coef < 0.0:
        raise ValueError("rejected_history_preference_wrong_preference_coef cannot be negative")


def rejected_history_preference_auxiliary_loss(
    model: nn.Module,
    snippets: Any,
    config: "PPOConfig",
) -> torch.Tensor:
    return rejected_history_preference_loss(
        model,
        snippets,
        batch_size=config.rejected_history_preference_batch_size,
        preferred_logprob_margin=config.rejected_history_preference_preferred_logprob_margin,
        wrong_logprob_margin=config.rejected_history_preference_wrong_logprob_margin,
        wrong_preference_coef=config.rejected_history_preference_wrong_preference_coef,
    )


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
    freeze_log_std: bool = False
    actor_encoder: str = "mlp"
    actor_history_length: int = 1
    history_baseline_level: str = "unspecified"
    action_sequence_horizon: int = 1
    sequence_aux_coef: float = 0.0
    recurrent_sequence_training: bool = False
    response_prediction_aux_coef: float = 0.0
    response_prediction_dim: int = 0
    response_prediction_horizon: int = 1
    response_prediction_stride: int = 1
    hidden_contrast_aux_coef: float = 0.0
    hidden_contrast_margin: float = 0.05
    action_contrast_aux_coef: float = 0.0
    action_contrast_margin: float = 0.15
    paired_hidden_action_contrast_aux_coef: float = 0.0
    paired_hidden_action_contrast_margin: float = 0.08
    paired_hidden_snapshot_npz: str = ""
    paired_hidden_snapshot_batch_size: int = 128
    outcome_intervention_aux_coef: float = 0.0
    outcome_intervention_snapshot_npz: str = ""
    outcome_intervention_batch_size: int = 128
    outcome_intervention_logprob_margin: float = 0.05
    outcome_intervention_source_losses: list[dict[str, Any]] = field(default_factory=list)
    rejected_history_preference_aux_coef: float = 0.0
    rejected_history_preference_snapshot_npz: str = ""
    rejected_history_preference_batch_size: int = 128
    rejected_history_preference_preferred_logprob_margin: float = 0.05
    rejected_history_preference_wrong_logprob_margin: float = 0.05
    rejected_history_preference_wrong_preference_coef: float = 1.0
    friction_bucket_aux_coef: float = 0.0
    friction_bucket_aux_observation_mask: str = "none"
    friction_bucket_aux_feature_source: str = "policy_features"
    baseline_action_anchor_coef: float = 0.0
    baseline_action_anchor_checkpoint: str = ""
    baseline_action_anchor_negative_advantage_only: bool = False
    snippet_action_anchor_coef: float = 0.0
    snippet_action_anchor_checkpoint: str = ""
    snippet_action_anchor_snapshot_npz: str = ""
    snippet_action_anchor_batch_size: int = 128
    snippet_action_anchor_preferred_only: bool = True
    trajectory_action_anchor_coef: float = 0.0
    trajectory_action_anchor_snapshot_npz: str = ""
    trajectory_action_anchor_batch_size: int = 128
    checkpoint_interval_steps: int = 0
    training_seed_csv: str = ""
    training_seed_mix_probability: float = 1.0
    vector_env_mode: str = "sync"
    vector_env_start_method: str = "fork"
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
        response_prediction_dim: int = 0,
        response_prediction_horizon: int = 1,
    ):
        super().__init__()
        if action_sequence_horizon < 1:
            raise ValueError("action_sequence_horizon must be at least 1")
        if response_prediction_dim < 0:
            raise ValueError("response_prediction_dim cannot be negative")
        if response_prediction_horizon < 1:
            raise ValueError("response_prediction_horizon must be at least 1")
        if actor_encoder not in {"mlp", "temporal_gru", *ONLINE_RECURRENT_ENCODERS}:
            raise ValueError(
                "actor_encoder must be one of: mlp, temporal_gru, online_gru, response_critical_online_gru, "
                "human_view_online_gru, wheel_human_view_online_gru, privileged_human_view_online_gru"
            )
        if actor_history_length < 1:
            raise ValueError("actor_history_length must be at least 1")
        self.obs_dim = int(obs_dim)
        self.act_dim = int(act_dim)
        self.actor_encoder = actor_encoder
        self.actor_history_length = int(actor_history_length)
        self.action_sequence_horizon = int(action_sequence_horizon)
        self.response_prediction_dim = int(response_prediction_dim)
        self.response_prediction_horizon = int(response_prediction_horizon)
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
            self.response_encoder = None
            self.context_encoder = None
            self.response_context_fusion = None
            self.response_feature_indices = ()
            self.context_feature_indices = ()
            self.privileged_feature_indices = ()
            self.privileged_encoder = None
            self.privileged_residual = None
        elif self.actor_encoder in (
            HUMAN_VIEW_ONLINE_RECURRENT_ENCODERS
            | {WHEEL_HUMAN_VIEW_ONLINE_RECURRENT_ENCODER, PRIVILEGED_HUMAN_VIEW_ONLINE_RECURRENT_ENCODER}
        ):
            if self.actor_encoder == PRIVILEGED_HUMAN_VIEW_ONLINE_RECURRENT_ENCODER:
                if obs_dim != PRIVILEGED_HUMAN_VIEW_OBS_DIM:
                    raise ValueError(
                        "privileged human-view online GRU actors require the 82-value frame "
                        "with the first 72 values matching the human-view contract"
                    )
                context_limit = HUMAN_VIEW_OBS_DIM
                self.privileged_feature_indices = tuple(range(HUMAN_VIEW_OBS_DIM, PRIVILEGED_HUMAN_VIEW_OBS_DIM))
                response_limit = HUMAN_VIEW_RESPONSE_FEATURE_DIM
            elif self.actor_encoder == WHEEL_HUMAN_VIEW_ONLINE_RECURRENT_ENCODER:
                if obs_dim != WHEEL_HUMAN_VIEW_OBS_DIM:
                    raise ValueError("wheel human-view online GRU actors require the canonical 85-value actor frame")
                context_limit = obs_dim
                self.privileged_feature_indices = ()
                response_limit = WHEEL_HUMAN_VIEW_RESPONSE_FEATURE_DIM
            else:
                if obs_dim != HUMAN_VIEW_OBS_DIM:
                    raise ValueError("human-view online GRU actors require the canonical 72-value actor frame")
                context_limit = obs_dim
                self.privileged_feature_indices = ()
                response_limit = HUMAN_VIEW_RESPONSE_FEATURE_DIM
            self.shared = None
            self.frame_encoder = None
            self.temporal_gru = None
            self.response_feature_indices = tuple(range(response_limit))
            self.context_feature_indices = tuple(range(response_limit, context_limit))
            self.response_encoder = nn.Sequential(
                nn.Linear(len(self.response_feature_indices), hidden_size),
                nn.Tanh(),
            )
            self.context_encoder = nn.Sequential(
                nn.Linear(len(self.context_feature_indices), hidden_size),
                nn.Tanh(),
            )
            self.online_gru_cell = nn.GRUCell(hidden_size, hidden_size)
            self.response_context_fusion = nn.Sequential(
                nn.Linear(hidden_size * 3, hidden_size),
                nn.Tanh(),
            )
            if self.actor_encoder == PRIVILEGED_HUMAN_VIEW_ONLINE_RECURRENT_ENCODER:
                self.privileged_encoder = nn.Sequential(
                    nn.Linear(len(self.privileged_feature_indices), hidden_size),
                    nn.Tanh(),
                )
                self.privileged_residual = nn.Linear(hidden_size * 3, hidden_size)
                nn.init.zeros_(self.privileged_residual.weight)
                nn.init.zeros_(self.privileged_residual.bias)
            else:
                self.privileged_encoder = None
                self.privileged_residual = None
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
            self.response_encoder = None
            self.context_encoder = None
            self.response_context_fusion = None
            self.response_feature_indices = ()
            self.context_feature_indices = ()
            self.privileged_feature_indices = ()
            self.privileged_encoder = None
            self.privileged_residual = None
        self.actor_mean = nn.Linear(hidden_size, act_dim)
        self.critic = nn.Linear(hidden_size, 1)
        self.log_std = nn.Parameter(torch.full((act_dim,), float(log_std_init)))
        self.sequence_tail = (
            nn.Linear(hidden_size, (self.action_sequence_horizon - 1) * act_dim)
            if self.action_sequence_horizon > 1
            else None
        )
        self.response_prediction_head = (
            nn.Linear(hidden_size + act_dim, self.response_prediction_dim * self.response_prediction_horizon)
            if self.response_prediction_dim > 0
            else None
        )

    def features_tensor(self, obs: torch.Tensor) -> torch.Tensor:
        if self.actor_encoder == "mlp":
            assert self.shared is not None
            return self.shared(obs)
        if self.is_online_recurrent:
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

    @property
    def is_online_recurrent(self) -> bool:
        return is_online_recurrent_encoder(self.actor_encoder)

    def _response_critical_features_tensor(self, obs: torch.Tensor, hidden: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        assert self.response_encoder is not None
        assert self.context_encoder is not None
        assert self.online_gru_cell is not None
        assert self.response_context_fusion is not None
        response_indices = torch.as_tensor(self.response_feature_indices, dtype=torch.long, device=obs.device)
        context_indices = torch.as_tensor(self.context_feature_indices, dtype=torch.long, device=obs.device)
        response_obs = obs.index_select(dim=-1, index=response_indices)
        context_obs = obs.index_select(dim=-1, index=context_indices)
        response_encoded = self.response_encoder(response_obs)
        context_encoded = self.context_encoder(context_obs)
        next_hidden = self.online_gru_cell(response_encoded, hidden)
        fused = self.response_context_fusion(torch.cat([next_hidden, context_encoded, next_hidden * context_encoded], dim=-1))
        if self.privileged_encoder is not None and self.privileged_residual is not None:
            privileged_indices = torch.as_tensor(self.privileged_feature_indices, dtype=torch.long, device=obs.device)
            privileged_obs = obs.index_select(dim=-1, index=privileged_indices)
            privileged_encoded = self.privileged_encoder(privileged_obs)
            fused = fused + self.privileged_residual(
                torch.cat([fused, privileged_encoded, fused * privileged_encoded], dim=-1)
            )
        return fused, next_hidden

    def recurrent_features_tensor(self, obs: torch.Tensor, hidden: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        if not self.is_online_recurrent:
            raise RuntimeError("recurrent_features_tensor requires an online recurrent actor_encoder")
        if self.actor_encoder in (
            HUMAN_VIEW_ONLINE_RECURRENT_ENCODERS
            | {WHEEL_HUMAN_VIEW_ONLINE_RECURRENT_ENCODER, PRIVILEGED_HUMAN_VIEW_ONLINE_RECURRENT_ENCODER}
        ):
            return self._response_critical_features_tensor(obs, hidden)
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
        if not self.is_online_recurrent:
            raise RuntimeError("evaluate_actions_recurrent_sequence requires an online recurrent actor_encoder")
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

    def action_mean_recurrent_sequence(
        self,
        obs: torch.Tensor,
        initial_hidden: torch.Tensor,
        dones: torch.Tensor,
    ) -> torch.Tensor:
        if not self.is_online_recurrent:
            raise RuntimeError("action_mean_recurrent_sequence requires an online recurrent actor_encoder")
        means = []
        hidden = initial_hidden
        for t in range(obs.shape[0]):
            dist, _, next_hidden = self.forward_recurrent(obs[t], hidden)
            means.append(torch.tanh(dist.mean))
            hidden = next_hidden
            if t < obs.shape[0] - 1:
                done_t = dones[t].to(dtype=torch.bool, device=obs.device)
                hidden = hidden.clone()
                hidden[done_t] = 0.0
        return torch.stack(means)

    def predict_response_recurrent_sequence(
        self,
        obs: torch.Tensor,
        actions: torch.Tensor,
        initial_hidden: torch.Tensor,
        dones: torch.Tensor,
    ) -> torch.Tensor:
        if not self.is_online_recurrent:
            raise RuntimeError("predict_response_recurrent_sequence requires an online recurrent actor_encoder")
        if self.response_prediction_head is None:
            raise RuntimeError("response prediction head is not enabled")
        predictions = []
        hidden = initial_hidden
        for t in range(obs.shape[0]):
            features, next_hidden = self.recurrent_features_tensor(obs[t], hidden)
            prediction = self.response_prediction_head(torch.cat([features, actions[t]], dim=-1))
            predictions.append(
                prediction.reshape(
                    prediction.shape[0],
                    self.response_prediction_horizon,
                    self.response_prediction_dim,
                )
            )
            hidden = next_hidden
            if t < obs.shape[0] - 1:
                done_t = dones[t].to(dtype=torch.bool, device=obs.device)
                hidden = hidden.clone()
                hidden[done_t] = 0.0
        return torch.stack(predictions)


def adapt_actor_critic_state(model: ActorCritic, source_state: dict[str, torch.Tensor]) -> str:
    target_state = model.state_dict()
    missing = [key for key in target_state if key not in source_state]
    unexpected = [key for key in source_state if key not in target_state]
    shape_mismatches = [
        key
        for key in source_state
        if key in target_state and tuple(source_state[key].shape) != tuple(target_state[key].shape)
    ]
    allowed_missing = {
        "response_prediction_head.weight",
        "response_prediction_head.bias",
    }
    privileged_branch_keys = {
        "privileged_encoder.0.weight",
        "privileged_encoder.0.bias",
        "privileged_residual.weight",
        "privileged_residual.bias",
    }
    if model.actor_encoder == PRIVILEGED_HUMAN_VIEW_ONLINE_RECURRENT_ENCODER:
        allowed_missing |= privileged_branch_keys
    allowed_shape_mismatches = {
        "response_prediction_head.weight",
        "response_prediction_head.bias",
    }
    if not missing and not unexpected and not shape_mismatches:
        model.load_state_dict(source_state)
        return "strict"
    wheel_response_key = "response_encoder.0.weight"
    if (
        model.actor_encoder == WHEEL_HUMAN_VIEW_ONLINE_RECURRENT_ENCODER
        and wheel_response_key in shape_mismatches
        and not unexpected
        and set(missing).issubset(allowed_missing)
        and set(shape_mismatches).issubset(allowed_shape_mismatches | {wheel_response_key})
    ):
        source_response_weight = source_state[wheel_response_key]
        target_response_weight = target_state[wheel_response_key]
        if (
            tuple(source_response_weight.shape)
            != (target_response_weight.shape[0], HUMAN_VIEW_RESPONSE_FEATURE_DIM)
            or tuple(target_response_weight.shape)
            != (target_response_weight.shape[0], WHEEL_HUMAN_VIEW_RESPONSE_FEATURE_DIM)
        ):
            raise RuntimeError(
                "init checkpoint cannot be partially loaded into wheel human-view response encoder: "
                f"source={tuple(source_response_weight.shape)}, target={tuple(target_response_weight.shape)}"
            )
        merged_state = dict(target_state)
        for key, value in source_state.items():
            if key not in shape_mismatches:
                merged_state[key] = value
        merged_response_weight = target_response_weight.clone()
        merged_response_weight[:, :HUMAN_VIEW_RESPONSE_FEATURE_DIM] = source_response_weight
        merged_response_weight[:, HUMAN_VIEW_RESPONSE_FEATURE_DIM:] = 0.0
        merged_state[wheel_response_key] = merged_response_weight
        model.load_state_dict(merged_state)
        partial_modes = ["wheel_response_encoder"]
        if (set(missing) | set(shape_mismatches)) & {
            "response_prediction_head.weight",
            "response_prediction_head.bias",
        }:
            partial_modes.append("response_prediction_head")
        return "partial_" + "_".join(partial_modes)
    if set(missing).issubset(allowed_missing) and not unexpected and set(shape_mismatches).issubset(
        allowed_shape_mismatches
    ):
        merged_state = dict(target_state)
        for key, value in source_state.items():
            if key not in shape_mismatches:
                merged_state[key] = value
        model.load_state_dict(merged_state)
        partial_modes = []
        if set(missing) & privileged_branch_keys:
            partial_modes.append("privileged_human_view_branch")
        if (set(missing) | set(shape_mismatches)) & {
            "response_prediction_head.weight",
            "response_prediction_head.bias",
        }:
            partial_modes.append("response_prediction_head")
        return "partial_" + "_".join(partial_modes)
    raise RuntimeError(
        "init checkpoint is incompatible: "
        f"missing={missing}, unexpected={unexpected}, shape_mismatches={shape_mismatches}"
    )


def load_init_checkpoint_state(model: ActorCritic, checkpoint_path: Path, device: torch.device) -> str:
    checkpoint = torch.load(checkpoint_path, map_location=device)
    source_state = checkpoint["model_state"]
    return adapt_actor_critic_state(model, source_state)


def save_training_checkpoint(
    model: ActorCritic,
    config: PPOConfig,
    checkpoint_metadata: dict | None,
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    state_dict = {key: value.detach().cpu() for key, value in model.state_dict().items()}
    torch.save(
        {
            "model_state": state_dict,
            "config": config.__dict__,
            "metadata": to_jsonable(checkpoint_metadata or {}),
        },
        path,
    )


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


def build_response_prediction_targets(
    observations: np.ndarray,
    dones: np.ndarray,
    response_dim: int,
    horizon: int,
    stride: int = 1,
) -> tuple[np.ndarray, np.ndarray]:
    if response_dim < 1:
        raise ValueError("response_dim must be positive")
    if horizon < 1:
        raise ValueError("horizon must be at least 1")
    if stride < 1:
        raise ValueError("stride must be at least 1")
    if response_dim > observations.shape[-1]:
        raise ValueError("response_dim cannot exceed observation dimension")
    rollout_n, num_envs, _ = observations.shape
    target = np.zeros((rollout_n, num_envs, horizon, response_dim), dtype=np.float32)
    mask = np.zeros((rollout_n, num_envs, horizon), dtype=np.float32)
    for t in range(rollout_n):
        for env_index in range(num_envs):
            for horizon_index in range(horizon):
                offset = (horizon_index + 1) * stride
                future_t = t + offset
                if future_t >= rollout_n:
                    break
                if np.any(dones[t:future_t, env_index] > 0.0):
                    break
                target[t, env_index, horizon_index] = observations[future_t, env_index, :response_dim]
                mask[t, env_index, horizon_index] = 1.0
    return target, mask


def load_training_seed_csv(path: Path | str) -> list[int]:
    seed_path = Path(path)
    with seed_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or "seed" not in reader.fieldnames:
            raise ValueError(f"training seed CSV must contain a 'seed' column: {seed_path}")
        seeds = [int(row["seed"]) for row in reader]
    if not seeds:
        raise ValueError(f"training seed CSV is empty: {seed_path}")
    return seeds


def make_vector_env(
    config: PPOConfig,
    env_config: DriftEnvConfig,
    *,
    seed: int,
    seed_sequence: list[int] | None,
    observation_mask_spec: ObservationMaskSpec | None = None,
) -> SyncAutoDriftVectorEnv | ParallelAutoDriftVectorEnv:
    if config.vector_env_mode == "sync":
        return SyncAutoDriftVectorEnv(
            num_envs=config.num_envs,
            config=env_config,
            seed=seed,
            seed_sequence=seed_sequence,
            seed_sequence_probability=config.training_seed_mix_probability,
            observation_mask_spec=observation_mask_spec,
        )
    if config.vector_env_mode == "parallel":
        return ParallelAutoDriftVectorEnv(
            num_envs=config.num_envs,
            config=env_config,
            seed=seed,
            seed_sequence=seed_sequence,
            seed_sequence_probability=config.training_seed_mix_probability,
            start_method=config.vector_env_start_method,
            observation_mask_spec=observation_mask_spec,
        )
    raise ValueError("vector_env_mode must be one of: sync, parallel")


def resolve_actor_history_config(config: PPOConfig, env_config: DriftEnvConfig) -> PPOConfig:
    if config.actor_encoder == "temporal_gru" and config.actor_history_length != env_config.history_length:
        return replace(config, actor_history_length=env_config.history_length)
    return config


def build_training_history_baseline(
    config: PPOConfig,
    env_config: DriftEnvConfig,
) -> dict[str, Any]:
    spec = build_history_baseline_spec(
        level=config.history_baseline_level,
        actor_encoder=config.actor_encoder,
        actor_history_length=config.actor_history_length,
        env_config=env_config,
    )
    return history_baseline_spec_to_dict(spec)


def friction_bucket_labels_from_mu(mu_values: np.ndarray) -> np.ndarray:
    mu = np.asarray(mu_values, dtype=np.float32)
    labels = np.ones(mu.shape, dtype=np.int64)
    labels[mu < 0.45] = 0
    labels[mu >= 0.80] = 2
    return labels


def recurrent_feature_sequence(
    model: ActorCritic,
    obs: torch.Tensor,
    initial_hidden: torch.Tensor,
    dones: torch.Tensor,
) -> torch.Tensor:
    if not model.is_online_recurrent:
        raise RuntimeError("recurrent_feature_sequence requires an online recurrent actor")
    features = []
    hidden = initial_hidden
    for t in range(obs.shape[0]):
        feature, next_hidden = model.recurrent_features_tensor(obs[t], hidden)
        features.append(feature)
        hidden = next_hidden
        if t < obs.shape[0] - 1:
            done_t = dones[t].to(dtype=torch.bool, device=obs.device)
            hidden = hidden.clone()
            hidden[done_t] = 0.0
    return torch.stack(features)


def recurrent_response_hidden_sequence(
    model: ActorCritic,
    obs: torch.Tensor,
    initial_hidden: torch.Tensor,
    dones: torch.Tensor,
) -> torch.Tensor:
    if not model.is_online_recurrent:
        raise RuntimeError("recurrent_response_hidden_sequence requires an online recurrent actor")
    hidden_states = []
    hidden = initial_hidden
    for t in range(obs.shape[0]):
        _, next_hidden = model.recurrent_features_tensor(obs[t], hidden)
        hidden_states.append(next_hidden)
        hidden = next_hidden
        if t < obs.shape[0] - 1:
            done_t = dones[t].to(dtype=torch.bool, device=obs.device)
            hidden = hidden.clone()
            hidden[done_t] = 0.0
    return torch.stack(hidden_states)


def mask_friction_aux_observations(obs: torch.Tensor, observation_mask: str) -> torch.Tensor:
    if observation_mask == "none":
        return obs
    if observation_mask == "wheel_only":
        if obs.shape[-1] < WHEEL_HUMAN_VIEW_RESPONSE_FEATURE_DIM:
            raise ValueError("wheel_only friction auxiliary mask requires a wheel-response observation frame")
        masked = obs.clone()
        masked[..., :HUMAN_VIEW_RESPONSE_FEATURE_DIM] = 0.0
        return masked
    raise ValueError(f"unknown friction bucket auxiliary observation mask: {observation_mask}")


def train(
    config: PPOConfig,
    save_path: Path | None = None,
    metrics_csv_path: Path | None = None,
    env_config: DriftEnvConfig | None = None,
    curriculum: list | None = None,
    checkpoint_metadata: dict | None = None,
    init_checkpoint_path: Path | None = None,
    observation_mask_spec: ObservationMaskSpec | None = None,
) -> ActorCritic:
    np.random.seed(config.seed)
    torch.manual_seed(config.seed)
    device = resolve_device(config.device)

    env_config = env_config or DriftEnvConfig()
    curriculum = curriculum or []
    active_env_config, active_stage = env_config_for_step(env_config, curriculum, 0)
    uses_online_recurrent = is_online_recurrent_encoder(config.actor_encoder)
    outcome_intervention_source_configs = normalize_outcome_intervention_source_losses(
        config.outcome_intervention_source_losses
    )
    config = resolve_actor_history_config(config, active_env_config)
    history_baseline_spec = build_training_history_baseline(config, active_env_config)
    checkpoint_metadata = dict(checkpoint_metadata or {})
    checkpoint_metadata["history_baseline"] = history_baseline_spec
    if uses_online_recurrent and active_env_config.history_length != 1:
        raise ValueError("online recurrent actors require env history_length=1; memory is carried in recurrent hidden state")
    if uses_online_recurrent and config.action_sequence_horizon > 1:
        raise ValueError("online recurrent actors do not currently support action_sequence_horizon > 1")
    if config.response_prediction_aux_coef > 0.0:
        if not uses_online_recurrent or not config.recurrent_sequence_training:
            raise ValueError("response prediction auxiliary loss requires online recurrent sequence training")
        if config.response_prediction_dim < 1:
            raise ValueError("response_prediction_dim must be positive when response_prediction_aux_coef > 0")
        if config.response_prediction_horizon < 1:
            raise ValueError("response_prediction_horizon must be at least 1")
        if config.response_prediction_stride < 1:
            raise ValueError("response_prediction_stride must be at least 1")
    if config.hidden_contrast_aux_coef > 0.0:
        if not uses_online_recurrent or not config.recurrent_sequence_training:
            raise ValueError("hidden contrast auxiliary loss requires online recurrent sequence training")
        if config.hidden_contrast_margin < 0.0:
            raise ValueError("hidden_contrast_margin cannot be negative")
    if config.action_contrast_aux_coef > 0.0:
        if not uses_online_recurrent or not config.recurrent_sequence_training:
            raise ValueError("action contrast auxiliary loss requires online recurrent sequence training")
        if config.action_contrast_margin < 0.0:
            raise ValueError("action_contrast_margin cannot be negative")
    if config.paired_hidden_action_contrast_aux_coef > 0.0:
        if not uses_online_recurrent or not config.recurrent_sequence_training:
            raise ValueError("paired hidden action contrast requires online recurrent sequence training")
        if not str(config.paired_hidden_snapshot_npz).strip():
            raise ValueError("paired_hidden_snapshot_npz is required when paired hidden contrast is enabled")
        if config.paired_hidden_action_contrast_margin < 0.0:
            raise ValueError("paired_hidden_action_contrast_margin cannot be negative")
        if config.paired_hidden_snapshot_batch_size < 1:
            raise ValueError("paired_hidden_snapshot_batch_size must be positive")
    if config.outcome_intervention_aux_coef > 0.0:
        if not uses_online_recurrent or not config.recurrent_sequence_training:
            raise ValueError("outcome intervention objective requires online recurrent sequence training")
        if not str(config.outcome_intervention_snapshot_npz).strip():
            raise ValueError("outcome_intervention_snapshot_npz is required when outcome intervention is enabled")
        if config.outcome_intervention_batch_size < 1:
            raise ValueError("outcome_intervention_batch_size must be positive")
        if config.outcome_intervention_logprob_margin < 0.0:
            raise ValueError("outcome_intervention_logprob_margin cannot be negative")
    if outcome_intervention_source_configs:
        if not uses_online_recurrent or not config.recurrent_sequence_training:
            raise ValueError("outcome intervention source losses require online recurrent sequence training")
    validate_rejected_history_preference_aux_config(config, uses_online_recurrent=uses_online_recurrent)
    if config.friction_bucket_aux_coef > 0.0:
        if not uses_online_recurrent or not config.recurrent_sequence_training:
            raise ValueError("friction bucket auxiliary loss requires online recurrent sequence training")
        if config.friction_bucket_aux_observation_mask not in FRICTION_BUCKET_AUX_OBSERVATION_MASKS:
            raise ValueError(
                "friction_bucket_aux_observation_mask must be one of: "
                + ", ".join(FRICTION_BUCKET_AUX_OBSERVATION_MASKS)
            )
        if config.friction_bucket_aux_feature_source not in FRICTION_BUCKET_AUX_FEATURE_SOURCES:
            raise ValueError(
                "friction_bucket_aux_feature_source must be one of: "
                + ", ".join(FRICTION_BUCKET_AUX_FEATURE_SOURCES)
            )
        if (
            config.friction_bucket_aux_observation_mask == "wheel_only"
            and config.actor_encoder != WHEEL_HUMAN_VIEW_ONLINE_RECURRENT_ENCODER
        ):
            raise ValueError("wheel_only friction auxiliary mask requires wheel_human_view_online_gru")
    if config.friction_bucket_aux_coef < 0.0:
        raise ValueError("friction_bucket_aux_coef cannot be negative")
    if config.baseline_action_anchor_coef > 0.0:
        if not str(config.baseline_action_anchor_checkpoint).strip():
            raise ValueError("baseline_action_anchor_checkpoint is required when baseline action anchor is enabled")
    if config.baseline_action_anchor_coef < 0.0:
        raise ValueError("baseline_action_anchor_coef cannot be negative")
    if config.snippet_action_anchor_coef > 0.0:
        if not uses_online_recurrent or not config.recurrent_sequence_training:
            raise ValueError("snippet action anchor requires online recurrent sequence training")
        if not str(config.snippet_action_anchor_checkpoint).strip():
            raise ValueError("snippet_action_anchor_checkpoint is required when snippet action anchor is enabled")
        snippet_anchor_npz = str(config.snippet_action_anchor_snapshot_npz).strip() or str(
            config.outcome_intervention_snapshot_npz
        ).strip()
        if not snippet_anchor_npz:
            raise ValueError("snippet_action_anchor_snapshot_npz is required when snippet action anchor is enabled")
        if config.snippet_action_anchor_batch_size < 1:
            raise ValueError("snippet_action_anchor_batch_size must be positive")
    if config.snippet_action_anchor_coef < 0.0:
        raise ValueError("snippet_action_anchor_coef cannot be negative")
    if config.trajectory_action_anchor_coef > 0.0:
        if not uses_online_recurrent or not config.recurrent_sequence_training:
            raise ValueError("trajectory action anchor requires online recurrent sequence training")
        if not str(config.trajectory_action_anchor_snapshot_npz).strip():
            raise ValueError("trajectory_action_anchor_snapshot_npz is required when trajectory anchor is enabled")
        if config.trajectory_action_anchor_batch_size < 1:
            raise ValueError("trajectory_action_anchor_batch_size must be positive")
    if config.trajectory_action_anchor_coef < 0.0:
        raise ValueError("trajectory_action_anchor_coef cannot be negative")
    if config.checkpoint_interval_steps < 0:
        raise ValueError("checkpoint_interval_steps cannot be negative")
    if not 0.0 <= config.training_seed_mix_probability <= 1.0:
        raise ValueError("training_seed_mix_probability must be in [0, 1]")
    training_seed_sequence = (
        load_training_seed_csv(config.training_seed_csv) if str(config.training_seed_csv).strip() else None
    )
    env = make_vector_env(
        config,
        active_env_config,
        seed=config.seed,
        seed_sequence=training_seed_sequence,
        observation_mask_spec=observation_mask_spec,
    )
    obs, infos = env.reset()
    if config.response_prediction_dim > env.single_observation_space.shape[0]:
        raise ValueError("response_prediction_dim cannot exceed observation dimension")
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
        response_prediction_dim=config.response_prediction_dim,
        response_prediction_horizon=config.response_prediction_horizon,
    ).to(device)
    friction_bucket_prediction_head = (
        nn.Linear(config.hidden_size, 3).to(device) if config.friction_bucket_aux_coef > 0.0 else None
    )
    if config.freeze_log_std:
        model.log_std.requires_grad_(False)
    trainable_parameters = [parameter for parameter in model.parameters() if parameter.requires_grad]
    if friction_bucket_prediction_head is not None:
        trainable_parameters.extend(friction_bucket_prediction_head.parameters())
    if not trainable_parameters:
        raise RuntimeError("no trainable parameters are available")
    optimizer = Adam(trainable_parameters, lr=config.learning_rate)
    if init_checkpoint_path is not None:
        load_mode = load_init_checkpoint_state(model, init_checkpoint_path, device)
        print(f"loaded_init_checkpoint={init_checkpoint_path} load_mode={load_mode}")
    baseline_action_anchor_model = None
    if config.baseline_action_anchor_coef > 0.0:
        baseline_action_anchor_model = ActorCritic(
            obs_dim=env.single_observation_space.shape[0],
            act_dim=env.single_action_space.shape[0],
            hidden_size=config.hidden_size,
            log_std_init=config.log_std_init,
            log_std_min=config.log_std_min,
            log_std_max=config.log_std_max,
            actor_encoder=config.actor_encoder,
            actor_history_length=config.actor_history_length,
            action_sequence_horizon=config.action_sequence_horizon,
            response_prediction_dim=config.response_prediction_dim,
            response_prediction_horizon=config.response_prediction_horizon,
        ).to(device)
        anchor_load_mode = load_init_checkpoint_state(
            baseline_action_anchor_model,
            Path(config.baseline_action_anchor_checkpoint),
            device,
        )
        baseline_action_anchor_model.eval()
        for parameter in baseline_action_anchor_model.parameters():
            parameter.requires_grad_(False)
        print(
            f"loaded_baseline_action_anchor={config.baseline_action_anchor_checkpoint} "
            f"load_mode={anchor_load_mode}"
        )
    paired_hidden_snapshots = (
        load_paired_hidden_snapshots(
            config.paired_hidden_snapshot_npz,
            device=device,
            obs_dim=env.single_observation_space.shape[0],
            hidden_size=config.hidden_size,
        )
        if config.paired_hidden_action_contrast_aux_coef > 0.0
        else None
    )
    outcome_intervention_snippets = (
        load_outcome_intervention_snippets(
            config.outcome_intervention_snapshot_npz,
            device=device,
            obs_dim=env.single_observation_space.shape[0],
            hidden_size=config.hidden_size,
            act_dim=env.single_action_space.shape[0],
        )
        if config.outcome_intervention_aux_coef > 0.0
        else None
    )
    outcome_intervention_source_snippets = [
        (
            source_config,
            load_outcome_intervention_snippets(
                source_config["snapshot_npz"],
                device=device,
                obs_dim=env.single_observation_space.shape[0],
                hidden_size=config.hidden_size,
                act_dim=env.single_action_space.shape[0],
            ),
        )
        for source_config in outcome_intervention_source_configs
    ]
    rejected_history_preference_snippets = (
        load_rejected_history_preference_snippets(
            config.rejected_history_preference_snapshot_npz,
            device=device,
            obs_dim=env.single_observation_space.shape[0],
            hidden_size=config.hidden_size,
            act_dim=env.single_action_space.shape[0],
        )
        if config.rejected_history_preference_aux_coef > 0.0
        else None
    )
    if rejected_history_preference_snippets is not None:
        print(
            f"loaded_rejected_history_preference={config.rejected_history_preference_snapshot_npz} "
            f"rows={rejected_history_preference_snippets.size}"
        )
    snippet_action_anchor = None
    if config.snippet_action_anchor_coef > 0.0:
        snippet_anchor_npz = str(config.snippet_action_anchor_snapshot_npz).strip() or str(
            config.outcome_intervention_snapshot_npz
        ).strip()
        snippet_action_anchor_snippets = (
            outcome_intervention_snippets
            if outcome_intervention_snippets is not None
            and snippet_anchor_npz == str(config.outcome_intervention_snapshot_npz).strip()
            else load_outcome_intervention_snippets(
                snippet_anchor_npz,
                device=device,
                obs_dim=env.single_observation_space.shape[0],
                hidden_size=config.hidden_size,
                act_dim=env.single_action_space.shape[0],
            )
        )
        snippet_anchor_model = ActorCritic(
            obs_dim=env.single_observation_space.shape[0],
            act_dim=env.single_action_space.shape[0],
            hidden_size=config.hidden_size,
            log_std_init=config.log_std_init,
            log_std_min=config.log_std_min,
            log_std_max=config.log_std_max,
            actor_encoder=config.actor_encoder,
            actor_history_length=config.actor_history_length,
            action_sequence_horizon=config.action_sequence_horizon,
            response_prediction_dim=config.response_prediction_dim,
            response_prediction_horizon=config.response_prediction_horizon,
        ).to(device)
        snippet_anchor_load_mode = load_init_checkpoint_state(
            snippet_anchor_model,
            Path(config.snippet_action_anchor_checkpoint),
            device,
        )
        snippet_anchor_model.eval()
        for parameter in snippet_anchor_model.parameters():
            parameter.requires_grad_(False)
        snippet_action_anchor = build_snippet_action_anchor(
            snippet_anchor_model,
            snippet_action_anchor_snippets,
            include_rejected_hidden=not config.snippet_action_anchor_preferred_only,
        )
        print(
            f"loaded_snippet_action_anchor={config.snippet_action_anchor_checkpoint} "
            f"snapshot={snippet_anchor_npz} load_mode={snippet_anchor_load_mode} "
            f"preferred_only={config.snippet_action_anchor_preferred_only}"
        )
    trajectory_action_anchor = (
        load_trajectory_action_anchor(
            config.trajectory_action_anchor_snapshot_npz,
            device=device,
            obs_dim=env.single_observation_space.shape[0],
            hidden_size=config.hidden_size,
            act_dim=env.single_action_space.shape[0],
        )
        if config.trajectory_action_anchor_coef > 0.0
        else None
    )
    if trajectory_action_anchor is not None:
        print(
            f"loaded_trajectory_action_anchor={config.trajectory_action_anchor_snapshot_npz} "
            f"rows={trajectory_action_anchor.size}"
        )
    print(f"training_device={device} num_envs={config.num_envs} curriculum_stage={active_stage}")

    global_step = 0
    update = 0
    metric_rows: list[dict[str, float | int]] = []
    recurrent_hidden = model.initial_hidden(config.num_envs, device) if uses_online_recurrent else None
    baseline_action_anchor_hidden = (
        baseline_action_anchor_model.initial_hidden(config.num_envs, device)
        if baseline_action_anchor_model is not None and uses_online_recurrent
        else None
    )
    checkpoint_interval = int(config.checkpoint_interval_steps)
    next_checkpoint_step = checkpoint_interval if checkpoint_interval > 0 else None
    while global_step < config.total_steps:
        next_env_config, next_stage = env_config_for_step(env_config, curriculum, global_step)
        if next_stage != active_stage:
            if uses_online_recurrent and next_env_config.history_length != 1:
                raise ValueError("online recurrent actors require env history_length=1 in every curriculum stage")
            build_training_history_baseline(config, next_env_config)
            active_env_config = next_env_config
            active_stage = next_stage
            env.close()
            env = make_vector_env(
                config,
                active_env_config,
                seed=config.seed + global_step,
                seed_sequence=training_seed_sequence,
            )
            obs, infos = env.reset()
            recurrent_hidden = model.initial_hidden(config.num_envs, device) if uses_online_recurrent else None
            baseline_action_anchor_hidden = (
                baseline_action_anchor_model.initial_hidden(config.num_envs, device)
                if baseline_action_anchor_model is not None and uses_online_recurrent
                else None
            )
            print(f"curriculum_stage={active_stage} step={global_step}")

        remaining = config.total_steps - global_step
        rollout_n = min(config.rollout_steps, max(1, int(np.ceil(remaining / config.num_envs))))
        obs_buf = np.zeros((rollout_n, config.num_envs, env.single_observation_space.shape[0]), dtype=np.float32)
        act_buf = np.zeros((rollout_n, config.num_envs, env.single_action_space.shape[0]), dtype=np.float32)
        logp_buf = np.zeros((rollout_n, config.num_envs), dtype=np.float32)
        rew_buf = np.zeros((rollout_n, config.num_envs), dtype=np.float32)
        done_buf = np.zeros((rollout_n, config.num_envs), dtype=np.float32)
        val_buf = np.zeros((rollout_n, config.num_envs), dtype=np.float32)
        friction_bucket_buf = (
            np.zeros((rollout_n, config.num_envs), dtype=np.int64)
            if config.friction_bucket_aux_coef > 0.0
            else None
        )
        hidden_buf = (
            np.zeros((rollout_n, config.num_envs, config.hidden_size), dtype=np.float32)
            if uses_online_recurrent
            else None
        )
        baseline_action_anchor_buf = np.zeros_like(act_buf) if baseline_action_anchor_model is not None else None

        episode_returns: list[float] = []
        episode_lengths: list[int] = []
        episode_terminated: list[float] = []
        for t in range(rollout_n):
            if friction_bucket_buf is not None:
                friction_bucket_buf[t] = friction_bucket_labels_from_mu(
                    np.asarray([float(info["mu"]) for info in infos], dtype=np.float32)
                )
            if uses_online_recurrent:
                assert recurrent_hidden is not None
                assert hidden_buf is not None
                hidden_buf[t] = recurrent_hidden.detach().cpu().numpy().astype(np.float32)
                action, logp, value, next_hidden = model.act_batch_recurrent(obs, recurrent_hidden)
            else:
                action, logp, value = model.act_batch(obs)
                next_hidden = None
            if baseline_action_anchor_model is not None:
                assert baseline_action_anchor_buf is not None
                obs_t = torch.as_tensor(obs, dtype=torch.float32, device=device)
                with torch.no_grad():
                    if uses_online_recurrent:
                        assert baseline_action_anchor_hidden is not None
                        anchor_dist, _, next_anchor_hidden = baseline_action_anchor_model.forward_recurrent(
                            obs_t,
                            baseline_action_anchor_hidden,
                        )
                    else:
                        anchor_dist, _ = baseline_action_anchor_model.forward(obs_t)
                        next_anchor_hidden = None
                    baseline_action_anchor_buf[t] = (
                        torch.tanh(anchor_dist.mean).detach().cpu().numpy().astype(np.float32)
                    )
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
            infos = [
                dict(info.get("reset_info", info)) if bool(is_done) else dict(info)
                for info, is_done in zip(step.infos, done, strict=True)
            ]
            if uses_online_recurrent:
                assert next_hidden is not None
                done_t = torch.as_tensor(done, dtype=torch.bool, device=device)
                next_hidden = next_hidden.clone()
                next_hidden[done_t] = 0.0
                recurrent_hidden = next_hidden.detach()
                if baseline_action_anchor_model is not None:
                    assert next_anchor_hidden is not None
                    next_anchor_hidden = next_anchor_hidden.clone()
                    next_anchor_hidden[done_t] = 0.0
                    baseline_action_anchor_hidden = next_anchor_hidden.detach()

        with torch.no_grad():
            if uses_online_recurrent:
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
        flat_baseline_action_anchor = (
            baseline_action_anchor_buf.reshape((-1, baseline_action_anchor_buf.shape[-1]))
            if baseline_action_anchor_buf is not None
            else None
        )
        if config.action_sequence_horizon > 1:
            seq_target_buf, seq_mask_buf = build_sequence_targets(act_buf, done_buf, config.action_sequence_horizon)
            flat_seq_target = seq_target_buf.reshape((-1, *seq_target_buf.shape[2:]))
            flat_seq_mask = seq_mask_buf.reshape((-1, *seq_mask_buf.shape[2:]))
        else:
            flat_seq_target = None
            flat_seq_mask = None
        if config.response_prediction_aux_coef > 0.0:
            response_target_buf, response_mask_buf = build_response_prediction_targets(
                obs_buf,
                done_buf,
                config.response_prediction_dim,
                config.response_prediction_horizon,
                config.response_prediction_stride,
            )
        else:
            response_target_buf = None
            response_mask_buf = None

        if uses_online_recurrent and config.recurrent_sequence_training:
            assert hidden_buf is not None
            obs_seq_t = torch.as_tensor(obs_buf, dtype=torch.float32, device=device)
            act_seq_t = torch.as_tensor(act_buf, dtype=torch.float32, device=device)
            old_logp_seq_t = torch.as_tensor(logp_buf, dtype=torch.float32, device=device)
            adv_seq_t = torch.as_tensor(advantages, dtype=torch.float32, device=device)
            ret_seq_t = torch.as_tensor(returns, dtype=torch.float32, device=device)
            done_seq_t = torch.as_tensor(done_buf, dtype=torch.float32, device=device)
            response_target_t = (
                torch.as_tensor(response_target_buf, dtype=torch.float32, device=device)
                if response_target_buf is not None
                else None
            )
            response_mask_t = (
                torch.as_tensor(response_mask_buf, dtype=torch.float32, device=device)
                if response_mask_buf is not None
                else None
            )
            initial_hidden_t = torch.as_tensor(hidden_buf[0], dtype=torch.float32, device=device)
            env_indices = np.arange(config.num_envs)
            env_minibatch = max(1, min(config.num_envs, config.minibatch_size // max(1, rollout_n)))
            response_loss_values: list[float] = []
            hidden_contrast_loss_values: list[float] = []
            action_contrast_loss_values: list[float] = []
            paired_hidden_action_contrast_loss_values: list[float] = []
            outcome_intervention_loss_values: list[float] = []
            outcome_intervention_source_loss_values: dict[str, list[float]] = {
                source_config["metric_token"]: [] for source_config, _ in outcome_intervention_source_snippets
            }
            rejected_history_preference_loss_values: list[float] = []
            friction_bucket_loss_values: list[float] = []
            friction_bucket_accuracy_values: list[float] = []
            baseline_action_anchor_loss_values: list[float] = []
            snippet_action_anchor_loss_values: list[float] = []
            trajectory_action_anchor_loss_values: list[float] = []
            friction_bucket_t = (
                torch.as_tensor(friction_bucket_buf, dtype=torch.long, device=device)
                if friction_bucket_buf is not None
                else None
            )
            baseline_action_anchor_t = (
                torch.as_tensor(baseline_action_anchor_buf, dtype=torch.float32, device=device)
                if baseline_action_anchor_buf is not None
                else None
            )
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
                    if config.hidden_contrast_aux_coef > 0.0:
                        reset_initial_hidden = torch.zeros_like(initial_hidden_t[mb_env])
                        reset_every_step_dones = torch.ones_like(done_seq_t[:, mb_env])
                        reset_logp, _, _ = model.evaluate_actions_recurrent_sequence(
                            obs_seq_t[:, mb_env],
                            act_seq_t[:, mb_env],
                            reset_initial_hidden,
                            reset_every_step_dones,
                        )
                        contrast_loss = logprob_intervention_contrast_loss(
                            logp,
                            reset_logp,
                            mb_adv,
                            margin=config.hidden_contrast_margin,
                        )
                        loss = loss + config.hidden_contrast_aux_coef * contrast_loss
                        hidden_contrast_loss_values.append(float(contrast_loss.detach().cpu().item()))
                    if config.action_contrast_aux_coef > 0.0:
                        reset_initial_hidden = torch.zeros_like(initial_hidden_t[mb_env])
                        reset_every_step_dones = torch.ones_like(done_seq_t[:, mb_env])
                        normal_action_mean = model.action_mean_recurrent_sequence(
                            obs_seq_t[:, mb_env],
                            initial_hidden_t[mb_env],
                            done_seq_t[:, mb_env],
                        )
                        reset_action_mean = model.action_mean_recurrent_sequence(
                            obs_seq_t[:, mb_env],
                            reset_initial_hidden,
                            reset_every_step_dones,
                        )
                        action_contrast_loss = action_mean_margin_contrast_loss(
                            normal_action_mean,
                            reset_action_mean,
                            mb_adv,
                            margin=config.action_contrast_margin,
                        )
                        loss = loss + config.action_contrast_aux_coef * action_contrast_loss
                        action_contrast_loss_values.append(float(action_contrast_loss.detach().cpu().item()))
                    if config.paired_hidden_action_contrast_aux_coef > 0.0:
                        assert paired_hidden_snapshots is not None
                        paired_hidden_loss = paired_hidden_action_contrast_loss(
                            model,
                            paired_hidden_snapshots,
                            batch_size=config.paired_hidden_snapshot_batch_size,
                            margin=config.paired_hidden_action_contrast_margin,
                        )
                        loss = loss + config.paired_hidden_action_contrast_aux_coef * paired_hidden_loss
                        paired_hidden_action_contrast_loss_values.append(
                            float(paired_hidden_loss.detach().cpu().item())
                        )
                    if config.outcome_intervention_aux_coef > 0.0:
                        assert outcome_intervention_snippets is not None
                        outcome_intervention_loss = outcome_weighted_intervention_loss(
                            model,
                            outcome_intervention_snippets,
                            batch_size=config.outcome_intervention_batch_size,
                            logprob_margin=config.outcome_intervention_logprob_margin,
                        )
                        loss = loss + config.outcome_intervention_aux_coef * outcome_intervention_loss
                        outcome_intervention_loss_values.append(
                            float(outcome_intervention_loss.detach().cpu().item())
                        )
                    for source_config, source_snippets in outcome_intervention_source_snippets:
                        source_loss = outcome_weighted_intervention_loss(
                            model,
                            source_snippets,
                            batch_size=int(source_config["batch_size"]),
                            logprob_margin=float(source_config["logprob_margin"]),
                        )
                        loss = loss + float(source_config["coef"]) * source_loss
                        outcome_intervention_source_loss_values[source_config["metric_token"]].append(
                            float(source_loss.detach().cpu().item())
                        )
                    if config.rejected_history_preference_aux_coef > 0.0:
                        assert rejected_history_preference_snippets is not None
                        preference_loss = rejected_history_preference_auxiliary_loss(
                            model,
                            rejected_history_preference_snippets,
                            config,
                        )
                        loss = loss + config.rejected_history_preference_aux_coef * preference_loss
                        rejected_history_preference_loss_values.append(
                            float(preference_loss.detach().cpu().item())
                        )
                    if config.snippet_action_anchor_coef > 0.0:
                        assert snippet_action_anchor is not None
                        snippet_anchor_loss_value = snippet_action_anchor_loss(
                            model,
                            snippet_action_anchor,
                            batch_size=config.snippet_action_anchor_batch_size,
                        )
                        loss = loss + config.snippet_action_anchor_coef * snippet_anchor_loss_value
                        snippet_action_anchor_loss_values.append(
                            float(snippet_anchor_loss_value.detach().cpu().item())
                        )
                    if config.trajectory_action_anchor_coef > 0.0:
                        assert trajectory_action_anchor is not None
                        trajectory_anchor_loss_value = trajectory_action_anchor_loss(
                            model,
                            trajectory_action_anchor,
                            batch_size=config.trajectory_action_anchor_batch_size,
                        )
                        loss = loss + config.trajectory_action_anchor_coef * trajectory_anchor_loss_value
                        trajectory_action_anchor_loss_values.append(
                            float(trajectory_anchor_loss_value.detach().cpu().item())
                        )
                    if config.friction_bucket_aux_coef > 0.0:
                        assert friction_bucket_prediction_head is not None
                        assert friction_bucket_t is not None
                        friction_obs_seq = mask_friction_aux_observations(
                            obs_seq_t[:, mb_env],
                            config.friction_bucket_aux_observation_mask,
                        )
                        if config.friction_bucket_aux_feature_source == "response_hidden":
                            feature_seq = recurrent_response_hidden_sequence(
                                model,
                                friction_obs_seq,
                                initial_hidden_t[mb_env],
                                done_seq_t[:, mb_env],
                            )
                        else:
                            feature_seq = recurrent_feature_sequence(
                                model,
                                friction_obs_seq,
                                initial_hidden_t[mb_env],
                                done_seq_t[:, mb_env],
                            )
                        logits = friction_bucket_prediction_head(feature_seq.reshape(-1, config.hidden_size))
                        labels = friction_bucket_t[:, mb_env].reshape(-1)
                        friction_loss = nn.functional.cross_entropy(logits, labels)
                        loss = loss + config.friction_bucket_aux_coef * friction_loss
                        with torch.no_grad():
                            friction_accuracy = (torch.argmax(logits, dim=1) == labels).float().mean()
                        friction_bucket_loss_values.append(float(friction_loss.detach().cpu().item()))
                        friction_bucket_accuracy_values.append(float(friction_accuracy.detach().cpu().item()))
                    if config.baseline_action_anchor_coef > 0.0:
                        assert baseline_action_anchor_t is not None
                        current_action_mean = model.action_mean_recurrent_sequence(
                            obs_seq_t[:, mb_env],
                            initial_hidden_t[mb_env],
                            done_seq_t[:, mb_env],
                        )
                        anchor_loss = baseline_action_anchor_loss(
                            current_action_mean,
                            baseline_action_anchor_t[:, mb_env],
                            mb_adv,
                            negative_advantage_only=config.baseline_action_anchor_negative_advantage_only,
                        )
                        loss = loss + config.baseline_action_anchor_coef * anchor_loss
                        baseline_action_anchor_loss_values.append(float(anchor_loss.detach().cpu().item()))
                    if config.response_prediction_aux_coef > 0.0 and rollout_n > 1:
                        if config.response_prediction_dim < 1:
                            raise ValueError("response_prediction_dim must be positive when response_prediction_aux_coef > 0")
                        assert response_target_t is not None
                        assert response_mask_t is not None
                        response_pred = model.predict_response_recurrent_sequence(
                            obs_seq_t[:, mb_env],
                            act_seq_t[:, mb_env],
                            initial_hidden_t[mb_env],
                            done_seq_t[:, mb_env],
                        )
                        response_target = response_target_t[:, mb_env].detach()
                        response_mask = response_mask_t[:, mb_env].unsqueeze(-1)
                        response_error = torch.square(response_pred - response_target)
                        response_loss = (response_error * response_mask).sum() / torch.clamp(
                            response_mask.sum() * config.response_prediction_dim,
                            min=1.0,
                        )
                        loss = loss + config.response_prediction_aux_coef * response_loss
                        response_loss_values.append(float(response_loss.detach().cpu().item()))

                    optimizer.zero_grad()
                    loss.backward()
                    nn.utils.clip_grad_norm_(trainable_parameters, config.max_grad_norm)
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
            baseline_action_anchor_t = (
                torch.as_tensor(flat_baseline_action_anchor, dtype=torch.float32, device=device)
                if flat_baseline_action_anchor is not None
                else None
            )
            baseline_action_anchor_loss_values: list[float] = []

            indices = np.arange(len(flat_obs))
            for _ in range(config.update_epochs):
                np.random.shuffle(indices)
                for start in range(0, len(indices), config.minibatch_size):
                    mb = indices[start : start + config.minibatch_size]
                    if uses_online_recurrent:
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
                    if config.baseline_action_anchor_coef > 0.0:
                        assert baseline_action_anchor_t is not None
                        if uses_online_recurrent:
                            assert hidden_t is not None
                            anchor_dist, _, _ = model.forward_recurrent(obs_t[mb], hidden_t[mb])
                        else:
                            anchor_dist, _ = model.forward(obs_t[mb])
                        current_action_mean = torch.tanh(anchor_dist.mean)
                        anchor_loss = baseline_action_anchor_loss(
                            current_action_mean,
                            baseline_action_anchor_t[mb],
                            adv_t[mb],
                            negative_advantage_only=config.baseline_action_anchor_negative_advantage_only,
                        )
                        loss = loss + config.baseline_action_anchor_coef * anchor_loss
                        baseline_action_anchor_loss_values.append(float(anchor_loss.detach().cpu().item()))

                    optimizer.zero_grad()
                    loss.backward()
                    nn.utils.clip_grad_norm_(trainable_parameters, config.max_grad_norm)
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
        if config.response_prediction_aux_coef > 0.0 and uses_online_recurrent and config.recurrent_sequence_training:
            row["response_prediction_loss_mean"] = (
                float(np.mean(response_loss_values)) if response_loss_values else float("nan")
            )
        if config.hidden_contrast_aux_coef > 0.0 and uses_online_recurrent and config.recurrent_sequence_training:
            row["hidden_contrast_loss_mean"] = (
                float(np.mean(hidden_contrast_loss_values)) if hidden_contrast_loss_values else float("nan")
            )
        if config.action_contrast_aux_coef > 0.0 and uses_online_recurrent and config.recurrent_sequence_training:
            row["action_contrast_loss_mean"] = (
                float(np.mean(action_contrast_loss_values)) if action_contrast_loss_values else float("nan")
            )
        if (
            config.paired_hidden_action_contrast_aux_coef > 0.0
            and uses_online_recurrent
            and config.recurrent_sequence_training
        ):
            row["paired_hidden_action_contrast_loss_mean"] = (
                float(np.mean(paired_hidden_action_contrast_loss_values))
                if paired_hidden_action_contrast_loss_values
                else float("nan")
            )
        if config.outcome_intervention_aux_coef > 0.0 and uses_online_recurrent and config.recurrent_sequence_training:
            row["outcome_intervention_loss_mean"] = (
                float(np.mean(outcome_intervention_loss_values))
                if outcome_intervention_loss_values
                else float("nan")
            )
        for source_config in outcome_intervention_source_configs:
            metric_token = source_config["metric_token"]
            values = outcome_intervention_source_loss_values.get(metric_token, [])
            row[f"outcome_intervention_source_{metric_token}_loss_mean"] = (
                float(np.mean(values)) if values else float("nan")
            )
            row[f"outcome_intervention_source_{metric_token}_coef"] = float(source_config["coef"])
        if (
            config.rejected_history_preference_aux_coef > 0.0
            and uses_online_recurrent
            and config.recurrent_sequence_training
        ):
            row["rejected_history_preference_loss_mean"] = (
                float(np.mean(rejected_history_preference_loss_values))
                if rejected_history_preference_loss_values
                else float("nan")
            )
            row["rejected_history_preference_aux_coef"] = float(config.rejected_history_preference_aux_coef)
        if config.friction_bucket_aux_coef > 0.0 and uses_online_recurrent and config.recurrent_sequence_training:
            row["friction_bucket_aux_loss_mean"] = (
                float(np.mean(friction_bucket_loss_values)) if friction_bucket_loss_values else float("nan")
            )
            row["friction_bucket_aux_accuracy_mean"] = (
                float(np.mean(friction_bucket_accuracy_values)) if friction_bucket_accuracy_values else float("nan")
            )
        if config.baseline_action_anchor_coef > 0.0:
            row["baseline_action_anchor_loss_mean"] = (
                float(np.mean(baseline_action_anchor_loss_values))
                if baseline_action_anchor_loss_values
                else float("nan")
            )
        if config.snippet_action_anchor_coef > 0.0:
            row["snippet_action_anchor_loss_mean"] = (
                float(np.mean(snippet_action_anchor_loss_values))
                if snippet_action_anchor_loss_values
                else float("nan")
            )
        if config.trajectory_action_anchor_coef > 0.0:
            row["trajectory_action_anchor_loss_mean"] = (
                float(np.mean(trajectory_action_anchor_loss_values))
                if trajectory_action_anchor_loss_values
                else float("nan")
            )
        metric_rows.append(row)
        if save_path is not None and next_checkpoint_step is not None and global_step >= next_checkpoint_step:
            periodic_path = save_path.parent / "checkpoints" / f"checkpoint_step_{global_step}.pt"
            save_training_checkpoint(model, config, checkpoint_metadata, periodic_path)
            while next_checkpoint_step <= global_step:
                next_checkpoint_step += checkpoint_interval
        if update % 5 == 0 or global_step >= config.total_steps:
            print(
                f"step={global_step} update={update} "
                f"stage={active_stage} "
                f"rollout_return_mean={avg_return:.2f} "
                f"reward_mean={float(rew_buf.mean()):.3f} "
                f"episode_count={len(episode_returns)}"
            )

    if save_path is not None:
        save_training_checkpoint(model, config, checkpoint_metadata, save_path)
    if metrics_csv_path is not None:
        write_csv_rows(metrics_csv_path, metric_rows)
    env.close()
    return model


def evaluate_actor(
    model: ActorCritic,
    episodes: int,
    seed: int,
    env_config: DriftEnvConfig | None = None,
    observation_mask_spec: ObservationMaskSpec | None = None,
) -> dict[str, float]:
    env = AutoDriftEnv(env_config or DriftEnvConfig())
    if observation_mask_spec is not None and observation_mask_spec.enabled:
        env = ControllerProfileObservationWrapper(env, observation_mask_spec)
    rows = []
    for episode in range(episodes):
        obs, info = env.reset(seed=seed + episode)
        recurrent_hidden = None
        rewards: list[float] = []
        lateral_errors: list[float] = []
        beta_errors: list[float] = []
        terminated = False
        truncated = False
        while not (terminated or truncated):
            if model.is_online_recurrent:
                action, _, _, recurrent_hidden = model.act_recurrent(obs, recurrent_hidden, deterministic=True)
            else:
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
    parser.add_argument("--num-envs", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default=None)
    parser.add_argument("--vector-env-mode", choices=["sync", "parallel"], default=None)
    parser.add_argument("--vector-env-start-method", default=None)
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
    profile_mask_spec: ObservationMaskSpec | None = None
    controller_profile_runtime: dict[str, Any] | None = None
    if args.config is not None:
        raw_config = read_json(args.config)
        if "ppo" not in raw_config:
            raise ValueError(f"{args.config} is missing required top-level 'ppo' config")
        if "env" not in raw_config:
            raise ValueError(f"{args.config} is missing required top-level 'env' config")
        if "controller_profile" in raw_config:
            profile_mask_spec = mask_spec_from_config(raw_config)
            controller_profile_runtime = profile_runtime_summary(raw_config)
        ppo_config = raw_config["ppo"]
        for key in config_data:
            if key in ppo_config:
                config_data[key] = ppo_config[key]
        if "eval_episodes" in ppo_config:
            eval_episodes = int(ppo_config["eval_episodes"])

    cli_overrides = {
        "total_steps": args.total_steps,
        "rollout_steps": args.rollout_steps,
        "num_envs": args.num_envs,
        "seed": args.seed,
        "device": args.device,
        "vector_env_mode": args.vector_env_mode,
        "vector_env_start_method": args.vector_env_start_method,
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
    active_env_config, _ = env_config_for_step(env_config, curriculum, 0)
    config = resolve_actor_history_config(config, active_env_config)
    history_baseline_spec = build_training_history_baseline(config, active_env_config)
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
            "history_baseline": history_baseline_spec,
            "controller_profile_runtime": controller_profile_runtime,
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
        checkpoint_metadata={
            "env": env_config,
            "curriculum": curriculum,
            "history_baseline": history_baseline_spec,
            "controller_profile_runtime": controller_profile_runtime,
        },
        init_checkpoint_path=args.init_checkpoint,
        observation_mask_spec=profile_mask_spec,
    )
    summary = evaluate_actor(
        model,
        eval_episodes,
        config.seed + 10_000,
        env_config=env_config,
        observation_mask_spec=profile_mask_spec,
    )
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
