from dataclasses import fields, replace

import numpy as np

from autodrift.artifacts import read_json
from autodrift.config import build_env_config
from autodrift.controller_profile_runtime import mask_spec_from_config
from autodrift.controller_profiles import PREVIOUS_COMMAND_INDICES
from autodrift.train_ppo import PPOConfig, make_vector_env


L0_CONFIG = "configs/paper_route_profiles/m1190_l0_current_masked_smoke.json"
L1_CONFIG = "configs/paper_route_profiles/m1190_l1_one_step_smoke.json"


def _ppo_config(config_data: dict) -> PPOConfig:
    field_names = {field.name for field in fields(PPOConfig)}
    ppo_data = {key: value for key, value in config_data["ppo"].items() if key in field_names}
    return PPOConfig(**ppo_data)


def test_sync_vector_env_applies_l0_profile_mask() -> None:
    config_data = read_json(L0_CONFIG)
    env_config = build_env_config(config_data["env"])
    ppo = replace(_ppo_config(config_data), vector_env_mode="sync")
    spec = mask_spec_from_config(config_data)

    raw_env = make_vector_env(ppo, env_config, seed=1195, seed_sequence=None)
    masked_env = make_vector_env(ppo, env_config, seed=1195, seed_sequence=None, observation_mask_spec=spec)
    try:
        raw_obs, _ = raw_env.reset()
        masked_obs, _ = masked_env.reset()
        assert np.all(masked_obs[:, list(PREVIOUS_COMMAND_INDICES)] == 0.0)
        assert raw_obs.shape == masked_obs.shape

        actions = np.tile(np.array([0.5, 0.2, -0.3], dtype=np.float32), (ppo.num_envs, 1))
        raw_step = raw_env.step(actions)
        masked_step = masked_env.step(actions)
        assert float(np.abs(raw_step.observations[:, list(PREVIOUS_COMMAND_INDICES)]).sum()) > 0.0
        assert np.all(masked_step.observations[:, list(PREVIOUS_COMMAND_INDICES)] == 0.0)
    finally:
        raw_env.close()
        masked_env.close()


def test_sync_vector_env_leaves_unmasked_profile_unchanged() -> None:
    config_data = read_json(L1_CONFIG)
    env_config = build_env_config(config_data["env"])
    ppo = replace(_ppo_config(config_data), vector_env_mode="sync")
    spec = mask_spec_from_config(config_data)

    raw_env = make_vector_env(ppo, env_config, seed=1196, seed_sequence=None)
    masked_env = make_vector_env(ppo, env_config, seed=1196, seed_sequence=None, observation_mask_spec=spec)
    try:
        raw_obs, _ = raw_env.reset()
        masked_obs, _ = masked_env.reset()
        assert np.allclose(raw_obs, masked_obs)

        actions = np.tile(np.array([0.5, 0.2, -0.3], dtype=np.float32), (ppo.num_envs, 1))
        raw_step = raw_env.step(actions)
        masked_step = masked_env.step(actions)
        assert np.allclose(raw_step.observations, masked_step.observations)
    finally:
        raw_env.close()
        masked_env.close()


def test_parallel_vector_env_applies_l0_profile_mask() -> None:
    config_data = read_json(L0_CONFIG)
    env_config = build_env_config(config_data["env"])
    ppo = replace(_ppo_config(config_data), num_envs=1, vector_env_mode="parallel", vector_env_start_method="fork")
    spec = mask_spec_from_config(config_data)

    env = make_vector_env(ppo, env_config, seed=1197, seed_sequence=None, observation_mask_spec=spec)
    try:
        obs, _ = env.reset()
        assert np.all(obs[:, list(PREVIOUS_COMMAND_INDICES)] == 0.0)

        step = env.step(np.array([[0.5, 0.2, -0.3]], dtype=np.float32))
        assert np.all(step.observations[:, list(PREVIOUS_COMMAND_INDICES)] == 0.0)
    finally:
        env.close()
