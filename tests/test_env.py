import numpy as np

from autodrift.dynamics import RandomizationConfig
from autodrift.env import AutoDriftEnv, DriftEnvConfig, FrictionStepConfig, ObstacleTaskConfig
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
    assert np.isfinite(next_info["curvature"])
    assert np.isfinite(next_info["progress"])


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


def test_full_action_history_observation_adds_previous_steer_and_drive():
    env = AutoDriftEnv(DriftEnvConfig(action_history_mode="full", history_length=2))
    obs, _ = env.reset(seed=17)

    assert obs.shape == (28,)
    assert np.allclose(obs[12:14], [0.0, 0.0])

    next_obs, _, _, _, info = env.step(np.array([0.4, -0.2], dtype=np.float32))

    assert next_obs.shape == (28,)
    assert np.allclose(next_obs[12:14], [-0.2, 0.4])
    assert "brake_scale" in info
    assert "steer_tau_scale" in info


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


def test_obstacle_task_adds_observation_features_and_info():
    env = AutoDriftEnv(
        DriftEnvConfig(
            obstacle=ObstacleTaskConfig(
                enabled=True,
                distance_range=(20.0, 20.0),
                half_width_range=(0.8, 0.8),
            )
        )
    )
    obs, info = env.reset(seed=20)

    assert obs.shape == (18,)
    assert info["obstacle_enabled"] is True
    assert info["obstacle_label"] in {"aeb_feasible", "aes_feasible", "drift_required", "unavoidable"}
    assert info["obstacle_distance"] > 0.0
    assert info["collision"] is False


def test_obstacle_task_can_require_aeb_infeasible_labels():
    env = AutoDriftEnv(
        DriftEnvConfig(
            speed_range=(14.0, 16.0),
            friction_limited_speed=False,
            obstacle=ObstacleTaskConfig(
                enabled=True,
                distance_range=(7.0, 9.0),
                half_width_range=(0.8, 1.0),
                require_aeb_infeasible=True,
            )
        )
    )

    for seed in range(22, 32):
        _, info = env.reset(seed=seed)
        assert info["obstacle_label"] != "aeb_feasible"


def test_obstacle_task_can_filter_allowed_labels():
    env = AutoDriftEnv(
        DriftEnvConfig(
            speed_range=(14.0, 16.0),
            friction_limited_speed=False,
            obstacle=ObstacleTaskConfig(
                enabled=True,
                distance_range=(1.0, 2.0),
                half_width_range=(0.8, 1.0),
                require_aeb_infeasible=True,
                allowed_labels=("unavoidable",),
                max_sample_attempts=1000,
            )
        )
    )

    for seed in range(33, 38):
        _, info = env.reset(seed=seed)
        assert info["obstacle_label"] == "unavoidable"


def test_obstacle_collision_terminates_episode_and_penalizes_reward():
    env = AutoDriftEnv(
        DriftEnvConfig(
            obstacle=ObstacleTaskConfig(
                enabled=True,
                distance_range=(0.1, 0.1),
                half_width_range=(1.0, 1.0),
                collision_penalty=7.0,
            )
        )
    )
    _, info = env.reset(seed=21)
    assert info["collision"] is True

    _, reward, terminated, _, next_info = env.step(np.array([0.0, 0.0], dtype=np.float32))

    assert terminated is True
    assert next_info["collision"] is True
    assert next_info["reward_terms"]["collision_penalty"] == 7.0
    assert reward < 0.0


def test_obstacle_pass_can_complete_episode_successfully():
    env = AutoDriftEnv(
        DriftEnvConfig(
            obstacle=ObstacleTaskConfig(
                enabled=True,
                distance_range=(20.0, 20.0),
                half_width_range=(0.8, 0.8),
                finish_on_pass=True,
                finish_pass_distance=2.0,
                pass_reward=5.0,
            )
        )
    )
    _, _ = env.reset(seed=32)
    frame = env.track.frame(env.state.x, env.state.y, env.state.psi)
    position = np.array([env.state.x, env.state.y], dtype=np.float64)
    env.obstacle_position = position - frame.tangent * 3.0
    env.collision = False
    env.min_obstacle_clearance = 3.0

    _, reward, terminated, truncated, info = env.step(np.array([0.0, 0.0], dtype=np.float32))

    assert terminated is False
    assert truncated is True
    assert info["obstacle_completed"] is True
    assert info["reward_terms"]["pass_reward"] == 5.0
    assert reward > 0.0


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


def test_termination_penalty_is_subtracted_on_failure():
    base_env = AutoDriftEnv(DriftEnvConfig(track_width=1.0, termination_penalty=0.0))
    penalty_env = AutoDriftEnv(DriftEnvConfig(track_width=1.0, termination_penalty=5.0))
    _, _ = base_env.reset(seed=19)
    _, _ = penalty_env.reset(seed=19)
    for env in (base_env, penalty_env):
        env.state.x = env.config.track_radius + 3.0
        env.state.y = 0.0
        env.state.psi = 0.0

    action = np.array([0.0, 0.0], dtype=np.float32)
    _, base_reward, base_terminated, _, _ = base_env.step(action)
    _, penalty_reward, penalty_terminated, _, penalty_info = penalty_env.step(action)

    assert base_terminated is True
    assert penalty_terminated is True
    assert np.isclose(base_reward - penalty_reward, 5.0)
    assert penalty_info["reward_terms"]["termination_penalty"] == 5.0


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
