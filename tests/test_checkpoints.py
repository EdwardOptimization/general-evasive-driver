import numpy as np
import torch

from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.train_ppo import ActorCritic


def test_actor_critic_checkpoint_loads_from_shape(tmp_path):
    model = ActorCritic(obs_dim=13, act_dim=2, hidden_size=16)
    checkpoint_path = tmp_path / "checkpoint.pt"
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": {"device": "cpu"},
        },
        checkpoint_path,
    )

    loaded, checkpoint = load_actor_critic_checkpoint(checkpoint_path, device="cpu")
    action, logp, value = loaded.act(np.zeros(13, dtype=np.float32), deterministic=True)

    assert checkpoint["config"]["device"] == "cpu"
    assert action.shape == (2,)
    assert np.isfinite(logp)
    assert np.isfinite(value)
