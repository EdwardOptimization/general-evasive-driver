import numpy as np

from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.policies import HeuristicPolicy


def test_env_reset_and_step_shapes():
    env = AutoDriftEnv()
    obs, info = env.reset(seed=11)

    assert obs.shape == env.observation_space.shape
    assert env.observation_space.contains(obs)
    assert 0.25 <= info["mu"] <= 1.15

    next_obs, reward, terminated, truncated, next_info = env.step(np.array([0.0, 0.2], dtype=np.float32))

    assert next_obs.shape == env.observation_space.shape
    assert np.isfinite(reward)
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert next_info["step"] == 1


def test_privileged_observation_adds_hidden_params():
    env = AutoDriftEnv(DriftEnvConfig(include_privileged_params=True))
    obs, _ = env.reset(seed=12)

    assert obs.shape == (17,)


def test_heuristic_policy_runs_for_multiple_steps():
    env = AutoDriftEnv()
    policy = HeuristicPolicy()
    obs, info = env.reset(seed=13)

    steps = 0
    for _ in range(25):
        action = policy.act(obs, info)
        assert env.action_space.contains(action)
        obs, reward, terminated, truncated, info = env.step(action)
        assert np.isfinite(reward)
        steps += 1
        if terminated or truncated:
            break

    assert steps > 0
