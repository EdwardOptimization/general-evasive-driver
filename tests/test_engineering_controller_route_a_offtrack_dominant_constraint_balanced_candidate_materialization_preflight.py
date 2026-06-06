from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
import autodrift.engineering_controller_route_a_offtrack_dominant_constraint_balanced_candidate_materialization_preflight as m2941


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _transition_row(
    *,
    index: int,
    constraint_family: str,
    baseline: str,
    repair: str,
) -> dict[str, object]:
    return {
        "transition_constraint_id": f"m2937-transition-constraint-{index:04d}",
        "panel_row_id": f"panel-{index}",
        "constraint_family": constraint_family,
        "transition_bucket": f"{baseline}->{repair}",
        "source_milestone": "m2934",
        "task_family": "T4" if index % 2 else "T5",
        "env_template_family": "fixture_env",
        "window_tag": "fixture_window",
        "actor_visible": False,
        "execution_scheduled": False,
        "ranking_claim_made": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
    }


def _specialized_rows(rows: list[dict[str, object]], family: str) -> list[dict[str, object]]:
    out = []
    for index, row in enumerate((item for item in rows if item["constraint_family"] == family), start=1):
        out.append(
            {
                "constraint_id": f"m2937-{family}-{index:04d}",
                "constraint_family": family,
                "source_transition_constraint_id": row["transition_constraint_id"],
                "panel_row_id": row["panel_row_id"],
                "transition_bucket": row["transition_bucket"],
                "actor_visible": False,
                "ranking_allowed": False,
                "diagnostic_only_no_verdict": True,
            }
        )
    return out


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m2937_dir = root / "m2937"
    m2938_audit = root / "m2938.md"
    m2939_synthesis = root / "m2939.md"
    m2940_design = root / "m2940.md"
    rows = [
        _transition_row(
            index=1,
            constraint_family="offtrack_persistence_constraint",
            baseline="offtrack",
            repair="offtrack",
        ),
        _transition_row(
            index=2,
            constraint_family="offtrack_persistence_constraint",
            baseline="offtrack",
            repair="offtrack",
        ),
        _transition_row(
            index=3,
            constraint_family="collision_speed_substitution_constraint",
            baseline="offtrack",
            repair="collision",
        ),
        _transition_row(
            index=4,
            constraint_family="collision_speed_substitution_constraint",
            baseline="offtrack",
            repair="speed_too_low",
        ),
        _transition_row(
            index=5,
            constraint_family="positive_transition_reference",
            baseline="offtrack",
            repair="success",
        ),
        _transition_row(
            index=6,
            constraint_family="context_retention_constraint",
            baseline="success",
            repair="offtrack",
        ),
        _transition_row(
            index=7,
            constraint_family="full_panel_accounting_constraint",
            baseline="success",
            repair="success",
        ),
    ]
    write_json(m2937_dir / "summary.json", {"status_pass": True, "gate_matrix_pass": True})
    write_csv_rows(m2937_dir / "transition_constraint_rows.csv", rows)
    write_csv_rows(
        m2937_dir / "offtrack_persistence_constraint_rows.csv",
        _specialized_rows(rows, "offtrack_persistence_constraint"),
    )
    write_csv_rows(
        m2937_dir / "collision_speed_substitution_constraint_rows.csv",
        _specialized_rows(rows, "collision_speed_substitution_constraint"),
    )
    write_csv_rows(
        m2937_dir / "context_retention_constraint_rows.csv",
        _specialized_rows(rows, "context_retention_constraint"),
    )
    write_csv_rows(
        m2937_dir / "positive_transition_reference_rows.csv",
        _specialized_rows(rows, "positive_transition_reference"),
    )
    write_csv_rows(
        m2937_dir / "candidate_surface_rows.csv",
        [
            {
                "candidate_surface_id": f"m2937-candidate-surface-{index:04d}",
                "surface_family": family,
                "source_row_count": count,
                "actor_visible": False,
            }
            for index, (family, count) in enumerate(
                [
                    ("full_panel_accounting", 7),
                    ("persistent_offtrack_pressure", 2),
                    ("collision_speed_substitution_guard", 2),
                    ("context_retention_guard", 1),
                    ("positive_reference_preservation", 1),
                ],
                start=1,
            )
        ],
    )
    write_csv_rows(m2937_dir / "actor_contract_guard_rows.csv", [{"guard_id": "fixture", "status_pass": True}])
    write_csv_rows(m2937_dir / "claim_boundary_rows.csv", [{"claim_id": "fixture", "status_pass": True}])
    write_csv_rows(m2937_dir / "gate_matrix.csv", [{"gate_id": "fixture", "status_pass": True}])
    m2938_audit.write_text("M2938 accepts M2937 complete claim-safe materialization.\n", encoding="utf-8")
    m2939_synthesis.write_text("decision: continue_to_m2940_tradeoff_aware_candidate_design\n", encoding="utf-8")
    m2940_design.write_text(
        "\n".join(
            [
                "# M2940",
                "- decision: `admit_m2941_constraint_balanced_candidate_materialization_preflight`",
                f"- next: `{m2941.MILESTONE_ID}`",
            ]
        ),
        encoding="utf-8",
    )
    return {
        "m2937_dir": m2937_dir,
        "m2938_audit": m2938_audit,
        "m2939_synthesis": m2939_synthesis,
        "m2940_design": m2940_design,
    }


def test_constraint_balanced_candidate_materialization_writes_no_execution_artifacts(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(m2941, "EXPECTED_TRANSITION_CONSTRAINT_COUNT", 7)
    monkeypatch.setattr(m2941, "EXPECTED_PERSISTENT_OFFTRACK_COUNT", 2)
    monkeypatch.setattr(m2941, "EXPECTED_COLLISION_SPEED_SUBSTITUTION_COUNT", 2)
    monkeypatch.setattr(m2941, "EXPECTED_CONTEXT_RETENTION_CONSTRAINT_COUNT", 1)
    monkeypatch.setattr(m2941, "EXPECTED_POSITIVE_REFERENCE_COUNT", 1)
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m2941"
    doc_path = tmp_path / "m2941.md"
    follow_up = tmp_path / "m2942.json"

    summary = m2941.run_constraint_balanced_candidate_materialization_preflight(
        m2937_dir=paths["m2937_dir"],
        m2938_audit=paths["m2938_audit"],
        m2939_synthesis=paths["m2939_synthesis"],
        m2940_design=paths["m2940_design"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["selected_candidate_route"] == m2941.ROUTE_FAMILY
    assert summary["candidate_route_row_count"] == 1
    assert summary["objective_balance_row_count"] == 5
    assert summary["constraint_carryforward_row_count"] == 7
    assert summary["blocked_shortcut_row_count"] == 7
    assert summary["environment_reset_run"] is False
    assert summary["training_run"] is False
    assert summary["repair_success_claim_made"] is False
    assert summary["driver_performance_claim_made"] is False
    assert doc_path.exists()
    assert read_json(follow_up)["id"] == m2941.NEXT_ID

    route_rows = _read_csv(output_dir / "candidate_route_rows.csv")
    objective_rows = _read_csv(output_dir / "objective_balance_rows.csv")
    carryforward_rows = _read_csv(output_dir / "constraint_carryforward_rows.csv")
    shortcut_rows = _read_csv(output_dir / "blocked_shortcut_rows.csv")
    actor_rows = _read_csv(output_dir / "actor_contract_guard_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")
    objective_counts = {row["objective_family"]: row["source_row_count"] for row in objective_rows}

    assert route_rows[0]["route_family"] == m2941.ROUTE_FAMILY
    assert route_rows[0]["execution_scheduled"] == "False"
    assert objective_counts["persistent_offtrack_reduction"] == "2"
    assert objective_counts["collision_speed_anti_substitution"] == "2"
    assert objective_counts["success_context_retention"] == "1"
    assert objective_counts["positive_reference_preservation"] == "1"
    assert objective_counts["full_panel_accounting"] == "7"
    assert {row["actor_visible"] for row in carryforward_rows} == {"False"}
    assert {row["evaluator_side_only"] for row in carryforward_rows} == {"True"}
    assert {row["status_pass"] for row in shortcut_rows} == {"True"}
    assert {row["claim_made"] for row in shortcut_rows} == {"False"}
    assert {row["status_pass"] for row in actor_rows} == {"True"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
