import numpy as np
import torch

from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.train_ppo import ActorCritic, build_sequence_targets, load_init_checkpoint_state


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


def test_init_checkpoint_rejects_different_observation_contract(tmp_path):
    source = ActorCritic(obs_dim=13, act_dim=2, hidden_size=16)
    checkpoint_path = tmp_path / "checkpoint.pt"
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in source.state_dict().items()},
            "config": {"device": "cpu"},
        },
        checkpoint_path,
    )

    target = ActorCritic(obs_dim=10, act_dim=2, hidden_size=16)

    with np.testing.assert_raises(RuntimeError):
        load_init_checkpoint_state(target, checkpoint_path, torch.device("cpu"))


def test_sequence_actor_checkpoint_loads_and_predicts_plan(tmp_path):
    model = ActorCritic(obs_dim=20, act_dim=2, hidden_size=16, action_sequence_horizon=4)
    checkpoint_path = tmp_path / "checkpoint.pt"
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": {"device": "cpu", "action_sequence_horizon": 4},
        },
        checkpoint_path,
    )

    loaded, _ = load_actor_critic_checkpoint(checkpoint_path, device="cpu")
    sequence = loaded.predict_sequence(np.zeros(20, dtype=np.float32))
    action, _, _ = loaded.act(np.zeros(20, dtype=np.float32), deterministic=True)

    assert loaded.action_sequence_horizon == 4
    assert sequence.shape == (4, 2)
    np.testing.assert_allclose(sequence[0], action, atol=1e-6)


def test_temporal_gru_actor_checkpoint_loads_and_exposes_latent(tmp_path):
    model = ActorCritic(obs_dim=56, act_dim=2, hidden_size=16, actor_encoder="temporal_gru", actor_history_length=4)
    checkpoint_path = tmp_path / "checkpoint.pt"
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": {"device": "cpu", "actor_encoder": "temporal_gru", "actor_history_length": 4},
        },
        checkpoint_path,
    )

    loaded, _ = load_actor_critic_checkpoint(checkpoint_path, device="cpu")
    features = loaded.features_tensor(torch.zeros(3, 56))
    action, _, value = loaded.act(np.zeros(56, dtype=np.float32), deterministic=True)

    assert loaded.actor_encoder == "temporal_gru"
    assert loaded.actor_history_length == 4
    assert features.shape == (3, 16)
    assert action.shape == (2,)
    assert np.isfinite(value)


def test_online_gru_actor_checkpoint_loads_and_updates_hidden(tmp_path):
    model = ActorCritic(obs_dim=15, act_dim=2, hidden_size=16, actor_encoder="online_gru")
    checkpoint_path = tmp_path / "checkpoint.pt"
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": {"device": "cpu", "actor_encoder": "online_gru", "actor_history_length": 1},
        },
        checkpoint_path,
    )

    loaded, _ = load_actor_critic_checkpoint(checkpoint_path, device="cpu")
    observation = np.linspace(-0.5, 0.5, 15, dtype=np.float32)
    action, _, value, hidden = loaded.act_recurrent(observation, deterministic=True)
    _, _, _, next_hidden = loaded.act_recurrent(observation, hidden, deterministic=True)

    assert loaded.actor_encoder == "online_gru"
    assert action.shape == (2,)
    assert hidden.shape == (1, 16)
    assert not torch.allclose(hidden, next_hidden)
    assert np.isfinite(value)


def test_temporal_gru_actor_rejects_mismatched_history_shape():
    with np.testing.assert_raises(ValueError):
        ActorCritic(obs_dim=55, act_dim=2, hidden_size=16, actor_encoder="temporal_gru", actor_history_length=4)


def test_init_checkpoint_rejects_old_temporal_driver_observation_contract(tmp_path):
    source = ActorCritic(obs_dim=76, act_dim=2, hidden_size=16, actor_encoder="temporal_gru", actor_history_length=4)
    checkpoint_path = tmp_path / "checkpoint.pt"
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in source.state_dict().items()},
            "config": {"device": "cpu", "actor_encoder": "temporal_gru", "actor_history_length": 4},
        },
        checkpoint_path,
    )

    target = ActorCritic(obs_dim=60, act_dim=2, hidden_size=16, actor_encoder="temporal_gru", actor_history_length=4)

    with np.testing.assert_raises(RuntimeError):
        load_init_checkpoint_state(target, checkpoint_path, torch.device("cpu"))


def test_sequence_targets_use_future_executed_actions_until_done():
    actions = np.array(
        [
            [[0.0, 0.0]],
            [[0.1, 0.2]],
            [[0.3, 0.4]],
            [[0.5, 0.6]],
        ],
        dtype=np.float32,
    )
    dones = np.array([[0.0], [1.0], [0.0], [0.0]], dtype=np.float32)

    target, mask = build_sequence_targets(actions, dones, horizon=3)

    np.testing.assert_allclose(target[0, 0, 0], [0.1, 0.2])
    assert mask[0, 0, 0] == 1.0
    assert mask[0, 0, 1] == 0.0
    assert mask[1, 0, 0] == 0.0
