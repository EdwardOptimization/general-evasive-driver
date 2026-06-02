from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows
from autodrift.paper_route_current_sim_role_stratified_residual_support_rescore import (
    run_role_stratified_residual_support_rescore,
)


def _role_row(scenario_id: str, role: str, design_route: str) -> dict[str, object]:
    primary_route = {
        "support_policy_coverage_materialization_required": "support_policy_coverage_candidate",
        "scenario_or_support_redesign_materialization_required": "scenario_or_support_redesign_candidate",
        "metric_semantics_edge_case": "metric_semantics_audit_candidate",
        "r4_mitigation_metric_availability_gap": "mitigation_semantics_or_support_redesign_candidate",
    }[design_route]
    return {
        "scenario_spec_id": scenario_id,
        "role_family": role,
        "support_label": "support_mixed",
        "primary_route_label": primary_route,
        "design_route_label": design_route,
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def _write_inputs(root: Path) -> tuple[Path, Path, Path]:
    residual_dir = root / "residual"
    role_dir = root / "role"
    r4_dir = root / "r4"
    residual_dir.mkdir()
    role_dir.mkdir()
    r4_dir.mkdir()
    role_rows = [
        _role_row("r2_cov", "R2_handling_limit_drift_capable_avoidance", "support_policy_coverage_materialization_required"),
        _role_row("r2_redesign", "R2_handling_limit_drift_capable_avoidance", "scenario_or_support_redesign_materialization_required"),
        _role_row("r3_metric", "R3_recovery_after_limit", "metric_semantics_edge_case"),
        _role_row("r4", "R4_unavoidable_mitigation", "r4_mitigation_metric_availability_gap"),
    ]
    write_csv_rows(residual_dir / "residual_scenario_rows.csv", role_rows)
    write_csv_rows(role_dir / "role_stratified_residual_rows.csv", role_rows)
    write_csv_rows(
        r4_dir / "r4_metric_semantics_rows.csv",
        [
            {
                "scenario_spec_id": "r4",
                "r4_metric_semantics_status": "proxy_metric_available_post_collision_blocked",
                "comparison_admissibility": "descriptive_proxy_audit_only",
            }
        ],
    )
    return residual_dir, role_dir, r4_dir


def test_role_stratified_residual_support_rescore_materializes_expected_categories(tmp_path: Path) -> None:
    residual_dir, role_dir, r4_dir = _write_inputs(tmp_path)
    output_dir = tmp_path / "out"

    summary = run_role_stratified_residual_support_rescore(
        residual_dir=residual_dir,
        role_redesign_dir=role_dir,
        r4_semantics_dir=r4_dir,
        output_dir=output_dir,
        target_residual_scenario_count=4,
    )

    assert summary["result_class"] == "current_sim_role_stratified_residual_support_rescore_pass"
    assert summary["rescored_residual_scenario_count"] == 4
    assert summary["r4_proxy_semantics_post_collision_blocked_count"] == 1
    assert summary["support_policy_coverage_gap_count"] == 1
    assert summary["scenario_or_support_redesign_gap_count"] == 1
    assert summary["metric_semantics_edge_count"] == 1
    assert summary["guardrail_violation_count"] == 0

    persisted = read_json(output_dir / "summary.json")
    assert persisted["rescored_residual_scenario_count"] == 4

    rows_text = (output_dir / "residual_rescore_rows.csv").read_text(encoding="utf-8")
    assert "r4_proxy_metric_semantics_available_post_collision_blocked" in rows_text
    assert "support_policy_coverage_gap" in rows_text
    assert "scenario_or_support_redesign_gap" in rows_text
    assert "metric_semantics_edge_case" in rows_text

    claims = (output_dir / "claim_boundary.csv").read_text(encoding="utf-8")
    assert "residual_support_solved,False,False" in claims
