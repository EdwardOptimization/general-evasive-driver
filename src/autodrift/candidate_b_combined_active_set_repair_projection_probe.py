"""Run Candidate B combined active-set repair/projection probe."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.candidate_b_temporal_safe_projection_probe import (
    DEFAULT_BASE_CHECKPOINT,
    DEFAULT_ENV_CONFIG,
    DEFAULT_M270_NPZ,
    DEFAULT_M297_NPZ,
    DEFAULT_TEMPORAL_BASE_SUMMARY,
    DEFAULT_TEMPORAL_CORPUS,
    run_temporal_safe_projection_probe,
)
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.exact_post_ppo_repair import (
    ExactRepairConfig,
    optimize_exact_post_ppo_repair,
    trajectory_action_anchor_errors,
)
from autodrift.intervention_objectives import load_trajectory_action_anchor, weighted_mean
from autodrift.train_ppo import resolve_device


DEFAULT_RAW_CHECKPOINT = Path("runs/ppo_m1026_candidate_b_guarded_smoke_seed61026/checkpoint.pt")
DEFAULT_CURRENT_FAMILY_CONFLICT_NPZ = Path(
    "runs/m393_current_family_rejected_boundary_targets/current_family_conflict_corpus.npz"
)
DEFAULT_COMBINED_ANCHOR_NPZ = Path(
    "runs/m1037_candidate_b_combined_active_set_anchor_export/combined_active_set_anchor_row16x4.npz"
)
DEFAULT_RUN_DIR = Path("runs/m1038_candidate_b_combined_active_set_repair_projection_probe")


REPAIR_CANDIDATES: tuple[tuple[str, str, int, float], ...] = (
    ("raw_row16x4_s40", "repair_from_raw", 61038, 0.02),
    ("base_row16x4_s40", "repair_from_base", 61039, 0.0),
    ("line_row16x4_s40", "line_search_boundary", 61040, 0.0),
)


def parse_alphas(text: str) -> tuple[float, ...]:
    values = tuple(float(part.strip()) for part in str(text).split(",") if part.strip())
    if not values:
        raise argparse.ArgumentTypeError("expected at least one alpha")
    if any(value < 0.0 or value > 1.0 for value in values):
        raise argparse.ArgumentTypeError("alphas must be in [0, 1]")
    return values


def classify_combined_active_set_probe(
    *,
    projection_result_class: str,
    actor_inputs_changed: bool,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if bool(actor_inputs_changed) or bool(ppo_used) or bool(promoted):
        return "candidate_b_combined_active_set_repair_contract_artifact"
    if projection_result_class.endswith("_first_replay_candidate"):
        return "candidate_b_combined_active_set_projection_first_replay_candidate"
    if projection_result_class.endswith("_no_temporal_candidate"):
        return "candidate_b_combined_active_set_repair_temporal_regression"
    if projection_result_class.endswith("_no_exact_candidate"):
        return "candidate_b_combined_active_set_repair_exact_regression"
    if projection_result_class.endswith("_base_equivalent"):
        return "candidate_b_combined_active_set_repair_base_equivalent"
    if projection_result_class.endswith("_proof_washout"):
        return "candidate_b_combined_active_set_projection_proof_washout"
    return "candidate_b_combined_active_set_repair_metric_artifact"


def failure_types_for_combined_probe(result_class: str) -> list[str]:
    if result_class.endswith("_first_replay_candidate"):
        return ["none"]
    if result_class.endswith("_contract_artifact"):
        return ["contract_violation"]
    if result_class.endswith("_base_equivalent"):
        return ["objective_overfit"]
    if result_class.endswith("_metric_artifact"):
        return ["metric_artifact"]
    return ["proof_washout"]


def next_blocker_for_combined_probe(result_class: str) -> str:
    if result_class.endswith("_first_replay_candidate"):
        return "candidate_b_combined_active_set_full_public_gate_design"
    if result_class.endswith("_temporal_regression") or result_class.endswith("_base_equivalent"):
        return "candidate_b_combined_active_set_temporal_objective_integration_design"
    if result_class.endswith("_exact_regression"):
        return "candidate_b_combined_active_set_exact_failure_audit"
    if result_class.endswith("_proof_washout"):
        return "candidate_b_combined_active_set_first_replay_failure_audit"
    return "candidate_b_combined_active_set_contract_or_metric_audit"


def _repair_config(lambda_param_raw: float) -> ExactRepairConfig:
    return ExactRepairConfig(
        lambda_current_family_conflict=1000.0,
        lambda_current_family_conflict_rejected=10.0,
        lambda_replay_trajectory_anchor=10.0,
        lambda_param_raw=float(lambda_param_raw),
    )


def _run_exact_repairs(
    *,
    base_checkpoint: Path,
    raw_checkpoint: Path,
    preference_npz: Path,
    outcome_npz: Path,
    current_family_conflict_npz: Path,
    combined_anchor_npz: Path,
    device: str,
    steps: int,
    learning_rate: float,
    run_dir: Path,
) -> tuple[list[dict[str, Any]], tuple[tuple[str, Path], ...]]:
    repair_rows: list[dict[str, Any]] = []
    repair_specs: list[tuple[str, Path]] = []
    for label, start_mode, seed, lambda_param_raw in REPAIR_CANDIDATES:
        candidate_run_dir = run_dir / "exact_repair" / label
        summary = optimize_exact_post_ppo_repair(
            base_checkpoint=base_checkpoint,
            raw_checkpoint=raw_checkpoint,
            preference_npz=preference_npz,
            outcome_npz=outcome_npz,
            current_family_conflict_npz=current_family_conflict_npz,
            replay_trajectory_anchor_npz=combined_anchor_npz,
            device=device,
            start_mode=start_mode,
            line_search_alphas=[0.0, 0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1],
            steps=steps,
            learning_rate=learning_rate,
            seed=seed,
            train_scope="actor_coupling",
            train_log_std=False,
            config=_repair_config(lambda_param_raw),
            run_dir=candidate_run_dir,
            selection_policy="best_feasible",
        )
        candidate_checkpoint = Path(str(summary["candidate_checkpoint"]))
        repair_specs.append((label, candidate_checkpoint))
        candidate = summary["candidate"]
        repair_rows.append(
            {
                "label": label,
                "start_mode": start_mode,
                "seed": int(seed),
                "lambda_param_raw": float(lambda_param_raw),
                "run_dir": str(candidate_run_dir),
                "candidate_checkpoint": str(candidate_checkpoint),
                "selected_step": int(summary.get("selected_step", -1)),
                "selected_metric_phase": str(summary.get("selected_metric_phase", "")),
                "exact_lexicographic_pass": bool(candidate.get("exact_lexicographic_pass", False)),
                "exact_m297_delta_vs_base": float(candidate.get("exact_m297_delta_vs_base", 0.0)),
                "exact_m270_delta_vs_base": float(candidate.get("exact_m270_delta_vs_base", 0.0)),
                "replay_trajectory_anchor_loss": float(candidate.get("replay_trajectory_anchor_loss", 0.0)),
                "actor_inputs_changed": bool(summary.get("actor_inputs_changed", False)),
                "ppo_used": bool(summary.get("ppo_run", False)),
                "checkpoint_promoted": bool(summary.get("checkpoint_promoted", False)),
            }
        )
    return repair_rows, tuple(repair_specs)


def combined_anchor_family_loss_rows(
    *,
    checkpoint_rows_csv: Path,
    combined_anchor_npz: Path,
    device: str,
) -> list[dict[str, Any]]:
    checkpoint_frame = pd.read_csv(checkpoint_rows_csv)
    raw_arrays = np.load(combined_anchor_npz)
    if "family_id" not in raw_arrays.files:
        raise ValueError("combined anchor npz must contain family_id for M1038 diagnostics")
    family_id_np = np.asarray(raw_arrays["family_id"], dtype=np.int64)
    resolved_device = resolve_device(device)
    family_id = torch.as_tensor(family_id_np, dtype=torch.long, device=resolved_device)
    rows: list[dict[str, Any]] = []
    for _, row in checkpoint_frame.iterrows():
        checkpoint = Path(str(row["checkpoint"]))
        model, _ = load_actor_critic_checkpoint(checkpoint, device=str(resolved_device))
        anchor = load_trajectory_action_anchor(
            combined_anchor_npz,
            device=resolved_device,
            obs_dim=int(model.obs_dim),
            hidden_size=int(model.actor_mean.in_features),
            act_dim=int(model.act_dim),
        )
        with torch.no_grad():
            errors = trajectory_action_anchor_errors(model, anchor)
            m267_mask = family_id == 0
            m183_mask = family_id == 1
            m267_loss = weighted_mean(errors[m267_mask], anchor.weight[m267_mask])
            m183_loss = weighted_mean(errors[m183_mask], anchor.weight[m183_mask])
            total_loss = weighted_mean(errors, anchor.weight)
        rows.append(
            {
                "candidate_label": str(row["candidate_label"]),
                "source_label": str(row["source_label"]),
                "alpha": float(row["alpha"]),
                "checkpoint": str(checkpoint),
                "combined_anchor_total_loss": float(total_loss.detach().cpu().item()),
                "combined_anchor_m267_loss": float(m267_loss.detach().cpu().item()),
                "combined_anchor_m183_row16_loss": float(m183_loss.detach().cpu().item()),
            }
        )
    return rows


def run_combined_active_set_repair_projection_probe(
    *,
    base_checkpoint: Path,
    raw_checkpoint: Path,
    preference_npz: Path,
    outcome_npz: Path,
    current_family_conflict_npz: Path,
    combined_anchor_npz: Path,
    temporal_corpus: Path,
    temporal_base_summary: Path,
    env_config_path: Path,
    alphas: tuple[float, ...],
    steps: int,
    learning_rate: float,
    max_continuation_steps: int,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    repair_rows, repair_specs = _run_exact_repairs(
        base_checkpoint=base_checkpoint,
        raw_checkpoint=raw_checkpoint,
        preference_npz=preference_npz,
        outcome_npz=outcome_npz,
        current_family_conflict_npz=current_family_conflict_npz,
        combined_anchor_npz=combined_anchor_npz,
        device=device,
        steps=steps,
        learning_rate=learning_rate,
        run_dir=run_dir,
    )
    write_csv_rows(run_dir / "exact_repair_summary.csv", repair_rows)
    projection_dir = run_dir / "temporal_projection"
    projection_summary = run_temporal_safe_projection_probe(
        base_checkpoint=base_checkpoint,
        repair_candidates=repair_specs,
        alphas=alphas,
        temporal_corpus=temporal_corpus,
        temporal_base_summary=temporal_base_summary,
        preference_npz=preference_npz,
        outcome_npz=outcome_npz,
        run_dir=projection_dir,
        device=device,
        env_config_path=env_config_path,
        max_continuation_steps=max_continuation_steps,
    )
    family_rows = combined_anchor_family_loss_rows(
        checkpoint_rows_csv=Path(str(projection_summary["candidate_checkpoints_csv"])),
        combined_anchor_npz=combined_anchor_npz,
        device=device,
    )
    combined_anchor_metrics_csv = run_dir / "combined_anchor_projection_metrics.csv"
    write_csv_rows(combined_anchor_metrics_csv, family_rows)
    result_class = classify_combined_active_set_probe(
        projection_result_class=str(projection_summary["result_class"]),
        actor_inputs_changed=bool(projection_summary.get("actor_input_change_count", 0)),
        ppo_used=False,
        promoted=False,
    )
    selected_label = projection_summary.get("selected_candidate_label")
    selected_family = next((row for row in family_rows if row["candidate_label"] == selected_label), None)
    summary = {
        "run_type": "candidate_b_combined_active_set_repair_projection_probe",
        "base_checkpoint": base_checkpoint,
        "raw_checkpoint": raw_checkpoint,
        "preference_npz": preference_npz,
        "outcome_npz": outcome_npz,
        "current_family_conflict_npz": current_family_conflict_npz,
        "combined_anchor_npz": combined_anchor_npz,
        "temporal_corpus": temporal_corpus,
        "temporal_base_summary": temporal_base_summary,
        "env_config": env_config_path,
        "alphas": list(alphas),
        "steps": int(steps),
        "learning_rate": float(learning_rate),
        "exact_repair_count": int(len(repair_rows)),
        "exact_repair_summary_csv": run_dir / "exact_repair_summary.csv",
        "temporal_projection_summary_json": projection_summary["summary_json"],
        "temporal_projection_result_class": projection_summary["result_class"],
        "combined_anchor_projection_metrics_csv": combined_anchor_metrics_csv,
        "selected_candidate_label": selected_label,
        "selected_checkpoint": projection_summary.get("selected_checkpoint"),
        "selected_combined_anchor_total_loss": selected_family.get("combined_anchor_total_loss")
        if selected_family is not None
        else None,
        "selected_combined_anchor_m267_loss": selected_family.get("combined_anchor_m267_loss")
        if selected_family is not None
        else None,
        "selected_combined_anchor_m183_row16_loss": selected_family.get("combined_anchor_m183_row16_loss")
        if selected_family is not None
        else None,
        "temporal_exact_pass_count": int(projection_summary.get("temporal_exact_pass_count", 0)),
        "temporal_and_exact_pass_count": int(projection_summary.get("temporal_and_exact_pass_count", 0)),
        "eligible_candidate_count": int(projection_summary.get("eligible_candidate_count", 0)),
        "m267_m264_first_replay_pass": bool(projection_summary.get("m267_m264_first_replay_pass", False)),
        "m267_m264_row15_retained": bool(projection_summary.get("m267_m264_row15_retained", False)),
        "m183_m170_first_replay_pass": bool(projection_summary.get("m183_m170_first_replay_pass", False)),
        "first_replay_attempted_candidate_count": int(
            projection_summary.get("first_replay_attempted_candidate_count", 0)
        ),
        "actor_inputs_changed": bool(projection_summary.get("actor_input_change_count", 0)),
        "training_started": True,
        "optimizer_started": True,
        "repair_used": True,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "private_holdout_used": False,
        "result_class": result_class,
        "failure_types": failure_types_for_combined_probe(result_class),
        "next_blocker": next_blocker_for_combined_probe(result_class),
        "summary_json": run_dir / "summary.json",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Candidate B combined active-set repair/projection probe.")
    parser.add_argument("--base-checkpoint", type=Path, default=DEFAULT_BASE_CHECKPOINT)
    parser.add_argument("--raw-checkpoint", type=Path, default=DEFAULT_RAW_CHECKPOINT)
    parser.add_argument("--preference-npz", type=Path, default=DEFAULT_M297_NPZ)
    parser.add_argument("--outcome-npz", type=Path, default=DEFAULT_M270_NPZ)
    parser.add_argument("--current-family-conflict-npz", type=Path, default=DEFAULT_CURRENT_FAMILY_CONFLICT_NPZ)
    parser.add_argument("--combined-anchor-npz", type=Path, default=DEFAULT_COMBINED_ANCHOR_NPZ)
    parser.add_argument("--temporal-corpus", type=Path, default=DEFAULT_TEMPORAL_CORPUS)
    parser.add_argument("--temporal-base-summary", type=Path, default=DEFAULT_TEMPORAL_BASE_SUMMARY)
    parser.add_argument("--env-config", type=Path, default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--alphas", type=parse_alphas, default=parse_alphas("0.05,0.10,0.15,0.20,0.25,0.30,0.35,0.40,0.45,0.50,0.60,0.75,1.0"))
    parser.add_argument("--steps", type=int, default=40)
    parser.add_argument("--learning-rate", type=float, default=3e-6)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    args = parser.parse_args()
    summary = run_combined_active_set_repair_projection_probe(
        base_checkpoint=args.base_checkpoint,
        raw_checkpoint=args.raw_checkpoint,
        preference_npz=args.preference_npz,
        outcome_npz=args.outcome_npz,
        current_family_conflict_npz=args.current_family_conflict_npz,
        combined_anchor_npz=args.combined_anchor_npz,
        temporal_corpus=args.temporal_corpus,
        temporal_base_summary=args.temporal_base_summary,
        env_config_path=args.env_config,
        alphas=args.alphas,
        steps=args.steps,
        learning_rate=args.learning_rate,
        max_continuation_steps=args.max_continuation_steps,
        device=args.device,
        run_dir=args.run_dir,
    )
    print(f"result_class={summary['result_class']}")
    print(f"selected_checkpoint={summary['selected_checkpoint']}")
    print(f"summary={summary['summary_json']}")


if __name__ == "__main__":
    main()
