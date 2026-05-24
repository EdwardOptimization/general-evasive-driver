from pathlib import Path

import pytest

from autodrift.artifacts import read_json
from autodrift.config import build_env_config
from autodrift.history_baselines import build_history_baseline_spec


MATCHED_SHORT_TRAIN_CONFIGS = {
    "L0_current_observation": Path("configs/ppo_m531_matched_l0_short_train.json"),
    "L2_finite_window": Path("configs/ppo_m531_matched_l2_short_train.json"),
    "L3_online_gru": Path("configs/ppo_m531_matched_l3_short_train.json"),
}

MATCHED_VARIANCE_4096_CONFIGS = {
    "L0_current_observation": Path("configs/ppo_m541_matched_l0_variance_4096.json"),
    "L2_finite_window": Path("configs/ppo_m541_matched_l2_variance_4096.json"),
    "L3_online_gru": Path("configs/ppo_m541_matched_l3_variance_4096.json"),
}


def _assert_history_baseline_config(
    *,
    config: dict,
    level: str,
    total_steps: int,
    seed: int,
) -> None:
    ppo = config["ppo"]
    env_config = build_env_config(config["env"])

    spec = build_history_baseline_spec(
        level=ppo["history_baseline_level"],
        actor_encoder=ppo["actor_encoder"],
        actor_history_length=ppo["actor_history_length"],
        env_config=env_config,
    )

    assert spec.level == level
    assert spec.input_contract == "P0_human_view_no_wheel_no_oracle"
    assert ppo["total_steps"] == total_steps
    assert ppo["rollout_steps"] == 64
    assert ppo["num_envs"] == 4
    assert ppo["update_epochs"] == 2
    assert ppo["minibatch_size"] == 128
    assert ppo["hidden_size"] == 64
    assert ppo["learning_rate"] == 0.0003
    assert ppo["eval_episodes"] == 5
    assert ppo["seed"] == seed
    assert config["env"]["action_history_mode"] == "full"
    assert config["env"].get("wheel_observation_mode", "none") == "none"


def _assert_shared_task_distribution_except_history_length(configs: dict[str, dict]) -> None:
    l0_env = dict(configs["L0_current_observation"]["env"])
    l2_env = dict(configs["L2_finite_window"]["env"])
    l3_env = dict(configs["L3_online_gru"]["env"])

    assert l0_env.pop("history_length") == 1
    assert l2_env.pop("history_length") == 4
    assert l3_env.pop("history_length") == 1
    assert l0_env == l2_env == l3_env


@pytest.mark.parametrize("level,path", sorted(MATCHED_SHORT_TRAIN_CONFIGS.items()))
def test_m531_matched_short_train_configs_declare_valid_history_baseline(level: str, path: Path) -> None:
    config = read_json(path)
    _assert_history_baseline_config(config=config, level=level, total_steps=1024, seed=3530)


def test_m531_matched_short_train_configs_share_task_distribution_except_history_length() -> None:
    configs = {level: read_json(path) for level, path in MATCHED_SHORT_TRAIN_CONFIGS.items()}
    _assert_shared_task_distribution_except_history_length(configs)


@pytest.mark.parametrize("level,path", sorted(MATCHED_VARIANCE_4096_CONFIGS.items()))
def test_m541_matched_variance_configs_declare_valid_history_baseline(level: str, path: Path) -> None:
    config = read_json(path)
    _assert_history_baseline_config(config=config, level=level, total_steps=4096, seed=3540)


def test_m541_matched_variance_configs_share_task_distribution_except_history_length() -> None:
    configs = {level: read_json(path) for level, path in MATCHED_VARIANCE_4096_CONFIGS.items()}
    _assert_shared_task_distribution_except_history_length(configs)


def test_m541_variance_configs_only_change_budget_and_seed_from_m531() -> None:
    for level in MATCHED_SHORT_TRAIN_CONFIGS:
        short_config = read_json(MATCHED_SHORT_TRAIN_CONFIGS[level])
        variance_config = read_json(MATCHED_VARIANCE_4096_CONFIGS[level])

        short_ppo = dict(short_config["ppo"])
        variance_ppo = dict(variance_config["ppo"])
        assert short_ppo.pop("total_steps") == 1024
        assert variance_ppo.pop("total_steps") == 4096
        assert short_ppo.pop("seed") == 3530
        assert variance_ppo.pop("seed") == 3540
        assert short_ppo == variance_ppo
        assert short_config["env"] == variance_config["env"]
