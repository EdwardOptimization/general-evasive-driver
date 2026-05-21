import numpy as np
import pytest

from autodrift.artifacts import read_json
from autodrift.config import build_env_config
from autodrift.dynamics import RandomizationConfig
from autodrift.env import AutoDriftEnv, DriftEnvConfig, FrictionStepConfig, ObstacleTaskConfig
from autodrift.policies import HeuristicPolicy
from autodrift.scenarios import ObstacleScenario


def test_env_reset_and_step_shapes():
    env = AutoDriftEnv()
    obs, info = env.reset(seed=11)

    assert obs.shape == env.observation_space.shape
    assert env.observation_space.contains(obs)
    assert 0.25 <= info["mu"] <= 1.15

    next_obs, reward, terminated, truncated, next_info = env.step(np.array([0.0, 0.2, -1.0], dtype=np.float32))

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

    assert obs.shape == (76,)


def test_full_dynamics_privileged_observation_adds_teacher_only_hidden_packet():
    env = AutoDriftEnv(
        DriftEnvConfig(
            include_privileged_params=True,
            privileged_observation_mode="full_dynamics",
            randomization=RandomizationConfig(
                mu_range=(0.42, 0.42),
                mass_scale_range=(1.10, 1.10),
                cg_shift_range=(0.05, 0.05),
                inertia_scale_range=(1.20, 1.20),
                tire_stiffness_scale_range=(0.80, 0.80),
                drive_scale_range=(1.30, 1.30),
                brake_scale_range=(0.70, 0.70),
                actuator_tau_scale_range=(1.50, 1.50),
            ),
        )
    )
    obs, info = env.reset(seed=12)

    assert obs.shape == (82,)
    assert np.allclose(
        obs[-10:],
        [
            info["mu"],
            info["mass_scale"],
            info["inertia_scale"],
            info["cg_shift"] / 0.25,
            info["front_tire_stiffness_scale"],
            info["rear_tire_stiffness_scale"],
            info["drive_scale"],
            info["brake_scale"],
            info["steer_tau_scale"],
            info["drive_tau_scale"],
        ],
    )


def test_privileged_observation_mode_rejects_unknown_mode():
    with pytest.raises(ValueError, match="privileged_observation_mode"):
        DriftEnvConfig(privileged_observation_mode="oracle")


def test_history_observation_stacks_recent_frames():
    env = AutoDriftEnv(DriftEnvConfig(history_length=4))
    obs, _ = env.reset(seed=15)
    next_obs, _, _, _, _ = env.step(np.array([0.0, 0.2, -1.0], dtype=np.float32))

    assert obs.shape == (288,)
    assert next_obs.shape == (288,)
    assert not np.allclose(next_obs[:72], next_obs[72:144])


def test_full_action_history_observation_adds_previous_steer_and_drive():
    env = AutoDriftEnv(DriftEnvConfig(action_history_mode="full", history_length=2))
    obs, _ = env.reset(seed=17)

    assert obs.shape == (144,)
    assert np.allclose(obs[9:12], [0.0, 0.0, 0.0])

    next_obs, _, _, _, info = env.step(np.array([0.4, 0.2, -1.0], dtype=np.float32))

    assert next_obs.shape == (144,)
    assert np.allclose(next_obs[9:12], [0.4, 0.6, 0.0])
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

    assert obs.shape == (72,)
    assert info["obstacle_enabled"] is True
    assert info["obstacle_perception_visible"] is True
    assert info["obstacle_label"] in {"aeb_feasible", "aes_feasible", "drift_required", "unavoidable"}
    assert info["obstacle_distance"] > 0.0
    assert info["collision"] is False
    assert np.isclose(info["obstacle_collision_radius"], 1.70)
    assert np.isfinite(info["min_clearance_margin"])
    assert len(env._obstacle_slot_features()) == env.config.obstacle_slots * 7
    assert env._obstacle_slot_features()[0] == 1.0


def test_obstacle_relative_velocity_mode_can_zero_context_motion_proxy():
    base_config = dict(
        speed_range=(12.0, 12.0),
        friction_limited_speed=False,
        obstacle=ObstacleTaskConfig(
            enabled=True,
            distance_range=(20.0, 20.0),
            half_width_range=(0.8, 0.8),
        ),
    )
    default_env = AutoDriftEnv(DriftEnvConfig(**base_config))
    strict_env = AutoDriftEnv(DriftEnvConfig(**base_config, obstacle_relative_velocity_mode="zero"))

    default_obs, _ = default_env.reset(seed=21)
    strict_obs, _ = strict_env.reset(seed=21)
    default_slots = default_env._obstacle_slot_features()
    strict_slots = strict_env._obstacle_slot_features()

    assert default_obs.shape == (72,)
    assert strict_obs.shape == (72,)
    assert np.linalg.norm(default_slots[3:5]) > 0.0
    assert strict_slots[3:5] == [0.0, 0.0]
    assert np.allclose(default_slots[:3], strict_slots[:3])
    assert np.allclose(default_slots[5:7], strict_slots[5:7])


def test_obstacle_perception_reveal_can_hide_obstacle_slots_until_step_or_distance():
    env = AutoDriftEnv(
        DriftEnvConfig(
            speed_range=(8.0, 8.0),
            friction_limited_speed=False,
            obstacle=ObstacleTaskConfig(
                enabled=True,
                distance_range=(20.0, 20.0),
                half_width_range=(0.8, 0.8),
                perception_reveal_step=5,
                perception_reveal_distance=12.0,
            ),
        )
    )
    _, info = env.reset(seed=22)

    assert info["obstacle_perception_visible"] is False
    assert env._obstacle_slot_features()[0] == 0.0

    env.step_count = 5
    assert env._obstacle_perception_visible(longitudinal_distance=20.0) is False
    assert env._obstacle_perception_visible(longitudinal_distance=12.0) is True

    env.step_count = 8
    _, info = env.reset(seed=22)
    assert info["obstacle_perception_visible"] is False
    assert env._obstacle_slot_features()[0] == 0.0


def test_obstacle_relative_velocity_mode_rejects_unknown_mode():
    with pytest.raises(ValueError, match="obstacle_relative_velocity_mode"):
        DriftEnvConfig(obstacle_relative_velocity_mode="world")


def test_front_rear_wheel_observation_adds_response_features():
    env = AutoDriftEnv(DriftEnvConfig(wheel_observation_mode="front_rear"))
    obs, _ = env.reset(seed=23)

    assert obs.shape == (85,)
    wheel_features = obs[12:25]
    assert wheel_features.shape == (13,)
    assert np.isfinite(wheel_features).all()
    assert np.allclose(wheel_features[4:7], 0.0)

    next_obs, _, _, _, _ = env.step(np.array([0.0, 1.0, -1.0], dtype=np.float32))

    assert next_obs.shape == (85,)
    assert np.isfinite(next_obs[12:25]).all()


def test_front_rear_raw_wheel_observation_keeps_clean_slot_shape():
    env = AutoDriftEnv(DriftEnvConfig(wheel_observation_mode="front_rear_raw"))
    obs, _ = env.reset(seed=24)

    assert obs.shape == (85,)
    wheel_features = obs[12:25]
    assert wheel_features.shape == (13,)
    assert np.isfinite(wheel_features).all()
    np.testing.assert_allclose(wheel_features[4:7], np.zeros(3, dtype=np.float32))
    np.testing.assert_allclose(wheel_features[10:13], np.zeros(3, dtype=np.float32))

    next_obs, _, _, _, _ = env.step(np.array([0.0, 1.0, -1.0], dtype=np.float32))
    next_wheel_features = next_obs[12:25]

    assert next_obs.shape == (85,)
    assert np.isfinite(next_wheel_features).all()
    np.testing.assert_allclose(next_wheel_features[4:7], np.zeros(3, dtype=np.float32))
    np.testing.assert_allclose(next_wheel_features[10:13], np.zeros(3, dtype=np.float32))


def test_wheel_observation_mode_rejects_unknown_mode():
    with pytest.raises(ValueError, match="wheel_observation_mode"):
        DriftEnvConfig(wheel_observation_mode="oracle")


def test_m8_driver_config_uses_deployable_observation_contract():
    config = build_env_config(read_json("configs/ppo_m8_temporal_gru_driver.json")["env"])
    env = AutoDriftEnv(config)

    assert config.include_privileged_params is False
    assert config.friction_limited_speed is False
    assert config.history_length == 4
    assert config.action_history_mode == "full"
    assert env.base_obs_dim == 72
    assert env.observation_space.shape == (288,)


def test_m67d_strict_self_id_config_preserves_clean_72_value_shape():
    config = build_env_config(read_json("configs/ppo_m67d_strict_self_id_context_driver.json")["env"])
    env = AutoDriftEnv(config)
    obs, _ = env.reset(seed=3600)

    assert config.include_privileged_params is False
    assert config.obstacle_relative_velocity_mode == "zero"
    assert env.base_obs_dim == 72
    assert env.observation_space.shape == (72,)
    assert obs.shape == (72,)
    assert np.allclose(obs[[47, 48]], [0.0, 0.0])


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


def test_obstacle_task_can_sample_near_threshold_cases():
    env = AutoDriftEnv(
        DriftEnvConfig(
            track_radius=60.0,
            speed_range=(11.0, 16.0),
            friction_limited_speed=False,
            friction_step=FrictionStepConfig(enabled=True, step_range=(8, 40), resample_speed_ref=False),
            obstacle=ObstacleTaskConfig(
                enabled=True,
                distance_range=(3.0, 25.0),
                half_width_range=(0.45, 1.15),
                require_aeb_infeasible=True,
                allowed_labels=("aes_feasible", "drift_required", "unavoidable"),
                max_sample_attempts=10000,
                max_threshold_score=0.25,
                min_time_after_friction_step=0.10,
            ),
            randomization=RandomizationConfig(mu_range=(0.25, 0.75)),
        )
    )

    _, info = env.reset(seed=3838)

    assert info["obstacle_label"] in {"aes_feasible", "drift_required", "unavoidable"}
    assert info["obstacle_label"] != "aeb_feasible"
    assert info["obstacle_threshold_score"] <= 0.25
    assert info["obstacle_time_after_friction_step"] >= 0.10
    assert 8 <= info["friction_step_at"] <= 40


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

    _, reward, terminated, _, next_info = env.step(np.array([0.0, -1.0, -1.0], dtype=np.float32))

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

    _, reward, terminated, truncated, info = env.step(np.array([0.0, -1.0, -1.0], dtype=np.float32))

    assert terminated is False
    assert truncated is True
    assert info["obstacle_completed"] is True
    assert info["reward_terms"]["pass_reward"] == 5.0
    assert reward > 0.0


def test_terminal_clearance_margin_reward_is_config_gated():
    disabled_env = AutoDriftEnv(
        DriftEnvConfig(
            obstacle=ObstacleTaskConfig(
                enabled=True,
                distance_range=(20.0, 20.0),
                half_width_range=(0.8, 0.8),
                finish_on_pass=True,
                finish_pass_distance=2.0,
                pass_reward=0.0,
            )
        )
    )
    shaped_env = AutoDriftEnv(
        DriftEnvConfig(
            obstacle=ObstacleTaskConfig(
                enabled=True,
                distance_range=(20.0, 20.0),
                half_width_range=(0.8, 0.8),
                finish_on_pass=True,
                finish_pass_distance=2.0,
                pass_reward=0.0,
                clearance_margin_reward_scale=2.0,
                clearance_margin_reward_clip=1.0,
            )
        )
    )
    disabled_obs, _ = disabled_env.reset(seed=32)
    shaped_obs, _ = shaped_env.reset(seed=32)
    assert disabled_obs.shape == shaped_obs.shape == (72,)

    for env in (disabled_env, shaped_env):
        frame = env.track.frame(env.state.x, env.state.y, env.state.psi)
        position = np.array([env.state.x, env.state.y], dtype=np.float64)
        env.obstacle_position = position - frame.tangent * 3.0
        env.collision = False
        env.min_obstacle_clearance = 3.0

    action = np.array([0.0, -1.0, -1.0], dtype=np.float32)
    _, _, _, disabled_truncated, disabled_info = disabled_env.step(action)
    _, shaped_reward, _, shaped_truncated, shaped_info = shaped_env.step(action)

    assert disabled_truncated is True
    assert shaped_truncated is True
    assert "clearance_margin_reward" not in disabled_info["reward_terms"]
    assert np.isclose(shaped_info["reward_terms"]["clearance_margin_reward"], 2.0)
    assert np.isclose(shaped_info["reward_terms"]["clearance_margin_reward_normalized"], 1.0)
    assert shaped_reward > 0.0


def test_terminal_clearance_margin_reward_penalizes_collision_margin():
    env = AutoDriftEnv(
        DriftEnvConfig(
            obstacle=ObstacleTaskConfig(
                enabled=True,
                distance_range=(0.1, 0.1),
                half_width_range=(1.0, 1.0),
                collision_penalty=0.0,
                clearance_margin_reward_scale=2.0,
                clearance_margin_reward_clip=1.0,
            )
        )
    )
    _, info = env.reset(seed=21)
    assert info["collision"] is True

    _, _, terminated, _, next_info = env.step(np.array([0.0, -1.0, -1.0], dtype=np.float32))

    assert terminated is True
    assert np.isclose(next_info["reward_terms"]["clearance_margin_reward"], -2.0)
    assert np.isclose(next_info["reward_terms"]["clearance_margin_reward_normalized"], -1.0)


def test_dense_clearance_margin_reward_only_applies_near_obstacle_window():
    near_env = AutoDriftEnv(
        DriftEnvConfig(
            obstacle=ObstacleTaskConfig(
                enabled=True,
                distance_range=(20.0, 20.0),
                half_width_range=(0.8, 0.8),
                dense_clearance_margin_reward_scale=0.5,
                dense_clearance_margin_reward_clip=1.0,
                dense_clearance_margin_reward_window=8.0,
            )
        )
    )
    far_env = AutoDriftEnv(
        DriftEnvConfig(
            obstacle=ObstacleTaskConfig(
                enabled=True,
                distance_range=(20.0, 20.0),
                half_width_range=(0.8, 0.8),
                dense_clearance_margin_reward_scale=0.5,
                dense_clearance_margin_reward_clip=1.0,
                dense_clearance_margin_reward_window=8.0,
            )
        )
    )
    near_obs, _ = near_env.reset(seed=34)
    far_obs, _ = far_env.reset(seed=34)
    assert near_obs.shape == far_obs.shape == (72,)

    for env, distance in ((near_env, 5.0), (far_env, 20.0)):
        frame = env.track.frame(env.state.x, env.state.y, env.state.psi)
        position = np.array([env.state.x, env.state.y], dtype=np.float64)
        env.obstacle_position = position + frame.tangent * distance
        env.collision = False
        env.min_obstacle_clearance = float("inf")

    action = np.array([0.0, -1.0, -1.0], dtype=np.float32)
    _, _, _, _, near_info = near_env.step(action)
    _, _, _, _, far_info = far_env.step(action)

    assert np.isclose(near_info["reward_terms"]["dense_clearance_margin_reward"], 0.5)
    assert np.isclose(near_info["reward_terms"]["dense_clearance_margin_reward_normalized"], 1.0)
    assert "dense_clearance_margin_reward" not in far_info["reward_terms"]


def test_stable_aes_reward_penalizes_high_sideslip_without_oracle_observation():
    base_config = DriftEnvConfig(
        obstacle=ObstacleTaskConfig(
            enabled=True,
            stable_aes_beta_limit=0.20,
            stable_aes_sideslip_penalty=0.0,
            stable_aes_drift_bonus_scale=1.0,
        )
    )
    penalty_config = DriftEnvConfig(
        obstacle=ObstacleTaskConfig(
            enabled=True,
            stable_aes_beta_limit=0.20,
            stable_aes_sideslip_penalty=3.0,
            stable_aes_drift_bonus_scale=0.25,
        )
    )
    base_env = AutoDriftEnv(base_config)
    penalty_env = AutoDriftEnv(penalty_config)
    base_env.reset(seed=42)
    penalty_env.reset(seed=42)

    scenario = ObstacleScenario(
        seed=42,
        speed=10.0,
        mu=0.9,
        obstacle_distance=12.0,
        obstacle_half_width=0.8,
        required_lateral_offset=2.0,
        time_to_obstacle=1.2,
        aeb_stop_distance=12.5,
        conventional_lateral_capacity=2.3,
        drift_lateral_capacity=4.6,
        label="aes_feasible",
    )
    for env in (base_env, penalty_env):
        env.obstacle_scenario = scenario
        env.state.vx = 10.0
        env.state.vy = 3.0
        env.beta_target = 0.25

    action = np.zeros(3, dtype=np.float32)
    base_frame = base_env.track.frame(base_env.state.x, base_env.state.y, base_env.state.psi)
    penalty_frame = penalty_env.track.frame(penalty_env.state.x, penalty_env.state.y, penalty_env.state.psi)
    base_reward, base_terms = base_env._reward(base_frame, action, base_env.last_forces)
    penalty_reward, penalty_terms = penalty_env._reward(penalty_frame, action, penalty_env.last_forces)

    assert penalty_terms["stable_aes_sideslip_cost"] > 0.0
    assert penalty_terms["drift_bonus"] < base_terms["drift_bonus"]
    assert penalty_reward < base_reward
    assert np.isclose(base_terms["stable_aes_sideslip_cost"], penalty_terms["stable_aes_sideslip_cost"])


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
        _, _, _, _, info = env.step(np.array([0.0, 0.2, -1.0], dtype=np.float32))

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

    action = np.array([0.0, -1.0, -1.0], dtype=np.float32)
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
