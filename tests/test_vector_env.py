import numpy as np

from autodrift.env import DriftEnvConfig
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


def test_vector_env_cycles_optional_seed_sequence_on_reset():
    env = SyncAutoDriftVectorEnv(
        num_envs=1,
        config=DriftEnvConfig(max_steps=1),
        seed=21,
        seed_sequence=[101, 103],
    )
    _, infos = env.reset()
    assert infos[0]["reset_seed"] == 101

    actions = np.zeros((1, env.single_action_space.shape[0]), dtype=np.float32)
    first_step = env.step(actions)
    assert first_step.truncated[0]
    assert first_step.infos[0]["reset_info"]["reset_seed"] == 103

    second_step = env.step(actions)
    assert second_step.truncated[0]
    assert second_step.infos[0]["reset_info"]["reset_seed"] == 101
