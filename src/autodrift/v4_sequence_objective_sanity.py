"""Exact no-training sanity metrics for the M755 v4 sequence objective."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import NOMINAL_FAULT, load_scenario_config
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.sequence_command_response_intervention import replay_sequence_variant
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.temporal_action_boundary_outcome_miner import _collect_seed_snapshots, _find_snapshot
from autodrift.train_ppo import resolve_device


ACTION_FIELDS = ("first_steer", "first_throttle", "first_brake")
GROUP_DIMENSIONS = (
    ("overall",),
    ("variant",),
    ("horizon",),
    ("preferred_fault_family",),
    ("wrong_fault_family",),
    ("fault_family_pair",),
    ("source_pool",),
    ("claim_boundary_level",),
    ("hard_negative_available",),
)


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _vector(row: dict[str, Any], fields: tuple[str, ...] = ACTION_FIELDS) -> np.ndarray:
    return np.asarray([_finite_float(row.get(field)) for field in fields], dtype=np.float32)


def _l2(lhs: np.ndarray, rhs: np.ndarray) -> float:
    if not np.all(np.isfinite(lhs)) or not np.all(np.isfinite(rhs)):
        return float("nan")
    return float(np.linalg.norm(lhs - rhs))


def _finite_values(values: list[float]) -> list[float]:
    return [float(value) for value in values if np.isfinite(value)]


def _mean(values: list[float]) -> float:
    finite = _finite_values(values)
    return float(np.mean(finite)) if finite else float("nan")


def _percentile(values: list[float], percentile: float) -> float:
    finite = _finite_values(values)
    return float(np.percentile(finite, percentile)) if finite else float("nan")


def _all_finite(values: list[float]) -> bool:
    return bool(values) and all(np.isfinite(float(value)) for value in values)


def _target_gap(row: dict[str, Any]) -> float:
    base = _finite_float(row.get("prefix_l2_mean"), default=0.0)
    return float(np.clip(base, 0.02, 0.06))


def _outcome_weight(row: dict[str, Any]) -> float:
    margin_gap = max(_finite_float(row.get("margin_gap_from_normal"), default=0.0), 0.0)
    horizon = max(float(_finite_float(row.get("horizon"), default=1.0)), 1.0)
    variant = str(row.get("variant", ""))
    variant_weight = 1.0 if variant == "zero_command_obs" else 0.75
    return float(np.clip(1.0 + 10.0 * margin_gap + 0.05 * min(horizon, 8.0), 1.0, 3.0) * variant_weight)


def _metadata_missing(row: dict[str, Any]) -> bool:
    required = (
        "source_index",
        "seed",
        "step",
        "preferred_fault",
        "variant",
        "horizon",
        "source_kind",
        "source_pool",
        "claim_boundary_level",
        "contrast_group_id",
    )
    return any(not str(row.get(field, "")).strip() for field in required)


def _contrast_lookup(rows: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    normal_rows: dict[str, dict[str, Any]] = {}
    hard_negative_rows: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        group_id = str(row.get("contrast_group_id", ""))
        role = str(row.get("contrast_role", ""))
        if role == "normal":
            normal_rows.setdefault(group_id, row)
        elif role == "hard_negative_action_only":
            hard_negative_rows.setdefault(group_id, []).append(row)
    return normal_rows, hard_negative_rows


def classify_v4_sequence_objective_sanity(
    *,
    positive_rows: int,
    reconstructed_rows: int,
    metadata_missing_rows: int,
    duplicate_group_ids: int,
    missing_normal_rows: int,
    missing_source_snapshots: int,
    exact_losses_finite: bool,
    normal_intervention_gap_mean: float,
    hard_negative_available_fraction: float,
    actor_parameters_changed: bool,
    min_reconstruction_success_rate: float = 0.98,
    min_gap_mean: float = 0.02,
) -> str:
    if bool(actor_parameters_changed) or int(metadata_missing_rows) > 0:
        return "v4_sequence_objective_metadata_artifact"
    reconstruction_rate = float(reconstructed_rows) / max(int(positive_rows), 1)
    if (
        reconstruction_rate < float(min_reconstruction_success_rate)
        or int(duplicate_group_ids) > 0
        or int(missing_normal_rows) > 0
        or int(missing_source_snapshots) > 0
    ):
        return "v4_sequence_objective_reconstruction_blocked"
    if not bool(exact_losses_finite) or float(normal_intervention_gap_mean) < float(min_gap_mean):
        return "v4_sequence_objective_degenerate"
    if float(hard_negative_available_fraction) < 0.98:
        return "v4_sequence_objective_hard_negative_sparse"
    return "v4_sequence_objective_sanity_pass"


def _metric_summary(rows: list[dict[str, Any]], *, dimensions: tuple[tuple[str, ...], ...] = GROUP_DIMENSIONS) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for keys in dimensions:
        groups: dict[tuple[str, ...], list[dict[str, Any]]] = {}
        for row in rows:
            if keys == ("overall",):
                key = ("overall",)
            else:
                key = tuple(str(row.get(field, "")) for field in keys)
            groups.setdefault(key, []).append(row)
        for key, group_rows in sorted(groups.items()):
            values = lambda name: [_finite_float(row.get(name)) for row in group_rows]
            output.append(
                {
                    "dimension": "|".join(keys),
                    "value": "|".join(key),
                    "sample_count": int(len(group_rows)),
                    "positive_group_count": int(len({str(row.get("contrast_group_id", "")) for row in group_rows})),
                    "normal_anchor_mse_mean": _mean(values("normal_anchor_mse")),
                    "intervention_anchor_mse_mean": _mean(values("intervention_anchor_mse")),
                    "normal_intervention_gap_mean": _mean(values("normal_intervention_gap")),
                    "normal_intervention_gap_p10": _percentile(values("normal_intervention_gap"), 10),
                    "target_gap_mean": _mean(values("target_gap")),
                    "gap_deficit_mean": _mean(values("gap_deficit")),
                    "gap_deficit_p95": _percentile(values("gap_deficit"), 95),
                    "hard_negative_available_fraction": float(
                        sum(1 for row in group_rows if _bool(row.get("hard_negative_available", False)))
                        / max(len(group_rows), 1)
                    ),
                    "hard_negative_calibration_loss_mean": _mean(values("hard_negative_calibration_loss")),
                    "first_action_drift_from_base_mean": _mean(values("first_action_drift_from_base")),
                    "first_action_drift_from_base_p95": _percentile(values("first_action_drift_from_base"), 95),
                    "outcome_weight_mean": _mean(values("outcome_weight")),
                }
            )
    return output


def run_v4_sequence_objective_sanity(
    *,
    checkpoint_path: Path,
    corpus_summary_path: Path,
    positive_rows_path: Path,
    contrast_rows_path: Path,
    fault_config_path: Path,
    scenario_config_path: Path,
    run_dir: Path,
    device: str,
    max_rows: int | None = None,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    corpus_summary = read_json(corpus_summary_path)
    scenario_config = load_scenario_config(scenario_config_path)
    env_config = load_env_config(Path(scenario_config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    checksum_before = model_parameter_checksum(model)
    response_dim = response_feature_dim_for_model(model)
    max_continuation_steps = int(scenario_config.get("max_continuation_steps", 60))
    positives = _read_csv_rows(positive_rows_path)
    if max_rows is not None:
        positives = positives[: max(0, int(max_rows))]
    contrast_rows = _read_csv_rows(contrast_rows_path)
    normal_by_group, hard_by_group = _contrast_lookup(contrast_rows)
    duplicate_group_ids = len(positives) - len({str(row.get("contrast_group_id", "")) for row in positives})
    metadata_missing_rows = sum(1 for row in positives if _metadata_missing(row))
    missing_normal_rows = sum(1 for row in positives if str(row.get("contrast_group_id", "")) not in normal_by_group)
    faults = [NOMINAL_FAULT, *scenario_config["faults"]]
    snapshots_by_seed: dict[int, list[Any]] = {}
    metric_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    missing_source_snapshots = 0
    unique_seeds = sorted({int(row.get("seed", -1)) for row in positives if str(row.get("seed", "")).strip()})
    for seed in unique_seeds:
        snapshots_by_seed[seed] = _collect_seed_snapshots(
            model=model,
            env_config=env_config,
            faults=faults,
            seed=int(seed),
            config=scenario_config,
            device=resolved_device,
        )
    normal_cache: dict[tuple[int, str, int, int], tuple[dict[str, Any], list[np.ndarray]]] = {}
    variant_cache: dict[tuple[int, str, int, int, str], dict[str, Any]] = {}
    for row in positives:
        group_id = str(row.get("contrast_group_id", ""))
        normal_base = normal_by_group.get(group_id)
        if normal_base is None:
            rejected_rows.append({**row, "rejection_reason": "missing_normal_row"})
            continue
        if _metadata_missing(row):
            rejected_rows.append({**row, "rejection_reason": "metadata_missing"})
            continue
        seed = int(row.get("seed", -1))
        fault_name = str(row.get("preferred_fault", ""))
        step = int(row.get("step", -1))
        horizon = int(row.get("horizon", 0))
        variant = str(row.get("variant", ""))
        snapshot = _find_snapshot(snapshots_by_seed.get(seed, []), fault_name=fault_name, step=step)
        if snapshot is None:
            missing_source_snapshots += 1
            rejected_rows.append({**row, "rejection_reason": "missing_source_snapshot"})
            continue
        normal_key = (seed, fault_name, step, horizon)
        if normal_key not in normal_cache:
            normal_cache[normal_key] = replay_sequence_variant(
                model=model,
                snapshot=snapshot,
                env_config=env_config,
                variant="normal",
                horizon=horizon,
                response_dim=response_dim,
                normal_actions=None,
                max_continuation_steps=max_continuation_steps,
                device=resolved_device,
            )
        normal_replay, normal_actions = normal_cache[normal_key]
        variant_key = (seed, fault_name, step, horizon, variant)
        if variant_key not in variant_cache:
            variant_replay, _ = replay_sequence_variant(
                model=model,
                snapshot=snapshot,
                env_config=env_config,
                variant=variant,
                horizon=horizon,
                response_dim=response_dim,
                normal_actions=normal_actions,
                max_continuation_steps=max_continuation_steps,
                device=resolved_device,
            )
            variant_cache[variant_key] = variant_replay
        variant_replay = variant_cache[variant_key]
        normal_action = _vector(normal_replay)
        intervention_action = _vector(variant_replay)
        normal_base_action = _vector(normal_base)
        intervention_base_action = _vector(row)
        normal_anchor_mse = float(np.mean((normal_action - normal_base_action) ** 2))
        intervention_anchor_mse = float(np.mean((intervention_action - intervention_base_action) ** 2))
        gap = _l2(normal_action, intervention_action)
        target_gap = _target_gap(row)
        gap_deficit = float(max(0.0, target_gap - gap)) if np.isfinite(gap) else float("nan")
        hard_available = group_id in hard_by_group
        hard_loss = 0.0
        if hard_available:
            hard_gaps = [_l2(normal_base_action, _vector(item)) for item in hard_by_group[group_id]]
            hard_gap = max(_finite_values(hard_gaps), default=0.0)
            hard_loss = float(max(0.0, hard_gap - gap + 0.005) ** 2) if np.isfinite(gap) else float("nan")
        first_action_drift = _l2(intervention_action, intervention_base_action)
        metric_rows.append(
            {
                "contrast_group_id": group_id,
                "source_index": row.get("source_index", ""),
                "seed": int(seed),
                "step": int(step),
                "preferred_fault": fault_name,
                "preferred_fault_family": row.get("preferred_fault_family", ""),
                "wrong_fault_family": row.get("wrong_fault_family", ""),
                "fault_family_pair": row.get("fault_family_pair", ""),
                "variant": variant,
                "horizon": int(horizon),
                "source_pool": row.get("source_pool", ""),
                "claim_boundary_level": row.get("claim_boundary_level", ""),
                "hard_negative_available": bool(hard_available),
                "normal_anchor_mse": normal_anchor_mse,
                "intervention_anchor_mse": intervention_anchor_mse,
                "normal_intervention_gap": gap,
                "target_gap": target_gap,
                "gap_deficit": gap_deficit,
                "hard_negative_calibration_loss": hard_loss,
                "first_action_drift_from_base": first_action_drift,
                "outcome_weight": _outcome_weight(row),
                "normal_success": bool(normal_replay.get("success", False)),
                "variant_success": bool(variant_replay.get("success", False)),
                "normal_margin": _finite_float(normal_replay.get("min_clearance_margin")),
                "variant_margin": _finite_float(variant_replay.get("min_clearance_margin")),
            }
        )
    checksum_after = model_parameter_checksum(model)
    summary_rows = _metric_summary(metric_rows)
    overall = next((row for row in summary_rows if row["dimension"] == "overall"), {})
    exact_losses = [
        _finite_float(row.get("normal_anchor_mse")) for row in metric_rows
    ] + [
        _finite_float(row.get("intervention_anchor_mse")) for row in metric_rows
    ] + [
        _finite_float(row.get("gap_deficit")) for row in metric_rows
    ]
    hard_fraction = float(
        sum(1 for row in metric_rows if _bool(row.get("hard_negative_available", False))) / max(len(metric_rows), 1)
    )
    result_class = classify_v4_sequence_objective_sanity(
        positive_rows=len(positives),
        reconstructed_rows=len(metric_rows),
        metadata_missing_rows=metadata_missing_rows,
        duplicate_group_ids=duplicate_group_ids,
        missing_normal_rows=missing_normal_rows,
        missing_source_snapshots=missing_source_snapshots,
        exact_losses_finite=_all_finite(exact_losses),
        normal_intervention_gap_mean=_finite_float(overall.get("normal_intervention_gap_mean")),
        hard_negative_available_fraction=hard_fraction,
        actor_parameters_changed=bool(checksum_before != checksum_after),
    )
    write_csv_rows(run_dir / "objective_rows.csv", metric_rows)
    write_csv_rows(run_dir / "objective_metrics.csv", summary_rows)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
    summary = {
        "run_type": "v4_sequence_objective_sanity",
        "checkpoint": checkpoint_path,
        "corpus_summary": corpus_summary_path,
        "positive_rows_input": positive_rows_path,
        "contrast_rows_input": contrast_rows_path,
        "fault_config": fault_config_path,
        "scenario_config": scenario_config_path,
        "corpus_result_class": corpus_summary.get("result_class"),
        "positive_rows": int(len(positives)),
        "reconstructed_rows": int(len(metric_rows)),
        "sample_reconstruction_success_rate": float(len(metric_rows) / max(len(positives), 1)),
        "metadata_missing_rows": int(metadata_missing_rows),
        "duplicate_group_ids": int(duplicate_group_ids),
        "missing_normal_rows": int(missing_normal_rows),
        "missing_source_snapshots": int(missing_source_snapshots),
        "rejected_rows": int(len(rejected_rows)),
        "normal_group_count": int(len({str(row.get("contrast_group_id", "")) for row in metric_rows})),
        "normal_anchor_mse_mean": _finite_float(overall.get("normal_anchor_mse_mean")),
        "intervention_anchor_mse_mean": _finite_float(overall.get("intervention_anchor_mse_mean")),
        "normal_intervention_gap_mean": _finite_float(overall.get("normal_intervention_gap_mean")),
        "normal_intervention_gap_p10": _finite_float(overall.get("normal_intervention_gap_p10")),
        "target_gap_mean": _finite_float(overall.get("target_gap_mean")),
        "gap_deficit_mean": _finite_float(overall.get("gap_deficit_mean")),
        "gap_deficit_p95": _finite_float(overall.get("gap_deficit_p95")),
        "hard_negative_available_fraction": hard_fraction,
        "hard_negative_sparse": bool(hard_fraction < 0.98),
        "claim_boundary_levels": sorted({str(row.get("claim_boundary_level", "")) for row in metric_rows}),
        "training_started": False,
        "optimizer_started": False,
        "checkpoint_loaded_for_eval_only": True,
        "ppo_used": False,
        "promoted": False,
        "actor_parameters_changed": bool(checksum_before != checksum_after),
        "result_class": result_class,
        "summary_json": run_dir / "summary.json",
        "objective_rows_csv": run_dir / "objective_rows.csv",
        "objective_metrics_csv": run_dir / "objective_metrics.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training v4 sequence objective sanity metrics.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--corpus-summary", type=Path, required=True)
    parser.add_argument("--positive-rows", type=Path, required=True)
    parser.add_argument("--contrast-rows", type=Path, required=True)
    parser.add_argument("--fault-config", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--max-rows", type=int, default=None)
    args = parser.parse_args()
    summary = run_v4_sequence_objective_sanity(
        checkpoint_path=args.checkpoint,
        corpus_summary_path=args.corpus_summary,
        positive_rows_path=args.positive_rows,
        contrast_rows_path=args.contrast_rows,
        fault_config_path=args.fault_config,
        scenario_config_path=args.scenario_config,
        run_dir=args.run_dir,
        device=args.device,
        max_rows=args.max_rows,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
