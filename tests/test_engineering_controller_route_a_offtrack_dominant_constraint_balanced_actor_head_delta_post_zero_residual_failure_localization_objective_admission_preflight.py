from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
import autodrift.engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_post_zero_residual_failure_localization_objective_admission_preflight as m2963


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _execution_row(
    index: int,
    *,
    source_milestone: str,
    task_family: str,
    success: bool,
    collision: bool,
    termination_reason: str,
) -> dict[str, object]:
    return {
        "seed": 296300 + index,
        "policy": "checkpoint",
        "steps": 20 + index,
        "collision": collision,
        "termination_reason": termination_reason,
        "outcome_bucket": "success_obstacle_pass" if success else termination_reason,
        "min_clearance_margin": 1.0 + index,
        "return": 10.0 + index,
        "lateral_rmse": 0.5 + index,
        "beta_abs_error_mean": 0.1 + index,
        "high_sideslip_fraction": 0.01 * index,
        "speed_mean": 4.0 + index,
        "action_rate_mean": 0.02 * index,
        "max_off_track_overshoot": 0.10 if termination_reason == "off_track" else 0.0,
        "time_to_first_off_track_s": 1.0 if termination_reason == "off_track" else "",
        "off_track_severity_proxy": 0.10 if termination_reason == "off_track" else 0.0,
        "recoverability_window_success_available": False,
        "recoverability_window_success": False,
        "success": success,
        "workload_id": f"task-{index}::L3_online_gru",
        "task_source_id": f"task-{index}",
        "profile_name": "L3_online_gru",
        "task_family": task_family,
        "source_edge": "capability_step_up",
        "window_tag": "mapping_window_unspecified",
        "checkpoint_path": "checkpoint.pt",
        "parent_checkpoint_path": "checkpoint.pt",
        "execution_candidate_id": f"m2960-execution-candidate-{index:04d}",
        "resolution_id": f"m2960-resolution-{index:04d}",
        "actor_head_delta_candidate_id": f"m2956-actor-head-delta-candidate-{index:04d}",
        "source_execution_admission_candidate_id": f"m2916-execution-admission-candidate-{index:04d}",
        "source_milestone": source_milestone,
        "source_family": "test_source",
        "source_row_id": f"source-row-{index:04d}",
        "diagnostic_only_no_verdict": True,
    }


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m2960_dir = root / "m2960"
    rows = [
        _execution_row(
            1,
            source_milestone="m2737",
            task_family="T4",
            success=True,
            collision=False,
            termination_reason="",
        ),
        _execution_row(
            2,
            source_milestone="m2737",
            task_family="T4",
            success=False,
            collision=True,
            termination_reason="obstacle_collision",
        ),
        _execution_row(
            3,
            source_milestone="m2746",
            task_family="T5",
            success=False,
            collision=False,
            termination_reason="off_track",
        ),
        _execution_row(
            4,
            source_milestone="m2746",
            task_family="T5",
            success=False,
            collision=False,
            termination_reason="speed_too_low",
        ),
    ]
    write_json(
        m2960_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "zero_residual_identity_mode": True,
            "residual_delta_abs_max": 0.0,
            "blocked_stale_guard_row_count": 2,
            "hidden_oracle_actor_input_detected": False,
            "future_target_actor_input_required": False,
        },
    )
    write_csv_rows(m2960_dir / "execution_candidate_rows.csv", [{"execution_candidate_id": row["execution_candidate_id"]} for row in rows])
    write_csv_rows(m2960_dir / "execution_resolution_rows.csv", [{"resolution_id": row["resolution_id"]} for row in rows])
    write_csv_rows(
        m2960_dir / "actor_head_delta_contract_execution_rows.csv",
        [
            {
                "actor_head_delta_contract_execution_id": f"contract-{index:04d}",
                "execution_candidate_id": row["execution_candidate_id"],
                "actor_observation_dim": 72,
                "actor_action_dim": 3,
                "zero_residual_identity_mode": True,
                "residual_delta_abs_max": 0.0,
                "status_pass": True,
            }
            for index, row in enumerate(rows, start=1)
        ],
    )
    write_csv_rows(m2960_dir / "bounded_execution_rows.csv", rows)
    write_csv_rows(m2960_dir / "bounded_execution_failure_rows.csv", [], fieldnames=["error_type"])
    write_csv_rows(m2960_dir / "source_milestone_aggregate.csv", [{"aggregate_value": "m2737"}, {"aggregate_value": "m2746"}])
    write_csv_rows(m2960_dir / "task_family_aggregate.csv", [{"aggregate_value": "T4"}, {"aggregate_value": "T5"}])
    write_csv_rows(
        m2960_dir / "guardrail_context_rows.csv",
        [
            {
                "guardrail_context_id": "m2960-guard-0001",
                "guardrail_source": "m2956_rejection_rows",
                "guardrail_family": "actor_head_delta_execution_admission_blocked_stale_fixed_surface",
                "source_milestone": "m2877",
                "source_row_id": "blocked-1",
                "guardrail_reason": "blocked stale fixed source",
                "row_count": 1,
                "execution_run": False,
            },
            {
                "guardrail_context_id": "m2960-guard-0002",
                "guardrail_source": "m2956_rejection_rows",
                "guardrail_family": "actor_head_delta_execution_admission_blocked_stale_fixed_surface",
                "source_milestone": "m2877",
                "source_row_id": "blocked-2",
                "guardrail_reason": "blocked stale fixed source",
                "row_count": 1,
                "execution_run": False,
            },
        ],
    )
    for name in ["actor_contract_guard_rows.csv", "claim_boundary_rows.csv", "gate_matrix.csv"]:
        write_csv_rows(m2960_dir / name, [{"id": "placeholder", "status_pass": True}])

    m2961_audit = root / "m2961.md"
    m2962_synthesis = root / "m2962.md"
    m2961_audit.write_text("M2961 accepts M2960 as complete and claim-safe.\n", encoding="utf-8")
    m2962_synthesis.write_text(m2963.MILESTONE_ID + "\n", encoding="utf-8")
    return {"m2960_dir": m2960_dir, "m2961_audit": m2961_audit, "m2962_synthesis": m2962_synthesis}


def test_outcome_and_objective_classification() -> None:
    rows = [
        _execution_row(1, source_milestone="m2737", task_family="T4", success=True, collision=False, termination_reason=""),
        _execution_row(2, source_milestone="m2737", task_family="T4", success=False, collision=True, termination_reason="obstacle_collision"),
        _execution_row(3, source_milestone="m2746", task_family="T5", success=False, collision=False, termination_reason="off_track"),
        _execution_row(4, source_milestone="m2746", task_family="T5", success=False, collision=False, termination_reason="speed_too_low"),
    ]

    assert [m2963.outcome_family(row) for row in rows] == [
        "diagnostic_success",
        "collision",
        "off_track",
        "speed_too_low",
    ]
    localization_rows = m2963.build_failure_localization_rows(rows)
    assert {row["candidate_admitted_for_objective_audit"] for row in localization_rows} == {True, False}
    assert {
        row["residual_objective_candidate_family"]
        for row in localization_rows
        if row["candidate_admitted_for_objective_audit"]
    } == {
        "collision_clearance_residual_objective",
        "offtrack_recovery_residual_objective",
        "speed_floor_context_guard_objective",
    }
    objective_rows = m2963.build_residual_objective_admission_rows(localization_rows)
    assert {row["objective_family"] for row in objective_rows} >= {
        "collision_clearance_residual_objective",
        "offtrack_recovery_residual_objective",
        "speed_floor_context_guard_objective",
        "success_identity_guard",
    }
    assert {row["training_scheduled"] for row in objective_rows} == {False}


def test_run_m2963_materialization_writes_no_execution_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m2963, "EXPECTED_EXECUTION_ROW_COUNT", 4)
    monkeypatch.setattr(m2963, "EXPECTED_CONTRACT_ROW_COUNT", 4)
    monkeypatch.setattr(m2963, "EXPECTED_BLOCKED_STALE_GUARD_COUNT", 2)
    monkeypatch.setattr(m2963, "EXPECTED_OUTCOME_COUNTS", {"diagnostic_success": 1, "collision": 1, "off_track": 1, "speed_too_low": 1})
    monkeypatch.setattr(m2963, "EXPECTED_SOURCE_MILESTONE_COUNTS", {"m2737": 2, "m2746": 2})
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m2963"
    doc_path = tmp_path / "m2963.md"
    follow_up = tmp_path / "m2964.json"

    summary = m2963.run_post_zero_residual_failure_localization_objective_admission_preflight(
        m2960_dir=paths["m2960_dir"],
        m2961_audit=paths["m2961_audit"],
        m2962_synthesis=paths["m2962_synthesis"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["execution_row_count"] == 4
    assert summary["bounded_execution_failure_row_count"] == 0
    assert summary["actor_head_delta_contract_execution_row_count"] == 4
    assert summary["outcome_counts"] == {"diagnostic_success": 1, "collision": 1, "off_track": 1, "speed_too_low": 1}
    assert summary["source_milestone_counts"] == {"m2737": 2, "m2746": 2}
    assert summary["failure_localization_row_count"] == 4
    assert summary["residual_objective_admission_row_count"] == 4
    assert summary["residual_objective_admitted_for_audit_count"] == 3
    assert summary["environment_reset_run"] is False
    assert summary["policy_rollout_run"] is False
    assert summary["training_run"] is False
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert doc_path.exists()
    assert read_json(follow_up)["id"] == m2963.NEXT_ID

    localization_rows = _read_csv(output_dir / "failure_localization_rows.csv")
    assert len(localization_rows) == 4
    assert {row["execution_scheduled"] for row in localization_rows} == {"False"}
    assert {row["training_scheduled"] for row in localization_rows} == {"False"}
    assert {row["ranking_allowed"] for row in localization_rows} == {"False"}

    objective_rows = _read_csv(output_dir / "residual_objective_admission_rows.csv")
    assert len(objective_rows) == 4
    assert {row["execution_scheduled"] for row in objective_rows} == {"False"}
    assert {row["ranking_allowed"] for row in objective_rows} == {"False"}
    assert sum(row["admitted_for_m2964_audit"] == "True" for row in objective_rows) == 3

    assert len(_read_csv(output_dir / "source_milestone_aggregate.csv")) == 2
    assert len(_read_csv(output_dir / "task_family_aggregate.csv")) == 2
    assert len(_read_csv(output_dir / "outcome_family_aggregate.csv")) == 4
    assert {row["status_pass"] for row in _read_csv(output_dir / "gate_matrix.csv")} == {"True"}
