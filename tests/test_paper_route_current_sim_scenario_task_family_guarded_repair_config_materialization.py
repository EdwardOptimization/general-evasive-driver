from __future__ import annotations

from pathlib import Path
from typing import Any

from autodrift import paper_route_current_sim_scenario_task_family_guarded_repair_config_materialization as materialization
from autodrift.artifacts import read_json, write_json
from autodrift.paper_route_current_sim_training_stability_repair_execution import EXPECTED_PROFILES, EXPECTED_SEED_IDS


def _source_config(*, profile_name: str, seed_id: int, privileged: bool = False) -> dict[str, Any]:
    return {
        "controller_profile": {
            "actor_encoder": "gru" if profile_name == "L3_online_gru" else "mlp",
            "actor_history_length": 1,
            "input_contract": "P0_human_view_no_wheel_no_oracle",
            "name": profile_name,
            "observation_dim": 72,
            "profile_specific_tuning": False,
            "ranking_admissible": False,
            "uses_hidden_oracle_actor_inputs": False,
            "uses_recurrent_hidden": profile_name == "L3_online_gru",
            "uses_reference_or_ttc_inputs": False,
            "uses_wheel_or_slip_inputs": False,
            "winner_selected": False,
        },
        "env": {
            "history_length": 1,
            "include_privileged_params": privileged,
            "obstacle": {
                "clearance_margin_reward_clip": 0.1,
                "clearance_margin_reward_scale": 0.0,
                "collision_penalty": 20.0,
                "dense_clearance_margin_reward_scale": 0.0,
                "dense_clearance_margin_reward_window": 5.0,
                "enabled": True,
            },
            "obstacle_relative_velocity_mode": "zero",
            "off_track_penalty": 8.0,
            "road_margin_cost_scale": 2.6,
            "road_margin_warning_fraction": 0.5,
            "termination_penalty": 8.0,
            "track_cost_scale": 3.0,
            "heading_cost_scale": 0.3,
            "track_width": 8.5,
            "wheel_observation_mode": "none",
        },
        "midcourse_corridor_containment_repair_protocol": {"stage": "midcourse_corridor_containment_v1"},
        "ppo": {
            "checkpoint_interval_steps": 4096,
            "clip_coef": 0.1,
            "eval_episodes": 32,
            "learning_rate": 0.0001,
            "max_grad_norm": 0.25,
            "minibatch_size": 256,
            "num_envs": 4,
            "rollout_steps": 128,
            "total_steps": 32768,
            "update_epochs": 2,
        },
    }


def _write_source_configs(root: Path, *, privileged_first: bool = False) -> None:
    for profile_index, profile_name in enumerate(EXPECTED_PROFILES):
        for seed_index, seed_id in enumerate(EXPECTED_SEED_IDS):
            privileged = privileged_first and profile_index == 0 and seed_index == 0
            path = root / profile_name / f"seed_{int(seed_id)}" / "config.json"
            write_json(path, _source_config(profile_name=profile_name, seed_id=int(seed_id), privileged=privileged))


def _write_gate_spec(path: Path) -> None:
    write_json(
        path,
        {
            "offtrack_target_policy": {
                "reduce_global_offtrack_count": True,
                "reduce_or_hold_target_slice_offtrack_count": True,
                "target_slice_count": 20,
            },
            "collision_guardrail_policy": {
                "do_not_increase_global_collision_count": True,
                "do_not_increase_guardrail_slice_collision_count": True,
                "guardrail_slice_count": 11,
            },
            "completeness_policy": {"target_episode_count": 1080},
        },
    )


def test_guarded_repair_materializes_shared_non_profile_configs(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    gate_spec = tmp_path / "repair_gate_spec.json"
    _write_source_configs(source_root)
    _write_gate_spec(gate_spec)

    summary = materialization.materialize_guarded_repair_configs(
        source_config_root=source_root,
        repair_gate_spec_path=gate_spec,
        output_dir=tmp_path / "out",
        training_output_root=tmp_path / "train",
        next_blocker="next",
    )

    assert summary["result_class"] == "current_sim_scenario_task_family_guarded_repair_config_materialization_pass"
    assert summary["config_count"] == len(EXPECTED_PROFILES) * len(EXPECTED_SEED_IDS)
    assert summary["profile_count"] == len(EXPECTED_PROFILES)
    assert summary["seed_count"] == len(EXPECTED_SEED_IDS)
    assert summary["budget_signature_count"] == 1
    assert summary["actor_contract_violation_count"] == 0
    assert summary["track_width_widened_count"] == 0
    assert summary["reward_changed_config_count"] == summary["config_count"]
    assert summary["repair_gate_spec_copied"] is True
    assert summary["offtrack_target_slice_count"] == 20
    assert summary["collision_guardrail_slice_count"] == 11

    generated = read_json(tmp_path / "out" / "configs" / "L0_current_masked" / "seed_222601" / "config.json")
    assert generated["env"]["track_width"] == 8.5
    assert generated["env"]["track_cost_scale"] == 3.4
    assert generated["env"]["road_margin_warning_fraction"] == 0.45
    assert generated["controller_profile"]["profile_specific_tuning"] is False
    protocol = generated["scenario_task_family_guarded_repair_protocol"]
    assert protocol["repair_gate_spec_encoded"] is True
    assert protocol["acceptance_criteria"]["return_improvement_alone_sufficient"] is False
    assert read_json(tmp_path / "out" / "summary.json")["next_blocker"] == "next"


def test_guarded_repair_fails_on_actor_contract_violation(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    gate_spec = tmp_path / "repair_gate_spec.json"
    _write_source_configs(source_root, privileged_first=True)
    _write_gate_spec(gate_spec)

    summary = materialization.materialize_guarded_repair_configs(
        source_config_root=source_root,
        repair_gate_spec_path=gate_spec,
        output_dir=tmp_path / "out",
        training_output_root=tmp_path / "train",
    )

    assert summary["result_class"] == "current_sim_scenario_task_family_guarded_repair_config_materialization_fail"
    assert summary["actor_contract_violation_count"] == 1
    assert summary["track_width_widened_count"] == 0
