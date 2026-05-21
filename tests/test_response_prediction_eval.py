import numpy as np
import torch

from autodrift.env import DriftEnvConfig
from autodrift.response_prediction_eval import compute_response_prediction_metrics, evaluate_checkpoint
from autodrift.train_ppo import ActorCritic


def test_response_prediction_eval_reports_horizon_metrics():
    torch.manual_seed(3)
    model = ActorCritic(
        obs_dim=5,
        act_dim=2,
        hidden_size=8,
        actor_encoder="online_gru",
        response_prediction_dim=2,
        response_prediction_horizon=3,
    )
    observations = np.array(
        [
            [0.0, 1.0, 2.0, 3.0, 4.0],
            [0.1, 1.1, 2.1, 3.1, 4.1],
            [0.2, 1.2, 2.2, 3.2, 4.2],
            [0.3, 1.3, 2.3, 3.3, 4.3],
        ],
        dtype=np.float32,
    )
    actions = np.zeros((4, 2), dtype=np.float32)
    dones = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)

    metrics = compute_response_prediction_metrics(
        model,
        observations,
        actions,
        dones,
        stride=1,
        device=torch.device("cpu"),
    )

    assert metrics["valid_targets"] == 6.0
    assert metrics["horizon_1_valid_targets"] == 3.0
    assert metrics["horizon_2_valid_targets"] == 2.0
    assert metrics["horizon_3_valid_targets"] == 1.0
    assert metrics["mse"] >= 0.0
    assert metrics["horizon_1_mse"] >= 0.0


def test_response_prediction_eval_returns_episode_rows(tmp_path):
    model = ActorCritic(
        obs_dim=72,
        act_dim=3,
        hidden_size=8,
        actor_encoder="human_view_online_gru",
        response_prediction_dim=3,
        response_prediction_horizon=2,
    )
    checkpoint_path = tmp_path / "checkpoint.pt"
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": {
                "device": "cpu",
                "actor_encoder": "human_view_online_gru",
                "actor_history_length": 1,
                "action_sequence_horizon": 1,
                "response_prediction_dim": 3,
                "response_prediction_horizon": 2,
                "response_prediction_stride": 1,
                "log_std_init": -1.0,
                "log_std_min": -5.0,
                "log_std_max": -0.5,
            },
        },
        checkpoint_path,
    )

    row, episode_rows = evaluate_checkpoint(
        "test",
        checkpoint_path,
        env_config=DriftEnvConfig(max_steps=4, speed_range=(4.0, 4.0)),
        seeds=[11],
        device=torch.device("cpu"),
    )

    assert row["status"] == "ok"
    assert row["episodes"] == 1
    assert episode_rows
    assert episode_rows[0]["policy"] == "test"
    assert episode_rows[0]["seed"] == 11
    assert episode_rows[0]["mse"] >= 0.0
