from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
import autodrift.engineering_controller_route_a_post_residual_stop_new_source_broad_failure_target_source_readiness_feasibility_materialization_preflight as m3025


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m3022_dir = root / "m3022"
    m3018_dir = root / "m3018"
    m3015_dir = root / "m3015"
    m3022_dir.mkdir()
    m3018_dir.mkdir()
    m3015_dir.mkdir()

    write_json(
        m3022_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "observation_shape": 72,
            "action_shape": 3,
            "actor_input_contract_changed": False,
            "hidden_oracle_actor_input_detected": False,
            "future_target_actor_input_required": False,
            "source_labels_actor_visible": False,
            "route_labels_actor_visible": False,
            "outcome_labels_actor_visible": False,
            "objective_labels_actor_visible": False,
            "success_progress_labels_actor_visible": False,
            "verdict_labels_actor_visible": False,
            "ttc_actor_input_required": False,
        },
    )
    row_assignments = [
        {
            "row_assignment_id": "m3022-row-assignment-0001",
            "source_localization_row_id": "loc-1",
            "source_episode_row_index": "1",
            "task_source_id": "src-1",
            "profile_name": "candidate",
            "profile_binding_name": "candidate",
            "binding_role": "candidate",
            "task_family": "T4",
            "source_edge": "edge-a",
            "window_tag": "window-a",
            "strata": "strata-a",
            "outcome_family": "off_track",
            "failure_family": "offtrack_recovery_failure",
            "primary_failure_mode": "off_track",
            "objective_family": "offtrack_recovery_broad_failure_contract",
            "future_target_materialization_allowed": True,
            "diagnostic_success": False,
            "diagnostic_non_success": True,
        },
        {
            "row_assignment_id": "m3022-row-assignment-0002",
            "source_localization_row_id": "loc-2",
            "source_episode_row_index": "2",
            "task_source_id": "src-2",
            "profile_name": "candidate",
            "profile_binding_name": "candidate",
            "binding_role": "candidate",
            "task_family": "T5",
            "source_edge": "edge-b",
            "window_tag": "window-b",
            "strata": "strata-b",
            "outcome_family": "collision",
            "failure_family": "collision_clearance_failure",
            "primary_failure_mode": "collision",
            "objective_family": "collision_clearance_guard_contract",
            "future_target_materialization_allowed": True,
            "diagnostic_success": False,
            "diagnostic_non_success": True,
        },
        {
            "row_assignment_id": "m3022-row-assignment-0003",
            "source_localization_row_id": "loc-3",
            "source_episode_row_index": "3",
            "task_source_id": "src-3",
            "profile_name": "parent",
            "profile_binding_name": "parent",
            "binding_role": "parent",
            "task_family": "T4",
            "source_edge": "edge-c",
            "window_tag": "window-c",
            "strata": "strata-c",
            "outcome_family": "success",
            "failure_family": "success_context",
            "primary_failure_mode": "success_context",
            "objective_family": "success_identity_context_guard",
            "future_target_materialization_allowed": False,
            "diagnostic_success": True,
            "diagnostic_non_success": False,
        },
    ]
    write_csv_rows(m3022_dir / "row_assignment_rows.csv", row_assignments)
    write_csv_rows(m3022_dir / "profile_source_guard_rows.csv", [{"row": "guard"}])
    write_csv_rows(m3022_dir / "actor_contract_guard_rows.csv", [{"status_pass": True}])
    write_csv_rows(m3022_dir / "claim_boundary_rows.csv", [{"status_pass": True}])
    write_csv_rows(m3022_dir / "gate_matrix.csv", [{"status_pass": True}])

    localization_rows = [
        {"localization_row_id": "loc-1", "execution_workload_id": "exec-1"},
        {"localization_row_id": "loc-2", "execution_workload_id": "exec-2"},
        {"localization_row_id": "loc-3", "execution_workload_id": "exec-3"},
    ]
    write_csv_rows(m3018_dir / "failure_localization_rows.csv", localization_rows)
    write_csv_rows(m3018_dir / "profile_source_aggregate_rows.csv", [{"row": "aggregate"}])
    episode_rows = [
        {"execution_workload_id": "exec-1", "return": "1.0"},
        {"execution_workload_id": "exec-2", "return": "2.0"},
        {"execution_workload_id": "exec-3", "return": "3.0"},
    ]
    write_csv_rows(m3015_dir / "episode_rows.csv", episode_rows)
    write_csv_rows(m3015_dir / "execution_guard_rows.csv", [{"row": "guard"}])

    m3023_audit = root / "m3023.md"
    m3023_audit.write_text(m3025.M3023_DECISION, encoding="utf-8")
    m3024_design = root / "m3024.md"
    m3024_design.write_text(m3025.M3024_DECISION, encoding="utf-8")
    return {
        "m3022_dir": m3022_dir,
        "m3018_dir": m3018_dir,
        "m3015_dir": m3015_dir,
        "m3023_audit": m3023_audit,
        "m3024_design": m3024_design,
    }


def test_readiness_rows_preserve_future_targets_and_success_guards(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m3025, "EXPECTED_ROW_ASSIGNMENT_ROWS", 3)
    monkeypatch.setattr(m3025, "EXPECTED_FUTURE_TARGET_ELIGIBLE_ROWS", 2)
    monkeypatch.setattr(m3025, "EXPECTED_SUCCESS_IDENTITY_GUARD_ROWS", 1)
    monkeypatch.setattr(
        m3025,
        "EXPECTED_OBJECTIVE_COUNTS",
        {
            "collision_clearance_guard_contract": 1,
            "offtrack_recovery_broad_failure_contract": 1,
            "success_identity_context_guard": 1,
        },
    )
    monkeypatch.setattr(
        m3025,
        "EXPECTED_FAILURE_COUNTS",
        {
            "collision_clearance_failure": 1,
            "offtrack_recovery_failure": 1,
            "success_context": 1,
        },
    )
    paths = _write_source_artifacts(tmp_path)
    source = m3025.load_source_artifacts(
        m3022_dir=paths["m3022_dir"],
        m3023_audit=paths["m3023_audit"],
        m3024_design=paths["m3024_design"],
        m3018_dir=paths["m3018_dir"],
        m3015_dir=paths["m3015_dir"],
        follow_up_manifest=tmp_path / "m3026.json",
    )

    readiness = m3025.build_target_source_readiness_rows(source)
    blockers = m3025.build_target_source_blocker_rows(readiness)
    success_guards = m3025.build_success_identity_guard_rows(readiness)

    assert len(readiness) == 3
    assert len(blockers) == 2
    assert len(success_guards) == 1
    assert all(row["episode_summary_available"] for row in readiness)
    assert not any(row["episode_summary_accepted_as_raw_trace"] for row in readiness)
    assert not any(row["raw_actor_view_trace_available"] for row in readiness)
    assert not any(row["numeric_target_tensor_materialized"] for row in readiness)
    assert success_guards[0]["success_identity_zero_target_guard"] is True
    assert success_guards[0]["positive_target_candidate"] is False


def test_run_m3025_writes_claim_safe_artifacts_and_followup(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m3025, "EXPECTED_ROW_ASSIGNMENT_ROWS", 3)
    monkeypatch.setattr(m3025, "EXPECTED_FUTURE_TARGET_ELIGIBLE_ROWS", 2)
    monkeypatch.setattr(m3025, "EXPECTED_SUCCESS_IDENTITY_GUARD_ROWS", 1)
    monkeypatch.setattr(
        m3025,
        "EXPECTED_OBJECTIVE_COUNTS",
        {
            "collision_clearance_guard_contract": 1,
            "offtrack_recovery_broad_failure_contract": 1,
            "success_identity_context_guard": 1,
        },
    )
    monkeypatch.setattr(
        m3025,
        "EXPECTED_FAILURE_COUNTS",
        {
            "collision_clearance_failure": 1,
            "offtrack_recovery_failure": 1,
            "success_context": 1,
        },
    )
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m3025"
    doc_path = tmp_path / "m3025.md"
    follow_up = tmp_path / "m3026.json"

    summary = m3025.run_target_source_readiness_feasibility_materialization_preflight(
        m3022_dir=paths["m3022_dir"],
        m3023_audit=paths["m3023_audit"],
        m3024_design=paths["m3024_design"],
        m3018_dir=paths["m3018_dir"],
        m3015_dir=paths["m3015_dir"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["target_source_readiness_row_count"] == 3
    assert summary["future_target_eligible_row_count"] == 2
    assert summary["success_identity_guard_row_count"] == 1
    assert summary["target_source_blocker_row_count"] == 2
    assert summary["target_source_feasibility_established_count"] == 0
    assert summary["numeric_target_tensor_materialized_count"] == 0
    assert summary["local_action_search_run_count"] == 0
    assert follow_up.exists()
    readiness_rows = _read_csv(output_dir / "target_source_readiness_rows.csv")
    assert readiness_rows[0]["target_source_status"] == "blocked_raw_actor_view_trace_missing"
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    assert all(row["status_pass"] == "True" for row in claim_rows)
    assert read_json(output_dir / "summary.json")["selected_next_action"] == m3025.NEXT_ID
