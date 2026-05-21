import numpy as np
import csv
import pytest
import torch

from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.env import DriftEnvConfig, ObstacleTaskConfig
from autodrift.train_ppo import (
    ActorCritic,
    PPOConfig,
    build_response_prediction_targets,
    build_sequence_targets,
    evaluate_actor,
    load_training_seed_csv,
    load_init_checkpoint_state,
    train,
)


def model_config(**overrides):
    config = {
        "device": "cpu",
        "actor_encoder": "mlp",
        "actor_history_length": 1,
        "action_sequence_horizon": 1,
        "response_prediction_dim": 0,
        "response_prediction_horizon": 1,
        "log_std_init": -1.0,
        "log_std_min": -5.0,
        "log_std_max": -0.5,
    }
    config.update(overrides)
    return config


def test_actor_critic_checkpoint_loads_from_explicit_model_config(tmp_path):
    model = ActorCritic(obs_dim=13, act_dim=2, hidden_size=16)
    checkpoint_path = tmp_path / "checkpoint.pt"
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": model_config(),
        },
        checkpoint_path,
    )

    loaded, checkpoint = load_actor_critic_checkpoint(checkpoint_path, device="cpu")
    action, logp, value = loaded.act(np.zeros(13, dtype=np.float32), deterministic=True)

    assert checkpoint["config"]["device"] == "cpu"
    assert action.shape == (2,)
    assert np.isfinite(logp)
    assert np.isfinite(value)


def test_actor_critic_checkpoint_rejects_missing_model_config_keys(tmp_path):
    model = ActorCritic(obs_dim=13, act_dim=2, hidden_size=16)
    checkpoint_path = tmp_path / "checkpoint.pt"
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": {"device": "cpu"},
        },
        checkpoint_path,
    )

    with np.testing.assert_raises(RuntimeError):
        load_actor_critic_checkpoint(checkpoint_path, device="cpu")


def test_init_checkpoint_rejects_different_observation_contract(tmp_path):
    source = ActorCritic(obs_dim=13, act_dim=2, hidden_size=16)
    checkpoint_path = tmp_path / "checkpoint.pt"
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in source.state_dict().items()},
            "config": model_config(),
        },
        checkpoint_path,
    )

    target = ActorCritic(obs_dim=10, act_dim=2, hidden_size=16)

    with np.testing.assert_raises(RuntimeError):
        load_init_checkpoint_state(target, checkpoint_path, torch.device("cpu"))


def test_train_writes_periodic_checkpoints(tmp_path):
    save_path = tmp_path / "run" / "checkpoint.pt"
    config = PPOConfig(
        total_steps=64,
        rollout_steps=16,
        num_envs=2,
        update_epochs=1,
        minibatch_size=16,
        hidden_size=8,
        checkpoint_interval_steps=32,
        seed=123,
        device="cpu",
    )

    train(
        config,
        save_path=save_path,
        env_config=DriftEnvConfig(max_steps=8, speed_range=(4.0, 6.0)),
    )

    periodic = sorted((tmp_path / "run" / "checkpoints").glob("checkpoint_step_*.pt"))

    assert save_path.exists()
    assert [path.name for path in periodic] == ["checkpoint_step_32.pt", "checkpoint_step_64.pt"]
    loaded, checkpoint = load_actor_critic_checkpoint(periodic[0], device="cpu")
    assert loaded.obs_dim == 72
    assert checkpoint["config"]["checkpoint_interval_steps"] == 32


def test_training_seed_csv_loads_ordered_seeds(tmp_path):
    seed_csv = tmp_path / "seeds.csv"
    seed_csv.write_text("seed,notes\n101,a\n103,b\n", encoding="utf-8")

    assert load_training_seed_csv(seed_csv) == [101, 103]


def test_train_accepts_hard_response_seed_csv(tmp_path):
    seed_csv = tmp_path / "seeds.csv"
    seed_csv.write_text("seed\n101\n103\n", encoding="utf-8")
    save_path = tmp_path / "run" / "checkpoint.pt"
    config = PPOConfig(
        total_steps=32,
        rollout_steps=8,
        num_envs=2,
        update_epochs=1,
        minibatch_size=8,
        hidden_size=8,
        training_seed_csv=str(seed_csv),
        seed=123,
        device="cpu",
    )

    train(
        config,
        save_path=save_path,
        env_config=DriftEnvConfig(max_steps=4, speed_range=(4.0, 6.0)),
    )

    _, checkpoint = load_actor_critic_checkpoint(save_path, device="cpu")
    assert checkpoint["config"]["training_seed_csv"] == str(seed_csv)


def test_sequence_actor_checkpoint_loads_and_predicts_plan(tmp_path):
    model = ActorCritic(obs_dim=20, act_dim=2, hidden_size=16, action_sequence_horizon=4)
    checkpoint_path = tmp_path / "checkpoint.pt"
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": model_config(action_sequence_horizon=4),
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
            "config": model_config(actor_encoder="temporal_gru", actor_history_length=4),
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
    model = ActorCritic(obs_dim=72, act_dim=3, hidden_size=16, actor_encoder="online_gru")
    checkpoint_path = tmp_path / "checkpoint.pt"
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": model_config(actor_encoder="online_gru", actor_history_length=1),
        },
        checkpoint_path,
    )

    loaded, _ = load_actor_critic_checkpoint(checkpoint_path, device="cpu")
    observation = np.linspace(-0.5, 0.5, 72, dtype=np.float32)
    action, _, value, hidden = loaded.act_recurrent(observation, deterministic=True)
    _, _, _, next_hidden = loaded.act_recurrent(observation, hidden, deterministic=True)

    assert loaded.actor_encoder == "online_gru"
    assert action.shape == (3,)
    assert hidden.shape == (1, 16)
    assert not torch.allclose(hidden, next_hidden)
    assert np.isfinite(value)


def test_human_view_online_actor_checkpoint_loads_and_updates_hidden(tmp_path):
    model = ActorCritic(obs_dim=72, act_dim=3, hidden_size=16, actor_encoder="human_view_online_gru")
    checkpoint_path = tmp_path / "checkpoint.pt"
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": model_config(actor_encoder="human_view_online_gru", actor_history_length=1),
        },
        checkpoint_path,
    )

    loaded, _ = load_actor_critic_checkpoint(checkpoint_path, device="cpu")
    observation = np.linspace(-0.5, 0.5, 72, dtype=np.float32)
    action, _, value, hidden = loaded.act_recurrent(observation, deterministic=True)
    _, _, _, next_hidden = loaded.act_recurrent(observation, hidden, deterministic=True)

    assert loaded.actor_encoder == "human_view_online_gru"
    assert loaded.response_feature_indices == tuple(range(12))
    assert loaded.context_feature_indices == tuple(range(12, 72))
    assert action.shape == (3,)
    assert hidden.shape == (1, 16)
    assert not torch.allclose(hidden, next_hidden)
    assert np.isfinite(value)


def test_human_view_online_actor_requires_canonical_frame():
    with np.testing.assert_raises(ValueError):
        ActorCritic(obs_dim=71, act_dim=3, hidden_size=16, actor_encoder="human_view_online_gru")


def test_wheel_human_view_online_actor_checkpoint_loads(tmp_path):
    model = ActorCritic(obs_dim=85, act_dim=3, hidden_size=16, actor_encoder="wheel_human_view_online_gru")
    checkpoint_path = tmp_path / "checkpoint.pt"
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": model_config(actor_encoder="wheel_human_view_online_gru", actor_history_length=1),
        },
        checkpoint_path,
    )

    loaded, _ = load_actor_critic_checkpoint(checkpoint_path, device="cpu")
    observation = np.linspace(-0.5, 0.5, 85, dtype=np.float32)
    action, _, value, hidden = loaded.act_recurrent(observation, deterministic=True)
    _, _, _, next_hidden = loaded.act_recurrent(observation, hidden, deterministic=True)

    assert loaded.actor_encoder == "wheel_human_view_online_gru"
    assert loaded.response_feature_indices == tuple(range(25))
    assert loaded.context_feature_indices == tuple(range(25, 85))
    assert action.shape == (3,)
    assert hidden.shape == (1, 16)
    assert not torch.allclose(hidden, next_hidden)
    assert np.isfinite(value)


def test_wheel_human_view_online_actor_requires_wheel_frame():
    with np.testing.assert_raises(ValueError):
        ActorCritic(obs_dim=84, act_dim=3, hidden_size=16, actor_encoder="wheel_human_view_online_gru")


def test_privileged_human_view_online_actor_requires_teacher_frame():
    with np.testing.assert_raises(ValueError):
        ActorCritic(obs_dim=81, act_dim=3, hidden_size=16, actor_encoder="privileged_human_view_online_gru")


def test_privileged_human_view_online_actor_checkpoint_loads(tmp_path):
    model = ActorCritic(obs_dim=82, act_dim=3, hidden_size=16, actor_encoder="privileged_human_view_online_gru")
    checkpoint_path = tmp_path / "checkpoint.pt"
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": model_config(actor_encoder="privileged_human_view_online_gru", actor_history_length=1),
        },
        checkpoint_path,
    )

    loaded, _ = load_actor_critic_checkpoint(checkpoint_path, device="cpu")
    observation = np.linspace(-0.5, 0.5, 82, dtype=np.float32)
    action, _, value, hidden = loaded.act_recurrent(observation, deterministic=True)
    _, _, _, next_hidden = loaded.act_recurrent(observation, hidden, deterministic=True)

    assert loaded.actor_encoder == "privileged_human_view_online_gru"
    assert loaded.response_feature_indices == tuple(range(12))
    assert loaded.context_feature_indices == tuple(range(12, 72))
    assert loaded.privileged_feature_indices == tuple(range(72, 82))
    assert action.shape == (3,)
    assert hidden.shape == (1, 16)
    assert not torch.allclose(hidden, next_hidden)
    assert np.isfinite(value)


def test_privileged_human_view_init_preserves_human_view_behavior(tmp_path):
    torch.manual_seed(7)
    source = ActorCritic(obs_dim=72, act_dim=3, hidden_size=16, actor_encoder="human_view_online_gru")
    checkpoint_path = tmp_path / "m62_like.pt"
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in source.state_dict().items()},
            "config": model_config(actor_encoder="human_view_online_gru", actor_history_length=1),
        },
        checkpoint_path,
    )
    target = ActorCritic(obs_dim=82, act_dim=3, hidden_size=16, actor_encoder="privileged_human_view_online_gru")

    load_mode = load_init_checkpoint_state(target, checkpoint_path, torch.device("cpu"))

    assert load_mode == "partial_privileged_human_view_branch"
    assert target.context_feature_indices == tuple(range(12, 72))
    assert target.privileged_feature_indices == tuple(range(72, 82))
    assert target.privileged_residual is not None
    assert float(target.privileged_residual.weight.detach().abs().sum()) == 0.0
    assert float(target.privileged_residual.bias.detach().abs().sum()) == 0.0

    obs72 = np.linspace(-0.7, 0.7, 72, dtype=np.float32)
    privileged = np.linspace(0.2, 1.2, 10, dtype=np.float32)
    obs82 = np.concatenate([obs72, privileged]).astype(np.float32)
    hidden_source = source.initial_hidden(1, torch.device("cpu"))
    hidden_target = target.initial_hidden(1, torch.device("cpu"))
    source_action, source_logp, source_value, source_next_hidden = source.act_recurrent(
        obs72,
        hidden_source,
        deterministic=True,
    )
    target_action, target_logp, target_value, target_next_hidden = target.act_recurrent(
        obs82,
        hidden_target,
        deterministic=True,
    )

    np.testing.assert_allclose(target_action, source_action, atol=1e-7)
    assert target_logp == pytest.approx(source_logp, abs=1e-7)
    assert target_value == pytest.approx(source_value, abs=1e-7)
    torch.testing.assert_close(target_next_hidden, source_next_hidden, atol=1e-7, rtol=0.0)


def test_privileged_human_view_init_rejects_privileged_branch_shape_mismatch(tmp_path):
    source = ActorCritic(obs_dim=82, act_dim=3, hidden_size=16, actor_encoder="privileged_human_view_online_gru")
    source_state = {key: value.detach().clone() for key, value in source.state_dict().items()}
    source_state["privileged_encoder.0.weight"] = torch.zeros(16, 9)
    checkpoint_path = tmp_path / "bad_privileged_branch.pt"
    torch.save(
        {
            "model_state": source_state,
            "config": model_config(actor_encoder="privileged_human_view_online_gru", actor_history_length=1),
        },
        checkpoint_path,
    )
    target = ActorCritic(obs_dim=82, act_dim=3, hidden_size=16, actor_encoder="privileged_human_view_online_gru")

    with np.testing.assert_raises(RuntimeError):
        load_init_checkpoint_state(target, checkpoint_path, torch.device("cpu"))


def test_human_view_online_actor_trains_with_canonical_frame(tmp_path):
    save_path = tmp_path / "run" / "checkpoint.pt"
    config = PPOConfig(
        total_steps=32,
        rollout_steps=8,
        num_envs=2,
        update_epochs=1,
        minibatch_size=8,
        hidden_size=8,
        actor_encoder="human_view_online_gru",
        recurrent_sequence_training=True,
        seed=127,
        device="cpu",
    )

    train(
        config,
        save_path=save_path,
        env_config=DriftEnvConfig(
            max_steps=8,
            speed_range=(4.0, 6.0),
            friction_limited_speed=False,
            obstacle=ObstacleTaskConfig(enabled=True, distance_range=(20.0, 24.0)),
        ),
    )

    loaded, _ = load_actor_critic_checkpoint(save_path, device="cpu")
    assert loaded.actor_encoder == "human_view_online_gru"


def test_train_logs_response_prediction_loss(tmp_path):
    save_path = tmp_path / "run" / "checkpoint.pt"
    metrics_path = tmp_path / "run" / "train_metrics.csv"
    config = PPOConfig(
        total_steps=32,
        rollout_steps=8,
        num_envs=2,
        update_epochs=1,
        minibatch_size=8,
        hidden_size=8,
        actor_encoder="human_view_online_gru",
        recurrent_sequence_training=True,
        response_prediction_aux_coef=0.01,
        response_prediction_dim=3,
        response_prediction_horizon=2,
        seed=129,
        device="cpu",
    )

    train(
        config,
        save_path=save_path,
        metrics_csv_path=metrics_path,
        env_config=DriftEnvConfig(
            max_steps=8,
            speed_range=(4.0, 6.0),
            friction_limited_speed=False,
            obstacle=ObstacleTaskConfig(enabled=True, distance_range=(20.0, 24.0)),
        ),
    )

    with metrics_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert rows
    assert "response_prediction_loss_mean" in rows[0]
    assert float(rows[0]["response_prediction_loss_mean"]) >= 0.0


def test_train_logs_hidden_contrast_loss(tmp_path):
    save_path = tmp_path / "run" / "checkpoint.pt"
    metrics_path = tmp_path / "run" / "train_metrics.csv"
    config = PPOConfig(
        total_steps=32,
        rollout_steps=8,
        num_envs=2,
        update_epochs=1,
        minibatch_size=8,
        hidden_size=8,
        actor_encoder="human_view_online_gru",
        recurrent_sequence_training=True,
        hidden_contrast_aux_coef=0.01,
        hidden_contrast_margin=0.05,
        seed=131,
        device="cpu",
    )

    train(
        config,
        save_path=save_path,
        metrics_csv_path=metrics_path,
        env_config=DriftEnvConfig(
            max_steps=8,
            speed_range=(4.0, 6.0),
            friction_limited_speed=False,
            obstacle=ObstacleTaskConfig(enabled=True, distance_range=(20.0, 24.0)),
        ),
    )

    with metrics_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert rows
    assert "hidden_contrast_loss_mean" in rows[0]
    assert float(rows[0]["hidden_contrast_loss_mean"]) >= 0.0


def test_train_logs_action_contrast_loss(tmp_path):
    save_path = tmp_path / "run" / "checkpoint.pt"
    metrics_path = tmp_path / "run" / "train_metrics.csv"
    config = PPOConfig(
        total_steps=32,
        rollout_steps=8,
        num_envs=2,
        update_epochs=1,
        minibatch_size=8,
        hidden_size=8,
        actor_encoder="human_view_online_gru",
        recurrent_sequence_training=True,
        action_contrast_aux_coef=0.01,
        action_contrast_margin=0.10,
        seed=132,
        device="cpu",
    )

    train(
        config,
        save_path=save_path,
        metrics_csv_path=metrics_path,
        env_config=DriftEnvConfig(
            max_steps=8,
            speed_range=(4.0, 6.0),
            friction_limited_speed=False,
            obstacle=ObstacleTaskConfig(enabled=True, distance_range=(20.0, 24.0)),
        ),
    )

    with metrics_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert rows
    assert "action_contrast_loss_mean" in rows[0]
    assert float(rows[0]["action_contrast_loss_mean"]) >= 0.0


def test_train_logs_paired_hidden_action_contrast_loss(tmp_path):
    save_path = tmp_path / "run" / "checkpoint.pt"
    metrics_path = tmp_path / "run" / "train_metrics.csv"
    snapshot_path = tmp_path / "snapshots.npz"
    np.savez_compressed(
        snapshot_path,
        nominal_observation=np.zeros((3, 72), dtype=np.float32),
        perturbed_observation=np.ones((3, 72), dtype=np.float32) * 0.01,
        nominal_hidden=np.zeros((3, 8), dtype=np.float32),
        perturbed_hidden=np.ones((3, 8), dtype=np.float32) * 0.1,
    )
    config = PPOConfig(
        total_steps=32,
        rollout_steps=8,
        num_envs=2,
        update_epochs=1,
        minibatch_size=8,
        hidden_size=8,
        actor_encoder="human_view_online_gru",
        recurrent_sequence_training=True,
        paired_hidden_action_contrast_aux_coef=0.01,
        paired_hidden_action_contrast_margin=0.05,
        paired_hidden_snapshot_npz=str(snapshot_path),
        paired_hidden_snapshot_batch_size=2,
        seed=133,
        device="cpu",
    )

    train(
        config,
        save_path=save_path,
        metrics_csv_path=metrics_path,
        env_config=DriftEnvConfig(
            max_steps=8,
            speed_range=(4.0, 6.0),
            friction_limited_speed=False,
            obstacle=ObstacleTaskConfig(enabled=True, distance_range=(20.0, 24.0)),
        ),
    )

    with metrics_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert rows
    assert "paired_hidden_action_contrast_loss_mean" in rows[0]
    assert float(rows[0]["paired_hidden_action_contrast_loss_mean"]) >= 0.0


def test_train_logs_outcome_intervention_loss(tmp_path):
    save_path = tmp_path / "run" / "checkpoint.pt"
    metrics_path = tmp_path / "run" / "train_metrics.csv"
    snippet_path = tmp_path / "outcome_snippets.npz"
    np.savez_compressed(
        snippet_path,
        observation=np.zeros((3, 72), dtype=np.float32),
        preferred_hidden=np.zeros((3, 8), dtype=np.float32),
        rejected_hidden=np.ones((3, 8), dtype=np.float32) * 0.1,
        preferred_action=np.zeros((3, 3), dtype=np.float32),
        weight=np.ones(3, dtype=np.float32),
    )
    config = PPOConfig(
        total_steps=32,
        rollout_steps=8,
        num_envs=2,
        update_epochs=1,
        minibatch_size=8,
        hidden_size=8,
        actor_encoder="human_view_online_gru",
        recurrent_sequence_training=True,
        outcome_intervention_aux_coef=0.01,
        outcome_intervention_snapshot_npz=str(snippet_path),
        outcome_intervention_batch_size=2,
        outcome_intervention_logprob_margin=0.05,
        seed=135,
        device="cpu",
    )

    train(
        config,
        save_path=save_path,
        metrics_csv_path=metrics_path,
        env_config=DriftEnvConfig(
            max_steps=8,
            speed_range=(4.0, 6.0),
            friction_limited_speed=False,
            obstacle=ObstacleTaskConfig(enabled=True, distance_range=(20.0, 24.0)),
        ),
    )

    with metrics_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert rows
    assert "outcome_intervention_loss_mean" in rows[0]
    assert float(rows[0]["outcome_intervention_loss_mean"]) >= 0.0


def test_train_requires_baseline_action_anchor_checkpoint():
    config = PPOConfig(
        total_steps=8,
        rollout_steps=4,
        num_envs=1,
        baseline_action_anchor_coef=0.01,
        device="cpu",
    )

    with np.testing.assert_raises(ValueError):
        train(config, env_config=DriftEnvConfig(max_steps=4, speed_range=(4.0, 6.0)))


def test_train_logs_baseline_action_anchor_loss(tmp_path):
    reference_model = ActorCritic(obs_dim=72, act_dim=3, hidden_size=8, actor_encoder="human_view_online_gru")
    reference_path = tmp_path / "reference.pt"
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in reference_model.state_dict().items()},
            "config": model_config(actor_encoder="human_view_online_gru", actor_history_length=1),
        },
        reference_path,
    )
    save_path = tmp_path / "run" / "checkpoint.pt"
    metrics_path = tmp_path / "run" / "train_metrics.csv"
    config = PPOConfig(
        total_steps=32,
        rollout_steps=8,
        num_envs=2,
        update_epochs=1,
        minibatch_size=8,
        hidden_size=8,
        actor_encoder="human_view_online_gru",
        recurrent_sequence_training=True,
        baseline_action_anchor_coef=0.05,
        baseline_action_anchor_checkpoint=str(reference_path),
        baseline_action_anchor_negative_advantage_only=True,
        seed=134,
        device="cpu",
    )

    train(
        config,
        save_path=save_path,
        metrics_csv_path=metrics_path,
        env_config=DriftEnvConfig(
            max_steps=8,
            speed_range=(4.0, 6.0),
            friction_limited_speed=False,
            obstacle=ObstacleTaskConfig(enabled=True, distance_range=(20.0, 24.0)),
        ),
        init_checkpoint_path=reference_path,
    )

    with metrics_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert rows
    assert "baseline_action_anchor_loss_mean" in rows[0]
    assert float(rows[0]["baseline_action_anchor_loss_mean"]) >= 0.0


def test_online_gru_sequence_eval_backpropagates_through_time():
    torch.manual_seed(0)
    model = ActorCritic(obs_dim=5, act_dim=2, hidden_size=8, actor_encoder="online_gru")
    actions = torch.tanh(torch.randn(3, 1, 2))
    initial_hidden = model.initial_hidden(1, torch.device("cpu"))

    obs = torch.randn(3, 1, 5, requires_grad=True)
    dones = torch.zeros(3, 1)
    _, _, values = model.evaluate_actions_recurrent_sequence(obs, actions, initial_hidden, dones)
    values[1].sum().backward()

    assert float(obs.grad[0].abs().sum()) > 0.0

    reset_obs = obs.detach().clone().requires_grad_(True)
    reset_dones = torch.tensor([[1.0], [0.0], [0.0]])
    _, _, reset_values = model.evaluate_actions_recurrent_sequence(reset_obs, actions, initial_hidden, reset_dones)
    reset_values[1].sum().backward()

    assert float(reset_obs.grad[0].abs().sum()) == 0.0


def test_online_gru_response_prediction_head_uses_recurrent_history():
    torch.manual_seed(1)
    model = ActorCritic(
        obs_dim=5,
        act_dim=2,
        hidden_size=8,
        actor_encoder="online_gru",
        response_prediction_dim=3,
        response_prediction_horizon=2,
    )
    actions = torch.tanh(torch.randn(3, 1, 2))
    initial_hidden = model.initial_hidden(1, torch.device("cpu"))

    obs = torch.randn(3, 1, 5, requires_grad=True)
    dones = torch.zeros(3, 1)
    predictions = model.predict_response_recurrent_sequence(obs, actions, initial_hidden, dones)
    predictions[1].sum().backward()

    assert predictions.shape == (3, 1, 2, 3)
    assert float(obs.grad[0].abs().sum()) > 0.0


def test_response_prediction_checkpoint_loads_declared_head(tmp_path):
    model = ActorCritic(
        obs_dim=5,
        act_dim=2,
        hidden_size=8,
        actor_encoder="online_gru",
        response_prediction_dim=3,
        response_prediction_horizon=2,
    )
    checkpoint_path = tmp_path / "checkpoint.pt"
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": model_config(actor_encoder="online_gru", response_prediction_dim=3, response_prediction_horizon=2),
        },
        checkpoint_path,
    )

    loaded, _ = load_actor_critic_checkpoint(checkpoint_path, device="cpu")

    assert loaded.response_prediction_dim == 3
    assert loaded.response_prediction_horizon == 2
    assert loaded.response_prediction_head is not None


def test_init_checkpoint_can_add_response_prediction_head(tmp_path):
    source = ActorCritic(obs_dim=5, act_dim=2, hidden_size=8, actor_encoder="online_gru", response_prediction_dim=0)
    target = ActorCritic(obs_dim=5, act_dim=2, hidden_size=8, actor_encoder="online_gru", response_prediction_dim=3)
    checkpoint_path = tmp_path / "checkpoint.pt"
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in source.state_dict().items()},
            "config": model_config(actor_encoder="online_gru", response_prediction_dim=0),
        },
        checkpoint_path,
    )

    load_mode = load_init_checkpoint_state(target, checkpoint_path, torch.device("cpu"))

    assert load_mode == "partial_response_prediction_head"
    assert target.response_prediction_head is not None
    for key, value in source.state_dict().items():
        torch.testing.assert_close(target.state_dict()[key], value)


def test_init_checkpoint_can_resize_response_prediction_head(tmp_path):
    source = ActorCritic(
        obs_dim=5,
        act_dim=2,
        hidden_size=8,
        actor_encoder="online_gru",
        response_prediction_dim=3,
        response_prediction_horizon=1,
    )
    target = ActorCritic(
        obs_dim=5,
        act_dim=2,
        hidden_size=8,
        actor_encoder="online_gru",
        response_prediction_dim=3,
        response_prediction_horizon=4,
    )
    checkpoint_path = tmp_path / "checkpoint.pt"
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in source.state_dict().items()},
            "config": model_config(actor_encoder="online_gru", response_prediction_dim=3, response_prediction_horizon=1),
        },
        checkpoint_path,
    )

    load_mode = load_init_checkpoint_state(target, checkpoint_path, torch.device("cpu"))

    assert load_mode == "partial_response_prediction_head"
    for key, value in source.state_dict().items():
        if key.startswith("response_prediction_head."):
            continue
        torch.testing.assert_close(target.state_dict()[key], value)


def test_evaluate_actor_carries_online_recurrent_hidden_state():
    model = ActorCritic(obs_dim=72, act_dim=3, hidden_size=8, actor_encoder="online_gru")
    calls = {"count": 0}

    def counted_act_recurrent(obs, hidden=None, deterministic=False):
        del obs, deterministic
        calls["count"] += 1
        next_hidden = model.initial_hidden(1, torch.device("cpu")) if hidden is None else hidden + 1.0
        return np.zeros(3, dtype=np.float32), 0.0, 0.0, next_hidden

    model.act_recurrent = counted_act_recurrent

    summary = evaluate_actor(model, episodes=1, seed=31, env_config=DriftEnvConfig(max_steps=3, speed_range=(4.0, 4.0)))

    assert calls["count"] > 0
    assert np.isfinite(summary["return_mean"])


def test_temporal_gru_actor_rejects_mismatched_history_shape():
    with np.testing.assert_raises(ValueError):
        ActorCritic(obs_dim=55, act_dim=2, hidden_size=16, actor_encoder="temporal_gru", actor_history_length=4)


def test_init_checkpoint_rejects_old_temporal_driver_observation_contract(tmp_path):
    source = ActorCritic(obs_dim=76, act_dim=2, hidden_size=16, actor_encoder="temporal_gru", actor_history_length=4)
    checkpoint_path = tmp_path / "checkpoint.pt"
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in source.state_dict().items()},
            "config": model_config(actor_encoder="temporal_gru", actor_history_length=4),
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


def test_response_prediction_targets_mask_future_observations_across_done():
    observations = np.array(
        [
            [[0.0, 10.0, 100.0]],
            [[1.0, 11.0, 101.0]],
            [[2.0, 12.0, 102.0]],
            [[3.0, 13.0, 103.0]],
            [[4.0, 14.0, 104.0]],
        ],
        dtype=np.float32,
    )
    dones = np.array([[0.0], [1.0], [0.0], [0.0], [0.0]], dtype=np.float32)

    target, mask = build_response_prediction_targets(observations, dones, response_dim=2, horizon=3, stride=1)

    np.testing.assert_allclose(target[0, 0, 0], [1.0, 11.0])
    assert mask[0, 0, 0] == 1.0
    assert mask[0, 0, 1] == 0.0
    assert mask[1, 0, 0] == 0.0
    np.testing.assert_allclose(target[2, 0, 1], [4.0, 14.0])
    assert mask[2, 0, 1] == 1.0
    assert mask[3, 0, 1] == 0.0
