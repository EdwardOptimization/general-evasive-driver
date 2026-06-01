from __future__ import annotations

from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, write_csv_rows
from autodrift.paper_route_current_sim_scenario_task_family_residual_support_audit import (
    primary_route_label,
    read_csv_rows,
    run_residual_support_audit,
)


def _scenario(
    scenario_id: str,
    role_family: str,
    support_label: str,
) -> dict[str, Any]:
    return {
        "scenario_spec_id": scenario_id,
        "scenario_family_id": role_family.split("_", maxsplit=1)[0],
        "role_family": role_family,
        "sampled_obstacle_label": "unavoidable" if role_family == "R4_unavoidable_mitigation" else "drift_required",
        "allowed_labels_metadata_only": "drift_required",
        "same_scene_group_id": scenario_id,
        "hidden_dynamics_bucket": "low_mu",
        "obstacle_longitudinal_timing_bucket": "mid",
        "obstacle_lateral_offset_bucket": "centerline",
        "initial_speed_mps": 14.0,
        "track_radius_m": 80.0,
        "track_width_m": 6.0,
        "actor_contract_id": "P0_human_view_no_wheel_no_oracle",
        "episode_count": 3,
        "support_label": support_label,
        "support_label_reason": "test",
        "aeb_success_count": 0,
        "aeb_collision_count": 1,
        "aeb_offtrack_count": 0,
        "aes_success_count": 0,
        "aes_collision_count": 1,
        "aes_offtrack_count": 0,
        "envelope_aes_success_count": 0,
        "envelope_aes_collision_count": 1,
        "envelope_aes_offtrack_count": 0,
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def _episode(scenario: dict[str, Any], policy: str) -> dict[str, Any]:
    return {
        "workload_id": f"{scenario['scenario_spec_id']}::{policy}",
        "scenario_spec_id": scenario["scenario_spec_id"],
        "scenario_family_id": scenario["scenario_family_id"],
        "role_family": scenario["role_family"],
        "sampled_obstacle_label": scenario["sampled_obstacle_label"],
        "support_policy_name": policy,
        "outcome_bucket": "collision_failure",
        "termination_reason": "obstacle_collision",
        "role_success": False,
        "success": False,
        "collision": True,
        "truncated": False,
    }


def test_primary_route_label_is_role_and_support_bounded() -> None:
    assert primary_route_label(_scenario("metric", "R3_recovery_after_limit", "metric_conflict"))[0] == (
        "metric_semantics_audit_candidate"
    )
    assert primary_route_label(_scenario("mixed", "R2_handling_limit_drift_capable_avoidance", "support_mixed"))[0] == (
        "support_policy_coverage_candidate"
    )
    assert primary_route_label(_scenario("blocked", "R2_handling_limit_drift_capable_avoidance", "support_blocked"))[0] == (
        "scenario_or_support_redesign_candidate"
    )
    assert primary_route_label(_scenario("r4", "R4_unavoidable_mitigation", "support_blocked"))[0] == (
        "mitigation_semantics_or_support_redesign_candidate"
    )
    assert primary_route_label(_scenario("clear", "R0_stable_avoidable", "support_clear"))[0] == "non_residual_support_clear"


def test_residual_support_audit_excludes_clear_rows_and_writes_route_summaries(tmp_path: Path) -> None:
    scenarios = [
        _scenario("r0_clear", "R0_stable_avoidable", "support_clear"),
        _scenario("r2_mixed", "R2_handling_limit_drift_capable_avoidance", "support_mixed"),
        _scenario("r2_blocked", "R2_handling_limit_drift_capable_avoidance", "support_blocked"),
        _scenario("r3_metric", "R3_recovery_after_limit", "metric_conflict"),
        _scenario("r4_blocked", "R4_unavoidable_mitigation", "support_blocked"),
    ]
    episodes = []
    for scenario in scenarios:
        for policy in ("aeb", "aes", "envelope_aes"):
            episodes.append(_episode(scenario, policy))
    episode_path = tmp_path / "episodes.csv"
    scenario_path = tmp_path / "scenarios.csv"
    role_path = tmp_path / "roles.csv"
    write_csv_rows(episode_path, episodes)
    write_csv_rows(scenario_path, scenarios)
    write_csv_rows(role_path, [{"role_family": "R2_handling_limit_drift_capable_avoidance"}])

    summary = run_residual_support_audit(
        episode_rows=episode_path,
        scenario_support_labels=scenario_path,
        role_support_summary=role_path,
        output_dir=tmp_path / "out",
        target_scenario_count=5,
        target_residual_scenario_count=4,
        target_support_clear_count=1,
        target_support_mixed_count=1,
        target_support_blocked_count=2,
        target_metric_conflict_count=1,
        target_r2_r5_residual_count=4,
        next_blocker="next",
    )

    assert summary["result_class"] == "current_sim_scenario_task_family_residual_support_audit_pass"
    assert summary["residual_scenario_count"] == 4
    assert summary["r0_residual_count"] == 0
    assert summary["r1_residual_count"] == 0
    assert summary["r2_r5_residual_count"] == 4
    assert summary["guardrail_violation_count"] == 0
    assert summary["support_policy_ranking_claim_made"] is False
    assert summary["winner_selected"] is False
    assert summary["next_blocker"] == "next"

    residual_rows = read_csv_rows(tmp_path / "out" / "residual_scenario_rows.csv")
    assert {row["scenario_spec_id"] for row in residual_rows} == {"r2_mixed", "r2_blocked", "r3_metric", "r4_blocked"}
    route_rows = read_csv_rows(tmp_path / "out" / "residual_route_summary.csv")
    route_labels = {row["primary_route_label"] for row in route_rows}
    assert route_labels == {
        "support_policy_coverage_candidate",
        "scenario_or_support_redesign_candidate",
        "metric_semantics_audit_candidate",
        "mitigation_semantics_or_support_redesign_candidate",
    }
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["result_class"] == summary["result_class"]
