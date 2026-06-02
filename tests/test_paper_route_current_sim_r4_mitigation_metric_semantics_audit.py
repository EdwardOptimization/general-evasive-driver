from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows
from autodrift.paper_route_current_sim_r4_mitigation_metric_semantics_audit import (
    run_r4_mitigation_metric_semantics_audit,
)


def _episode_row(scenario_id: str, policy: str, *, collision: bool = True) -> dict[str, object]:
    return {
        "scenario_spec_id": scenario_id,
        "role_family": "R4_unavoidable_mitigation",
        "support_policy_name": policy,
        "success": False,
        "collision": collision,
        "termination_reason": "obstacle_collision" if collision else "off_track",
        "impact_speed_mps": 8.0 if collision else "",
        "impact_speed_mps_available": collision,
        "time_to_collision_s": 1.2 if collision else "",
        "time_to_collision_s_available": collision,
        "collision_side_proxy": "front" if collision else "",
        "impact_speed_proxy": 8.0 if collision else "",
        "impact_beta_abs": 0.2 if collision else "",
        "impact_yaw_rate_abs": 1.1 if collision else "",
        "impact_severity_proxy": 8.5 if collision else "",
        "collision_mitigation_score": 8.5,
        "delta_v_at_impact_mps_available": False,
        "post_event_speed_mps_available": False,
        "post_event_yaw_rate_abs_available": False,
        "post_event_offtrack_overshoot_available": False,
        "recoverability_window_success_available": False,
        "ranking_admissible": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }


def _write_input(input_dir: Path) -> None:
    input_dir.mkdir(parents=True)
    episode_rows = [
        _episode_row("r4_a", "aeb"),
        _episode_row("r4_a", "aes"),
        _episode_row("r4_b", "aeb"),
        _episode_row("r4_b", "aes", collision=False),
    ]
    write_csv_rows(input_dir / "episode_rows.csv", episode_rows)
    write_csv_rows(
        input_dir / "scenario_support_labels.csv",
        [
            {"scenario_spec_id": "r4_a", "support_label": "support_blocked"},
            {"scenario_spec_id": "r4_b", "support_label": "support_mixed"},
        ],
    )
    write_csv_rows(input_dir / "r4_metric_field_completeness.csv", [])


def test_r4_mitigation_metric_semantics_audit_is_artifact_only_and_non_ranking(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    _write_input(input_dir)

    summary = run_r4_mitigation_metric_semantics_audit(
        input_dir=input_dir,
        output_dir=output_dir,
        target_scenario_count=2,
    )

    assert summary["result_class"] == "current_sim_r4_mitigation_metric_semantics_audit_pass"
    assert summary["scenario_count"] == 2
    assert summary["impact_proxy_available_scenario_count"] == 2
    assert summary["post_collision_blocked_scenario_count"] == 2
    assert summary["obstacle_passage_success_insufficient_count"] == 2
    assert summary["ranking_admissible_count"] == 0
    assert summary["winner_selected_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_rollout_started"] is False
    assert summary["measured_rollout_started"] is False

    persisted = read_json(output_dir / "summary.json")
    assert persisted["result_class"] == summary["result_class"]

    scenario_rows = (output_dir / "r4_metric_semantics_rows.csv").read_text(encoding="utf-8")
    assert "insufficient_for_r4" in scenario_rows
    assert "proxy_metric_available_post_collision_blocked" in scenario_rows

    policy_rows = (output_dir / "r4_metric_proxy_policy_aggregate.csv").read_text(encoding="utf-8")
    assert "ranking_admissible" in policy_rows
    assert "True" not in policy_rows

    claim_rows = (output_dir / "r4_claim_boundary.csv").read_text(encoding="utf-8")
    assert "post_collision_recovery_measured,False,False" in claim_rows
