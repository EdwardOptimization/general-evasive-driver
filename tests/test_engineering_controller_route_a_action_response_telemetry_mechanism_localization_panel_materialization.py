from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import write_csv_rows, write_json
from autodrift import (
    engineering_controller_route_a_action_response_telemetry_mechanism_localization_panel_materialization as m2766,
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m2764_dir = root / "m2764"
    m2762_dir = root / "m2762"
    m2764_dir.mkdir()
    m2762_dir.mkdir()
    action_rows = []
    telemetry_rows = []
    containment_rows = []
    mechanism_rows = []
    for index in range(12):
        resolution_id = f"m2764-probe-resolution-{index + 1:04d}"
        candidate_id = f"m2753-cross-axis-candidate-{index + 1:04d}"
        collision = index in {0, 7, 8}
        offtrack = not collision and index < 10
        termination = "obstacle_collision" if collision else "off_track" if offtrack else ""
        action_rows.append(
            {
                "probe_id": f"m2764-action-response-probe-{index + 1:04d}",
                "probe_resolution_id": resolution_id,
                "candidate_id": candidate_id,
                "localization_id": f"m2756-localization-{index + 1:04d}",
                "task_source_id": f"m1680-spec-{index + 1:04d}",
                "failure_family": "collision_negative_clearance" if collision else "offtrack_positive_clearance",
                "previous_command": 0.2,
                "previous_command_source": "policy_action_trace_zero_bootstrap",
                "current_action": 0.3,
                "current_action_source": "policy_action_trace",
                "trace_delta_proxy": 0.04,
                "trace_delta_source": "current_action_minus_previous_command",
                "plan_first_action_error_proxy": 0.04,
                "plan_first_action_error_source": "policy_action_trace_delta_fallback",
                "speed_response_proxy": 12.0,
                "yaw_response_proxy": 0.3,
                "beta_response_proxy": 0.2,
                "finite_metric": True,
                "m2762_contract_satisfied": True,
                "action_response_labels_actor_visible": False,
            }
        )
        telemetry_rows.append(
            {
                "probe_id": f"m2764-action-response-probe-{index + 1:04d}",
                "probe_resolution_id": resolution_id,
                "candidate_id": candidate_id,
                "localization_id": f"m2756-localization-{index + 1:04d}",
                "task_source_id": f"m1680-spec-{index + 1:04d}",
                "failure_family": "collision_negative_clearance" if collision else "offtrack_positive_clearance",
                "m2764_finite_metric": True,
                "finite_metric_improved_from_m2759": True,
                "m2759_row_backfilled": False,
                "actor_visible_allowed": False,
                "hidden_oracle_actor_input_required": False,
                "actor_input_contract_changed": False,
            }
        )
        containment_rows.append(
            {
                "probe_id": f"m2764-containment-probe-{index + 1:04d}",
                "probe_resolution_id": resolution_id,
                "candidate_id": candidate_id,
                "localization_id": f"m2756-localization-{index + 1:04d}",
                "task_source_id": f"m1680-spec-{index + 1:04d}",
                "failure_family": "collision_negative_clearance" if collision else "offtrack_positive_clearance",
                "termination_reason": termination,
                "min_clearance_margin": -0.2 if collision else 5.0,
                "obstacle_completed": not collision and not offtrack,
                "containment_failure_flag": offtrack,
                "collision_risk_flag": collision,
                "containment_labels_actor_visible": False,
            }
        )
        mechanism_rows.append(
            {
                "mechanism_context_id": f"m2764-mechanism-{index + 1:04d}",
                "probe_resolution_id": resolution_id,
                "candidate_id": candidate_id,
                "mechanism_tag": "obstacle_timing_context" if collision else "track_containment_context",
                "mechanism_tag_actor_visible": False,
            }
        )
    write_json(
        m2764_dir / "summary.json",
        {
            "status_pass": True,
            "action_response_probe_row_count": 12,
            "telemetry_coverage_row_count": 12,
            "containment_probe_row_count": 12,
            "guardrail_context_row_count": 31,
            "finite_metric_true_count": 12,
            "telemetry_coverage_improved_count": 12,
            "m2759_rows_backfilled": False,
        },
    )
    write_csv_rows(m2764_dir / "action_response_probe_rows.csv", action_rows)
    write_csv_rows(m2764_dir / "telemetry_coverage_rows.csv", telemetry_rows)
    write_csv_rows(m2764_dir / "containment_probe_rows.csv", containment_rows)
    write_csv_rows(m2764_dir / "mechanism_context_rows.csv", mechanism_rows)
    write_csv_rows(
        m2764_dir / "guardrail_context_rows.csv",
        [
            {
                "guardrail_context_id": f"m2764-guardrail-{index + 1:04d}",
                "guardrail_source": "prior_panel",
                "execution_run": False,
                "ordinary_success_denominator_allowed": False,
                "protected_rows_in_success_denominator": False,
                "actor_visible_allowed": False,
            }
            for index in range(31)
        ],
    )
    write_csv_rows(
        m2764_dir / "actor_contract_guard_rows.csv",
        [
            {"guard_id": "obs", "guard_family": "p0_observation_dim", "observed": 72, "expected": 72, "status_pass": True},
            {"guard_id": "act", "guard_family": "action_dim", "observed": 3, "expected": 3, "status_pass": True},
        ],
    )
    write_csv_rows(m2764_dir / "claim_boundary_rows.csv", [{"claim_id": "claim", "status_pass": True}])
    write_csv_rows(m2764_dir / "gate_matrix.csv", [{"gate_id": "gate", "status_pass": True}])
    write_csv_rows(
        m2762_dir / "telemetry_schema_contract_rows.csv",
        [
            {"contract_id": "c1", "output_column": "previous_command", "schema_status_pass": True},
            {"contract_id": "c2", "output_column": "current_action", "schema_status_pass": True},
            {"contract_id": "c3", "output_column": "plan_first_action_error_proxy", "schema_status_pass": True},
            {"contract_id": "c4", "output_column": "finite_metric", "schema_status_pass": True},
        ],
    )
    audit = root / "m2765.md"
    audit.write_text("M2765 routes to m2766 mechanism localization panel.\n", encoding="utf-8")
    return {"m2764_dir": m2764_dir, "m2762_dir": m2762_dir, "audit": audit}


def test_m2766_materializes_mechanism_localization_panel(tmp_path: Path) -> None:
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m2766"
    doc_path = tmp_path / "m2766.md"
    follow_up = tmp_path / "m2767.json"

    summary = m2766.run(
        m2764_dir=paths["m2764_dir"],
        m2765_audit=paths["audit"],
        m2762_dir=paths["m2762_dir"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["telemetry_join_row_count"] == 12
    assert summary["mechanism_localization_row_count"] == 12
    assert summary["repair_admission_row_count"] == 12
    assert summary["finite_telemetry_join_count"] == 12
    assert summary["telemetry_coverage_improved_count"] == 12
    assert summary["m2759_rows_backfilled"] is False
    assert summary["guardrail_context_row_count"] == 31
    assert summary["guardrail_execution"] is False
    assert summary["protected_rows_in_success_denominator"] is False
    assert summary["actor_contract_guard_rows_pass"] is True
    assert summary["diagnostic_labels_actor_visible"] is False
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert doc_path.exists()
    assert follow_up.exists()

    join_rows = _read_csv(output_dir / "telemetry_join_rows.csv")
    mechanism_rows = _read_csv(output_dir / "mechanism_localization_rows.csv")
    repair_rows = _read_csv(output_dir / "repair_admission_rows.csv")
    guardrail_rows = _read_csv(output_dir / "guardrail_context_rows.csv")
    assert {row["finite_metric"] for row in join_rows} == {"True"}
    assert {row["m2764_telemetry_coverage_improved"] for row in join_rows} == {"True"}
    assert {row["m2759_row_backfilled"] for row in join_rows} == {"False"}
    assert {"obstacle_timing_context", "track_containment_context"}.issubset(
        {row["primary_mechanism"] for row in mechanism_rows}
    )
    assert {row["ranking_run"] for row in mechanism_rows} == {"False"}
    assert {row["ranking_run"] for row in repair_rows} == {"False"}
    assert {row["winner_selected"] for row in repair_rows} == {"False"}
    assert {row["execution_run"] for row in guardrail_rows} == {"False"}
    assert {row["protected_rows_in_success_denominator"] for row in guardrail_rows} == {"False"}
    assert {row["status_pass"] for row in _read_csv(output_dir / "gate_matrix.csv")} == {"True"}
