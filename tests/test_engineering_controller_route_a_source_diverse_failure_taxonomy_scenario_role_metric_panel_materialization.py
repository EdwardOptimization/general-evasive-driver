from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift import (
    engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel_materialization as m2743,
)


def _write_m2740_source(root: Path) -> None:
    root.mkdir()
    write_json(
        root / "summary.json",
        {
            "status_pass": True,
            "taxonomy_row_count": 9,
            "execution_taxonomy_row_count": 4,
            "negative_context_taxonomy_row_count": 2,
            "blocked_guard_taxonomy_row_count": 3,
            "gate_matrix_pass": True,
            "hidden_oracle_actor_input_detected": False,
        },
    )
    write_csv_rows(
        root / "taxonomy_rows.csv",
        [
            _taxonomy("t1", "candidate_execution", "off_track"),
            _taxonomy("t2", "candidate_execution", "off_track"),
            _taxonomy("t3", "candidate_execution", "collision_failure"),
            _taxonomy("t4", "candidate_execution", "diagnostic_success_context", success=True),
            _taxonomy("n1", "negative_context_guard", "negative_context_guard", execution_run=False),
            _taxonomy("n2", "negative_context_guard", "negative_context_guard", execution_run=False),
            _taxonomy("b1", "blocked_surface_guard", "blocked_guard", execution_run=False),
            _taxonomy("p1", "blocked_surface_guard", "protected_or_hf3_blocker", execution_run=False),
            _taxonomy("p2", "blocked_surface_guard", "protected_or_hf3_blocker", execution_run=False),
        ],
    )
    write_csv_rows(root / "taxonomy_aggregate_rows.csv", [{"aggregate_id": "a", "status_pass": True}])
    write_csv_rows(root / "source_family_context_rows.csv", [{"source_family": "source", "status_pass": True}])
    write_csv_rows(root / "task_family_context_rows.csv", [{"task_family": "T4", "status_pass": True}])
    write_csv_rows(root / "guardrail_context_rows.csv", [{"guardrail_family": "negative_context_guard", "status_pass": True}])
    write_csv_rows(
        root / "actor_contract_join_rows.csv",
        [
            {"contract_field": "observation_shape", "observed_value": 72, "expected_value": 72, "status_pass": True},
            {
                "contract_field": "hidden_oracle_actor_input_detected",
                "observed_value": False,
                "expected_value": False,
                "status_pass": True,
            },
        ],
    )
    write_csv_rows(root / "claim_boundary_rows.csv", [{"claim_id": "claim", "status_pass": True}])
    write_csv_rows(root / "gate_matrix.csv", [{"gate_id": "gate", "status_pass": True}])


def _taxonomy(
    taxonomy_id: str,
    source_row_type: str,
    taxonomy_family: str,
    *,
    success: bool = False,
    execution_run: bool = True,
) -> dict:
    return {
        "taxonomy_id": taxonomy_id,
        "source_row_type": source_row_type,
        "source_milestone": "m2740-source",
        "source_family": "source_family",
        "source_key": f"T4:{taxonomy_id}",
        "workload_id": f"workload-{taxonomy_id}",
        "task_source_id": f"task-source-{taxonomy_id}",
        "profile_name": "L3_online_gru",
        "task_family": "T4",
        "taxonomy_family": taxonomy_family,
        "primary_failure_family": taxonomy_family,
        "repair_signal": "inspect",
        "success": success,
        "execution_run": execution_run,
        "execution_admitted": execution_run,
        "actor_visible_allowed": False,
        "protected_rows_in_success_denominator": False,
    }


def test_m2743_materializes_actor_invisible_role_metric_panel(monkeypatch, tmp_path: Path) -> None:
    m2740_dir = tmp_path / "m2740"
    output_dir = tmp_path / "m2743"
    doc_path = tmp_path / "m2743.md"
    design = tmp_path / "m2742.md"
    route_plan = tmp_path / "route.md"
    follow_up = tmp_path / "m2744.json"
    _write_m2740_source(m2740_dir)
    design.write_text(
        "admit_source_diverse_failure_taxonomy_scenario_role_metric_panel_materialization\n",
        encoding="utf-8",
    )
    route_plan.write_text("scenario-role metric report\n", encoding="utf-8")
    write_json(follow_up, {"id": "m2744"})
    monkeypatch.setattr(m2743, "EXPECTED_TAXONOMY_ROW_COUNT", 9)
    monkeypatch.setattr(m2743, "EXPECTED_EXECUTION_TAXONOMY_ROW_COUNT", 4)
    monkeypatch.setattr(m2743, "EXPECTED_OFFTRACK_TARGET_COUNT", 2)
    monkeypatch.setattr(m2743, "EXPECTED_COLLISION_CAUTION_COUNT", 1)
    monkeypatch.setattr(m2743, "EXPECTED_DIAGNOSTIC_SUCCESS_CONTEXT_COUNT", 1)
    monkeypatch.setattr(m2743, "EXPECTED_NEGATIVE_CONTEXT_GUARD_COUNT", 2)
    monkeypatch.setattr(m2743, "EXPECTED_BLOCKED_SAME_SURFACE_GUARD_COUNT", 1)
    monkeypatch.setattr(m2743, "EXPECTED_PROTECTED_HF3_EXCLUSION_COUNT", 2)

    summary = m2743.materialize_source_diverse_failure_taxonomy_scenario_role_metric_panel(
        m2740_dir=m2740_dir,
        m2742_design=design,
        route_plan=route_plan,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["scenario_role_row_count"] == 6
    assert summary["target_panel_row_count"] == 4
    assert summary["offtrack_target_row_count"] == 2
    assert summary["collision_caution_row_count"] == 1
    assert summary["diagnostic_success_context_row_count"] == 1
    assert summary["negative_context_guardrail_row_count"] == 2
    assert summary["blocked_same_surface_guard_row_count"] == 1
    assert summary["protected_hf3_exclusion_guard_row_count"] == 2
    assert summary["environment_reset_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert read_json(output_dir / "summary.json") == summary

    role_rows = m2743.read_csv_rows(output_dir / "scenario_role_rows.csv")
    assert {row["scenario_role"] for row in role_rows} == {
        "offtrack_containment_target",
        "collision_caution_guard",
        "diagnostic_success_context",
        "negative_context_guardrail",
        "blocked_same_surface_guard",
        "protected_hf3_exclusion_guard",
    }
    target_rows = m2743.read_csv_rows(output_dir / "target_panel_rows.csv")
    assert {row["target_panel_admitted"] for row in target_rows if row["scenario_role"] == "offtrack_containment_target"} == {"True"}
    assert {row["target_panel_admitted"] for row in target_rows if row["scenario_role"] != "offtrack_containment_target"} == {"False"}
    assert {row["execution_scheduled"] for row in target_rows} == {"False"}
    guardrail_rows = m2743.read_csv_rows(output_dir / "guardrail_context_rows.csv")
    assert {row["ordinary_success_denominator_allowed"] for row in guardrail_rows} == {"False"}
    gate_rows = m2743.read_csv_rows(output_dir / "gate_matrix.csv")
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.exists()
