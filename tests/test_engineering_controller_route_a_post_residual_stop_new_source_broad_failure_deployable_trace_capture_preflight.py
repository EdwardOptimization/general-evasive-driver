from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from autodrift.artifacts import read_json, write_csv_rows, write_json
import autodrift.engineering_controller_route_a_post_residual_stop_new_source_broad_failure_deployable_trace_capture_preflight as m3027


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m3025_dir = root / "m3025"
    m3015_dir = root / "m3015"
    m3012_dir = root / "m3012"
    m3025_dir.mkdir()
    m3015_dir.mkdir()
    m3012_dir.mkdir()

    write_json(
        m3025_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "target_source_readiness_row_count": 3,
            "future_target_eligible_row_count": 2,
            "success_identity_guard_row_count": 1,
            "actor_contract_shape_72_action_3": True,
        },
    )
    readiness_rows = [
        {
            "target_source_readiness_row_id": "m3025-target-source-readiness-0001",
            "row_assignment_id": "assign-1",
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
            "objective_family": "offtrack_recovery_broad_failure_contract",
            "failure_family": "offtrack_recovery_failure",
            "target_source_status": "blocked_raw_actor_view_trace_missing",
            "future_target_materialization_allowed": True,
            "actor_observation_dim": 72,
            "actor_action_dim": 3,
        },
        {
            "target_source_readiness_row_id": "m3025-target-source-readiness-0002",
            "row_assignment_id": "assign-2",
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
            "objective_family": "collision_clearance_guard_contract",
            "failure_family": "collision_clearance_failure",
            "target_source_status": "blocked_raw_actor_view_trace_missing",
            "future_target_materialization_allowed": True,
            "actor_observation_dim": 72,
            "actor_action_dim": 3,
        },
        {
            "target_source_readiness_row_id": "m3025-target-source-readiness-0003",
            "row_assignment_id": "assign-3",
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
            "objective_family": "success_identity_context_guard",
            "failure_family": "success_context",
            "target_source_status": "guard_only_success_identity",
            "future_target_materialization_allowed": False,
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

    write_json(m3015_dir / "summary.json", {"status_pass": True, "gate_matrix_pass": True})
    episode_rows = [
        {
            "execution_workload_id": "exec-1",
            "executable_workload_id": "workload-1",
            "workload_id": "workload-1",
            "steps": "3",
            "m3015_eval_seed": "301500",
            "profile_config_path": "profile-1.json",
            "checkpoint_path": "checkpoint-1.pt",
        },
        {
            "execution_workload_id": "exec-2",
            "executable_workload_id": "workload-2",
            "workload_id": "workload-2",
            "steps": "4",
            "m3015_eval_seed": "301501",
            "profile_config_path": "profile-2.json",
            "checkpoint_path": "checkpoint-2.pt",
        },
        {
            "execution_workload_id": "exec-3",
            "executable_workload_id": "workload-3",
            "workload_id": "workload-3",
            "steps": "2",
            "m3015_eval_seed": "301502",
            "profile_config_path": "profile-3.json",
            "checkpoint_path": "checkpoint-3.pt",
        },
    ]
    write_csv_rows(m3015_dir / "episode_rows.csv", episode_rows)
    execution_rows = [
        {
            "execution_workload_id": "exec-1",
            "executable_workload_id": "workload-1",
            "workload_id": "workload-1",
            "task_source_id": "src-1",
            "profile_name": "candidate",
            "profile_binding_name": "candidate",
            "binding_role": "candidate",
            "executable_source_spec_id": "spec-1",
            "config_path": "profile-1.json",
            "checkpoint_path": "checkpoint-1.pt",
        },
        {
            "execution_workload_id": "exec-2",
            "executable_workload_id": "workload-2",
            "workload_id": "workload-2",
            "task_source_id": "src-2",
            "profile_name": "candidate",
            "profile_binding_name": "candidate",
            "binding_role": "candidate",
            "executable_source_spec_id": "spec-2",
            "config_path": "profile-2.json",
            "checkpoint_path": "checkpoint-2.pt",
        },
        {
            "execution_workload_id": "exec-3",
            "executable_workload_id": "workload-3",
            "workload_id": "workload-3",
            "task_source_id": "src-3",
            "profile_name": "parent",
            "profile_binding_name": "parent",
            "binding_role": "parent",
            "executable_source_spec_id": "spec-3",
            "config_path": "profile-3.json",
            "checkpoint_path": "checkpoint-3.pt",
        },
    ]
    write_csv_rows(m3015_dir / "execution_workload_rows.csv", execution_rows)
    write_csv_rows(m3015_dir / "execution_guard_rows.csv", [{"status_pass": True}])

    write_json(
        m3012_dir / "summary.json",
        {"status_pass": True, "gate_matrix_pass": True},
    )
    write_json(
        m3012_dir / "executable_source_specs.json",
        {
            "executable_source_specs": [
                {"task_source_id": "src-1", "executable_source_spec_id": "spec-1"},
                {"task_source_id": "src-2", "executable_source_spec_id": "spec-2"},
                {"task_source_id": "src-3", "executable_source_spec_id": "spec-3"},
            ]
        },
    )
    write_csv_rows(
        m3012_dir / "executable_workload_rows.csv",
        [
            {"executable_workload_id": "workload-1", "workload_id": "workload-1"},
            {"executable_workload_id": "workload-2", "workload_id": "workload-2"},
            {"executable_workload_id": "workload-3", "workload_id": "workload-3"},
        ],
    )

    m3026_audit = root / "m3026.md"
    m3026_audit.write_text(m3027.M3026_DECISION, encoding="utf-8")
    return {"m3025_dir": m3025_dir, "m3015_dir": m3015_dir, "m3012_dir": m3012_dir, "m3026_audit": m3026_audit}


def _fake_capture(plan: dict, execution_row: dict, context: dict) -> dict:
    del execution_row, context
    steps = max(1, int(plan["expected_trace_step_count"]))
    observation = np.full((steps, 72), float(steps), dtype=np.float32)
    action = np.zeros((steps, 3), dtype=np.float32)
    return {
        "observation_trace": observation,
        "action_trace": action,
        "next_observation_trace": observation + 0.25,
        "reward_trace": np.arange(steps, dtype=np.float32),
        "done_trace": np.asarray([False] * (steps - 1) + [True], dtype=np.bool_),
        "timeout_trace": np.asarray([False] * steps, dtype=np.bool_),
        "terminated": True,
        "truncated": False,
        "termination_reason": "",
        "completion_reason": "unit_test",
        "outcome_bucket": "unit_test_outcome",
        "checkpoint_loaded_read_only": True,
        "direct_profile_policy_mode": True,
    }


def test_m3027_capture_plan_preserves_future_targets_and_success_guards(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m3027, "EXPECTED_READINESS_ROW_COUNT", 3)
    monkeypatch.setattr(m3027, "EXPECTED_FUTURE_TARGET_ROW_COUNT", 2)
    monkeypatch.setattr(m3027, "EXPECTED_SUCCESS_GUARD_ROW_COUNT", 1)
    monkeypatch.setattr(m3027, "EXPECTED_RAW_TRACE_ROW_COUNT", 3)
    paths = _write_source_artifacts(tmp_path)
    source = m3027.load_source_artifacts(
        m3025_dir=paths["m3025_dir"],
        m3026_audit=paths["m3026_audit"],
        m3015_dir=paths["m3015_dir"],
        m3012_dir=paths["m3012_dir"],
        follow_up_manifest=tmp_path / "m3028.json",
    )

    plan_rows = m3027.build_capture_plan_rows(source)

    assert len(plan_rows) == 3
    assert [row["row_role"] for row in plan_rows] == [
        "future_target_candidate",
        "future_target_candidate",
        "success_identity_guard",
    ]
    assert sum(row["execute_capture"] for row in plan_rows) == 3
    assert plan_rows[-1]["success_identity_guard_row_id"] == "m3025-success-identity-guard-0001"
    assert plan_rows[-1]["positive_target_candidate"] is False
    assert {row["actor_observation_dim"] for row in plan_rows} == {72}
    assert {row["actor_action_dim"] for row in plan_rows} == {3}


def test_run_m3027_trace_capture_preflight_writes_raw_trace_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m3027, "EXPECTED_READINESS_ROW_COUNT", 3)
    monkeypatch.setattr(m3027, "EXPECTED_FUTURE_TARGET_ROW_COUNT", 2)
    monkeypatch.setattr(m3027, "EXPECTED_SUCCESS_GUARD_ROW_COUNT", 1)
    monkeypatch.setattr(m3027, "EXPECTED_RAW_TRACE_ROW_COUNT", 3)
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m3027"
    doc_path = tmp_path / "m3027.md"
    follow_up = tmp_path / "m3028.json"

    summary = m3027.run_deployable_trace_capture_preflight(
        m3025_dir=paths["m3025_dir"],
        m3026_audit=paths["m3026_audit"],
        m3015_dir=paths["m3015_dir"],
        m3012_dir=paths["m3012_dir"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
        capture_fn=_fake_capture,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["capture_plan_row_count"] == 3
    assert summary["future_target_raw_trace_count"] == 2
    assert summary["success_identity_raw_trace_count"] == 1
    assert summary["raw_trace_persisted_count"] == 3
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["raw_trace_tensors_finite"] is True
    assert summary["target_source_feasibility_claim_made"] is False
    assert summary["local_action_search_run"] is False
    assert summary["numeric_target_tensor_materialized_count"] == 0
    assert summary["training_run"] is False
    assert summary["validation_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert read_json(follow_up)["id"] == m3027.NEXT_ID

    index_rows = _read_csv(output_dir / "raw_trace_index_rows.csv")
    guard_rows = _read_csv(output_dir / "raw_trace_guard_rows.csv")
    availability_rows = _read_csv(output_dir / "raw_trace_availability_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")
    assert len(index_rows) == 3
    assert {row["actor_observation_dim"] for row in index_rows} == {"72"}
    assert {row["actor_action_dim"] for row in index_rows} == {"3"}
    assert {row["raw_trace_persisted"] for row in index_rows} == {"True"}
    assert len(guard_rows) == 3
    assert any(row["success_identity_guard"] == "True" and row["positive_target_candidate"] == "False" for row in guard_rows)
    assert len(availability_rows) == 3
    assert {row["availability_status"] for row in availability_rows} == {"raw_trace_persisted_pending_m3028_audit"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}

    first_trace = np.load(index_rows[0]["raw_trace_path"])
    assert first_trace["observation_trace"].shape == (3, 72)
    assert first_trace["action_trace"].shape == (3, 3)
    assert first_trace["next_observation_trace"].shape == (3, 72)
