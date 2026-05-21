import pandas as pd
import pytest

from autodrift.artifacts import read_json
from autodrift.config import build_env_config
from autodrift.env import AutoDriftEnv
from autodrift.privileged_upper_bound import build_seed_delta, summarize_upper_bound
from autodrift.train_ppo import ActorCritic


def test_build_seed_delta_matches_repeated_seed_by_episode_index():
    frame = pd.DataFrame(
        [
            {
                "episode_index": 0,
                "seed": 11,
                "policy": "m62",
                "terminated": True,
                "collision": True,
                "obstacle_completed": False,
                "return": 1.0,
                "min_clearance_margin": -0.10,
                "mu": 0.4,
                "brake_scale": 0.8,
                "steer_tau_scale": 1.5,
            },
            {
                "episode_index": 1,
                "seed": 11,
                "policy": "m62",
                "terminated": False,
                "collision": False,
                "obstacle_completed": True,
                "return": 2.0,
                "min_clearance_margin": 0.05,
                "mu": 0.4,
                "brake_scale": 0.8,
                "steer_tau_scale": 1.5,
            },
            {
                "episode_index": 0,
                "seed": 11,
                "policy": "teacher",
                "terminated": False,
                "collision": False,
                "obstacle_completed": True,
                "return": 3.0,
                "min_clearance_margin": 0.20,
                "mu": 0.4,
                "brake_scale": 0.8,
                "steer_tau_scale": 1.5,
            },
            {
                "episode_index": 1,
                "seed": 11,
                "policy": "teacher",
                "terminated": False,
                "collision": False,
                "obstacle_completed": True,
                "return": 1.5,
                "min_clearance_margin": 0.01,
                "mu": 0.4,
                "brake_scale": 0.8,
                "steer_tau_scale": 1.5,
            },
        ]
    )

    delta = build_seed_delta(frame, "m62", "teacher")
    summary = summarize_upper_bound(delta, "m62", "teacher")

    assert delta["seed"].tolist() == [11, 11]
    assert delta["success_delta"].tolist() == [1.0, 0.0]
    assert delta["min_clearance_margin_delta"].tolist() == pytest.approx([0.30, -0.04])
    assert summary["success_delta"] == 0.5
    assert summary["candidate_margin_improved_count"] == 1
    assert summary["candidate_margin_regressed_count"] == 1


def test_build_seed_delta_requires_matching_episode_sequence():
    frame = pd.DataFrame(
        [
            {
                "episode_index": 0,
                "seed": 11,
                "policy": "m62",
                "terminated": False,
                "collision": False,
                "obstacle_completed": True,
                "return": 1.0,
                "min_clearance_margin": 0.1,
                "mu": 0.4,
                "brake_scale": 0.8,
                "steer_tau_scale": 1.5,
            },
            {
                "episode_index": 0,
                "seed": 12,
                "policy": "teacher",
                "terminated": False,
                "collision": False,
                "obstacle_completed": True,
                "return": 1.0,
                "min_clearance_margin": 0.1,
                "mu": 0.4,
                "brake_scale": 0.8,
                "steer_tau_scale": 1.5,
            },
        ]
    )

    with pytest.raises(ValueError, match="same episode_index and seed"):
        build_seed_delta(frame, "m62", "teacher")


def test_m67a_privileged_teacher_config_uses_full_dynamics_obs():
    raw_config = read_json("configs/ppo_m67a_privileged_upper_bound_teacher.json")
    env_config = build_env_config(raw_config["env"])
    env = AutoDriftEnv(env_config)

    assert env_config.include_privileged_params is True
    assert env_config.privileged_observation_mode == "full_dynamics"
    assert env.observation_space.shape == (82,)
    ActorCritic(
        obs_dim=int(env.observation_space.shape[0]),
        act_dim=3,
        hidden_size=8,
        actor_encoder=raw_config["ppo"]["actor_encoder"],
        response_prediction_dim=raw_config["ppo"]["response_prediction_dim"],
        response_prediction_horizon=raw_config["ppo"]["response_prediction_horizon"],
    )


def test_m67e_warm_started_privileged_teacher_config_uses_strict_teacher_frame():
    raw_config = read_json("configs/ppo_m67e_warm_started_privileged_teacher.json")
    env_config = build_env_config(raw_config["env"])
    env = AutoDriftEnv(env_config)
    obs, _ = env.reset(seed=3267)

    assert env_config.include_privileged_params is True
    assert env_config.privileged_observation_mode == "full_dynamics"
    assert env_config.obstacle_relative_velocity_mode == "zero"
    assert env.observation_space.shape == (82,)
    assert obs.shape == (82,)
    assert obs[47] == 0.0
    assert obs[48] == 0.0
    model = ActorCritic(
        obs_dim=int(env.observation_space.shape[0]),
        act_dim=3,
        hidden_size=8,
        actor_encoder=raw_config["ppo"]["actor_encoder"],
        response_prediction_dim=raw_config["ppo"]["response_prediction_dim"],
        response_prediction_horizon=raw_config["ppo"]["response_prediction_horizon"],
    )
    assert model.response_feature_indices == tuple(range(12))
    assert model.context_feature_indices == tuple(range(12, 72))
    assert model.privileged_feature_indices == tuple(range(72, 82))
