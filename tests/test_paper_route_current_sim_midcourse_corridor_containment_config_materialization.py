from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_json
from autodrift.paper_route_current_sim_midcourse_corridor_containment_config_materialization import (
    build_containment_config,
    materialize_containment_configs,
)
from autodrift.paper_route_current_sim_training_stability_repair_execution import EXPECTED_PROFILES, EXPECTED_SEED_IDS


def _source_configs(tmp_path: Path) -> Path:
    source_root = tmp_path / "source"
    for profile_name in EXPECTED_PROFILES:
        for seed_id in EXPECTED_SEED_IDS:
            source_path = source_root / profile_name / f"seed_{int(seed_id)}" / "config.json"
            source_path.parent.mkdir(parents=True, exist_ok=True)
            write_json(
                source_path,
                {
                    "controller_profile": {
                        "actor_encoder": "online_gru" if profile_name == "L3_online_gru" else "mlp",
                        "actor_history_length": 1,
                        "env_history_length": 1,
                        "input_contract": "P0_human_view_no_wheel_no_oracle",
                        "observation_dim": 72,
                        "uses_hidden_oracle_actor_inputs": False,
                        "uses_wheel_or_slip_inputs": False,
                        "uses_reference_or_ttc_inputs": False,
                    },
                    "env": {
                        "history_length": 1,
                        "include_privileged_params": False,
                        "wheel_observation_mode": "none",
                        "obstacle_relative_velocity_mode": "zero",
                        "track_width": 8.5,
                        "obstacle": {
                            "enabled": True,
                            "collision_penalty": 25.0,
                            "clearance_margin_reward_scale": 0.0,
                            "clearance_margin_reward_clip": 0.25,
                            "dense_clearance_margin_reward_scale": 0.0,
                            "dense_clearance_margin_reward_window": 8.0,
                        },
                    },
                    "ppo": {
                        "total_steps": 32768,
                        "rollout_steps": 128,
                        "num_envs": 4,
                        "update_epochs": 2,
                        "minibatch_size": 256,
                        "learning_rate": 0.0001,
                        "clip_coef": 0.1,
                        "max_grad_norm": 0.25,
                        "eval_episodes": 32,
                        "checkpoint_interval_steps": 4096,
                    },
                    "matched_budget_training_protocol": {"stage": "matched_budget_medium_v1"},
                },
            )
    return source_root


def test_build_containment_config_preserves_contract_and_sets_target_values(tmp_path: Path) -> None:
    source_root = _source_configs(tmp_path)

    config = build_containment_config(
        profile_name="L0_current_masked",
        seed_id=222601,
        source_config_root=source_root,
    )

    assert config["env"]["track_width"] == 8.5
    assert config["env"]["track_cost_scale"] == 3.0
    assert config["env"]["heading_cost_scale"] == 0.30
    assert config["env"]["road_margin_cost_scale"] == 2.6
    assert config["env"]["road_margin_warning_fraction"] == 0.50
    assert config["env"]["off_track_penalty"] == 8.0
    assert config["env"]["obstacle"]["dense_clearance_margin_reward_scale"] == 0.5
    assert config["env"]["obstacle"]["dense_clearance_margin_reward_window"] == 10.0
    assert config["env"]["obstacle"]["clearance_margin_reward_scale"] == 1.0
    assert config["env"]["include_privileged_params"] is False
    assert config["env"]["wheel_observation_mode"] == "none"
    assert config["env"]["obstacle_relative_velocity_mode"] == "zero"
    assert config["controller_profile"]["profile_specific_tuning"] is False
    assert config["midcourse_corridor_containment_repair_protocol"]["acceptance_criteria"][
        "return_improvement_alone_sufficient"
    ] is False


def test_materialize_containment_configs_writes_matched_matrix(tmp_path: Path) -> None:
    source_root = _source_configs(tmp_path)

    summary = materialize_containment_configs(
        output_dir=tmp_path / "out",
        source_config_root=source_root,
        training_output_root=tmp_path / "train",
    )

    assert summary["result_class"] == "current_sim_midcourse_corridor_containment_config_materialization_pass"
    assert summary["materialized_config_count"] == 15
    assert summary["training_matrix_row_count"] == 15
    assert summary["profile_set_matched"] is True
    assert summary["seed_set_matched"] is True
    assert summary["budget_signature_count"] == 1
    assert summary["contract_violation_count"] == 0
    assert summary["target_value_mismatch_count"] == 0
    assert summary["track_width_widened_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["training_started"] is False
    assert (tmp_path / "out" / "training_matrix.csv").exists()
    generated = read_json(tmp_path / "out" / "configs" / "L3_online_gru" / "seed_222603" / "config.json")
    assert generated["midcourse_corridor_containment_repair_protocol"]["stage"] == "midcourse_corridor_containment_v1"
    assert generated["controller_profile"]["midcourse_corridor_containment_config"] is True
