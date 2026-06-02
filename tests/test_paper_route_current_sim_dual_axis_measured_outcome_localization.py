from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.paper_route_current_sim_dual_axis_measured_outcome_localization import (
    read_csv_rows,
    run_measured_outcome_localization,
)


def _episode(
    *,
    role_family: str,
    scenario_family_id: str,
    outcome_bucket: str,
    termination_reason: str,
    success: bool = False,
    collision: bool = False,
    index: int,
) -> dict[str, object]:
    return {
        "workload_id": f"{role_family}_{index}",
        "pack_id": "baseline_reference_pack",
        "profile_name": "L0_current_masked",
        "role_family": role_family,
        "scenario_family_id": scenario_family_id,
        "sampled_obstacle_label": "unavoidable" if role_family == "R4_unavoidable_mitigation" else "aes_feasible",
        "hidden_dynamics_bucket": "nominal",
        "obstacle_longitudinal_timing_bucket": "mid",
        "obstacle_lateral_offset_bucket": "centerline",
        "sampling_repair_class": "",
        "outcome_bucket": outcome_bucket,
        "termination_reason": termination_reason,
        "success": success,
        "collision": collision,
        "environment_rollout_started": True,
        "policy_action_executed": True,
        "measured_rollout_started": True,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "ranking_admissible": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
    }


def _inputs(tmp_path: Path) -> tuple[Path, Path]:
    rows: list[dict[str, object]] = []
    for index in range(30):
        rows.append(
            _episode(
                role_family="R0_stable_avoidable",
                scenario_family_id="R0",
                outcome_bucket="off_track_noncollision_noncompletion",
                termination_reason="off_track",
                index=index,
            )
        )
    for index in range(24):
        rows.append(
            _episode(
                role_family="R2_handling_limit_drift_capable_avoidance",
                scenario_family_id="R2",
                outcome_bucket="off_track_noncollision_noncompletion",
                termination_reason="off_track",
                index=index,
            )
        )
    for index in range(6):
        rows.append(
            _episode(
                role_family="R2_handling_limit_drift_capable_avoidance",
                scenario_family_id="R2",
                outcome_bucket="collision_failure",
                termination_reason="obstacle_collision",
                collision=True,
                index=100 + index,
            )
        )
    for index in range(30):
        rows.append(
            _episode(
                role_family="R1_aeb_infeasible_stable_aes",
                scenario_family_id="R1",
                outcome_bucket="collision_failure",
                termination_reason="obstacle_collision",
                collision=True,
                index=index,
            )
        )
    for index in range(30):
        rows.append(
            _episode(
                role_family="R4_unavoidable_mitigation",
                scenario_family_id="R4",
                outcome_bucket="collision_failure",
                termination_reason="obstacle_collision",
                collision=True,
                index=index,
            )
        )

    summary_path = tmp_path / "summary.json"
    episode_rows_path = tmp_path / "episode_rows.csv"
    write_json(summary_path, {"result_class": "current_sim_dual_axis_repaired_pack_measured_execution_pass"})
    write_csv_rows(episode_rows_path, rows)
    return summary_path, episode_rows_path


def test_measured_outcome_localization_routes_target_guardrail_and_r4_semantics(tmp_path: Path) -> None:
    summary_path, episode_rows_path = _inputs(tmp_path)

    summary = run_measured_outcome_localization(
        summary_path=summary_path,
        episode_rows_path=episode_rows_path,
        output_dir=tmp_path / "out",
        target_episode_count=120,
        minimum_slice_episode_count=30,
        offtrack_target_threshold=0.70,
        high_priority_offtrack_threshold=0.85,
        collision_guardrail_threshold=0.15,
    )

    assert summary["result_class"] == "current_sim_dual_axis_measured_outcome_localization_pass"
    assert summary["source_episode_count"] == 120
    assert summary["offtrack_target_slice_count"] > 0
    assert summary["collision_guardrail_slice_count"] > 0
    assert summary["r4_mitigation_semantics_slice_count"] > 0
    assert summary["high_priority_offtrack_slice_count"] > 0
    assert summary["ranking_admissible_count"] == 0
    assert summary["winner_selected_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_rollout_started"] is False
    assert summary["policy_action_executed"] is False
    assert summary["training_started"] is False
    assert summary["paper_level_claim_made"] is False
    assert summary["finite_window_vs_gru_conclusion_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    slice_rows = read_csv_rows(tmp_path / "out" / "slice_rows.csv")
    r2_row = next(row for row in slice_rows if row["slice_axis"] == "role_family" and row["slice_value"].startswith("R2_"))
    assert r2_row["route_class"] == "offtrack_target_with_collision_guardrail"
    assert r2_row["is_offtrack_target"] == "True"
    assert r2_row["is_collision_guardrail"] == "True"

    r4_family_row = next(row for row in slice_rows if row["slice_axis"] == "role_family" and row["slice_value"].startswith("R4_"))
    assert r4_family_row["route_class"] == "r4_mitigation_semantics"
    assert r4_family_row["is_collision_guardrail"] == "False"

    r4_scenario_row = next(row for row in slice_rows if row["slice_axis"] == "scenario_family_id" and row["slice_value"] == "R4")
    assert r4_scenario_row["route_class"] == "r4_mitigation_semantics"

    claim_boundary = (tmp_path / "out" / "claim_boundary.csv").read_text(encoding="utf-8")
    assert "controller_family_ranking,False" in claim_boundary
    assert "scenario_redesign_executed,False" in claim_boundary
    assert "training_repair_success,False" in claim_boundary

    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["artifacts"]["offtrack_target_slice_rows"].endswith("offtrack_target_slice_rows.csv")


def test_measured_outcome_localization_fails_closed_on_episode_count_mismatch(tmp_path: Path) -> None:
    summary_path, episode_rows_path = _inputs(tmp_path)

    summary = run_measured_outcome_localization(
        summary_path=summary_path,
        episode_rows_path=episode_rows_path,
        output_dir=tmp_path / "out",
        target_episode_count=121,
    )

    assert summary["result_class"] == "current_sim_dual_axis_measured_outcome_localization_incomplete_or_fail"
    assert summary["source_episode_count"] == 120
    assert summary["target_episode_count"] == 121
    assert summary["paper_level_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
