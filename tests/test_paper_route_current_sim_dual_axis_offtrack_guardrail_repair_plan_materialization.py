from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization import (
    read_csv_rows,
    run_repair_plan_materialization,
)


SPEC_FIELDNAMES = [
    "repair_spec_id",
    "source_group",
    "source_slice_axis",
    "source_slice_value",
    "source_consolidated_route",
    "actionability_class",
    "repair_family",
    "priority_tier",
    "target_metric",
    "guardrail_metric",
    "allowed_repair_levers",
    "blocked_levers",
    "collision_guardrail_required",
    "r4_mitigation_semantics",
    "diagnostic_no_ranking_guardrail",
    "repair_execution_started",
    "training_started",
    "ranking_admissible",
    "winner_selected",
    "paper_level_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "level3_self_id_claim_made",
    "scenario_redesign_executed_claim_made",
    "training_repair_success_claim_made",
]


def _spec(
    *,
    spec_id: str,
    family: str,
    group: str,
    axis: str,
    value: str,
    priority: str,
    target_metric: str,
    guardrail_metric: str,
    collision: bool = False,
    r4: bool = False,
    diagnostic: bool = False,
) -> dict[str, object]:
    return {
        "repair_spec_id": spec_id,
        "source_group": group,
        "source_slice_axis": axis,
        "source_slice_value": value,
        "source_consolidated_route": group,
        "actionability_class": "role_semantics",
        "repair_family": family,
        "priority_tier": priority,
        "target_metric": target_metric,
        "guardrail_metric": guardrail_metric,
        "allowed_repair_levers": "offtrack_margin_reward|curriculum_sampling_weight",
        "blocked_levers": "actor_input_change|hidden_oracle_feature_injection|profile_specific_tuning",
        "collision_guardrail_required": collision,
        "r4_mitigation_semantics": r4,
        "diagnostic_no_ranking_guardrail": diagnostic,
        "repair_execution_started": False,
        "training_started": False,
        "ranking_admissible": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
    }


def _inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path, Path, Path]:
    summary_path = tmp_path / "summary.json"
    repair_spec_path = tmp_path / "repair_specs.csv"
    ordinary_path = tmp_path / "ordinary.csv"
    mixed_path = tmp_path / "mixed.csv"
    collision_path = tmp_path / "collision.csv"
    r4_path = tmp_path / "r4.csv"
    diagnostic_path = tmp_path / "diagnostic.csv"
    write_json(summary_path, {"result_class": "current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization_pass"})
    ordinary_rows = [
        _spec(
            spec_id="ordinary_0000",
            family="priority_offtrack_containment_repair",
            group="offtrack_target",
            axis="role_family",
            value="R0_stable_avoidable",
            priority="P0",
            target_metric="offtrack_rate_down",
            guardrail_metric="collision_rate_monitor",
        )
    ]
    mixed_rows = [
        _spec(
            spec_id="mixed_0000",
            family="guarded_offtrack_containment_repair",
            group="offtrack_target",
            axis="role_family",
            value="R2_handling_limit_drift_capable_avoidance",
            priority="P1",
            target_metric="offtrack_rate_down",
            guardrail_metric="collision_rate_not_worse",
            collision=True,
        )
    ]
    collision_rows = [
        _spec(
            spec_id="collision_0000",
            family="collision_guardrail_constraint",
            group="collision_guardrail",
            axis="obstacle_longitudinal_timing_bucket",
            value="late_close",
            priority="G0",
            target_metric="not_applicable_guardrail_only",
            guardrail_metric="collision_rate_not_worse",
            collision=True,
        )
    ]
    r4_rows = [
        _spec(
            spec_id="r4_0000",
            family="r4_mitigation_semantics_guardrail",
            group="r4_mitigation",
            axis="role_family",
            value="R4_unavoidable_mitigation",
            priority="R4",
            target_metric="mitigation_semantics_preserved",
            guardrail_metric="r4_not_ordinary_avoidance",
            r4=True,
        )
    ]
    diagnostic_rows = [
        _spec(
            spec_id="diagnostic_0000",
            family="diagnostic_no_ranking_guardrail",
            group="diagnostic_guardrail",
            axis="profile_name",
            value="L2_window_50",
            priority="D0",
            target_metric="not_applicable_diagnostic_only",
            guardrail_metric="no_ranking_no_winner_claims",
            diagnostic=True,
        )
    ]
    write_csv_rows(repair_spec_path, [*ordinary_rows, *mixed_rows, *collision_rows, *r4_rows, *diagnostic_rows], fieldnames=SPEC_FIELDNAMES)
    write_csv_rows(ordinary_path, ordinary_rows, fieldnames=SPEC_FIELDNAMES)
    write_csv_rows(mixed_path, mixed_rows, fieldnames=SPEC_FIELDNAMES)
    write_csv_rows(collision_path, collision_rows, fieldnames=SPEC_FIELDNAMES)
    write_csv_rows(r4_path, r4_rows, fieldnames=SPEC_FIELDNAMES)
    write_csv_rows(diagnostic_path, diagnostic_rows, fieldnames=SPEC_FIELDNAMES)
    return summary_path, repair_spec_path, ordinary_path, mixed_path, collision_path, r4_path, diagnostic_path


def test_repair_plan_materialization_writes_plan_artifacts_without_execution(tmp_path: Path) -> None:
    summary_path, repair_spec_path, ordinary_path, mixed_path, collision_path, r4_path, diagnostic_path = _inputs(tmp_path)

    summary = run_repair_plan_materialization(
        summary_path=summary_path,
        repair_spec_rows_path=repair_spec_path,
        ordinary_rows_path=ordinary_path,
        mixed_rows_path=mixed_path,
        collision_rows_path=collision_path,
        r4_rows_path=r4_path,
        diagnostic_rows_path=diagnostic_path,
        output_dir=tmp_path / "out",
        target_repair_spec_row_count=5,
        target_ordinary_row_count=1,
        target_mixed_row_count=1,
        target_collision_row_count=1,
        target_r4_row_count=1,
        target_diagnostic_row_count=1,
    )

    assert summary["result_class"] == "current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization_pass"
    assert summary["input_repair_spec_row_count"] == 5
    assert summary["ordinary_offtrack_source_count"] == 1
    assert summary["mixed_guarded_source_count"] == 1
    assert summary["collision_guardrail_source_count"] == 1
    assert summary["r4_guardrail_source_count"] == 1
    assert summary["diagnostic_guardrail_source_count"] == 1
    assert summary["reward_delta_row_count"] == 2
    assert summary["curriculum_weight_row_count"] == 2
    assert summary["guardrail_constraint_row_count"] == 4
    assert summary["mixed_guarded_constraint_row_count"] == 1
    assert summary["profile_specific_tuning_count"] == 0
    assert summary["actor_input_change_count"] == 0
    assert summary["hidden_oracle_feature_injection_count"] == 0
    assert summary["collision_blind_mixed_repair_count"] == 0
    assert summary["r4_ordinary_repair_count"] == 0
    assert summary["ranking_admissible_count"] == 0
    assert summary["winner_selected_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["repair_execution_started"] is False
    assert summary["training_started"] is False
    assert summary["paper_level_claim_made"] is False
    assert summary["current_sim_verdict_claim_made"] is False

    reward_rows = read_csv_rows(tmp_path / "out" / "reward_delta_rows.csv")
    assert {row["repair_spec_id"] for row in reward_rows} == {"ordinary_0000", "mixed_0000"}

    mixed_constraints = read_csv_rows(tmp_path / "out" / "mixed_guarded_constraint_rows.csv")
    assert mixed_constraints[0]["constraint_metric"] == "collision_rate_not_worse"

    claim_boundary = (tmp_path / "out" / "claim_boundary.csv").read_text(encoding="utf-8")
    assert "repair_execution,False" in claim_boundary
    assert "current_sim_verdict,False" in claim_boundary

    plan = read_json(tmp_path / "out" / "repair_implementation_plan.json")
    assert "actor_input_change" in plan["blocked_levers"]

    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["artifacts"]["repair_implementation_plan"].endswith("repair_implementation_plan.json")


def test_repair_plan_materialization_fails_closed_on_source_count_mismatch(tmp_path: Path) -> None:
    summary_path, repair_spec_path, ordinary_path, mixed_path, collision_path, r4_path, diagnostic_path = _inputs(tmp_path)

    summary = run_repair_plan_materialization(
        summary_path=summary_path,
        repair_spec_rows_path=repair_spec_path,
        ordinary_rows_path=ordinary_path,
        mixed_rows_path=mixed_path,
        collision_rows_path=collision_path,
        r4_rows_path=r4_path,
        diagnostic_rows_path=diagnostic_path,
        output_dir=tmp_path / "out",
        target_repair_spec_row_count=6,
        target_ordinary_row_count=1,
        target_mixed_row_count=1,
        target_collision_row_count=1,
        target_r4_row_count=1,
        target_diagnostic_row_count=1,
    )

    assert summary["result_class"] == "current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization_incomplete_or_fail"
    assert summary["input_repair_spec_row_count"] == 5
    assert summary["target_repair_spec_row_count"] == 6
    assert summary["repair_execution_started"] is False
    assert summary["training_repair_success_claim_made"] is False
