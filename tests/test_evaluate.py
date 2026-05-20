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
    policy = ActorPolicy(ActorCritic(obs_dim=28, act_dim=2, hidden_size=8), env_config, ablation="zero_action_history")
    observation = np.arange(28, dtype=np.float32)

    transformed = policy._transform_observation(observation)

    assert transformed[12] == 0.0
    assert transformed[13] == 0.0
    assert transformed[26] == 0.0
    assert transformed[27] == 0.0


def test_actor_policy_can_ablate_temporal_history():
    env_config = DriftEnvConfig(history_length=2, action_history_mode="legacy")
    policy = ActorPolicy(ActorCritic(obs_dim=26, act_dim=2, hidden_size=8), env_config, ablation="single_frame_history")
    observation = np.arange(26, dtype=np.float32)

    transformed = policy._transform_observation(observation)

    np.testing.assert_allclose(transformed[:13], transformed[13:])
