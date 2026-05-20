import numpy as np

from autodrift.dynamics import RandomizationConfig
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import SEGMENT_NAMES, ActorPolicy, curvature_segment, run_episode
from autodrift.train_ppo import ActorCritic


def test_curvature_segment_classifies_signed_curvature():
    assert curvature_segment(0.02) == "left_curve"
    assert curvature_segment(-0.02) == "right_curve"
    assert curvature_segment(0.0) == "near_zero"


def test_episode_row_includes_curvature_segment_metrics():
    env = AutoDriftEnv(
        DriftEnvConfig(
            max_steps=8,
            track_kind="figure_eight",
            speed_range=(4.0, 4.0),
            randomization=RandomizationConfig(mu_range=(1.0, 1.0)),
        )
    )

    row = run_episode(env, "heuristic", seed=23)

    segment_steps = sum(int(row[f"{segment}_steps"]) for segment in SEGMENT_NAMES)
    assert segment_steps == row["steps"]
    assert segment_steps > 0
    assert any(int(row[f"{segment}_steps"]) > 0 for segment in SEGMENT_NAMES)
    assert np.isfinite(row["lateral_rmse"])


def test_actor_policy_can_ablate_action_history():
    env_config = DriftEnvConfig(history_length=2, action_history_mode="full")
    policy = ActorPolicy(ActorCritic(obs_dim=22, act_dim=2, hidden_size=8), env_config, ablation="zero_action_history")
    observation = np.arange(22, dtype=np.float32)

    transformed = policy._transform_observation(observation)

    assert transformed[9] == 0.0
    assert transformed[10] == 0.0
    assert transformed[20] == 0.0
    assert transformed[21] == 0.0


def test_actor_policy_can_ablate_current_response_only():
    env_config = DriftEnvConfig(history_length=2, action_history_mode="full")
    policy = ActorPolicy(ActorCritic(obs_dim=22, act_dim=2, hidden_size=8), env_config, ablation="zero_current_response")
    observation = np.arange(22, dtype=np.float32)

    transformed = policy._transform_observation(observation)

    np.testing.assert_allclose(transformed[[0, 1, 2, 3, 4, 9, 10]], np.zeros(7, dtype=np.float32))
    np.testing.assert_allclose(transformed[11:], observation[11:])


def test_actor_policy_can_ablate_all_response_history():
    env_config = DriftEnvConfig(history_length=2, action_history_mode="full")
    policy = ActorPolicy(ActorCritic(obs_dim=22, act_dim=2, hidden_size=8), env_config, ablation="zero_all_response")
    observation = np.arange(22, dtype=np.float32)

    transformed = policy._transform_observation(observation)

    np.testing.assert_allclose(transformed[[0, 1, 2, 3, 4, 9, 10]], np.zeros(7, dtype=np.float32))
    np.testing.assert_allclose(transformed[[11, 12, 13, 14, 15, 20, 21]], np.zeros(7, dtype=np.float32))
    np.testing.assert_allclose(transformed[[5, 6, 7, 8]], observation[[5, 6, 7, 8]])


def test_actor_policy_can_ablate_temporal_history():
    env_config = DriftEnvConfig(history_length=2, action_history_mode="legacy")
    policy = ActorPolicy(ActorCritic(obs_dim=20, act_dim=2, hidden_size=8), env_config, ablation="single_frame_history")
    observation = np.arange(20, dtype=np.float32)

    transformed = policy._transform_observation(observation)

    np.testing.assert_allclose(transformed[:10], transformed[10:])


def test_actor_policy_can_shuffle_temporal_history_deterministically():
    env_config = DriftEnvConfig(history_length=4, action_history_mode="none")
    policy = ActorPolicy(ActorCritic(obs_dim=8, act_dim=2, hidden_size=8), env_config, ablation="shuffled_history")
    observation = np.arange(8, dtype=np.float32)

    transformed = policy._transform_observation(observation)

    np.testing.assert_allclose(transformed, np.array([4, 5, 0, 1, 2, 3, 6, 7], dtype=np.float32))
