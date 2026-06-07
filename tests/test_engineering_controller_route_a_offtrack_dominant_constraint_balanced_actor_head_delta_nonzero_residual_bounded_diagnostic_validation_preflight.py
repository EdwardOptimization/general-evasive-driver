from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from autodrift.artifacts import read_json, write_csv_rows, write_json
import autodrift.engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_bounded_diagnostic_validation_preflight as m3000


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _metric_row(*, execution_candidate_id: str, workload_id: str, seed: int, success: bool) -> dict[str, object]:
    return {
        "seed": seed,
        "policy": "checkpoint",
        "steps": 12,
        "terminated": True,
        "truncated": False,
        "collision": False,
        "obstacle_completed": success,
        "min_obstacle_clearance": 2.5,
        "obstacle_collision_radius": 1.0,
        "min_clearance_margin": 1.5,
        "termination_reason": "" if success else "off_track",
        "completion_reason": "obstacle_pass" if success else "off_track",
        "outcome_bucket": "success_obstacle_pass" if success else "off_track_noncollision_noncompletion",
        "return": 3.0,
        "mean_reward": 0.25,
        "lateral_rmse": 0.1,
        "beta_abs_error_mean": 0.05,
        "high_sideslip_fraction": 0.0,
        "speed_mean": 8.0,
        "action_rate_mean": 0.2,
        "max_off_track_overshoot": 0.0,
        "time_to_first_off_track_s": "",
        "off_track_severity_proxy": 0.0,
        "recoverability_window_success": success,
        "recoverability_window_success_available": True,
        "success": success,
        "workload_id": workload_id,
        "task_source_id": f"task-{workload_id}",
        "profile_name": "L3_online_gru",
        "task_family": "T4",
        "source_edge": "unit",
        "window_tag": "unit",
        "strata": "unit",
        "executable_source_family": "unit",
        "env_template_family": "unit",
        "profile_config_path": "profile.json",
        "checkpoint_path": "checkpoint.pt",
        "parent_profile_config_path": "profile.json",
        "parent_checkpoint_path": "checkpoint.pt",
        "profile_env_history_length": 4,
        "eval_seed": seed,
        "m2960_eval_seed": seed,
        "execution_candidate_id": execution_candidate_id,
    }


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m2996_dir = root / "m2996"
    m2977_dir = root / "m2977"
    m2960_dir = root / "m2960"
    m2996_dir.mkdir()
    m2977_dir.mkdir()
    m2960_dir.mkdir()
    raw_dir = root / "raw"
    target_dir = root / "target"
    raw_dir.mkdir()
    target_dir.mkdir()
    artifact = root / "candidate_residual_head_artifact.npz"
    np.savez(
        artifact,
        linear_weight=np.zeros((72, 3), dtype=np.float32),
        linear_bias=np.zeros((3,), dtype=np.float32),
        residual_limit=np.asarray([0.08], dtype=np.float32),
        success_guard_required_abs_max=np.asarray([0.001], dtype=np.float32),
        observation_dim=np.asarray([72], dtype=np.int64),
        action_dim=np.asarray([3], dtype=np.int64),
    )
    raw_paths = []
    target_paths = []
    for index in range(1, 4):
        raw = raw_dir / f"raw-{index}.npz"
        target = target_dir / f"target-{index}.npz"
        np.savez(raw, observation_trace=np.zeros((2, 72), dtype=np.float32))
        np.savez(target, target_action_delta=np.zeros((2, 3), dtype=np.float32))
        raw_paths.append(str(raw))
        target_paths.append(str(target))

    write_json(
        m2996_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "required_artifacts_present": True,
            "candidate_residual_head_artifact": str(artifact),
        },
    )
    write_csv_rows(
        m2996_dir / "validation_contract_rows.csv",
        [
            {
                "validation_contract_id": "contract-1",
                "fitting_dataset_row_id": "fit-1",
                "target_tensor_row_id": "target-1",
                "raw_trace_path": raw_paths[0],
                "target_tensor_path": target_paths[0],
                "status_pass": True,
            },
            {
                "validation_contract_id": "contract-2",
                "fitting_dataset_row_id": "fit-2",
                "target_tensor_row_id": "target-2",
                "raw_trace_path": raw_paths[1],
                "target_tensor_path": target_paths[1],
                "status_pass": True,
            },
        ],
    )
    write_csv_rows(
        m2996_dir / "success_behavior_retention_guard_rows.csv",
        [
            {
                "success_retention_guard_id": "success-1",
                "success_guard_loss_id": "loss-1",
                "raw_trace_path": raw_paths[2],
                "target_tensor_path": target_paths[2],
                "status_pass": True,
            }
        ],
    )
    write_csv_rows(
        m2996_dir / "stale_exclusion_guard_rows.csv",
        [
            {
                "stale_exclusion_guard_id": "stale-1",
                "stale_exclusion_audit_id": "audit-1",
                "stale_guardrail_exclusion_binding_id": "binding-1",
                "stale_guardrail_exclusion_row_id": "stale-row-1",
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "self_id_denominator_allowed": False,
                "stale_guardrail_excluded": True,
                "status_pass": True,
            }
        ],
    )
    write_csv_rows(
        m2996_dir / "actor_input_exclusion_rows.csv",
        [
            {"forbidden_metadata_key": f"forbidden-{index}", "actor_visible": False, "status_pass": True}
            for index in range(14)
        ],
    )
    write_csv_rows(
        m2996_dir / "checkpoint_side_effect_guard_rows.csv",
        [{"side_effect": "checkpoint_save", "scheduled_or_run": False, "status_pass": True}],
    )
    write_csv_rows(
        m2996_dir / "residual_head_wrapper_contract_rows.csv",
        [{"artifact_path": str(artifact), "status_pass": True}],
    )
    write_csv_rows(m2996_dir / "parent_comparison_plan_rows.csv", [{"status_pass": True}])
    write_csv_rows(m2996_dir / "gate_matrix.csv", [{"gate_id": "gate", "status_pass": True}])

    raw_index_rows = []
    capture_rows = []
    parent_rows = []
    for index in range(1, 4):
        execution_candidate_id = f"exec-{index}"
        workload_id = f"workload-{index}"
        seed = 300000 + index
        capture_plan_id = f"capture-{index}"
        raw_index_rows.append(
            {
                "raw_trace_index_row_id": f"raw-index-{index}",
                "capture_plan_row_id": capture_plan_id,
                "execution_candidate_id": execution_candidate_id,
                "raw_trace_path": raw_paths[index - 1],
                "expected_trace_step_count": 2,
            }
        )
        capture_rows.append(
            {
                "capture_plan_row_id": capture_plan_id,
                "execution_candidate_id": execution_candidate_id,
                "row_role": "success_identity_guard" if index == 3 else "future_training_candidate",
                "m2960_eval_seed": seed,
                "workload_id": workload_id,
                "task_family": "T4",
                "parent_checkpoint_path": str(root / f"checkpoint-{index}.pt"),
                "parent_profile_config_path": str(root / f"profile-{index}.json"),
                "actor_observation_dim": 72,
                "actor_action_dim": 3,
            }
        )
        (root / f"checkpoint-{index}.pt").write_text("checkpoint\n", encoding="utf-8")
        write_json(root / f"profile-{index}.json", {"profile": index})
        parent_rows.append(_metric_row(execution_candidate_id=execution_candidate_id, workload_id=workload_id, seed=seed, success=index == 3))
    write_csv_rows(m2977_dir / "raw_trace_index_rows.csv", raw_index_rows)
    write_csv_rows(m2977_dir / "capture_plan_rows.csv", capture_rows)
    write_csv_rows(m2960_dir / "bounded_execution_rows.csv", parent_rows)

    m2999_design = root / "m2999.md"
    m2999_design.write_text("decision: admit_m3000_bounded_diagnostic_validation_preflight\n", encoding="utf-8")
    executable_specs = root / "specs.json"
    write_json(executable_specs, {"executable_task_specs": []})
    executable_workload = root / "workload.csv"
    write_csv_rows(executable_workload, [{"workload_id": f"workload-{index}"} for index in range(1, 4)])
    return {
        "m2996_dir": m2996_dir,
        "m2977_dir": m2977_dir,
        "m2960_dir": m2960_dir,
        "m2999_design": m2999_design,
        "executable_specs": executable_specs,
        "executable_workload": executable_workload,
    }


def _fake_validation(plan: dict, context: dict) -> dict[str, object]:
    del context
    success = plan["row_role"] == "success_behavior_retention"
    return {
        **_metric_row(
            execution_candidate_id=str(plan["execution_candidate_id"]),
            workload_id=str(plan["workload_id"]),
            seed=int(plan["m2960_eval_seed"]),
            success=success,
        ),
        "actor_observation_dim": 72,
        "actor_action_dim": 3,
        "candidate_residual_head_loaded_read_only": True,
        "parent_checkpoint_loaded_read_only": True,
        "nonzero_residual_wrapper_mode": True,
        "zero_residual_identity_mode": False,
        "residual_limit": 0.08,
        "residual_delta_norm_max": 0.015,
        "residual_delta_abs_max": 0.01,
        "residual_trace_count": 12,
        "parent_action_abs_max": 0.4,
        "bounded_action_abs_max": 0.41,
    }


def test_m3000_builds_candidate_success_and_stale_accounting(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m3000, "EXPECTED_CANDIDATE_VALIDATION_COUNT", 2)
    monkeypatch.setattr(m3000, "EXPECTED_SUCCESS_RETENTION_COUNT", 1)
    monkeypatch.setattr(m3000, "EXPECTED_STALE_EXCLUSION_COUNT", 1)
    paths = _write_source_artifacts(tmp_path)
    source = m3000.load_source_artifacts(
        m2996_dir=paths["m2996_dir"],
        m2999_design=paths["m2999_design"],
        m2977_dir=paths["m2977_dir"],
        m2960_dir=paths["m2960_dir"],
        executable_specs=paths["executable_specs"],
        executable_workload=paths["executable_workload"],
        follow_up_manifest=tmp_path / "m3001.json",
    )

    plan_rows = m3000.build_diagnostic_plan_rows(source)
    stale_rows = m3000.build_stale_exclusion_guard_rows(source)

    assert [row["row_role"] for row in plan_rows] == [
        "candidate_validation",
        "candidate_validation",
        "success_behavior_retention",
    ]
    assert all(row["execution_admitted"] for row in plan_rows)
    assert len(stale_rows) == 1
    assert stale_rows[0]["executed_in_m3000"] is False
    assert stale_rows[0]["validation_denominator_allowed"] is False


def test_m3000_run_writes_claim_safe_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m3000, "EXPECTED_CANDIDATE_VALIDATION_COUNT", 2)
    monkeypatch.setattr(m3000, "EXPECTED_SUCCESS_RETENTION_COUNT", 1)
    monkeypatch.setattr(m3000, "EXPECTED_STALE_EXCLUSION_COUNT", 1)
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m3000"
    doc_path = tmp_path / "m3000.md"
    follow_up = tmp_path / "m3001.json"

    summary = m3000.run_bounded_diagnostic_validation_preflight(
        m2996_dir=paths["m2996_dir"],
        m2999_design=paths["m2999_design"],
        m2977_dir=paths["m2977_dir"],
        m2960_dir=paths["m2960_dir"],
        executable_specs=paths["executable_specs"],
        executable_workload=paths["executable_workload"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
        validation_fn=_fake_validation,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["candidate_validation_execution_row_count"] == 2
    assert summary["success_behavior_retention_execution_row_count"] == 1
    assert summary["candidate_validation_failure_row_count"] == 0
    assert summary["stale_guardrail_executed_count"] == 0
    assert summary["parent_comparison_report_only"] is True
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["checkpoint_mutated"] is False
    assert summary["validation_result_claim_made"] is False
    assert summary["driver_performance_claim_made"] is False
    assert read_json(follow_up)["id"] == m3000.NEXT_ID

    candidate_rows = _read_csv(output_dir / "candidate_validation_execution_rows.csv")
    success_rows = _read_csv(output_dir / "success_behavior_retention_execution_rows.csv")
    failure_rows = _read_csv(output_dir / "candidate_validation_failure_rows.csv")
    stale_rows = _read_csv(output_dir / "stale_exclusion_guard_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")
    assert len(candidate_rows) == 2
    assert len(success_rows) == 1
    assert len(failure_rows) == 0
    assert {row["nonzero_residual_wrapper_mode"] for row in candidate_rows + success_rows} == {"True"}
    assert {row["zero_residual_identity_mode"] for row in candidate_rows + success_rows} == {"False"}
    assert stale_rows[0]["executed_in_m3000"] == "False"
    assert {row["status_pass"] for row in gate_rows} == {"True"}
