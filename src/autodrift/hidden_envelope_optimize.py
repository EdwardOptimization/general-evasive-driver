"""Objective-only optimization for no-wheel hidden-envelope belief."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch import nn

from autodrift.artifacts import make_run_dir, to_jsonable, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import load_env_config
from autodrift.hidden_envelope_probe import (
    CURRENT_RESPONSE,
    FULL_OBSERVATION,
    POLICY_FEATURES,
    RESET_POLICY_FEATURES,
    RESET_RESPONSE_HIDDEN,
    RESPONSE_HIDDEN,
    response_feature_dim_for_model,
    summarize_hidden_envelope_gains,
)
from autodrift.input_observability_audit import (
    TARGETS,
    future_envelope_targets,
    split_by_episode,
    train_ridge_regression_probe,
)
from autodrift.train_ppo import (
    ActorCritic,
    recurrent_feature_sequence,
    recurrent_response_hidden_sequence,
    resolve_device,
)

CONTRAST_MODES = ("mean", "per_target")


@dataclass(frozen=True)
class HiddenEnvelopeObjectiveBatch:
    observations: np.ndarray
    dones: np.ndarray
    sample_mask: np.ndarray
    targets: np.ndarray
    rows: list[dict[str, Any]]


@dataclass(frozen=True)
class EnvelopeHeadMetrics:
    phase: str
    split: str
    loss: float
    reset_loss: float
    normal_minus_reset_loss: float
    current_response_loss: float
    normal_minus_current_response_loss: float
    samples: int


def normalized_target_weights(weights: tuple[float, ...] | list[float] | np.ndarray) -> np.ndarray:
    values = np.asarray(weights, dtype=np.float32)
    if values.shape != (len(TARGETS),):
        raise ValueError(f"target weights must have exactly {len(TARGETS)} values")
    if not np.isfinite(values).all():
        raise ValueError("target weights must be finite")
    if np.any(values <= 0.0):
        raise ValueError("target weights must be positive")
    return values / float(values.mean())


def trainable_hidden_envelope_parameters(model: ActorCritic) -> list[nn.Parameter]:
    if model.response_encoder is None or model.online_gru_cell is None:
        raise ValueError("hidden-envelope optimization requires a response recurrent actor")
    return [
        *model.response_encoder.parameters(),
        *model.online_gru_cell.parameters(),
    ]


def _deterministic_action_from_hidden(
    model: ActorCritic,
    observation: np.ndarray,
    hidden: torch.Tensor,
    device: torch.device,
) -> tuple[np.ndarray, torch.Tensor]:
    obs_t = torch.as_tensor(observation, dtype=torch.float32, device=device).unsqueeze(0)
    with torch.no_grad():
        dist, _, next_hidden = model.forward_recurrent(obs_t, hidden)
        action = torch.tanh(dist.mean)
    return action.squeeze(0).detach().cpu().numpy().astype(np.float32), next_hidden.detach()


def collect_hidden_envelope_objective_batch(
    model: ActorCritic,
    env_config: DriftEnvConfig,
    episodes: int,
    seed: int,
    horizon_steps: int,
    sample_stride: int,
    max_samples: int | None,
    device: torch.device,
) -> HiddenEnvelopeObjectiveBatch:
    if not model.is_online_recurrent:
        raise ValueError("hidden-envelope optimization requires an online recurrent checkpoint")
    if episodes < 2:
        raise ValueError("at least two episodes are required for episode-disjoint evaluation")
    if horizon_steps < 1:
        raise ValueError("horizon_steps must be at least 1")
    if sample_stride < 1:
        raise ValueError("sample_stride must be at least 1")

    env = AutoDriftEnv(env_config)
    episode_observations: list[np.ndarray] = []
    episode_dones: list[np.ndarray] = []
    episode_masks: list[np.ndarray] = []
    episode_targets: list[np.ndarray] = []
    rows: list[dict[str, Any]] = []

    try:
        for episode in range(episodes):
            obs, info = env.reset(seed=seed + episode)
            hidden = model.initial_hidden(1, device)
            observations: list[np.ndarray] = []
            dones: list[float] = []
            masks: list[bool] = []
            targets: list[np.ndarray] = []
            terminated = False
            truncated = False
            while not (terminated or truncated):
                observation = np.asarray(obs, dtype=np.float32)
                observations.append(observation)
                should_sample = int(info["step"]) % sample_stride == 0 and (
                    max_samples is None or len(rows) < max_samples
                )
                if should_sample:
                    target_values = future_envelope_targets(env, horizon_steps=horizon_steps)
                    target = np.asarray([target_values[name] for name in TARGETS], dtype=np.float32)
                    rows.append(
                        {
                            "episode": episode,
                            "seed": seed + episode,
                            "step": int(info["step"]),
                            "obstacle_label": str(info.get("obstacle_label", "")),
                            **target_values,
                        }
                    )
                else:
                    target = np.zeros(len(TARGETS), dtype=np.float32)
                masks.append(bool(should_sample))
                targets.append(target)

                action, next_hidden = _deterministic_action_from_hidden(model, observation, hidden, device)
                obs, _, terminated, truncated, info = env.step(action)
                done = bool(terminated or truncated)
                dones.append(float(done))
                hidden = torch.zeros_like(next_hidden) if done else next_hidden
                if max_samples is not None and len(rows) >= max_samples:
                    break
            episode_observations.append(np.asarray(observations, dtype=np.float32))
            episode_dones.append(np.asarray(dones, dtype=np.float32))
            episode_masks.append(np.asarray(masks, dtype=bool))
            episode_targets.append(np.asarray(targets, dtype=np.float32))
            if max_samples is not None and len(rows) >= max_samples:
                break
    finally:
        env.close()

    if len(rows) == 0:
        raise ValueError("hidden-envelope objective batch has no sampled states")
    max_len = max(len(item) for item in episode_observations)
    obs_dim = int(episode_observations[0].shape[1])
    episode_count = len(episode_observations)
    observations_batch = np.zeros((max_len, episode_count, obs_dim), dtype=np.float32)
    dones_batch = np.ones((max_len, episode_count), dtype=np.float32)
    sample_mask = np.zeros((max_len, episode_count), dtype=bool)
    targets_batch = np.zeros((max_len, episode_count, len(TARGETS)), dtype=np.float32)
    for index, (obs_array, done_array, mask_array, target_array) in enumerate(
        zip(episode_observations, episode_dones, episode_masks, episode_targets, strict=True)
    ):
        length = len(obs_array)
        observations_batch[:length, index] = obs_array
        dones_batch[:length, index] = done_array
        sample_mask[:length, index] = mask_array
        targets_batch[:length, index] = target_array
    return HiddenEnvelopeObjectiveBatch(
        observations=observations_batch,
        dones=dones_batch,
        sample_mask=sample_mask,
        targets=targets_batch,
        rows=rows,
    )


def _feature_sequences(
    model: ActorCritic,
    observations: torch.Tensor,
    dones: torch.Tensor,
) -> dict[str, torch.Tensor]:
    initial_hidden = model.initial_hidden(observations.shape[1], observations.device)
    reset_dones = torch.ones_like(dones)
    return {
        POLICY_FEATURES: recurrent_feature_sequence(model, observations, initial_hidden, dones),
        RESPONSE_HIDDEN: recurrent_response_hidden_sequence(model, observations, initial_hidden, dones),
        RESET_POLICY_FEATURES: recurrent_feature_sequence(model, observations, initial_hidden, reset_dones),
        RESET_RESPONSE_HIDDEN: recurrent_response_hidden_sequence(model, observations, initial_hidden, reset_dones),
    }


def _normalization(
    targets: torch.Tensor,
    train_mask: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    train_targets = targets[train_mask]
    mean = train_targets.mean(dim=0, keepdim=True)
    std = train_targets.std(dim=0, keepdim=True).clamp_min(1e-6)
    return mean, std


def _envelope_head_metrics(
    model: ActorCritic,
    envelope_head: nn.Linear,
    current_response_head: nn.Linear | None,
    observations: torch.Tensor,
    dones: torch.Tensor,
    targets: torch.Tensor,
    target_mean: torch.Tensor,
    target_std: torch.Tensor,
    response_dim: int,
    mask: torch.Tensor,
    phase: str,
    split: str,
) -> EnvelopeHeadMetrics:
    if int(mask.sum().item()) == 0:
        return EnvelopeHeadMetrics(
            phase=phase,
            split=split,
            loss=float("nan"),
            reset_loss=float("nan"),
            normal_minus_reset_loss=float("nan"),
            current_response_loss=float("nan"),
            normal_minus_current_response_loss=float("nan"),
            samples=0,
        )
    with torch.no_grad():
        features = _feature_sequences(model, observations, dones)
        normalized_targets = (targets - target_mean) / target_std
        normal_pred = envelope_head(features[RESPONSE_HIDDEN])
        reset_pred = envelope_head(features[RESET_RESPONSE_HIDDEN])
        normal_loss = torch.square(normal_pred - normalized_targets).mean(dim=-1)
        reset_loss = torch.square(reset_pred - normalized_targets).mean(dim=-1)
        if current_response_head is None:
            current_loss = torch.full_like(normal_loss, float("nan"))
        else:
            current_response = observations[..., :response_dim]
            current_pred = current_response_head(current_response)
            current_loss = torch.square(current_pred - normalized_targets).mean(dim=-1)
    return EnvelopeHeadMetrics(
        phase=phase,
        split=split,
        loss=float(normal_loss[mask].mean().item()),
        reset_loss=float(reset_loss[mask].mean().item()),
        normal_minus_reset_loss=float((normal_loss[mask] - reset_loss[mask]).mean().item()),
        current_response_loss=float(current_loss[mask].mean().item()),
        normal_minus_current_response_loss=float((normal_loss[mask] - current_loss[mask]).mean().item()),
        samples=int(mask.sum().item()),
    )


def hidden_envelope_feature_sets_from_batch(
    model: ActorCritic,
    batch: HiddenEnvelopeObjectiveBatch,
    device: torch.device,
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    observations = torch.as_tensor(batch.observations, dtype=torch.float32, device=device)
    dones = torch.as_tensor(batch.dones, dtype=torch.float32, device=device)
    sample_mask = torch.as_tensor(batch.sample_mask, dtype=torch.bool, device=device)
    with torch.no_grad():
        features = _feature_sequences(model, observations, dones)
    flat_mask = sample_mask.cpu().numpy().reshape(-1)
    flat_observations = batch.observations.reshape(-1, batch.observations.shape[-1])[flat_mask]
    response_dim = response_feature_dim_for_model(model)
    feature_arrays = {
        FULL_OBSERVATION: flat_observations.astype(np.float32),
        CURRENT_RESPONSE: flat_observations[:, :response_dim].astype(np.float32),
        POLICY_FEATURES: features[POLICY_FEATURES].detach().cpu().numpy().reshape(-1, features[POLICY_FEATURES].shape[-1])[
            flat_mask
        ].astype(np.float32),
        RESPONSE_HIDDEN: features[RESPONSE_HIDDEN].detach().cpu().numpy().reshape(-1, features[RESPONSE_HIDDEN].shape[-1])[
            flat_mask
        ].astype(np.float32),
        RESET_POLICY_FEATURES: features[RESET_POLICY_FEATURES]
        .detach()
        .cpu()
        .numpy()
        .reshape(-1, features[RESET_POLICY_FEATURES].shape[-1])[flat_mask]
        .astype(np.float32),
        RESET_RESPONSE_HIDDEN: features[RESET_RESPONSE_HIDDEN]
        .detach()
        .cpu()
        .numpy()
        .reshape(-1, features[RESET_RESPONSE_HIDDEN].shape[-1])[flat_mask]
        .astype(np.float32),
    }
    flat_targets = batch.targets.reshape(-1, batch.targets.shape[-1])[flat_mask]
    target_arrays = {name: flat_targets[:, index].astype(np.float32) for index, name in enumerate(TARGETS)}
    return feature_arrays, target_arrays


def ridge_rows_for_hidden_envelope_features(
    features: dict[str, np.ndarray],
    targets: dict[str, np.ndarray],
    train_mask: np.ndarray,
    ridge: float,
    phase: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    probe_rows: list[dict[str, Any]] = []
    for target_name, target_values in targets.items():
        for feature_name, feature_values in features.items():
            result = train_ridge_regression_probe(
                features=feature_values,
                targets=target_values,
                train_mask=train_mask,
                target_name=target_name,
                feature_set=feature_name,
                ridge=ridge,
            )
            row = dict(result.__dict__)
            row["phase"] = phase
            probe_rows.append(row)
    gain_rows = summarize_hidden_envelope_gains(probe_rows)
    for row in gain_rows:
        row["phase"] = phase
    return probe_rows, gain_rows


def save_checkpoint_like(
    model: ActorCritic,
    source_checkpoint: dict[str, Any],
    path: Path,
    metadata: dict[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": source_checkpoint["config"],
            "metadata": to_jsonable(metadata),
        },
        path,
    )


def optimize_hidden_envelope_objective(
    checkpoint_path: Path,
    env_config_path: Path,
    episodes: int,
    seed: int,
    horizon_steps: int,
    sample_stride: int,
    max_samples: int | None,
    train_fraction: float,
    ridge: float,
    steps: int,
    batch_size: int,
    learning_rate: float,
    contrast_coef: float,
    contrast_margin: float,
    contrast_mode: str,
    current_response_loss_coef: float,
    current_response_contrast_coef: float,
    current_response_contrast_margin: float,
    target_loss_weights: tuple[float, ...],
    grad_clip_norm: float,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    if contrast_mode not in CONTRAST_MODES:
        raise ValueError("contrast_mode must be one of: " + ", ".join(CONTRAST_MODES))
    resolved_device = resolve_device(device)
    torch.manual_seed(seed)
    np.random.seed(seed)
    target_weights_np = normalized_target_weights(target_loss_weights)
    model, source_checkpoint = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    env_config = load_env_config(env_config_path)
    batch = collect_hidden_envelope_objective_batch(
        model=model,
        env_config=env_config,
        episodes=episodes,
        seed=seed,
        horizon_steps=horizon_steps,
        sample_stride=sample_stride,
        max_samples=max_samples,
        device=resolved_device,
    )
    train_mask_np = split_by_episode(batch.rows, train_fraction=train_fraction, seed=seed + 31)

    for parameter in model.parameters():
        parameter.requires_grad_(False)
    trainable_model_parameters = trainable_hidden_envelope_parameters(model)
    for parameter in trainable_model_parameters:
        parameter.requires_grad_(True)
    envelope_head = nn.Linear(model.actor_mean.in_features, len(TARGETS)).to(resolved_device)
    response_dim = response_feature_dim_for_model(model)
    current_response_head: nn.Linear | None = None
    if current_response_loss_coef > 0.0 or current_response_contrast_coef > 0.0:
        current_response_head = nn.Linear(response_dim, len(TARGETS)).to(resolved_device)
    optimizer_parameters: list[nn.Parameter] = [*trainable_model_parameters, *envelope_head.parameters()]
    if current_response_head is not None:
        optimizer_parameters.extend(current_response_head.parameters())
    optimizer = torch.optim.AdamW(
        optimizer_parameters,
        lr=learning_rate,
        weight_decay=1e-4,
    )

    observations = torch.as_tensor(batch.observations, dtype=torch.float32, device=resolved_device)
    dones = torch.as_tensor(batch.dones, dtype=torch.float32, device=resolved_device)
    targets = torch.as_tensor(batch.targets, dtype=torch.float32, device=resolved_device)
    target_weights = torch.as_tensor(target_weights_np, dtype=torch.float32, device=resolved_device)
    sample_mask = torch.as_tensor(batch.sample_mask, dtype=torch.bool, device=resolved_device)
    flat_train_mask = torch.as_tensor(train_mask_np, dtype=torch.bool, device=resolved_device)
    train_mask = torch.zeros_like(sample_mask)
    test_mask = torch.zeros_like(sample_mask)
    train_mask[sample_mask] = flat_train_mask
    test_mask[sample_mask] = ~flat_train_mask
    target_mean, target_std = _normalization(targets, train_mask)

    before_features, before_targets = hidden_envelope_feature_sets_from_batch(model, batch, resolved_device)
    before_probe_rows, before_gain_rows = ridge_rows_for_hidden_envelope_features(
        before_features,
        before_targets,
        train_mask_np,
        ridge=ridge,
        phase="before",
    )
    before_head_metrics = [
        _envelope_head_metrics(
            model,
            envelope_head,
            current_response_head,
            observations,
            dones,
            targets,
            target_mean,
            target_std,
            response_dim,
            train_mask,
            "before",
            "train",
        ),
        _envelope_head_metrics(
            model,
            envelope_head,
            current_response_head,
            observations,
            dones,
            targets,
            target_mean,
            target_std,
            response_dim,
            test_mask,
            "before",
            "test",
        ),
    ]

    rng = np.random.default_rng(seed + 97)
    train_positions = torch.nonzero(train_mask.reshape(-1), as_tuple=False).squeeze(1).cpu().numpy()
    if len(train_positions) == 0:
        raise ValueError("hidden-envelope optimization has no train samples")
    train_rows: list[dict[str, Any]] = []
    for step in range(1, max(1, int(steps)) + 1):
        features = _feature_sequences(model, observations, dones)
        normal_hidden = features[RESPONSE_HIDDEN].reshape(-1, model.actor_mean.in_features)
        reset_hidden = features[RESET_RESPONSE_HIDDEN].reshape(-1, model.actor_mean.in_features)
        flat_observations = observations.reshape(-1, observations.shape[-1])
        current_response = flat_observations[:, :response_dim]
        flat_targets = ((targets - target_mean) / target_std).reshape(-1, len(TARGETS))
        batch_positions = rng.choice(
            train_positions,
            size=min(batch_size, len(train_positions)),
            replace=len(train_positions) < batch_size,
        )
        batch_index = torch.as_tensor(batch_positions, dtype=torch.long, device=resolved_device)
        normal_pred = envelope_head(normal_hidden[batch_index])
        with torch.no_grad():
            reset_pred = envelope_head(reset_hidden[batch_index])
        per_target_loss = torch.square(normal_pred - flat_targets[batch_index])
        reset_per_target_loss = torch.square(reset_pred - flat_targets[batch_index])
        per_sample_loss = (per_target_loss * target_weights).mean(dim=-1)
        reset_per_sample_loss = (reset_per_target_loss * target_weights).mean(dim=-1)
        if current_response_head is None:
            current_per_target_loss = torch.zeros_like(per_target_loss)
            current_per_sample_loss = torch.zeros_like(per_sample_loss)
        else:
            current_pred = current_response_head(current_response[batch_index])
            current_per_target_loss = torch.square(current_pred - flat_targets[batch_index])
            current_per_sample_loss = (current_per_target_loss * target_weights).mean(dim=-1)
        prediction_loss = per_sample_loss.mean()
        current_response_prediction_loss = current_per_sample_loss.mean()
        if contrast_mode == "mean":
            contrast_loss = torch.relu(contrast_margin + per_sample_loss - reset_per_sample_loss).mean()
            current_response_contrast_loss = torch.relu(
                current_response_contrast_margin + per_sample_loss - current_per_sample_loss.detach()
            ).mean()
        else:
            contrast_loss = torch.relu(contrast_margin + per_target_loss - reset_per_target_loss)
            contrast_loss = (contrast_loss * target_weights).mean(dim=-1).mean()
            current_response_contrast_loss = torch.relu(
                current_response_contrast_margin + per_target_loss - current_per_target_loss.detach()
            )
            current_response_contrast_loss = (current_response_contrast_loss * target_weights).mean(dim=-1).mean()
        loss = (
            prediction_loss
            + contrast_coef * contrast_loss
            + current_response_loss_coef * current_response_prediction_loss
            + current_response_contrast_coef * current_response_contrast_loss
        )
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        grad_norm = nn.utils.clip_grad_norm_(
            [*trainable_model_parameters, *envelope_head.parameters()],
            grad_clip_norm,
        )
        optimizer.step()
        if step == 1 or step == steps or step % max(1, steps // 10) == 0:
            train_rows.append(
                {
                    "step": step,
                    "loss": float(loss.detach().cpu().item()),
                    "prediction_loss": float(prediction_loss.detach().cpu().item()),
                    "contrast_loss": float(contrast_loss.detach().cpu().item()),
                    "current_response_prediction_loss": float(
                        current_response_prediction_loss.detach().cpu().item()
                    ),
                    "current_response_contrast_loss": float(current_response_contrast_loss.detach().cpu().item()),
                    "reset_loss": float(reset_per_sample_loss.mean().detach().cpu().item()),
                    "current_response_loss": float(current_per_sample_loss.mean().detach().cpu().item()),
                    "braking_loss_weight": float(target_weights_np[0]),
                    "yaw_loss_weight": float(target_weights_np[1]),
                    "lateral_loss_weight": float(target_weights_np[2]),
                    "contrast_mode": contrast_mode,
                    "grad_norm": float(
                        grad_norm.detach().cpu().item() if isinstance(grad_norm, torch.Tensor) else grad_norm
                    ),
                }
            )

    after_features, after_targets = hidden_envelope_feature_sets_from_batch(model, batch, resolved_device)
    after_probe_rows, after_gain_rows = ridge_rows_for_hidden_envelope_features(
        after_features,
        after_targets,
        train_mask_np,
        ridge=ridge,
        phase="after",
    )
    after_head_metrics = [
        _envelope_head_metrics(
            model,
            envelope_head,
            current_response_head,
            observations,
            dones,
            targets,
            target_mean,
            target_std,
            response_dim,
            train_mask,
            "after",
            "train",
        ),
        _envelope_head_metrics(
            model,
            envelope_head,
            current_response_head,
            observations,
            dones,
            targets,
            target_mean,
            target_std,
            response_dim,
            test_mask,
            "after",
            "test",
        ),
    ]

    run_dir.mkdir(parents=True, exist_ok=True)
    samples_csv = run_dir / "samples.csv"
    train_metrics_csv = run_dir / "train_metrics.csv"
    head_metrics_csv = run_dir / "head_metrics.csv"
    probe_summary_csv = run_dir / "probe_summary.csv"
    hidden_gain_csv = run_dir / "hidden_gain_summary.csv"
    optimized_checkpoint = run_dir / "optimized_checkpoint.pt"
    summary_json = run_dir / "summary.json"
    manifest_json = run_dir / "manifest.json"

    write_csv_rows(samples_csv, batch.rows)
    write_csv_rows(train_metrics_csv, train_rows)
    head_rows = [metric.__dict__ for metric in [*before_head_metrics, *after_head_metrics]]
    write_csv_rows(head_metrics_csv, head_rows)
    probe_rows = [*before_probe_rows, *after_probe_rows]
    gain_rows = [*before_gain_rows, *after_gain_rows]
    write_csv_rows(probe_summary_csv, probe_rows)
    write_csv_rows(hidden_gain_csv, gain_rows)
    save_checkpoint_like(
        model,
        source_checkpoint,
        optimized_checkpoint,
        {
            "run_type": "hidden_envelope_objective_only",
            "init_checkpoint": checkpoint_path,
            "env_config": env_config_path,
            "steps": steps,
            "seed": seed,
            "contrast_mode": contrast_mode,
            "current_response_loss_coef": float(current_response_loss_coef),
            "current_response_contrast_coef": float(current_response_contrast_coef),
            "current_response_contrast_margin": float(current_response_contrast_margin),
            "target_loss_weights": {
                target: float(weight) for target, weight in zip(TARGETS, target_weights_np, strict=True)
            },
        },
    )
    before_by_target = {row["target"]: row for row in before_gain_rows}
    after_by_target = {row["target"]: row for row in after_gain_rows}
    lift_delta = {
        target: float(
            after_by_target[target]["response_hidden_minus_reset_test_r2"]
            - before_by_target[target]["response_hidden_minus_reset_test_r2"]
        )
        for target in before_by_target
    }
    summary = {
        "run_type": "hidden_envelope_objective_only",
        "checkpoint": checkpoint_path,
        "optimized_checkpoint": optimized_checkpoint,
        "env_config": env_config_path,
        "episodes": episodes,
        "samples": int(len(batch.rows)),
        "train_samples": int(train_mask.sum().item()),
        "test_samples": int(test_mask.sum().item()),
        "seed": seed,
        "horizon_steps": horizon_steps,
        "sample_stride": sample_stride,
        "steps": steps,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "contrast_coef": contrast_coef,
        "contrast_margin": contrast_margin,
        "contrast_mode": contrast_mode,
        "current_response_loss_coef": float(current_response_loss_coef),
        "current_response_contrast_coef": float(current_response_contrast_coef),
        "current_response_contrast_margin": float(current_response_contrast_margin),
        "target_loss_weights": {
            target: float(weight) for target, weight in zip(TARGETS, target_weights_np, strict=True)
        },
        "before_hidden_gain_summary": before_gain_rows,
        "after_hidden_gain_summary": after_gain_rows,
        "response_hidden_minus_reset_test_r2_delta": lift_delta,
        "head_metrics": head_rows,
        "artifacts": {
            "samples_csv": samples_csv,
            "train_metrics_csv": train_metrics_csv,
            "head_metrics_csv": head_metrics_csv,
            "probe_summary_csv": probe_summary_csv,
            "hidden_gain_summary_csv": hidden_gain_csv,
            "optimized_checkpoint": optimized_checkpoint,
        },
    }
    write_json(summary_json, summary)
    write_json(
        manifest_json,
        {
            "run_type": "hidden_envelope_objective_only",
            "checkpoint": checkpoint_path,
            "env_config": env_config_path,
            "episodes": episodes,
            "seed": seed,
            "horizon_steps": horizon_steps,
            "sample_stride": sample_stride,
            "steps": steps,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "contrast_coef": contrast_coef,
            "contrast_margin": contrast_margin,
            "contrast_mode": contrast_mode,
            "current_response_loss_coef": float(current_response_loss_coef),
            "current_response_contrast_coef": float(current_response_contrast_coef),
            "current_response_contrast_margin": float(current_response_contrast_margin),
            "target_loss_weights": summary["target_loss_weights"],
            "artifacts": summary["artifacts"],
        },
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Optimize only a no-wheel hidden-envelope objective.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--seed", type=int, default=9420)
    parser.add_argument("--horizon-steps", type=int, default=15)
    parser.add_argument("--sample-stride", type=int, default=3)
    parser.add_argument("--max-samples", type=int, default=800)
    parser.add_argument("--train-fraction", type=float, default=0.70)
    parser.add_argument("--ridge", type=float, default=0.1)
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--learning-rate", type=float, default=0.0003)
    parser.add_argument("--contrast-coef", type=float, default=0.5)
    parser.add_argument("--contrast-margin", type=float, default=0.02)
    parser.add_argument("--contrast-mode", choices=CONTRAST_MODES, default="mean")
    parser.add_argument("--current-response-loss-coef", type=float, default=0.0)
    parser.add_argument("--current-response-contrast-coef", type=float, default=0.0)
    parser.add_argument("--current-response-contrast-margin", type=float, default=0.0)
    parser.add_argument(
        "--target-loss-weights",
        type=float,
        nargs=len(TARGETS),
        default=(1.0, 1.0, 1.0),
        metavar=("BRAKING", "YAW", "LATERAL"),
        help="Positive per-target loss weights; normalized to mean one.",
    )
    parser.add_argument("--grad-clip-norm", type=float, default=1.0)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="hidden_envelope_optimize", seed=args.seed)
    summary = optimize_hidden_envelope_objective(
        checkpoint_path=args.checkpoint,
        env_config_path=args.env_config,
        episodes=args.episodes,
        seed=args.seed,
        horizon_steps=args.horizon_steps,
        sample_stride=args.sample_stride,
        max_samples=args.max_samples,
        train_fraction=args.train_fraction,
        ridge=args.ridge,
        steps=args.steps,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        contrast_coef=args.contrast_coef,
        contrast_margin=args.contrast_margin,
        contrast_mode=args.contrast_mode,
        current_response_loss_coef=args.current_response_loss_coef,
        current_response_contrast_coef=args.current_response_contrast_coef,
        current_response_contrast_margin=args.current_response_contrast_margin,
        target_loss_weights=tuple(args.target_loss_weights),
        grad_clip_norm=args.grad_clip_norm,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.DataFrame(summary["after_hidden_gain_summary"]).to_string(index=False))
    print(f"run_dir={run_dir}")
    print(f"response_hidden_minus_reset_test_r2_delta={summary['response_hidden_minus_reset_test_r2_delta']}")


if __name__ == "__main__":
    main()
