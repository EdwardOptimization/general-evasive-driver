from __future__ import annotations

from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.paper_route_current_sim_scenario_task_family_role_success_semantics import (
    is_r0_safe_stop_success,
    role_success,
    role_success_reason,
)
from autodrift.paper_route_current_sim_scenario_task_family_role_success_semantics_repair import (
    read_csv_rows,
    run_role_success_semantics_repair,
)


def _row(
    role_family: str = "R0_stable_avoidable",
    *,
    scenario_id: str = "r0_0",
    policy: str = "aeb",
    seed_repeat_index: int = 0,
    termination_reason: str = "speed_too_low",
    outcome_bucket: str = "speed_too_low_noncollision_noncompletion",
    min_clearance_margin: float = 5.0,
    collision: bool = False,
    offtrack: bool = False,
    success: bool = False,
    obstacle_completed: bool = False,
) -> dict[str, Any]:
    return {
        "workload_id": f"{scenario_id}::{policy}::{seed_repeat_index}",
        "scenario_index": 0,
        "support_policy_index": 0,
        "seed_repeat_index": seed_repeat_index,
        "eval_seed": 100 + seed_repeat_index,
        "scenario_spec_id": scenario_id,
        "scenario_family_id": role_family.split("_", maxsplit=1)[0],
        "role_family": role_family,
        "sampled_obstacle_label": "aeb_feasible" if role_family == "R0_stable_avoidable" else "drift_required",
        "allowed_labels_metadata_only": "aeb_feasible",
        "same_scene_group_id": "scene_0",
        "hidden_dynamics_bucket": "nominal",
        "obstacle_longitudinal_timing_bucket": "early_far",
        "obstacle_lateral_offset_bucket": "centerline",
        "initial_speed_mps": 12.0,
        "track_radius_m": 40.0,
        "track_width_m": 8.0,
        "actor_contract_id": "P0_human_view_no_wheel_no_oracle",
        "support_policy_name": policy,
        "support_policy_kind": "support",
        "support_policy_uses_privileged_info": False,
        "support_policy_deployable_candidate": False,
        "diagnostic_only": True,
        "ranking_admissible": False,
        "policy": policy,
        "seed": 100 + seed_repeat_index,
        "steps": 12,
        "terminated": True,
        "truncated": False,
        "success": success,
        "collision": collision,
        "obstacle_completed": obstacle_completed,
        "termination_reason": "off_track" if offtrack else termination_reason,
        "outcome_bucket": "off_track_noncollision_noncompletion" if offtrack else outcome_bucket,
        "return": 1.0,
        "min_clearance_margin": min_clearance_margin,
        "max_off_track_overshoot": 0.0,
        "time_to_first_off_track_s": 0.0,
        "high_sideslip_fraction": 0.0,
        "action_rate_mean": 0.1,
        "environment_rollout_started": True,
        "policy_action_executed": True,
        "measured_rollout_started": True,
    }


def _spec(scenario_id: str, role_family: str) -> dict[str, Any]:
    return {
        "scenario_spec_id": scenario_id,
        "scenario_family_id": role_family.split("_", maxsplit=1)[0],
        "role_family": role_family,
        "sampled_obstacle_label": "aeb_feasible" if role_family == "R0_stable_avoidable" else "drift_required",
        "allowed_labels_metadata_only": "aeb_feasible",
        "same_scene_group_id": "scene_0",
        "hidden_dynamics_bucket": "nominal",
        "obstacle_longitudinal_timing_bucket": "early_far",
        "obstacle_lateral_offset_bucket": "centerline",
        "initial_speed_mps": 12.0,
        "track_radius_m": 40.0,
        "track_width_m": 8.0,
        "actor_contract_id": "P0_human_view_no_wheel_no_oracle",
    }


def test_r0_safe_stop_success_is_role_bounded() -> None:
    safe_stop = _row()
    assert is_r0_safe_stop_success(safe_stop)
    assert role_success(safe_stop)
    assert role_success_reason(safe_stop) == "r0_safe_stop_success"

    assert not role_success(_row(collision=True))
    assert not role_success(_row(offtrack=True))
    assert not role_success(_row(min_clearance_margin=0.0))

    non_r0_safe_stop = _row(role_family="R2_handling_limit_drift_capable_avoidance", scenario_id="r2_0")
    assert not is_r0_safe_stop_success(non_r0_safe_stop)
    assert not role_success(non_r0_safe_stop)

    obstacle_pass = _row(
        role_family="R2_handling_limit_drift_capable_avoidance",
        scenario_id="r2_pass",
        termination_reason="success",
        outcome_bucket="success_obstacle_pass",
        success=True,
        obstacle_completed=True,
    )
    assert role_success(obstacle_pass)
    assert role_success_reason(obstacle_pass) == "obstacle_pass_success"


def test_role_success_semantics_repair_rescores_r0_support_clear(tmp_path: Path) -> None:
    episodes = []
    for repeat in range(3):
        episodes.append(_row("R0_stable_avoidable", scenario_id="r0_0", policy="aeb", seed_repeat_index=repeat))
        episodes.append(_row("R2_handling_limit_drift_capable_avoidance", scenario_id="r2_0", policy="aeb", seed_repeat_index=repeat))
    config_path = tmp_path / "config.json"
    episode_path = tmp_path / "episodes.csv"
    baseline_labels_path = tmp_path / "baseline_labels.csv"
    write_json(config_path, {"scenario_specs": [_spec("r0_0", "R0_stable_avoidable"), _spec("r2_0", "R2_handling_limit_drift_capable_avoidance")]})
    write_csv_rows(episode_path, episodes)
    write_csv_rows(
        baseline_labels_path,
        [
            {**_spec("r0_0", "R0_stable_avoidable"), "support_label": "metric_conflict"},
            {**_spec("r2_0", "R2_handling_limit_drift_capable_avoidance"), "support_label": "support_blocked"},
        ],
    )

    summary = run_role_success_semantics_repair(
        config=config_path,
        episode_rows=episode_path,
        baseline_scenario_support_labels=baseline_labels_path,
        output_dir=tmp_path / "out",
        target_episode_count=6,
        target_scenario_spec_count=2,
        target_support_policy_count=1,
        target_r0_support_clear_count=1,
        target_r0_aeb_role_success_count=3,
        target_r0_safe_stop_success_count=3,
        min_support_clear_delta=1,
        max_metric_conflict_delta=0,
        next_blocker="next",
    )

    assert summary["result_class"] == "current_sim_scenario_task_family_role_success_semantics_repair_pass"
    assert summary["r0_support_clear_count"] == 1
    assert summary["r0_metric_conflict_count"] == 0
    assert summary["r0_aeb_role_success_count"] == 3
    assert summary["r0_safe_stop_success_count"] == 3
    assert summary["non_r0_safe_stop_success_count"] == 0
    assert summary["support_clear_delta"] == 1
    assert summary["metric_conflict_delta"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_rollout_started"] is False
    assert summary["next_blocker"] == "next"

    scenario_rows = read_csv_rows(tmp_path / "out" / "scenario_support_labels_rescored.csv")
    labels = {row["scenario_spec_id"]: row["support_label"] for row in scenario_rows}
    assert labels == {"r0_0": "support_clear", "r2_0": "metric_conflict"}
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["result_class"] == summary["result_class"]
