import numpy as np

from autodrift.env import AutoDriftEnv, DriftEnvConfig, ObstacleTaskConfig
from autodrift.policies import make_policy


def test_aeb_policy_commands_full_brake():
    env = AutoDriftEnv()
    policy = make_policy("aeb", env)
    obs, info = env.reset(seed=30)

    action = policy.act(obs, info)

    np.testing.assert_allclose(action, np.array([0.0, -1.0], dtype=np.float32))


def test_aes_heuristic_policy_runs_with_obstacle_info():
    env = AutoDriftEnv(
        DriftEnvConfig(
            speed_range=(12.0, 16.0),
            friction_limited_speed=False,
            obstacle=ObstacleTaskConfig(
                enabled=True,
                distance_range=(5.0, 9.0),
                half_width_range=(0.8, 1.0),
                require_aeb_infeasible=True,
            ),
        )
    )
    policy = make_policy("aes_heuristic", env)
    obs, info = env.reset(seed=31)

    action = policy.act(obs, info)

    assert env.action_space.contains(action)
    assert action[1] < 0.0


def test_envelope_aes_policy_runs_with_obstacle_info():
    env = AutoDriftEnv(
        DriftEnvConfig(
            speed_range=(12.0, 16.0),
            friction_limited_speed=False,
            obstacle=ObstacleTaskConfig(
                enabled=True,
                distance_range=(5.0, 9.0),
                half_width_range=(0.8, 1.0),
                require_aeb_infeasible=True,
            ),
        )
    )
    policy = make_policy("envelope_aes", env)
    obs, info = env.reset(seed=34)

    action = policy.act(obs, info)

    assert env.action_space.contains(action)
    assert action[0] != 0.0
