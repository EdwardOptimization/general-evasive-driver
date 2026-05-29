from __future__ import annotations

from pathlib import Path

import torch

from autodrift.contour_aware_exact_objective_sensitivity_probe import (
    run_contour_aware_exact_objective_sensitivity_probe,
)


class TinyActor(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.actor_mean = torch.nn.Linear(2, 3)


def _loader(checkpoint: Path, device: str):
    del checkpoint, device
    return TinyActor()


def test_sensitivity_probe_detects_controlled_perturbation(tmp_path: Path) -> None:
    checkpoint = tmp_path / "checkpoint.pt"
    checkpoint.write_bytes(b"stable checkpoint bytes")

    def evaluator(candidate_id, scale, model, candidate_run_dir):
        del candidate_id, model
        candidate_run_dir.mkdir(parents=True)
        return {
            "positive_exact_residual_mean": float(scale) ** 2,
            "positive_policy_action_residual_l2_max": abs(float(scale)) * 10.0,
            "diagnostic_exact_residual_mean": float(scale) ** 2,
            "diagnostic_policy_action_residual_l2_max": abs(float(scale)) * 10.0,
            "passes_public_smoke_gates": scale == 0.0,
            "null_result_classification": "base" if scale == 0.0 else "perturbed",
            "checkpoint_weights_mutated": False,
            "donor_plus_action_used_as_loss_target": False,
            "diagnostic_rows_used_as_positive": False,
        }

    summary = run_contour_aware_exact_objective_sensitivity_probe(
        materialization_run_dir=tmp_path / "materialization",
        checkpoint=checkpoint,
        run_dir=tmp_path / "run",
        scales=(0.0, 1e-4, 1e-3),
        load_model_fn=_loader,
        evaluate_candidate_fn=evaluator,
    )

    assert summary["passes_public_smoke_gates"] is True
    assert summary["base_residual_near_zero"] is True
    assert summary["measurable_perturbation_residual"] is True
    assert summary["perturbed_checkpoint_written"] is False
    assert summary["actor_update_run"] is False


def test_sensitivity_probe_reports_null_perturbation(tmp_path: Path) -> None:
    checkpoint = tmp_path / "checkpoint.pt"
    checkpoint.write_bytes(b"stable checkpoint bytes")

    def evaluator(candidate_id, scale, model, candidate_run_dir):
        del candidate_id, scale, model
        candidate_run_dir.mkdir(parents=True)
        return {
            "positive_exact_residual_mean": 0.0,
            "positive_policy_action_residual_l2_max": 0.0,
            "diagnostic_exact_residual_mean": 0.0,
            "diagnostic_policy_action_residual_l2_max": 0.0,
            "passes_public_smoke_gates": True,
            "null_result_classification": "base",
            "checkpoint_weights_mutated": False,
            "donor_plus_action_used_as_loss_target": False,
            "diagnostic_rows_used_as_positive": False,
        }

    summary = run_contour_aware_exact_objective_sensitivity_probe(
        materialization_run_dir=tmp_path / "materialization",
        checkpoint=checkpoint,
        run_dir=tmp_path / "run",
        scales=(0.0, 1e-4, 1e-3),
        load_model_fn=_loader,
        evaluate_candidate_fn=evaluator,
    )

    assert summary["passes_public_smoke_gates"] is False
    assert summary["null_result_classification"] == "controlled_perturbation_residual_null"
    assert summary["base_residual_near_zero"] is True
    assert summary["measurable_perturbation_residual"] is False
