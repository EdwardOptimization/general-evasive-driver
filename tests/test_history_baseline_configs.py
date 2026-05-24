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

L3_REPAIR_4096_CONFIGS = {
    "fast_select": Path("configs/ppo_m546_l3_repair_fast_select_4096.json"),
    "lr1e4": Path("configs/ppo_m546_l3_repair_lr1e4_4096.json"),
    "lr5e5": Path("configs/ppo_m546_l3_repair_lr5e5_4096.json"),
}

L3_UPDATE_ALIGNED_REPAIR_4096_CONFIGS = {
    "fast_select": Path("configs/ppo_m548_l3_repair_fast_select_ckpt256_4096.json"),
    "lr1e4": Path("configs/ppo_m548_l3_repair_lr1e4_ckpt256_4096.json"),
    "lr5e5": Path("configs/ppo_m548_l3_repair_lr5e5_ckpt256_4096.json"),
}

L3_REPAIR_V2_4096_CONFIGS = {
    "epoch1_clip01": Path("configs/ppo_m555_l3_repair_epoch1_clip01_4096.json"),
    "longseq_epoch1": Path("configs/ppo_m555_l3_repair_longseq_epoch1_4096.json"),
    "lowentropy_epoch1": Path("configs/ppo_m555_l3_repair_lowentropy_epoch1_4096.json"),
}

L3_COLLISION_MARGIN_REPAIR_4096_CONFIGS = {
    "collision35_dense002": Path("configs/ppo_m559_l3_collision35_dense002_4096.json"),
    "collision35_terminal4": Path("configs/ppo_m559_l3_collision35_terminal4_4096.json"),
    "collision45_terminal4": Path("configs/ppo_m559_l3_collision45_terminal4_4096.json"),
}


def _assert_history_baseline_config(
    *,
    config: dict,
    level: str,
    total_steps: int,
    seed: int,
    learning_rate: float = 0.0003,
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
    assert ppo["learning_rate"] == learning_rate
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


@pytest.mark.parametrize("variant,path", sorted(L3_REPAIR_4096_CONFIGS.items()))
def test_m546_l3_repair_configs_preserve_p0_l3_contract(variant: str, path: Path) -> None:
    expected_learning_rates = {
        "fast_select": 0.0003,
        "lr1e4": 0.0001,
        "lr5e5": 0.00005,
    }
    config = read_json(path)
    _assert_history_baseline_config(
        config=config,
        level="L3_online_gru",
        total_steps=4096,
        seed=3540,
        learning_rate=expected_learning_rates[variant],
    )
    assert config["ppo"]["recurrent_sequence_training"] is True
    assert config["ppo"]["checkpoint_interval_steps"] == 512


def test_m546_l3_repair_configs_preserve_m541_l3_env_distribution() -> None:
    base = read_json(MATCHED_VARIANCE_4096_CONFIGS["L3_online_gru"])
    for path in L3_REPAIR_4096_CONFIGS.values():
        repair = read_json(path)
        assert repair["env"] == base["env"]


def test_m546_l3_repair_configs_only_change_approved_optimization_controls() -> None:
    base = read_json(MATCHED_VARIANCE_4096_CONFIGS["L3_online_gru"])
    allowed_differences = {
        "checkpoint_interval_steps",
        "learning_rate",
        "max_grad_norm",
    }
    expected = {
        "fast_select": {"learning_rate": 0.0003, "checkpoint_interval_steps": 512},
        "lr1e4": {"learning_rate": 0.0001, "max_grad_norm": 0.25, "checkpoint_interval_steps": 512},
        "lr5e5": {"learning_rate": 0.00005, "max_grad_norm": 0.25, "checkpoint_interval_steps": 512},
    }

    for variant, path in L3_REPAIR_4096_CONFIGS.items():
        repair = read_json(path)
        base_ppo = dict(base["ppo"])
        repair_ppo = dict(repair["ppo"])
        differences = {
            key
            for key in sorted(set(base_ppo) | set(repair_ppo))
            if base_ppo.get(key) != repair_ppo.get(key)
        }
        assert differences <= allowed_differences
        for key, value in expected[variant].items():
            assert repair_ppo[key] == value


@pytest.mark.parametrize("variant,path", sorted(L3_UPDATE_ALIGNED_REPAIR_4096_CONFIGS.items()))
def test_m548_update_aligned_configs_preserve_p0_l3_contract(variant: str, path: Path) -> None:
    expected_learning_rates = {
        "fast_select": 0.0003,
        "lr1e4": 0.0001,
        "lr5e5": 0.00005,
    }
    config = read_json(path)
    _assert_history_baseline_config(
        config=config,
        level="L3_online_gru",
        total_steps=4096,
        seed=3540,
        learning_rate=expected_learning_rates[variant],
    )
    assert config["ppo"]["recurrent_sequence_training"] is True
    assert config["ppo"]["checkpoint_interval_steps"] == 256


def test_m548_update_aligned_configs_preserve_m546_env_distribution() -> None:
    for variant, path in L3_UPDATE_ALIGNED_REPAIR_4096_CONFIGS.items():
        parent = read_json(L3_REPAIR_4096_CONFIGS[variant])
        repair = read_json(path)
        assert repair["env"] == parent["env"]


def test_m548_update_aligned_configs_only_change_checkpoint_cadence_from_m546() -> None:
    for variant, path in L3_UPDATE_ALIGNED_REPAIR_4096_CONFIGS.items():
        parent = read_json(L3_REPAIR_4096_CONFIGS[variant])
        repair = read_json(path)
        parent_ppo = dict(parent["ppo"])
        repair_ppo = dict(repair["ppo"])

        assert parent_ppo.pop("checkpoint_interval_steps") == 512
        assert repair_ppo.pop("checkpoint_interval_steps") == 256
        assert repair_ppo == parent_ppo


@pytest.mark.parametrize("variant,path", sorted(L3_REPAIR_V2_4096_CONFIGS.items()))
def test_m555_l3_repair_v2_configs_preserve_p0_l3_contract(variant: str, path: Path) -> None:
    del variant
    config = read_json(path)
    ppo = config["ppo"]
    env_config = build_env_config(config["env"])
    spec = build_history_baseline_spec(
        level=ppo["history_baseline_level"],
        actor_encoder=ppo["actor_encoder"],
        actor_history_length=ppo["actor_history_length"],
        env_config=env_config,
    )

    assert spec.level == "L3_online_gru"
    assert spec.input_contract == "P0_human_view_no_wheel_no_oracle"
    assert ppo["actor_encoder"] == "human_view_online_gru"
    assert ppo["actor_history_length"] == 1
    assert ppo["history_baseline_level"] == "L3_online_gru"
    assert ppo["recurrent_sequence_training"] is True
    assert ppo["total_steps"] == 4096
    assert ppo["num_envs"] == 4
    assert ppo["hidden_size"] == 64
    assert ppo["checkpoint_interval_steps"] == 256
    assert ppo["eval_episodes"] == 5
    assert ppo["seed"] == 3540
    assert config["env"]["history_length"] == 1
    assert config["env"]["action_history_mode"] == "full"
    assert config["env"].get("wheel_observation_mode", "none") == "none"


def test_m555_l3_repair_v2_configs_preserve_m548_l3_env_distribution() -> None:
    base = read_json(L3_UPDATE_ALIGNED_REPAIR_4096_CONFIGS["fast_select"])
    for path in L3_REPAIR_V2_4096_CONFIGS.values():
        repair = read_json(path)
        assert repair["env"] == base["env"]


def test_m555_l3_repair_v2_configs_only_change_m554_approved_ppo_controls() -> None:
    base = read_json(L3_UPDATE_ALIGNED_REPAIR_4096_CONFIGS["fast_select"])
    allowed_differences = {
        "clip_coef",
        "ent_coef",
        "freeze_log_std",
        "learning_rate",
        "log_std_init",
        "max_grad_norm",
        "minibatch_size",
        "rollout_steps",
        "update_epochs",
    }
    expected = {
        "epoch1_clip01": {
            "learning_rate": 0.0001,
            "update_epochs": 1,
            "clip_coef": 0.10,
            "max_grad_norm": 0.25,
        },
        "longseq_epoch1": {
            "rollout_steps": 128,
            "minibatch_size": 128,
            "learning_rate": 0.0001,
            "update_epochs": 1,
            "clip_coef": 0.10,
            "max_grad_norm": 0.25,
        },
        "lowentropy_epoch1": {
            "learning_rate": 0.0001,
            "update_epochs": 1,
            "clip_coef": 0.10,
            "ent_coef": 0.0005,
            "max_grad_norm": 0.25,
            "freeze_log_std": True,
            "log_std_init": -1.25,
        },
    }

    assert set(L3_REPAIR_V2_4096_CONFIGS) == set(expected)
    for variant, path in L3_REPAIR_V2_4096_CONFIGS.items():
        repair = read_json(path)
        base_ppo = dict(base["ppo"])
        repair_ppo = dict(repair["ppo"])
        differences = {
            key
            for key in sorted(set(base_ppo) | set(repair_ppo))
            if base_ppo.get(key) != repair_ppo.get(key)
        }
        assert differences <= allowed_differences
        for key, value in expected[variant].items():
            assert repair_ppo[key] == value


@pytest.mark.parametrize("variant,path", sorted(L3_COLLISION_MARGIN_REPAIR_4096_CONFIGS.items()))
def test_m559_collision_margin_configs_preserve_p0_l3_contract(variant: str, path: Path) -> None:
    del variant
    config = read_json(path)
    ppo = config["ppo"]
    env_config = build_env_config(config["env"])
    spec = build_history_baseline_spec(
        level=ppo["history_baseline_level"],
        actor_encoder=ppo["actor_encoder"],
        actor_history_length=ppo["actor_history_length"],
        env_config=env_config,
    )

    assert spec.level == "L3_online_gru"
    assert spec.input_contract == "P0_human_view_no_wheel_no_oracle"
    assert ppo == read_json(L3_REPAIR_V2_4096_CONFIGS["epoch1_clip01"])["ppo"]
    assert config["env"]["history_length"] == 1
    assert config["env"].get("wheel_observation_mode", "none") == "none"


def test_m559_collision_margin_configs_only_change_m558_approved_obstacle_reward_fields() -> None:
    base = read_json(L3_REPAIR_V2_4096_CONFIGS["epoch1_clip01"])
    allowed_obstacle_differences = {
        "clearance_margin_reward_clip",
        "clearance_margin_reward_scale",
        "collision_penalty",
        "dense_clearance_margin_reward_clip",
        "dense_clearance_margin_reward_scale",
        "dense_clearance_margin_reward_window",
    }
    expected = {
        "collision35_terminal4": {
            "collision_penalty": 35.0,
            "clearance_margin_reward_scale": 4.0,
            "clearance_margin_reward_clip": 0.50,
        },
        "collision35_dense002": {
            "collision_penalty": 35.0,
            "clearance_margin_reward_scale": 4.0,
            "clearance_margin_reward_clip": 0.50,
            "dense_clearance_margin_reward_scale": 0.02,
            "dense_clearance_margin_reward_clip": 0.50,
            "dense_clearance_margin_reward_window": 8.0,
        },
        "collision45_terminal4": {
            "collision_penalty": 45.0,
            "clearance_margin_reward_scale": 4.0,
            "clearance_margin_reward_clip": 0.50,
        },
    }

    assert set(L3_COLLISION_MARGIN_REPAIR_4096_CONFIGS) == set(expected)
    for variant, path in L3_COLLISION_MARGIN_REPAIR_4096_CONFIGS.items():
        repair = read_json(path)
        assert repair["ppo"] == base["ppo"]

        base_env = dict(base["env"])
        repair_env = dict(repair["env"])
        base_obstacle = dict(base_env.pop("obstacle"))
        repair_obstacle = dict(repair_env.pop("obstacle"))
        assert repair_env == base_env

        differences = {
            key
            for key in sorted(set(base_obstacle) | set(repair_obstacle))
            if base_obstacle.get(key) != repair_obstacle.get(key)
        }
        assert differences <= allowed_obstacle_differences
        for key, value in expected[variant].items():
            assert repair_obstacle[key] == value
