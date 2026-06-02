from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows
from autodrift.paper_route_current_sim_scenario_support_redesign_consolidation import (
    run_scenario_support_redesign_consolidation,
)


def _residual_row(scenario_id: str, role: str, failure: str, hidden: str = "low_mu") -> dict[str, object]:
    return {
        "scenario_spec_id": scenario_id,
        "scenario_family_id": role.split("_", maxsplit=1)[0],
        "role_family": role,
        "sampled_obstacle_label": "drift_required",
        "same_scene_group_id": scenario_id,
        "hidden_dynamics_bucket": hidden,
        "obstacle_longitudinal_timing_bucket": "late_close" if failure == "collision_dominated_failure" else "mid",
        "obstacle_lateral_offset_bucket": "left_offset" if failure == "offtrack_dominated_failure" else "centerline",
        "initial_speed_mps": 15.0,
        "track_radius_m": 80.0,
        "track_width_m": 6.5,
        "actor_contract_id": "P0_human_view_no_wheel_no_oracle",
        "support_label": "support_blocked",
        "dominant_failure_mode": failure,
        "collision_count": 5 if failure == "collision_dominated_failure" else 0,
        "offtrack_count": 5 if failure == "offtrack_dominated_failure" else 0,
        "aeb_success_count": 0,
        "aeb_collision_count": 5,
        "aeb_offtrack_count": 0,
        "aes_success_count": 0,
        "aes_collision_count": 5 if failure == "collision_dominated_failure" else 0,
        "aes_offtrack_count": 5 if failure == "offtrack_dominated_failure" else 0,
        "envelope_aes_success_count": 0,
        "envelope_aes_collision_count": 0,
        "envelope_aes_offtrack_count": 5,
    }


def _write_inputs(root: Path) -> tuple[Path, Path, Path]:
    rescore_dir = root / "rescore"
    residual_dir = root / "residual"
    source_dir = root / "source"
    rescore_dir.mkdir()
    residual_dir.mkdir()
    source_dir.mkdir()
    residual_rows = [
        _residual_row("original_1", "R2_handling_limit_drift_capable_avoidance", "collision_dominated_failure"),
        _residual_row("original_2", "R5_hidden_dynamics_robustness", "offtrack_dominated_failure", "weak_brake"),
    ]
    write_csv_rows(
        rescore_dir / "residual_rescore_rows.csv",
        [
            {"scenario_spec_id": "original_1", "rescore_route_label": "scenario_or_support_redesign_gap"},
            {"scenario_spec_id": "original_2", "rescore_route_label": "scenario_or_support_redesign_gap"},
            {"scenario_spec_id": "coverage_only", "rescore_route_label": "support_policy_coverage_gap"},
        ],
    )
    write_csv_rows(residual_dir / "residual_scenario_rows.csv", residual_rows)
    remapped = _residual_row("remapped_1", "R3_recovery_after_limit", "collision_dominated_failure")
    remapped.update(
        {
            "recommended_next_route": "scenario_or_support_redesign_candidate",
            "dominant_failure_bucket": "collision_dominated_failure",
            "source_signature": "remapped_sig",
        }
    )
    secondary = _residual_row("coverage_only", "R3_recovery_after_limit", "collision_dominated_failure")
    secondary.update(
        {
            "recommended_next_route": "support_policy_coverage_materialization_candidate",
            "dominant_failure_bucket": "collision_dominated_failure",
            "source_signature": "coverage_sig",
        }
    )
    write_csv_rows(source_dir / "coverage_gap_source_rows.csv", [remapped, secondary])
    return rescore_dir, residual_dir, source_dir


def test_scenario_support_redesign_consolidation_materializes_expected_outputs(tmp_path: Path) -> None:
    rescore_dir, residual_dir, source_dir = _write_inputs(tmp_path)
    output_dir = tmp_path / "out"

    summary = run_scenario_support_redesign_consolidation(
        rescore_dir=rescore_dir,
        residual_dir=residual_dir,
        source_mapping_dir=source_dir,
        output_dir=output_dir,
        target_original_redesign_gap_count=2,
        target_remapped_redesign_candidate_count=1,
        target_secondary_coverage_row_count=1,
    )

    assert summary["result_class"] == "current_sim_scenario_support_redesign_consolidation_pass"
    assert summary["original_redesign_gap_count"] == 2
    assert summary["remapped_coverage_redesign_candidate_count"] == 1
    assert summary["combined_redesign_related_row_count"] == 3
    assert summary["unique_redesign_scenario_count"] == 3
    assert summary["secondary_coverage_materialization_row_count"] == 1
    assert summary["needs_user_review_count"] == 0
    assert summary["guardrail_violation_count"] == 0

    persisted = read_json(output_dir / "summary.json")
    assert persisted["combined_redesign_related_row_count"] == 3

    rows_text = (output_dir / "consolidated_redesign_rows.csv").read_text(encoding="utf-8")
    assert "original_m2336_redesign_gap" in rows_text
    assert "remapped_m2340_coverage_redesign_candidate" in rows_text
    assert "geometry_timing_rebalance_candidate" in rows_text

    secondary_text = (output_dir / "secondary_coverage_materialization_rows.csv").read_text(encoding="utf-8")
    assert "support_policy_coverage_materialization_candidate" in secondary_text

    claims = (output_dir / "claim_boundary.csv").read_text(encoding="utf-8")
    assert "support_policy_ranking,False,False" in claims
