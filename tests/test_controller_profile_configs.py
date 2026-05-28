from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.config import build_env_config
from autodrift.controller_profile_configs import (
    build_all_profile_configs,
    config_filename,
    write_generated_configs,
)
from autodrift.controller_profiles import FINITE_WINDOW_STEPS, all_profiles, get_profile
from autodrift.env import AutoDriftEnv


def test_build_all_profile_configs_generates_all_profiles() -> None:
    configs = build_all_profile_configs()
    assert set(configs) == {profile.name for profile in all_profiles()}
    assert len(configs) == 8


def test_l0_config_contains_runtime_mask_metadata() -> None:
    config = build_all_profile_configs()["L0_current_masked"]
    profile = config["controller_profile"]

    assert profile["observation_mask"] == "zero_previous_command_fields"
    assert profile["previous_command_mask_indices"] == [9, 10, 11]
    assert profile["uses_hidden_oracle_actor_inputs"] is False
    assert config["ppo"]["actor_encoder"] == "mlp"
    assert config["env"]["history_length"] == 1


def test_l2_configs_cover_finite_windows() -> None:
    configs = build_all_profile_configs()
    for steps in FINITE_WINDOW_STEPS:
        config = configs[f"L2_window_{steps}"]
        assert config["env"]["history_length"] == steps
        assert config["ppo"]["actor_encoder"] == "temporal_gru"
        assert config["ppo"]["actor_history_length"] == steps
        assert config["ppo"]["history_baseline_level"] == "L2_finite_window"


def test_l3_reset_control_is_not_training_enabled() -> None:
    config = build_all_profile_configs()["L3_reset_control"]
    assert config["controller_profile"]["training_enabled"] is False
    assert config["controller_profile"]["reset_hidden_policy"] == "every_step_control"
    assert config["ppo"]["actor_encoder"] == "human_view_online_gru"
    assert config["ppo"]["recurrent_sequence_training"] is False


def test_generated_env_configs_are_no_oracle_human_view() -> None:
    for name, config in build_all_profile_configs().items():
        profile = get_profile(name)
        env_config = build_env_config(config["env"])
        env = AutoDriftEnv(env_config)

        assert env.observation_space.shape == (profile.observation_dim,)
        assert env_config.include_privileged_params is False
        assert env_config.wheel_observation_mode == "none"
        assert env_config.action_history_mode == "full"
        assert env_config.obstacle_relative_velocity_mode == "zero"
        assert env_config.road_lookahead_count == 8
        assert env_config.obstacle_slots == 4


def test_write_generated_configs_outputs_json_and_summary(tmp_path: Path) -> None:
    output_dir = tmp_path / "configs"
    run_dir = tmp_path / "run"
    summary = write_generated_configs(output_dir=output_dir, run_dir=run_dir)

    assert summary["generated_config_count"] == 8
    assert summary["training_started"] is False
    assert summary["ppo_used"] is False
    assert summary["private_holdout_used"] is False

    for profile in all_profiles():
        path = output_dir / config_filename(profile)
        assert path.exists()
        config = read_json(path)
        assert config["controller_profile"]["name"] == profile.name

    persisted_summary = read_json(run_dir / "summary.json")
    assert persisted_summary == summary
    assert (run_dir / "config_rows.csv").exists()
