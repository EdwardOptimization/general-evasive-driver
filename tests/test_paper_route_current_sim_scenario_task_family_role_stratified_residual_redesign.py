from __future__ import annotations

from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, write_csv_rows
from autodrift.paper_route_current_sim_scenario_task_family_role_stratified_residual_redesign import (
    REQUIRED_MITIGATION_FIELDS,
    design_route_label,
    read_csv_rows,
    run_role_stratified_residual_redesign,
)


def _residual(
    scenario_id: str,
    role_family: str,
    primary_route_label: str,
    support_label: str,
) -> dict[str, Any]:
    return {
        "scenario_spec_id": scenario_id,
        "scenario_family_id": role_family.split("_", maxsplit=1)[0],
        "role_family": role_family,
        "sampled_obstacle_label": "unavoidable" if role_family == "R4_unavoidable_mitigation" else "drift_required",
        "support_label": support_label,
        "primary_route_label": primary_route_label,
        "dominant_failure_mode": "collision_dominated_failure",
        "hidden_dynamics_bucket": "low_mu",
        "obstacle_longitudinal_timing_bucket": "mid",
        "obstacle_lateral_offset_bucket": "centerline",
        "episode_count": 3,
        "success_count": 0,
        "collision_count": 3,
        "offtrack_count": 0,
        "aeb_success_count": 0,
        "aes_success_count": 0,
        "envelope_aes_success_count": 0,
    }


def _episode(scenario_id: str) -> dict[str, Any]:
    return {
        "workload_id": scenario_id,
        "scenario_spec_id": scenario_id,
        "support_policy_name": "aeb",
        "collision": True,
        "outcome_bucket": "collision_failure",
        "termination_reason": "obstacle_collision",
        "min_clearance_margin": -0.1,
        "max_off_track_overshoot": 0.0,
        "high_sideslip_fraction": 0.0,
        "action_rate_mean": 0.1,
        "return": -1.0,
    }


def test_design_route_label_marks_r4_metric_availability_gap_without_severity_fields() -> None:
    row = _residual(
        "r4",
        "R4_unavoidable_mitigation",
        "mitigation_semantics_or_support_redesign_candidate",
        "support_blocked",
    )
    label, _, requires_new_measurement = design_route_label(row, ["collision", "min_clearance_margin"])
    assert label == "r4_mitigation_metric_availability_gap"
    assert requires_new_measurement is True

    label, _, requires_new_measurement = design_route_label(row, list(REQUIRED_MITIGATION_FIELDS))
    assert label == "r4_mitigation_semantics_ready"
    assert requires_new_measurement is False


def test_role_stratified_residual_redesign_writes_counts_and_claim_boundary(tmp_path: Path) -> None:
    residual_rows = [
        _residual(
            "r4",
            "R4_unavoidable_mitigation",
            "mitigation_semantics_or_support_redesign_candidate",
            "support_blocked",
        ),
        _residual(
            "coverage",
            "R2_handling_limit_drift_capable_avoidance",
            "support_policy_coverage_candidate",
            "support_mixed",
        ),
        _residual(
            "redesign",
            "R3_recovery_after_limit",
            "scenario_or_support_redesign_candidate",
            "support_blocked",
        ),
        _residual(
            "metric",
            "R5_hidden_dynamics_robustness",
            "metric_semantics_audit_candidate",
            "metric_conflict",
        ),
    ]
    episode_rows = [_episode(row["scenario_spec_id"]) for row in residual_rows]
    residual_path = tmp_path / "residual.csv"
    episode_path = tmp_path / "episodes.csv"
    write_csv_rows(residual_path, residual_rows)
    write_csv_rows(episode_path, episode_rows)

    summary = run_role_stratified_residual_redesign(
        residual_scenario_rows=residual_path,
        episode_rows=episode_path,
        output_dir=tmp_path / "out",
        target_residual_scenario_count=4,
        target_r4_mitigation_row_count=1,
        target_coverage_row_count=1,
        target_redesign_row_count=1,
        target_metric_edge_row_count=1,
        next_blocker="next",
    )

    assert summary["result_class"] == "current_sim_scenario_task_family_role_stratified_residual_redesign_pass"
    assert summary["r4_mitigation_row_count"] == 1
    assert summary["r4_mitigation_metric_availability_gap"] is True
    assert summary["r4_missing_required_mitigation_metric_count"] == len(REQUIRED_MITIGATION_FIELDS)
    assert summary["r2_r3_r5_coverage_row_count"] == 1
    assert summary["r2_r3_r5_redesign_row_count"] == 1
    assert summary["metric_edge_row_count"] == 1
    assert summary["guardrail_violation_count"] == 0
    assert summary["support_policy_ranking_claim_made"] is False
    assert summary["mitigation_performance_claim_made"] is False

    stratified_rows = read_csv_rows(tmp_path / "out" / "role_stratified_residual_rows.csv")
    labels = {row["scenario_spec_id"]: row["design_route_label"] for row in stratified_rows}
    assert labels["r4"] == "r4_mitigation_metric_availability_gap"
    assert labels["coverage"] == "support_policy_coverage_materialization_required"
    assert labels["redesign"] == "scenario_or_support_redesign_materialization_required"
    assert labels["metric"] == "metric_semantics_edge_case"

    claim_rows = read_csv_rows(tmp_path / "out" / "claim_boundary.csv")
    mitigation_claim = [row for row in claim_rows if row["claim"] == "mitigation_performance_measured"][0]
    assert mitigation_claim["admissible"] == "False"
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["result_class"] == summary["result_class"]
