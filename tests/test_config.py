from autodrift.config import build_curriculum, build_env_config, env_config_for_step
from autodrift.evaluate import load_env_config


def test_build_env_config_overrides_nested_randomization():
    config = build_env_config(
        {
            "track_kind": "figure_eight",
            "track_width": 7.0,
            "termination_penalty": 8.0,
            "speed_range": [5.0, 8.0],
            "randomization": {"mu_range": [0.6, 1.0]},
        }
    )

    assert config.track_kind == "figure_eight"
    assert config.track_width == 7.0
    assert config.termination_penalty == 8.0
    assert config.speed_range == (5.0, 8.0)
    assert config.randomization.mu_range == (0.6, 1.0)


def test_build_env_config_overrides_friction_step():
    config = build_env_config(
        {
            "friction_step": {
                "enabled": True,
                "step_range": [20, 40],
                "mu_range": [0.3, 0.6],
                "resample_speed_ref": False,
            }
        }
    )

    assert config.friction_step.enabled is True
    assert config.friction_step.step_range == (20, 40)
    assert config.friction_step.mu_range == (0.3, 0.6)
    assert config.friction_step.resample_speed_ref is False


def test_build_env_config_overrides_obstacle_task():
    config = build_env_config(
        {
            "obstacle": {
                "enabled": True,
                "distance_range": [20.0, 30.0],
                "half_width_range": [0.6, 1.0],
                "collision_penalty": 12.0,
                "require_aeb_infeasible": True,
                "finish_on_pass": True,
                "pass_reward": 6.0,
                "allowed_labels": ["aes_feasible", "drift_required"],
                "stable_aes_beta_limit": 0.18,
                "stable_aes_sideslip_penalty": 2.5,
                "stable_aes_drift_bonus_scale": 0.25,
                "max_threshold_score": 0.05,
                "min_time_after_friction_step": 0.10,
                "perception_reveal_step": 12,
                "perception_reveal_distance": 18.0,
                "clearance_margin_reward_scale": 1.5,
                "clearance_margin_reward_clip": 0.20,
                "dense_clearance_margin_reward_scale": 0.05,
                "dense_clearance_margin_reward_clip": 0.30,
                "dense_clearance_margin_reward_window": 6.0,
                "motion_mode": "constant_velocity_crosser",
                "crosser_lateral_velocity_range": [-3.0, 3.0],
            }
        }
    )

    assert config.obstacle.enabled is True
    assert config.obstacle.distance_range == (20.0, 30.0)
    assert config.obstacle.half_width_range == (0.6, 1.0)
    assert config.obstacle.collision_penalty == 12.0
    assert config.obstacle.require_aeb_infeasible is True
    assert config.obstacle.finish_on_pass is True
    assert config.obstacle.pass_reward == 6.0
    assert config.obstacle.allowed_labels == ("aes_feasible", "drift_required")
    assert config.obstacle.stable_aes_beta_limit == 0.18
    assert config.obstacle.stable_aes_sideslip_penalty == 2.5
    assert config.obstacle.stable_aes_drift_bonus_scale == 0.25
    assert config.obstacle.max_threshold_score == 0.05
    assert config.obstacle.min_time_after_friction_step == 0.10
    assert config.obstacle.perception_reveal_step == 12
    assert config.obstacle.perception_reveal_distance == 18.0
    assert config.obstacle.clearance_margin_reward_scale == 1.5
    assert config.obstacle.clearance_margin_reward_clip == 0.20
    assert config.obstacle.dense_clearance_margin_reward_scale == 0.05
    assert config.obstacle.dense_clearance_margin_reward_clip == 0.30
    assert config.obstacle.dense_clearance_margin_reward_window == 6.0
    assert config.obstacle.motion_mode == "constant_velocity_crosser"
    assert config.obstacle.crosser_lateral_velocity_range == (-3.0, 3.0)


def test_build_env_config_overrides_action_history_mode():
    config = build_env_config({"action_history_mode": "full", "history_length": 3})

    assert config.action_history_mode == "full"
    assert config.history_length == 3


def test_build_env_config_overrides_observation_scale_and_high_speed_limit():
    config = build_env_config(
        {
            "max_speed_limit": 45.0,
            "observation_scale": {
                "ego_vx": 40.0,
                "ego_vy": 40.0,
                "ego_ax": 50.0,
                "ego_ay": 60.0,
                "road_y": 60.0,
                "obstacle_rel_vy": 30.0,
                "road_lookahead_time_s": 2.5,
                "road_lookahead_max_distance": 120.0,
            },
        }
    )

    assert config.max_speed_limit == 45.0
    assert config.observation_scale.ego_vx == 40.0
    assert config.observation_scale.ego_vy == 40.0
    assert config.observation_scale.ego_ax == 50.0
    assert config.observation_scale.ego_ay == 60.0
    assert config.observation_scale.road_y == 60.0
    assert config.observation_scale.obstacle_rel_vy == 30.0
    assert config.observation_scale.road_lookahead_time_s == 2.5
    assert config.observation_scale.road_lookahead_max_distance == 120.0


def test_build_env_config_rejects_unknown_observation_scale_key():
    try:
        build_env_config({"observation_scale": {"ego_speed": 40.0}})
    except ValueError as exc:
        assert "observation_scale" in str(exc)
    else:
        raise AssertionError("unknown observation_scale key should be rejected")


def test_build_env_config_rejects_legacy_action_history_mode():
    try:
        build_env_config({"action_history_mode": "legacy"})
    except ValueError as exc:
        assert "action_history_mode" in str(exc)
    else:
        raise AssertionError("legacy action history mode should be rejected")


def test_load_env_config_requires_explicit_env_section(tmp_path):
    path = tmp_path / "raw-env.json"
    path.write_text('{"track_width": 7.0}', encoding="utf-8")

    try:
        load_env_config(path)
    except ValueError as exc:
        assert "top-level 'env'" in str(exc)
    else:
        raise AssertionError("raw env-root config should be rejected")


def test_curriculum_selects_stage_before_base():
    base_data = {"track_width": 5.0, "randomization": {"mu_range": [0.25, 1.15]}}
    base_config = build_env_config(base_data)
    curriculum = build_curriculum(
        base_data,
        [{"name": "easy", "until_step": 100, "env": {"track_width": 8.0}}],
    )

    early_config, early_name = env_config_for_step(base_config, curriculum, 50)
    late_config, late_name = env_config_for_step(base_config, curriculum, 100)

    assert early_name == "easy"
    assert early_config.track_width == 8.0
    assert late_name == "base"
    assert late_config.track_width == 5.0
