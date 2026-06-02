from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, write_json
from autodrift.paper_route_current_sim_r4_metric_instrumented_support_diagnostic_rerun import (
    R4_ROLE_FAMILY,
    materialize_r4_only_config,
    read_csv_table,
    run_r4_metric_instrumented_support_diagnostic_rerun,
)


def _scenario(spec_id: str, role: str) -> dict[str, Any]:
    return {
        "scenario_spec_id": spec_id,
        "scenario_family_id": role.split("_", maxsplit=1)[0],
        "role_family": role,
        "sampled_obstacle_label": "unavoidable" if role == R4_ROLE_FAMILY else "aeb_feasible",
        "allowed_labels_metadata_only": "unavoidable" if role == R4_ROLE_FAMILY else "aeb_feasible",
        "same_scene_group_id": spec_id,
        "hidden_dynamics_bucket": "weak_brake",
        "obstacle_longitudinal_timing_bucket": "mid",
        "obstacle_lateral_offset_bucket": "centerline",
        "initial_speed_mps": 12.0,
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


def _write_config(tmp_path: Path) -> Path:
    path = tmp_path / "base_config.json"
    write_json(
        path,
        {
            "scenario_specs": [
                _scenario("r0", "R0_stable_avoidable"),
                _scenario("r4_a", R4_ROLE_FAMILY),
                _scenario("r4_b", R4_ROLE_FAMILY),
            ]
        },
    )
    return path


def _fake_rollout(
    workload_row: Mapping[str, Any],
    scenario_spec: Mapping[str, Any],
    support_policy_name: str,
    eval_seed: int,
) -> dict[str, Any]:
    del workload_row
    return {
        "seed": eval_seed,
        "policy": support_policy_name,
        "steps": 20,
        "terminated": True,
        "truncated": False,
        "collision": True,
        "obstacle_completed": False,
        "termination_reason": "obstacle_collision",
        "outcome_bucket": "collision_failure",
        "return": -5.0,
        "min_clearance_margin": -0.2,
        "max_off_track_overshoot": 0.0,
        "time_to_first_off_track_s": 0.0,
        "high_sideslip_fraction": 0.2,
        "action_rate_mean": 0.05,
        "obstacle_label": scenario_spec["sampled_obstacle_label"],
        "impact_speed_mps": 8.0,
        "impact_speed_mps_available": True,
        "time_to_collision_s": 1.1,
        "time_to_collision_s_available": True,
        "collision_side_proxy": "front",
        "delta_v_at_impact_mps_available": False,
        "post_event_speed_mps_available": False,
        "recoverability_window_success_available": False,
        "impact_speed_proxy": 8.0,
        "impact_beta_abs": 0.3,
        "impact_yaw_rate_abs": 1.2,
        "impact_severity_proxy": 9.5,
        "collision_mitigation_score": 9.5,
    }


def test_materialize_r4_only_config_filters_non_r4_specs(tmp_path: Path) -> None:
    base = _write_config(tmp_path)
    result = materialize_r4_only_config(
        base_config=base,
        output_config=tmp_path / "r4.json",
        target_scenario_spec_count=2,
    )
    assert result["base_scenario_spec_count"] == 3
    assert result["r4_scenario_spec_count"] == 2
    payload = read_json(tmp_path / "r4.json")
    assert [spec["scenario_spec_id"] for spec in payload["scenario_specs"]] == ["r4_a", "r4_b"]
    assert {spec["role_family"] for spec in payload["scenario_specs"]} == {R4_ROLE_FAMILY}


def test_r4_metric_instrumented_support_diagnostic_rerun_with_fake_rollout(tmp_path: Path) -> None:
    base = _write_config(tmp_path)
    summary = run_r4_metric_instrumented_support_diagnostic_rerun(
        base_config=base,
        output_dir=tmp_path / "out",
        eval_seed_base=100,
        support_policies=("aeb", "aes"),
        seed_repeats=2,
        target_scenario_spec_count=2,
        target_support_policy_count=2,
        target_episode_count=8,
        rollout_fn=_fake_rollout,
    )

    assert summary["result_class"] == "current_sim_r4_metric_instrumented_support_diagnostic_rerun_pass"
    assert summary["base_result_class"] == "current_sim_scenario_task_family_feasibility_calibration_pass"
    assert summary["episode_count"] == 8
    assert summary["scenario_spec_count"] == 2
    assert summary["support_policy_count"] == 2
    assert summary["seed_repeat_count"] == 2
    assert summary["non_r4_role_count"] == 0
    assert summary["required_r4_export_missing_field_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["controller_family_ranking_claim_made"] is False
    assert summary["winner_selected"] is False
    assert summary["paper_level_claim_made"] is False

    rows, fieldnames = read_csv_table(tmp_path / "out" / "episode_rows.csv")
    assert len(rows) == 8
    assert "impact_speed_mps" in fieldnames
    assert "time_to_collision_s" in fieldnames
    assert {row["role_family"] for row in rows} == {R4_ROLE_FAMILY}
    field_rows, _ = read_csv_table(tmp_path / "out" / "r4_metric_field_completeness.csv")
    missing = [row for row in field_rows if row["present_in_episode_rows"] != "True"]
    assert missing == []
