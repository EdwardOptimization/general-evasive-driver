from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift import (
    engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_target_panel_materialization as m2721,
)


def _write_m2719_source(root: Path) -> None:
    root.mkdir()
    write_json(
        root / "summary.json",
        {
            "status_pass": True,
            "offtrack_taxonomy_row_count": 2,
            "obstacle_collision_taxonomy_row_count": 1,
            "diagnostic_success_taxonomy_row_count": 1,
            "protected_excluded_taxonomy_row_count": 2,
            "gate_matrix_pass": True,
        },
    )
    taxonomy_rows = [
        _taxonomy("t1", "c1", "anchor-a", "L0_current_masked", "off_track"),
        _taxonomy("t2", "c2", "anchor-a", "L3_online_gru", "obstacle_collision"),
        _taxonomy("t3", "c3", "anchor-b", "L3_reset_control_corrected", "diagnostic_success"),
        _taxonomy("t4", "c4", "anchor-b", "L2_window_50_current_tiled", "off_track"),
        _taxonomy("t5", "p1", "", "L3_online_gru", "protected_excluded", source_type="protected_proposal_exclusion"),
        _taxonomy("t6", "p2", "", "L3_online_gru", "protected_excluded", source_type="protected_proposal_exclusion"),
    ]
    write_csv_rows(root / "taxonomy_rows.csv", taxonomy_rows)
    write_csv_rows(root / "taxonomy_aggregate_rows.csv", [{"aggregate_id": "a", "status_pass": True}])
    write_csv_rows(root / "profile_taxonomy_context_rows.csv", [{"profile_name": "L0_current_masked"}])
    write_csv_rows(root / "anchor_taxonomy_context_rows.csv", [{"anchor_task_source_id": "anchor-a"}])
    write_csv_rows(root / "actor_contract_join_rows.csv", [{"contract_field": "observation_shape", "status_pass": True}])
    write_csv_rows(root / "claim_boundary_rows.csv", [{"claim_id": "claim", "status_pass": True}])
    write_csv_rows(root / "gate_matrix.csv", [{"gate_id": "gate", "status_pass": True}])


def _taxonomy(
    taxonomy_id: str,
    candidate_id: str,
    anchor: str,
    profile: str,
    family: str,
    *,
    source_type: str = "exact_execution",
) -> dict:
    return {
        "taxonomy_id": taxonomy_id,
        "source_row_type": source_type,
        "candidate_id": candidate_id,
        "anchor_task_source_id": anchor,
        "workload_id": f"{anchor}::{profile}" if anchor else candidate_id,
        "task_source_id": anchor,
        "profile_name": profile,
        "task_family": "T4",
        "taxonomy_family": family,
        "profile_ranking_allowed": False,
        "protected_rows_in_success_denominator": False,
        "taxonomy_labels_actor_visible": False,
    }


def test_m2721_materializes_offtrack_panel_without_execution_or_ranking(monkeypatch, tmp_path: Path) -> None:
    m2719_dir = tmp_path / "m2719"
    output_dir = tmp_path / "m2721"
    doc_path = tmp_path / "m2721.md"
    audit = tmp_path / "m2720.md"
    follow_up = tmp_path / "m2722.json"
    _write_m2719_source(m2719_dir)
    audit.write_text(
        "accept_m2719_route_to_current_m1690_exact_executable_reentry_offtrack_repair_target_panel_materialization\n",
        encoding="utf-8",
    )
    write_json(follow_up, {"id": "m2722"})
    monkeypatch.setattr(m2721, "EXPECTED_OFFTRACK_TARGET_COUNT", 2)
    monkeypatch.setattr(m2721, "EXPECTED_COLLISION_CAUTION_COUNT", 1)
    monkeypatch.setattr(m2721, "EXPECTED_SUCCESS_CONTEXT_COUNT", 1)
    monkeypatch.setattr(m2721, "EXPECTED_PROTECTED_EXCLUSION_COUNT", 2)

    summary = m2721.materialize_offtrack_repair_target_panel(
        m2719_dir=m2719_dir,
        m2720_audit=audit,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["offtrack_target_row_count"] == 2
    assert summary["collision_caution_row_count"] == 1
    assert summary["diagnostic_success_context_row_count"] == 1
    assert summary["protected_exclusion_row_count"] == 2
    assert summary["environment_reset_run"] is False
    assert summary["profile_ranking_allowed"] is False
    assert summary["driver_performance_claim_made"] is False
    assert read_json(output_dir / "summary.json") == summary

    target_rows = m2721.read_csv_rows(output_dir / "offtrack_target_rows.csv")
    assert len(target_rows) == 2
    assert {row["target_panel_admitted"] for row in target_rows} == {"True"}
    protected_rows = m2721.read_csv_rows(output_dir / "protected_exclusion_rows.csv")
    assert {row["target_panel_admitted"] for row in protected_rows} == {"False"}
    assert {row["protected_rows_in_success_denominator"] for row in protected_rows} == {"False"}
    gate_rows = m2721.read_csv_rows(output_dir / "gate_matrix.csv")
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.exists()
