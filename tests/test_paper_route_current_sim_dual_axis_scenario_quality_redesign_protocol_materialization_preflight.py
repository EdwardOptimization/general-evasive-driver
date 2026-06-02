from __future__ import annotations

from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.paper_route_current_sim_dual_axis_scenario_quality_redesign_protocol_materialization_preflight import (
    RESULT_FAIL,
    RESULT_PASS,
    read_csv_rows,
    run_protocol_materialization_preflight,
)


def _panel(
    *,
    panel_id: str,
    panel_class: str,
    panel_scope: str,
    axis: str,
    value: str,
    scenario_quality: bool = False,
    repair_candidate: bool = False,
    collision_guardrail: bool = False,
    hidden_guardrail: bool = False,
    geometry_guardrail: bool = False,
) -> dict[str, Any]:
    return {
        "panel_id": panel_id,
        "panel_class": panel_class,
        "panel_scope": panel_scope,
        "axis": axis,
        "value": value,
        "source_row_ids": panel_id,
        "episode_count": 100,
        "actual_success_count": 10,
        "actual_success_rate": 0.1,
        "hard_offtrack_count": 80,
        "hard_offtrack_rate": 0.8,
        "soft_offtrack_violation_count": 0,
        "soft_offtrack_violation_rate": 0.0,
        "boundary_tolerated_success_count": 0,
        "boundary_tolerated_success_rate": 0.0,
        "collision_count": 10 if collision_guardrail else 0,
        "collision_rate": 0.1 if collision_guardrail else 0.0,
        "max_step_noncompletion_count": 0,
        "max_step_noncompletion_rate": 0.0,
        "other_count": 0,
        "other_rate": 0.0,
        "mean_min_clearance_margin": 1.0,
        "min_min_clearance_margin": -0.1 if collision_guardrail else 0.5,
        "mean_overshoot_m": 0.2,
        "max_overshoot_m": 0.3,
        "mean_steps": 100.0,
        "diagnostic_pattern": "hard_offtrack_dominated",
        "scenario_quality_blocker": scenario_quality,
        "possible_repair_plan_candidate": repair_candidate,
        "collision_mitigation_guardrail": collision_guardrail,
        "hidden_dynamics_guardrail": hidden_guardrail,
        "geometry_timing_guardrail": geometry_guardrail,
        "soft_boundary_diagnostic": False,
        "monitoring_only": False,
        "diagnostic_only": not repair_candidate,
        "ranking_admissible": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "reason": "test row",
    }


def _write_inputs(tmp_path: Path, rows: list[dict[str, Any]], *, source_pass: bool = True) -> dict[str, Path]:
    paths = {
        "panel_rows": tmp_path / "panel_rows.csv",
        "summary": tmp_path / "summary.json",
        "protocol_doc": tmp_path / "protocol.md",
    }
    write_csv_rows(paths["panel_rows"], rows)
    write_json(paths["summary"], {"result_class": "m2452_pass" if source_pass else "m2452_fail"})
    paths["protocol_doc"].write_text("# protocol\n", encoding="utf-8")
    return paths


def _complete_rows() -> list[dict[str, Any]]:
    return [
        _panel(
            panel_id="stable",
            panel_class="scenario_quality_blocker",
            panel_scope="stable_avoidable_boundary_quality",
            axis="role_family+sampled_obstacle_label",
            value="R0_stable_avoidable|aeb_feasible",
            scenario_quality=True,
        ),
        _panel(
            panel_id="aes",
            panel_class="scenario_quality_blocker",
            panel_scope="aeb_infeasible_stable_aes_quality",
            axis="role_family+sampled_obstacle_label",
            value="R1_aeb_infeasible_stable_aes|aes_feasible",
            scenario_quality=True,
        ),
        _panel(
            panel_id="drift",
            panel_class="possible_repair_plan_candidate",
            panel_scope="handling_limit_drift_required",
            axis="sampled_obstacle_label",
            value="drift_required",
            repair_candidate=True,
            collision_guardrail=True,
        ),
        _panel(
            panel_id="hidden",
            panel_class="possible_repair_plan_candidate",
            panel_scope="hidden_dynamics",
            axis="hidden_dynamics_bucket",
            value="low_mu",
            repair_candidate=True,
            hidden_guardrail=True,
            collision_guardrail=True,
        ),
        _panel(
            panel_id="mitigation",
            panel_class="collision_mitigation_guardrail",
            panel_scope="unavoidable_mitigation",
            axis="sampled_obstacle_label",
            value="unavoidable",
            collision_guardrail=True,
        ),
        _panel(
            panel_id="monitoring",
            panel_class="monitoring_only",
            panel_scope="monitoring_profile_name",
            axis="profile_name",
            value="L3_online_gru",
        )
        | {"monitoring_only": True},
    ]


def test_protocol_materialization_creates_required_groups_and_claim_boundary(tmp_path: Path) -> None:
    paths = _write_inputs(tmp_path, _complete_rows())

    summary = run_protocol_materialization_preflight(
        panel_rows_path=paths["panel_rows"],
        m2452_summary_path=paths["summary"],
        protocol_doc_path=paths["protocol_doc"],
        output_dir=tmp_path / "out",
    )

    assert summary["result_class"] == RESULT_PASS
    assert summary["stable_feasibility_support_count"] > 0
    assert summary["stable_aes_support_count"] > 0
    assert summary["handling_limit_guardrail_count"] > 0
    assert summary["hidden_dynamics_guardrail_count"] > 0
    assert summary["mitigation_guardrail_count"] > 0
    assert summary["labels_enter_actor_input_count"] == 0
    assert summary["actor_input_contract_changed_count"] == 0
    assert summary["ranking_admissible_count"] == 0
    assert summary["winner_selected_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["policy_action_executed"] is False
    assert summary["scenario_redesign_executed"] is False
    assert summary["current_sim_verdict_claim_made"] is False

    candidates = read_csv_rows(tmp_path / "out" / "candidate_rows.csv")
    groups = {row["candidate_group"] for row in candidates}
    assert "stable_feasibility_support" in groups
    assert "stable_aes_support" in groups
    assert "handling_limit_guardrail" in groups
    assert "hidden_dynamics_guardrail" in groups
    assert "mitigation_guardrail" in groups
    assert {row["ranking_admissible"] for row in candidates} == {"False"}

    claim_boundary = (tmp_path / "out" / "claim_boundary.csv").read_text(encoding="utf-8")
    assert "current_sim_verdict,blocked,False" in claim_boundary
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["artifacts"]["candidate_rows"].endswith("candidate_rows.csv")


def test_protocol_materialization_fails_closed_when_required_group_missing(tmp_path: Path) -> None:
    rows = [row for row in _complete_rows() if row["panel_id"] != "aes"]
    paths = _write_inputs(tmp_path, rows)

    summary = run_protocol_materialization_preflight(
        panel_rows_path=paths["panel_rows"],
        m2452_summary_path=paths["summary"],
        protocol_doc_path=paths["protocol_doc"],
        output_dir=tmp_path / "out",
    )

    assert summary["result_class"] == RESULT_FAIL
    assert "stable_aes_support" in summary["missing_required_groups"]
    assert "scenario_sampling_failure" in summary["failure_types_observed"]
    assert summary["paper_level_claim_made"] is False


def test_protocol_materialization_fails_closed_on_source_failure(tmp_path: Path) -> None:
    paths = _write_inputs(tmp_path, _complete_rows(), source_pass=False)

    summary = run_protocol_materialization_preflight(
        panel_rows_path=paths["panel_rows"],
        m2452_summary_path=paths["summary"],
        protocol_doc_path=paths["protocol_doc"],
        output_dir=tmp_path / "out",
    )

    assert summary["result_class"] == RESULT_FAIL
    assert "lineage_invalid" in summary["failure_types_observed"]
    assert summary["level3_self_id_claim_made"] is False
