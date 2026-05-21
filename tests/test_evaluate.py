import numpy as np

from autodrift.dynamics import RandomizationConfig
from autodrift.env import AutoDriftEnv, DriftEnvConfig, ObstacleTaskConfig
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


def test_episode_row_includes_obstacle_clearance_margin():
    env = AutoDriftEnv(
        DriftEnvConfig(
            max_steps=3,
            obstacle=ObstacleTaskConfig(
                enabled=True,
                distance_range=(20.0, 20.0),
                half_width_range=(0.8, 0.8),
            ),
        )
    )

    row = run_episode(env, "heuristic", seed=24)

    assert np.isclose(row["obstacle_collision_radius"], 1.70)
    assert np.isfinite(row["min_clearance_margin"])


def test_actor_policy_can_ablate_action_history():
    env_config = DriftEnvConfig(history_length=2, action_history_mode="full")
    policy = ActorPolicy(ActorCritic(obs_dim=144, act_dim=3, hidden_size=8), env_config, ablation="zero_action_history")
    observation = np.arange(144, dtype=np.float32)

    transformed = policy._transform_observation(observation)

    assert transformed[9] == 0.0
    assert transformed[10] == 0.0
    assert transformed[11] == 0.0
    assert transformed[81] == 0.0
    assert transformed[82] == 0.0
    assert transformed[83] == 0.0


def test_actor_policy_can_ablate_current_response_only():
    env_config = DriftEnvConfig(history_length=2, action_history_mode="full")
    policy = ActorPolicy(ActorCritic(obs_dim=144, act_dim=3, hidden_size=8), env_config, ablation="zero_current_response")
    observation = np.arange(144, dtype=np.float32)

    transformed = policy._transform_observation(observation)

    np.testing.assert_allclose(transformed[:12], np.zeros(12, dtype=np.float32))
    np.testing.assert_allclose(transformed[12:], observation[12:])


def test_actor_policy_can_ablate_all_response_history():
    env_config = DriftEnvConfig(history_length=2, action_history_mode="full")
    policy = ActorPolicy(ActorCritic(obs_dim=144, act_dim=3, hidden_size=8), env_config, ablation="zero_all_response")
    observation = np.arange(144, dtype=np.float32)

    transformed = policy._transform_observation(observation)

    np.testing.assert_allclose(transformed[:12], np.zeros(12, dtype=np.float32))
    np.testing.assert_allclose(transformed[72:84], np.zeros(12, dtype=np.float32))
    np.testing.assert_allclose(transformed[12:72], observation[12:72])


def test_actor_policy_can_ablate_wheel_response_only():
    env_config = DriftEnvConfig(
        history_length=2,
        action_history_mode="full",
        wheel_observation_mode="front_rear",
    )
    policy = ActorPolicy(ActorCritic(obs_dim=170, act_dim=3, hidden_size=8), env_config, ablation="zero_wheel_response")
    observation = np.arange(170, dtype=np.float32)

    transformed = policy._transform_observation(observation)

    np.testing.assert_allclose(transformed[12:25], np.zeros(13, dtype=np.float32))
    np.testing.assert_allclose(transformed[97:110], np.zeros(13, dtype=np.float32))
    np.testing.assert_allclose(transformed[:12], observation[:12])
    np.testing.assert_allclose(transformed[25:85], observation[25:85])


def test_actor_policy_can_ablate_temporal_history():
    env_config = DriftEnvConfig(history_length=2, action_history_mode="full")
    policy = ActorPolicy(ActorCritic(obs_dim=144, act_dim=3, hidden_size=8), env_config, ablation="single_frame_history")
    observation = np.arange(144, dtype=np.float32)

    transformed = policy._transform_observation(observation)

    np.testing.assert_allclose(transformed[:72], transformed[72:])


def test_actor_policy_can_shuffle_temporal_history_deterministically():
    env_config = DriftEnvConfig(history_length=4, action_history_mode="none")
    policy = ActorPolicy(ActorCritic(obs_dim=8, act_dim=3, hidden_size=8), env_config, ablation="shuffled_history")
    observation = np.arange(8, dtype=np.float32)

    transformed = policy._transform_observation(observation)

    np.testing.assert_allclose(transformed, np.array([4, 5, 0, 1, 2, 3, 6, 7], dtype=np.float32))


def test_actor_policy_can_reset_online_recurrent_state_each_step():
    env_config = DriftEnvConfig(history_length=1, action_history_mode="full")
    model = ActorCritic(obs_dim=72, act_dim=3, hidden_size=8, actor_encoder="online_gru")
    observation = np.linspace(-0.4, 0.4, 72, dtype=np.float32)

    stateful_policy = ActorPolicy(model, env_config)
    stateful_policy.act(observation, {})
    stateful_hidden = stateful_policy.hidden.detach().clone()
    stateful_policy.act(observation, {})
    assert not np.allclose(stateful_hidden.numpy(), stateful_policy.hidden.detach().numpy())

    reset_policy = ActorPolicy(model, env_config, ablation="reset_recurrent_state")
    reset_policy.act(observation, {})
    reset_hidden = reset_policy.hidden.detach().clone()
    reset_policy.act(observation, {})
    np.testing.assert_allclose(reset_hidden.numpy(), reset_policy.hidden.detach().numpy(), atol=1e-6)
