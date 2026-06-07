from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from autodrift.artifacts import read_json, write_csv_rows, write_json
import autodrift.engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_fitting_contract_materialization_preflight as m2987


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_target_tensor(path: Path, *, steps: int, zero: bool = False) -> None:
    base = np.zeros((steps, 3), dtype=np.float32)
    delta = np.zeros((steps, 3), dtype=np.float32) if zero else np.full((steps, 3), 0.01, dtype=np.float32)
    mask = np.zeros((steps,), dtype=bool) if zero else np.ones((steps,), dtype=bool)
    weight = np.zeros((steps,), dtype=np.float32) if zero else np.ones((steps,), dtype=np.float32)
    np.savez_compressed(
        path,
        base_action=base,
        target_action=np.clip(base + delta, -1.0, 1.0).astype(np.float32),
        target_action_delta=delta,
        target_valid_mask=mask,
        target_loss_weight=weight,
    )


def _write_source_artifacts(root: Path, *, actor_visible_target_label: bool = False) -> dict[str, Path]:
    m2983_dir = root / "m2983"
    m2983_dir.mkdir()
    tensor_dir = m2983_dir / "target_tensors"
    tensor_dir.mkdir()
    target_1 = tensor_dir / "target-1.npz"
    target_2 = tensor_dir / "target-2.npz"
    success_1 = tensor_dir / "success-1.npz"
    _write_target_tensor(target_1, steps=5)
    _write_target_tensor(target_2, steps=4)
    _write_target_tensor(success_1, steps=3, zero=True)
    write_json(
        m2983_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "candidate_target_tensor_materialized_count": 2,
            "success_identity_zero_target_guard_row_count": 1,
            "stale_guardrail_exclusion_row_count": 1,
            "target_quality_validated": False,
        },
    )
    write_csv_rows(
        m2983_dir / "target_tensor_rows.csv",
        [
            {
                "target_tensor_row_id": "m2983-target-tensor-0001",
                "training_admission_candidate_id": "candidate-1",
                "objective_family": "offtrack_recovery_residual_objective",
                "outcome_bucket": "off_track",
                "target_tensor_path": str(target_1),
                "target_action_delta_shape": "5x3",
                "target_valid_mask_shape": "5",
                "target_loss_weight_shape": "5",
                "target_quality_validated": False,
                "target_labels_actor_visible": actor_visible_target_label,
                "target_provenance_actor_visible": False,
                "positive_residual_target": True,
                "residual_fitting_run": False,
                "training_run": False,
                "validation_run": False,
                "ranking_run": False,
                "checkpoint_mutated": False,
            },
            {
                "target_tensor_row_id": "m2983-target-tensor-0002",
                "training_admission_candidate_id": "candidate-2",
                "objective_family": "speed_floor_context_guard_objective",
                "outcome_bucket": "speed_too_low",
                "target_tensor_path": str(target_2),
                "target_action_delta_shape": "4x3",
                "target_valid_mask_shape": "4",
                "target_loss_weight_shape": "4",
                "target_quality_validated": False,
                "target_labels_actor_visible": False,
                "target_provenance_actor_visible": False,
                "positive_residual_target": True,
                "residual_fitting_run": False,
                "training_run": False,
                "validation_run": False,
                "ranking_run": False,
                "checkpoint_mutated": False,
            },
        ],
    )
    write_csv_rows(
        m2983_dir / "success_identity_zero_target_guard_rows.csv",
        [
            {
                "success_identity_zero_target_guard_row_id": "m2983-success-zero-guard-0001",
                "source_row_id": "success-1",
                "target_tensor_path": str(success_1),
                "zero_target_guard": True,
                "positive_residual_target": False,
            }
        ],
    )
    write_csv_rows(
        m2983_dir / "stale_guardrail_exclusion_rows.csv",
        [
            {
                "stale_guardrail_exclusion_row_id": "m2983-stale-exclusion-0001",
                "source_row_id": "stale-1",
                "guard_family": "actor_head_delta_execution_admission_blocked_stale_fixed_surface",
                "target_materialized": False,
                "positive_residual_target": False,
                "training_denominator_allowed": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "stale_guardrail_excluded": True,
            }
        ],
    )
    write_csv_rows(m2983_dir / "gate_matrix.csv", [{"gate_id": f"gate-{index}", "status_pass": True} for index in range(14)])
    audit = root / "m2984.md"
    audit.write_text(
        "accept_m2983_target_tensor_materialization_claim_safe_route_to_m2985_fitting_admission_design\n",
        encoding="utf-8",
    )
    design = root / "m2985.md"
    design.write_text(
        "route_to_m2986_fitting_contract_branch_synthesis_before_m2987_contract_materialization\n",
        encoding="utf-8",
    )
    synthesis = root / "m2986.md"
    synthesis.write_text("continue_to_m2987_fitting_contract_materialization_preflight\n", encoding="utf-8")
    return {"m2983_dir": m2983_dir, "audit": audit, "design": design, "synthesis": synthesis}


def test_run_m2987_materializes_contract_rows_and_followup(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m2987, "EXPECTED_TARGET_ROW_COUNT", 2)
    monkeypatch.setattr(m2987, "EXPECTED_SUCCESS_ZERO_GUARD_COUNT", 1)
    monkeypatch.setattr(m2987, "EXPECTED_STALE_EXCLUSION_COUNT", 1)
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m2987"
    follow_up = tmp_path / "m2988.json"

    summary = m2987.run_fitting_contract_materialization_preflight(
        m2983_dir=paths["m2983_dir"],
        m2984_audit=paths["audit"],
        m2985_design=paths["design"],
        m2986_synthesis=paths["synthesis"],
        output_dir=output_dir,
        doc_path=tmp_path / "m2987.md",
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["mask_weight_binding_row_count"] == 2
    assert summary["success_identity_zero_guard_binding_row_count"] == 1
    assert summary["stale_guardrail_exclusion_binding_row_count"] == 1
    assert summary["target_quality_validated"] is False
    assert summary["residual_fitting_run"] is False
    assert summary["training_run"] is False
    assert follow_up.exists()
    split_rows = _read_csv(output_dir / "split_denominator_rows.csv")
    assert split_rows[0]["future_fitting_denominator_allowed_after_audit"] == "True"
    assert split_rows[1]["guard_denominator_allowed"] == "True"
    assert split_rows[2]["future_fitting_denominator_allowed_after_audit"] == "False"
    stale_rows = _read_csv(output_dir / "stale_guardrail_exclusion_binding_rows.csv")
    assert stale_rows[0]["stale_guardrail_excluded"] == "True"
    assert read_json(output_dir / "summary.json")["selected_next_action"] == m2987.NEXT_ID


def test_run_m2987_fails_closed_when_target_label_is_actor_visible(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m2987, "EXPECTED_TARGET_ROW_COUNT", 2)
    monkeypatch.setattr(m2987, "EXPECTED_SUCCESS_ZERO_GUARD_COUNT", 1)
    monkeypatch.setattr(m2987, "EXPECTED_STALE_EXCLUSION_COUNT", 1)
    paths = _write_source_artifacts(tmp_path, actor_visible_target_label=True)

    summary = m2987.run_fitting_contract_materialization_preflight(
        m2983_dir=paths["m2983_dir"],
        m2984_audit=paths["audit"],
        m2985_design=paths["design"],
        m2986_synthesis=paths["synthesis"],
        output_dir=tmp_path / "m2987",
        doc_path=tmp_path / "m2987.md",
        follow_up_manifest=tmp_path / "m2988.json",
    )

    assert summary["status_pass"] is False
    mask_rows = _read_csv(tmp_path / "m2987" / "mask_weight_binding_rows.csv")
    assert mask_rows[0]["status_pass"] == "False"
