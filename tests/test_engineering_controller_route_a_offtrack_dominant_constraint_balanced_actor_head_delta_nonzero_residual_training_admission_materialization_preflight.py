from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
import autodrift.engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_training_admission_materialization_preflight as m2970


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _row_assignment(index: int, *, outcome_family: str, objective_family: str) -> dict[str, object]:
    success = objective_family == "success_identity_guard"
    return {
        "assignment_id": f"m2966-row-assignment-{index:04d}",
        "localization_row_id": f"m2963-failure-localization-{index:04d}",
        "execution_candidate_id": f"m2960-execution-candidate-{index:04d}",
        "source_milestone": "m2737" if index <= 2 else "m2746",
        "source_row_id": f"source-row-{index:04d}",
        "task_family": "T4" if index <= 2 else "T5",
        "workload_id": f"task-{index}::L3_online_gru",
        "outcome_family": outcome_family,
        "objective_family": objective_family,
        "objective_role": "success_identity_guard" if success else "future_training_candidate_after_audit",
        "training_candidate_after_future_audit": not success,
        "success_identity_guard": success,
        "stale_guardrail": False,
        "actor_visible_label": False,
        "training_scheduled": False,
        "execution_scheduled": False,
        "ranking_allowed": False,
        "validation_denominator_allowed": False,
        "paper_denominator_allowed": False,
    }


def _objective_family_row(index: int, *, objective_family: str, outcome: str, count: int) -> dict[str, object]:
    admitted = objective_family != "success_identity_guard"
    return {
        "objective_family": objective_family,
        "source_trigger_outcome": outcome,
        "source_row_count": count,
        "admitted_for_materialization": True,
        "future_training_manifest_required": admitted,
        "future_execution_manifest_required": admitted,
        "training_scheduled": False,
        "execution_scheduled": False,
        "ranking_allowed": False,
        "winner_selection_allowed": False,
        "promotion_allowed": False,
        "ordinary_engineering_denominator_allowed": False,
        "validation_denominator_allowed": False,
        "paper_denominator_allowed": False,
        "high_fidelity_readiness_allowed": False,
        "self_id_claim_allowed": False,
        "actor_input_change_required": False,
        "actor_visible_labels_required": False,
        "claim_boundary": f"family {index}",
    }


def _objective_component_row(index: int, *, objective_family: str) -> dict[str, object]:
    return {
        "component_id": f"m2966-objective-component-{index:04d}",
        "objective_family": objective_family,
        "component_role": "identity_residual_guard"
        if objective_family == "success_identity_guard"
        else "future_training_candidate_after_audit",
        "source_trigger_outcome": "diagnostic_success" if objective_family == "success_identity_guard" else "non_success",
        "source_row_count": 1,
        "loss_component": f"loss-{index}",
        "target_signal": f"target-{index}-not-actor-input",
        "success_identity_guard": objective_family == "success_identity_guard",
        "materialization_only_no_training": True,
        "actor_visible": False,
        "training_scheduled": False,
        "execution_scheduled": False,
        "ranking_allowed": False,
    }


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m2966_dir = root / "m2966"
    m2966_dir.mkdir()
    write_json(
        m2966_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "actor_input_contract_changed": False,
            "hidden_oracle_actor_input_detected": False,
            "future_target_actor_input_required": False,
        },
    )
    families = [
        ("collision_clearance_residual_objective", "collision", 1),
        ("offtrack_recovery_residual_objective", "off_track", 1),
        ("speed_floor_context_guard_objective", "speed_too_low", 1),
        ("success_identity_guard", "diagnostic_success", 1),
    ]
    write_csv_rows(
        m2966_dir / "objective_family_rows.csv",
        [
            _objective_family_row(index, objective_family=family, outcome=outcome, count=count)
            for index, (family, outcome, count) in enumerate(families, start=1)
        ],
    )
    write_csv_rows(
        m2966_dir / "objective_component_rows.csv",
        [
            _objective_component_row(index, objective_family=family)
            for index, (family, _outcome, _count) in enumerate(families, start=1)
        ],
    )
    write_csv_rows(
        m2966_dir / "row_assignment_rows.csv",
        [
            _row_assignment(
                1,
                outcome_family="diagnostic_success",
                objective_family="success_identity_guard",
            ),
            _row_assignment(
                2,
                outcome_family="collision",
                objective_family="collision_clearance_residual_objective",
            ),
            _row_assignment(
                3,
                outcome_family="off_track",
                objective_family="offtrack_recovery_residual_objective",
            ),
            _row_assignment(
                4,
                outcome_family="speed_too_low",
                objective_family="speed_floor_context_guard_objective",
            ),
        ],
    )
    write_csv_rows(
        m2966_dir / "success_identity_guard_rows.csv",
        [
            {
                "guard_id": "m2966-success-identity-guard-0001",
                "localization_row_id": "m2963-failure-localization-0001",
                "execution_candidate_id": "m2960-execution-candidate-0001",
                "source_milestone": "m2737",
                "task_family": "T4",
                "outcome_family": "diagnostic_success",
                "residual_target": "zero_residual_identity",
                "actor_visible": False,
                "positive_training_target": False,
                "training_scheduled": False,
                "execution_scheduled": False,
            }
        ],
    )
    write_csv_rows(
        m2966_dir / "stale_guardrail_rows.csv",
        [
            {
                "guardrail_id": f"m2966-stale-guardrail-{index:04d}",
                "source_guardrail_context_id": f"m2963-guard-{index:04d}",
                "guardrail_source": "m2956_rejection_rows",
                "guardrail_family": "actor_head_delta_execution_admission_blocked_stale_fixed_surface",
                "source_milestone": "m2877",
                "source_row_id": f"blocked-{index}",
                "row_count": 1,
                "execution_run": False,
                "objective_denominator_allowed": False,
                "training_scheduled": False,
                "execution_scheduled": False,
            }
            for index in range(1, 3)
        ],
    )
    for name in ["actor_contract_guard_rows.csv", "claim_boundary_rows.csv", "gate_matrix.csv"]:
        write_csv_rows(m2966_dir / name, [{"id": "placeholder", "status_pass": True}])

    m2967_audit = root / "m2967.md"
    m2968_synthesis = root / "m2968.md"
    m2969_design = root / "m2969.md"
    m2967_audit.write_text(
        "accept_m2966_nonzero_residual_objective_materialization_claim_safe_route_to_m2968_objective_branch_synthesis\n",
        encoding="utf-8",
    )
    m2968_synthesis.write_text("continue_to_m2969_nonzero_residual_training_admission_design\n", encoding="utf-8")
    m2969_design.write_text(m2970.MILESTONE_ID + "\n", encoding="utf-8")
    return {
        "m2966_dir": m2966_dir,
        "m2967_audit": m2967_audit,
        "m2968_synthesis": m2968_synthesis,
        "m2969_design": m2969_design,
    }


def test_m2970_candidate_rows_preserve_no_training_boundary() -> None:
    assignment_rows = [
        _row_assignment(1, outcome_family="diagnostic_success", objective_family="success_identity_guard"),
        _row_assignment(2, outcome_family="collision", objective_family="collision_clearance_residual_objective"),
    ]

    candidate_rows = m2970.build_training_admission_candidate_rows(assignment_rows)

    assert len(candidate_rows) == 1
    assert candidate_rows[0]["objective_family"] == "collision_clearance_residual_objective"
    assert candidate_rows[0]["future_training_manifest_required"] is True
    assert candidate_rows[0]["training_scheduled"] is False
    assert candidate_rows[0]["ppo_scheduled"] is False
    assert candidate_rows[0]["actor_visible_label"] is False


def test_run_m2970_materialization_writes_no_execution_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m2970, "EXPECTED_ROW_ASSIGNMENT_COUNT", 4)
    monkeypatch.setattr(m2970, "EXPECTED_TRAINING_CANDIDATE_COUNT", 3)
    monkeypatch.setattr(m2970, "EXPECTED_SUCCESS_IDENTITY_ROW_COUNT", 1)
    monkeypatch.setattr(m2970, "EXPECTED_STALE_GUARDRAIL_COUNT", 2)
    monkeypatch.setattr(m2970, "EXPECTED_OUTCOME_COUNTS", {"diagnostic_success": 1, "collision": 1, "off_track": 1, "speed_too_low": 1})
    monkeypatch.setattr(
        m2970,
        "EXPECTED_TRAINING_CANDIDATE_OBJECTIVE_COUNTS",
        {
            "collision_clearance_residual_objective": 1,
            "offtrack_recovery_residual_objective": 1,
            "speed_floor_context_guard_objective": 1,
        },
    )
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m2970"
    doc_path = tmp_path / "m2970.md"
    follow_up = tmp_path / "m2971.json"

    summary = m2970.run_nonzero_residual_training_admission_materialization_preflight(
        m2966_dir=paths["m2966_dir"],
        m2967_audit=paths["m2967_audit"],
        m2968_synthesis=paths["m2968_synthesis"],
        m2969_design=paths["m2969_design"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["source_row_assignment_count"] == 4
    assert summary["training_admission_profile_row_count"] == 1
    assert summary["training_admission_candidate_row_count"] == 3
    assert summary["training_admission_guard_row_count"] == 3
    assert summary["objective_balance_row_count"] == 4
    assert summary["success_identity_guard_row_count"] == 1
    assert summary["stale_guardrail_row_count"] == 2
    assert summary["training_run"] is False
    assert summary["ppo_run"] is False
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert doc_path.exists()
    assert read_json(follow_up)["id"] == m2970.NEXT_ID

    profile_rows = _read_csv(output_dir / "training_admission_profile_rows.csv")
    candidate_rows = _read_csv(output_dir / "training_admission_candidate_rows.csv")
    guard_rows = _read_csv(output_dir / "training_admission_guard_rows.csv")
    objective_rows = _read_csv(output_dir / "objective_balance_rows.csv")
    success_rows = _read_csv(output_dir / "success_identity_guard_rows.csv")
    stale_rows = _read_csv(output_dir / "stale_guardrail_rows.csv")
    actor_rows = _read_csv(output_dir / "actor_contract_guard_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")

    assert len(profile_rows) == 1
    assert {row["training_scheduled"] for row in profile_rows} == {"False"}
    assert len(candidate_rows) == 3
    assert {row["training_admission_status"] for row in candidate_rows} == {m2970.TRAINING_ADMISSION_STATUS}
    assert {row["training_scheduled"] for row in candidate_rows} == {"False"}
    assert {row["execution_scheduled"] for row in candidate_rows} == {"False"}
    assert {row["ppo_scheduled"] for row in candidate_rows} == {"False"}
    assert {row["actor_visible_label"] for row in candidate_rows} == {"False"}
    assert {row["validation_denominator_allowed"] for row in candidate_rows} == {"False"}
    assert {row["paper_denominator_allowed"] for row in candidate_rows} == {"False"}
    assert len(guard_rows) == 3
    assert {row["execution_allowed"] for row in guard_rows} == {"False"}
    assert {row["positive_training_target"] for row in guard_rows} == {"False"}
    assert len(objective_rows) == 4
    assert {row["materialization_only_no_training"] for row in objective_rows} == {"True"}
    assert {row["actor_visible"] for row in objective_rows} == {"False"}
    assert len(success_rows) == 1
    assert success_rows[0]["positive_training_target"] == "False"
    assert len(stale_rows) == 2
    assert {row["execution_run"] for row in stale_rows} == {"False"}
    assert {row["training_denominator_allowed"] for row in stale_rows} == {"False"}
    assert {row["status_pass"] for row in actor_rows} == {"True"}
    assert all(row["claim_made"] == "False" for row in claim_rows if row["allowed_in_m2970"] == "False")
    assert {row["status_pass"] for row in gate_rows} == {"True"}
