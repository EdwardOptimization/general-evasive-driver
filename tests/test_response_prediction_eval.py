import numpy as np
import torch

from autodrift.response_prediction_eval import compute_response_prediction_metrics
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
