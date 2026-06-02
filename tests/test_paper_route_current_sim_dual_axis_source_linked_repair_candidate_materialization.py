from __future__ import annotations

from pathlib import Path
from typing import Any

from autodrift import paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization as candidates
from autodrift import paper_route_current_sim_dual_axis_source_linked_bounded_repair_plan_materialization as repair_plan
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _plan_row(
    *,
    lever_family: str,
    plan_route: str = "offtrack_repair_plan",
    diagnostic: bool = False,
    family_diagnostic: bool = False,
    ranking_admissible: bool = False,
) -> dict[str, Any]:
    return {
        "slice_axis": "slice_axis",
        "slice_key": "slice_axis",
        "slice_value": lever_family,
        "source_table": "episode_family_membership_rows" if family_diagnostic else "episode_rows",
        "episode_count": 20,
        "success_rate": 0.0,
        "offtrack_rate": 0.8,
        "collision_rate": 0.1,
        "max_step_noncompletion_rate": 0.0,
        "speed_too_low_rate": 0.0,
        "dominant_failure_mode": "offtrack_dominated_failure",
        "source_consolidated_route": "test",
        "source_actionability_class": "test",
        "source_priority_score": 1.0,
        "plan_route": plan_route,
        "lever_family": lever_family,
        "candidate_levers": "test lever",
        "acceptance_gates": "test gate",
        "stop_rules": "test stop",
        "non_regression_guardrails": "test guardrail",
        "diagnostic_only_monitoring": diagnostic,
        "family_membership_diagnostic_monitoring": family_diagnostic,
        "max_step_guardrail_required": plan_route == "max_step_noncompletion_guardrail",
        "speed_too_low_guardrail_required": plan_route == "speed_too_low_guardrail",
        "repair_execution_allowed": False,
        "training_allowed": False,
        "ranking_admissible": ranking_admissible,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "source_linked_repair_plan_materialization": True,
        "source_linked_family_ranking_claim_made": False,
        "support_policy_ranking_claim_made": False,
    }


def _write_source(tmp_path: Path, *, result_class: str | None = None, diagnostic_ranking: bool = False) -> Path:
    source = tmp_path / "source"
    offtrack_rows = [
        _plan_row(lever_family="geometry_timing_containment"),
        _plan_row(lever_family="hidden_dynamics_actuator_response_robustness"),
        _plan_row(lever_family="hidden_dynamics_actuator_response_robustness"),
        _plan_row(lever_family="role_conditioned_containment"),
        _plan_row(lever_family="role_semantics_containment", plan_route="offtrack_repair_plan_with_collision_guardrail"),
        _plan_row(lever_family="outcome_failure_surface_containment"),
    ]
    collision_rows = [
        _plan_row(lever_family="collision_non_regression_guardrail", plan_route="collision_guardrail_constraint")
    ]
    r4_rows = [
        _plan_row(lever_family="unavoidable_mitigation_semantics", plan_route="r4_mitigation_semantics_guardrail")
    ]
    max_step_rows = [
        _plan_row(lever_family="noncompletion_horizon_guardrail", plan_route="max_step_noncompletion_guardrail")
    ]
    speed_too_low_rows = [
        _plan_row(lever_family="low_speed_progress_guardrail", plan_route="speed_too_low_guardrail")
    ]
    diagnostic_rows = [
        _plan_row(
            lever_family="non_ranking_diagnostic_monitor",
            plan_route="diagnostic_monitoring_only",
            diagnostic=True,
            ranking_admissible=diagnostic_ranking,
        )
    ]
    family_rows = [
        _plan_row(
            lever_family="source_linked_family_membership_diagnostic",
            plan_route="family_membership_diagnostic_monitoring",
            diagnostic=True,
            family_diagnostic=True,
        )
    ]
    write_json(
        source / "summary.json",
        {"result_class": result_class or "current_sim_dual_axis_source_linked_bounded_repair_plan_materialization_pass"},
    )
    repair_rows = offtrack_rows + collision_rows + r4_rows + max_step_rows + speed_too_low_rows + diagnostic_rows + family_rows
    write_csv_rows(source / "repair_plan_rows.csv", repair_rows, fieldnames=repair_plan.PLAN_FIELDNAMES)
    write_csv_rows(source / "offtrack_repair_plan_rows.csv", offtrack_rows, fieldnames=repair_plan.PLAN_FIELDNAMES)
    write_csv_rows(source / "collision_guardrail_plan_rows.csv", collision_rows, fieldnames=repair_plan.PLAN_FIELDNAMES)
    write_csv_rows(source / "r4_mitigation_plan_rows.csv", r4_rows, fieldnames=repair_plan.PLAN_FIELDNAMES)
    write_csv_rows(source / "max_step_noncompletion_plan_rows.csv", max_step_rows, fieldnames=repair_plan.PLAN_FIELDNAMES)
    write_csv_rows(source / "speed_too_low_plan_rows.csv", speed_too_low_rows, fieldnames=repair_plan.PLAN_FIELDNAMES)
    write_csv_rows(source / "diagnostic_monitoring_rows.csv", diagnostic_rows, fieldnames=repair_plan.PLAN_FIELDNAMES)
    write_csv_rows(source / "family_membership_diagnostic_rows.csv", family_rows, fieldnames=repair_plan.PLAN_FIELDNAMES)
    return source


def test_source_linked_candidate_materialization_writes_guarded_run_dir_overlays(tmp_path: Path) -> None:
    source = _write_source(tmp_path)
    out = tmp_path / "out"

    summary = candidates.run_source_linked_repair_candidate_materialization(
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
    assert summary["collision_guardrail_source_row_count"] == 1
    assert summary["r4_mitigation_source_row_count"] == 1
    assert summary["max_step_source_row_count"] == 1
    assert summary["speed_too_low_source_row_count"] == 1
    assert summary["diagnostic_monitoring_source_row_count"] == 1
    assert summary["family_membership_diagnostic_source_row_count"] == 1
    assert summary["guardrail_metadata_row_count"] == 24
    assert summary["diagnostic_rows_monitoring_only"] is True
    assert summary["family_rows_monitoring_only"] is True
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
        assert row["diagnostic_rows_monitoring_only"] == "True"
        assert row["family_rows_monitoring_only"] == "True"
        assert Path(row["overlay_path"]).exists()
    guardrail_rows = candidates.read_csv_rows(out / "candidate_guardrail_metadata.csv")
    assert len(guardrail_rows) == 24
    assert {row["guardrail_type"] for row in guardrail_rows} == {
        "collision_non_regression",
        "r4_mitigation_semantics",
        "max_step_noncompletion",
        "speed_too_low",
        "diagnostic_monitoring",
        "source_linked_family_membership_diagnostic",
    }
    for row in guardrail_rows:
        assert Path(row["artifact_ref"]).exists()
        assert row["ranking_admissible"] == "False"
    payload = read_json(out / "repair_candidate_overlays" / "c04_source_linked_outcome_failure_surface_containment.json")
    assert payload["artifact_only"] is True
    assert payload["source_linked"] is True
    assert payload["active_config_overwrite"] is False
    assert payload["guardrails"]["source_linked_family_ranking_allowed"] is False


def test_source_linked_candidate_materialization_fails_closed_on_source_failure(tmp_path: Path) -> None:
    source = _write_source(
        tmp_path,
        result_class="current_sim_dual_axis_source_linked_bounded_repair_plan_materialization_incomplete_or_fail",
    )

    summary = candidates.run_source_linked_repair_candidate_materialization(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_offtrack_row_count=6,
    )

    assert summary["result_class"] == candidates.RESULT_FAIL
    assert summary["source_result_class"].endswith("_fail")


def test_source_linked_candidate_materialization_fails_closed_on_unassigned_rows(tmp_path: Path) -> None:
    source = _write_source(tmp_path)
    rows = candidates.read_csv_rows(source / "offtrack_repair_plan_rows.csv")
    rows.append(_plan_row(lever_family="unknown_future_family"))
    write_csv_rows(source / "offtrack_repair_plan_rows.csv", rows, fieldnames=repair_plan.PLAN_FIELDNAMES)

    summary = candidates.run_source_linked_repair_candidate_materialization(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_offtrack_row_count=7,
    )

    assert summary["result_class"] == candidates.RESULT_FAIL
    assert summary["unassigned_offtrack_repair_plan_row_count"] == 1


def test_source_linked_candidate_materialization_fails_closed_on_missing_guardrail_metadata(tmp_path: Path) -> None:
    source = _write_source(tmp_path)
    write_csv_rows(source / "max_step_noncompletion_plan_rows.csv", [], fieldnames=repair_plan.PLAN_FIELDNAMES)

    summary = candidates.run_source_linked_repair_candidate_materialization(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_offtrack_row_count=6,
    )

    assert summary["result_class"] == candidates.RESULT_FAIL
    assert summary["max_step_source_row_count"] == 0
    assert summary["guardrail_metadata_missing_count"] == 4


def test_source_linked_candidate_materialization_fails_closed_on_diagnostic_ranking(tmp_path: Path) -> None:
    source = _write_source(tmp_path, diagnostic_ranking=True)

    summary = candidates.run_source_linked_repair_candidate_materialization(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_offtrack_row_count=6,
    )

    assert summary["result_class"] == candidates.RESULT_FAIL
    assert summary["diagnostic_rows_monitoring_only"] is False
    assert summary["source_ranking_admissible_count"] == 1
