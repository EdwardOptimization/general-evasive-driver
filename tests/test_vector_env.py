import numpy as np

from autodrift.vector_env import SyncAutoDriftVectorEnv


def test_vector_env_reset_and_step_shapes():
    env = SyncAutoDriftVectorEnv(num_envs=3, seed=21)
    obs, infos = env.reset()

    assert obs.shape == (3, env.single_observation_space.shape[0])
    assert len(infos) == 3

    actions = np.zeros((3, env.single_action_space.shape[0]), dtype=np.float32)
    step = env.step(actions)

    assert step.observations.shape == obs.shape
    assert step.rewards.shape == (3,)
    assert step.terminated.shape == (3,)
    assert step.truncated.shape == (3,)
    assert len(step.infos) == 3
