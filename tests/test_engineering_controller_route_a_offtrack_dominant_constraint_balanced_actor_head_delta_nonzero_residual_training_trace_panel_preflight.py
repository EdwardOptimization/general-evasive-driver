from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
import autodrift.engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_training_trace_panel_preflight as m2973


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m2970_dir = root / "m2970"
    m2960_dir = root / "m2960"
    m2970_dir.mkdir()
    m2960_dir.mkdir()
    write_json(
        m2970_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
        },
    )
    candidate_rows = [
        {
            "training_admission_candidate_id": "m2970-candidate-0001",
            "execution_candidate_id": "m2960-execution-candidate-0001",
            "workload_id": "workload-1",
            "task_family": "T4",
            "outcome_family": "off_track",
            "objective_family": "offtrack_recovery_residual_objective",
            "actor_visible_label": False,
        },
        {
            "training_admission_candidate_id": "m2970-candidate-0002",
            "execution_candidate_id": "m2960-execution-candidate-0002",
            "workload_id": "workload-2",
            "task_family": "T5",
            "outcome_family": "collision",
            "objective_family": "collision_clearance_residual_objective",
            "actor_visible_label": False,
        },
    ]
    success_rows = [
        {
            "guard_id": "m2970-success-guard-0001",
            "execution_candidate_id": "m2960-execution-candidate-0003",
            "guard_family": "success_identity_guard",
            "positive_training_target": False,
            "training_scheduled": False,
        }
    ]
    stale_rows = [
        {
            "guardrail_id": "m2970-stale-guardrail-0001",
            "guardrail_family": "actor_head_delta_execution_admission_blocked_stale_fixed_surface",
            "execution_run": False,
        }
    ]
    write_csv_rows(m2970_dir / "training_admission_candidate_rows.csv", candidate_rows)
    write_csv_rows(m2970_dir / "training_admission_guard_rows.csv", [{"guard_id": "guard", "status_pass": True}])
    write_csv_rows(m2970_dir / "success_identity_guard_rows.csv", success_rows)
    write_csv_rows(m2970_dir / "stale_guardrail_rows.csv", stale_rows)
    write_csv_rows(m2970_dir / "gate_matrix.csv", [{"gate_id": "m2970-gate", "status_pass": True}])

    bounded_rows = [
        {
            "execution_candidate_id": "m2960-execution-candidate-0001",
            "residual_trace_count": 8,
            "hidden_oracle_actor_input_required": False,
            "future_target_actor_input_required": False,
        },
        {
            "execution_candidate_id": "m2960-execution-candidate-0002",
            "residual_trace_count": 0,
            "hidden_oracle_actor_input_required": False,
            "future_target_actor_input_required": False,
        },
        {
            "execution_candidate_id": "m2960-execution-candidate-0003",
            "residual_trace_count": 5,
            "hidden_oracle_actor_input_required": False,
            "future_target_actor_input_required": False,
        },
    ]
    contract_rows = [
        {
            "execution_candidate_id": "m2960-execution-candidate-0001",
            "residual_trace_count": 8,
            "actor_observation_dim": 72,
            "actor_action_dim": 3,
            "parent_checkpoint_loaded_read_only": True,
            "zero_residual_identity_mode": True,
            "residual_delta_abs_max": 0.0,
            "hidden_oracle_actor_input_required": False,
            "future_target_actor_input_required": False,
        },
        {
            "execution_candidate_id": "m2960-execution-candidate-0002",
            "residual_trace_count": 0,
            "actor_observation_dim": 72,
            "actor_action_dim": 3,
            "parent_checkpoint_loaded_read_only": True,
            "zero_residual_identity_mode": True,
            "residual_delta_abs_max": 0.0,
            "hidden_oracle_actor_input_required": False,
            "future_target_actor_input_required": False,
        },
        {
            "execution_candidate_id": "m2960-execution-candidate-0003",
            "residual_trace_count": 5,
            "actor_observation_dim": 72,
            "actor_action_dim": 3,
            "parent_checkpoint_loaded_read_only": True,
            "zero_residual_identity_mode": True,
            "residual_delta_abs_max": 0.0,
            "hidden_oracle_actor_input_required": False,
            "future_target_actor_input_required": False,
        },
    ]
    write_json(m2960_dir / "summary.json", {"status_pass": True, "gate_matrix_pass": True})
    write_csv_rows(m2960_dir / "bounded_execution_rows.csv", bounded_rows)
    write_csv_rows(m2960_dir / "actor_head_delta_contract_execution_rows.csv", contract_rows)

    m2971_audit = root / "m2971.md"
    m2972_design = root / "m2972.md"
    m2971_audit.write_text(
        "accept_m2970_nonzero_residual_training_admission_materialization_claim_safe_route_to_m2972_training_preflight_design\n",
        encoding="utf-8",
    )
    m2972_design.write_text(m2973.MILESTONE_ID + "\n", encoding="utf-8")
    return {
        "m2970_dir": m2970_dir,
        "m2971_audit": m2971_audit,
        "m2972_design": m2972_design,
        "m2960_dir": m2960_dir,
    }


def test_m2973_trace_panel_rows_keep_raw_trace_missing_explicit() -> None:
    candidate_rows = [
        {
            "training_admission_candidate_id": "candidate-1",
            "execution_candidate_id": "exec-1",
            "workload_id": "workload-1",
            "task_family": "T4",
            "outcome_family": "off_track",
            "objective_family": "offtrack_recovery_residual_objective",
        }
    ]
    execution_by_candidate = {"exec-1": {"execution_candidate_id": "exec-1", "residual_trace_count": "12"}}
    contract_by_candidate = {
        "exec-1": {
            "execution_candidate_id": "exec-1",
            "residual_trace_count": "12",
            "actor_observation_dim": "72",
            "actor_action_dim": "3",
            "parent_checkpoint_loaded_read_only": "True",
            "zero_residual_identity_mode": "True",
            "residual_delta_abs_max": "0.0",
        }
    }

    rows = m2973.build_trace_panel_rows(
        candidate_rows,
        execution_by_candidate=execution_by_candidate,
        contract_by_candidate=contract_by_candidate,
    )

    assert rows[0]["trace_available"] is True
    assert rows[0]["raw_trace_persisted"] is False
    assert rows[0]["trace_step_count"] == 12
    assert rows[0]["training_started"] is False
    assert rows[0]["ppo_run"] is False
    assert rows[0]["checkpoint_mutated"] is False


def test_run_m2973_trace_panel_preflight_writes_claim_safe_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m2973, "EXPECTED_TRAINING_CANDIDATE_COUNT", 2)
    monkeypatch.setattr(m2973, "EXPECTED_SUCCESS_IDENTITY_GUARD_COUNT", 1)
    monkeypatch.setattr(m2973, "EXPECTED_STALE_GUARDRAIL_COUNT", 1)
    monkeypatch.setattr(m2973, "EXPECTED_OUTCOME_COUNTS", {"off_track": 1, "collision": 1})
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m2973"
    doc_path = tmp_path / "m2973.md"
    follow_up = tmp_path / "m2974.json"

    summary = m2973.run_training_trace_panel_preflight(
        m2970_dir=paths["m2970_dir"],
        m2971_audit=paths["m2971_audit"],
        m2972_design=paths["m2972_design"],
        m2960_dir=paths["m2960_dir"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["training_trace_panel_row_count"] == 2
    assert summary["trace_guard_row_count"] == 2
    assert summary["trace_availability_row_count"] == 4
    assert summary["trace_metadata_present_count"] == 2
    assert summary["raw_trace_persisted_count"] == 0
    assert summary["trace_panel_ready_for_residual_fitting"] is False
    assert summary["training_run"] is False
    assert summary["ppo_run"] is False
    assert summary["validation_run"] is False
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert read_json(follow_up)["id"] == m2973.NEXT_ID

    panel_rows = _read_csv(output_dir / "trace_panel_rows.csv")
    guard_rows = _read_csv(output_dir / "trace_guard_rows.csv")
    availability_rows = _read_csv(output_dir / "trace_availability_rows.csv")
    actor_rows = _read_csv(output_dir / "actor_contract_guard_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")

    assert len(panel_rows) == 2
    assert {row["training_started"] for row in panel_rows} == {"False"}
    assert {row["ppo_run"] for row in panel_rows} == {"False"}
    assert {row["raw_trace_persisted"] for row in panel_rows} == {"False"}
    assert {row["validation_denominator_allowed"] for row in panel_rows} == {"False"}
    assert len(guard_rows) == 2
    assert {row["positive_training_target"] for row in guard_rows} == {"False"}
    assert {row["checkpoint_mutated"] for row in guard_rows} == {"False"}
    assert len(availability_rows) == 4
    assert any(row["availability_status"] == "metadata_only_raw_trace_missing" for row in availability_rows)
    assert {row["status_pass"] for row in actor_rows} == {"True"}
    assert all(row["claim_made"] == "False" for row in claim_rows if row["allowed_in_m2973"] == "False")
    assert {row["status_pass"] for row in gate_rows} == {"True"}
