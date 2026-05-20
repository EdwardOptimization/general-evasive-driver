import numpy as np

from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.latent_probe import (
    TARGET_SPECS,
    build_feature_sets,
    bucket_label,
    collect_probe_dataset,
    split_by_episode,
    train_linear_probe,
)
from autodrift.train_ppo import ActorCritic


def test_bucket_label_uses_expected_hidden_parameter_boundaries():
    assert bucket_label(0.40, TARGET_SPECS["mu_bucket"]) == "low"
    assert bucket_label(0.60, TARGET_SPECS["mu_bucket"]) == "medium"
    assert bucket_label(0.90, TARGET_SPECS["mu_bucket"]) == "high"
    assert bucket_label(-0.08, TARGET_SPECS["cg_bucket"]) == "rear"
    assert bucket_label(0.08, TARGET_SPECS["cg_bucket"]) == "front"


def test_split_by_episode_keeps_train_and_test_episodes_disjoint():
    rows = [{"episode": episode, "step": step} for episode in range(6) for step in range(2)]

    train_mask = split_by_episode(rows, train_fraction=0.5, seed=3)
    train_episodes = {rows[index]["episode"] for index, is_train in enumerate(train_mask) if is_train}
    test_episodes = {rows[index]["episode"] for index, is_train in enumerate(train_mask) if not is_train}

    assert train_episodes
    assert test_episodes
    assert train_episodes.isdisjoint(test_episodes)


def test_train_linear_probe_beats_majority_on_separable_data():
    features = np.array([[-2.0], [-1.5], [-1.0], [1.0], [1.5], [2.0]], dtype=np.float32)
    labels = np.array([0, 0, 0, 1, 1, 1], dtype=np.int64)
    train_mask = np.array([True, True, False, True, True, False])

    result = train_linear_probe(
        features=features,
        labels=labels,
        train_mask=train_mask,
        target_name="mu_bucket",
        feature_set="synthetic",
        seed=9,
        epochs=120,
        learning_rate=0.05,
    )

    assert result.status == "ok"
    assert result.test_accuracy > result.majority_accuracy


def test_collect_probe_dataset_records_observations_and_hidden_labels():
    env_config = DriftEnvConfig(max_steps=3, history_length=2, action_history_mode="full")
    env = AutoDriftEnv(env_config)
    model = ActorCritic(obs_dim=int(env.observation_space.shape[0]), act_dim=2, hidden_size=8)

    dataset = collect_probe_dataset(model=model, env_config=env_config, episodes=2, seed=11)

    assert dataset.observations.shape[0] == len(dataset.rows)
    assert dataset.observations.shape[1] == int(env.observation_space.shape[0])
    assert "mu_bucket" in dataset.labels
    assert "steering_tau_bucket" in dataset.labels


def test_build_feature_sets_supports_temporal_gru_latent():
    env_config = DriftEnvConfig(history_length=3, action_history_mode="none")
    model = ActorCritic(
        obs_dim=36,
        act_dim=2,
        hidden_size=8,
        actor_encoder="temporal_gru",
        actor_history_length=3,
    )
    observations = np.arange(72, dtype=np.float32).reshape(2, 36)

    features = build_feature_sets(model, observations, env_config, seed=5)

    assert features["latent"].shape == (2, 8)
    assert features["single_frame"].shape == (2, 12)
    assert features["shuffled_history_latent"].shape == (2, 8)
