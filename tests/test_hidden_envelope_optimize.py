import json

import numpy as np
import torch

from autodrift.env import DriftEnvConfig
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.hidden_envelope_optimize import (
    collect_hidden_envelope_objective_batch,
    hidden_envelope_feature_sets_from_batch,
    normalized_target_weights,
    optimize_hidden_envelope_objective,
    trainable_hidden_envelope_parameters,
)
from autodrift.train_ppo import ActorCritic


def _write_human_view_checkpoint(path, hidden_size=8):
    model = ActorCritic(
        obs_dim=72,
        act_dim=3,
        hidden_size=hidden_size,
        actor_encoder="human_view_online_gru",
    )
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": {
                "actor_encoder": "human_view_online_gru",
                "actor_history_length": 1,
                "action_sequence_horizon": 1,
                "response_prediction_dim": 0,
                "response_prediction_horizon": 1,
                "log_std_init": -1.0,
                "log_std_min": -5.0,
                "log_std_max": -0.5,
            },
        },
        path,
    )


def test_trainable_hidden_envelope_parameters_excludes_actor_head():
    model = ActorCritic(
        obs_dim=72,
        act_dim=3,
        hidden_size=8,
        actor_encoder="human_view_online_gru",
    )

    params = trainable_hidden_envelope_parameters(model)
    param_ids = {id(parameter) for parameter in params}

    assert id(list(model.actor_mean.parameters())[0]) not in param_ids
    assert id(list(model.context_encoder.parameters())[0]) not in param_ids
    assert id(list(model.response_encoder.parameters())[0]) in param_ids
    assert id(list(model.online_gru_cell.parameters())[0]) in param_ids


def test_normalized_target_weights_validates_shape_and_values():
    weights = normalized_target_weights((3.0, 1.0, 2.0))

    np.testing.assert_allclose(weights, np.asarray([1.5, 0.5, 1.0], dtype=np.float32))

    for bad_weights in ((1.0, 2.0), (1.0, 0.0, 1.0), (1.0, float("nan"), 1.0)):
        try:
            normalized_target_weights(bad_weights)
        except ValueError:
            pass
        else:  # pragma: no cover - pytest assertion is clearer outside raises context here.
            raise AssertionError(f"expected invalid weights to fail: {bad_weights}")


def test_collect_hidden_envelope_objective_batch_keeps_episode_sequences():
    env_config = DriftEnvConfig(max_steps=4, history_length=1, action_history_mode="full")
    model = ActorCritic(
        obs_dim=72,
        act_dim=3,
        hidden_size=8,
        actor_encoder="human_view_online_gru",
    )

    batch = collect_hidden_envelope_objective_batch(
        model=model,
        env_config=env_config,
        episodes=3,
        seed=51,
        horizon_steps=2,
        sample_stride=1,
        max_samples=8,
        device=next(model.parameters()).device,
    )

    assert batch.observations.ndim == 3
    assert batch.observations.shape[1] >= 2
    assert batch.sample_mask.sum() == len(batch.rows) == 8
    assert batch.targets.shape[-1] == 3

    features, targets = hidden_envelope_feature_sets_from_batch(
        model,
        batch,
        next(model.parameters()).device,
    )
    assert features["response_hidden"].shape[0] == 8
    assert targets["future_yaw_response"].shape == (8,)
    assert np.isfinite(features["response_hidden"]).all()


def test_optimize_hidden_envelope_objective_writes_artifacts(tmp_path):
    checkpoint = tmp_path / "checkpoint.pt"
    _write_human_view_checkpoint(checkpoint)
    env_config = tmp_path / "env.json"
    env_config.write_text(
        json.dumps(
            {
                "env": {
                    "max_steps": 4,
                    "history_length": 1,
                    "action_history_mode": "full",
                    "speed_range": [4.0, 6.0],
                }
            }
        ),
        encoding="utf-8",
    )

    summary = optimize_hidden_envelope_objective(
        checkpoint_path=checkpoint,
        env_config_path=env_config,
        episodes=3,
        seed=53,
        horizon_steps=2,
        sample_stride=1,
        max_samples=9,
        train_fraction=0.67,
        ridge=0.1,
        steps=2,
        batch_size=4,
        learning_rate=0.0003,
        contrast_coef=0.5,
        contrast_margin=0.02,
        contrast_mode="per_target",
        current_response_loss_coef=0.1,
        current_response_contrast_coef=0.2,
        current_response_contrast_margin=0.01,
        target_loss_weights=(3.0, 1.0, 1.0),
        grad_clip_norm=1.0,
        device="cpu",
        run_dir=tmp_path / "run",
    )

    assert summary["samples"] == 9
    assert (tmp_path / "run" / "optimized_checkpoint.pt").exists()
    assert (tmp_path / "run" / "hidden_gain_summary.csv").exists()
    loaded, checkpoint_data = load_actor_critic_checkpoint(tmp_path / "run" / "optimized_checkpoint.pt", device="cpu")
    assert loaded.is_online_recurrent
    assert checkpoint_data["metadata"]["init_checkpoint"] == str(checkpoint)
    assert summary["contrast_mode"] == "per_target"
    assert summary["current_response_loss_coef"] == 0.1
    assert summary["current_response_contrast_coef"] == 0.2
    assert summary["target_loss_weights"]["future_braking_deceleration"] > 1.0
    assert set(summary["response_hidden_minus_reset_test_r2_delta"]) == {
        "future_braking_deceleration",
        "future_lateral_accel_response",
        "future_yaw_response",
    }
