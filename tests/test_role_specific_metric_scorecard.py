from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows
from autodrift.role_specific_metric_scorecard import (
    metric_contract_rows,
    run_role_specific_metric_scorecard_extraction,
)


def _row(idx: int, *, role: str, profile: str) -> dict[str, object]:
    collision = role == "unavoidable_mitigation"
    success = role != "unavoidable_mitigation" and idx % 3 == 0
    return {
        "workload_id": f"w{idx}",
        "profile_name": profile,
        "role_panel_id": role,
        "hidden_dynamics_bucket": "nominal",
        "sampled_obstacle_label": "unavoidable" if collision else "aes_feasible",
        "outcome_bucket": "collision_failure" if collision else ("success_obstacle_pass" if success else "off_track_noncollision_noncompletion"),
        "success": success,
        "obstacle_completed": success,
        "obstacle_passed_raw": success,
        "collision": collision,
        "min_clearance_margin": -0.1 if collision else 1.0,
        "return": 1.0,
        "steps": 32,
        "action_rate_mean": 0.2,
        "high_sideslip_fraction": 0.0,
        "recovery_success": success,
        "controlled_drift_recovery_success": success,
        "drift_used": role == "drift_required_recovery",
        "recovery_time_proxy": 0.1 if success else "",
        "impact_severity_proxy": 2.0 if collision else "",
        "collision_mitigation_score": 2.0 if collision else 0.0,
        "impact_speed_proxy": 2.0 if collision else "",
        "impact_beta_abs": 0.2 if collision else "",
        "impact_yaw_rate_abs": 0.3 if collision else "",
        "off_track_severity_proxy": 0.0,
    }


def test_metric_contract_blocks_unavoidable_success_primary() -> None:
    contract = metric_contract_rows()

    assert not any(
        row["role_panel_id"] == "unavoidable_mitigation"
        and row["metric_name"] == "success_obstacle_pass_rate"
        and row["primary_metric"]
        for row in contract
    )
    assert any(
        row["role_panel_id"] == "unavoidable_mitigation"
        and row["metric_name"] == "impact_severity_proxy_mean"
        and row["primary_metric"]
        for row in contract
    )


def test_role_specific_metric_scorecard_extraction_smoke(tmp_path: Path) -> None:
    roles = [
        "stable_avoidance_aes",
        "drift_required_recovery",
        "hidden_dynamics_robustness",
        "unavoidable_mitigation",
    ]
    rows = []
    idx = 0
    profiles = [f"profile_{index}" for index in range(12)]
    for role in roles:
        for profile in profiles:
            for _ in range(1):
                rows.append(_row(idx, role=role, profile=profile))
                idx += 1
    rows_path = tmp_path / "episode_rows.csv"
    write_csv_rows(rows_path, rows)

    summary = run_role_specific_metric_scorecard_extraction(
        episode_rows_path=rows_path,
        output_dir=tmp_path / "out",
        target_episode_count=len(rows),
    )

    assert summary["result_class"] == "role_specific_metric_scorecard_extraction_pass"
    assert summary["episode_count"] == len(rows)
    assert summary["role_panel_count"] == 4
    assert summary["profile_count"] == 12
    assert summary["profile_role_scorecard_rows"] == 48
    assert summary["role_panel_scorecard_rows"] == 4
    assert summary["mitigation_contract_uses_success_as_primary"] is False
    assert summary["ranking_admissible_after_audit"] is False
    assert summary["guardrail_violation_count"] == 0
    assert (tmp_path / "out" / "profile_role_scorecard.csv").exists()
    assert (tmp_path / "out" / "ranking_blockers.csv").exists()
    assert read_json(tmp_path / "out" / "summary.json")["result_class"] == summary["result_class"]
