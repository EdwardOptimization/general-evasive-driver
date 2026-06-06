from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
import autodrift.engineering_controller_route_a_offtrack_dominant_tradeoff_aware_repair_redesign_materialization_preflight as m2937


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _outcome_row(
    *,
    index: int,
    panel_family: str,
    baseline: str,
    repair: str,
    offtrack_persisted: bool = False,
    offtrack_regressed: bool = False,
    context_regressed: bool = False,
    positive: bool = False,
    context_preserved: bool = False,
) -> dict[str, object]:
    return {
        "outcome_shift_id": f"shift-{index}",
        "panel_row_id": f"panel-{index}",
        "panel_row_family": panel_family,
        "source_milestone": "m1" if index <= 4 else "m2",
        "source_family": "fixture",
        "source_edge": "fixture_edge",
        "source_row_id": f"source-{index}",
        "task_family": "T4" if index % 2 else "T5",
        "task_source_id": f"task-{index}",
        "workload_id": f"workload-{index}",
        "profile_name": "L3_online_gru",
        "env_template_family": "fixture_env",
        "window_tag": "fixture_window",
        "checkpoint_context": "fixture_checkpoint",
        "m2919_outcome_family": baseline,
        "m2931_outcome_family": repair,
        "transition_bucket": f"{baseline}->{repair}",
        "transition_family": "fixture_transition_family",
        "offtrack_persisted": offtrack_persisted,
        "offtrack_regressed_to_collision_or_speed": offtrack_regressed,
        "context_regressed_to_offtrack_or_collision": context_regressed,
        "offtrack_repaired_to_success": positive,
        "context_preserved_success": context_preserved,
    }


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m2934_dir = root / "m2934"
    m2935_audit = root / "m2935.md"
    m2936_design = root / "m2936.md"
    rows = [
        _outcome_row(
            index=1,
            panel_family="offtrack_repair_target",
            baseline="offtrack",
            repair="offtrack",
            offtrack_persisted=True,
        ),
        _outcome_row(
            index=2,
            panel_family="offtrack_repair_target",
            baseline="offtrack",
            repair="offtrack",
            offtrack_persisted=True,
        ),
        _outcome_row(
            index=3,
            panel_family="offtrack_repair_target",
            baseline="offtrack",
            repair="collision",
            offtrack_regressed=True,
        ),
        _outcome_row(
            index=4,
            panel_family="offtrack_repair_target",
            baseline="offtrack",
            repair="speed_too_low",
            offtrack_regressed=True,
        ),
        _outcome_row(
            index=5,
            panel_family="offtrack_repair_target",
            baseline="offtrack",
            repair="success",
            positive=True,
        ),
        _outcome_row(
            index=6,
            panel_family="non_offtrack_context_regression",
            baseline="success",
            repair="offtrack",
            context_regressed=True,
        ),
        _outcome_row(
            index=7,
            panel_family="non_offtrack_context_regression",
            baseline="success",
            repair="success",
            context_preserved=True,
        ),
    ]
    write_json(m2934_dir / "summary.json", {"status_pass": True, "gate_matrix_pass": True})
    write_csv_rows(m2934_dir / "outcome_shift_rows.csv", rows)
    write_csv_rows(
        m2934_dir / "offtrack_target_shift_rows.csv",
        [row for row in rows if row["panel_row_family"] == "offtrack_repair_target"],
    )
    write_csv_rows(
        m2934_dir / "context_regression_rows.csv",
        [row for row in rows if str(row["panel_row_family"]).startswith("non_offtrack_context")],
    )
    write_csv_rows(m2934_dir / "gate_matrix.csv", [{"gate_id": "fixture", "status_pass": True}])
    m2935_audit.write_text("M2935 accepts M2934 complete claim-safe localization.\n", encoding="utf-8")
    m2936_design.write_text(
        "\n".join(
            [
                "# M2936",
                "- decision: `admit_m2937_tradeoff_aware_repair_redesign_materialization_preflight`",
                f"- next: `{m2937.MILESTONE_ID}`",
            ]
        ),
        encoding="utf-8",
    )
    return {"m2934_dir": m2934_dir, "m2935_audit": m2935_audit, "m2936_design": m2936_design}


def test_tradeoff_aware_materialization_writes_no_execution_constraint_artifacts(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(m2937, "EXPECTED_PANEL_ROW_COUNT", 7)
    monkeypatch.setattr(m2937, "EXPECTED_OFFTRACK_TARGET_COUNT", 5)
    monkeypatch.setattr(m2937, "EXPECTED_CONTEXT_ROW_COUNT", 2)
    monkeypatch.setattr(m2937, "EXPECTED_PERSISTENT_OFFTRACK_COUNT", 2)
    monkeypatch.setattr(m2937, "EXPECTED_COLLISION_SPEED_SUBSTITUTION_COUNT", 2)
    monkeypatch.setattr(m2937, "EXPECTED_CONTEXT_RETENTION_CONSTRAINT_COUNT", 1)
    monkeypatch.setattr(m2937, "EXPECTED_POSITIVE_REFERENCE_COUNT", 1)
    monkeypatch.setattr(
        m2937,
        "EXPECTED_TRANSITION_COUNTS",
        {
            "offtrack->offtrack": 2,
            "offtrack->collision": 1,
            "offtrack->speed_too_low": 1,
            "offtrack->success": 1,
            "success->offtrack": 1,
            "success->success": 1,
        },
    )
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m2937"
    doc_path = tmp_path / "m2937.md"
    follow_up = tmp_path / "m2938.json"

    summary = m2937.run_tradeoff_aware_repair_redesign_materialization_preflight(
        m2934_dir=paths["m2934_dir"],
        m2935_audit=paths["m2935_audit"],
        m2936_design=paths["m2936_design"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["transition_constraint_row_count"] == 7
    assert summary["offtrack_persistence_constraint_row_count"] == 2
    assert summary["collision_speed_substitution_constraint_row_count"] == 2
    assert summary["context_retention_constraint_row_count"] == 1
    assert summary["positive_transition_reference_row_count"] == 1
    assert summary["candidate_surface_row_count"] == 5
    assert summary["environment_reset_run"] is False
    assert summary["training_run"] is False
    assert summary["repair_success_claim_made"] is False
    assert summary["driver_performance_claim_made"] is False
    assert doc_path.exists()
    assert read_json(follow_up)["id"] == m2937.NEXT_ID

    transition_rows = _read_csv(output_dir / "transition_constraint_rows.csv")
    candidate_rows = _read_csv(output_dir / "candidate_surface_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")
    assert len(transition_rows) == 7
    assert {row["actor_visible"] for row in transition_rows} == {"False"}
    assert {row["ranking_claim_made"] for row in transition_rows} == {"False"}
    assert {row["execution_scheduled"] for row in candidate_rows} == {"False"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
