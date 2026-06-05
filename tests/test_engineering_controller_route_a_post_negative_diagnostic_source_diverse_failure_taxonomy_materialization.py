from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift import (
    engineering_controller_route_a_post_negative_diagnostic_source_diverse_failure_taxonomy_materialization as m2740,
)


def _write_m2737_source(root: Path) -> None:
    root.mkdir()
    write_json(
        root / "summary.json",
        {
            "status_pass": True,
            "candidate_execution_row_count": 4,
            "negative_context_guard_row_count": 2,
            "blocked_surface_guard_row_count": 3,
            "gate_matrix_pass": True,
        },
    )
    execution_rows = [
        _execution_row("c1", "m2693", "source_diverse_current_sim_offtrack", "T4", success=False, collision=False, outcome="off_track_noncollision_noncompletion"),
        _execution_row("c2", "m2693", "source_diverse_current_sim_offtrack", "T5", success=False, collision=True, outcome="collision_failure"),
        _execution_row("c3", "m2716", "exact_executable_reentry_baseline", "T4", success=True, collision=False, outcome="success_obstacle_pass"),
        _execution_row("c4", "m2716", "exact_executable_reentry_baseline", "T5", success=False, collision=False, outcome="off_track_noncollision_noncompletion"),
    ]
    write_csv_rows(root / "candidate_execution_rows.csv", execution_rows)
    write_csv_rows(
        root / "source_family_aggregate.csv",
        [
            {"source_milestone": "m2693", "source_family": "source_diverse_current_sim_offtrack", "ranking_claim_made": False},
            {"source_milestone": "m2716", "source_family": "exact_executable_reentry_baseline", "ranking_claim_made": False},
        ],
    )
    write_csv_rows(
        root / "task_family_aggregate.csv",
        [
            {"task_family": "T4", "ranking_claim_made": False},
            {"task_family": "T5", "ranking_claim_made": False},
        ],
    )
    write_csv_rows(
        root / "negative_context_guard_rows.csv",
        [
            {
                "guard_id": f"neg-{index}",
                "context_id": f"context-{index}",
                "candidate_row_id": f"negative-candidate-{index}",
                "task_family": "T4",
                "success": False,
                "collision": False,
                "termination_reason": "off_track",
                "outcome_bucket": "off_track_noncollision_noncompletion",
                "execution_admitted": False,
                "execution_run": False,
                "protected_rows_in_success_denominator": False,
                "actor_visible_allowed": False,
            }
            for index in range(1, 3)
        ],
    )
    write_csv_rows(
        root / "blocked_surface_guard_rows.csv",
        [
            _blocked_row("same", "same_surface_repair_loop"),
            _blocked_row("protected", "protected_mitigation_blocker"),
            _blocked_row("hf3", "hf3_source_dependency_blocker"),
        ],
    )
    write_csv_rows(
        root / "actor_contract_guard_rows.csv",
        [
            {"guard_family": "observation_shape", "status_pass": True},
            {"guard_family": "action_shape", "status_pass": True},
            {"guard_family": "hidden_oracle_actor_input_detected", "status_pass": True},
        ],
    )
    write_csv_rows(root / "claim_boundary_rows.csv", [{"claim_id": "claim", "status_pass": True}])
    write_csv_rows(root / "gate_matrix.csv", [{"gate_id": "gate", "status_pass": True}])


def _execution_row(
    candidate_id: str,
    source_milestone: str,
    source_family: str,
    task_family: str,
    *,
    success: bool,
    collision: bool,
    outcome: str,
) -> dict:
    return {
        "candidate_id": candidate_id,
        "resolution_id": f"resolution-{candidate_id}",
        "source_milestone": source_milestone,
        "source_family": source_family,
        "source_key": f"{task_family}:{candidate_id}",
        "workload_id": f"workload-{candidate_id}",
        "task_source_id": f"task-source-{candidate_id}",
        "profile_name": "L3_online_gru",
        "task_family": task_family,
        "outcome_bucket": outcome,
        "success": success,
        "collision": collision,
        "termination_reason": "off_track" if "off_track" in outcome else "",
        "full_rollout_execution": True,
        "hidden_oracle_actor_input_required": False,
        "protected_rows_in_success_denominator": False,
        "ranking_run": False,
        "driver_performance_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "level3_self_id_claim_made": False,
    }


def _blocked_row(blocked_id: str, family: str) -> dict:
    return {
        "guard_id": f"blocked-{blocked_id}",
        "blocked_id": blocked_id,
        "blocked_family": family,
        "source_milestone": "m2737-source",
        "source_row_id": f"source-{blocked_id}",
        "execution_candidate": False,
        "execution_admitted": False,
        "execution_run": False,
        "protected_rows_in_success_denominator": False,
        "actor_visible_allowed": False,
    }


def test_m2740_materializes_source_diverse_taxonomy_without_execution_or_ranking(monkeypatch, tmp_path: Path) -> None:
    m2737_dir = tmp_path / "m2737"
    output_dir = tmp_path / "m2740"
    doc_path = tmp_path / "m2740.md"
    synthesis = tmp_path / "m2739.md"
    follow_up = tmp_path / "m2741.json"
    _write_m2737_source(m2737_dir)
    synthesis.write_text(
        "continue_to_route_a_post_negative_diagnostic_source_diverse_failure_taxonomy_materialization\n",
        encoding="utf-8",
    )
    write_json(follow_up, {"id": "m2741"})
    monkeypatch.setattr(m2740, "EXPECTED_EXECUTION_ROW_COUNT", 4)
    monkeypatch.setattr(m2740, "EXPECTED_NEGATIVE_CONTEXT_GUARD_ROW_COUNT", 2)
    monkeypatch.setattr(m2740, "EXPECTED_BLOCKED_GUARD_ROW_COUNT", 3)
    monkeypatch.setattr(m2740, "EXPECTED_DIAGNOSTIC_SUCCESS_CONTEXT_ROW_COUNT", 1)
    monkeypatch.setattr(m2740, "EXPECTED_COLLISION_FAILURE_ROW_COUNT", 1)
    monkeypatch.setattr(m2740, "EXPECTED_OFFTRACK_ROW_COUNT", 2)

    summary = m2740.materialize_post_negative_source_diverse_failure_taxonomy(
        m2737_dir=m2737_dir,
        m2739_synthesis=synthesis,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["execution_taxonomy_row_count"] == 4
    assert summary["negative_context_taxonomy_row_count"] == 2
    assert summary["blocked_guard_taxonomy_row_count"] == 3
    assert summary["diagnostic_success_context_taxonomy_row_count"] == 1
    assert summary["collision_failure_taxonomy_row_count"] == 1
    assert summary["offtrack_taxonomy_row_count"] == 2
    assert summary["guardrail_execution_run"] is False
    assert summary["source_family_ranking_allowed"] is False
    assert summary["task_family_ranking_allowed"] is False
    assert summary["environment_reset_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert read_json(output_dir / "summary.json") == summary

    taxonomy_rows = m2740.read_csv_rows(output_dir / "taxonomy_rows.csv")
    assert {row["taxonomy_family"] for row in taxonomy_rows} == {
        "diagnostic_success_context",
        "collision_failure",
        "off_track",
        "negative_context_guard",
        "blocked_guard",
        "protected_or_hf3_blocker",
    }
    assert {row["source_family_ranking_allowed"] for row in taxonomy_rows} == {"False"}
    assert {row["task_family_ranking_allowed"] for row in taxonomy_rows} == {"False"}
    guardrail_rows = m2740.read_csv_rows(output_dir / "guardrail_context_rows.csv")
    assert {row["execution_run_count"] for row in guardrail_rows} == {"0"}
    assert {row["actor_visible_count"] for row in guardrail_rows} == {"0"}
    gate_rows = m2740.read_csv_rows(output_dir / "gate_matrix.csv")
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.exists()
