"""Run grounded target search on boundary-conditioned source rows."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.grounded_capability_action_target_miner import (
    ACCEPTED_TARGET_FIELDNAMES,
    UNACCEPTED_ROW_FIELDNAMES,
    SurfaceConfig,
    _finite_float,
    mine_targets_for_surface,
    parse_surface_config,
    write_target_corpus,
)
from autodrift.hidden_envelope_multiseed_gate import parse_checkpoint_spec
from autodrift.terminal_margin_recovery_anchor import parse_float_list
from autodrift.train_ppo import resolve_device


def load_boundary_source_rows(path: Path) -> pd.DataFrame:
    rows = pd.read_csv(path)
    required = {
        "source_index",
        "coupling_row_index",
        "surface",
        "variant",
        "target",
        "left_seed",
        "left_step",
        "right_seed",
        "right_step",
        "capability_z_distance",
        "action_distance",
        "coupling_gap",
    }
    missing = sorted(required.difference(rows.columns))
    if missing:
        raise ValueError("boundary source rows missing columns: " + ", ".join(missing))
    result = rows.copy().reset_index(drop=True)
    result.insert(0, "selected_source_index", result["source_index"].astype(int).to_numpy())
    return result


def _empty_float_stat(frame: pd.DataFrame, column: str, fn: str) -> float:
    if frame.empty:
        return float("nan")
    series = frame[column].astype(float)
    if fn == "mean":
        return float(series.mean())
    if fn == "min":
        return float(series.min())
    if fn == "max":
        return float(series.max())
    raise ValueError(f"unknown float stat: {fn}")


def _diversity(rows: pd.DataFrame) -> dict[str, Any]:
    if rows.empty:
        return {
            "rows": 0,
            "unique_physical_pairs": 0,
            "unique_left_seeds": 0,
            "surfaces": 0,
            "variants": 0,
            "targets": 0,
            "max_physical_pair_dominance": 0.0,
        }
    pair_cols = ["left_seed", "left_step", "right_seed", "right_step"]
    pair_counts = rows.groupby(pair_cols, observed=True).size()
    return {
        "rows": int(len(rows)),
        "unique_physical_pairs": int(len(pair_counts)),
        "unique_left_seeds": int(rows["left_seed"].nunique()),
        "surfaces": int(rows["surface"].nunique()),
        "variants": int(rows["variant"].nunique()),
        "targets": int(rows["target"].nunique()),
        "max_physical_pair_dominance": float(pair_counts.max() / len(rows)) if len(rows) else 0.0,
    }


def run_boundary_conditioned_grounded_target_miner(
    *,
    checkpoint_path: Path,
    boundary_source_rows_csv: Path,
    surface_configs: tuple[SurfaceConfig, ...],
    delay_steps: int,
    steer_deltas: tuple[float, ...],
    throttle_deltas: tuple[float, ...],
    brake_deltas: tuple[float, ...],
    min_margin_improvement: float,
    min_risk_improvement: float,
    max_action_l2: float,
    max_continuation_steps: int,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    source_rows = load_boundary_source_rows(boundary_source_rows_csv)
    surface_config_by_name = {item.surface: item.env_config_path for item in surface_configs}
    missing_configs = sorted(set(source_rows["surface"].astype(str)).difference(surface_config_by_name)) if not source_rows.empty else []
    if missing_configs:
        raise ValueError(f"missing env configs for surfaces: {missing_configs}")

    candidate_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    unaccepted_rows: list[dict[str, Any]] = []
    corpus: dict[str, list[np.ndarray]] = {
        "observations": [],
        "normal_hidden": [],
        "variant_hidden": [],
        "target_actions": [],
        "normal_base_actions": [],
        "variant_base_actions": [],
    }
    for surface, surface_rows in source_rows.groupby("surface", observed=True):
        surface_candidate_rows, surface_accepted_rows, surface_unaccepted_rows, surface_corpus = mine_targets_for_surface(
            model=model,
            env_config_path=surface_config_by_name[str(surface)],
            rows=surface_rows.reset_index(drop=True),
            delay_steps=delay_steps,
            steer_deltas=steer_deltas,
            throttle_deltas=throttle_deltas,
            brake_deltas=brake_deltas,
            min_margin_improvement=min_margin_improvement,
            min_risk_improvement=min_risk_improvement,
            max_action_l2=max_action_l2,
            max_continuation_steps=max_continuation_steps,
            device=resolved_device,
        )
        candidate_rows.extend(surface_candidate_rows)
        accepted_rows.extend(surface_accepted_rows)
        unaccepted_rows.extend(surface_unaccepted_rows)
        for key, values in surface_corpus.items():
            corpus[key].extend(values)

    target_corpus_path: Path | None = None
    if accepted_rows:
        target_corpus_path = run_dir / "target_corpus.npz"
        write_target_corpus(
            output_npz=target_corpus_path,
            observations=corpus["observations"],
            normal_hidden=corpus["normal_hidden"],
            variant_hidden=corpus["variant_hidden"],
            target_actions=corpus["target_actions"],
            normal_base_actions=corpus["normal_base_actions"],
            variant_base_actions=corpus["variant_base_actions"],
            weights=[float(row["weight"]) for row in accepted_rows],
            row_ids=list(range(len(accepted_rows))),
            source_indices=[int(row["source_index"]) for row in accepted_rows],
        )

    write_csv_rows(run_dir / "selected_boundary_source_rows.csv", source_rows.to_dict(orient="records"))
    write_csv_rows(run_dir / "target_candidates.csv", candidate_rows)
    write_csv_rows(run_dir / "accepted_targets.csv", accepted_rows, fieldnames=ACCEPTED_TARGET_FIELDNAMES)
    write_csv_rows(run_dir / "unaccepted_rows.csv", unaccepted_rows, fieldnames=UNACCEPTED_ROW_FIELDNAMES)

    candidate_frame = pd.DataFrame(candidate_rows)
    accepted_frame = pd.DataFrame(accepted_rows)
    unaccepted_frame = pd.DataFrame(unaccepted_rows)
    summary = {
        "run_type": "boundary_conditioned_grounded_target_miner",
        "checkpoint": checkpoint_path,
        "boundary_source_rows_csv": boundary_source_rows_csv,
        "surface_configs": {item.surface: item.env_config_path for item in surface_configs},
        "source_row_diversity": _diversity(source_rows),
        "accepted_target_diversity": _diversity(accepted_frame),
        "delay_steps": int(delay_steps),
        "steer_deltas": steer_deltas,
        "throttle_deltas": throttle_deltas,
        "brake_deltas": brake_deltas,
        "min_margin_improvement": float(min_margin_improvement),
        "min_risk_improvement": float(min_risk_improvement),
        "max_action_l2": float(max_action_l2),
        "max_continuation_steps": int(max_continuation_steps),
        "device": str(resolved_device),
        "source_rows": int(len(source_rows)),
        "candidate_rollouts": int(len(candidate_rows)),
        "accepted_targets": int(len(accepted_rows)),
        "unaccepted_rows": int(len(unaccepted_rows)),
        "candidate_margin_improvement_max": _empty_float_stat(candidate_frame, "margin_improvement", "max"),
        "candidate_margin_improvement_mean": _empty_float_stat(candidate_frame, "margin_improvement", "mean"),
        "candidate_risk_improvement_max": _empty_float_stat(candidate_frame, "risk_improvement", "max"),
        "candidate_risk_improvement_mean": _empty_float_stat(candidate_frame, "risk_improvement", "mean"),
        "accepted_margin_improvement_mean": _empty_float_stat(accepted_frame, "margin_improvement", "mean"),
        "accepted_margin_improvement_min": _empty_float_stat(accepted_frame, "margin_improvement", "min"),
        "accepted_margin_improvement_max": _empty_float_stat(accepted_frame, "margin_improvement", "max"),
        "best_unaccepted_margin_improvement": _empty_float_stat(unaccepted_frame, "best_margin_improvement", "max"),
        "best_unaccepted_risk_improvement": _empty_float_stat(unaccepted_frame, "best_risk_improvement", "max"),
        "candidate_rejection_counts": (
            candidate_frame["rejection_reason"].value_counts().to_dict()
            if not candidate_frame.empty
            else {}
        ),
        "diagnostic_only": True,
        "labels_enter_actor_input": False,
        "actor_parameters_changed": False,
        "ppo_used": False,
        "promoted": False,
        "optimizer_admission": False,
        "target_corpus_npz": target_corpus_path,
        "target_candidates_csv": run_dir / "target_candidates.csv",
        "accepted_targets_csv": run_dir / "accepted_targets.csv",
        "unaccepted_rows_csv": run_dir / "unaccepted_rows.csv",
        "selected_boundary_source_rows_csv": run_dir / "selected_boundary_source_rows.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run target search on boundary-conditioned rows.")
    parser.add_argument("--checkpoint-policy", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--boundary-source-rows", type=Path, required=True)
    parser.add_argument("--surface-config", type=parse_surface_config, action="append", required=True)
    parser.add_argument("--delay-steps", type=int, default=2)
    parser.add_argument("--steer-deltas", type=parse_float_list, default=(-0.08, -0.04, -0.02, 0.0, 0.02, 0.04, 0.08))
    parser.add_argument("--throttle-deltas", type=parse_float_list, default=(-0.06, -0.03, 0.0, 0.03))
    parser.add_argument("--brake-deltas", type=parse_float_list, default=(-0.08, -0.04, -0.02, 0.0, 0.02, 0.04, 0.08))
    parser.add_argument("--min-margin-improvement", type=float, default=0.02)
    parser.add_argument("--min-risk-improvement", type=float, default=0.05)
    parser.add_argument("--max-action-l2", type=float, default=0.10)
    parser.add_argument("--max-continuation-steps", type=int, default=40)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="boundary_conditioned_grounded_target_miner")
    summary = run_boundary_conditioned_grounded_target_miner(
        checkpoint_path=args.checkpoint_policy.path,
        boundary_source_rows_csv=args.boundary_source_rows,
        surface_configs=tuple(args.surface_config),
        delay_steps=args.delay_steps,
        steer_deltas=args.steer_deltas,
        throttle_deltas=args.throttle_deltas,
        brake_deltas=args.brake_deltas,
        min_margin_improvement=args.min_margin_improvement,
        min_risk_improvement=args.min_risk_improvement,
        max_action_l2=args.max_action_l2,
        max_continuation_steps=args.max_continuation_steps,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
