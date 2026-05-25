"""No-training alpha-boundary audit for a raw controlled-fusion direction."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import torch

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import load_scenario_config
from autodrift.public_base_controlled_fusion_surface_probe import (
    controlled_surface_checksums,
    evaluate_controlled_fusion_alphas,
    _clone_state_dict,
    _load_trainable_samples,
)
from autodrift.public_base_regenerated_target_residual_probe import target_weight_vector
from autodrift.train_ppo import resolve_device
from autodrift.v4_sequence_objective_probe import _metadata_missing, _parse_float_list, _read_csv_rows


DEFAULT_BOUNDARY_ALPHAS = (
    0.050,
    0.075,
    0.100,
    0.125,
    0.150,
    0.175,
    0.200,
    0.225,
    0.250,
    0.275,
    0.300,
    0.325,
    0.350,
    0.500,
    0.750,
    1.000,
)


def classify_controlled_fusion_raw_direction_feasibility(
    *,
    forbidden_parameter_changed_between_checkpoints: bool,
    allowed_surface_changed_between_checkpoints: bool,
    reconstruction_success_rate: float,
    metadata_missing_rows: int,
    missing_target_keys: int,
    candidate_count: int,
    any_tail_lift: bool,
    any_normal_retained_tail_lift: bool,
    training_started: bool,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if (
        bool(forbidden_parameter_changed_between_checkpoints)
        or bool(training_started)
        or bool(ppo_used)
        or bool(promoted)
    ):
        return "public_base_controlled_fusion_raw_direction_feasibility_contract_artifact"
    if not bool(allowed_surface_changed_between_checkpoints):
        return "public_base_controlled_fusion_raw_direction_feasibility_no_raw_direction"
    if int(missing_target_keys) > 0:
        return "public_base_controlled_fusion_raw_direction_feasibility_target_join_blocked"
    if float(reconstruction_success_rate) < 0.98 or int(metadata_missing_rows) > 0:
        return "public_base_controlled_fusion_raw_direction_feasibility_reconstruction_blocked"
    if int(candidate_count) > 0:
        return "public_base_controlled_fusion_raw_direction_feasibility_candidate"
    if bool(any_normal_retained_tail_lift):
        return "public_base_controlled_fusion_raw_direction_feasibility_target_conflict"
    if bool(any_tail_lift):
        return "public_base_controlled_fusion_raw_direction_feasibility_trust_region_conflict"
    return "public_base_controlled_fusion_raw_direction_feasibility_no_tail_lift"


def run_controlled_fusion_raw_direction_feasibility(
    *,
    base_checkpoint_path: Path,
    raw_checkpoint_path: Path,
    positive_rows_path: Path,
    contrast_rows_path: Path,
    scenario_config_path: Path,
    target_rows_path: Path,
    m912_summary_path: Path,
    low_tail_rows_path: Path,
    run_dir: Path,
    device: str,
    alphas: tuple[float, ...] = DEFAULT_BOUNDARY_ALPHAS,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    scenario_config = load_scenario_config(scenario_config_path)
    env_config = load_env_config(Path(scenario_config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    base_model, _ = load_actor_critic_checkpoint(base_checkpoint_path, device=str(resolved_device))
    raw_model, _ = load_actor_critic_checkpoint(raw_checkpoint_path, device=str(resolved_device))
    base_model.eval()
    raw_model.eval()
    for parameter in base_model.parameters():
        parameter.requires_grad_(False)
    for parameter in raw_model.parameters():
        parameter.requires_grad_(False)
    base_state = _clone_state_dict(base_model)
    raw_state = _clone_state_dict(raw_model)
    base_checksums = controlled_surface_checksums(base_state)
    raw_checksums = controlled_surface_checksums(raw_state)
    positives = _read_csv_rows(positive_rows_path)
    contrast_rows = _read_csv_rows(contrast_rows_path)
    target_rows = _read_csv_rows(target_rows_path)
    low_tail_rows = _read_csv_rows(low_tail_rows_path)
    m912_summary = read_json(m912_summary_path)
    metadata_missing_rows = sum(1 for row in positives if _metadata_missing(row))
    samples, meta_rows, rejected_rows = _load_trainable_samples(
        model=base_model,
        positive_rows=positives,
        contrast_rows=contrast_rows,
        scenario_config=scenario_config,
        env_config=env_config,
        device=resolved_device,
    )
    reconstruction_rate = float(len(meta_rows) / max(len(positives), 1))
    if len(meta_rows) == 0:
        target_mask = torch.empty((0,), dtype=torch.bool, device=resolved_device)
        target_actions = torch.empty((0, 3), dtype=torch.float32, device=resolved_device)
        weight_rows: list[dict[str, Any]] = []
        missing_target_keys: set[tuple[str, str, str, str]] = set()
        alpha_rows: list[dict[str, Any]] = []
        objective_rows: list[dict[str, Any]] = []
    else:
        target_mask, _low_tail_mask, target_actions, _target_weights, weight_rows, missing_target_keys = (
            target_weight_vector(
                meta_rows=meta_rows,
                target_rows=target_rows,
                low_tail_rows=low_tail_rows,
                normal_actions=samples["normal_actions"],
            )
        )
        if missing_target_keys:
            alpha_rows = []
            objective_rows = []
        else:
            alpha_rows, objective_rows = evaluate_controlled_fusion_alphas(
                base_model,
                samples=samples,
                meta_rows=meta_rows,
                base_state=base_state,
                raw_state=raw_state,
                alphas=alphas,
                target_mask=target_mask,
                target_actions=target_actions,
                target_rows=target_rows,
                near_base_gap_p10=float(m912_summary["near_base_gap_p10"]),
                near_base_gap_deficit_mean=float(m912_summary["near_base_gap_deficit_mean"]),
                near_base_low_tail_fraction=float(m912_summary["low_tail_fraction"]),
            )
    candidate_rows = [row for row in alpha_rows if bool(row.get("exact_probe_candidate", False))]
    tail_rows = [row for row in alpha_rows if bool(row.get("tail_lift_pass", False))]
    normal_tail_rows = [
        row for row in alpha_rows if bool(row.get("tail_lift_pass", False)) and bool(row.get("normal_retention_pass", False))
    ]
    low_tail_effect_rows = [row for row in alpha_rows if bool(row.get("low_tail_effect_candidate", False))]
    target_tolerance_rows = [row for row in alpha_rows if bool(row.get("target_tolerance_candidate", False))]
    normal_safe_trend_rows = [row for row in alpha_rows if bool(row.get("normal_safe_low_tail_trend", False))]
    forbidden_changed = bool(base_checksums["forbidden"] != raw_checksums["forbidden"])
    allowed_changed = bool(
        base_checksums["actor_mean"] != raw_checksums["actor_mean"] or base_checksums["fusion"] != raw_checksums["fusion"]
    )
    result_class = classify_controlled_fusion_raw_direction_feasibility(
        forbidden_parameter_changed_between_checkpoints=forbidden_changed,
        allowed_surface_changed_between_checkpoints=allowed_changed,
        reconstruction_success_rate=reconstruction_rate,
        metadata_missing_rows=metadata_missing_rows,
        missing_target_keys=len(missing_target_keys),
        candidate_count=len(candidate_rows),
        any_tail_lift=bool(tail_rows),
        any_normal_retained_tail_lift=bool(normal_tail_rows),
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    best_candidate = candidate_rows[0] if candidate_rows else {}
    best_normal_retaining = min(
        [row for row in alpha_rows if bool(row.get("normal_retention_pass", False))],
        key=lambda row: (float(row.get("low_tail_fraction", 1.0)), float(row.get("gap_deficit_mean", 1.0))),
        default={},
    )
    best_tail_lift_nonretaining = min(
        [row for row in tail_rows if not bool(row.get("normal_retention_pass", False))],
        key=lambda row: (float(row.get("low_tail_fraction", 1.0)), float(row.get("gap_deficit_mean", 1.0))),
        default={},
    )
    write_csv_rows(run_dir / "alpha_metrics.csv", alpha_rows)
    write_csv_rows(run_dir / "objective_rows.csv", objective_rows)
    write_csv_rows(run_dir / "target_weight_rows.csv", weight_rows)
    write_csv_rows(
        run_dir / "rejected_rows.csv",
        [*rejected_rows, *({"rejection_reason": "missing_target_join", "key": str(key)} for key in sorted(missing_target_keys))],
    )
    summary = {
        "run_type": "public_base_controlled_fusion_raw_direction_feasibility",
        "base_checkpoint": base_checkpoint_path,
        "raw_checkpoint": raw_checkpoint_path,
        "positive_rows_input": positive_rows_path,
        "contrast_rows_input": contrast_rows_path,
        "scenario_config": scenario_config_path,
        "target_rows": target_rows_path,
        "m912_summary": m912_summary_path,
        "low_tail_rows": low_tail_rows_path,
        "positive_rows": int(len(positives)),
        "reconstructed_rows": int(len(meta_rows)),
        "sample_reconstruction_success_rate": reconstruction_rate,
        "metadata_missing_rows": int(metadata_missing_rows),
        "target_rows_count": int(len(target_rows)),
        "joined_target_rows": int(sum(1 for row in weight_rows if bool(row.get("target_available", False)))),
        "missing_target_keys": int(len(missing_target_keys)),
        "low_tail_rows_count": int(len(low_tail_rows)),
        "alphas": [float(alpha) for alpha in alphas],
        "candidate_alpha_count": int(len(candidate_rows)),
        "candidate_alphas": [float(row.get("alpha")) for row in candidate_rows],
        "strict_candidate_count": int(len(candidate_rows)),
        "low_tail_effect_candidate_count": int(len(low_tail_effect_rows)),
        "target_tolerance_candidate_count": int(len(target_tolerance_rows)),
        "normal_safe_low_tail_trend_count": int(len(normal_safe_trend_rows)),
        "low_tail_effect_candidate_alphas": [float(row.get("alpha")) for row in low_tail_effect_rows],
        "target_tolerance_candidate_alphas": [float(row.get("alpha")) for row in target_tolerance_rows],
        "normal_safe_low_tail_trend_alphas": [float(row.get("alpha")) for row in normal_safe_trend_rows],
        "best_candidate": best_candidate,
        "best_normal_retaining_row": best_normal_retaining,
        "best_tail_lift_nonretaining_row": best_tail_lift_nonretaining,
        "actor_mean_changed_between_checkpoints": bool(base_checksums["actor_mean"] != raw_checksums["actor_mean"]),
        "fusion_changed_between_checkpoints": bool(base_checksums["fusion"] != raw_checksums["fusion"]),
        "forbidden_parameter_changed_between_checkpoints": forbidden_changed,
        "base_checksums": base_checksums,
        "raw_checksums": raw_checksums,
        "training_started": False,
        "optimizer_started": False,
        "m880_exact_used": False,
        "replay_used": False,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "result_class": result_class,
        "summary_json": run_dir / "summary.json",
        "alpha_metrics_csv": run_dir / "alpha_metrics.csv",
        "objective_rows_csv": run_dir / "objective_rows.csv",
        "target_weight_rows_csv": run_dir / "target_weight_rows.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training controlled-fusion raw direction alpha audit.")
    parser.add_argument("--base-checkpoint", type=Path, required=True)
    parser.add_argument("--raw-checkpoint", type=Path, required=True)
    parser.add_argument("--positive-rows", type=Path, required=True)
    parser.add_argument("--contrast-rows", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--target-rows", type=Path, required=True)
    parser.add_argument("--m912-summary", type=Path, required=True)
    parser.add_argument("--low-tail-rows", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--alphas", type=_parse_float_list, default=DEFAULT_BOUNDARY_ALPHAS)
    args = parser.parse_args()
    summary = run_controlled_fusion_raw_direction_feasibility(
        base_checkpoint_path=args.base_checkpoint,
        raw_checkpoint_path=args.raw_checkpoint,
        positive_rows_path=args.positive_rows,
        contrast_rows_path=args.contrast_rows,
        scenario_config_path=args.scenario_config,
        target_rows_path=args.target_rows,
        m912_summary_path=args.m912_summary,
        low_tail_rows_path=args.low_tail_rows,
        run_dir=args.run_dir,
        device=args.device,
        alphas=tuple(args.alphas),
    )
    for key, value in summary.items():
        if isinstance(value, (str, int, float, bool)):
            print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
