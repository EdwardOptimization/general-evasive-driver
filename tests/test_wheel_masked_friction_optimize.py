import json

import torch

from autodrift.train_ppo import ActorCritic
from autodrift.wheel_masked_friction_optimize import (
    _wheel_response_norms,
    optimize_wheel_masked_friction,
    trainable_response_parameters,
)


def test_wheel_response_norms_split_body_and_wheel_columns():
    model = ActorCritic(obs_dim=85, act_dim=3, hidden_size=8, actor_encoder="wheel_human_view_online_gru")
    with torch.no_grad():
        model.response_encoder[0].weight[:, :12] = 2.0
        model.response_encoder[0].weight[:, 12:25] = 3.0

    norms = _wheel_response_norms(model)

    assert norms["body_norm"] > 0.0
    assert norms["wheel_norm"] > norms["body_norm"]
    assert norms["wheel_max"] == 3.0


def test_trainable_response_parameters_excludes_actor_head():
    model = ActorCritic(obs_dim=85, act_dim=3, hidden_size=8, actor_encoder="wheel_human_view_online_gru")

    params = trainable_response_parameters(model)
    param_ids = {id(parameter) for parameter in params}

    assert id(list(model.actor_mean.parameters())[0]) not in param_ids
    assert id(list(model.response_encoder.parameters())[0]) in param_ids
    assert id(list(model.online_gru_cell.parameters())[0]) in param_ids


def test_objective_only_optimizer_ignores_non_ppo_config_keys(tmp_path):
    source = ActorCritic(obs_dim=72, act_dim=3, hidden_size=8, actor_encoder="human_view_online_gru")
    checkpoint_path = tmp_path / "m62_like.pt"
    torch.save(
        {"model_state": {key: value.detach().cpu() for key, value in source.state_dict().items()}},
        checkpoint_path,
    )
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "ppo": {
                    "hidden_size": 8,
                    "actor_encoder": "wheel_human_view_online_gru",
                    "actor_history_length": 1,
                    "eval_episodes": 2,
                },
                "env": {
                    "max_steps": 3,
                    "history_length": 1,
                    "action_history_mode": "full",
                    "wheel_observation_mode": "front_rear",
                    "speed_range": [4.0, 6.0],
                },
            }
        ),
        encoding="utf-8",
    )

    summary = optimize_wheel_masked_friction(
        config_path=config_path,
        init_checkpoint=checkpoint_path,
        episodes=2,
        seed=23,
        device="cpu",
        max_samples=None,
        train_fraction=0.5,
        steps=1,
        batch_size=4,
        learning_rate=0.0003,
        grad_clip_norm=1.0,
        run_dir=tmp_path / "run",
    )

    assert summary["load_mode"] == "partial_wheel_response_encoder"
    assert summary["samples"] > 0
    assert (tmp_path / "run" / "objective_summary.csv").exists()
