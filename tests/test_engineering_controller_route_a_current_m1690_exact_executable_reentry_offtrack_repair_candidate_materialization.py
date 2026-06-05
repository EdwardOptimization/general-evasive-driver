from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift import (
    engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_candidate_materialization as m2725,
)


def _write_m2721_source(root: Path) -> None:
    root.mkdir()
    write_json(
        root / "summary.json",
        {
            "status_pass": True,
            "offtrack_target_row_count": 2,
            "collision_caution_row_count": 1,
            "diagnostic_success_context_row_count": 1,
            "protected_exclusion_row_count": 2,
            "gate_matrix_pass": True,
        },
    )
    write_csv_rows(
        root / "offtrack_target_rows.csv",
        [
            _panel("p1", "c1", "anchor-a", "L0_current_masked", "T4", "off_track", True),
            _panel("p2", "c2", "anchor-b", "L3_online_gru", "T5", "off_track", True),
        ],
    )
    write_csv_rows(root / "collision_caution_rows.csv", [_panel("p3", "c3", "anchor-c", "L0_current_masked", "T4", "obstacle_collision", False)])
    write_csv_rows(
        root / "diagnostic_success_context_rows.csv",
        [_panel("p4", "c4", "anchor-d", "L3_reset_control_corrected", "T5", "diagnostic_success", False)],
    )
    write_csv_rows(
        root / "protected_exclusion_rows.csv",
        [
            _panel("p5", "c5", "", "L3_online_gru", "T4", "protected_excluded", False),
            _panel("p6", "c6", "", "L2_window_50_current_tiled", "T5", "protected_excluded", False),
        ],
    )
    write_csv_rows(root / "actor_contract_join_rows.csv", [{"contract_field": "observation_shape", "status_pass": True}])
    write_csv_rows(root / "claim_boundary_rows.csv", [{"claim_id": "claim", "status_pass": True}])
    write_csv_rows(root / "gate_matrix.csv", [{"gate_id": "gate", "status_pass": True}])


def _panel(
    panel_row_id: str,
    candidate_id: str,
    anchor: str,
    profile: str,
    task_family: str,
    taxonomy_family: str,
    admitted: bool,
) -> dict:
    return {
        "panel_row_id": panel_row_id,
        "candidate_id": candidate_id,
        "anchor_task_source_id": anchor,
        "workload_id": f"{anchor}::{profile}" if anchor else candidate_id,
        "task_source_id": anchor,
        "profile_name": profile,
        "task_family": task_family,
        "taxonomy_family": taxonomy_family,
        "target_panel_admitted": admitted,
        "execution_scheduled": False,
        "target_labels_actor_visible": False,
        "protected_rows_in_success_denominator": False,
        "diagnostic_only_no_verdict": True,
    }


def test_m2725_materializes_candidates_without_execution_or_config_overwrite(monkeypatch, tmp_path: Path) -> None:
    m2721_dir = tmp_path / "m2721"
    output_dir = tmp_path / "m2725"
    doc_path = tmp_path / "m2725.md"
    design = tmp_path / "m2724.md"
    follow_up = tmp_path / "m2726.json"
    _write_m2721_source(m2721_dir)
    design.write_text(
        "admit_current_m1690_exact_executable_reentry_offtrack_repair_candidate_materialization\n",
        encoding="utf-8",
    )
    write_json(follow_up, {"id": "m2726"})
    monkeypatch.setattr(m2725, "EXPECTED_TARGET_COUNT", 2)
    monkeypatch.setattr(m2725, "EXPECTED_COLLISION_GUARDRAIL_COUNT", 1)
    monkeypatch.setattr(m2725, "EXPECTED_SUCCESS_CONTEXT_COUNT", 1)
    monkeypatch.setattr(m2725, "EXPECTED_PROTECTED_EXCLUSION_COUNT", 2)

    summary = m2725.materialize_offtrack_repair_candidates(
        m2724_design=design,
        m2721_dir=m2721_dir,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["candidate_target_row_count"] == 2
    assert summary["collision_guardrail_row_count"] == 1
    assert summary["diagnostic_success_context_guardrail_row_count"] == 1
    assert summary["protected_exclusion_guardrail_row_count"] == 2
    assert summary["active_config_overwritten"] is False
    assert summary["repair_execution_started"] is False
    assert summary["training_run"] is False
    assert summary["actor_input_change"] is False
    assert summary["driver_performance_claim_made"] is False
    assert read_json(output_dir / "summary.json") == summary

    candidate_rows = m2725.read_csv_rows(output_dir / "candidate_target_rows.csv")
    assert len(candidate_rows) == 2
    assert {row["active_config_overwritten"] for row in candidate_rows} == {"False"}
    assert {row["target_labels_actor_visible"] for row in candidate_rows} == {"False"}
    overlay_rows = m2725.read_csv_rows(output_dir / "shared_repair_overlay_rows.csv")
    assert overlay_rows
    assert {row["active_config_overwritten"] for row in overlay_rows} == {"False"}
    guardrail_rows = m2725.read_csv_rows(output_dir / "guardrail_rows.csv")
    assert len(guardrail_rows) == 4
    assert {row["target_panel_admitted"] for row in guardrail_rows} == {"False"}
    gate_rows = m2725.read_csv_rows(output_dir / "gate_matrix.csv")
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.exists()
