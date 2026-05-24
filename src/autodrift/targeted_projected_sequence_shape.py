"""Run explicit source-id targeted projected sequence candidate searches."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.boundary_conditioned_grounded_target_miner import _diversity, _empty_float_stat, load_boundary_source_rows
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.grounded_capability_action_target_miner import SurfaceConfig, parse_surface_config
from autodrift.hidden_envelope_multiseed_gate import parse_checkpoint_spec
from autodrift.sequence_target_miner import parse_int_list
from autodrift.terminal_margin_recovery_anchor import parse_float_list
from autodrift.train_ppo import resolve_device
from autodrift.trust_projected_sequence_shape import (
    mine_projected_sequences_for_surface,
    source_recovery_summary,
)


TARGETED_FAMILIES = (
    "targeted_constant_delta",
    "targeted_decay_hold",
    "targeted_late_brake_hold",
    "targeted_steer_build_brake_hold",
    "targeted_smoothstep_hold",
)


def _bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    if pd.isna(value):
        return False
    return bool(value)


def filter_source_ids(source_rows: pd.DataFrame, source_ids: tuple[int, ...]) -> pd.DataFrame:
    if "source_index" not in source_rows.columns:
        raise ValueError("source rows missing source_index")
    ids = [int(value) for value in source_ids]
    selected = source_rows[source_rows["source_index"].astype(int).isin(ids)].copy()
    found = set(selected["source_index"].astype(int).tolist())
    missing = [value for value in ids if value not in found]
    if missing:
        raise ValueError(f"source ids not found: {missing}")
    selected["_source_order"] = selected["source_index"].astype(int).map({value: index for index, value in enumerate(ids)})
    return selected.sort_values("_source_order").drop(columns=["_source_order"]).reset_index(drop=True)


def baseline_summary_to_near_sources(
    baseline_source_summary: pd.DataFrame,
    source_rows: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    baseline_by_id = {
        int(row["source_index"]): dict(row)
        for _, row in baseline_source_summary.reset_index(drop=True).iterrows()
    }
    for _, source in source_rows.reset_index(drop=True).iterrows():
        source_index = int(source["source_index"])
        baseline = baseline_by_id.get(source_index, {})
        rows.append(
            {
                "source_index": source_index,
                "source_tier": str(source.get("source_tier", "")),
                "surface": str(source.get("surface", "")),
                "target": str(source.get("target", "")),
                "variant": str(source.get("variant", "")),
                "accepted_candidate_count": int(baseline.get("accepted_after_projection", 0) or 0),
                "best_primary_failure": "mean_l2_excess",
                "has_collision_near_miss": False,
            }
        )
    return pd.DataFrame(rows)


def targeted_source_summary(
    candidate_rows: list[dict[str, Any]],
    baseline_source_summary: pd.DataFrame,
    source_rows: pd.DataFrame,
) -> list[dict[str, Any]]:
    near_sources = baseline_summary_to_near_sources(baseline_source_summary, source_rows)
    summary = source_recovery_summary(candidate_rows, near_sources)
    baseline_by_id = {
        int(row["source_index"]): dict(row)
        for _, row in baseline_source_summary.reset_index(drop=True).iterrows()
    }
    for row in summary:
        baseline = baseline_by_id.get(int(row["source_index"]), {})
        baseline_after = int(baseline.get("accepted_after_projection", 0) or 0)
        baseline_best = float(baseline.get("best_projected_margin_improvement", float("nan")))
        row["baseline_accepted_after_projection"] = baseline_after
        row["baseline_best_margin_improvement"] = baseline_best
        row["targeted_regression"] = bool(baseline_after > 0 and int(row["accepted_after_projection"]) == 0)
        row["best_margin_delta_vs_m630"] = (
            float(row["best_projected_margin_improvement"]) - baseline_best
            if np.isfinite(baseline_best)
            else float("nan")
        )
    return summary


def run_targeted_projected_sequence_shape(
    *,
    checkpoint_path: Path,
    source_table_csv: Path,
    baseline_source_summary_csv: Path,
    source_ids: tuple[int, ...],
    primary_source_id: int,
    secondary_source_id: int,
    sentinel_source_ids: tuple[int, ...],
    surface_configs: tuple[SurfaceConfig, ...],
    sequence_lengths: tuple[int, ...],
    families: tuple[str, ...],
    steer_deltas: tuple[float, ...],
    throttle_deltas: tuple[float, ...],
    brake_deltas: tuple[float, ...],
    delay_steps: int,
    per_step_action_l2: float,
    sequence_mean_l2_limit: float,
    sequence_max_l2_limit: float,
    max_delta_delta_l2_limit: float,
    min_margin_improvement: float,
    min_risk_improvement: float,
    max_continuation_steps: int,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    source_rows = filter_source_ids(load_boundary_source_rows(source_table_csv), source_ids)
    baseline_source_summary = pd.read_csv(baseline_source_summary_csv)
    near_sources = baseline_summary_to_near_sources(baseline_source_summary, source_rows)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    surface_config_by_name = {item.surface: item.env_config_path for item in surface_configs}
    missing_configs = sorted(set(source_rows["surface"].astype(str)).difference(surface_config_by_name)) if not source_rows.empty else []
    if missing_configs:
        raise ValueError(f"missing env configs for surfaces: {missing_configs}")

    candidate_rows: list[dict[str, Any]] = []
    for surface, surface_rows in source_rows.groupby("surface", observed=True):
        candidate_rows.extend(
            mine_projected_sequences_for_surface(
                model=model,
                env_config_path=surface_config_by_name[str(surface)],
                rows=surface_rows.reset_index(drop=True),
                near_miss_sources=near_sources,
                sequence_lengths=sequence_lengths,
                families=families,
                steer_deltas=steer_deltas,
                throttle_deltas=throttle_deltas,
                brake_deltas=brake_deltas,
                delay_steps=delay_steps,
                per_step_action_l2=per_step_action_l2,
                sequence_mean_l2_limit=sequence_mean_l2_limit,
                sequence_max_l2_limit=sequence_max_l2_limit,
                max_delta_delta_l2_limit=max_delta_delta_l2_limit,
                min_margin_improvement=min_margin_improvement,
                min_risk_improvement=min_risk_improvement,
                max_continuation_steps=max_continuation_steps,
                device=resolved_device,
            )
        )

    source_summary = targeted_source_summary(candidate_rows, baseline_source_summary, source_rows)
    accepted_rows = [row for row in candidate_rows if _bool(row.get("accepted", False))]
    candidate_frame = pd.DataFrame(candidate_rows)
    accepted_frame = pd.DataFrame(accepted_rows)
    source_summary_frame = pd.DataFrame(source_summary)
    write_csv_rows(run_dir / "selected_targeted_source_rows.csv", source_rows.to_dict(orient="records"))
    write_csv_rows(run_dir / "targeted_projected_candidates.csv", candidate_rows)
    write_csv_rows(run_dir / "accepted_targeted_sequences.csv", accepted_rows)
    write_csv_rows(run_dir / "source_recovery_summary.csv", source_summary)

    trust_ok = True
    if not candidate_frame.empty:
        trust_ok = bool(
            (candidate_frame["sequence_mean_l2"] <= float(sequence_mean_l2_limit) + 1e-8).all()
            and (candidate_frame["sequence_max_l2"] <= float(sequence_max_l2_limit) + 1e-8).all()
            and (candidate_frame["max_delta_delta_l2"] <= float(max_delta_delta_l2_limit) + 1e-8).all()
        )

    by_source = {
        int(row["source_index"]): row
        for row in source_summary
    }
    primary = by_source.get(int(primary_source_id), {})
    secondary = by_source.get(int(secondary_source_id), {})
    sentinel_regressions = {
        str(source_id): bool(by_source.get(int(source_id), {}).get("targeted_regression", False))
        for source_id in sentinel_source_ids
    }
    summary = {
        "run_type": "targeted_projected_sequence_shape",
        "checkpoint": checkpoint_path,
        "source_table_csv": source_table_csv,
        "baseline_source_summary_csv": baseline_source_summary_csv,
        "surface_configs": {item.surface: item.env_config_path for item in surface_configs},
        "source_ids": source_ids,
        "primary_source_id": int(primary_source_id),
        "secondary_source_id": int(secondary_source_id),
        "sentinel_source_ids": sentinel_source_ids,
        "source_row_diversity": _diversity(source_rows),
        "accepted_targeted_diversity": _diversity(accepted_frame),
        "sequence_lengths": sequence_lengths,
        "families": families,
        "candidate_rollouts": int(len(candidate_rows)),
        "accepted_targeted_candidates": int(len(accepted_rows)),
        "source8_recovered": bool(primary.get("accepted_after_projection", 0) > 0),
        "source8_best_margin_improvement": float(primary.get("best_projected_margin_improvement", float("nan"))),
        "source0_best_margin_improvement": float(secondary.get("best_projected_margin_improvement", float("nan"))),
        "source7_regression": bool(sentinel_regressions.get("7", False)),
        "source30_regression": bool(sentinel_regressions.get("30", False)),
        "sentinel_regressions": sentinel_regressions,
        "trust_limits_preserved": trust_ok,
        "candidate_margin_improvement_max": _empty_float_stat(candidate_frame, "margin_improvement", "max"),
        "accepted_margin_improvement_mean": _empty_float_stat(accepted_frame, "margin_improvement", "mean"),
        "accepted_counts_by_source": (
            {str(key): int(value) for key, value in accepted_frame["source_index"].value_counts().to_dict().items()}
            if not accepted_frame.empty
            else {}
        ),
        "accepted_counts_by_family": (
            {str(key): int(value) for key, value in accepted_frame["family"].value_counts().to_dict().items()}
            if not accepted_frame.empty
            else {}
        ),
        "candidate_acceptance_reason_counts": (
            candidate_frame[candidate_frame["accepted"].map(_bool)]["rejection_reason"].value_counts().to_dict()
            if not candidate_frame.empty
            else {}
        ),
        "candidate_rejection_counts": (
            candidate_frame[~candidate_frame["accepted"].map(_bool)]["rejection_reason"].value_counts().to_dict()
            if not candidate_frame.empty
            else {}
        ),
        "diagnostic_only": True,
        "labels_enter_actor_input": False,
        "actor_parameters_changed": False,
        "ppo_used": False,
        "promoted": False,
        "optimizer_admission": False,
        "target_acceptance_thresholds_changed": False,
        "trust_regions_changed": False,
        "targeted_projected_candidates_csv": run_dir / "targeted_projected_candidates.csv",
        "accepted_targeted_sequences_csv": run_dir / "accepted_targeted_sequences.csv",
        "source_recovery_summary_csv": run_dir / "source_recovery_summary.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run targeted projected sequence shape search.")
    parser.add_argument("--checkpoint-policy", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--source-table", type=Path, required=True)
    parser.add_argument("--baseline-source-summary", type=Path, required=True)
    parser.add_argument("--source-ids", type=parse_int_list, required=True)
    parser.add_argument("--primary-source-id", type=int, required=True)
    parser.add_argument("--secondary-source-id", type=int, required=True)
    parser.add_argument("--sentinel-source-ids", type=parse_int_list, required=True)
    parser.add_argument("--surface-config", type=parse_surface_config, action="append", required=True)
    parser.add_argument("--sequence-lengths", type=parse_int_list, default=(5, 7, 9))
    parser.add_argument("--family", type=str, action="append", default=None)
    parser.add_argument("--steer-deltas", type=parse_float_list, default=(-0.02, 0.0, 0.02, 0.03, 0.04, 0.05, 0.06))
    parser.add_argument("--throttle-deltas", type=parse_float_list, default=(-0.08, -0.07, -0.06, -0.05))
    parser.add_argument("--brake-deltas", type=parse_float_list, default=(0.02, 0.03, 0.04, 0.05, 0.06, 0.08))
    parser.add_argument("--delay-steps", type=int, default=2)
    parser.add_argument("--per-step-action-l2", type=float, default=0.10)
    parser.add_argument("--sequence-mean-l2-limit", type=float, default=0.08)
    parser.add_argument("--sequence-max-l2-limit", type=float, default=0.10)
    parser.add_argument("--max-delta-delta-l2-limit", type=float, default=0.08)
    parser.add_argument("--min-margin-improvement", type=float, default=0.02)
    parser.add_argument("--min-risk-improvement", type=float, default=0.05)
    parser.add_argument("--max-continuation-steps", type=int, default=80)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    families = tuple(args.family or TARGETED_FAMILIES)
    run_dir = args.run_dir or make_run_dir(prefix="targeted_projected_sequence_shape")
    summary = run_targeted_projected_sequence_shape(
        checkpoint_path=args.checkpoint_policy.path,
        source_table_csv=args.source_table,
        baseline_source_summary_csv=args.baseline_source_summary,
        source_ids=tuple(args.source_ids),
        primary_source_id=args.primary_source_id,
        secondary_source_id=args.secondary_source_id,
        sentinel_source_ids=tuple(args.sentinel_source_ids),
        surface_configs=tuple(args.surface_config),
        sequence_lengths=tuple(args.sequence_lengths),
        families=families,
        steer_deltas=args.steer_deltas,
        throttle_deltas=args.throttle_deltas,
        brake_deltas=args.brake_deltas,
        delay_steps=args.delay_steps,
        per_step_action_l2=args.per_step_action_l2,
        sequence_mean_l2_limit=args.sequence_mean_l2_limit,
        sequence_max_l2_limit=args.sequence_max_l2_limit,
        max_delta_delta_l2_limit=args.max_delta_delta_l2_limit,
        min_margin_improvement=args.min_margin_improvement,
        min_risk_improvement=args.min_risk_improvement,
        max_continuation_steps=args.max_continuation_steps,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
