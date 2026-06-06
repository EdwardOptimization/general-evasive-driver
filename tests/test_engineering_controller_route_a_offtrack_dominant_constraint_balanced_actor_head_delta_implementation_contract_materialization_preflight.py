from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
import autodrift.engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_implementation_contract_materialization_preflight as m2944


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _objective_row(index: int, family: str, source_family: str, count: int) -> dict[str, object]:
    return {
        "objective_balance_id": f"m2941-objective-balance-{index:04d}",
        "objective_family": family,
        "source_constraint_family": source_family,
        "source_row_count": count,
        "actor_visible": False,
        "ranking_allowed": False,
        "diagnostic_only_no_verdict": True,
    }


def _carryforward_row(index: int, constraint_family: str, objective_family: str) -> dict[str, object]:
    return {
        "carryforward_constraint_id": f"m2941-carryforward-constraint-{index:04d}",
        "source_transition_constraint_id": f"m2937-transition-constraint-{index:04d}",
        "source_panel_row_id": f"panel-{index}",
        "source_constraint_family": constraint_family,
        "transition_bucket": "offtrack->offtrack" if "offtrack" in constraint_family else "success->success",
        "objective_family": objective_family,
        "actor_visible": False,
        "evaluator_side_only": True,
        "future_candidate_must_account": True,
        "execution_scheduled": False,
        "ranking_allowed": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
    }


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m2941_dir = root / "m2941"
    m2942_audit = root / "m2942.md"
    m2943_design = root / "m2943.md"
    objective_rows = [
        _objective_row(1, "persistent_offtrack_reduction", "offtrack_persistence_constraint", 2),
        _objective_row(2, "collision_speed_anti_substitution", "collision_speed_substitution_constraint", 2),
        _objective_row(3, "success_context_retention", "context_retention_constraint", 1),
        _objective_row(4, "positive_reference_preservation", "positive_transition_reference", 1),
        _objective_row(5, "full_panel_accounting", "all_transition_constraints", 7),
    ]
    carryforward_rows = [
        _carryforward_row(1, "offtrack_persistence_constraint", "persistent_offtrack_reduction"),
        _carryforward_row(2, "offtrack_persistence_constraint", "persistent_offtrack_reduction"),
        _carryforward_row(3, "collision_speed_substitution_constraint", "collision_speed_anti_substitution"),
        _carryforward_row(4, "collision_speed_substitution_constraint", "collision_speed_anti_substitution"),
        _carryforward_row(5, "context_retention_constraint", "success_context_retention"),
        _carryforward_row(6, "positive_transition_reference", "positive_reference_preservation"),
        _carryforward_row(7, "full_panel_accounting_constraint", "full_panel_accounting"),
    ]
    write_json(m2941_dir / "summary.json", {"status_pass": True, "gate_matrix_pass": True})
    write_csv_rows(
        m2941_dir / "candidate_route_rows.csv",
        [{"candidate_route_id": "m2941-candidate-route-0001", "route_family": "constraint_balanced"}],
    )
    write_csv_rows(m2941_dir / "objective_balance_rows.csv", objective_rows)
    write_csv_rows(m2941_dir / "constraint_carryforward_rows.csv", carryforward_rows)
    write_csv_rows(m2941_dir / "blocked_shortcut_rows.csv", [{"shortcut_id": "fixture", "status_pass": True}])
    write_csv_rows(m2941_dir / "actor_contract_guard_rows.csv", [{"guard_id": "fixture", "status_pass": True}])
    write_csv_rows(m2941_dir / "claim_boundary_rows.csv", [{"claim_id": "fixture", "status_pass": True}])
    write_csv_rows(m2941_dir / "gate_matrix.csv", [{"gate_id": "fixture", "status_pass": True}])
    m2942_audit.write_text("M2942 accepts M2941 complete claim-safe materialization.\n", encoding="utf-8")
    m2943_design.write_text(
        "\n".join(
            [
                "# M2943",
                "- decision: `admit_m2944_actor_head_delta_implementation_contract_materialization_preflight`",
                f"- next: `{m2944.MILESTONE_ID}`",
            ]
        ),
        encoding="utf-8",
    )
    return {"m2941_dir": m2941_dir, "m2942_audit": m2942_audit, "m2943_design": m2943_design}


def test_actor_head_delta_contract_materialization_writes_no_implementation_artifacts(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(m2944, "EXPECTED_CARRYFORWARD_CONSTRAINT_COUNT", 7)
    monkeypatch.setattr(m2944, "EXPECTED_PERSISTENT_OFFTRACK_COUNT", 2)
    monkeypatch.setattr(m2944, "EXPECTED_COLLISION_SPEED_SUBSTITUTION_COUNT", 2)
    monkeypatch.setattr(m2944, "EXPECTED_CONTEXT_RETENTION_CONSTRAINT_COUNT", 1)
    monkeypatch.setattr(m2944, "EXPECTED_POSITIVE_REFERENCE_COUNT", 1)
    monkeypatch.setattr(m2944, "EXPECTED_FULL_PANEL_COUNT", 7)
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m2944"
    doc_path = tmp_path / "m2944.md"
    follow_up = tmp_path / "m2945.json"

    summary = m2944.run_actor_head_delta_implementation_contract_materialization_preflight(
        m2941_dir=paths["m2941_dir"],
        m2942_audit=paths["m2942_audit"],
        m2943_design=paths["m2943_design"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["selected_implementation_design"] == m2944.IMPLEMENTATION_DESIGN
    assert summary["implementation_surface_row_count"] == 1
    assert summary["delta_contract_row_count"] == 7
    assert summary["objective_binding_row_count"] == 5
    assert summary["constraint_traceability_row_count"] == 7
    assert summary["blocked_shortcut_row_count"] == 8
    assert summary["implementation_run"] is False
    assert summary["checkpoint_modification_run"] is False
    assert summary["environment_reset_run"] is False
    assert summary["training_run"] is False
    assert summary["repair_success_claim_made"] is False
    assert doc_path.exists()
    assert read_json(follow_up)["id"] == m2944.NEXT_ID

    surface_rows = _read_csv(output_dir / "implementation_surface_rows.csv")
    delta_rows = _read_csv(output_dir / "delta_contract_rows.csv")
    objective_rows = _read_csv(output_dir / "objective_binding_rows.csv")
    traceability_rows = _read_csv(output_dir / "constraint_traceability_rows.csv")
    shortcut_rows = _read_csv(output_dir / "blocked_shortcut_rows.csv")
    actor_rows = _read_csv(output_dir / "actor_contract_guard_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")

    assert surface_rows[0]["design_family"] == m2944.IMPLEMENTATION_DESIGN
    assert surface_rows[0]["implementation_scheduled"] == "False"
    assert {row["status_pass"] for row in delta_rows} == {"True"}
    assert {row["status_pass"] for row in objective_rows} == {"True"}
    assert {row["actor_visible"] for row in traceability_rows} == {"False"}
    assert {row["implementation_scheduled"] for row in traceability_rows} == {"False"}
    assert {row["status_pass"] for row in shortcut_rows} == {"True"}
    assert {row["claim_made"] for row in shortcut_rows} == {"False"}
    assert {row["status_pass"] for row in actor_rows} == {"True"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
