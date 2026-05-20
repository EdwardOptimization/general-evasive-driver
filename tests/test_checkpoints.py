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


def test_init_checkpoint_expands_single_frame_policy_to_extra_features(tmp_path):
    torch.manual_seed(4)
    source = ActorCritic(obs_dim=13, act_dim=2, hidden_size=16)
    checkpoint_path = tmp_path / "checkpoint.pt"
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in source.state_dict().items()},
            "config": {"device": "cpu"},
        },
        checkpoint_path,
    )

    target = ActorCritic(obs_dim=18, act_dim=2, hidden_size=16)
    load_mode = load_init_checkpoint_state(target, checkpoint_path, torch.device("cpu"))

    base_obs = torch.linspace(-0.3, 0.3, 13).unsqueeze(0)
    extra_obs = torch.randn(1, 5)
    with torch.no_grad():
        source_dist, source_value = source(base_obs)
        target_dist, target_value = target(torch.cat([base_obs, extra_obs], dim=1))

    assert load_mode == "partial_input_expand"
    np.testing.assert_allclose(target_dist.mean.numpy(), source_dist.mean.numpy(), atol=1e-6)
    np.testing.assert_allclose(target_value.numpy(), source_value.numpy(), atol=1e-6)


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


def test_init_checkpoint_can_add_sequence_head_and_expand_obs(tmp_path):
    torch.manual_seed(8)
    source = ActorCritic(obs_dim=18, act_dim=2, hidden_size=16)
    checkpoint_path = tmp_path / "checkpoint.pt"
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in source.state_dict().items()},
            "config": {"device": "cpu"},
        },
        checkpoint_path,
    )

    target = ActorCritic(obs_dim=20, act_dim=2, hidden_size=16, action_sequence_horizon=3)
    load_mode = load_init_checkpoint_state(target, checkpoint_path, torch.device("cpu"))

    assert "partial_input_expand" in load_mode
    assert "new_sequence_head" in load_mode
    assert target.predict_sequence(np.zeros(20, dtype=np.float32)).shape == (3, 2)


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
