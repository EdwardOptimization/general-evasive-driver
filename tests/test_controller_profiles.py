from pathlib import Path

import numpy as np

from autodrift.artifacts import read_json
from autodrift.controller_profiles import (
    FINITE_WINDOW_STEPS,
    HUMAN_VIEW_OBS_DIM,
    PREVIOUS_COMMAND_INDICES,
    ZERO_PREVIOUS_COMMANDS,
    all_profiles,
    apply_observation_mask,
    get_profile,
    profile_contract,
    profile_env_config,
    profile_ppo_overrides,
    profile_summary,
    profile_to_row,
    write_profile_smoke,
)
from autodrift.env import AutoDriftEnv
from autodrift.train_ppo import ActorCritic


def test_profile_names_cover_l0_l1_l2_l3() -> None:
    names = {profile.name for profile in all_profiles()}
    assert "L0_current_masked" in names
    assert "L1_one_step" in names
    assert "L3_online_gru" in names
    assert "L3_reset_control" in names
    for steps in FINITE_WINDOW_STEPS:
        assert f"L2_window_{steps}" in names


def test_l0_masks_previous_command_fields_only() -> None:
    profile = get_profile("L0_current_masked")
    assert profile.observation_mask == ZERO_PREVIOUS_COMMANDS
    assert profile.previous_command_mask_indices == PREVIOUS_COMMAND_INDICES

    obs = np.arange(HUMAN_VIEW_OBS_DIM, dtype=np.float32)
    masked = apply_observation_mask(profile, obs)

    for index in PREVIOUS_COMMAND_INDICES:
        assert masked[index] == 0.0
    assert masked[0] == obs[0]
    assert masked[8] == obs[8]
    assert masked[12] == obs[12]


def test_profile_envs_are_canonical_no_oracle_human_view() -> None:
    for profile in all_profiles():
        env_config = profile_env_config(profile)
        env = AutoDriftEnv(env_config)
        assert env.observation_space.shape == (profile.observation_dim,)
        assert env_config.action_history_mode == "full"
        assert env_config.include_privileged_params is False
        assert env_config.wheel_observation_mode == "none"
        assert env_config.road_lookahead_count == 8
        assert env_config.obstacle_slots == 4
        assert env_config.obstacle_relative_velocity_mode == "zero"


def test_profile_actorcritic_instantiation_without_training() -> None:
    profiles = [
        get_profile("L0_current_masked"),
        get_profile("L1_one_step"),
        get_profile("L2_window_13"),
        get_profile("L2_window_100"),
        get_profile("L3_online_gru"),
        get_profile("L3_reset_control"),
    ]
    for profile in profiles:
        model = ActorCritic(
            obs_dim=profile.observation_dim,
            act_dim=3,
            hidden_size=16,
            actor_encoder=profile.actor_encoder,
            actor_history_length=profile.actor_history_length,
        )
        assert model.actor_encoder == profile.actor_encoder


def test_profile_ppo_overrides_are_contract_clean() -> None:
    l2 = get_profile("L2_window_25")
    l2_overrides = profile_ppo_overrides(l2)
    assert l2_overrides["actor_encoder"] == "temporal_gru"
    assert l2_overrides["actor_history_length"] == 25
    assert l2_overrides["history_baseline_level"] == "L2_finite_window"
    assert l2_overrides["recurrent_sequence_training"] is False

    l3 = get_profile("L3_online_gru")
    l3_overrides = profile_ppo_overrides(l3)
    assert l3_overrides["actor_encoder"] == "human_view_online_gru"
    assert l3_overrides["history_baseline_level"] == "L3_online_gru"
    assert l3_overrides["recurrent_sequence_training"] is True


def test_profile_contracts_forbid_oracle_inputs() -> None:
    for profile in all_profiles():
        contract = profile_contract(profile)
        row = profile_to_row(profile)
        assert contract["uses_hidden_oracle_actor_inputs"] is False
        assert contract["uses_wheel_or_slip_inputs"] is False
        assert contract["uses_reference_or_ttc_inputs"] is False
        assert row["uses_hidden_oracle_actor_inputs"] is False
        assert "hidden_physical_params" in row["forbidden_inputs"]
        assert "wheel_or_slip_observations" in row["forbidden_inputs"]
        assert "ttc_required_clearance_or_stopping_distance" in row["forbidden_inputs"]


def test_write_profile_smoke(tmp_path: Path) -> None:
    write_profile_smoke(tmp_path)
    summary = read_json(tmp_path / "summary.json")
    rows = (tmp_path / "profile_rows.csv").read_text(encoding="utf-8").splitlines()

    assert summary == profile_summary()
    assert summary["training_started"] is False
    assert summary["ppo_used"] is False
    assert summary["private_holdout_used"] is False
    assert len(rows) == len(all_profiles()) + 1
