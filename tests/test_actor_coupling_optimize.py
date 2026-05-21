import json

import torch

from autodrift.actor_coupling_optimize import (
    actor_coupling_trainable_parameters,
    optimize_actor_coupling,
)
from autodrift.checkpoints import load_actor_critic_checkpoint
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


def test_actor_coupling_trainable_parameters_excludes_response_gru():
    model = ActorCritic(
        obs_dim=72,
        act_dim=3,
        hidden_size=8,
        actor_encoder="human_view_online_gru",
    )

    params = actor_coupling_trainable_parameters(model)
    param_ids = {id(parameter) for parameter in params}

    assert id(list(model.response_encoder.parameters())[0]) not in param_ids
    assert id(list(model.online_gru_cell.parameters())[0]) not in param_ids
    assert id(list(model.context_encoder.parameters())[0]) not in param_ids
    assert id(list(model.response_context_fusion.parameters())[0]) in param_ids
    assert id(list(model.actor_mean.parameters())[0]) in param_ids


def test_optimize_actor_coupling_writes_loadable_checkpoint(tmp_path):
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

    summary = optimize_actor_coupling(
        checkpoint_path=checkpoint,
        env_config_path=env_config,
        episodes=3,
        seed=61,
        horizon_steps=2,
        sample_stride=1,
        max_samples=9,
        train_fraction=0.67,
        steps=2,
        batch_size=4,
        learning_rate=0.0001,
        anchor_coef=10.0,
        contrast_coef=1.0,
        action_margin=0.04,
        grad_clip_norm=1.0,
        device="cpu",
        run_dir=tmp_path / "run",
    )

    assert summary["samples"] == 9
    assert summary["after_test_action_distance_mean"] >= 0.0
    assert (tmp_path / "run" / "action_coupling_metrics.csv").exists()
    loaded, data = load_actor_critic_checkpoint(tmp_path / "run" / "optimized_checkpoint.pt", device="cpu")
    assert loaded.is_online_recurrent
    assert data["metadata"]["init_checkpoint"] == str(checkpoint)
