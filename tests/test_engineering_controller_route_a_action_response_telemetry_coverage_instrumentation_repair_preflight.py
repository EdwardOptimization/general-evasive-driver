from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import write_csv_rows, write_json
from autodrift import engineering_controller_route_a_action_response_telemetry_coverage_instrumentation_repair_preflight as m2762


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_m2759_source(root: Path) -> Path:
    m2759_dir = root / "m2759"
    m2759_dir.mkdir()
    action_rows = []
    execution_rows = []
    for index in range(12):
        resolution_id = f"m2759-probe-resolution-{index + 1:04d}"
        action_rows.append(
            {
                "probe_id": f"m2759-action-response-probe-{index + 1:04d}",
                "probe_resolution_id": resolution_id,
                "candidate_id": f"candidate-{index + 1:04d}",
                "localization_id": f"localization-{index + 1:04d}",
                "task_source_id": f"m1680-spec-{index + 1:04d}",
                "failure_family": "collision_negative_clearance" if index < 3 else "offtrack_positive_clearance",
                "previous_command": "",
                "current_action": 0.1 + index,
                "actuator_lag_proxy": "",
                "actuator_error_proxy": "",
                "action_rate_mean": 0.1 + index,
                "action_rate_peak": 0.1 + index,
                "command_response_phase_lag_proxy": 0.1 + index,
                "speed_response_proxy": 10.0 + index,
                "yaw_response_proxy": 0.2 + index,
                "beta_response_proxy": 0.03 + index,
                "plan_first_action_error_proxy": "",
                "finite_metric": False,
                "action_response_labels_actor_visible": False,
                "diagnostic_only_no_verdict": True,
                "claim_boundary": "m2759 diagnostic",
            }
        )
        execution_rows.append(
            {
                "probe_resolution_id": resolution_id,
                "candidate_id": f"candidate-{index + 1:04d}",
                "localization_id": f"localization-{index + 1:04d}",
                "task_source_id": f"m1680-spec-{index + 1:04d}",
                "failure_family": "collision_negative_clearance" if index < 3 else "offtrack_positive_clearance",
                "termination_reason": "off_track" if index < 10 else "",
                "plan_action_rate_mean": "",
                "plan_first_action_error_mean": "",
                "action_rate_mean": 0.1 + index,
                "actor_input_contract_changed": False,
                "hidden_oracle_actor_input_required": False,
                "source_build_run": False,
                "adapter_probe_run": False,
                "external_simulation_run": False,
                "ranking_run": False,
                "winner_selected": False,
                "checkpoint_promoted": False,
                "success_rate_verdict_claim_made": False,
                "repair_success_claim_made": False,
                "driver_performance_claim_made": False,
                "validation_readiness_claim_made": False,
                "validation_result_claim_made": False,
                "paper_claim_made": False,
                "current_sim_verdict_claim_made": False,
                "high_fidelity_validation_claim_made": False,
                "full_ideal_driver_gate_passed": False,
                "level3_self_id_claim_made": False,
            }
        )
    write_json(
        m2759_dir / "summary.json",
        {
            "status_pass": True,
            "action_response_probe_row_count": 12,
            "probe_execution_row_count": 12,
            "guardrail_context_row_count": 31,
        },
    )
    write_csv_rows(m2759_dir / "action_response_probe_rows.csv", action_rows)
    write_csv_rows(m2759_dir / "probe_execution_rows.csv", execution_rows)
    write_csv_rows(
        m2759_dir / "guardrail_context_rows.csv",
        [
            {
                "m2759_guardrail_id": f"guard-{index + 1:04d}",
                "execution_run": False,
                "ordinary_success_denominator_allowed": False,
                "protected_rows_in_success_denominator": False,
                "actor_visible_allowed": False,
            }
            for index in range(31)
        ],
    )
    write_csv_rows(
        m2759_dir / "actor_contract_guard_rows.csv",
        [
            {
                "guard_id": "obs",
                "guard_family": "p0_observation_dim",
                "observed": 72,
                "expected": 72,
                "status_pass": True,
                "actor_visible_allowed": False,
            },
            {
                "guard_id": "action",
                "guard_family": "action_dim",
                "observed": 3,
                "expected": 3,
                "status_pass": True,
                "actor_visible_allowed": False,
            },
        ],
    )
    write_csv_rows(m2759_dir / "claim_boundary_rows.csv", [{"claim_id": "claim", "status_pass": True}])
    write_csv_rows(m2759_dir / "gate_matrix.csv", [{"gate_id": "gate", "status_pass": True}])
    return m2759_dir


def test_m2762_materializes_telemetry_coverage_contract(tmp_path: Path) -> None:
    m2759_dir = _write_m2759_source(tmp_path)
    synthesis = tmp_path / "m2761.md"
    synthesis.write_text("M2761 routes to m2762 telemetry coverage instrumentation repair.", encoding="utf-8")
    output_dir = tmp_path / "out"
    doc = tmp_path / "doc.md"
    follow_up = tmp_path / "m2763.json"

    summary = m2762.run(
        m2759_dir=m2759_dir,
        m2761_synthesis=synthesis,
        output_dir=output_dir,
        doc_path=doc,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["m2759_action_response_row_count"] == 12
    assert summary["m2759_incoming_finite_metric_false_count"] == 12
    assert summary["previous_command_missing_count"] == 12
    assert summary["plan_first_action_error_missing_count"] == 12
    assert summary["telemetry_schema_contract_row_count"] >= 6
    assert summary["m2759_rows_backfilled"] is False
    assert follow_up.exists()
    assert doc.exists()

    gap_rows = _read_csv(output_dir / "telemetry_coverage_gap_rows.csv")
    assert len(gap_rows) == 12
    assert {row["incoming_finite_metric"] for row in gap_rows} == {"False"}
    assert {row["gap_class"] for row in gap_rows} == {"previous_command_and_plan_first_action_missing"}
    assert {row["m2759_row_backfilled"] for row in gap_rows} == {"False"}
    assert {row["actor_visible_allowed"] for row in gap_rows} == {"False"}
    assert {row["hidden_oracle_actor_input_required"] for row in gap_rows} == {"False"}

    schema_rows = _read_csv(output_dir / "telemetry_schema_contract_rows.csv")
    assert "previous_command" in {row["output_column"] for row in schema_rows}
    assert "plan_first_action_error_proxy" in {row["output_column"] for row in schema_rows}
    assert {row["actor_visible_allowed"] for row in schema_rows} == {"False"}
    assert {row["hidden_oracle_actor_input_required"] for row in schema_rows} == {"False"}
    assert {row["actor_input_contract_changed"] for row in schema_rows} == {"False"}

    gates = _read_csv(output_dir / "gate_matrix.csv")
    assert {row["status_pass"] for row in gates} == {"True"}


def test_m2762_preserves_source_gap_without_backfill(tmp_path: Path) -> None:
    m2759_dir = _write_m2759_source(tmp_path)
    synthesis = tmp_path / "m2761.md"
    synthesis.write_text("m2762", encoding="utf-8")

    m2762.run(
        m2759_dir=m2759_dir,
        m2761_synthesis=synthesis,
        output_dir=tmp_path / "out",
        doc_path=tmp_path / "doc.md",
        follow_up_manifest=tmp_path / "m2763.json",
    )

    source_rows = _read_csv(m2759_dir / "action_response_probe_rows.csv")
    assert {row["previous_command"] for row in source_rows} == {""}
    assert {row["plan_first_action_error_proxy"] for row in source_rows} == {""}
    assert {row["finite_metric"] for row in source_rows} == {"False"}
