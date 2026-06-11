import numpy as np
import pytest

from autodrift.artifacts import read_json
from autodrift.config import build_env_config
from autodrift.dynamics import RandomizationConfig, VehicleState
from autodrift.env import (
    AutoDriftEnv,
    DriftEnvConfig,
    FrictionStepConfig,
    ObservationScaleConfig,
    ObstacleTaskConfig,
    WarmupGateConfig,
)
from autodrift.policies import HeuristicPolicy
from autodrift.scenarios import ObstacleScenario
from autodrift.tasks import PathFrame


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
    assert "termination_reason" in next_info
    assert "obstacle_passed_raw" in next_info
    assert "completion_reason" in next_info


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


def test_road_margin_cost_is_default_off_and_configurable():
    env = AutoDriftEnv()
    env.reset(seed=141)
    frame = PathFrame(
        lateral_error=4.0,
        heading_error=0.0,
        curvature=0.0,
        progress=0.0,
        tangent_heading=0.0,
        tangent=np.array([1.0, 0.0], dtype=np.float64),
    )

    _, default_terms = env._reward(frame, env.last_control, env.last_forces)

    repaired_env = AutoDriftEnv(
        DriftEnvConfig(track_width=5.0, road_margin_cost_scale=2.0, road_margin_warning_fraction=0.5)
    )
    repaired_env.reset(seed=141)
    _, repaired_terms = repaired_env._reward(frame, repaired_env.last_control, repaired_env.last_forces)

    assert "road_margin_cost" not in default_terms
    assert repaired_terms["road_margin_fraction"] == pytest.approx(0.8)
    assert repaired_terms["road_margin_cost"] == pytest.approx(0.36)


def test_off_track_penalty_is_separate_from_generic_termination_penalty():
    env = AutoDriftEnv(
        DriftEnvConfig(
            friction_limited_speed=False,
            speed_range=(8.0, 8.0),
            track_radius=18.0,
            track_width=0.1,
            termination_penalty=1.0,
            off_track_penalty=4.0,
        )
    )
    env.reset(seed=142)
    env.state = VehicleState(19.0, 0.0, np.pi / 2.0, 8.0, 0.0, 0.0)

    _, _, terminated, _, info = env.step(np.array([0.0, -1.0, -1.0], dtype=np.float32))

    assert terminated is True
    assert info["termination_reason"] == "off_track"
    assert info["reward_terms"]["termination_penalty"] == pytest.approx(1.0)
    assert info["reward_terms"]["off_track_penalty"] == pytest.approx(4.0)


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


def test_default_observation_scale_preserves_legacy_obs72_and_fixed_preview():
    env = AutoDriftEnv(DriftEnvConfig(friction_limited_speed=False, speed_range=(20.0, 20.0)))
    obs, info = env.reset(seed=2001)

    assert obs.shape == (72,)
    np.testing.assert_allclose(env._road_lookahead_distances(), np.arange(5.0, 45.0, 5.0))
    assert info["road_lookahead_distance_max"] == pytest.approx(40.0)
    assert info["max_speed_limit"] == pytest.approx(32.0)

    env.state = VehicleState(env.state.x, env.state.y, env.state.psi, 20.0, 12.0, env.state.yaw_rate)
    scaled = env._base_observation()

    assert scaled[0] == pytest.approx(1.0)
    assert scaled[1] == pytest.approx(1.0)


def test_high_speed_observation_scale_keeps_shape_and_extends_preview():
    env = AutoDriftEnv(
        DriftEnvConfig(
            friction_limited_speed=False,
            speed_range=(36.0, 36.0),
            track_radius=250.0,
            max_speed_limit=45.0,
            observation_scale=ObservationScaleConfig(
                ego_vx=40.0,
                ego_vy=40.0,
                ego_ax=50.0,
                ego_ay=60.0,
                road_y=60.0,
                obstacle_rel_vy=30.0,
                road_lookahead_time_s=2.5,
                road_lookahead_max_distance=120.0,
            ),
        )
    )
    obs, info = env.reset(seed=2002)

    assert obs.shape == (72,)
    assert env._road_lookahead_distances()[-1] == pytest.approx(90.0)
    assert info["road_lookahead_distance_max"] == pytest.approx(90.0)
    assert info["road_lookahead_time_s"] == pytest.approx(2.5, rel=1e-5)
    assert info["max_speed_limit"] == pytest.approx(45.0)

    env.state = VehicleState(env.state.x, env.state.y, env.state.psi, 36.0, 12.0, env.state.yaw_rate)
    scaled = env._base_observation()

    assert scaled[0] == pytest.approx(0.9)
    assert scaled[1] == pytest.approx(0.3)


def test_observation_scale_rejects_bad_constants():
    with pytest.raises(ValueError, match="observation_scale"):
        ObservationScaleConfig(ego_vx=0.0)
    with pytest.raises(ValueError, match="road_lookahead_time_s"):
        ObservationScaleConfig(road_lookahead_time_s=-0.1)


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


def _moving_crosser_config(relative_velocity_mode: str = "ego") -> DriftEnvConfig:
    return DriftEnvConfig(
        dt=0.02,
        max_steps=90,
        track_kind="circle",
        track_radius=60.0,
        track_width=8.5,
        speed_range=(12.0, 12.0),
        beta_target_range=(0.04, 0.04),
        friction_limited_speed=False,
        obstacle_relative_velocity_mode=relative_velocity_mode,
        obstacle=ObstacleTaskConfig(
            enabled=True,
            distance_range=(24.0, 24.0),
            half_width_range=(0.7, 0.7),
            lateral_offset_range=(-2.0, -2.0),
            finish_on_pass=True,
            allowed_labels=("aeb_feasible", "aes_feasible", "drift_required", "unavoidable"),
            motion_mode="constant_velocity_crosser",
            crosser_lateral_velocity_range=(4.0, 4.0),
        ),
    )


def _first_obstacle_slot(obs: np.ndarray) -> np.ndarray:
    # obs72 layout: ego9 + action3 + road32, then obstacle slot0 x 7.
    return np.asarray(obs[44:51], dtype=np.float64)


def test_moving_obstacle_preserves_zero_relative_velocity_contract():
    env = AutoDriftEnv(_moving_crosser_config(relative_velocity_mode="zero"))
    obs, info = env.reset(seed=2301)

    assert obs.shape == (72,)
    assert info["obstacle_motion_mode"] == "constant_velocity_crosser"
    assert info["obstacle_lateral_velocity"] == pytest.approx(4.0)
    for _ in range(8):
        slot = _first_obstacle_slot(obs)
        assert slot[0] == 1.0
        assert slot[3:5].tolist() == [0.0, 0.0]
        obs, _, terminated, truncated, _ = env.step(np.array([0.0, 0.0, -1.0], dtype=np.float32))
        assert not (terminated or truncated)


def test_moving_obstacle_updates_position_and_exposes_ego_relative_velocity():
    env = AutoDriftEnv(_moving_crosser_config(relative_velocity_mode="ego"))
    obs, info = env.reset(seed=2302)
    body_y = [float(info["active_obstacle_body_y"])]
    rel_norms = [float(np.linalg.norm(_first_obstacle_slot(obs)[3:5]))]

    assert info["obstacle_motion_mode"] == "constant_velocity_crosser"
    assert info["obstacle_predicted_lateral_offset_at_arrival"] == pytest.approx(6.0)
    assert env.obstacle_scenario is not None
    assert env.obstacle_scenario.required_lateral_offset == pytest.approx(0.0)

    for _ in range(12):
        obs, _, terminated, truncated, info = env.step(np.array([0.0, 0.0, -1.0], dtype=np.float32))
        body_y.append(float(info["active_obstacle_body_y"]))
        rel_norms.append(float(np.linalg.norm(_first_obstacle_slot(obs)[3:5])))
        assert not (terminated or truncated)

    assert max(body_y) - min(body_y) > 0.5
    assert max(rel_norms) > 0.01


def test_moving_obstacle_replay_is_deterministic_for_same_seed_and_actions():
    actions = [
        np.array([0.05 * np.sin(i), -0.2, -1.0], dtype=np.float32)
        for i in range(14)
    ]

    def rollout() -> list[tuple[np.ndarray, float, bool, bool, dict[str, float | bool | str]]]:
        env = AutoDriftEnv(_moving_crosser_config(relative_velocity_mode="ego"))
        obs, info = env.reset(seed=2303)
        rows = [(obs.copy(), 0.0, False, False, info)]
        for action in actions:
            obs, reward, terminated, truncated, info = env.step(action)
            rows.append((obs.copy(), reward, terminated, truncated, info))
            if terminated or truncated:
                break
        return rows

    left = rollout()
    right = rollout()

    assert len(left) == len(right)
    for (obs_l, reward_l, terminated_l, truncated_l, info_l), (
        obs_r,
        reward_r,
        terminated_r,
        truncated_r,
        info_r,
    ) in zip(left, right, strict=True):
        np.testing.assert_allclose(obs_l, obs_r, atol=1e-7, rtol=0.0)
        assert reward_l == pytest.approx(reward_r, abs=1e-12)
        assert terminated_l is terminated_r
        assert truncated_l is truncated_r
        for key in (
            "active_obstacle_body_x",
            "active_obstacle_body_y",
            "obstacle_lateral_velocity",
            "obstacle_predicted_lateral_offset_at_arrival",
            "collision",
            "obstacle_completed",
            "termination_reason",
            "completion_reason",
        ):
            assert info_l[key] == pytest.approx(info_r[key]) if isinstance(info_l[key], float) else info_l[key] == info_r[key]


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


def test_warmup_gate_defaults_preserve_obstacle_slot_behavior():
    base_env = AutoDriftEnv(
        DriftEnvConfig(
            speed_range=(8.0, 8.0),
            friction_limited_speed=False,
            obstacle=ObstacleTaskConfig(
                enabled=True,
                distance_range=(20.0, 20.0),
                half_width_range=(0.8, 0.8),
            ),
        )
    )
    explicit_disabled_env = AutoDriftEnv(
        DriftEnvConfig(
            speed_range=(8.0, 8.0),
            friction_limited_speed=False,
            obstacle=ObstacleTaskConfig(
                enabled=True,
                distance_range=(20.0, 20.0),
                half_width_range=(0.8, 0.8),
            ),
            warmup_gate=WarmupGateConfig(enabled=False),
        )
    )

    base_obs, base_info = base_env.reset(seed=220)
    disabled_obs, disabled_info = explicit_disabled_env.reset(seed=220)

    assert base_obs.shape == disabled_obs.shape == (72,)
    np.testing.assert_allclose(base_env._obstacle_slot_features(), explicit_disabled_env._obstacle_slot_features())
    assert base_info["active_obstacle_kind"] == disabled_info["active_obstacle_kind"] == "emergency_obstacle"
    assert base_info["warmup_gate_enabled"] is False
    assert disabled_info["warmup_gate_enabled"] is False


def test_warmup_gate_can_occupy_slot0_before_emergency_reveal():
    env = AutoDriftEnv(
        DriftEnvConfig(
            speed_range=(8.0, 8.0),
            friction_limited_speed=False,
            obstacle_relative_velocity_mode="zero",
            obstacle=ObstacleTaskConfig(
                enabled=True,
                distance_range=(30.0, 30.0),
                half_width_range=(0.8, 0.8),
                perception_reveal_step=20,
            ),
            warmup_gate=WarmupGateConfig(
                enabled=True,
                distance_range=(12.0, 12.0),
                lateral_offset_range=(1.0, 1.0),
                half_width_range=(0.5, 0.5),
                reveal_step=0,
                max_active_steps=30,
            ),
        )
    )

    obs, info = env.reset(seed=221)
    slot0 = obs[44:51]

    assert obs.shape == (72,)
    assert info["active_obstacle_kind"] == "warmup_gate"
    assert info["warmup_gate_active"] is True
    assert info["warmup_gate_visible"] is True
    assert info["obstacle_perception_visible"] is False
    assert slot0[0] == 1.0
    assert np.isclose(slot0[5], 0.1)
    assert np.isclose(slot0[6], 0.1)
    assert np.allclose(slot0[3:5], [0.0, 0.0])


def test_warmup_gate_switches_slot0_to_emergency_obstacle_after_timeout():
    env = AutoDriftEnv(
        DriftEnvConfig(
            speed_range=(8.0, 8.0),
            friction_limited_speed=False,
            obstacle_relative_velocity_mode="zero",
            obstacle=ObstacleTaskConfig(
                enabled=True,
                distance_range=(30.0, 30.0),
                half_width_range=(0.8, 0.8),
                perception_reveal_step=0,
                perception_reveal_distance=100.0,
            ),
            warmup_gate=WarmupGateConfig(
                enabled=True,
                distance_range=(12.0, 12.0),
                lateral_offset_range=(1.0, 1.0),
                half_width_range=(0.5, 0.5),
                reveal_step=0,
                max_active_steps=1,
            ),
        )
    )

    reset_obs, reset_info = env.reset(seed=222)
    reset_slot0 = reset_obs[44:51].copy()
    next_obs, _, _, _, next_info = env.step(np.array([0.0, -1.0, -1.0], dtype=np.float32))
    next_slot0 = next_obs[44:51]

    assert reset_info["active_obstacle_kind"] == "warmup_gate"
    assert next_info["active_obstacle_kind"] == "emergency_obstacle"
    assert next_info["warmup_gate_active"] is False
    assert next_info["warmup_gate_min_clearance"] < float("inf")
    assert np.isfinite(next_info["warmup_gate_clearance_margin"])
    assert next_obs.shape == (72,)
    assert reset_slot0[0] == next_slot0[0] == 1.0
    assert not np.allclose(reset_slot0[1:3], next_slot0[1:3])
    assert np.isclose(next_slot0[5], 0.16)
    assert np.isclose(next_slot0[6], 0.16)


def test_warmup_gate_config_can_be_loaded_from_json_dict():
    config = build_env_config(
        {
            "warmup_gate": {
                "enabled": True,
                "distance_range": [10.0, 12.0],
                "lateral_offset_range": [-0.5, 0.5],
                "half_width_range": [0.4, 0.6],
                "reveal_step": 3,
                "max_active_steps": 12,
                "finish_pass_distance": 1.0,
            }
        }
    )

    assert config.warmup_gate.enabled is True
    assert config.warmup_gate.distance_range == (10.0, 12.0)
    assert config.warmup_gate.lateral_offset_range == (-0.5, 0.5)
    assert config.warmup_gate.half_width_range == (0.4, 0.6)
    assert config.warmup_gate.reveal_step == 3
    assert config.warmup_gate.max_active_steps == 12
    assert config.warmup_gate.finish_pass_distance == 1.0


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


@pytest.mark.parametrize(
    "mode",
    [
        "front_rear_omega",
        "front_rear_omega_ground",
        "front_rear_omega_ground_error",
    ],
)
def test_local_wheel_ground_speed_profiles_keep_clean_slot_shape(mode):
    env = AutoDriftEnv(DriftEnvConfig(wheel_observation_mode=mode))
    obs, _ = env.reset(seed=25)

    assert obs.shape == (85,)
    wheel_features = obs[12:25]
    assert wheel_features.shape == (13,)
    assert np.isfinite(wheel_features).all()
    np.testing.assert_allclose(wheel_features[10:13], np.zeros(3, dtype=np.float32))

    next_obs, _, _, _, _ = env.step(np.array([0.3, 1.0, -1.0], dtype=np.float32))
    next_wheel_features = next_obs[12:25]

    assert next_obs.shape == (85,)
    assert np.isfinite(next_wheel_features).all()
    np.testing.assert_allclose(next_wheel_features[10:13], np.zeros(3, dtype=np.float32))


def test_local_wheel_ground_speed_profile_uses_bicycle_contact_speed_not_slip_ratio():
    env = AutoDriftEnv(DriftEnvConfig(wheel_observation_mode="front_rear_omega_ground_error"))
    env.reset(seed=26)
    env.state = VehicleState(x=0.0, y=0.0, psi=0.0, vx=10.0, vy=1.5, yaw_rate=0.4, steer=0.2)
    env.front_wheel_speed = 9.0
    env.rear_wheel_speed = 11.0
    env.last_front_wheel_speed = 9.0
    env.last_rear_wheel_speed = 11.0

    front_ground, rear_ground = env._front_rear_local_ground_speeds()
    wheel_features = np.asarray(env._wheel_response_features(ax_body=0.0), dtype=np.float32)

    expected_front_ground = 10.0 * np.cos(0.2) + (1.5 + 0.4 * env.params.lf) * np.sin(0.2)
    assert np.isclose(front_ground, expected_front_ground)
    assert np.isclose(rear_ground, 10.0)
    np.testing.assert_allclose(wheel_features[0:4], [9.0 / 20.0, 11.0 / 20.0, front_ground / 20.0, 0.5])
    np.testing.assert_allclose(
        wheel_features[4:7],
        [(9.0 - front_ground) / 20.0, (11.0 - rear_ground) / 20.0, 0.0],
    )
    np.testing.assert_allclose(wheel_features[10:13], np.zeros(3, dtype=np.float32))


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
    assert next_info["termination_reason"] == "obstacle_collision"
    assert next_info["completion_reason"] == "obstacle_collision"
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
    assert info["obstacle_passed_raw"] is True
    assert info["termination_reason"] == ""
    assert info["completion_reason"] == "obstacle_pass"
    assert info["reward_terms"]["pass_reward"] == 5.0
    assert reward > 0.0


def test_obstacle_pass_raw_can_continue_when_finish_on_pass_disabled():
    env = AutoDriftEnv(
        DriftEnvConfig(
            max_steps=20,
            obstacle=ObstacleTaskConfig(
                enabled=True,
                distance_range=(20.0, 20.0),
                half_width_range=(0.8, 0.8),
                finish_on_pass=False,
                finish_pass_distance=2.0,
                pass_reward=5.0,
            ),
        )
    )
    _, _ = env.reset(seed=33)
    frame = env.track.frame(env.state.x, env.state.y, env.state.psi)
    position = np.array([env.state.x, env.state.y], dtype=np.float64)
    env.obstacle_position = position - frame.tangent * 3.0
    env.collision = False
    env.min_obstacle_clearance = 3.0

    _, _, terminated, truncated, info = env.step(np.array([0.0, -1.0, -1.0], dtype=np.float32))

    assert terminated is False
    assert truncated is False
    assert info["obstacle_passed_raw"] is True
    assert info["obstacle_completed"] is False
    assert info["termination_reason"] == ""
    assert info["completion_reason"] == ""
    assert "pass_reward" not in info["reward_terms"]


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
    assert penalty_info["termination_reason"] == "off_track"


def test_termination_reason_reports_each_failure_mode_without_changing_observation_shape():
    env = AutoDriftEnv(DriftEnvConfig(track_width=1.0))
    obs, _ = env.reset(seed=94)
    assert obs.shape == env.observation_space.shape

    frame = env.track.frame(env.state.x, env.state.y, env.state.psi)
    env.state.vx = float("nan")
    assert env._termination_reason(frame) == "non_finite_state"

    env.reset(seed=94)
    env.state.x = env.config.track_radius + 3.0
    frame = env.track.frame(env.state.x, env.state.y, env.state.psi)
    assert env._termination_reason(frame) == "off_track"

    env.reset(seed=94)
    frame = env.track.frame(env.state.x, env.state.y, env.state.psi)
    env.collision = True
    assert env._termination_reason(frame) == "obstacle_collision"

    env.reset(seed=94)
    frame = env.track.frame(env.state.x, env.state.y, env.state.psi)
    env.state.vx = 0.1
    env.state.vy = 0.0
    assert env._termination_reason(frame) == "speed_too_low"

    env.reset(seed=94)
    frame = env.track.frame(env.state.x, env.state.y, env.state.psi)
    env.state.vx = 33.0
    env.state.vy = 0.0
    assert env._termination_reason(frame) == "speed_too_high"

    env.reset(seed=94)
    frame = env.track.frame(env.state.x, env.state.y, env.state.psi)
    env.state.yaw_rate = 6.1
    assert env._termination_reason(frame) == "yaw_rate_limit"


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
