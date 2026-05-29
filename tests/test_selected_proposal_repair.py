from __future__ import annotations

from pathlib import Path

from autodrift.selected_proposal_repair import run_selected_proposal_repair


def _write_candidate_summary(path: Path) -> None:
    rows = [
        "candidate_id,alpha,checkpoint,selected_repair_candidate",
        f"alpha02,0.2,{path.parent / 'alpha02.pt'},True",
        f"alpha04,0.4,{path.parent / 'alpha04.pt'},True",
        f"alpha10,1.0,{path.parent / 'alpha10.pt'},True",
    ]
    for filename in ("alpha02.pt", "alpha04.pt", "alpha10.pt"):
        (path.parent / filename).write_text("checkpoint", encoding="utf-8")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def _fake_repair_summary(*, alpha: float, pass_candidate: bool) -> dict[str, object]:
    initial = 0.01 * float(alpha)
    ratio = 0.5 if pass_candidate else 0.0
    repaired = initial * (1.0 - ratio)
    return {
        "candidate_id": f"alpha{alpha}",
        "proposal_source_type": "same_line_interpolation",
        "alpha": float(alpha),
        "proposal_checkpoint": f"alpha{alpha}.pt",
        "initial_positive_exact_residual_mean": initial,
        "repaired_positive_exact_residual_mean": repaired,
        "positive_exact_residual_reduction": initial - repaired,
        "positive_exact_residual_reduction_ratio": ratio,
        "initial_positive_action_l2_max": initial * 10.0,
        "repaired_positive_action_l2_max": repaired * 10.0,
        "proposal_actor_mean_l2_to_base": alpha,
        "repaired_actor_mean_l2_to_base": alpha * 0.9,
        "repaired_actor_mean_l2_to_proposal": alpha * 0.1,
        "non_actor_mean_delta_to_proposal_max": 0.0,
        "accepted_backtracking_step_count": 1 if pass_candidate else 0,
        "projection_stop_reason": "target_reduction_reached" if pass_candidate else "no_backtracking_candidate_accepted",
        "passes_candidate_gate": pass_candidate,
        "null_result_classification": "selected_proposal_candidate_repair_public_pass"
        if pass_candidate
        else "residual_not_reduced",
        "guardrail_violation_count": 0,
        "base_interpolation_used_for_repair": False,
        "repaired_checkpoint_written": False,
        "diagnostic_rows_used_as_positive": False,
        "donor_plus_action_used_as_loss_target": False,
        "non_actor_mean_parameter_changed": False,
    }


def test_selected_proposal_repair_aggregates_primary_and_stress_pass(tmp_path: Path) -> None:
    candidate_summary = tmp_path / "candidate_summary.csv"
    _write_candidate_summary(candidate_summary)

    def repair_fn(**kwargs):
        run_dir = Path(kwargs["run_dir"])
        run_dir.mkdir(parents=True)
        return _fake_repair_summary(alpha=float(kwargs["alpha"]), pass_candidate=True)

    summary = run_selected_proposal_repair(
        base_checkpoint=tmp_path / "base.pt",
        candidate_summary=candidate_summary,
        materialization_run_dir=tmp_path / "materialization",
        run_dir=tmp_path / "run",
        selected_alphas=(0.2, 1.0),
        repair_fn=repair_fn,
    )

    assert summary["passes_public_smoke_gates"] is True
    assert summary["selected_candidate_count"] == 2
    assert summary["candidate_public_pass_count"] == 2
    assert summary["primary_alpha_0_2_pass"] is True
    assert summary["null_result_classification"] == "selected_proposal_repair_public_pass"
    assert (tmp_path / "run" / "candidate_summary.csv").exists()
    assert (tmp_path / "run" / "aggregate_summary.csv").exists()
    assert (tmp_path / "run" / "guardrail_summary.csv").exists()


def test_selected_proposal_repair_reports_primary_pass_stress_fail(tmp_path: Path) -> None:
    candidate_summary = tmp_path / "candidate_summary.csv"
    _write_candidate_summary(candidate_summary)

    def repair_fn(**kwargs):
        run_dir = Path(kwargs["run_dir"])
        run_dir.mkdir(parents=True)
        alpha = float(kwargs["alpha"])
        return _fake_repair_summary(alpha=alpha, pass_candidate=alpha == 0.2)

    summary = run_selected_proposal_repair(
        base_checkpoint=tmp_path / "base.pt",
        candidate_summary=candidate_summary,
        materialization_run_dir=tmp_path / "materialization",
        run_dir=tmp_path / "run",
        selected_alphas=(0.2, 1.0),
        repair_fn=repair_fn,
    )

    assert summary["passes_public_smoke_gates"] is True
    assert summary["candidate_public_pass_count"] == 1
    assert summary["primary_alpha_0_2_pass"] is True
    assert summary["null_result_classification"] == "selected_proposal_primary_pass_stress_fail"


def test_selected_proposal_repair_fails_when_primary_fails(tmp_path: Path) -> None:
    candidate_summary = tmp_path / "candidate_summary.csv"
    _write_candidate_summary(candidate_summary)

    def repair_fn(**kwargs):
        run_dir = Path(kwargs["run_dir"])
        run_dir.mkdir(parents=True)
        return _fake_repair_summary(alpha=float(kwargs["alpha"]), pass_candidate=False)

    summary = run_selected_proposal_repair(
        base_checkpoint=tmp_path / "base.pt",
        candidate_summary=candidate_summary,
        materialization_run_dir=tmp_path / "materialization",
        run_dir=tmp_path / "run",
        selected_alphas=(0.2, 1.0),
        repair_fn=repair_fn,
    )

    assert summary["passes_public_smoke_gates"] is False
    assert summary["primary_alpha_0_2_pass"] is False
    assert summary["null_result_classification"] == "selected_proposal_repair_scope_insufficient"
