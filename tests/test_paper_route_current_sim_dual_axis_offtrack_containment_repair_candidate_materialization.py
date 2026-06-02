from __future__ import annotations

from pathlib import Path
from typing import Any

from autodrift import paper_route_current_sim_dual_axis_offtrack_containment_repair_candidate_materialization as candidates
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _plan_row(*, lever_family: str, plan_route: str = "offtrack_repair_plan") -> dict[str, Any]:
    return {
        "slice_axis": "slice_axis",
        "slice_key": "slice_axis",
        "slice_value": lever_family,
        "episode_count": 20,
        "success_rate": 0.0,
        "offtrack_rate": 0.8,
        "collision_rate": 0.1,
        "dominant_failure_mode": "offtrack_dominated_failure",
        "source_consolidated_route": plan_route,
        "source_actionability_class": "test",
        "plan_route": plan_route,
        "lever_family": lever_family,
        "candidate_levers": "test lever",
        "acceptance_gates": "test gate",
        "stop_rules": "test stop",
        "non_regression_guardrails": "test guardrail",
        "diagnostic_only_monitoring": False,
        "repair_execution_allowed": False,
        "training_allowed": False,
        "ranking_admissible": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
    }


def _write_source(tmp_path: Path, *, result_class: str | None = None) -> Path:
    source = tmp_path / "source"
    offtrack_rows = [
        _plan_row(lever_family="geometry_timing_containment"),
        _plan_row(lever_family="hidden_dynamics_actuator_response_robustness"),
        _plan_row(lever_family="offtrack_containment_general"),
        _plan_row(lever_family="offtrack_containment_repair_family"),
        _plan_row(lever_family="role_conditioned_containment"),
        _plan_row(lever_family="role_semantics_containment", plan_route="offtrack_repair_plan_with_collision_guardrail"),
    ]
    collision_rows = [_plan_row(lever_family="collision_non_regression_guardrail", plan_route="collision_guardrail_constraint")]
    r4_rows = [_plan_row(lever_family="unavoidable_mitigation_semantics", plan_route="r4_mitigation_semantics_guardrail")]
    diagnostic_rows = [_plan_row(lever_family="non_ranking_diagnostic_monitor", plan_route="diagnostic_monitoring_only")]
    write_json(source / "summary.json", {"result_class": result_class or "current_sim_dual_axis_bounded_repair_plan_materialization_pass"})
    write_csv_rows(source / "offtrack_repair_plan_rows.csv", offtrack_rows)
    write_csv_rows(source / "collision_guardrail_plan_rows.csv", collision_rows)
    write_csv_rows(source / "r4_mitigation_plan_rows.csv", r4_rows)
    write_csv_rows(source / "diagnostic_monitoring_rows.csv", diagnostic_rows)
    return source


def test_offtrack_candidate_materialization_writes_compact_run_dir_only_overlays(tmp_path: Path) -> None:
    source = _write_source(tmp_path)
    out = tmp_path / "out"

    summary = candidates.run_offtrack_containment_repair_candidate_materialization(
        source_dir=source,
        output_dir=out,
        target_offtrack_row_count=6,
        max_candidate_count=4,
    )

    assert summary["result_class"] == candidates.RESULT_PASS
    assert summary["source_offtrack_repair_plan_row_count"] == 6
    assert summary["assigned_offtrack_repair_plan_row_count"] == 6
    assert summary["unassigned_offtrack_repair_plan_row_count"] == 0
    assert summary["candidate_count"] == 4
    assert summary["candidate_overlay_written_count"] == 4
    assert summary["candidate_overlay_outside_run_dir_count"] == 0
    assert summary["guardrail_metadata_row_count"] == 8
    assert summary["active_config_overwrite_count"] == 0
    assert summary["repair_execution_allowed_count"] == 0
    assert summary["ranking_admissible_count"] == 0
    assert summary["guardrail_violation_count"] == 0

    overlay_rows = candidates.read_csv_rows(out / "repair_candidate_overlays.csv")
    assert len(overlay_rows) == 4
    for row in overlay_rows:
        assert row["run_dir_only"] == "True"
        assert row["active_config_overwrite"] == "False"
        assert row["guardrail_metadata_attached"] == "True"
        assert Path(row["overlay_path"]).exists()
    for row in candidates.read_csv_rows(out / "candidate_guardrail_metadata.csv"):
        assert Path(row["artifact_ref"]).exists()
    payload = read_json(out / "repair_candidate_overlays" / "c03_general_offtrack_boundary_containment.json")
    assert payload["artifact_only"] is True
    assert payload["active_config_overwrite"] is False


def test_offtrack_candidate_materialization_fails_closed_on_source_failure(tmp_path: Path) -> None:
    source = _write_source(tmp_path, result_class="current_sim_dual_axis_bounded_repair_plan_materialization_fail")

    summary = candidates.run_offtrack_containment_repair_candidate_materialization(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_offtrack_row_count=6,
    )

    assert summary["result_class"] == candidates.RESULT_FAIL
    assert summary["source_result_class"].endswith("_fail")


def test_offtrack_candidate_materialization_fails_closed_on_unassigned_rows(tmp_path: Path) -> None:
    source = _write_source(tmp_path)
    rows = candidates.read_csv_rows(source / "offtrack_repair_plan_rows.csv")
    rows.append(_plan_row(lever_family="unknown_future_family"))
    write_csv_rows(source / "offtrack_repair_plan_rows.csv", rows)

    summary = candidates.run_offtrack_containment_repair_candidate_materialization(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_offtrack_row_count=7,
    )

    assert summary["result_class"] == candidates.RESULT_FAIL
    assert summary["unassigned_offtrack_repair_plan_row_count"] == 1


def test_offtrack_candidate_materialization_fails_closed_on_missing_guardrails(tmp_path: Path) -> None:
    source = _write_source(tmp_path)
    write_csv_rows(source / "r4_mitigation_plan_rows.csv", [])

    summary = candidates.run_offtrack_containment_repair_candidate_materialization(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_offtrack_row_count=6,
    )

    assert summary["result_class"] == candidates.RESULT_FAIL
    assert summary["r4_mitigation_source_row_count"] == 0
