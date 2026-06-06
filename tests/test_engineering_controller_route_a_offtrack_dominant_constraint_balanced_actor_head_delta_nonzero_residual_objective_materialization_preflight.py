from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
import autodrift.engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_objective_materialization_preflight as m2966


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _localization_row(index: int, *, outcome_family: str, objective_family: str) -> dict[str, object]:
    return {
        "localization_row_id": f"m2963-failure-localization-{index:04d}",
        "execution_candidate_id": f"m2960-execution-candidate-{index:04d}",
        "source_milestone": "m2737" if index <= 2 else "m2746",
        "source_row_id": f"source-row-{index:04d}",
        "task_family": "T4" if index <= 2 else "T5",
        "workload_id": f"task-{index}::L3_online_gru",
        "outcome_family": outcome_family,
        "residual_objective_candidate_family": objective_family,
        "candidate_admitted_for_objective_audit": objective_family != "success_identity_guard",
        "training_scheduled": False,
        "execution_scheduled": False,
        "ranking_allowed": False,
    }


def _objective_admission_row(index: int, *, objective_family: str, outcome: str, count: int, admitted: bool) -> dict[str, object]:
    return {
        "admission_row_id": f"m2963-residual-objective-admission-{index:04d}",
        "objective_family": objective_family,
        "trigger_outcome_family": outcome,
        "candidate_row_count": count,
        "admitted_for_m2964_audit": admitted,
        "training_scheduled": False,
        "execution_scheduled": False,
        "ranking_allowed": False,
    }


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m2963_dir = root / "m2963"
    localization_rows = [
        _localization_row(1, outcome_family="diagnostic_success", objective_family="success_identity_guard"),
        _localization_row(2, outcome_family="collision", objective_family="collision_clearance_residual_objective"),
        _localization_row(3, outcome_family="off_track", objective_family="offtrack_recovery_residual_objective"),
        _localization_row(4, outcome_family="speed_too_low", objective_family="speed_floor_context_guard_objective"),
    ]
    objective_rows = [
        _objective_admission_row(
            1,
            objective_family="collision_clearance_residual_objective",
            outcome="collision",
            count=1,
            admitted=True,
        ),
        _objective_admission_row(
            2,
            objective_family="offtrack_recovery_residual_objective",
            outcome="off_track",
            count=1,
            admitted=True,
        ),
        _objective_admission_row(
            3,
            objective_family="speed_floor_context_guard_objective",
            outcome="speed_too_low",
            count=1,
            admitted=True,
        ),
        _objective_admission_row(
            4,
            objective_family="success_identity_guard",
            outcome="diagnostic_success",
            count=1,
            admitted=False,
        ),
    ]
    write_json(
        m2963_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "actor_input_contract_changed": False,
            "hidden_oracle_actor_input_detected": False,
            "future_target_actor_input_required": False,
        },
    )
    write_csv_rows(m2963_dir / "failure_localization_rows.csv", localization_rows)
    write_csv_rows(m2963_dir / "residual_objective_admission_rows.csv", objective_rows)
    write_csv_rows(
        m2963_dir / "guardrail_context_rows.csv",
        [
            {
                "guardrail_context_id": "m2963-guard-0001",
                "guardrail_source": "m2956_rejection_rows",
                "guardrail_family": "actor_head_delta_execution_admission_blocked_stale_fixed_surface",
                "source_milestone": "m2877",
                "source_row_id": "blocked-1",
                "guardrail_reason": "blocked stale fixed source",
                "row_count": 1,
                "execution_run": False,
            },
            {
                "guardrail_context_id": "m2963-guard-0002",
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
        write_csv_rows(m2963_dir / name, [{"id": "placeholder", "status_pass": True}])

    m2964_audit = root / "m2964.md"
    m2965_design = root / "m2965.md"
    m2964_audit.write_text("accept_m2963_post_zero_residual_failure_localization_objective_admission\n", encoding="utf-8")
    m2965_design.write_text(m2966.MILESTONE_ID + "\n", encoding="utf-8")
    return {"m2963_dir": m2963_dir, "m2964_audit": m2964_audit, "m2965_design": m2965_design}


def test_m2966_objective_rows_preserve_training_boundary() -> None:
    objective_rows = [
        _objective_admission_row(
            1,
            objective_family="collision_clearance_residual_objective",
            outcome="collision",
            count=7,
            admitted=True,
        ),
        _objective_admission_row(
            2,
            objective_family="success_identity_guard",
            outcome="diagnostic_success",
            count=13,
            admitted=False,
        ),
    ]

    family_rows = m2966.build_objective_family_rows(objective_rows)
    assert {row["objective_family"] for row in family_rows} == {
        "collision_clearance_residual_objective",
        "success_identity_guard",
    }
    assert {row["training_scheduled"] for row in family_rows} == {False}
    assert {row["actor_visible_labels_required"] for row in family_rows} == {False}
    success_row = next(row for row in family_rows if row["objective_family"] == "success_identity_guard")
    assert success_row["future_training_manifest_required"] is False

    components = m2966.build_objective_component_rows(family_rows)
    assert {row["materialization_only_no_training"] for row in components} == {True}
    assert {row["actor_visible"] for row in components} == {False}


def test_run_m2966_materialization_writes_no_execution_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m2966, "EXPECTED_LOCALIZATION_ROW_COUNT", 4)
    monkeypatch.setattr(m2966, "EXPECTED_SUCCESS_IDENTITY_ROW_COUNT", 1)
    monkeypatch.setattr(m2966, "EXPECTED_STALE_GUARDRAIL_COUNT", 2)
    monkeypatch.setattr(m2966, "EXPECTED_OUTCOME_COUNTS", {"diagnostic_success": 1, "collision": 1, "off_track": 1, "speed_too_low": 1})
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m2966"
    doc_path = tmp_path / "m2966.md"
    follow_up = tmp_path / "m2967.json"

    summary = m2966.run_nonzero_residual_objective_materialization_preflight(
        m2963_dir=paths["m2963_dir"],
        m2964_audit=paths["m2964_audit"],
        m2965_design=paths["m2965_design"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["failure_localization_row_count"] == 4
    assert summary["residual_objective_admission_row_count"] == 4
    assert summary["objective_family_row_count"] == 4
    assert summary["objective_component_row_count"] == 4
    assert summary["row_assignment_row_count"] == 4
    assert summary["success_identity_guard_row_count"] == 1
    assert summary["stale_guardrail_row_count"] == 2
    assert summary["non_success_objective_family_count"] == 3
    assert summary["environment_reset_run"] is False
    assert summary["policy_rollout_run"] is False
    assert summary["training_run"] is False
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert doc_path.exists()
    assert read_json(follow_up)["id"] == m2966.NEXT_ID

    family_rows = _read_csv(output_dir / "objective_family_rows.csv")
    assert len(family_rows) == 4
    assert {row["training_scheduled"] for row in family_rows} == {"False"}
    assert {row["execution_scheduled"] for row in family_rows} == {"False"}
    assert {row["actor_visible_labels_required"] for row in family_rows} == {"False"}

    assignment_rows = _read_csv(output_dir / "row_assignment_rows.csv")
    assert len(assignment_rows) == 4
    assert {row["training_scheduled"] for row in assignment_rows} == {"False"}
    assert {row["execution_scheduled"] for row in assignment_rows} == {"False"}
    assert sum(row["training_candidate_after_future_audit"] == "True" for row in assignment_rows) == 3
    assert sum(row["success_identity_guard"] == "True" for row in assignment_rows) == 1

    success_rows = _read_csv(output_dir / "success_identity_guard_rows.csv")
    assert len(success_rows) == 1
    assert success_rows[0]["positive_training_target"] == "False"

    stale_rows = _read_csv(output_dir / "stale_guardrail_rows.csv")
    assert len(stale_rows) == 2
    assert {row["execution_run"] for row in stale_rows} == {"False"}
    assert {row["objective_denominator_allowed"] for row in stale_rows} == {"False"}

    assert {row["status_pass"] for row in _read_csv(output_dir / "gate_matrix.csv")} == {"True"}
