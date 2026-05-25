"""Materialize controlled-fusion candidate checkpoints and exact-check them."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoint_interpolation import write_interpolation_sweep
from autodrift.public_base_controlled_fusion_raw_direction_feasibility import (
    run_controlled_fusion_raw_direction_feasibility,
)
from autodrift.v4_sequence_objective_probe import _parse_float_list


def _alpha_token(alpha: float) -> str:
    text = f"{float(alpha):.9f}".rstrip("0").rstrip(".")
    return text.replace(".", "_")


def classify_controlled_fusion_candidate_compatibility(
    *,
    materialized_checkpoint_count: int,
    expected_checkpoint_count: int,
    exact_candidate_count: int,
    primary_candidate_exact_pass: bool,
    forbidden_parameter_changed: bool,
    training_started: bool,
    optimizer_started: bool,
    replay_used: bool,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if (
        bool(forbidden_parameter_changed)
        or bool(training_started)
        or bool(optimizer_started)
        or bool(replay_used)
        or bool(ppo_used)
        or bool(promoted)
    ):
        return "public_base_controlled_fusion_candidate_compatibility_contract_artifact"
    if int(materialized_checkpoint_count) != int(expected_checkpoint_count):
        return "public_base_controlled_fusion_candidate_compatibility_materialization_failed"
    if bool(primary_candidate_exact_pass):
        return "public_base_controlled_fusion_candidate_compatibility_primary_candidate"
    if int(exact_candidate_count) > 0:
        return "public_base_controlled_fusion_candidate_compatibility_backup_candidate"
    return "public_base_controlled_fusion_candidate_compatibility_exact_regression"


def run_controlled_fusion_candidate_compatibility(
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
    candidate_alphas: tuple[float, ...],
    primary_alpha: float,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    interpolation_dir = run_dir / "interpolation"
    interpolation_manifest = write_interpolation_sweep(
        run_dir=interpolation_dir,
        base_checkpoint_path=base_checkpoint_path,
        target_checkpoint_path=raw_checkpoint_path,
        alphas=[float(alpha) for alpha in candidate_alphas],
        base_label="m399_public_base",
        target_label="m940_boundary_raw",
        label_prefix="m944cf",
    )
    candidate_rows: list[dict[str, Any]] = []
    exact_summaries: list[dict[str, Any]] = []
    for checkpoint_row in interpolation_manifest["checkpoints"]:
        candidate_alpha = float(checkpoint_row["alpha"])
        exact_dir = run_dir / f"alpha_{_alpha_token(candidate_alpha)}_exact"
        exact_summary = run_controlled_fusion_raw_direction_feasibility(
            base_checkpoint_path=base_checkpoint_path,
            raw_checkpoint_path=Path(checkpoint_row["path"]),
            positive_rows_path=positive_rows_path,
            contrast_rows_path=contrast_rows_path,
            scenario_config_path=scenario_config_path,
            target_rows_path=target_rows_path,
            m912_summary_path=m912_summary_path,
            low_tail_rows_path=low_tail_rows_path,
            run_dir=exact_dir,
            device=device,
            alphas=(1.0,),
        )
        exact_summaries.append(exact_summary)
        exact_pass = bool(
            int(exact_summary.get("strict_candidate_count", 0)) > 0
            and not bool(exact_summary.get("forbidden_parameter_changed_between_checkpoints", True))
            and not bool(exact_summary.get("training_started", True))
            and not bool(exact_summary.get("replay_used", True))
            and not bool(exact_summary.get("ppo_used", True))
            and not bool(exact_summary.get("promoted", True))
        )
        candidate_rows.append(
            {
                "candidate_alpha": candidate_alpha,
                "policy_label": checkpoint_row.get("policy_label", ""),
                "checkpoint_path": checkpoint_row["path"],
                "exact_run_dir": str(exact_dir),
                "exact_candidate_pass": exact_pass,
                "strict_candidate_count": int(exact_summary.get("strict_candidate_count", 0)),
                "low_tail_effect_candidate_count": int(exact_summary.get("low_tail_effect_candidate_count", 0)),
                "target_tolerance_candidate_count": int(exact_summary.get("target_tolerance_candidate_count", 0)),
                "forbidden_parameter_changed_between_checkpoints": bool(
                    exact_summary.get("forbidden_parameter_changed_between_checkpoints", True)
                ),
                "best_candidate": exact_summary.get("best_candidate", {}),
                "result_class": exact_summary.get("result_class", ""),
            }
        )
    primary_alpha_value = float(primary_alpha)
    primary_rows = [row for row in candidate_rows if abs(float(row["candidate_alpha"]) - primary_alpha_value) <= 1e-9]
    primary_candidate_exact_pass = bool(primary_rows and primary_rows[0]["exact_candidate_pass"])
    exact_candidate_count = sum(1 for row in candidate_rows if bool(row["exact_candidate_pass"]))
    forbidden_changed = any(
        bool(summary.get("forbidden_parameter_changed_between_checkpoints", True)) for summary in exact_summaries
    )
    training_started = any(bool(summary.get("training_started", False)) for summary in exact_summaries)
    optimizer_started = any(bool(summary.get("optimizer_started", False)) for summary in exact_summaries)
    replay_used = any(bool(summary.get("replay_used", False)) for summary in exact_summaries)
    ppo_used = any(bool(summary.get("ppo_used", False)) for summary in exact_summaries)
    promoted = any(bool(summary.get("promoted", False)) for summary in exact_summaries)
    result_class = classify_controlled_fusion_candidate_compatibility(
        materialized_checkpoint_count=len(interpolation_manifest["checkpoints"]),
        expected_checkpoint_count=len(candidate_alphas),
        exact_candidate_count=exact_candidate_count,
        primary_candidate_exact_pass=primary_candidate_exact_pass,
        forbidden_parameter_changed=forbidden_changed,
        training_started=training_started,
        optimizer_started=optimizer_started,
        replay_used=replay_used,
        ppo_used=ppo_used,
        promoted=promoted,
    )
    write_csv_rows(run_dir / "candidate_compatibility.csv", candidate_rows)
    summary = {
        "run_type": "public_base_controlled_fusion_candidate_compatibility",
        "base_checkpoint": base_checkpoint_path,
        "raw_checkpoint": raw_checkpoint_path,
        "positive_rows_input": positive_rows_path,
        "contrast_rows_input": contrast_rows_path,
        "scenario_config": scenario_config_path,
        "target_rows": target_rows_path,
        "m912_summary": m912_summary_path,
        "low_tail_rows": low_tail_rows_path,
        "candidate_alphas": [float(alpha) for alpha in candidate_alphas],
        "primary_alpha": primary_alpha_value,
        "materialized_checkpoint_count": int(len(interpolation_manifest["checkpoints"])),
        "expected_checkpoint_count": int(len(candidate_alphas)),
        "exact_candidate_count": int(exact_candidate_count),
        "primary_candidate_exact_pass": primary_candidate_exact_pass,
        "backup_candidate_exact_pass_count": int(
            sum(
                1
                for row in candidate_rows
                if bool(row["exact_candidate_pass"]) and abs(float(row["candidate_alpha"]) - primary_alpha_value) > 1e-9
            )
        ),
        "forbidden_parameter_changed": bool(forbidden_changed),
        "training_started": bool(training_started),
        "optimizer_started": bool(optimizer_started),
        "replay_used": bool(replay_used),
        "ppo_used": bool(ppo_used),
        "promoted": bool(promoted),
        "checkpoint_promoted": False,
        "exact_no_update_used": True,
        "m880_exact_used": False,
        "candidate_rows": candidate_rows,
        "primary_candidate_row": primary_rows[0] if primary_rows else {},
        "interpolation_manifest": interpolation_dir / "manifest.json",
        "candidate_compatibility_csv": run_dir / "candidate_compatibility.csv",
        "result_class": result_class,
        "summary_json": run_dir / "summary.json",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize controlled-fusion candidates and exact-check them.")
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
    parser.add_argument("--candidate-alphas", type=_parse_float_list, required=True)
    parser.add_argument("--primary-alpha", type=float, required=True)
    args = parser.parse_args()
    summary = run_controlled_fusion_candidate_compatibility(
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
        candidate_alphas=tuple(args.candidate_alphas),
        primary_alpha=float(args.primary_alpha),
    )
    for key, value in summary.items():
        if isinstance(value, (str, int, float, bool)):
            print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
