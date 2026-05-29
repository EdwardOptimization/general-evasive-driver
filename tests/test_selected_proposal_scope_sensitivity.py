from __future__ import annotations

from pathlib import Path

from autodrift.selected_proposal_scope_sensitivity import (
    FEATURE_MODE_DIFFERENTIABLE,
    FEATURE_MODE_FROZEN,
    run_selected_proposal_scope_sensitivity,
)


SCOPES = ("actor_mean", "fusion_actor", "context_fusion_actor", "response_fusion_actor", "full_policy_actor")


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


def _write_materialization(path: Path) -> None:
    path.mkdir(parents=True)
    (path / "diagnostic_policy_guardrail_rows.csv").write_text("role\n", encoding="utf-8")


def _row(*, alpha: float, scope: str, feature_mode: str, frozen_upstream_bad: bool = False, reduce_primary: bool = True) -> dict[str, object]:
    wider = scope != "actor_mean"
    primary = alpha == 0.2
    differentiable = feature_mode == FEATURE_MODE_DIFFERENTIABLE
    upstream = 0.0
    if feature_mode == FEATURE_MODE_FROZEN and wider and frozen_upstream_bad:
        upstream = 0.1
    elif differentiable and wider:
        upstream = 0.1
    reduced = bool(differentiable and wider and primary and reduce_primary)
    return {
        "candidate_id": f"alpha{alpha}",
        "proposal_source_type": "same_line_interpolation",
        "alpha": float(alpha),
        "proposal_checkpoint": f"alpha{alpha}.pt",
        "scope": scope,
        "feature_mode": feature_mode,
        "parameter_name_count": 1,
        "parameter_names": "actor_mean.weight",
        "initial_positive_exact_residual_mean": 0.01,
        "initial_positive_action_l2_max": 0.1,
        "scope_grad_norm": 0.1 if differentiable or scope == "actor_mean" else 0.01,
        "actor_mean_grad_norm": 0.01,
        "upstream_grad_norm": upstream,
        "finite_gradient": True,
        "nonzero_gradient": bool(differentiable or scope == "actor_mean"),
        "upstream_nonzero_gradient": bool(upstream > 0.0),
        "initial_scope_l2_to_base": 0.1,
        "model_restored_after_probe": True,
        "max_parameter_delta_after_restore": 0.0,
        "one_step_reduced": reduced,
        "one_step_factor": 1.0 if reduced else "",
        "one_step_l2": 0.01 if reduced else 0.0,
        "one_step_reduction": 0.001 if reduced else 0.0,
        "one_step_reduction_ratio": 0.1 if reduced else 0.0,
        "one_step_scope_l2_to_base": 0.09,
        "one_step_stop_reason": "accepted" if reduced else "no_backtracking_candidate_accepted",
    }


def _run(tmp_path: Path, *, frozen_upstream_bad: bool = False, reduce_primary: bool = True):
    candidate_summary = tmp_path / "candidate_summary.csv"
    materialization = tmp_path / "materialization"
    _write_candidate_summary(candidate_summary)
    _write_materialization(materialization)

    def candidate_fn(**kwargs):
        alpha = float(kwargs["alpha"])
        rows = []
        for scope in SCOPES:
            for mode in (FEATURE_MODE_FROZEN, FEATURE_MODE_DIFFERENTIABLE):
                rows.append(
                    _row(
                        alpha=alpha,
                        scope=scope,
                        feature_mode=mode,
                        frozen_upstream_bad=frozen_upstream_bad,
                        reduce_primary=reduce_primary,
                    )
                )
        return rows

    return run_selected_proposal_scope_sensitivity(
        base_checkpoint=tmp_path / "base.pt",
        candidate_summary=candidate_summary,
        materialization_run_dir=materialization,
        run_dir=tmp_path / "run",
        scopes=SCOPES,
        candidate_fn=candidate_fn,
    )


def test_scope_sensitivity_aggregates_public_pass(tmp_path: Path) -> None:
    summary = _run(tmp_path)

    assert summary["passes_public_smoke_gates"] is True
    assert summary["selected_candidate_count"] == 3
    assert summary["scope_count"] == 5
    assert summary["frozen_feature_upstream_grad_zero"] is True
    assert summary["primary_alpha_0_2_wider_scope_nonzero_grad_count"] == 4
    assert summary["primary_alpha_0_2_wider_scope_reduction_count"] == 4
    assert summary["model_restored_after_probe_count"] == 15
    assert summary["null_result_classification"] == "selected_proposal_scope_sensitivity_public_pass"
    assert (tmp_path / "run" / "summary.json").exists()
    assert (tmp_path / "run" / "scope_summary.csv").exists()
    assert (tmp_path / "run" / "guardrail_summary.csv").exists()


def test_scope_sensitivity_fails_frozen_upstream_gradient(tmp_path: Path) -> None:
    summary = _run(tmp_path, frozen_upstream_bad=True)

    assert summary["passes_public_smoke_gates"] is False
    assert summary["frozen_feature_upstream_grad_zero"] is False
    assert summary["null_result_classification"] == "frozen_feature_upstream_gradient_violation"


def test_scope_sensitivity_fails_without_primary_wider_reduction(tmp_path: Path) -> None:
    summary = _run(tmp_path, reduce_primary=False)

    assert summary["passes_public_smoke_gates"] is False
    assert summary["primary_alpha_0_2_wider_scope_reduction_count"] == 0
    assert summary["null_result_classification"] == "primary_wider_scope_no_one_step_reduction"
