from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from autodrift.artifacts import read_json, write_csv_rows, write_json
import autodrift.engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_bounded_fitting_preflight as m2990
import autodrift.engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_success_identity_guard_constrained_fitting_preflight as m2993


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_trace(path: Path, *, steps: int, scale: float, vary_x: bool = True) -> np.ndarray:
    obs = np.zeros((steps, 72), dtype=np.float32)
    if vary_x:
        obs[:, 0] = np.linspace(-1.0, 1.0, steps, dtype=np.float32)
        obs[:, 2] = np.linspace(0.0, 0.5, steps, dtype=np.float32)
    obs[:, 1] = scale
    np.savez_compressed(
        path,
        observation_trace=obs,
        action_trace=np.zeros((steps, 3), dtype=np.float32),
        next_observation_trace=obs,
        reward_trace=np.zeros((steps,), dtype=np.float32),
        done_trace=np.zeros((steps,), dtype=bool),
        timeout_trace=np.zeros((steps,), dtype=bool),
    )
    return obs


def _write_target(path: Path, obs: np.ndarray, *, zero: bool = False) -> None:
    if zero:
        delta = np.zeros((obs.shape[0], 3), dtype=np.float32)
        mask = np.zeros((obs.shape[0],), dtype=bool)
        weight = np.zeros((obs.shape[0],), dtype=np.float32)
    else:
        delta = np.zeros((obs.shape[0], 3), dtype=np.float32)
        delta[:, 0] = 0.02 * obs[:, 1] + 0.01 * obs[:, 0]
        delta[:, 1] = -0.005 * obs[:, 1]
        delta[:, 2] = 0.002 * obs[:, 2]
        mask = np.ones((obs.shape[0],), dtype=bool)
        weight = np.ones((obs.shape[0],), dtype=np.float32)
    base = np.zeros((obs.shape[0], 3), dtype=np.float32)
    np.savez_compressed(
        path,
        base_action=base,
        target_action=np.clip(base + delta, -1.0, 1.0).astype(np.float32),
        target_action_delta=delta,
        target_valid_mask=mask,
        target_loss_weight=weight,
    )


def _write_source_artifacts(root: Path, *, include_m2992_synthesis: bool = True) -> dict[str, Path]:
    m2983_dir = root / "m2983"
    m2987_dir = root / "m2987"
    m2990_dir = root / "m2990"
    tensor_dir = m2983_dir / "target_tensors"
    raw_dir = m2983_dir / "raw_traces"
    tensor_dir.mkdir(parents=True)
    raw_dir.mkdir(parents=True)
    m2987_dir.mkdir()
    m2990_dir.mkdir()

    target_rows = []
    mask_rows = []
    for index, steps in enumerate((5, 4), start=1):
        raw_path = raw_dir / f"trace-{index}.npz"
        target_path = tensor_dir / f"target-{index}.npz"
        obs = _write_trace(raw_path, steps=steps, scale=float(index))
        _write_target(target_path, obs)
        target_id = f"target-{index}"
        target_rows.append(
            {
                "target_tensor_row_id": target_id,
                "training_admission_candidate_id": f"candidate-{index}",
                "objective_family": "offtrack_recovery_residual_objective",
                "outcome_bucket": "off_track",
                "raw_trace_path": str(raw_path),
                "target_tensor_path": str(target_path),
                "target_quality_validated": False,
                "target_labels_actor_visible": False,
                "target_provenance_actor_visible": False,
            }
        )
        mask_rows.append(
            {
                "mask_weight_binding_id": f"mask-{index}",
                "target_tensor_row_id": target_id,
                "training_admission_candidate_id": f"candidate-{index}",
                "objective_family": "offtrack_recovery_residual_objective",
                "outcome_bucket": "off_track",
                "target_tensor_path": str(target_path),
                "target_valid_mask_true_count": steps,
                "target_loss_weight_sum": float(steps),
                "target_action_delta_abs_max": 0.04,
                "target_quality_validated": False,
                "target_labels_actor_visible": False,
                "target_provenance_actor_visible": False,
                "fit_candidate_after_audit": True,
                "status_pass": True,
            }
        )

    success_raw = raw_dir / "success-trace.npz"
    success_target = tensor_dir / "success-target.npz"
    success_obs = _write_trace(success_raw, steps=3, scale=0.0, vary_x=False)
    _write_target(success_target, success_obs, zero=True)
    success_rows = [
        {
            "success_identity_zero_target_guard_row_id": "success-1",
            "raw_trace_path": str(success_raw),
            "target_tensor_path": str(success_target),
            "zero_target_guard": True,
            "positive_residual_target": False,
        }
    ]
    success_binding_rows = [
        {
            "success_identity_zero_guard_binding_id": "success-binding-1",
            "success_identity_zero_target_guard_row_id": "success-1",
            "target_tensor_path": str(success_target),
            "zero_target_guard": True,
            "positive_residual_target": False,
            "future_fitting_denominator_allowed_after_audit": False,
            "guard_denominator_allowed": True,
            "target_action_delta_abs_max": 0.0,
            "status_pass": True,
        }
    ]
    stale_rows = [
        {
            "stale_guardrail_exclusion_binding_id": "stale-binding-1",
            "stale_guardrail_exclusion_row_id": "stale-1",
            "guard_family": "stale_fixed_source",
            "future_fitting_denominator_allowed_after_audit": False,
            "validation_denominator_allowed": False,
            "paper_denominator_allowed": False,
            "stale_guardrail_excluded": True,
            "status_pass": True,
        }
    ]

    write_csv_rows(m2983_dir / "target_tensor_rows.csv", target_rows)
    write_csv_rows(m2983_dir / "success_identity_zero_target_guard_rows.csv", success_rows)
    write_csv_rows(m2983_dir / "stale_guardrail_exclusion_rows.csv", [{"stale_guardrail_exclusion_row_id": "stale-1"}])
    write_json(m2987_dir / "summary.json", {"status_pass": True, "gate_matrix_pass": True})
    write_csv_rows(m2987_dir / "mask_weight_binding_rows.csv", mask_rows)
    write_csv_rows(m2987_dir / "success_identity_zero_guard_binding_rows.csv", success_binding_rows)
    write_csv_rows(m2987_dir / "stale_guardrail_exclusion_binding_rows.csv", stale_rows)
    write_csv_rows(m2987_dir / "gate_matrix.csv", [{"gate_id": "gate-1", "status_pass": True}])
    write_json(m2990_dir / "summary.json", {"success_guard_predicted_residual_abs_max": 0.08})

    audit = root / "m2988.md"
    audit.write_text(
        "accept_m2987_fitting_contract_materialization_claim_safe_route_to_m2989_fitting_admission_design\n",
        encoding="utf-8",
    )
    design = root / "m2989.md"
    design.write_text(
        "admit_m2990_bounded_residual_fitting_preflight_without_validation_or_promotion\n",
        encoding="utf-8",
    )
    m2991_audit = root / "m2991.md"
    m2991_audit.write_text(
        "accept_m2990_artifact_claim_safe_reject_direct_validation_route_to_m2992_success_identity_guard_repair_branch_synthesis\n",
        encoding="utf-8",
    )
    m2992_synthesis = root / "m2992.md"
    if include_m2992_synthesis:
        m2992_synthesis.write_text(
            "continue_to_m2993_success_identity_guard_constrained_fitting_preflight\n",
            encoding="utf-8",
        )
    return {
        "m2983_dir": m2983_dir,
        "m2987_dir": m2987_dir,
        "m2990_dir": m2990_dir,
        "m2988_audit": audit,
        "m2989_design": design,
        "m2991_audit": m2991_audit,
        "m2992_synthesis": m2992_synthesis,
    }


def _run_m2993(tmp_path: Path, paths: dict[str, Path]) -> dict:
    return m2993.run_success_identity_guard_constrained_fitting_preflight(
        m2987_dir=paths["m2987_dir"],
        m2988_audit=paths["m2988_audit"],
        m2989_design=paths["m2989_design"],
        m2991_audit=paths["m2991_audit"],
        m2992_synthesis=paths["m2992_synthesis"],
        m2983_dir=paths["m2983_dir"],
        m2990_dir=paths["m2990_dir"],
        output_dir=tmp_path / "m2993",
        doc_path=tmp_path / "m2993.md",
        follow_up_manifest=tmp_path / "m2994.json",
    )


def test_run_m2993_writes_guard_constrained_artifacts_and_followup(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m2990, "EXPECTED_CANDIDATE_COUNT", 2)
    monkeypatch.setattr(m2993, "EXPECTED_CANDIDATE_COUNT", 2)
    monkeypatch.setattr(m2993, "EXPECTED_SUCCESS_GUARD_COUNT", 1)
    monkeypatch.setattr(m2993, "EXPECTED_STALE_EXCLUSION_COUNT", 1)
    paths = _write_source_artifacts(tmp_path)

    summary = _run_m2993(tmp_path, paths)

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["guard_constrained_offline_fitting_run"] is True
    assert summary["validation_run"] is False
    assert summary["ranking_run"] is False
    assert summary["checkpoint_mutated"] is False
    assert summary["success_guard_predicted_residual_abs_max"] <= m2993.SUCCESS_GUARD_REQUIRED_ABS_MAX
    assert summary["success_guard_improved_from_m2990"] is True
    assert summary["final_candidate_weighted_mse"] <= summary["initial_candidate_weighted_mse"]
    assert Path(summary["candidate_residual_head_artifact"]).exists()
    assert (tmp_path / "m2994.json").exists()
    assert read_json(tmp_path / "m2993" / "summary.json")["selected_next_action"] == m2993.NEXT_ID

    loss_rows = _read_csv(tmp_path / "m2993" / "guard_constrained_loss_trace_rows.csv")
    assert loss_rows[-1]["status_pass"] == "True"
    dataset_rows = _read_csv(tmp_path / "m2993" / "fitting_dataset_rows.csv")
    assert dataset_rows[0]["fitting_dataset_row_id"].startswith("m2993-")
    assert "M2993 Route A" in dataset_rows[0]["claim_boundary"]
    with np.load(Path(summary["candidate_residual_head_artifact"]), allow_pickle=False) as artifact:
        assert np.isclose(float(artifact["guard_weight_multiplier"][0]), m2993.GUARD_WEIGHT_MULTIPLIER)


def test_run_m2993_fails_closed_when_m2992_synthesis_is_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m2990, "EXPECTED_CANDIDATE_COUNT", 2)
    monkeypatch.setattr(m2993, "EXPECTED_CANDIDATE_COUNT", 2)
    monkeypatch.setattr(m2993, "EXPECTED_SUCCESS_GUARD_COUNT", 1)
    monkeypatch.setattr(m2993, "EXPECTED_STALE_EXCLUSION_COUNT", 1)
    paths = _write_source_artifacts(tmp_path, include_m2992_synthesis=False)

    summary = _run_m2993(tmp_path, paths)

    assert summary["status_pass"] is False
    assert summary["guard_constrained_offline_fitting_run"] is False
    assert not Path(summary["candidate_residual_head_artifact"]).exists()
    loss_rows = _read_csv(tmp_path / "m2993" / "guard_constrained_loss_trace_rows.csv")
    assert loss_rows[-1]["status_pass"] == "False"
    gates = _read_csv(tmp_path / "m2993" / "gate_matrix.csv")
    source_gate = next(row for row in gates if row["gate_id"].endswith("source_artifacts_present"))
    assert source_gate["status_pass"] == "False"
