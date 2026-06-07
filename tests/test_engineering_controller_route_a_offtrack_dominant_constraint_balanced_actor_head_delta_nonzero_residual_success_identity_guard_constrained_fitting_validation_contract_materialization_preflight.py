from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from autodrift.artifacts import read_json, write_csv_rows, write_json
import autodrift.engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_success_identity_guard_constrained_fitting_validation_contract_materialization_preflight as m2996


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_npz(path: Path, *, obs_dim: int = 72, action_dim: int = 3) -> None:
    np.savez_compressed(
        path,
        linear_weight=np.zeros((obs_dim, action_dim), dtype=np.float32),
        linear_bias=np.zeros((action_dim,), dtype=np.float32),
        residual_limit=np.asarray([0.08], dtype=np.float32),
        guard_weight_multiplier=np.asarray([1000.0], dtype=np.float32),
        success_guard_required_abs_max=np.asarray([0.001], dtype=np.float32),
        observation_dim=np.asarray([obs_dim], dtype=np.int64),
        action_dim=np.asarray([action_dim], dtype=np.int64),
    )


def _write_m2993_fixture(root: Path, *, bad_artifact_shape: bool = False) -> Path:
    m2993_dir = root / "m2993"
    trace_dir = m2993_dir / "traces"
    tensor_dir = m2993_dir / "tensors"
    trace_dir.mkdir(parents=True)
    tensor_dir.mkdir(parents=True)
    write_json(
        m2993_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "required_artifacts_present": True,
        },
    )
    _write_npz(
        m2993_dir / "candidate_residual_head_artifact.npz",
        obs_dim=70 if bad_artifact_shape else 72,
        action_dim=3,
    )

    fitting_rows = []
    for index in range(1, 3):
        raw_trace_path = trace_dir / f"trace-{index}.npz"
        target_path = tensor_dir / f"target-{index}.npz"
        np.savez_compressed(raw_trace_path, observation_trace=np.zeros((4, 72), dtype=np.float32))
        np.savez_compressed(target_path, target_action_delta=np.zeros((4, 3), dtype=np.float32))
        fitting_rows.append(
            {
                "fitting_dataset_row_id": f"m2993-fitting-{index:04d}",
                "target_tensor_row_id": f"target-{index}",
                "mask_weight_binding_id": f"mask-{index}",
                "training_admission_candidate_id": f"candidate-{index}",
                "objective_family": "offtrack_recovery_residual_objective",
                "outcome_bucket": "off_track",
                "raw_trace_path": str(raw_trace_path),
                "target_tensor_path": str(target_path),
                "observation_shape": "4x72",
                "target_action_delta_shape": "4x3",
                "fit_sample_count": 4,
                "target_valid_mask_true_count": 4,
                "target_loss_weight_sum": 4.0,
                "fitting_denominator_used": True,
                "target_quality_validated": False,
                "target_labels_actor_visible": False,
                "target_provenance_actor_visible": False,
                "status_pass": True,
                "claim_boundary": "m2993",
            }
        )
    write_csv_rows(m2993_dir / "fitting_dataset_rows.csv", fitting_rows)
    write_csv_rows(
        m2993_dir / "success_guard_loss_rows.csv",
        [
            {
                "success_guard_loss_id": "m2993-success-guard-loss-0001",
                "success_identity_zero_guard_binding_id": "success-binding-1",
                "success_identity_zero_target_guard_row_id": "success-1",
                "raw_trace_path": str(trace_dir / "trace-1.npz"),
                "target_tensor_path": str(tensor_dir / "target-1.npz"),
                "zero_target_guard": True,
                "fitting_denominator_used": False,
                "target_action_delta_abs_max": 0.0,
                "predicted_residual_abs_max": 0.0001,
                "predicted_residual_mse": 1.0e-8,
                "status_pass": True,
                "claim_boundary": "m2993",
                "guard_penalty_or_constraint_used": True,
                "m2990_predicted_residual_abs_max": 0.08,
                "improved_from_m2990": True,
                "zero_residual_guard_satisfied": True,
            }
        ],
    )
    write_csv_rows(
        m2993_dir / "stale_exclusion_audit_rows.csv",
        [
            {
                "stale_exclusion_audit_id": "m2993-stale-0001",
                "stale_guardrail_exclusion_binding_id": "stale-binding-1",
                "stale_guardrail_exclusion_row_id": "stale-1",
                "guard_family": "stale_fixed_source",
                "fitting_denominator_used": False,
                "validation_denominator_used": False,
                "paper_denominator_used": False,
                "stale_guardrail_excluded": True,
                "status_pass": True,
                "claim_boundary": "m2993",
            }
        ],
    )
    write_csv_rows(
        m2993_dir / "actor_input_exclusion_rows.csv",
        [
            {
                "actor_input_exclusion_id": "m2993-actor-0001",
                "forbidden_metadata_key": "target_action_delta",
                "actor_visible": False,
                "status_pass": True,
                "claim_boundary": "m2993",
            }
        ],
    )
    write_csv_rows(
        m2993_dir / "checkpoint_side_effect_guard_rows.csv",
        [
            {
                "side_effect_guard_id": "m2993-side-0001",
                "side_effect": "environment_reset",
                "scheduled_or_run": False,
                "expected": False,
                "status_pass": True,
                "claim_boundary": "m2993",
            }
        ],
    )
    write_csv_rows(m2993_dir / "claim_boundary_rows.csv", [{"claim_id": "claim", "status_pass": True}])
    write_csv_rows(m2993_dir / "gate_matrix.csv", [{"gate_id": "gate", "status_pass": True}])
    return m2993_dir


def _run_m2996(
    tmp_path: Path,
    m2993_dir: Path,
    *,
    include_m2995_design: bool = True,
) -> dict:
    m2994 = tmp_path / "m2994.md"
    m2995 = tmp_path / "m2995.md"
    m2994.write_text("accept_m2993_artifact_claim_safe_route_to_m2995_validation_admission_design\n", encoding="utf-8")
    if include_m2995_design:
        m2995.write_text(
            "admit_m2996_validation_contract_materialization_preflight_without_validation_or_promotion\n",
            encoding="utf-8",
        )
    else:
        m2995.write_text("design exists but does not admit m2996\n", encoding="utf-8")
    return m2996.run_validation_contract_materialization_preflight(
        m2993_dir=m2993_dir,
        m2994_audit=m2994,
        m2995_design=m2995,
        output_dir=tmp_path / "m2996",
        doc_path=tmp_path / "m2996.md",
        follow_up_manifest=tmp_path / "m2997.json",
    )


def test_m2996_materializes_validation_contracts_without_execution(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m2996, "EXPECTED_VALIDATION_CONTRACT_COUNT", 2)
    monkeypatch.setattr(m2996, "EXPECTED_SUCCESS_RETENTION_COUNT", 1)
    monkeypatch.setattr(m2996, "EXPECTED_STALE_EXCLUSION_COUNT", 1)
    monkeypatch.setattr(m2996, "EXPECTED_ACTOR_EXCLUSION_COUNT", 1)
    monkeypatch.setattr(m2996, "EXPECTED_SIDE_EFFECT_COUNT", 1)
    m2993_dir = _write_m2993_fixture(tmp_path)

    summary = _run_m2996(tmp_path, m2993_dir)

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["validation_contract_row_count"] == 2
    assert summary["success_behavior_retention_guard_row_count"] == 1
    assert summary["stale_exclusion_guard_row_count"] == 1
    assert summary["validation_run"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["checkpoint_mutated"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["selected_next_action"] == m2996.NEXT_ID
    assert read_json(tmp_path / "m2997.json")["id"] == m2996.NEXT_ID

    validation_rows = _read_csv(tmp_path / "m2996" / "validation_contract_rows.csv")
    wrapper_rows = _read_csv(tmp_path / "m2996" / "residual_head_wrapper_contract_rows.csv")
    comparison_rows = _read_csv(tmp_path / "m2996" / "parent_comparison_plan_rows.csv")
    claim_rows = _read_csv(tmp_path / "m2996" / "claim_boundary_rows.csv")
    gate_rows = _read_csv(tmp_path / "m2996" / "gate_matrix.csv")

    assert {row["validation_run"] for row in validation_rows} == {"False"}
    assert {row["ranking_run"] for row in validation_rows} == {"False"}
    assert {row["status_pass"] for row in wrapper_rows} == {"True"}
    assert {row["ranking_planned"] for row in comparison_rows} == {"False"}
    assert {row["winner_selection_planned"] for row in comparison_rows} == {"False"}
    assert all(row["claim_made"] == "False" for row in claim_rows if row["allowed_in_m2996"] == "False")
    assert {row["status_pass"] for row in gate_rows} == {"True"}


def test_m2996_fails_closed_without_m2995_admission(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m2996, "EXPECTED_VALIDATION_CONTRACT_COUNT", 2)
    monkeypatch.setattr(m2996, "EXPECTED_SUCCESS_RETENTION_COUNT", 1)
    monkeypatch.setattr(m2996, "EXPECTED_STALE_EXCLUSION_COUNT", 1)
    monkeypatch.setattr(m2996, "EXPECTED_ACTOR_EXCLUSION_COUNT", 1)
    monkeypatch.setattr(m2996, "EXPECTED_SIDE_EFFECT_COUNT", 1)
    m2993_dir = _write_m2993_fixture(tmp_path)

    summary = _run_m2996(tmp_path, m2993_dir, include_m2995_design=False)

    assert summary["status_pass"] is False
    assert summary["gate_matrix_pass"] is False
    assert summary["validation_run"] is False
    assert summary["checkpoint_mutated"] is False
    gates = _read_csv(tmp_path / "m2996" / "gate_matrix.csv")
    assert next(row for row in gates if row["gate_id"].endswith("m2995_admits_m2996"))["status_pass"] == "False"
    assert next(row for row in gates if row["gate_id"].endswith("source_preconditions_pass"))["status_pass"] == "False"


def test_m2996_fails_closed_with_bad_residual_head_shape(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m2996, "EXPECTED_VALIDATION_CONTRACT_COUNT", 2)
    monkeypatch.setattr(m2996, "EXPECTED_SUCCESS_RETENTION_COUNT", 1)
    monkeypatch.setattr(m2996, "EXPECTED_STALE_EXCLUSION_COUNT", 1)
    monkeypatch.setattr(m2996, "EXPECTED_ACTOR_EXCLUSION_COUNT", 1)
    monkeypatch.setattr(m2996, "EXPECTED_SIDE_EFFECT_COUNT", 1)
    m2993_dir = _write_m2993_fixture(tmp_path, bad_artifact_shape=True)

    summary = _run_m2996(tmp_path, m2993_dir)

    assert summary["status_pass"] is False
    assert summary["artifact_metadata"]["linear_weight_shape"] == "70x3"
    gates = _read_csv(tmp_path / "m2996" / "gate_matrix.csv")
    assert next(row for row in gates if row["gate_id"].endswith("artifact_metadata_pass"))["status_pass"] == "False"
