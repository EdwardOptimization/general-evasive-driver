from autodrift.config import build_curriculum, build_env_config, env_config_for_step


def test_build_env_config_overrides_nested_randomization():
    config = build_env_config(
        {
            "track_kind": "figure_eight",
            "track_width": 7.0,
            "speed_range": [5.0, 8.0],
            "randomization": {"mu_range": [0.6, 1.0]},
        }
    )

    assert config.track_kind == "figure_eight"
    assert config.track_width == 7.0
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
