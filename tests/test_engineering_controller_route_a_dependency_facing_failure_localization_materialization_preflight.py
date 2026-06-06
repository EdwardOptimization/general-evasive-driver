from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
import autodrift.engineering_controller_route_a_dependency_facing_failure_localization_materialization_preflight as m2922


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _execution_row(
    index: int,
    *,
    source_milestone: str,
    task_family: str,
    checkpoint_path: str,
    success: bool,
    collision: bool,
    termination_reason: str,
) -> dict[str, object]:
    return {
        "seed": 292200 + index,
        "policy": "checkpoint",
        "steps": 20 + index,
        "collision": collision,
        "termination_reason": termination_reason,
        "min_clearance_margin": 1.0 + index,
        "return": 10.0 + index,
        "success": success,
        "workload_id": f"task-{index}::L3_online_gru",
        "task_source_id": f"task-{index}",
        "profile_name": "L3_online_gru",
        "task_family": task_family,
        "checkpoint_path": checkpoint_path,
        "execution_candidate_id": f"candidate-{index:04d}",
        "source_milestone": source_milestone,
        "training_scheduled": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "hidden_oracle_actor_input_required": False,
        "future_target_actor_input_required": False,
        "route_labels_actor_visible": False,
        "source_labels_actor_visible": False,
        "diagnostic_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "driver_performance_claim_made": False,
        "paper_claim_made": False,
        "level3_self_id_claim_made": False,
        "diagnostic_only_no_verdict": True,
    }


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m2919_dir = root / "m2919"
    rows = [
        _execution_row(
            1,
            source_milestone="m2737",
            task_family="T4",
            checkpoint_path="checkpoint-a.pt",
            success=True,
            collision=False,
            termination_reason="",
        ),
        _execution_row(
            2,
            source_milestone="m2737",
            task_family="T4",
            checkpoint_path="checkpoint-a.pt",
            success=False,
            collision=True,
            termination_reason="obstacle_collision",
        ),
        _execution_row(
            3,
            source_milestone="m2746",
            task_family="T5",
            checkpoint_path="checkpoint-b.pt",
            success=False,
            collision=False,
            termination_reason="off_track",
        ),
        _execution_row(
            4,
            source_milestone="m2746",
            task_family="T5",
            checkpoint_path="checkpoint-b.pt",
            success=False,
            collision=False,
            termination_reason="speed_too_low",
        ),
    ]
    write_json(m2919_dir / "summary.json", {"status_pass": True, "gate_matrix_pass": True})
    write_csv_rows(m2919_dir / "execution_candidate_rows.csv", [{"execution_candidate_id": row["execution_candidate_id"]} for row in rows])
    write_csv_rows(m2919_dir / "execution_resolution_rows.csv", [{"resolution_id": f"resolution-{index}"} for index in range(1, 5)])
    write_csv_rows(m2919_dir / "bounded_execution_rows.csv", rows)
    write_csv_rows(m2919_dir / "bounded_execution_failure_rows.csv", [], fieldnames=["error_type"])
    write_csv_rows(
        m2919_dir / "source_milestone_aggregate.csv",
        [
            {"aggregate_family": "source_milestone", "aggregate_value": "m2737", "episode_count": 2},
            {"aggregate_family": "source_milestone", "aggregate_value": "m2746", "episode_count": 2},
        ],
    )
    write_csv_rows(
        m2919_dir / "task_family_aggregate.csv",
        [
            {"aggregate_family": "task_family", "aggregate_value": "T4", "episode_count": 2},
            {"aggregate_family": "task_family", "aggregate_value": "T5", "episode_count": 2},
        ],
    )
    write_csv_rows(
        m2919_dir / "guardrail_context_rows.csv",
        [
            {
                "guardrail_source": "m2913_route_context_rows",
                "guardrail_family": "same_family_route_b_acquisition_rows",
                "source_milestone": "",
                "source_row_id": "route-b",
                "guardrail_reason": "context only",
                "row_count": 1,
                "execution_run": False,
            },
            {
                "guardrail_source": "m2913_route_context_rows",
                "guardrail_family": "route_c_source_unavailable_rows",
                "source_milestone": "",
                "source_row_id": "route-c",
                "guardrail_reason": "context only",
                "row_count": 1,
                "execution_run": False,
            },
        ],
    )
    for name in ["actor_contract_guard_rows.csv", "claim_boundary_rows.csv", "gate_matrix.csv"]:
        write_csv_rows(m2919_dir / name, [{"id": "placeholder", "status_pass": True}])

    m2920_audit = root / "m2920.md"
    m2921_synthesis = root / "m2921.md"
    m2920_audit.write_text("M2920 accepts M2919 as complete and claim-safe.\n", encoding="utf-8")
    m2921_synthesis.write_text(m2922.MILESTONE_ID + "\n", encoding="utf-8")
    return {"m2919_dir": m2919_dir, "m2920_audit": m2920_audit, "m2921_synthesis": m2921_synthesis}


def test_outcome_family_classifier_and_group_rows() -> None:
    rows = [
        _execution_row(1, source_milestone="m2737", task_family="T4", checkpoint_path="a.pt", success=True, collision=False, termination_reason=""),
        _execution_row(2, source_milestone="m2737", task_family="T4", checkpoint_path="a.pt", success=False, collision=True, termination_reason="obstacle_collision"),
        _execution_row(3, source_milestone="m2746", task_family="T5", checkpoint_path="b.pt", success=False, collision=False, termination_reason="off_track"),
        _execution_row(4, source_milestone="m2746", task_family="T5", checkpoint_path="b.pt", success=False, collision=False, termination_reason="speed_too_low"),
    ]

    assert [m2922.outcome_family(row) for row in rows] == [
        "diagnostic_success",
        "collision",
        "off_track",
        "speed_too_low",
    ]
    outcome_rows = m2922.build_outcome_family_rows(rows)
    assert {row["outcome_family"]: row["row_count"] for row in outcome_rows} == {
        "diagnostic_success": 1,
        "collision": 1,
        "off_track": 1,
        "speed_too_low": 1,
    }
    source_rows = m2922.build_group_rows(rows, group_family="source_milestone", key="source_milestone")
    assert {row["group_value"]: row["row_count"] for row in source_rows} == {"m2737": 2, "m2746": 2}
    assert {row["ranking_claim_made"] for row in source_rows} == {False}


def test_run_materialization_writes_complete_no_execution_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m2922, "EXPECTED_EXECUTION_ROW_COUNT", 4)
    monkeypatch.setattr(m2922, "EXPECTED_OUTCOME_COUNTS", {"diagnostic_success": 1, "collision": 1, "off_track": 1, "speed_too_low": 1})
    monkeypatch.setattr(m2922, "EXPECTED_SOURCE_MILESTONE_COUNTS", {"m2737": 2, "m2746": 2})
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m2922"
    doc_path = tmp_path / "m2922.md"
    follow_up = tmp_path / "m2923.json"

    summary = m2922.run_failure_localization_materialization_preflight(
        m2919_dir=paths["m2919_dir"],
        m2920_audit=paths["m2920_audit"],
        m2921_synthesis=paths["m2921_synthesis"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["execution_row_count"] == 4
    assert summary["bounded_execution_failure_row_count"] == 0
    assert summary["outcome_counts"] == {"diagnostic_success": 1, "collision": 1, "off_track": 1, "speed_too_low": 1}
    assert summary["source_milestone_counts"] == {"m2737": 2, "m2746": 2}
    assert summary["next_route_candidate_row_count"] == 4
    assert summary["next_route_candidate_admitted_count"] >= 3
    assert summary["environment_reset_run"] is False
    assert summary["policy_rollout_run"] is False
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert doc_path.exists()
    assert read_json(follow_up)["id"] == m2922.NEXT_ID

    assert len(_read_csv(output_dir / "source_milestone_outcome_rows.csv")) == 2
    assert len(_read_csv(output_dir / "task_family_outcome_rows.csv")) == 2
    assert len(_read_csv(output_dir / "checkpoint_outcome_rows.csv")) == 2
    next_route_rows = _read_csv(output_dir / "next_route_candidate_rows.csv")
    assert {row["execution_scheduled"] for row in next_route_rows} == {"False"}
    assert {row["ranking_allowed"] for row in next_route_rows} == {"False"}
    assert {row["status_pass"] for row in _read_csv(output_dir / "gate_matrix.csv")} == {"True"}
