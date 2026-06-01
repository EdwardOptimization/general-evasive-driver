from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from autodrift import paper_route_current_sim_scenario_task_family_measured_execution as runner
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _scenario(spec_id: str, role: str = "R0_stable_avoidable", label: str = "aeb_feasible") -> dict[str, Any]:
    return {
        "scenario_spec_id": spec_id,
        "scenario_family_id": role.split("_", maxsplit=1)[0],
        "role_family": role,
        "sampled_obstacle_label": label,
        "allowed_labels_metadata_only": label,
        "same_scene_group_id": f"group-{spec_id}",
        "hidden_dynamics_bucket": "nominal",
        "obstacle_longitudinal_timing_bucket": "early_far",
        "obstacle_lateral_offset_bucket": "centerline",
        "initial_speed_mps": 8.0,
        "track_radius_m": 80.0,
        "track_width_m": 6.0,
        "actor_contract_id": "P0_human_view_no_wheel_no_oracle",
        "contract_violation_count": 0,
        "labels_enter_actor_input": False,
        "ranking_admissible": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "execution_blocked_by_unsupported_capability": False,
        "env_config": {
            "history_length": 1,
            "action_history_mode": "full",
            "include_privileged_params": False,
            "wheel_observation_mode": "none",
            "obstacle_relative_velocity_mode": "zero",
        },
    }


def _write_inputs(tmp_path: Path, *, ranking_flag: bool = False) -> tuple[Path, Path, Path]:
    config_path = tmp_path / "scenario_config.json"
    write_json(config_path, {"scenario_specs": [_scenario("spec_a"), _scenario("spec_b", role="R1_aeb_infeasible_stable_aes", label="aes_feasible")]})

    config_root = tmp_path / "configs"
    selected_rows: list[dict[str, Any]] = []
    for profile, seed in (("L0_current_masked", 101), ("L3_online_gru", 102)):
        write_json(
            config_root / profile / f"seed_{seed}" / "config.json",
            {
                "env": {"history_length": 1, "action_history_mode": "full"},
                "controller_profile": {
                    "name": profile,
                    "observation_mask": "none",
                    "previous_command_mask_indices": [],
                    "history_transform": "none",
                    "reset_hidden_policy": "episode_persistent",
                },
            },
        )
        selected_rows.append(
            {
                "matrix_id": f"{profile}::seed_{seed}",
                "profile_name": profile,
                "seed_id": seed,
                "selected_checkpoint_path": str(tmp_path / "checkpoints" / profile / f"seed_{seed}" / "checkpoint.pt"),
                "selected_checkpoint_step": 2048,
                "selected_checkpoint_kind": "periodic",
                "selected_readiness_floor_pass": False,
                "diagnostic_only": True,
                "ranking_admissible": ranking_flag,
                "winner_selected": False,
            }
        )
    selected_path = tmp_path / "selected_checkpoint_rows.csv"
    write_csv_rows(selected_path, selected_rows)
    return config_path, selected_path, config_root


def _fake_rollout(workload_row: Mapping[str, Any], scenario_spec: Mapping[str, Any], eval_seed: int) -> dict[str, Any]:
    return {
        "seed": eval_seed,
        "policy": "checkpoint",
        "steps": 40,
        "terminated": True,
        "truncated": False,
        "collision": False,
        "obstacle_completed": True,
        "termination_reason": "obstacle_completed",
        "outcome_bucket": "success_obstacle_pass",
        "return": 12.0,
        "min_clearance_margin": 0.42,
        "max_off_track_overshoot": 0.0,
        "time_to_first_off_track_s": 0.0,
        "high_sideslip_fraction": 0.0,
        "action_rate_mean": 0.05,
        "obstacle_label": scenario_spec["sampled_obstacle_label"],
        "workload_marker": workload_row["workload_id"],
    }


def test_scenario_task_family_measured_execution_preserves_metadata_with_fake_rollout(tmp_path: Path) -> None:
    config_path, selected_path, config_root = _write_inputs(tmp_path)

    summary = runner.run_scenario_task_family_measured_execution(
        config_path=config_path,
        selected_rows_path=selected_path,
        config_root=config_root,
        output_dir=tmp_path / "out",
        eval_seed_base=500,
        target_scenario_spec_count=2,
        target_selected_checkpoint_count=2,
        target_episode_count=4,
        rollout_fn=_fake_rollout,
    )

    assert summary["result_class"] == "current_sim_scenario_task_family_measured_execution_pass"
    assert summary["episode_count"] == 4
    assert summary["scenario_spec_count"] == 2
    assert summary["selected_checkpoint_count"] == 2
    assert summary["failure_count"] == 0
    assert summary["metadata_missing_count"] == 0
    assert summary["metric_completeness_failure_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["controller_family_ranking_claim_made"] is False
    assert summary["winner_selected"] is False
    assert summary["paper_level_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert summary["role_family_counts"] == {
        "R0_stable_avoidable": 2,
        "R1_aeb_infeasible_stable_aes": 2,
    }
    assert summary["profile_counts"] == {"L0_current_masked": 2, "L3_online_gru": 2}

    episode_rows = runner.read_csv_rows(tmp_path / "out" / "episode_rows.csv")
    assert [int(row["eval_seed"]) for row in episode_rows] == [500, 501, 1500, 1501]
    assert {row["sampled_label_matches_spec"] for row in episode_rows} == {"True"}
    assert (tmp_path / "out" / "aggregate_by_role_family.csv").exists()
    assert (tmp_path / "out" / "aggregate_by_profile_seed.csv").exists()
    assert (tmp_path / "out" / "claim_boundary.csv").exists()

    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["next_blocker"] == runner.DEFAULT_NEXT_BLOCKER


def test_scenario_task_family_measured_execution_fails_closed_on_metadata_gap(tmp_path: Path) -> None:
    config_path, selected_path, config_root = _write_inputs(tmp_path)
    payload = read_json(config_path)
    payload["scenario_specs"][0].pop("role_family")
    write_json(config_path, payload)

    summary = runner.run_scenario_task_family_measured_execution(
        config_path=config_path,
        selected_rows_path=selected_path,
        config_root=config_root,
        output_dir=tmp_path / "out",
        eval_seed_base=500,
        target_scenario_spec_count=2,
        target_selected_checkpoint_count=2,
        target_episode_count=4,
        rollout_fn=_fake_rollout,
    )

    assert summary["result_class"] == "current_sim_scenario_task_family_measured_execution_incomplete_or_fail"
    assert summary["episode_count"] == 0
    assert summary["validation_failure_count"] > 0
    assert summary["metadata_missing_count"] > 0
    assert summary["environment_rollout_started"] is False
    assert summary["policy_action_executed"] is False


def test_scenario_task_family_measured_execution_fails_closed_on_ranking_flag(tmp_path: Path) -> None:
    config_path, selected_path, config_root = _write_inputs(tmp_path, ranking_flag=True)

    summary = runner.run_scenario_task_family_measured_execution(
        config_path=config_path,
        selected_rows_path=selected_path,
        config_root=config_root,
        output_dir=tmp_path / "out",
        eval_seed_base=500,
        target_scenario_spec_count=2,
        target_selected_checkpoint_count=2,
        target_episode_count=4,
        rollout_fn=_fake_rollout,
    )

    assert summary["result_class"] == "current_sim_scenario_task_family_measured_execution_incomplete_or_fail"
    assert summary["episode_count"] == 0
    validation_rows = (tmp_path / "out" / "validation_failure_rows.csv").read_text(encoding="utf-8")
    assert "guardrail_violation" in validation_rows
    assert "selected_row_ranking" in validation_rows
