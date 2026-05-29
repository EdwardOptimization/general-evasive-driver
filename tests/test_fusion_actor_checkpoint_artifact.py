from __future__ import annotations

from pathlib import Path

import pytest

from autodrift.fusion_actor_checkpoint_artifact import run_fusion_actor_checkpoint_artifact


def _write_candidate_summary(path: Path) -> None:
    checkpoint = path.parent / "alpha_0_2.pt"
    checkpoint.write_text("proposal", encoding="utf-8")
    path.write_text(
        "candidate_id,alpha,checkpoint,selected_repair_candidate\n"
        f"m1352_alpha_0_2,0.2,{checkpoint},True\n",
        encoding="utf-8",
    )


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    base = tmp_path / "base.pt"
    proposal = tmp_path / "alpha_0_2.pt"
    candidate_summary = tmp_path / "candidate_summary.csv"
    materialization = tmp_path / "materialization"
    base.write_text("base", encoding="utf-8")
    proposal.write_text("proposal", encoding="utf-8")
    _write_candidate_summary(candidate_summary)
    materialization.mkdir()
    return base, proposal, candidate_summary, materialization


def _fake_repair(**kwargs):
    checkpoint_path = Path(kwargs["checkpoint_artifact_path"])
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text("artifact", encoding="utf-8")
    run_dir = Path(kwargs["run_dir"])
    run_dir.mkdir(parents=True, exist_ok=True)
    return {
        "candidate_id": kwargs["candidate_id"],
        "alpha": float(kwargs["alpha"]),
        "initial_positive_exact_residual_mean": 0.0012401377316564322,
        "repaired_positive_exact_residual_mean": 0.0007376365829259157,
        "positive_exact_residual_reduction_ratio": 0.40519785496674926,
        "accepted_backtracking_step_count": 1,
        "excluded_parameter_delta_max": 0.0,
        "passes_candidate_gate": True,
        "null_result_classification": "fusion_actor_candidate_repair_public_pass",
        "guardrail_violation_count": 0,
    }


def _fake_repair_without_artifact(**kwargs):
    return {
        "candidate_id": kwargs["candidate_id"],
        "alpha": float(kwargs["alpha"]),
        "initial_positive_exact_residual_mean": 0.0012401377316564322,
        "repaired_positive_exact_residual_mean": 0.0007376365829259157,
        "positive_exact_residual_reduction_ratio": 0.40519785496674926,
        "accepted_backtracking_step_count": 1,
        "excluded_parameter_delta_max": 0.0,
        "passes_candidate_gate": True,
        "null_result_classification": "fusion_actor_candidate_repair_public_pass",
        "guardrail_violation_count": 0,
    }


def test_checkpoint_artifact_materialization_public_pass(tmp_path: Path) -> None:
    base, proposal, candidate_summary, materialization = _write_inputs(tmp_path)

    summary = run_fusion_actor_checkpoint_artifact(
        base_checkpoint=base,
        proposal_checkpoint=proposal,
        candidate_summary=candidate_summary,
        materialization_run_dir=materialization,
        run_dir=tmp_path / "run",
        repair_fn=_fake_repair,
    )

    assert summary["passes_public_smoke_gates"] is True
    assert summary["checkpoint_artifact_count"] == 1
    assert summary["selected_alpha"] == 0.2
    assert summary["artifact_label"] == "objective_sanity_artifact_only"
    assert summary["null_result_classification"] == "fusion_actor_checkpoint_artifact_public_pass"
    assert (tmp_path / "run" / "artifact_metadata.json").exists()
    assert (tmp_path / "run" / "checksums.sha256").exists()
    assert Path(summary["artifact_path"]).exists()


def test_checkpoint_artifact_materialization_requires_artifact(tmp_path: Path) -> None:
    base, proposal, candidate_summary, materialization = _write_inputs(tmp_path)

    summary = run_fusion_actor_checkpoint_artifact(
        base_checkpoint=base,
        proposal_checkpoint=proposal,
        candidate_summary=candidate_summary,
        materialization_run_dir=materialization,
        run_dir=tmp_path / "run",
        repair_fn=_fake_repair_without_artifact,
    )

    assert summary["passes_public_smoke_gates"] is False
    assert summary["checkpoint_artifact_count"] == 0
    assert summary["null_result_classification"] == "checkpoint_artifact_missing"


def test_checkpoint_artifact_rejects_non_primary_alpha(tmp_path: Path) -> None:
    base, proposal, candidate_summary, materialization = _write_inputs(tmp_path)

    with pytest.raises(ValueError, match="alpha 0.2 primary"):
        run_fusion_actor_checkpoint_artifact(
            base_checkpoint=base,
            proposal_checkpoint=proposal,
            candidate_summary=candidate_summary,
            materialization_run_dir=materialization,
            run_dir=tmp_path / "run",
            selected_alpha=0.4,
            repair_fn=_fake_repair,
        )
