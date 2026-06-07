from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
import autodrift.engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_target_source_feasibility_preflight as m2981


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m2977_dir = root / "m2977"
    m2970_dir = root / "m2970"
    m2977_dir.mkdir()
    m2970_dir.mkdir()
    write_json(m2977_dir / "summary.json", {"status_pass": True, "gate_matrix_pass": True})
    raw_trace_dir = m2977_dir / "raw_traces"
    raw_trace_dir.mkdir()
    for name in ("candidate-1.npz", "candidate-2.npz", "success-1.npz"):
        (raw_trace_dir / name).write_bytes(b"npz-placeholder")
    raw_trace_index_rows = [
        {
            "raw_trace_index_row_id": "raw-1",
            "source_row_id": "candidate-1",
            "execution_candidate_id": "exec-1",
            "row_role": "future_training_candidate",
            "objective_or_guard_family": "offtrack_recovery_residual_objective",
            "raw_trace_path": str(raw_trace_dir / "candidate-1.npz"),
            "raw_trace_persisted": True,
            "trace_step_count": 5,
            "actor_observation_dim": 72,
            "actor_action_dim": 3,
            "outcome_bucket": "off_track",
        },
        {
            "raw_trace_index_row_id": "raw-2",
            "source_row_id": "candidate-2",
            "execution_candidate_id": "exec-2",
            "row_role": "future_training_candidate",
            "objective_or_guard_family": "collision_clearance_residual_objective",
            "raw_trace_path": str(raw_trace_dir / "candidate-2.npz"),
            "raw_trace_persisted": True,
            "trace_step_count": 4,
            "actor_observation_dim": 72,
            "actor_action_dim": 3,
            "outcome_bucket": "collision",
        },
        {
            "raw_trace_index_row_id": "raw-3",
            "source_row_id": "success-1",
            "execution_candidate_id": "exec-3",
            "row_role": "success_identity_guard",
            "objective_or_guard_family": "success_identity_guard",
            "raw_trace_path": str(raw_trace_dir / "success-1.npz"),
            "raw_trace_persisted": True,
            "trace_step_count": 3,
            "actor_observation_dim": 72,
            "actor_action_dim": 3,
            "outcome_bucket": "diagnostic_success",
        },
    ]
    raw_trace_guard_rows = [
        {
            "raw_trace_guard_row_id": "guard-success-1",
            "source_row_id": "success-1",
            "execution_candidate_id": "exec-3",
            "guard_family": "success_identity_guard",
            "guard_role": "success_identity_guard",
        },
        {
            "raw_trace_guard_row_id": "guard-stale-1",
            "source_row_id": "stale-1",
            "execution_candidate_id": "",
            "guard_family": "actor_head_delta_execution_admission_blocked_stale_fixed_surface",
            "guard_role": "stale_fixed_source_guardrail",
        },
    ]
    write_csv_rows(m2977_dir / "raw_trace_index_rows.csv", raw_trace_index_rows)
    write_csv_rows(m2977_dir / "raw_trace_guard_rows.csv", raw_trace_guard_rows)
    write_csv_rows(m2977_dir / "raw_trace_availability_rows.csv", [{"row": "availability"}])
    write_csv_rows(
        m2970_dir / "objective_balance_rows.csv",
        [
            {"objective_family": "offtrack_recovery_residual_objective"},
            {"objective_family": "collision_clearance_residual_objective"},
            {"objective_family": "success_identity_guard"},
        ],
    )
    write_csv_rows(
        m2970_dir / "training_admission_candidate_rows.csv",
        [
            {"training_admission_candidate_id": "candidate-1", "outcome_family": "off_track"},
            {"training_admission_candidate_id": "candidate-2", "outcome_family": "collision"},
        ],
    )
    write_csv_rows(
        m2970_dir / "training_admission_guard_rows.csv",
        [
            {"training_admission_guard_id": "success-1", "guard_family": "success_identity_guard"},
            {"training_admission_guard_id": "stale-1", "guard_family": "stale_fixed_source_guardrail"},
        ],
    )
    design = root / "m2980.md"
    design.write_text("admit_m2981_residual_target_source_feasibility_preflight\n", encoding="utf-8")
    return {"m2977_dir": m2977_dir, "m2970_dir": m2970_dir, "m2980_design": design}


def test_build_target_source_plan_separates_candidates_success_and_stale(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m2981, "EXPECTED_TRAINING_CANDIDATE_COUNT", 2)
    monkeypatch.setattr(m2981, "EXPECTED_SUCCESS_IDENTITY_GUARD_COUNT", 1)
    monkeypatch.setattr(m2981, "EXPECTED_STALE_GUARDRAIL_COUNT", 1)
    monkeypatch.setattr(m2981, "EXPECTED_PLAN_ROW_COUNT", 4)
    paths = _write_source_artifacts(tmp_path)
    source = m2981.load_source_artifacts(
        m2977_dir=paths["m2977_dir"],
        m2970_dir=paths["m2970_dir"],
        m2980_design=paths["m2980_design"],
        follow_up_manifest=tmp_path / "m2982.json",
    )

    plan_rows = m2981.build_target_source_plan_rows(source)

    assert len(plan_rows) == 4
    assert [row["row_role"] for row in plan_rows] == [
        "future_training_candidate",
        "future_training_candidate",
        "success_identity_guard",
        "stale_fixed_source_guardrail",
    ]
    assert sum(row["positive_residual_target"] for row in plan_rows) == 2
    assert plan_rows[2]["success_identity_zero_target_guard"] is True
    assert plan_rows[3]["stale_guardrail_excluded"] is True
    assert not any(row["numeric_target_tensor_materialized"] for row in plan_rows)


def test_run_m2981_writes_feasibility_artifacts_without_numeric_targets(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m2981, "EXPECTED_TRAINING_CANDIDATE_COUNT", 2)
    monkeypatch.setattr(m2981, "EXPECTED_SUCCESS_IDENTITY_GUARD_COUNT", 1)
    monkeypatch.setattr(m2981, "EXPECTED_STALE_GUARDRAIL_COUNT", 1)
    monkeypatch.setattr(m2981, "EXPECTED_PLAN_ROW_COUNT", 4)
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m2981"
    doc_path = tmp_path / "m2981.md"
    follow_up = tmp_path / "m2982.json"

    summary = m2981.run_target_source_feasibility_preflight(
        m2977_dir=paths["m2977_dir"],
        m2970_dir=paths["m2970_dir"],
        m2980_design=paths["m2980_design"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["target_source_plan_row_count"] == 4
    assert summary["target_candidate_row_count"] == 2
    assert summary["success_identity_zero_target_guard_row_count"] == 1
    assert summary["stale_guardrail_exclusion_row_count"] == 1
    assert summary["numeric_target_tensor_materialized_count"] == 0
    assert summary["local_action_search_run"] is False
    assert summary["residual_fitting_run"] is False
    assert summary["training_run"] is False
    assert summary["required_artifacts_present"] is True
    assert follow_up.exists()
    target_rows = _read_csv(output_dir / "target_candidate_rows.csv")
    assert target_rows[0]["target_tensor_shape"] == "5x3"
    assert target_rows[0]["numeric_target_tensor_materialized"] == "False"
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    assert all(row["status_pass"] == "True" for row in claim_rows)
    assert read_json(output_dir / "summary.json")["selected_next_action"] == m2981.NEXT_ID
