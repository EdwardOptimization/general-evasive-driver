from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from autodrift.artifacts import read_json, write_csv_rows, write_json
import autodrift.engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_target_tensor_materialization_preflight as m2983


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_trace(path: Path, *, steps: int, lateral: float = 0.2) -> None:
    observation = np.zeros((steps, 72), dtype=np.float32)
    observation[:, 1] = lateral
    action = np.zeros((steps, 3), dtype=np.float32)
    next_observation = observation.copy()
    reward = np.ones((steps,), dtype=np.float32)
    done = np.zeros((steps,), dtype=bool)
    timeout = np.zeros((steps,), dtype=bool)
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
    m2981_dir = root / "m2981"
    m2977_dir = root / "m2977"
    m2981_dir.mkdir()
    m2977_dir.mkdir()
    trace_dir = root / "raw_traces"
    trace_dir.mkdir()
    candidate_1 = trace_dir / "candidate-1.npz"
    candidate_2 = trace_dir / "candidate-2.npz"
    success_1 = trace_dir / "success-1.npz"
    _write_trace(candidate_1, steps=5, lateral=0.3)
    _write_trace(candidate_2, steps=4, lateral=-0.1)
    _write_trace(success_1, steps=3, lateral=0.0)
    write_json(m2981_dir / "summary.json", {"status_pass": True, "gate_matrix_pass": True})
    write_csv_rows(m2981_dir / "target_source_plan_rows.csv", [{"row_role": "future_training_candidate"}])
    write_csv_rows(
        m2981_dir / "target_candidate_rows.csv",
        [
            {
                "target_candidate_row_id": "m2981-target-candidate-0001",
                "training_admission_candidate_id": "candidate-1",
                "source_raw_trace_index_row_id": "raw-1",
                "execution_candidate_id": "exec-1",
                "objective_family": "offtrack_recovery_residual_objective",
                "outcome_bucket": "off_track",
                "raw_trace_path": str(candidate_1),
            },
            {
                "target_candidate_row_id": "m2981-target-candidate-0002",
                "training_admission_candidate_id": "candidate-2",
                "source_raw_trace_index_row_id": "raw-2",
                "execution_candidate_id": "exec-2",
                "objective_family": "speed_floor_context_guard_objective",
                "outcome_bucket": "speed_too_low",
                "raw_trace_path": str(candidate_2),
            },
        ],
    )
    write_csv_rows(
        m2981_dir / "success_identity_zero_target_guard_rows.csv",
        [
            {
                "success_identity_zero_target_guard_row_id": "m2981-success-zero-guard-0001",
                "source_row_id": "success-1",
                "source_raw_trace_index_row_id": "raw-3",
                "execution_candidate_id": "exec-3",
                "raw_trace_path": str(success_1),
            }
        ],
    )
    write_csv_rows(
        m2981_dir / "stale_guardrail_exclusion_rows.csv",
        [
            {
                "stale_guardrail_exclusion_row_id": "m2981-stale-exclusion-0001",
                "source_row_id": "stale-1",
                "source_raw_trace_guard_row_id": "guard-stale-1",
                "guard_family": "actor_head_delta_execution_admission_blocked_stale_fixed_surface",
            }
        ],
    )
    write_csv_rows(m2981_dir / "gate_matrix.csv", [{"gate_id": "gate-1", "status_pass": True}])
    write_csv_rows(m2977_dir / "raw_trace_index_rows.csv", [{"raw_trace_index_row_id": "raw-1"}])
    audit = root / "m2982.md"
    audit.write_text(
        "accept_m2981_target_source_feasibility_claim_safe_route_to_m2983_target_tensor_materialization_preflight\n",
        encoding="utf-8",
    )
    return {"m2981_dir": m2981_dir, "m2977_dir": m2977_dir, "audit": audit}


def test_materialize_candidate_target_writes_bounded_tensor(tmp_path: Path) -> None:
    paths = _write_source_artifacts(tmp_path)
    candidate = _read_csv(paths["m2981_dir"] / "target_candidate_rows.csv")[0]

    row = m2983.materialize_candidate_target(candidate_row=candidate, target_dir=tmp_path / "targets", index=1)

    assert row["target_action_delta_shape"] == "5x3"
    assert row["target_valid_mask_true_count"] == 5
    assert row["target_labels_actor_visible"] is False
    assert row["target_provenance_actor_visible"] is False
    assert row["target_action_delta_abs_max"] <= m2983.TARGET_DELTA_ABS_LIMIT
    tensor = np.load(row["target_tensor_path"])
    assert tensor["target_action_delta"].shape == (5, 3)
    assert np.all(np.isfinite(tensor["target_action_delta"]))
    assert np.all(tensor["target_valid_mask"])


def test_run_m2983_materializes_targets_guards_and_followup(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m2983, "EXPECTED_TRAINING_CANDIDATE_COUNT", 2)
    monkeypatch.setattr(m2983, "EXPECTED_TARGET_TENSOR_ROW_COUNT", 2)
    monkeypatch.setattr(m2983, "EXPECTED_SUCCESS_IDENTITY_GUARD_COUNT", 1)
    monkeypatch.setattr(m2983, "EXPECTED_STALE_GUARDRAIL_COUNT", 1)
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m2983"
    follow_up = tmp_path / "m2984.json"

    summary = m2983.run_target_tensor_materialization_preflight(
        m2981_dir=paths["m2981_dir"],
        m2982_audit=paths["audit"],
        m2977_dir=paths["m2977_dir"],
        output_dir=output_dir,
        doc_path=tmp_path / "m2983.md",
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["target_tensor_row_count"] == 2
    assert summary["success_identity_zero_target_guard_row_count"] == 1
    assert summary["stale_guardrail_exclusion_row_count"] == 1
    assert summary["numeric_target_tensor_materialized_count"] == 2
    assert summary["success_identity_positive_target_count"] == 0
    assert summary["stale_guardrail_target_materialized_count"] == 0
    assert summary["residual_fitting_run"] is False
    assert summary["training_run"] is False
    assert summary["validation_run"] is False
    assert summary["required_artifacts_present"] is True
    assert follow_up.exists()
    target_rows = _read_csv(output_dir / "target_tensor_rows.csv")
    assert len(target_rows) == 2
    success_rows = _read_csv(output_dir / "success_identity_zero_target_guard_rows.csv")
    zero_tensor = np.load(success_rows[0]["target_tensor_path"])
    assert not np.any(zero_tensor["target_valid_mask"])
    assert np.max(np.abs(zero_tensor["target_action_delta"])) == 0.0
    assert read_json(output_dir / "summary.json")["selected_next_action"] == m2983.NEXT_ID
