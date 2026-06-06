from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
import autodrift.engineering_controller_route_a_offtrack_dominant_repair_execution_outcome_shift_localization_preflight as m2934


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _episode(
    *,
    candidate_id: str,
    repair_candidate_id: str = "",
    success: bool = False,
    collision: bool = False,
    termination_reason: str = "",
    source_milestone: str = "m1",
    task_family: str = "T4",
    source_row_id: str = "",
) -> dict[str, object]:
    row = {
        "execution_candidate_id": candidate_id,
        "repair_execution_candidate_id": repair_candidate_id,
        "success": success,
        "collision": collision,
        "termination_reason": termination_reason,
        "min_clearance_margin": 1.0,
        "return": 2.0,
        "speed_mean": 3.0,
        "source_milestone": source_milestone,
        "task_family": task_family,
        "source_row_id": source_row_id or candidate_id,
    }
    if repair_candidate_id:
        row["panel_row_id"] = repair_candidate_id.replace("repair", "panel")
    return row


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m2919_dir = root / "m2919"
    m2925_dir = root / "m2925"
    m2928_dir = root / "m2928"
    m2931_dir = root / "m2931"

    baseline_rows = [
        _episode(candidate_id="base-1", termination_reason="off_track", source_milestone="m1", task_family="T4"),
        _episode(candidate_id="base-2", termination_reason="off_track", source_milestone="m1", task_family="T4"),
        _episode(candidate_id="base-3", termination_reason="off_track", source_milestone="m1", task_family="T5"),
        _episode(candidate_id="base-4", success=True, source_milestone="m2", task_family="T4"),
        _episode(candidate_id="base-5", collision=True, termination_reason="obstacle_collision", source_milestone="m2", task_family="T5"),
    ]
    repair_rows = [
        _episode(candidate_id="", repair_candidate_id="repair-1", success=True, source_milestone="m1", task_family="T4"),
        _episode(candidate_id="", repair_candidate_id="repair-2", termination_reason="off_track", source_milestone="m1", task_family="T4"),
        _episode(candidate_id="", repair_candidate_id="repair-3", collision=True, termination_reason="obstacle_collision", source_milestone="m1", task_family="T5"),
        _episode(candidate_id="", repair_candidate_id="repair-4", termination_reason="off_track", source_milestone="m2", task_family="T4"),
        _episode(candidate_id="", repair_candidate_id="repair-5", collision=True, termination_reason="obstacle_collision", source_milestone="m2", task_family="T5"),
    ]
    candidate_rows = []
    for index in range(1, 6):
        offtrack_target = index <= 3
        candidate_rows.append(
            {
                "repair_execution_candidate_id": f"repair-{index}",
                "panel_row_id": f"panel-{index}",
                "panel_row_family": "offtrack_repair_target" if offtrack_target else "non_offtrack_context",
                "source_milestone": "m1" if index <= 3 else "m2",
                "source_family": "fixture",
                "source_edge": "edge",
                "source_row_id": f"source-{index}",
                "task_family": "T4" if index in {1, 2, 4} else "T5",
                "task_source_id": f"task-{index}",
                "workload_id": f"workload-{index}",
                "profile_name": "L3_online_gru",
                "m2919_execution_candidate_id": f"base-{index}",
                "m2919_resolution_id": f"resolution-{index}",
                "original_checkpoint_context": "fixture_checkpoint",
                "env_template_family": "fixture_env",
                "window_tag": "fixture_window",
            }
        )

    write_json(m2919_dir / "summary.json", {"status_pass": True, "gate_matrix_pass": True})
    write_csv_rows(m2919_dir / "bounded_execution_rows.csv", baseline_rows)
    write_json(
        m2925_dir / "summary.json",
        {"status_pass": True, "gate_matrix_pass": True, "offtrack_row_count": 3, "non_offtrack_context_row_count": 2},
    )
    write_csv_rows(m2925_dir / "offtrack_slice_rows.csv", [{"id": f"off-{i}"} for i in range(3)])
    write_csv_rows(m2925_dir / "non_offtrack_context_rows.csv", [{"id": f"ctx-{i}"} for i in range(2)])
    write_json(m2928_dir / "summary.json", {"status_pass": True, "gate_matrix_pass": True})
    write_csv_rows(
        m2928_dir / "coverage_constraint_rows.csv",
        [
            {
                "coverage_constraint_id": "coverage-1",
                "coverage_family": "denominator",
                "coverage_value": "total",
                "observed_row_count": 5,
                "expected_row_count": 5,
                "source_scope": "fixture",
                "coverage_constraint_status_pass": True,
                "ranking_claim_made": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "high_fidelity_readiness_allowed": False,
                "self_id_claim_allowed": False,
                "actor_visible": False,
                "diagnostic_only_no_verdict": True,
            }
        ],
    )
    write_csv_rows(m2928_dir / "shortcut_exclusion_rows.csv", [{"shortcut_family": "fixture_shortcut", "status_pass": True}])
    write_json(
        m2931_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "diagnostic_success_count": 1,
            "diagnostic_collision_count": 2,
            "diagnostic_offtrack_count": 2,
            "diagnostic_speed_too_low_count": 0,
        },
    )
    write_csv_rows(m2931_dir / "repair_execution_candidate_rows.csv", candidate_rows)
    write_csv_rows(m2931_dir / "repair_execution_rows.csv", repair_rows)
    write_csv_rows(m2931_dir / "repair_execution_failure_rows.csv", [])
    write_csv_rows(m2931_dir / "repair_target_context_rows.csv", [{"id": f"target-{i}"} for i in range(5)])
    write_csv_rows(
        m2931_dir / "guardrail_context_rows.csv",
        [
            {"guardrail_family": "route_b_context_only", "execution_run": False},
            {"guardrail_family": "route_c_source_unavailable_rows", "execution_run": False},
            {"guardrail_family": "m2877_fixed_post_package_rows", "execution_run": False},
        ],
    )
    for name in ["actor_contract_guard_rows.csv", "claim_boundary_rows.csv", "gate_matrix.csv"]:
        write_csv_rows(m2931_dir / name, [{"id": "placeholder", "status_pass": True}])

    m2932_audit = root / "m2932.md"
    m2933_synthesis = root / "m2933.md"
    m2932_audit.write_text("M2932 accepts M2931 complete claim-safe diagnostics.\n", encoding="utf-8")
    m2933_synthesis.write_text(
        "\n".join(["# M2933", "- synthesis decision: `continue`", f"- next: `{m2934.MILESTONE_ID}`"]),
        encoding="utf-8",
    )
    return {
        "m2919_dir": m2919_dir,
        "m2925_dir": m2925_dir,
        "m2928_dir": m2928_dir,
        "m2931_dir": m2931_dir,
        "m2932_audit": m2932_audit,
        "m2933_synthesis": m2933_synthesis,
    }


def test_outcome_shift_localization_materializes_no_execution_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m2934, "EXPECTED_PANEL_ROW_COUNT", 5)
    monkeypatch.setattr(m2934, "EXPECTED_OFFTRACK_TARGET_COUNT", 3)
    monkeypatch.setattr(m2934, "EXPECTED_CONTEXT_ROW_COUNT", 2)
    monkeypatch.setattr(m2934, "EXPECTED_COVERAGE_CONSTRAINT_COUNT", 1)
    monkeypatch.setattr(m2934, "EXPECTED_SHORTCUT_EXCLUSION_COUNT", 1)
    monkeypatch.setattr(m2934, "EXPECTED_M2919_OUTCOME_COUNTS", {"offtrack": 3, "success": 1, "collision": 1})
    monkeypatch.setattr(m2934, "EXPECTED_M2931_OUTCOME_COUNTS", {"success": 1, "offtrack": 2, "collision": 2})
    monkeypatch.setattr(
        m2934,
        "EXPECTED_M2931_DIAGNOSTIC_COUNTS",
        {"success": 1, "collision": 2, "offtrack": 2, "speed_too_low": 0},
    )
    monkeypatch.setattr(
        m2934,
        "EXPECTED_TRANSITION_COUNTS",
        {
            "offtrack->success": 1,
            "offtrack->offtrack": 1,
            "offtrack->collision": 1,
            "success->offtrack": 1,
            "collision->collision": 1,
        },
    )
    monkeypatch.setattr(m2934, "EXPECTED_PANEL_SOURCE_COUNTS", {"m1": 3, "m2": 2})
    monkeypatch.setattr(m2934, "EXPECTED_PANEL_TASK_COUNTS", {"T4": 3, "T5": 2})
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m2934"
    doc_path = tmp_path / "m2934.md"
    follow_up = tmp_path / "m2935.json"

    summary = m2934.run_outcome_shift_localization_preflight(
        m2919_dir=paths["m2919_dir"],
        m2925_dir=paths["m2925_dir"],
        m2928_dir=paths["m2928_dir"],
        m2931_dir=paths["m2931_dir"],
        m2932_audit=paths["m2932_audit"],
        m2933_synthesis=paths["m2933_synthesis"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["outcome_shift_row_count"] == 5
    assert summary["offtrack_target_shift_row_count"] == 3
    assert summary["context_regression_row_count"] == 2
    assert summary["transition_counts"]["offtrack->success"] == 1
    assert summary["offtrack_regression_or_substitution_count"] == 1
    assert summary["success_context_regression_to_offtrack_or_collision_count"] == 1
    assert summary["environment_reset_run"] is False
    assert summary["training_run"] is False
    assert summary["repair_success_claim_made"] is False
    assert summary["driver_performance_claim_made"] is False
    assert doc_path.exists()
    assert read_json(follow_up)["id"] == m2934.NEXT_ID

    shift_rows = _read_csv(output_dir / "outcome_shift_rows.csv")
    offtrack_rows = _read_csv(output_dir / "offtrack_target_shift_rows.csv")
    context_rows = _read_csv(output_dir / "context_regression_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")
    assert len(shift_rows) == 5
    assert len(offtrack_rows) == 3
    assert len(context_rows) == 2
    assert {row["execution_performed_by_m2934"] for row in shift_rows} == {"False"}
    assert {row["repair_success_claim_made"] for row in shift_rows} == {"False"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
