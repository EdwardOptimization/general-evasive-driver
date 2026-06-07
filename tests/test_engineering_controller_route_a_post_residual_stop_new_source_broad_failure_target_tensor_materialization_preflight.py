from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from autodrift.artifacts import read_json, write_csv_rows, write_json
import autodrift.engineering_controller_route_a_post_residual_stop_new_source_broad_failure_target_tensor_materialization_preflight as m3032


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_trace(path: Path, *, steps: int, action_bias: float = 0.0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    observation = np.zeros((steps, 72), dtype=np.float32)
    observation[:, 1] = np.linspace(-1.0, 1.0, steps, dtype=np.float32)
    action = np.zeros((steps, 3), dtype=np.float32)
    action[:, 0] = action_bias
    next_observation = observation.copy()
    reward = np.zeros((steps,), dtype=np.float32)
    done = np.zeros((steps,), dtype=bool)
    timeout = np.zeros((steps,), dtype=bool)
    done[-1] = True
    np.savez_compressed(
        path,
        observation_trace=observation,
        action_trace=action,
        next_observation_trace=next_observation,
        reward_trace=reward,
        done_trace=done,
        timeout_trace=timeout,
    )


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m3029_dir = root / "m3029"
    m3027_dir = root / "m3027"
    trace_dir = m3027_dir / "raw_traces"
    m3029_dir.mkdir()
    trace_dir.mkdir(parents=True)

    candidate_rows = []
    plan_rows = []
    raw_rows = []
    objectives = [
        ("offtrack_recovery_broad_failure_contract", "offtrack_recovery_failure"),
        ("collision_clearance_guard_contract", "collision_clearance_failure"),
    ]
    for index, (objective, failure) in enumerate(objectives, start=1):
        trace_path = trace_dir / f"candidate-{index}.npz"
        _write_trace(trace_path, steps=index + 4, action_bias=0.1 * index)
        candidate_rows.append(
            {
                "target_source_candidate_row_id": f"candidate-{index}",
                "target_source_plan_row_id": f"plan-{index}",
                "target_source_readiness_row_id": f"readiness-{index}",
                "raw_trace_index_row_id": f"raw-{index}",
                "row_assignment_id": f"assign-{index}",
                "task_source_id": f"src-{index}",
                "profile_name": "candidate",
                "binding_role": "candidate",
                "objective_family": objective,
                "failure_family": failure,
                "raw_trace_path": str(trace_path),
                "trace_step_count": index + 4,
                "actor_observation_dim": 72,
                "actor_action_dim": 3,
                "target_source_feasibility_established": True,
                "future_target_candidate": True,
                "local_action_search_run": False,
                "numeric_target_tensor_materialized": False,
                "target_labels_actor_visible": False,
                "target_provenance_actor_visible": False,
            }
        )
        plan_rows.append(
            {
                "target_source_plan_row_id": f"plan-{index}",
                "target_source_readiness_row_id": f"readiness-{index}",
                "raw_trace_index_row_id": f"raw-{index}",
                "row_assignment_id": f"assign-{index}",
                "row_role": "future_target_candidate",
            }
        )
        raw_rows.append(
            {
                "raw_trace_index_row_id": f"raw-{index}",
                "target_source_readiness_row_id": f"readiness-{index}",
                "row_role": "future_target_candidate",
                "raw_trace_path": str(trace_path),
                "trace_step_count": index + 4,
            }
        )

    success_trace = trace_dir / "success.npz"
    _write_trace(success_trace, steps=4)
    success_rows = [
        {
            "success_identity_guard_row_id": "success-1",
            "target_source_plan_row_id": "plan-3",
            "target_source_readiness_row_id": "readiness-3",
            "raw_trace_index_row_id": "raw-3",
            "row_assignment_id": "assign-3",
            "task_source_id": "src-3",
            "profile_name": "parent",
            "binding_role": "parent",
            "raw_trace_path": str(success_trace),
            "trace_step_count": 4,
            "positive_target_candidate": False,
            "target_source_feasibility_established": False,
        }
    ]
    plan_rows.append(
        {
            "target_source_plan_row_id": "plan-3",
            "target_source_readiness_row_id": "readiness-3",
            "raw_trace_index_row_id": "raw-3",
            "row_assignment_id": "assign-3",
            "row_role": "success_identity_guard",
        }
    )
    raw_rows.append(
        {
            "raw_trace_index_row_id": "raw-3",
            "target_source_readiness_row_id": "readiness-3",
            "row_role": "success_identity_guard",
            "raw_trace_path": str(success_trace),
            "trace_step_count": 4,
        }
    )

    write_json(
        m3029_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "target_source_plan_row_count": 3,
            "target_source_candidate_row_count": 2,
            "success_identity_guard_row_count": 1,
            "target_source_feasibility_established_count": 2,
            "numeric_target_tensor_materialized_count": 0,
            "local_action_search_run_count": 0,
            "actor_contract_shape_72_action_3": True,
        },
    )
    write_csv_rows(m3029_dir / "target_source_plan_rows.csv", plan_rows)
    write_csv_rows(m3029_dir / "target_source_candidate_rows.csv", candidate_rows)
    write_csv_rows(m3029_dir / "success_identity_guard_rows.csv", success_rows)
    write_csv_rows(m3029_dir / "target_source_availability_rows.csv", [{"status_pass": True}])
    write_csv_rows(m3029_dir / "actor_contract_guard_rows.csv", [{"status_pass": True}])
    write_csv_rows(m3029_dir / "claim_boundary_rows.csv", [{"status_pass": True}])
    write_csv_rows(m3029_dir / "gate_matrix.csv", [{"status_pass": True}])
    write_csv_rows(m3027_dir / "raw_trace_index_rows.csv", raw_rows)

    m3030_audit = root / "m3030.md"
    m3030_audit.write_text(m3032.M3030_DECISION, encoding="utf-8")
    m3031_synthesis = root / "m3031.md"
    m3031_synthesis.write_text(m3032.M3031_DECISION, encoding="utf-8")
    return {"m3029_dir": m3029_dir, "m3027_dir": m3027_dir, "m3030_audit": m3030_audit, "m3031_synthesis": m3031_synthesis}


def test_materialize_candidate_target_writes_bounded_actor_invisible_tensor(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.npz"
    _write_trace(trace_path, steps=5, action_bias=0.2)
    row = {
        "target_source_candidate_row_id": "candidate-1",
        "target_source_plan_row_id": "plan-1",
        "target_source_readiness_row_id": "readiness-1",
        "raw_trace_index_row_id": "raw-1",
        "row_assignment_id": "assign-1",
        "task_source_id": "src-1",
        "profile_name": "candidate",
        "binding_role": "candidate",
        "objective_family": "collision_clearance_guard_contract",
        "failure_family": "collision_clearance_failure",
        "raw_trace_path": str(trace_path),
    }

    target = m3032.materialize_candidate_target(candidate_row=row, target_dir=tmp_path / "targets", index=1)

    tensor = np.load(target["target_tensor_path"])
    assert tensor["target_action_delta"].shape == (5, 3)
    assert float(np.max(np.abs(tensor["target_action_delta"]))) <= m3032.TARGET_DELTA_ABS_LIMIT
    assert tensor["target_valid_mask"].sum() == 4
    assert target["numeric_target_tensor_materialized"] is True
    assert target["target_labels_actor_visible"] is False
    assert target["target_provenance_actor_visible"] is False
    assert target["local_action_search_run"] is False
    assert target["training_run"] is False
    assert target["validation_run"] is False


def test_run_m3032_writes_claim_safe_target_tensor_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m3032, "EXPECTED_TARGET_SOURCE_PLAN_ROWS", 3)
    monkeypatch.setattr(m3032, "EXPECTED_TARGET_CANDIDATE_ROWS", 2)
    monkeypatch.setattr(m3032, "EXPECTED_SUCCESS_IDENTITY_GUARD_ROWS", 1)
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m3032"
    follow_up = tmp_path / "m3033.json"

    summary = m3032.run_target_tensor_materialization_preflight(
        m3029_dir=paths["m3029_dir"],
        m3030_audit=paths["m3030_audit"],
        m3031_synthesis=paths["m3031_synthesis"],
        m3027_dir=paths["m3027_dir"],
        output_dir=output_dir,
        doc_path=tmp_path / "m3032.md",
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["target_tensor_row_count"] == 2
    assert summary["numeric_target_tensor_materialized_count"] == 2
    assert summary["success_identity_zero_target_guard_row_count"] == 1
    assert summary["target_tensor_file_count"] == 3
    assert summary["local_action_search_run"] is False
    assert summary["environment_step_run"] is False
    assert summary["training_run"] is False
    assert summary["validation_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert read_json(follow_up)["id"] == m3032.NEXT_ID

    target_rows = _read_csv(output_dir / "target_tensor_rows.csv")
    success_rows = _read_csv(output_dir / "success_identity_zero_target_guard_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")
    assert len(target_rows) == 2
    assert {row["numeric_target_tensor_materialized"] for row in target_rows} == {"True"}
    assert {row["target_labels_actor_visible"] for row in target_rows} == {"False"}
    assert {row["local_action_search_run"] for row in target_rows} == {"False"}
    zero_tensor = np.load(success_rows[0]["target_tensor_path"])
    assert zero_tensor["target_valid_mask"].sum() == 0
    assert float(np.max(np.abs(zero_tensor["target_action_delta"]))) == 0.0
    assert {row["status_pass"] for row in gate_rows} == {"True"}
