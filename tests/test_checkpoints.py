import numpy as np
import torch

from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.train_ppo import ActorCritic, load_init_checkpoint_state


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


def test_init_checkpoint_expands_single_frame_policy_to_history_obs(tmp_path):
    torch.manual_seed(3)
    source = ActorCritic(obs_dim=13, act_dim=2, hidden_size=16)
    checkpoint_path = tmp_path / "checkpoint.pt"
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in source.state_dict().items()},
            "config": {"device": "cpu"},
        },
        checkpoint_path,
    )

    target = ActorCritic(obs_dim=52, act_dim=2, hidden_size=16)
    load_mode = load_init_checkpoint_state(target, checkpoint_path, torch.device("cpu"))

    current_obs = torch.linspace(-0.5, 0.5, 13).unsqueeze(0)
    history_tail = torch.randn(1, 39)
    with torch.no_grad():
        source_dist, source_value = source(current_obs)
        target_dist, target_value = target(torch.cat([current_obs, history_tail], dim=1))

    assert load_mode == "partial_input_expand"
    np.testing.assert_allclose(target_dist.mean.numpy(), source_dist.mean.numpy(), atol=1e-6)
    np.testing.assert_allclose(target_value.numpy(), source_value.numpy(), atol=1e-6)
