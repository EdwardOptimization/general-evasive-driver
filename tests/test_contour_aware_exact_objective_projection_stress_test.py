from __future__ import annotations

from pathlib import Path

from autodrift.contour_aware_exact_objective_projection_stress_test import (
    run_contour_aware_exact_objective_projection_stress_test,
)


def _fake_summary(*, scale: float, seed: int, pass_candidate: bool = True) -> dict[str, object]:
    initial = abs(float(scale)) * (1.0 + 0.001 * int(seed))
    ratio = 0.75 if pass_candidate else 0.1
    repaired = initial * (1.0 - ratio)
    return {
        "initial_positive_exact_residual_mean": initial,
        "repaired_positive_exact_residual_mean": repaired,
        "positive_exact_residual_reduction_ratio": ratio,
        "initial_positive_action_l2_max": initial * 10.0,
        "repaired_positive_action_l2_max": repaired * 10.0,
        "initial_actor_mean_l2_to_base": 0.1,
        "repaired_actor_mean_l2_to_base": 0.09,
        "accepted_backtracking_step_count": 1 if pass_candidate else 0,
        "backtracking_candidate_count": 2,
        "projection_stop_reason": "target_reduction_reached" if pass_candidate else "no_backtracking_candidate_accepted",
        "passes_public_smoke_gates": pass_candidate,
        "null_result_classification": "contour_aware_exact_objective_projection_repair_public_pass"
        if pass_candidate
        else "reduction_ratio_below_threshold",
        "guardrail_violation_count": 0,
        "repaired_checkpoint_written": False,
        "base_interpolation_used_for_repair": False,
        "diagnostic_rows_used_as_positive": False,
        "donor_plus_action_used_as_loss_target": False,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "level3_self_id_claim_made": False,
    }


def test_projection_stress_test_aggregates_public_pass(tmp_path: Path) -> None:
    def repair_fn(**kwargs):
        run_dir = Path(kwargs["run_dir"])
        run_dir.mkdir(parents=True)
        return _fake_summary(scale=float(kwargs["perturb_scale"]), seed=int(kwargs["perturb_seed"]))

    summary = run_contour_aware_exact_objective_projection_stress_test(
        materialization_run_dir=tmp_path / "materialization",
        checkpoint=tmp_path / "checkpoint.pt",
        run_dir=tmp_path / "run",
        scales=(1e-4, 3e-4, 1e-3),
        seeds=(1645, 1646, 1647),
        repair_fn=repair_fn,
    )

    assert summary["passes_public_smoke_gates"] is True
    assert summary["stress_candidate_count"] == 9
    assert summary["measurable_initial_residual_count"] == 9
    assert summary["residual_reduced_count"] == 9
    assert summary["candidate_public_pass_count"] == 9
    assert summary["accepted_backtracking_candidate_count"] == 9
    assert summary["checkpoint_artifact_count"] == 0
    assert summary["null_result_classification"] == "damped_projection_stress_public_pass"
    assert (tmp_path / "run" / "candidate_summary.csv").exists()
    assert (tmp_path / "run" / "aggregate_summary.csv").exists()
    assert (tmp_path / "run" / "guardrail_summary.csv").exists()


def test_projection_stress_test_reports_threshold_failure(tmp_path: Path) -> None:
    def repair_fn(**kwargs):
        run_dir = Path(kwargs["run_dir"])
        run_dir.mkdir(parents=True)
        fail = int(kwargs["perturb_seed"]) == 1647 and float(kwargs["perturb_scale"]) == 1e-3
        return _fake_summary(scale=float(kwargs["perturb_scale"]), seed=int(kwargs["perturb_seed"]), pass_candidate=not fail)

    summary = run_contour_aware_exact_objective_projection_stress_test(
        materialization_run_dir=tmp_path / "materialization",
        checkpoint=tmp_path / "checkpoint.pt",
        run_dir=tmp_path / "run",
        scales=(1e-4, 3e-4, 1e-3),
        seeds=(1645, 1646, 1647),
        repair_fn=repair_fn,
    )

    assert summary["passes_public_smoke_gates"] is False
    assert summary["candidate_public_pass_count"] == 8
    assert summary["residual_reduced_count"] == 9
    assert summary["accepted_backtracking_candidate_count"] == 8
    assert summary["min_positive_exact_residual_reduction_ratio"] < 0.25
    assert summary["null_result_classification"] == "reduction_ratio_below_threshold"
