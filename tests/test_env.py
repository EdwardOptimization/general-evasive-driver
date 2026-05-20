import numpy as np

from autodrift.dynamics import RandomizationConfig
from autodrift.env import AutoDriftEnv, DriftEnvConfig, FrictionStepConfig
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


def test_history_observation_stacks_recent_frames():
    env = AutoDriftEnv(DriftEnvConfig(history_length=4))
    obs, _ = env.reset(seed=15)
    next_obs, _, _, _, _ = env.step(np.array([0.0, 0.2], dtype=np.float32))

    assert obs.shape == (52,)
    assert next_obs.shape == (52,)
    assert not np.allclose(next_obs[:13], next_obs[13:26])


def test_speed_reference_respects_low_friction_limit():
    env = AutoDriftEnv(
        DriftEnvConfig(
            track_radius=18.0,
            speed_range=(8.0, 12.0),
            randomization=RandomizationConfig(mu_range=(0.25, 0.25)),
        )
    )
    _, info = env.reset(seed=14)

    friction_limit = (info["mu"] * 9.81 * 18.0) ** 0.5 * env.config.friction_speed_margin
    assert info["speed_ref"] <= friction_limit + 1e-9


def test_figure_eight_env_reset_reports_track_kind_and_curvature():
    env = AutoDriftEnv(DriftEnvConfig(track_kind="figure_eight", speed_range=(4.0, 8.0)))
    obs, info = env.reset(seed=18)

    assert obs.shape == env.observation_space.shape
    assert info["track_kind"] == "figure_eight"
    assert np.isfinite(env.track.frame(env.state.x, env.state.y, env.state.psi).curvature)


def test_friction_step_changes_mu_and_reports_transition():
    env = AutoDriftEnv(
        DriftEnvConfig(
            friction_step=FrictionStepConfig(
                enabled=True,
                step_range=(3, 3),
                mu_range=(0.35, 0.35),
            ),
            randomization=RandomizationConfig(mu_range=(1.0, 1.0)),
        )
    )
    _, info = env.reset(seed=16)
    assert info["initial_mu"] == 1.0
    assert info["mu"] == 1.0
    assert info["friction_step_at"] == 3

    for _ in range(3):
        _, _, _, _, info = env.step(np.array([0.0, 0.2], dtype=np.float32))

    assert info["initial_mu"] == 1.0
    assert info["mu"] == 0.35
    assert info["friction_step_applied"] is True


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
