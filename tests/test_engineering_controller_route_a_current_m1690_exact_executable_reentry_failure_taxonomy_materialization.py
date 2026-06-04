from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift import (
    engineering_controller_route_a_current_m1690_exact_executable_reentry_failure_taxonomy_materialization as m2719,
)


def _write_m2716_source(root: Path) -> None:
    root.mkdir()
    write_json(
        root / "summary.json",
        {
            "status_pass": True,
            "exact_execution_row_count": 4,
            "protected_proposal_exclusion_audit_row_count": 2,
            "gate_matrix_pass": True,
        },
    )
    exact_rows = [
        _exact_row("c1", "anchor-a", "L0_current_masked", success=False, collision=False, termination="off_track"),
        _exact_row("c2", "anchor-a", "L3_online_gru", success=False, collision=True, termination="obstacle_collision"),
        _exact_row("c3", "anchor-b", "L3_reset_control_corrected", success=True, collision=False, termination=""),
        _exact_row("c4", "anchor-b", "L2_window_50_current_tiled", success=False, collision=False, termination="off_track"),
    ]
    write_csv_rows(root / "exact_execution_rows.csv", exact_rows)
    write_csv_rows(
        root / "profile_aggregate.csv",
        [
            {"group_key": "L0_current_masked", "diagnostic_only_no_verdict": True, "ranking_claim_made": False},
            {"group_key": "L3_online_gru", "diagnostic_only_no_verdict": True, "ranking_claim_made": False},
        ],
    )
    write_csv_rows(
        root / "anchor_aggregate.csv",
        [
            {"group_key": "anchor-a", "diagnostic_only_no_verdict": True},
            {"group_key": "anchor-b", "diagnostic_only_no_verdict": True},
        ],
    )
    write_csv_rows(
        root / "protected_proposal_exclusion_audit_rows.csv",
        [
            {
                "exclusion_id": f"protected-{index}",
                "support_candidate_id": f"support-{index}",
                "proposed_workload_id": f"protected-workload-{index}",
                "profile_name": "L3_online_gru",
                "m2716_execution_candidate": False,
                "m2716_execution_admitted": False,
                "m2716_execution_run": False,
                "protected_rows_in_success_denominator": False,
            }
            for index in range(1, 3)
        ],
    )
    write_csv_rows(
        root / "actor_contract_join_rows.csv",
        [
            {"contract_field": "observation_shape", "status_pass": True},
            {"contract_field": "action_shape", "status_pass": True},
        ],
    )
    write_csv_rows(root / "claim_boundary_rows.csv", [{"claim_id": "claim", "status_pass": True}])
    write_csv_rows(root / "gate_matrix.csv", [{"gate_id": "gate", "status_pass": True}])


def _exact_row(candidate_id: str, anchor: str, profile: str, *, success: bool, collision: bool, termination: str) -> dict:
    return {
        "candidate_id": candidate_id,
        "anchor_task_source_id": anchor,
        "workload_id": f"{anchor}::{profile}",
        "task_source_id": anchor,
        "profile_name": profile,
        "task_family": "T4",
        "success": success,
        "collision": collision,
        "termination_reason": termination,
        "hidden_oracle_actor_input_required": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "ranking_run": False,
        "driver_performance_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "level3_self_id_claim_made": False,
    }


def test_m2719_materializes_taxonomy_without_execution_or_ranking(monkeypatch, tmp_path: Path) -> None:
    m2716_dir = tmp_path / "m2716"
    output_dir = tmp_path / "m2719"
    doc_path = tmp_path / "m2719.md"
    synthesis = tmp_path / "m2718.md"
    follow_up = tmp_path / "m2720.json"
    _write_m2716_source(m2716_dir)
    synthesis.write_text(
        "continue_to_current_m1690_exact_executable_reentry_failure_taxonomy_materialization_preflight\n",
        encoding="utf-8",
    )
    write_json(follow_up, {"id": "m2720"})
    monkeypatch.setattr(m2719, "EXPECTED_EXACT_EXECUTION_ROW_COUNT", 4)
    monkeypatch.setattr(m2719, "EXPECTED_PROTECTED_EXCLUSION_ROW_COUNT", 2)
    monkeypatch.setattr(m2719, "EXPECTED_DIAGNOSTIC_SUCCESS_ROW_COUNT", 1)
    monkeypatch.setattr(m2719, "EXPECTED_OBSTACLE_COLLISION_ROW_COUNT", 1)
    monkeypatch.setattr(m2719, "EXPECTED_OFFTRACK_ROW_COUNT", 2)

    summary = m2719.materialize_current_m1690_exact_executable_reentry_failure_taxonomy(
        m2716_dir=m2716_dir,
        m2718_synthesis=synthesis,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["exact_execution_taxonomy_row_count"] == 4
    assert summary["protected_exclusion_taxonomy_row_count"] == 2
    assert summary["diagnostic_success_taxonomy_row_count"] == 1
    assert summary["obstacle_collision_taxonomy_row_count"] == 1
    assert summary["offtrack_taxonomy_row_count"] == 2
    assert summary["profile_ranking_allowed"] is False
    assert summary["protected_execution_run"] is False
    assert summary["environment_reset_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert read_json(output_dir / "summary.json") == summary

    taxonomy_rows = m2719.read_csv_rows(output_dir / "taxonomy_rows.csv")
    assert {row["taxonomy_family"] for row in taxonomy_rows} == {
        "diagnostic_success",
        "obstacle_collision",
        "off_track",
        "protected_excluded",
    }
    assert {row["profile_ranking_allowed"] for row in taxonomy_rows} == {"False"}
    profile_rows = m2719.read_csv_rows(output_dir / "profile_taxonomy_context_rows.csv")
    assert {row["winner_selection_allowed"] for row in profile_rows} == {"False"}
    gate_rows = m2719.read_csv_rows(output_dir / "gate_matrix.csv")
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.exists()
