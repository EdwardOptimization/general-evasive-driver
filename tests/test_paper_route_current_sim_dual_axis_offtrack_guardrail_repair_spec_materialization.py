from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization import (
    read_csv_rows,
    run_repair_spec_materialization,
)


def _row(
    *,
    axis: str,
    value: str,
    route: str,
    actionability: str,
    high: bool = False,
    collision_guardrail: bool = False,
    r4: bool = False,
) -> dict[str, object]:
    return {
        "slice_axis": axis,
        "slice_key": axis,
        "slice_value": value,
        "episode_count": 30,
        "success_rate": 0.0,
        "offtrack_rate": 0.8,
        "collision_rate": 0.2 if collision_guardrail else 0.0,
        "dominant_failure_mode": "offtrack_dominated_failure",
        "is_high_priority_offtrack": high,
        "source_route_class": route,
        "consolidated_route": route,
        "actionability_class": actionability,
        "repair_target_admissible": route in {"offtrack_repair_target", "offtrack_repair_target_with_collision_guardrail"},
        "collision_guardrail_required": collision_guardrail,
        "r4_mitigation_semantics": r4,
        "diagnostic_only": route in {"diagnostic_guardrail", "diagnostic_only"},
        "ranking_admissible": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
    }


def _inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path]:
    summary_path = tmp_path / "summary.json"
    offtrack_path = tmp_path / "offtrack.csv"
    collision_path = tmp_path / "collision.csv"
    r4_path = tmp_path / "r4.csv"
    diagnostic_path = tmp_path / "diagnostic.csv"
    write_json(summary_path, {"result_class": "current_sim_dual_axis_actionable_target_consolidation_pass"})
    write_csv_rows(
        offtrack_path,
        [
            _row(
                axis="role_family",
                value="R0_stable_avoidable",
                route="offtrack_repair_target",
                actionability="role_semantics",
                high=True,
            ),
            _row(
                axis="role_family",
                value="R2_handling_limit_drift_capable_avoidance",
                route="offtrack_repair_target_with_collision_guardrail",
                actionability="role_semantics",
                collision_guardrail=True,
            ),
        ],
    )
    write_csv_rows(
        collision_path,
        [
            _row(
                axis="obstacle_longitudinal_timing_bucket",
                value="late_close",
                route="collision_guardrail",
                actionability="geometry_timing",
                collision_guardrail=True,
            )
        ],
    )
    write_csv_rows(
        r4_path,
        [
            _row(
                axis="role_family",
                value="R4_unavoidable_mitigation",
                route="r4_mitigation_semantics",
                actionability="r4_mitigation_semantics",
                r4=True,
            )
        ],
    )
    write_csv_rows(
        diagnostic_path,
        [
            _row(
                axis="profile_name",
                value="L2_window_50",
                route="diagnostic_guardrail",
                actionability="diagnostic_guardrail",
            )
        ],
    )
    return summary_path, offtrack_path, collision_path, r4_path, diagnostic_path


def test_repair_spec_materialization_writes_guarded_specs_without_execution(tmp_path: Path) -> None:
    summary_path, offtrack_path, collision_path, r4_path, diagnostic_path = _inputs(tmp_path)

    summary = run_repair_spec_materialization(
        summary_path=summary_path,
        offtrack_target_rows_path=offtrack_path,
        collision_guardrail_rows_path=collision_path,
        r4_rows_path=r4_path,
        diagnostic_guardrail_rows_path=diagnostic_path,
        output_dir=tmp_path / "out",
        target_offtrack_row_count=2,
        target_collision_guardrail_row_count=1,
        target_r4_row_count=1,
        target_diagnostic_guardrail_row_count=1,
    )

    assert summary["result_class"] == "current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization_pass"
    assert summary["repair_spec_row_count"] == 5
    assert summary["ordinary_offtrack_repair_spec_count"] == 1
    assert summary["mixed_guarded_repair_spec_count"] == 1
    assert summary["collision_guardrail_spec_count"] == 1
    assert summary["r4_guardrail_spec_count"] == 1
    assert summary["diagnostic_guardrail_spec_count"] == 1
    assert summary["profile_or_pack_repair_spec_count"] == 0
    assert summary["r4_ordinary_repair_spec_count"] == 0
    assert summary["collision_blind_mixed_repair_spec_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["repair_execution_started"] is False
    assert summary["training_started"] is False
    assert summary["paper_level_claim_made"] is False
    assert summary["training_repair_success_claim_made"] is False

    specs = read_csv_rows(tmp_path / "out" / "repair_spec_rows.csv")
    guarded = next(row for row in specs if row["repair_family"] == "guarded_offtrack_containment_repair")
    assert guarded["collision_guardrail_required"] == "True"
    assert "collision_guardrail_weight" in guarded["allowed_repair_levers"]

    diagnostic = next(row for row in specs if row["repair_family"] == "diagnostic_no_ranking_guardrail")
    assert diagnostic["source_slice_axis"] == "profile_name"
    assert diagnostic["ranking_admissible"] == "False"

    claim_boundary = (tmp_path / "out" / "claim_boundary.csv").read_text(encoding="utf-8")
    assert "repair_execution,False" in claim_boundary
    assert "training_repair_success,False" in claim_boundary

    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["artifacts"]["repair_spec_rows"].endswith("repair_spec_rows.csv")


def test_repair_spec_materialization_fails_closed_on_source_count_mismatch(tmp_path: Path) -> None:
    summary_path, offtrack_path, collision_path, r4_path, diagnostic_path = _inputs(tmp_path)

    summary = run_repair_spec_materialization(
        summary_path=summary_path,
        offtrack_target_rows_path=offtrack_path,
        collision_guardrail_rows_path=collision_path,
        r4_rows_path=r4_path,
        diagnostic_guardrail_rows_path=diagnostic_path,
        output_dir=tmp_path / "out",
        target_offtrack_row_count=3,
        target_collision_guardrail_row_count=1,
        target_r4_row_count=1,
        target_diagnostic_guardrail_row_count=1,
    )

    assert summary["result_class"] == "current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization_incomplete_or_fail"
    assert summary["source_offtrack_row_count"] == 2
    assert summary["target_offtrack_row_count"] == 3
    assert summary["paper_level_claim_made"] is False
    assert summary["training_repair_success_claim_made"] is False
