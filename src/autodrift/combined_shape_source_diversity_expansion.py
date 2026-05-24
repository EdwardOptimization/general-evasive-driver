"""Expand combined projected sequence grids across source-diverse near misses."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.boundary_conditioned_grounded_target_miner import _diversity, load_boundary_source_rows
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.grounded_capability_action_target_miner import SurfaceConfig, parse_surface_config
from autodrift.hidden_envelope_multiseed_gate import parse_checkpoint_spec
from autodrift.targeted_projected_sequence_shape import TARGETED_FAMILIES
from autodrift.train_ppo import resolve_device
from autodrift.trust_projected_sequence_shape import (
    _bool,
    _empty_float_stat,
    mine_projected_sequences_for_surface,
    source_recovery_summary,
)


@dataclass(frozen=True)
class ShapeGridSpec:
    name: str
    sequence_lengths: tuple[int, ...]
    families: tuple[str, ...]
    steer_deltas: tuple[float, ...]
    throttle_deltas: tuple[float, ...]
    brake_deltas: tuple[float, ...]


def default_shape_grid_specs() -> tuple[ShapeGridSpec, ...]:
    return (
        ShapeGridSpec(
            name="source8_recovery_style",
            sequence_lengths=(5, 7, 9),
            families=TARGETED_FAMILIES,
            steer_deltas=(-0.02, 0.0, 0.02, 0.03, 0.04, 0.05, 0.06),
            throttle_deltas=(-0.08, -0.07, -0.06, -0.05),
            brake_deltas=(0.02, 0.03, 0.04, 0.05, 0.06, 0.08),
        ),
        ShapeGridSpec(
            name="source7_preservation_style",
            sequence_lengths=(3, 5, 7, 9),
            families=("targeted_constant_delta", "targeted_decay_hold", "targeted_late_brake_hold"),
            steer_deltas=(0.06, 0.08, 0.10),
            throttle_deltas=(-0.02, 0.0, 0.02),
            brake_deltas=(0.0, 0.02, 0.04),
        ),
    )


def select_trust_primary_non_collision_sources(
    near_miss_sources: pd.DataFrame,
    source_rows: pd.DataFrame,
) -> pd.DataFrame:
    required = {
        "source_index",
        "best_primary_failure",
        "has_trust_near_miss",
        "has_collision_near_miss",
    }
    missing = sorted(required.difference(near_miss_sources.columns))
    if missing:
        raise ValueError("near-miss sources missing columns: " + ", ".join(missing))
    selected_near = near_miss_sources[
        near_miss_sources["has_trust_near_miss"].map(_bool)
        & ~near_miss_sources["has_collision_near_miss"].map(_bool)
        & near_miss_sources["best_primary_failure"].isin(["mean_l2_excess", "max_l2_excess"])
    ].copy()
    ordered_ids = selected_near["source_index"].astype(int).tolist()
    selected = source_rows[source_rows["source_index"].astype(int).isin(ordered_ids)].copy()
    found = set(selected["source_index"].astype(int).tolist())
    missing_ids = [source_id for source_id in ordered_ids if source_id not in found]
    if missing_ids:
        raise ValueError(f"source ids not found in source table: {missing_ids}")
    selected["_source_order"] = selected["source_index"].astype(int).map(
        {source_id: index for index, source_id in enumerate(ordered_ids)}
    )
    selected["source_diversity_expansion_focus"] = True
    return selected.sort_values("_source_order").drop(columns=["_source_order"]).reset_index(drop=True)


def _source_rows_for_source_ids(source_rows: pd.DataFrame, source_ids: set[int]) -> pd.DataFrame:
    if source_rows.empty or not source_ids:
        return source_rows.iloc[0:0].copy()
    return source_rows[source_rows["source_index"].astype(int).isin(source_ids)].drop_duplicates("source_index")


def _diversity_row(label: str, rows: pd.DataFrame) -> dict[str, Any]:
    diversity = _diversity(rows)
    return {"set": label, **diversity}


def source_diversity_summary(
    *,
    selected_source_rows: pd.DataFrame,
    source_summary_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    source_summary = pd.DataFrame(source_summary_rows)
    accepted_ids: set[int] = set()
    if not source_summary.empty:
        accepted_ids = set(
            source_summary[source_summary["accepted_after_projection"].astype(int) > 0]["source_index"].astype(int)
        )
    accepted_source_rows = _source_rows_for_source_ids(selected_source_rows, accepted_ids)
    return [
        _diversity_row("selected_sources", selected_source_rows),
        _diversity_row("accepted_sources", accepted_source_rows),
    ]


def admission_metrics(
    *,
    selected_source_rows: pd.DataFrame,
    source_summary_rows: list[dict[str, Any]],
    trust_limits_preserved: bool,
) -> dict[str, Any]:
    source_summary = pd.DataFrame(source_summary_rows)
    accepted_ids: set[int] = set()
    if not source_summary.empty:
        accepted_ids = set(
            source_summary[source_summary["accepted_after_projection"].astype(int) > 0]["source_index"].astype(int)
        )
    accepted_source_rows = _source_rows_for_source_ids(selected_source_rows, accepted_ids)
    diversity = _diversity(accepted_source_rows)
    accepted_source_rows_count = int(len(accepted_source_rows))
    accepted_surfaces = int(diversity["surfaces"])
    accepted_targets = int(diversity["targets"])
    accepted_unique_physical_pairs = int(diversity["unique_physical_pairs"])
    accepted_unique_left_seeds = int(diversity["unique_left_seeds"])
    target_corpus_admission_candidate = bool(
        trust_limits_preserved
        and accepted_source_rows_count >= 8
        and accepted_unique_physical_pairs >= 6
        and accepted_unique_left_seeds >= 6
        and accepted_surfaces >= 2
        and accepted_targets >= 2
    )
    return {
        "accepted_source_rows": accepted_source_rows_count,
        "accepted_unique_physical_pairs": accepted_unique_physical_pairs,
        "accepted_unique_left_seeds": accepted_unique_left_seeds,
        "accepted_surfaces": accepted_surfaces,
        "accepted_targets": accepted_targets,
        "accepted_variants": int(diversity["variants"]),
        "target_corpus_admission_candidate": target_corpus_admission_candidate,
    }


def _value_counts(frame: pd.DataFrame, column: str) -> dict[str, int]:
    if frame.empty or column not in frame.columns:
        return {}
    return {str(key): int(value) for key, value in frame[column].value_counts().to_dict().items()}


def _readable_source_ids(rows: pd.DataFrame) -> list[int]:
    return rows["source_index"].astype(int).tolist() if not rows.empty else []


def run_combined_shape_source_diversity_expansion(
    *,
    checkpoint_path: Path,
    source_table_csv: Path,
    near_miss_sources_csv: Path,
    surface_configs: tuple[SurfaceConfig, ...],
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
    near_miss_sources = pd.read_csv(near_miss_sources_csv)
    source_rows = load_boundary_source_rows(source_table_csv)
    selected_source_rows = select_trust_primary_non_collision_sources(near_miss_sources, source_rows)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    surface_config_by_name = {item.surface: item.env_config_path for item in surface_configs}
    missing_configs = (
        sorted(set(selected_source_rows["surface"].astype(str)).difference(surface_config_by_name))
        if not selected_source_rows.empty
        else []
    )
    if missing_configs:
        raise ValueError(f"missing env configs for surfaces: {missing_configs}")

    all_candidate_rows: list[dict[str, Any]] = []
    grid_summaries: list[dict[str, Any]] = []
    for spec in default_shape_grid_specs():
        grid_candidate_rows: list[dict[str, Any]] = []
        for surface, surface_rows in selected_source_rows.groupby("surface", observed=True):
            grid_candidate_rows.extend(
                mine_projected_sequences_for_surface(
                    model=model,
                    env_config_path=surface_config_by_name[str(surface)],
                    rows=surface_rows.reset_index(drop=True),
                    near_miss_sources=near_miss_sources,
                    sequence_lengths=spec.sequence_lengths,
                    families=spec.families,
                    steer_deltas=spec.steer_deltas,
                    throttle_deltas=spec.throttle_deltas,
                    brake_deltas=spec.brake_deltas,
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
        for row in grid_candidate_rows:
            row["grid_name"] = spec.name
        grid_frame = pd.DataFrame(grid_candidate_rows)
        accepted_grid = grid_frame[grid_frame["accepted"].map(_bool)] if not grid_frame.empty else pd.DataFrame()
        grid_summaries.append(
            {
                "grid_name": spec.name,
                "candidate_rollouts": int(len(grid_candidate_rows)),
                "accepted_candidates": int(len(accepted_grid)),
                "accepted_counts_by_source": _value_counts(accepted_grid, "source_index"),
            }
        )
        all_candidate_rows.extend(grid_candidate_rows)

    candidate_frame = pd.DataFrame(all_candidate_rows)
    accepted_rows = [row for row in all_candidate_rows if _bool(row.get("accepted", False))]
    accepted_frame = pd.DataFrame(accepted_rows)
    source_summary_rows = source_recovery_summary(all_candidate_rows, near_miss_sources)
    diversity_rows = source_diversity_summary(
        selected_source_rows=selected_source_rows,
        source_summary_rows=source_summary_rows,
    )
    trust_ok = True
    if not candidate_frame.empty:
        trust_ok = bool(
            (candidate_frame["sequence_mean_l2"] <= float(sequence_mean_l2_limit) + 1e-8).all()
            and (candidate_frame["sequence_max_l2"] <= float(sequence_max_l2_limit) + 1e-8).all()
            and (candidate_frame["max_delta_delta_l2"] <= float(max_delta_delta_l2_limit) + 1e-8).all()
        )
    metrics = admission_metrics(
        selected_source_rows=selected_source_rows,
        source_summary_rows=source_summary_rows,
        trust_limits_preserved=trust_ok,
    )

    write_csv_rows(run_dir / "selected_expanded_source_rows.csv", selected_source_rows.to_dict(orient="records"))
    write_csv_rows(run_dir / "expanded_projected_candidates.csv", all_candidate_rows)
    write_csv_rows(run_dir / "accepted_expanded_sequences.csv", accepted_rows)
    write_csv_rows(run_dir / "source_recovery_summary.csv", source_summary_rows)
    write_csv_rows(run_dir / "source_diversity_summary.csv", diversity_rows)

    summary = {
        "run_type": "combined_shape_source_diversity_expansion",
        "checkpoint": checkpoint_path,
        "source_table_csv": source_table_csv,
        "near_miss_sources_csv": near_miss_sources_csv,
        "surface_configs": {item.surface: item.env_config_path for item in surface_configs},
        "grid_names": [spec.name for spec in default_shape_grid_specs()],
        "grid_summaries": grid_summaries,
        "selected_source_rows": int(len(selected_source_rows)),
        "selected_source_ids": _readable_source_ids(selected_source_rows),
        "source_row_diversity": _diversity(selected_source_rows),
        "candidate_rollouts": int(len(all_candidate_rows)),
        "accepted_expanded_candidates": int(len(accepted_rows)),
        "accepted_counts_by_source": _value_counts(accepted_frame, "source_index"),
        "accepted_counts_by_grid": _value_counts(accepted_frame, "grid_name"),
        "trust_limits_preserved": trust_ok,
        "candidate_margin_improvement_max": _empty_float_stat(candidate_frame, "margin_improvement", "max"),
        "candidate_margin_improvement_mean": _empty_float_stat(candidate_frame, "margin_improvement", "mean"),
        "accepted_margin_improvement_mean": _empty_float_stat(accepted_frame, "margin_improvement", "mean"),
        "accepted_margin_improvement_min": _empty_float_stat(accepted_frame, "margin_improvement", "min"),
        "accepted_margin_improvement_max": _empty_float_stat(accepted_frame, "margin_improvement", "max"),
        **metrics,
        "diagnostic_only": True,
        "labels_enter_actor_input": False,
        "actor_parameters_changed": False,
        "ppo_used": False,
        "promoted": False,
        "optimizer_admission": False,
        "target_acceptance_thresholds_changed": False,
        "trust_regions_changed": False,
        "selected_expanded_source_rows_csv": run_dir / "selected_expanded_source_rows.csv",
        "expanded_projected_candidates_csv": run_dir / "expanded_projected_candidates.csv",
        "accepted_expanded_sequences_csv": run_dir / "accepted_expanded_sequences.csv",
        "source_recovery_summary_csv": run_dir / "source_recovery_summary.csv",
        "source_diversity_summary_csv": run_dir / "source_diversity_summary.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run broad combined projected sequence source-diversity expansion.")
    parser.add_argument("--checkpoint-policy", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--source-table", type=Path, required=True)
    parser.add_argument("--near-miss-sources", type=Path, required=True)
    parser.add_argument("--surface-config", type=parse_surface_config, action="append", required=True)
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

    run_dir = args.run_dir or make_run_dir(prefix="combined_shape_source_diversity_expansion")
    summary = run_combined_shape_source_diversity_expansion(
        checkpoint_path=args.checkpoint_policy.path,
        source_table_csv=args.source_table,
        near_miss_sources_csv=args.near_miss_sources,
        surface_configs=tuple(args.surface_config),
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
    print(f"run_dir={run_dir}")
    print(f"target_corpus_admission_candidate={summary['target_corpus_admission_candidate']}")


if __name__ == "__main__":
    main()
