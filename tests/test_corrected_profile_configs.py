from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.config import build_env_config
from autodrift.controller_profile_runtime import CURRENT_TILED_HISTORY, mask_spec_from_config
from autodrift.corrected_profile_configs import (
    build_corrected_profile_configs,
    write_corrected_profile_configs,
)
from autodrift.env import AutoDriftEnv


def test_corrected_profile_configs_cover_expected_profiles() -> None:
    configs = build_corrected_profile_configs()
    assert set(configs) == {
        "L0_current_masked",
        "L1_one_step",
        "L2_window_13",
        "L2_window_13_current_tiled",
        "L2_window_25",
        "L2_window_25_current_tiled",
        "L3_online_gru",
        "L3_reset_control_corrected",
    }


def test_current_tiled_l2_configs_preserve_capacity_contract() -> None:
    configs = build_corrected_profile_configs()
    for tiled_name, source_name in [
        ("L2_window_13_current_tiled", "L2_window_13"),
        ("L2_window_25_current_tiled", "L2_window_25"),
    ]:
        tiled = configs[tiled_name]
        source = configs[source_name]
        assert tiled["env"] == source["env"]
        assert tiled["ppo"]["actor_encoder"] == source["ppo"]["actor_encoder"] == "temporal_gru"
        assert tiled["ppo"]["actor_history_length"] == source["ppo"]["actor_history_length"]
        assert tiled["ppo"]["hidden_size"] == source["ppo"]["hidden_size"]
        assert tiled["controller_profile"]["observation_dim"] == source["controller_profile"]["observation_dim"]
        assert tiled["controller_profile"]["history_transform"] == CURRENT_TILED_HISTORY
        assert tiled["controller_profile"]["current_tiled_history_control"] is True
        assert tiled["controller_profile"]["uses_hidden_oracle_actor_inputs"] is False
        assert tiled["controller_profile"]["uses_wheel_or_slip_inputs"] is False
        assert mask_spec_from_config(tiled).history_transform == CURRENT_TILED_HISTORY


def test_corrected_reset_control_config_expresses_eval_semantics() -> None:
    config = build_corrected_profile_configs()["L3_reset_control_corrected"]
    profile = config["controller_profile"]
    assert profile["source_profile_name"] == "L3_reset_control"
    assert profile["reset_hidden_policy"] == "every_step_control"
    assert profile["corrected_reset_control"] is True
    assert profile["eval_reset_hidden_policy_enforced"] is True
    assert profile["training_enabled"] is True
    assert config["ppo"]["actor_encoder"] == "human_view_online_gru"
    assert config["ppo"]["recurrent_sequence_training"] is False
    assert mask_spec_from_config(config).reset_hidden_policy == "every_step_control"


def test_corrected_configs_keep_no_oracle_human_view_env_contract() -> None:
    for config in build_corrected_profile_configs().values():
        env_config = build_env_config(config["env"])
        env = AutoDriftEnv(env_config)
        assert env.observation_space.shape == (config["controller_profile"]["observation_dim"],)
        assert env_config.include_privileged_params is False
        assert env_config.wheel_observation_mode == "none"
        assert env_config.action_history_mode == "full"
        assert env_config.obstacle_relative_velocity_mode == "zero"
        assert env_config.road_lookahead_count == 8
        assert env_config.obstacle_slots == 4


def test_write_corrected_profile_configs_outputs_json_summary_and_rows(tmp_path: Path) -> None:
    output_dir = tmp_path / "configs"
    run_dir = tmp_path / "run"
    summary = write_corrected_profile_configs(output_dir=output_dir, run_dir=run_dir)

    assert summary["result_class"] == "corrected_profile_configs_generated"
    assert summary["generated_config_count"] == 8
    assert summary["current_tiled_profiles"] == ["L2_window_13_current_tiled", "L2_window_25_current_tiled"]
    assert summary["corrected_reset_profiles"] == ["L3_reset_control_corrected"]
    assert summary["training_started"] is False
    assert summary["ppo_used"] is False
    assert summary["private_holdout_used"] is False

    expected = {
        "m1207_l0_current_masked.json",
        "m1207_l1_one_step.json",
        "m1207_l2_window_13.json",
        "m1207_l2_window_13_current_tiled.json",
        "m1207_l2_window_25.json",
        "m1207_l2_window_25_current_tiled.json",
        "m1207_l3_online_gru.json",
        "m1207_l3_reset_control_corrected.json",
    }
    assert {path.name for path in output_dir.glob("*.json")} == expected
    assert read_json(run_dir / "summary.json") == summary
    assert (run_dir / "config_rows.csv").exists()
