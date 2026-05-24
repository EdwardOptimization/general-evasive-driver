"""Mine boundary-conditioned source rows before grounded target search."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.grounded_capability_action_target_miner import (
    SUPPORTED_VARIANTS,
    SurfaceConfig,
    _finite_float,
    parse_surface_config,
    risk_score,
)
from autodrift.hidden_envelope_multiseed_gate import parse_checkpoint_spec
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.matched_history_outcome_gate import _snapshot, collect_requested_outcome_snapshots
from autodrift.terminal_margin_recovery_anchor import _rollout_first_action_override
from autodrift.train_ppo import ActorCritic, resolve_device


PHYSICAL_KEY = ["surface", "variant", "target", "left_seed", "left_step", "right_seed", "right_step"]


@dataclass(frozen=True)
class BoundaryDiversity:
    rows: int
    unique_physical_pairs: int
    unique_left_seeds: int
    surfaces: int
    variants: int
    targets: int
    max_physical_pair_dominance: float
    pass_diversity: bool


def select_source_pool(
    rows: pd.DataFrame,
    *,
    include_variants: tuple[str, ...] = SUPPORTED_VARIANTS,
    min_capability_z_distance: float = 0.10,
) -> pd.DataFrame:
    required = {
        "candidate_for_grounding",
        "surface",
        "variant",
        "target",
        "capability_z_distance",
        "action_distance",
        "coupling_gap",
        "left_seed",
        "left_step",
        "right_seed",
        "right_step",
    }
    missing = sorted(required.difference(rows.columns))
    if missing:
        raise ValueError("coupling rows missing columns: " + ", ".join(missing))
    frame = rows[
        rows["candidate_for_grounding"].astype(bool)
        & rows["variant"].astype(str).isin(set(include_variants))
        & (rows["capability_z_distance"].astype(float) >= float(min_capability_z_distance))
    ].copy()
    if frame.empty:
        return frame
    frame = frame.reset_index().rename(columns={"index": "coupling_row_index"})
    frame = frame.sort_values(["capability_z_distance", "coupling_gap"], ascending=[False, False])
    frame = frame.drop_duplicates(subset=PHYSICAL_KEY, keep="first").reset_index(drop=True)
    frame.insert(0, "source_index", np.arange(len(frame), dtype=np.int64))
    return frame


def request_left_snapshots(rows: pd.DataFrame) -> dict[int, set[int]]:
    requests: dict[int, set[int]] = {}
    for _, row in rows.iterrows():
        requests.setdefault(int(row["left_seed"]), set()).add(int(row["left_step"]))
    return requests


def boundary_acceptance(
    *,
    baseline: dict[str, Any],
    risk_threshold: float,
    margin_window: float,
) -> tuple[bool, str]:
    if bool(baseline.get("off_road", False)):
        return False, "baseline_off_road"
    if bool(baseline.get("spin_out", False)):
        return False, "baseline_spin_out"
    margin = _finite_float(baseline.get("min_clearance_margin"))
    if not np.isfinite(margin):
        return False, "baseline_margin_not_finite"
    if bool(baseline.get("collision", False)):
        return True, "baseline_collision"
    if margin <= float(margin_window):
        return True, "baseline_margin_window"
    baseline_risk = _finite_float(baseline.get("baseline_risk_score"), risk_score(baseline))
    if baseline_risk >= float(risk_threshold):
        return True, "baseline_high_risk"
    return False, "baseline_far_from_boundary"


def boundary_score(
    *,
    capability_z_distance: float,
    baseline_margin: float,
    baseline_risk_score: float,
    risk_min: float,
    risk_max: float,
    source_count: int,
    margin_window: float,
) -> float:
    if risk_max > risk_min:
        normalized_risk = (float(baseline_risk_score) - float(risk_min)) / (float(risk_max) - float(risk_min))
    else:
        normalized_risk = 0.0
    normalized_risk = float(np.clip(normalized_risk, 0.0, 1.0))
    margin_boost = max(0.0, float(margin_window) - float(baseline_margin))
    return float(
        float(capability_z_distance)
        * (1.0 + margin_boost)
        * (1.0 + normalized_risk)
        / np.sqrt(max(int(source_count), 1))
    )


def diversity_summary(rows: pd.DataFrame) -> BoundaryDiversity:
    if rows.empty:
        return BoundaryDiversity(
            rows=0,
            unique_physical_pairs=0,
            unique_left_seeds=0,
            surfaces=0,
            variants=0,
            targets=0,
            max_physical_pair_dominance=0.0,
            pass_diversity=False,
        )
    pair_cols = ["left_seed", "left_step", "right_seed", "right_step"]
    pair_counts = rows.groupby(pair_cols, observed=True).size()
    dominance = float(pair_counts.max() / len(rows)) if len(rows) else 0.0
    unique_pairs = int(len(pair_counts))
    left_seeds = int(rows["left_seed"].nunique())
    surfaces = int(rows["surface"].nunique())
    variants = int(rows["variant"].nunique())
    targets = int(rows["target"].nunique())
    pass_diversity = (
        len(rows) >= 24
        and unique_pairs >= 8
        and left_seeds >= 8
        and surfaces >= 2
        and variants >= 2
        and targets >= 2
        and dominance <= 0.25
    )
    return BoundaryDiversity(
        rows=int(len(rows)),
        unique_physical_pairs=unique_pairs,
        unique_left_seeds=left_seeds,
        surfaces=surfaces,
        variants=variants,
        targets=targets,
        max_physical_pair_dominance=dominance,
        pass_diversity=bool(pass_diversity),
    )


def _risk_quantile(values: list[float], quantile: float) -> float:
    finite = [float(value) for value in values if np.isfinite(value)]
    if not finite:
        return float("inf")
    return float(np.quantile(np.asarray(finite, dtype=np.float64), float(quantile)))


def _row_source_count(rows: pd.DataFrame, row: pd.Series) -> int:
    mask = np.ones(len(rows), dtype=bool)
    for column in PHYSICAL_KEY:
        mask &= rows[column].to_numpy() == row[column]
    return int(mask.sum())


def mine_sources_for_surface(
    *,
    model: ActorCritic,
    env_config_path: Path,
    rows: pd.DataFrame,
    max_continuation_steps: int,
    device: torch.device,
) -> list[dict[str, Any]]:
    env_config = load_env_config(env_config_path)
    snapshots = collect_requested_outcome_snapshots(
        model=model,
        env_config=env_config,
        requests=request_left_snapshots(rows),
        device=device,
    )
    output: list[dict[str, Any]] = []
    for _, row in rows.reset_index(drop=True).iterrows():
        left = _snapshot(snapshots, int(row["left_seed"]), int(row["left_step"]))
        base_action, _ = deterministic_action_from_hidden(model, left.observation, left.hidden, device)
        baseline = _rollout_first_action_override(
            model=model,
            snapshot=left,
            first_action=base_action,
            max_continuation_steps=max_continuation_steps,
            device=device,
        )
        output.append(
            {
                "source_index": int(row["source_index"]),
                "coupling_row_index": int(row["coupling_row_index"]),
                "surface": str(row["surface"]),
                "target": str(row["target"]),
                "variant": str(row["variant"]),
                "left_seed": int(row["left_seed"]),
                "right_seed": int(row["right_seed"]),
                "left_step": int(row["left_step"]),
                "right_step": int(row["right_step"]),
                "capability_z_distance": float(row["capability_z_distance"]),
                "action_distance": float(row["action_distance"]),
                "coupling_gap": float(row["coupling_gap"]),
                "base_steer": float(base_action[0]),
                "base_throttle": float(base_action[1]),
                "base_brake": float(base_action[2]),
                "baseline_success": bool(baseline.get("success", False)),
                "baseline_collision": bool(baseline.get("collision", False)),
                "baseline_off_road": bool(baseline.get("off_road", False)),
                "baseline_spin_out": bool(baseline.get("spin_out", False)),
                "baseline_terminal_reason": str(baseline.get("terminal_reason", "")),
                "baseline_margin": _finite_float(baseline.get("min_clearance_margin")),
                "baseline_risk_score": risk_score(baseline),
                "obstacle_completed": bool(baseline.get("obstacle_completed", False)),
                "continuation_steps": int(baseline.get("steps", 0)),
            }
        )
    return output


def classify_source_rollouts(
    source_rollouts: pd.DataFrame,
    *,
    risk_quantile: float,
    margin_window: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], float]:
    if source_rollouts.empty:
        return [], [], float("inf")
    risk_threshold = _risk_quantile(source_rollouts["baseline_risk_score"].astype(float).tolist(), risk_quantile)
    risk_min = float(source_rollouts["baseline_risk_score"].astype(float).min())
    risk_max = float(source_rollouts["baseline_risk_score"].astype(float).max())
    group_counts = (
        source_rollouts.groupby(PHYSICAL_KEY, observed=True)
        .size()
        .rename("source_group_count")
        .reset_index()
    )
    merged = source_rollouts.merge(group_counts, on=PHYSICAL_KEY, how="left")
    boundary_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    for _, row in merged.iterrows():
        baseline = {
            "collision": bool(row["baseline_collision"]),
            "off_road": bool(row["baseline_off_road"]),
            "spin_out": bool(row["baseline_spin_out"]),
            "min_clearance_margin": float(row["baseline_margin"]),
            "baseline_risk_score": float(row["baseline_risk_score"]),
        }
        accepted, reason = boundary_acceptance(
            baseline=baseline,
            risk_threshold=risk_threshold,
            margin_window=margin_window,
        )
        item = row.to_dict()
        item["boundary_acceptance_reason"] = reason
        item["risk_threshold"] = float(risk_threshold)
        item["source_group_count"] = int(row["source_group_count"])
        item["boundary_score"] = boundary_score(
            capability_z_distance=float(row["capability_z_distance"]),
            baseline_margin=float(row["baseline_margin"]),
            baseline_risk_score=float(row["baseline_risk_score"]),
            risk_min=risk_min,
            risk_max=risk_max,
            source_count=int(row["source_group_count"]),
            margin_window=margin_window,
        )
        if accepted:
            boundary_rows.append(item)
        else:
            rejected_rows.append(item)
    boundary_rows = sorted(boundary_rows, key=lambda item: float(item["boundary_score"]), reverse=True)
    rejected_rows = sorted(rejected_rows, key=lambda item: float(item["boundary_score"]), reverse=True)
    return boundary_rows, rejected_rows, risk_threshold


def run_boundary_conditioned_source_miner(
    *,
    checkpoint_path: Path,
    coupling_rows_csv: Path,
    surface_configs: tuple[SurfaceConfig, ...],
    include_variants: tuple[str, ...],
    min_capability_z_distance: float,
    margin_window: float,
    risk_quantile: float,
    max_continuation_steps: int,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    rows = pd.read_csv(coupling_rows_csv)
    source_pool = select_source_pool(
        rows,
        include_variants=include_variants,
        min_capability_z_distance=min_capability_z_distance,
    )
    surface_config_by_name = {item.surface: item.env_config_path for item in surface_configs}
    missing_configs = sorted(set(source_pool["surface"].astype(str)).difference(surface_config_by_name)) if not source_pool.empty else []
    if missing_configs:
        raise ValueError(f"missing env configs for surfaces: {missing_configs}")

    source_rollout_rows: list[dict[str, Any]] = []
    for surface, surface_rows in source_pool.groupby("surface", observed=True):
        source_rollout_rows.extend(
            mine_sources_for_surface(
                model=model,
                env_config_path=surface_config_by_name[str(surface)],
                rows=surface_rows.reset_index(drop=True),
                max_continuation_steps=max_continuation_steps,
                device=resolved_device,
            )
        )

    source_rollouts = pd.DataFrame(source_rollout_rows)
    boundary_rows, rejected_rows, risk_threshold = classify_source_rollouts(
        source_rollouts,
        risk_quantile=risk_quantile,
        margin_window=margin_window,
    )
    boundary_frame = pd.DataFrame(boundary_rows)
    rejected_frame = pd.DataFrame(rejected_rows)
    diversity = diversity_summary(boundary_frame)
    write_csv_rows(run_dir / "selected_source_pool.csv", source_pool.to_dict(orient="records"))
    write_csv_rows(run_dir / "source_rollouts.csv", source_rollout_rows)
    write_csv_rows(run_dir / "boundary_source_rows.csv", boundary_rows)
    write_csv_rows(run_dir / "rejected_far_rows.csv", rejected_rows)

    summary = {
        "run_type": "boundary_conditioned_source_miner",
        "checkpoint": checkpoint_path,
        "coupling_rows_csv": coupling_rows_csv,
        "surface_configs": {item.surface: item.env_config_path for item in surface_configs},
        "include_variants": include_variants,
        "min_capability_z_distance": float(min_capability_z_distance),
        "margin_window": float(margin_window),
        "risk_quantile": float(risk_quantile),
        "risk_threshold": float(risk_threshold),
        "max_continuation_steps": int(max_continuation_steps),
        "device": str(resolved_device),
        "source_candidate_rows": int(len(rows)),
        "selected_source_pool_rows": int(len(source_pool)),
        "source_rollout_rows": int(len(source_rollout_rows)),
        "boundary_source_rows": int(len(boundary_rows)),
        "rejected_far_rows": int(len(rejected_rows)),
        "baseline_margin_mean": float(source_rollouts["baseline_margin"].mean()) if not source_rollouts.empty else float("nan"),
        "baseline_margin_median": float(source_rollouts["baseline_margin"].median()) if not source_rollouts.empty else float("nan"),
        "baseline_margin_min": float(source_rollouts["baseline_margin"].min()) if not source_rollouts.empty else float("nan"),
        "baseline_margin_max": float(source_rollouts["baseline_margin"].max()) if not source_rollouts.empty else float("nan"),
        "baseline_collision_rows": int(source_rollouts["baseline_collision"].sum()) if not source_rollouts.empty else 0,
        "baseline_margin_le_window_rows": int((source_rollouts["baseline_margin"] <= float(margin_window)).sum()) if not source_rollouts.empty else 0,
        "boundary_acceptance_counts": (
            boundary_frame["boundary_acceptance_reason"].value_counts().to_dict()
            if not boundary_frame.empty
            else {}
        ),
        "rejection_counts": (
            rejected_frame["boundary_acceptance_reason"].value_counts().to_dict()
            if not rejected_frame.empty
            else {}
        ),
        "diversity": diversity,
        "diversity_pass": bool(diversity.pass_diversity),
        "labels_enter_actor_input": False,
        "actor_parameters_changed": False,
        "ppo_used": False,
        "promoted": False,
        "source_rollouts_csv": run_dir / "source_rollouts.csv",
        "boundary_source_rows_csv": run_dir / "boundary_source_rows.csv",
        "rejected_far_rows_csv": run_dir / "rejected_far_rows.csv",
        "selected_source_pool_csv": run_dir / "selected_source_pool.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine boundary-conditioned source rows.")
    parser.add_argument("--checkpoint-policy", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--coupling-rows", type=Path, required=True)
    parser.add_argument("--surface-config", type=parse_surface_config, action="append", required=True)
    parser.add_argument("--include-variant", type=str, action="append", default=None)
    parser.add_argument("--min-capability-z-distance", type=float, default=0.10)
    parser.add_argument("--margin-window", type=float, default=0.50)
    parser.add_argument("--risk-quantile", type=float, default=0.75)
    parser.add_argument("--max-continuation-steps", type=int, default=80)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="boundary_conditioned_source_miner")
    summary = run_boundary_conditioned_source_miner(
        checkpoint_path=args.checkpoint_policy.path,
        coupling_rows_csv=args.coupling_rows,
        surface_configs=tuple(args.surface_config),
        include_variants=tuple(args.include_variant or SUPPORTED_VARIANTS),
        min_capability_z_distance=args.min_capability_z_distance,
        margin_window=args.margin_window,
        risk_quantile=args.risk_quantile,
        max_continuation_steps=args.max_continuation_steps,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
