import csv
import json
from pathlib import Path

from autodrift.engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_objective_materialization import (
    RESULT_CLASS_PASS,
    run_objective_materialization,
)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_objective_materialization_writes_protected_gate_bundle(tmp_path):
    design_doc = tmp_path / "m2652.md"
    localization_summary = tmp_path / "summary.json"
    localization_findings = tmp_path / "findings.json"
    regression_rows = tmp_path / "regression.csv"
    gate_rows = tmp_path / "m2648_gates.csv"
    doc_path = tmp_path / "m2653.md"
    follow_up_manifest = tmp_path / "m2654.json"
    output_dir = tmp_path / "run"

    design_doc.write_text(
        "severity_proxy_non_regression obstacle_penetration_non_regression",
        encoding="utf-8",
    )
    localization_summary.write_text(
        json.dumps(
            {
                "real_behavior_regression_localized": True,
                "likely_severity_proxy_component_driver": "obstacle_penetration_proxy_worsened",
            }
        ),
        encoding="utf-8",
    )
    localization_findings.write_text(
        json.dumps(
            {
                "metric_artifact_detected": False,
                "localization_class": "real_behavior_regression_likely_obstacle_penetration_deepened",
                "regressed_row": {
                    "localization_row_id": "m2650_regressed_row",
                },
            }
        ),
        encoding="utf-8",
    )
    _write_csv(
        regression_rows,
        [
            {
                "localization_row_id": "m2650_regressed_row",
                "seed": 267101,
                "dynamics_axis_id": "fresh_fault_delay_noise",
            }
        ],
    )
    _write_csv(
        gate_rows,
        [
            {
                "gate_id": "target_road_boundary_margin_control",
                "evaluated_row_count": 16,
                "improved_row_count": 16,
                "regressed_row_count": 0,
            },
            {
                "gate_id": "target_drift_collision_recovery_tradeoff",
                "evaluated_row_count": 8,
                "improved_row_count": 8,
                "regressed_row_count": 0,
            },
        ],
    )
    follow_up_manifest.write_text("{}", encoding="utf-8")

    summary = run_objective_materialization(
        output_dir,
        design_doc=design_doc,
        localization_summary=localization_summary,
        localization_findings=localization_findings,
        regression_rows=regression_rows,
        m2648_gate_rows=gate_rows,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
        milestone="m2653-test",
        next_blocker="m2654-test",
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == RESULT_CLASS_PASS
    assert summary["objective_family_row_count"] == 3
    assert summary["protected_component_gate_row_count"] == 4
    assert summary["target_preservation_gate_row_count"] == 2
    assert summary["abort_rule_row_count"] >= 9
    assert summary["gate_matrix_pass"] is True
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_or_oracle_actor_inputs_required"] is False
    assert summary["repair_execution_started"] is False
    assert summary["training_run"] is False
    assert summary["success_rate_computed"] is False
    assert "obstacle_penetration_non_regression" in summary["protected_component_gate_ids"]
    assert doc_path.exists()

    protected_rows = list(
        csv.DictReader((output_dir / "protected_component_gate_rows.csv").open())
    )
    assert {row["component_gate_id"] for row in protected_rows} == {
        "severity_proxy_non_regression",
        "obstacle_penetration_non_regression",
        "minimum_obstacle_clearance_preservation",
        "event_transition_guard",
    }
    matrix_rows = list(csv.DictReader((output_dir / "gate_matrix.csv").open()))
    assert {row["status_pass"] for row in matrix_rows} == {"True"}
