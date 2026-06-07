from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from autodrift.artifacts import read_json, write_csv_rows, write_json
import autodrift.engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_deployable_trace_capture_preflight as m2977


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m2973_dir = root / "m2973"
    m2960_dir = root / "m2960"
    m2973_dir.mkdir()
    m2960_dir.mkdir()
    write_json(
        m2973_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "raw_trace_persisted_count": 0,
            "trace_panel_ready_for_residual_fitting": False,
        },
    )
    trace_panel_rows = [
        {
            "trace_panel_row_id": "m2973-panel-0001",
            "training_admission_candidate_id": "candidate-1",
            "execution_candidate_id": "exec-1",
            "workload_id": "workload-1",
            "task_family": "T4",
            "outcome_family": "off_track",
            "objective_family": "offtrack_recovery_residual_objective",
            "trace_step_count": 3,
            "actor_observation_dim": 72,
            "actor_action_dim": 3,
        },
        {
            "trace_panel_row_id": "m2973-panel-0002",
            "training_admission_candidate_id": "candidate-2",
            "execution_candidate_id": "exec-2",
            "workload_id": "workload-2",
            "task_family": "T5",
            "outcome_family": "collision",
            "objective_family": "collision_clearance_residual_objective",
            "trace_step_count": 4,
            "actor_observation_dim": 72,
            "actor_action_dim": 3,
        },
    ]
    trace_guard_rows = [
        {
            "trace_guard_row_id": "m2973-success-0001",
            "source_guard_id": "success-1",
            "execution_candidate_id": "exec-3",
            "guard_family": "success_identity_guard",
            "guard_role": "zero_residual_identity_guard_not_positive_training_target",
            "trace_step_count": 2,
        },
        {
            "trace_guard_row_id": "m2973-stale-0001",
            "source_guard_id": "stale-1",
            "execution_candidate_id": "",
            "guard_family": "actor_head_delta_execution_admission_blocked_stale_fixed_surface",
            "guard_role": "blocked_stale_fixed_source_guardrail_not_executed",
            "trace_step_count": 0,
        },
    ]
    write_csv_rows(m2973_dir / "trace_panel_rows.csv", trace_panel_rows)
    write_csv_rows(m2973_dir / "trace_guard_rows.csv", trace_guard_rows)
    write_csv_rows(
        m2973_dir / "trace_availability_rows.csv",
        [{"trace_availability_row_id": "availability", "trace_metadata_present": True}],
    )
    write_csv_rows(m2973_dir / "gate_matrix.csv", [{"gate_id": "m2973-gate", "status_pass": True}])

    bounded_rows = [
        {
            "execution_candidate_id": "exec-1",
            "m2960_eval_seed": 296001,
            "workload_id": "workload-1",
            "task_family": "T4",
            "outcome_bucket": "off_track_noncollision_noncompletion",
            "parent_checkpoint_path": "checkpoint-1.pt",
            "parent_profile_config_path": "profile-1.json",
        },
        {
            "execution_candidate_id": "exec-2",
            "m2960_eval_seed": 296002,
            "workload_id": "workload-2",
            "task_family": "T5",
            "outcome_bucket": "collision_failure",
            "parent_checkpoint_path": "checkpoint-2.pt",
            "parent_profile_config_path": "profile-2.json",
        },
        {
            "execution_candidate_id": "exec-3",
            "m2960_eval_seed": 296003,
            "workload_id": "workload-3",
            "task_family": "T4",
            "outcome_bucket": "success_obstacle_pass",
            "parent_checkpoint_path": "checkpoint-3.pt",
            "parent_profile_config_path": "profile-3.json",
        },
    ]
    write_json(m2960_dir / "summary.json", {"status_pass": True, "gate_matrix_pass": True})
    write_csv_rows(m2960_dir / "bounded_execution_rows.csv", bounded_rows)
    write_csv_rows(m2960_dir / "actor_head_delta_contract_execution_rows.csv", [{"status_pass": True}])

    m2975 = root / "m2975.md"
    m2976 = root / "m2976.md"
    m2975.write_text("continue_to_m2976_deployable_trace_capture_design\n", encoding="utf-8")
    m2976.write_text("admit_m2977_deployable_trace_capture_preflight\n", encoding="utf-8")
    executable_specs = root / "executable_specs.json"
    executable_specs.write_text('{"executable_task_specs": []}\n', encoding="utf-8")
    executable_workload = root / "executable_workload.csv"
    write_csv_rows(executable_workload, [{"workload_id": "workload-1"}])
    return {
        "m2973_dir": m2973_dir,
        "m2960_dir": m2960_dir,
        "m2975": m2975,
        "m2976": m2976,
        "executable_specs": executable_specs,
        "executable_workload": executable_workload,
    }


def _fake_capture(plan: dict, execution_row: dict, context: dict) -> dict:
    del execution_row, context
    steps = max(1, int(plan["expected_trace_step_count"]))
    observation = np.full((steps, 72), float(steps), dtype=np.float32)
    action = np.zeros((steps, 3), dtype=np.float32)
    return {
        "observation_trace": observation,
        "action_trace": action,
        "next_observation_trace": observation + 0.5,
        "reward_trace": np.arange(steps, dtype=np.float32),
        "done_trace": np.asarray([False] * (steps - 1) + [True], dtype=np.bool_),
        "timeout_trace": np.asarray([False] * steps, dtype=np.bool_),
        "terminated": True,
        "truncated": False,
        "termination_reason": "",
        "completion_reason": "unit_test",
        "outcome_bucket": "unit_test_outcome",
        "checkpoint_loaded_read_only": True,
        "zero_residual_identity_mode": True,
        "residual_delta_abs_max": 0.0,
    }


def test_m2977_capture_plan_executes_candidates_and_success_guards_only(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m2977, "EXPECTED_TRAINING_CANDIDATE_COUNT", 2)
    monkeypatch.setattr(m2977, "EXPECTED_SUCCESS_IDENTITY_GUARD_COUNT", 1)
    monkeypatch.setattr(m2977, "EXPECTED_STALE_GUARDRAIL_COUNT", 1)
    monkeypatch.setattr(m2977, "EXPECTED_EXECUTED_RAW_TRACE_COUNT", 3)
    paths = _write_source_artifacts(tmp_path)
    source = m2977.load_source_artifacts(
        m2973_dir=paths["m2973_dir"],
        m2975_synthesis=paths["m2975"],
        m2976_design=paths["m2976"],
        m2960_dir=paths["m2960_dir"],
        executable_specs=paths["executable_specs"],
        executable_workload=paths["executable_workload"],
        follow_up_manifest=tmp_path / "m2978.json",
    )

    plan_rows = m2977.build_capture_plan_rows(source)

    assert len(plan_rows) == 4
    assert sum(row["execute_capture"] for row in plan_rows) == 3
    assert [row["row_role"] for row in plan_rows] == [
        "future_training_candidate",
        "future_training_candidate",
        "success_identity_guard",
        "stale_fixed_source_guardrail",
    ]
    assert plan_rows[-1]["stale_guardrail_protected"] is True
    assert plan_rows[-1]["execute_capture"] is False


def test_run_m2977_trace_capture_preflight_writes_raw_trace_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m2977, "EXPECTED_TRAINING_CANDIDATE_COUNT", 2)
    monkeypatch.setattr(m2977, "EXPECTED_SUCCESS_IDENTITY_GUARD_COUNT", 1)
    monkeypatch.setattr(m2977, "EXPECTED_STALE_GUARDRAIL_COUNT", 1)
    monkeypatch.setattr(m2977, "EXPECTED_EXECUTED_RAW_TRACE_COUNT", 3)
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m2977"
    doc_path = tmp_path / "m2977.md"
    follow_up = tmp_path / "m2978.json"

    summary = m2977.run_deployable_trace_capture_preflight(
        m2973_dir=paths["m2973_dir"],
        m2975_synthesis=paths["m2975"],
        m2976_design=paths["m2976"],
        m2960_dir=paths["m2960_dir"],
        executable_specs=paths["executable_specs"],
        executable_workload=paths["executable_workload"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
        capture_fn=_fake_capture,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["raw_trace_persisted_count"] == 3
    assert summary["future_training_candidate_raw_trace_count"] == 2
    assert summary["success_identity_raw_trace_count"] == 1
    assert summary["stale_guardrail_protected_count"] == 1
    assert summary["stale_guardrail_executed_count"] == 0
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["raw_trace_tensors_finite"] is True
    assert summary["residual_fitting_run"] is False
    assert summary["training_run"] is False
    assert summary["validation_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert read_json(follow_up)["id"] == m2977.NEXT_ID

    index_rows = _read_csv(output_dir / "raw_trace_index_rows.csv")
    guard_rows = _read_csv(output_dir / "raw_trace_guard_rows.csv")
    availability_rows = _read_csv(output_dir / "raw_trace_availability_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")
    assert len(index_rows) == 3
    assert {row["actor_observation_dim"] for row in index_rows} == {"72"}
    assert {row["actor_action_dim"] for row in index_rows} == {"3"}
    assert {row["raw_trace_persisted"] for row in index_rows} == {"True"}
    assert len(guard_rows) == 2
    assert any(row["stale_guardrail_protected"] == "True" and row["raw_trace_persisted"] == "False" for row in guard_rows)
    assert len(availability_rows) == 4
    assert any(row["availability_status"] == "protected_stale_guardrail_not_executed" for row in availability_rows)
    assert {row["status_pass"] for row in gate_rows} == {"True"}

    first_trace = np.load(index_rows[0]["raw_trace_path"])
    assert first_trace["observation_trace"].shape == (3, 72)
    assert first_trace["action_trace"].shape == (3, 3)
    assert first_trace["next_observation_trace"].shape == (3, 72)
