from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
import autodrift.engineering_controller_route_a_offtrack_dominant_repair_admission_materialization_preflight as m2928


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m2925_dir = root / "m2925"
    offtrack_rows = [
        {
            "offtrack_slice_id": "offtrack-1",
            "source_milestone": "m2737",
            "task_family": "T4",
            "checkpoint_context": "public_pilot_l3_checkpoint",
            "env_template_family": "env_a",
            "window_tag": "window_a",
            "offtrack_severity_band": "low_overshoot_le_0p02",
            "time_to_offtrack_band": "early_le_1p75s",
            "m2925_execution_performed": False,
            "ranking_claim_made": False,
            "diagnostic_only_no_verdict": True,
        },
        {
            "offtrack_slice_id": "offtrack-2",
            "source_milestone": "m2737",
            "task_family": "T5",
            "checkpoint_context": "m2655_mitigation_preserving_checkpoint",
            "env_template_family": "env_b",
            "window_tag": "window_b",
            "offtrack_severity_band": "medium_overshoot_le_0p08",
            "time_to_offtrack_band": "mid_le_2p5s",
            "m2925_execution_performed": False,
            "ranking_claim_made": False,
            "diagnostic_only_no_verdict": True,
        },
        {
            "offtrack_slice_id": "offtrack-3",
            "source_milestone": "m2746",
            "task_family": "T5",
            "checkpoint_context": "m2655_mitigation_preserving_checkpoint",
            "env_template_family": "env_b",
            "window_tag": "window_b",
            "offtrack_severity_band": "high_overshoot_gt_0p08",
            "time_to_offtrack_band": "late_gt_2p5s",
            "m2925_execution_performed": False,
            "ranking_claim_made": False,
            "diagnostic_only_no_verdict": True,
        },
    ]
    context_rows = [
        {
            "context_row_id": "context-1",
            "outcome_family": "diagnostic_success",
            "source_milestone": "m2737",
            "task_family": "T4",
            "m2925_execution_performed": False,
            "ranking_claim_made": False,
            "diagnostic_only_no_verdict": True,
        },
        {
            "context_row_id": "context-2",
            "outcome_family": "speed_too_low",
            "source_milestone": "m2746",
            "task_family": "T4",
            "m2925_execution_performed": False,
            "ranking_claim_made": False,
            "diagnostic_only_no_verdict": True,
        },
    ]
    guardrail_rows = [
        {"guardrail_family": "route_b_context_only", "execution_run": False},
        {"guardrail_family": "route_c_source_unavailable_rows", "execution_run": False},
        {"guardrail_family": "m2877_fixed_post_package_rows", "execution_run": False},
    ]
    write_json(
        m2925_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "offtrack_row_count": 3,
            "non_offtrack_context_row_count": 2,
            "guardrail_context_row_count": 3,
            "offtrack_source_counts": {"m2737": 2, "m2746": 1},
            "offtrack_task_counts": {"T4": 1, "T5": 2},
            "offtrack_checkpoint_context_counts": {
                "public_pilot_l3_checkpoint": 1,
                "m2655_mitigation_preserving_checkpoint": 2,
            },
            "offtrack_environment_counts": {"env_a": 1, "env_b": 2},
            "offtrack_window_counts": {"window_a": 1, "window_b": 2},
            "offtrack_overshoot_band_counts": {
                "low_overshoot_le_0p02": 1,
                "medium_overshoot_le_0p08": 1,
                "high_overshoot_gt_0p08": 1,
            },
            "offtrack_time_band_counts": {
                "early_le_1p75s": 1,
                "mid_le_2p5s": 1,
                "late_gt_2p5s": 1,
            },
        },
    )
    write_csv_rows(m2925_dir / "offtrack_slice_rows.csv", offtrack_rows)
    write_csv_rows(m2925_dir / "non_offtrack_context_rows.csv", context_rows)
    write_csv_rows(m2925_dir / "guardrail_context_rows.csv", guardrail_rows)
    for name in ["actor_contract_guard_rows.csv", "claim_boundary_rows.csv", "gate_matrix.csv"]:
        write_csv_rows(m2925_dir / name, [{"id": "placeholder", "status_pass": True}])

    m2926_audit = root / "m2926.md"
    m2927_synthesis = root / "m2927.md"
    m2926_audit.write_text("M2926 accepts M2925 complete and claim-safe.\n", encoding="utf-8")
    m2927_synthesis.write_text(
        "\n".join(
            [
                "# M2927",
                "- synthesis decision: `continue`",
                f"- next: `{m2928.MILESTONE_ID}`",
            ]
        ),
        encoding="utf-8",
    )
    return {
        "m2925_dir": m2925_dir,
        "m2926_audit": m2926_audit,
        "m2927_synthesis": m2927_synthesis,
    }


def test_shortcut_rows_cover_required_families() -> None:
    rows = m2928.build_shortcut_exclusion_rows()
    families = {row["shortcut_family"] for row in rows}
    excluded_text = " ".join(str(row["excluded_signal_or_claim"]) for row in rows)
    assert m2928.REQUIRED_SHORTCUT_FAMILIES.issubset(families)
    assert "oracle" in excluded_text
    assert "speed_ref" in excluded_text
    assert "performance" in excluded_text
    assert {row["actor_visible"] for row in rows} == {False}
    assert {row["status_pass"] for row in rows} == {True}


def test_run_materialization_writes_repair_admission_without_execution(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m2928, "EXPECTED_TOTAL_ROW_COUNT", 5)
    monkeypatch.setattr(m2928, "EXPECTED_OFFTRACK_COUNT", 3)
    monkeypatch.setattr(m2928, "EXPECTED_NON_OFFTRACK_CONTEXT_COUNT", 2)
    monkeypatch.setattr(m2928, "EXPECTED_OFFTRACK_SOURCE_COUNTS", {"m2737": 2, "m2746": 1})
    monkeypatch.setattr(m2928, "EXPECTED_OFFTRACK_TASK_COUNTS", {"T4": 1, "T5": 2})
    monkeypatch.setattr(
        m2928,
        "EXPECTED_CHECKPOINT_CONTEXT_COUNTS",
        {"public_pilot_l3_checkpoint": 1, "m2655_mitigation_preserving_checkpoint": 2},
    )
    monkeypatch.setattr(m2928, "EXPECTED_ENVIRONMENT_COUNTS", {"env_a": 1, "env_b": 2})
    monkeypatch.setattr(m2928, "EXPECTED_WINDOW_COUNTS", {"window_a": 1, "window_b": 2})
    monkeypatch.setattr(
        m2928,
        "EXPECTED_OVERSHOOT_BAND_COUNTS",
        {"low_overshoot_le_0p02": 1, "medium_overshoot_le_0p08": 1, "high_overshoot_gt_0p08": 1},
    )
    monkeypatch.setattr(
        m2928,
        "EXPECTED_TIME_BAND_COUNTS",
        {"early_le_1p75s": 1, "mid_le_2p5s": 1, "late_gt_2p5s": 1},
    )
    monkeypatch.setattr(m2928, "EXPECTED_GUARDRAIL_CONTEXT_ROW_COUNT", 3)
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m2928"
    doc_path = tmp_path / "m2928.md"
    follow_up = tmp_path / "m2929.json"

    summary = m2928.run_offtrack_dominant_repair_admission_materialization_preflight(
        m2925_dir=paths["m2925_dir"],
        m2926_audit=paths["m2926_audit"],
        m2927_synthesis=paths["m2927_synthesis"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["denominator_total_row_count"] == 5
    assert summary["offtrack_row_count"] == 3
    assert summary["non_offtrack_context_row_count"] == 2
    assert summary["repair_hypothesis_row_count"] == 4
    assert summary["coverage_constraint_rows_pass"] is True
    assert summary["guardrails_preserved"] is True
    assert summary["environment_reset_run"] is False
    assert summary["policy_rollout_run"] is False
    assert summary["training_run"] is False
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert doc_path.exists()
    assert read_json(follow_up)["id"] == m2928.NEXT_ID

    repair_rows = _read_csv(output_dir / "repair_hypothesis_rows.csv")
    coverage_rows = _read_csv(output_dir / "coverage_constraint_rows.csv")
    shortcut_rows = _read_csv(output_dir / "shortcut_exclusion_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")
    assert len(repair_rows) == 4
    assert len(coverage_rows) == summary["coverage_constraint_row_count"]
    assert {row["execution_scheduled"] for row in repair_rows} == {"False"}
    assert {row["ranking_allowed"] for row in repair_rows} == {"False"}
    assert {row["coverage_constraint_status_pass"] for row in coverage_rows} == {"True"}
    assert {row["ranking_claim_made"] for row in coverage_rows} == {"False"}
    assert "map_or_oracle_progress_metrics" in {row["shortcut_family"] for row in shortcut_rows}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
