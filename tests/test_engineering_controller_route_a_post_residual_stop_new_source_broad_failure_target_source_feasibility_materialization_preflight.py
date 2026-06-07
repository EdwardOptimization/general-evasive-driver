from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
import autodrift.engineering_controller_route_a_post_residual_stop_new_source_broad_failure_target_source_feasibility_materialization_preflight as m3029


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m3025_dir = root / "m3025"
    m3027_dir = root / "m3027"
    m3025_dir.mkdir()
    m3027_dir.mkdir()
    trace_dir = m3027_dir / "raw_traces"
    trace_dir.mkdir()

    write_json(
        m3025_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "target_source_readiness_row_count": 3,
            "future_target_eligible_row_count": 2,
            "success_identity_guard_row_count": 1,
            "target_source_feasibility_established_count": 0,
            "actor_contract_shape_72_action_3": True,
        },
    )
    readiness_rows = [
        {
            "target_source_readiness_row_id": "m3025-target-source-readiness-0001",
            "row_assignment_id": "assign-1",
            "source_episode_row_index": "1",
            "task_source_id": "src-1",
            "profile_name": "candidate",
            "binding_role": "candidate",
            "objective_family": "offtrack_recovery_broad_failure_contract",
            "failure_family": "offtrack_recovery_failure",
            "target_role": "future_target_candidate",
            "future_target_materialization_allowed": True,
            "raw_actor_view_trace_required": True,
            "raw_actor_view_trace_available": False,
            "actor_observation_dim": 72,
            "actor_action_dim": 3,
        },
        {
            "target_source_readiness_row_id": "m3025-target-source-readiness-0002",
            "row_assignment_id": "assign-2",
            "source_episode_row_index": "2",
            "task_source_id": "src-2",
            "profile_name": "candidate",
            "binding_role": "candidate",
            "objective_family": "collision_clearance_guard_contract",
            "failure_family": "collision_clearance_failure",
            "target_role": "future_target_candidate",
            "future_target_materialization_allowed": True,
            "raw_actor_view_trace_required": True,
            "raw_actor_view_trace_available": False,
            "actor_observation_dim": 72,
            "actor_action_dim": 3,
        },
        {
            "target_source_readiness_row_id": "m3025-target-source-readiness-0003",
            "row_assignment_id": "assign-3",
            "source_episode_row_index": "3",
            "task_source_id": "src-3",
            "profile_name": "parent",
            "binding_role": "parent",
            "objective_family": "success_identity_context_guard",
            "failure_family": "success_context",
            "target_role": "success_identity_zero_target_guard",
            "future_target_materialization_allowed": False,
            "raw_actor_view_trace_required": False,
            "raw_actor_view_trace_available": False,
            "actor_observation_dim": 72,
            "actor_action_dim": 3,
        },
    ]
    write_csv_rows(m3025_dir / "target_source_readiness_rows.csv", readiness_rows)
    write_csv_rows(
        m3025_dir / "target_source_blocker_rows.csv",
        [
            {"target_source_blocker_row_id": "blocker-1", "target_source_readiness_row_id": "m3025-target-source-readiness-0001"},
            {"target_source_blocker_row_id": "blocker-2", "target_source_readiness_row_id": "m3025-target-source-readiness-0002"},
        ],
    )
    write_csv_rows(
        m3025_dir / "success_identity_guard_rows.csv",
        [
            {
                "success_identity_guard_row_id": "m3025-success-identity-guard-0001",
                "target_source_readiness_row_id": "m3025-target-source-readiness-0003",
                "positive_target_candidate": False,
            }
        ],
    )
    write_csv_rows(m3025_dir / "actor_contract_guard_rows.csv", [{"status_pass": True}])
    write_csv_rows(m3025_dir / "gate_matrix.csv", [{"status_pass": True}])

    write_json(
        m3027_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "raw_trace_index_row_count": 3,
            "future_target_raw_trace_count": 2,
            "success_identity_raw_trace_count": 1,
            "raw_trace_tensors_finite": True,
            "actor_contract_shape_72_action_3": True,
        },
    )
    raw_rows = []
    availability_rows = []
    guard_rows = []
    roles = ["future_target_candidate", "future_target_candidate", "success_identity_guard"]
    for index, readiness in enumerate(readiness_rows, start=1):
        trace_path = trace_dir / f"trace-{index}.npz"
        trace_path.write_bytes(b"npz-placeholder")
        role = roles[index - 1]
        raw_rows.append(
            {
                "raw_trace_index_row_id": f"raw-{index}",
                "target_source_readiness_row_id": readiness["target_source_readiness_row_id"],
                "row_assignment_id": readiness["row_assignment_id"],
                "source_episode_row_index": readiness["source_episode_row_index"],
                "execution_workload_id": f"exec-{index}",
                "task_source_id": readiness["task_source_id"],
                "profile_name": readiness["profile_name"],
                "binding_role": readiness["binding_role"],
                "row_role": role,
                "objective_family": readiness["objective_family"],
                "failure_family": readiness["failure_family"],
                "raw_trace_path": str(trace_path),
                "raw_trace_persisted": True,
                "trace_step_count": index + 2,
                "actor_observation_dim": 72,
                "actor_action_dim": 3,
                "tensors_finite": True,
                "target_source_feasibility_claim_made": False,
                "local_action_search_run": False,
                "numeric_target_tensor_materialized": False,
            }
        )
        availability_rows.append(
            {
                "raw_trace_availability_row_id": f"availability-{index}",
                "target_source_readiness_row_id": readiness["target_source_readiness_row_id"],
                "raw_trace_persisted": True,
                "trace_file_exists": True,
                "trace_step_count": index + 2,
            }
        )
        guard_rows.append(
            {
                "raw_trace_guard_row_id": f"guard-{index}",
                "target_source_readiness_row_id": readiness["target_source_readiness_row_id"],
                "positive_target_candidate": False,
                "local_action_search_run": False,
                "numeric_target_tensor_materialized": False,
                "training_run": False,
                "validation_run": False,
            }
        )
    write_csv_rows(m3027_dir / "raw_trace_index_rows.csv", raw_rows)
    write_csv_rows(m3027_dir / "raw_trace_availability_rows.csv", availability_rows)
    write_csv_rows(m3027_dir / "raw_trace_guard_rows.csv", guard_rows)
    write_csv_rows(m3027_dir / "actor_contract_guard_rows.csv", [{"status_pass": True}])
    write_csv_rows(m3027_dir / "gate_matrix.csv", [{"status_pass": True}])

    m3028_audit = root / "m3028.md"
    m3028_audit.write_text(m3029.M3028_DECISION, encoding="utf-8")
    return {"m3025_dir": m3025_dir, "m3027_dir": m3027_dir, "m3028_audit": m3028_audit}


def test_m3029_plan_materializes_feasible_candidates_and_success_guards(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m3029, "EXPECTED_DENOMINATOR_ROWS", 3)
    monkeypatch.setattr(m3029, "EXPECTED_FUTURE_TARGET_ROWS", 2)
    monkeypatch.setattr(m3029, "EXPECTED_SUCCESS_GUARD_ROWS", 1)
    paths = _write_source_artifacts(tmp_path)
    source = m3029.load_source_artifacts(
        m3027_dir=paths["m3027_dir"],
        m3028_audit=paths["m3028_audit"],
        m3025_dir=paths["m3025_dir"],
        follow_up_manifest=tmp_path / "m3030.json",
    )

    plan_rows = m3029.build_target_source_plan_rows(source)
    candidate_rows = m3029.build_target_source_candidate_rows(plan_rows)
    success_rows = m3029.build_success_identity_guard_rows(plan_rows)

    assert len(plan_rows) == 3
    assert len(candidate_rows) == 2
    assert len(success_rows) == 1
    assert sum(row["target_source_feasibility_established"] for row in plan_rows) == 2
    assert all(row["future_target_candidate"] for row in candidate_rows)
    assert not any(row["numeric_target_tensor_materialized"] for row in plan_rows)
    assert not any(row["local_action_search_run"] for row in plan_rows)
    assert success_rows[0]["success_identity_zero_target_guard"] is True
    assert success_rows[0]["positive_target_candidate"] is False
    assert success_rows[0]["target_source_feasibility_established"] is False


def test_run_m3029_writes_claim_safe_feasibility_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m3029, "EXPECTED_DENOMINATOR_ROWS", 3)
    monkeypatch.setattr(m3029, "EXPECTED_FUTURE_TARGET_ROWS", 2)
    monkeypatch.setattr(m3029, "EXPECTED_SUCCESS_GUARD_ROWS", 1)
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m3029"
    doc_path = tmp_path / "m3029.md"
    follow_up = tmp_path / "m3030.json"

    summary = m3029.run_target_source_feasibility_materialization_preflight(
        m3027_dir=paths["m3027_dir"],
        m3028_audit=paths["m3028_audit"],
        m3025_dir=paths["m3025_dir"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["target_source_plan_row_count"] == 3
    assert summary["target_source_candidate_row_count"] == 2
    assert summary["success_identity_guard_row_count"] == 1
    assert summary["target_source_feasibility_established_count"] == 2
    assert summary["numeric_target_tensor_materialized_count"] == 0
    assert summary["local_action_search_run_count"] == 0
    assert summary["environment_reset_run"] is False
    assert summary["training_run"] is False
    assert summary["validation_run"] is False
    assert read_json(follow_up)["id"] == m3029.NEXT_ID

    candidate_rows = _read_csv(output_dir / "target_source_candidate_rows.csv")
    success_rows = _read_csv(output_dir / "success_identity_guard_rows.csv")
    availability_rows = _read_csv(output_dir / "target_source_availability_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")
    assert len(candidate_rows) == 2
    assert {row["target_source_feasibility_established"] for row in candidate_rows} == {"True"}
    assert success_rows[0]["positive_target_candidate"] == "False"
    assert success_rows[0]["target_source_feasibility_established"] == "False"
    assert len(availability_rows) == 3
    assert "target_source_feasible_pending_m3030_audit" in {row["availability_status"] for row in availability_rows}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert read_json(output_dir / "summary.json")["selected_next_action"] == m3029.NEXT_ID
