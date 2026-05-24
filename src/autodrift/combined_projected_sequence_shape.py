"""Run combined projected sequence grids and merge source-level evidence."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.grounded_capability_action_target_miner import SurfaceConfig, parse_surface_config
from autodrift.hidden_envelope_multiseed_gate import parse_checkpoint_spec
from autodrift.targeted_projected_sequence_shape import (
    TARGETED_FAMILIES,
    run_targeted_projected_sequence_shape,
    targeted_source_summary,
)


@dataclass(frozen=True)
class GridSpec:
    name: str
    source_ids: tuple[int, ...]
    primary_source_id: int
    secondary_source_id: int
    sentinel_source_ids: tuple[int, ...]
    sequence_lengths: tuple[int, ...]
    families: tuple[str, ...]
    steer_deltas: tuple[float, ...]
    throttle_deltas: tuple[float, ...]
    brake_deltas: tuple[float, ...]


def default_grid_specs() -> tuple[GridSpec, ...]:
    return (
        GridSpec(
            name="source8_recovery_grid",
            source_ids=(8, 0, 30),
            primary_source_id=8,
            secondary_source_id=0,
            sentinel_source_ids=(30,),
            sequence_lengths=(5, 7, 9),
            families=TARGETED_FAMILIES,
            steer_deltas=(-0.02, 0.0, 0.02, 0.03, 0.04, 0.05, 0.06),
            throttle_deltas=(-0.08, -0.07, -0.06, -0.05),
            brake_deltas=(0.02, 0.03, 0.04, 0.05, 0.06, 0.08),
        ),
        GridSpec(
            name="source7_preservation_grid",
            source_ids=(7,),
            primary_source_id=7,
            secondary_source_id=7,
            sentinel_source_ids=(),
            sequence_lengths=(3, 5, 7, 9),
            families=("targeted_constant_delta", "targeted_decay_hold", "targeted_late_brake_hold"),
            steer_deltas=(0.06, 0.08, 0.10),
            throttle_deltas=(-0.02, 0.0, 0.02),
            brake_deltas=(0.0, 0.02, 0.04),
        ),
    )


def _bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    if pd.isna(value):
        return False
    return bool(value)


def _read_grid_csv(path: Path, grid_name: str) -> list[dict[str, Any]]:
    frame = pd.read_csv(path)
    if frame.empty:
        return []
    frame.insert(0, "grid_name", grid_name)
    return frame.to_dict(orient="records")


def _source_rows_from_candidates(candidate_rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not candidate_rows:
        return pd.DataFrame(columns=["source_index"])
    frame = pd.DataFrame(candidate_rows)
    columns = [
        column
        for column in ["source_index", "source_tier", "surface", "target", "variant"]
        if column in frame.columns
    ]
    return frame[columns].drop_duplicates("source_index").reset_index(drop=True)


def combined_source_summary(
    candidate_rows: list[dict[str, Any]],
    baseline_source_summary: pd.DataFrame,
) -> list[dict[str, Any]]:
    source_rows = _source_rows_from_candidates(candidate_rows)
    summary = targeted_source_summary(candidate_rows, baseline_source_summary, source_rows)
    for row in summary:
        source_candidates = [
            item for item in candidate_rows
            if int(item.get("source_index", -1)) == int(row["source_index"])
        ]
        accepted_grid_names = sorted(
            {
                str(item.get("grid_name", ""))
                for item in source_candidates
                if _bool(item.get("accepted", False))
            }
        )
        row["accepted_grid_names"] = ";".join(accepted_grid_names)
        row["has_acceptance"] = bool(int(row.get("accepted_after_projection", 0)) > 0)
    return summary


def run_combined_projected_sequence_shape(
    *,
    checkpoint_path: Path,
    source_table_csv: Path,
    baseline_source_summary_csv: Path,
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
    baseline_source_summary = pd.read_csv(baseline_source_summary_csv)
    all_candidate_rows: list[dict[str, Any]] = []
    all_accepted_rows: list[dict[str, Any]] = []
    grid_summaries: list[dict[str, Any]] = []
    for spec in default_grid_specs():
        grid_dir = run_dir / spec.name
        grid_summary = run_targeted_projected_sequence_shape(
            checkpoint_path=checkpoint_path,
            source_table_csv=source_table_csv,
            baseline_source_summary_csv=baseline_source_summary_csv,
            source_ids=spec.source_ids,
            primary_source_id=spec.primary_source_id,
            secondary_source_id=spec.secondary_source_id,
            sentinel_source_ids=spec.sentinel_source_ids,
            surface_configs=surface_configs,
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
            device=device,
            run_dir=grid_dir,
        )
        grid_summaries.append({"grid_name": spec.name, **grid_summary})
        all_candidate_rows.extend(_read_grid_csv(grid_dir / "targeted_projected_candidates.csv", spec.name))
        all_accepted_rows.extend(_read_grid_csv(grid_dir / "accepted_targeted_sequences.csv", spec.name))

    source_summary = combined_source_summary(all_candidate_rows, baseline_source_summary)
    source_frame = pd.DataFrame(source_summary)
    candidate_frame = pd.DataFrame(all_candidate_rows)
    accepted_frame = pd.DataFrame(all_accepted_rows)
    write_csv_rows(run_dir / "combined_projected_candidates.csv", all_candidate_rows)
    write_csv_rows(run_dir / "accepted_combined_sequences.csv", all_accepted_rows)
    write_csv_rows(run_dir / "source_recovery_summary.csv", source_summary)

    trust_ok = True
    if not candidate_frame.empty:
        trust_ok = bool(
            (candidate_frame["sequence_mean_l2"] <= float(sequence_mean_l2_limit) + 1e-8).all()
            and (candidate_frame["sequence_max_l2"] <= float(sequence_max_l2_limit) + 1e-8).all()
            and (candidate_frame["max_delta_delta_l2"] <= float(max_delta_delta_l2_limit) + 1e-8).all()
        )
    accepted_by_source = (
        {str(key): int(value) for key, value in accepted_frame["source_index"].value_counts().to_dict().items()}
        if not accepted_frame.empty
        else {}
    )
    accepted_by_grid = (
        {str(key): int(value) for key, value in accepted_frame["grid_name"].value_counts().to_dict().items()}
        if not accepted_frame.empty
        else {}
    )

    def _source_has(source_index: int) -> bool:
        if source_frame.empty:
            return False
        rows = source_frame[source_frame["source_index"].astype(int) == int(source_index)]
        return bool(not rows.empty and rows.iloc[0].get("has_acceptance", False))

    summary = {
        "run_type": "combined_projected_sequence_shape",
        "checkpoint": checkpoint_path,
        "source_table_csv": source_table_csv,
        "baseline_source_summary_csv": baseline_source_summary_csv,
        "grid_names": [spec.name for spec in default_grid_specs()],
        "grid_summaries": grid_summaries,
        "candidate_rollouts": int(len(all_candidate_rows)),
        "accepted_combined_candidates": int(len(all_accepted_rows)),
        "accepted_counts_by_source": accepted_by_source,
        "accepted_counts_by_grid": accepted_by_grid,
        "source8_recovered": _source_has(8),
        "source0_recovered": _source_has(0),
        "source7_recovered": _source_has(7),
        "source30_preserved": _source_has(30),
        "all_four_sources_have_acceptance": all(_source_has(source_id) for source_id in [8, 0, 7, 30]),
        "trust_limits_preserved": trust_ok,
        "diagnostic_only": True,
        "labels_enter_actor_input": False,
        "actor_parameters_changed": False,
        "ppo_used": False,
        "promoted": False,
        "optimizer_admission": False,
        "target_acceptance_thresholds_changed": False,
        "trust_regions_changed": False,
        "combined_projected_candidates_csv": run_dir / "combined_projected_candidates.csv",
        "accepted_combined_sequences_csv": run_dir / "accepted_combined_sequences.csv",
        "source_recovery_summary_csv": run_dir / "source_recovery_summary.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run combined source-preserving projected sequence grids.")
    parser.add_argument("--checkpoint-policy", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--source-table", type=Path, required=True)
    parser.add_argument("--baseline-source-summary", type=Path, required=True)
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

    run_dir = args.run_dir or make_run_dir(prefix="combined_projected_sequence_shape")
    summary = run_combined_projected_sequence_shape(
        checkpoint_path=args.checkpoint_policy.path,
        source_table_csv=args.source_table,
        baseline_source_summary_csv=args.baseline_source_summary,
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
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
