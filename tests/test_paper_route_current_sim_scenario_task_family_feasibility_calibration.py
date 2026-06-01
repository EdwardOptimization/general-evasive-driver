from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from autodrift import paper_route_current_sim_scenario_task_family_feasibility_calibration as calibration
from autodrift.artifacts import read_json, write_json


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


def _write_config(tmp_path: Path, *, ranking_flag: bool = False) -> Path:
    config_path = tmp_path / "scenario_config.json"
    spec_a = _scenario("spec_a")
    spec_b = _scenario("spec_b", role="R1_aeb_infeasible_stable_aes", label="aes_feasible")
    spec_a["ranking_admissible"] = ranking_flag
    write_json(config_path, {"scenario_specs": [spec_a, spec_b]})
    return config_path


def _fake_rollout(
    workload_row: Mapping[str, Any],
    scenario_spec: Mapping[str, Any],
    support_policy_name: str,
    eval_seed: int,
) -> dict[str, Any]:
    del workload_row
    scenario_id = str(scenario_spec["scenario_spec_id"])
    success = scenario_id == "spec_a" and support_policy_name == "aeb"
    obstacle_completed = success
    return {
        "seed": eval_seed,
        "policy": support_policy_name,
        "steps": 40,
        "terminated": True,
        "truncated": False,
        "collision": False,
        "obstacle_completed": obstacle_completed,
        "termination_reason": "obstacle_completed" if success else "off_track",
        "outcome_bucket": "success_obstacle_pass" if success else "off_track_noncollision_noncompletion",
        "return": 12.0 if success else -2.0,
        "min_clearance_margin": 0.42 if success else -0.1,
        "max_off_track_overshoot": 0.0 if success else 0.8,
        "time_to_first_off_track_s": 0.0 if success else 1.2,
        "high_sideslip_fraction": 0.0,
        "action_rate_mean": 0.05,
        "obstacle_label": scenario_spec["sampled_obstacle_label"],
    }


def test_feasibility_calibration_materializes_support_labels_with_fake_rollout(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)

    summary = calibration.run_feasibility_calibration(
        config_path=config_path,
        output_dir=tmp_path / "out",
        eval_seed_base=700,
        support_policies=("aeb", "aes", "envelope_aes"),
        seed_repeats=2,
        target_scenario_spec_count=2,
        target_support_policy_count=3,
        target_episode_count=12,
        rollout_fn=_fake_rollout,
    )

    assert summary["result_class"] == "current_sim_scenario_task_family_feasibility_calibration_pass"
    assert summary["episode_count"] == 12
    assert summary["scenario_spec_count"] == 2
    assert summary["support_policy_count"] == 3
    assert summary["seed_repeat_count"] == 2
    assert summary["failure_count"] == 0
    assert summary["metadata_missing_count"] == 0
    assert summary["metric_completeness_failure_count"] == 0
    assert summary["ranking_admissible_count"] == 0
    assert summary["winner_selected"] is False
    assert summary["paper_level_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert summary["support_label_counts"] == {"support_blocked": 1, "support_clear": 1}

    scenario_rows = calibration.read_csv_rows(tmp_path / "out" / "scenario_support_labels.csv")
    labels = {row["scenario_spec_id"]: row["support_label"] for row in scenario_rows}
    assert labels == {"spec_a": "support_clear", "spec_b": "support_blocked"}
    assert (tmp_path / "out" / "support_aggregate_rows.csv").exists()
    assert (tmp_path / "out" / "role_support_summary.csv").exists()
    assert (tmp_path / "out" / "claim_boundary.csv").exists()

    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["next_blocker"] == calibration.DEFAULT_NEXT_BLOCKER


def test_feasibility_calibration_fails_closed_on_contract_or_ranking_flag(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path, ranking_flag=True)

    summary = calibration.run_feasibility_calibration(
        config_path=config_path,
        output_dir=tmp_path / "out",
        eval_seed_base=700,
        support_policies=("aeb", "aes", "envelope_aes"),
        seed_repeats=2,
        target_scenario_spec_count=2,
        target_support_policy_count=3,
        target_episode_count=12,
        rollout_fn=_fake_rollout,
    )

    assert summary["result_class"] == "current_sim_scenario_task_family_feasibility_calibration_incomplete_or_fail"
    assert summary["episode_count"] == 0
    assert summary["validation_failure_count"] > 0
    assert summary["environment_rollout_started"] is False
    assert summary["policy_action_executed"] is False
    validation_rows = (tmp_path / "out" / "validation_failure_rows.csv").read_text(encoding="utf-8")
    assert "guardrail_violation" in validation_rows
    assert "ranking_admissible" in validation_rows


def test_feasibility_calibration_rejects_unknown_support_policy(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)

    summary = calibration.run_feasibility_calibration(
        config_path=config_path,
        output_dir=tmp_path / "out",
        eval_seed_base=700,
        support_policies=("aeb", "unknown_policy"),
        seed_repeats=2,
        target_scenario_spec_count=2,
        target_support_policy_count=2,
        target_episode_count=8,
        rollout_fn=_fake_rollout,
    )

    assert summary["result_class"] == "current_sim_scenario_task_family_feasibility_calibration_incomplete_or_fail"
    assert summary["episode_count"] == 0
    validation_rows = (tmp_path / "out" / "validation_failure_rows.csv").read_text(encoding="utf-8")
    assert "unsupported_support_policy" in validation_rows
