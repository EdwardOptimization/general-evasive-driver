from __future__ import annotations

from pathlib import Path

from autodrift.proposal_source_preflight import run_proposal_source_preflight


ALPHAS = (0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.4, 0.6, 0.8, 1.0)


def _alpha_label(alpha: float) -> str:
    text = str(alpha).replace(".", "_")
    return f"m1352_alpha_{text}"


def _write_candidate_tables(root: Path, *, all_pass: bool = False) -> tuple[Path, Path]:
    candidate_path = root / "candidate_checkpoints.csv"
    alpha_path = root / "alpha_summary.csv"
    rows = ["alpha,label,checkpoint,exact_admitted,actor_inputs_changed,forbidden_parameter_mutation_detected,log_std_l2"]
    alpha_rows = ["alpha,label,checkpoint,preflight_pass,m267_m264_gate_pass,m183_m170_gate_pass"]
    for alpha in ALPHAS:
        label = _alpha_label(alpha)
        checkpoint = root / f"{label}.pt"
        checkpoint.write_text("checkpoint", encoding="utf-8")
        rows.append(f"{alpha},{label},{checkpoint},True,False,False,0.0")
        preflight_pass = all_pass or alpha <= 0.1
        m267_pass = preflight_pass or alpha < 1.0
        m183_pass = preflight_pass
        alpha_rows.append(f"{alpha},{label},{checkpoint},{preflight_pass},{m267_pass},{m183_pass}")
    candidate_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    alpha_path.write_text("\n".join(alpha_rows) + "\n", encoding="utf-8")
    return candidate_path, alpha_path


def _fake_exact_summary(**kwargs):
    checkpoint = Path(kwargs["checkpoint"])
    parts = checkpoint.stem.split("_")
    alpha = float(f"{parts[-2]}.{parts[-1]}")
    residual = abs(alpha - 0.1) * 0.01
    return {
        "positive_exact_residual_mean": residual,
        "positive_policy_action_residual_l2_max": residual * 10.0,
        "diagnostic_policy_action_residual_l2_max": residual * 5.0,
        "diagnostic_rows_used_as_positive": False,
        "donor_plus_action_used_as_loss_target": False,
        "actor_input_contract_changed": False,
        "checkpoint_weights_mutated": False,
        "passes_public_smoke_gates": residual == 0.0,
        "null_result_classification": "contour_aware_policy_target_exact_evaluator_public_pass"
        if residual == 0.0
        else "public_gate_failure",
    }


def _zero_exact_summary(**kwargs):
    summary = _fake_exact_summary(**kwargs)
    summary["positive_exact_residual_mean"] = 0.0
    return summary


def _fake_delta(base_checkpoint: Path, candidate_checkpoint: Path, device: str) -> dict[str, float]:
    del base_checkpoint, device
    stem = candidate_checkpoint.stem
    scale = 0.0 if stem.endswith("0_1") else 0.2
    return {
        "parameter_l2_to_base": scale,
        "parameter_max_abs_to_base": scale / 10.0,
        "actor_mean_l2_to_base": scale / 2.0,
        "non_actor_mean_l2_to_base": scale / 2.0,
    }


def test_proposal_source_preflight_selects_repair_candidates(tmp_path: Path) -> None:
    candidate_path, alpha_path = _write_candidate_tables(tmp_path)

    summary = run_proposal_source_preflight(
        base_checkpoint=tmp_path / "m1352_alpha_0_1.pt",
        candidate_checkpoints=candidate_path,
        alpha_summary=alpha_path,
        materialization_run_dir=tmp_path / "materialization",
        run_dir=tmp_path / "run",
        exact_evaluate_fn=_fake_exact_summary,
        model_delta_fn=_fake_delta,
    )

    assert summary["passes_public_smoke_gates"] is True
    assert summary["source_candidate_count"] == 10
    assert summary["branch_compatible_candidate_count"] == 10
    assert summary["base_anchor_count"] == 1
    assert summary["larger_proposal_candidate_count"] == 5
    assert summary["selected_repair_candidate_count"] == 5
    assert summary["checkpoint_artifact_count"] == 0
    assert summary["projection_used_count"] == 0
    assert summary["null_result_classification"] == "proposal_source_preflight_public_pass"
    assert (tmp_path / "run" / "candidate_summary.csv").exists()
    assert (tmp_path / "run" / "guardrail_summary.csv").exists()


def test_proposal_source_preflight_fails_without_selected_candidate(tmp_path: Path) -> None:
    candidate_path, alpha_path = _write_candidate_tables(tmp_path, all_pass=True)

    summary = run_proposal_source_preflight(
        base_checkpoint=tmp_path / "m1352_alpha_0_1.pt",
        candidate_checkpoints=candidate_path,
        alpha_summary=alpha_path,
        materialization_run_dir=tmp_path / "materialization",
        run_dir=tmp_path / "run",
        exact_evaluate_fn=_zero_exact_summary,
        model_delta_fn=_fake_delta,
    )

    assert summary["passes_public_smoke_gates"] is False
    assert summary["selected_repair_candidate_count"] == 0
    assert summary["null_result_classification"] == "no_selected_repair_candidate"
