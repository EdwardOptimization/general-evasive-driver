"""No-training actor-head coupling audit for fused history feature deltas."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.cross_fault_hidden_action_gap_audit import (
    SENTINEL_FAULT_PAIRS,
    _mean,
    _percentile,
    _safe_ratio,
    _summary_stats,
)
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import (
    NOMINAL_FAULT,
    ExtremeSnapshot,
    collect_fault_snapshots,
    evaluate_matched_pair,
    find_cross_fault_match,
    load_scenario_config,
)
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import ActorCritic, resolve_device
from autodrift.trajectory_terminal_boundary_source_miner import assigned_split


DEFAULT_ALPHAS = (0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0)


def _l2(left: torch.Tensor, right: torch.Tensor) -> float:
    return float(torch.linalg.vector_norm(left.detach().float() - right.detach().float()).item())


def parse_alphas(text: str | None) -> tuple[float, ...]:
    if not text:
        return DEFAULT_ALPHAS
    values = tuple(float(item.strip()) for item in text.split(",") if item.strip())
    if not values:
        raise ValueError("alpha list cannot be empty")
    if any(value < 0.0 for value in values):
        raise ValueError("alpha values must be non-negative")
    return tuple(sorted(set(values)))


def compute_actor_head_coupling(
    *,
    model: ActorCritic,
    observation: np.ndarray,
    normal_hidden: torch.Tensor,
    variant_hidden: torch.Tensor,
    device: torch.device,
    alphas: tuple[float, ...],
    action_threshold: float,
) -> dict[str, float]:
    obs_t = torch.as_tensor(observation, dtype=torch.float32, device=device).unsqueeze(0)
    normal_hidden_t = normal_hidden.to(device=device, dtype=torch.float32)
    variant_hidden_t = variant_hidden.to(device=device, dtype=torch.float32)
    with torch.no_grad():
        normal_features, _ = model.recurrent_features_tensor(obs_t, normal_hidden_t)
        variant_features, _ = model.recurrent_features_tensor(obs_t, variant_hidden_t)
        normal_pre_tanh = model.actor_mean(normal_features)
        variant_pre_tanh = model.actor_mean(variant_features)
        normal_action = torch.tanh(normal_pre_tanh)
        variant_action = torch.tanh(variant_pre_tanh)
        feature_delta = variant_features - normal_features
        alpha_action_l2: dict[float, float] = {}
        alpha_to_threshold = float("nan")
        for alpha in alphas:
            alpha_features = normal_features + float(alpha) * feature_delta
            alpha_action = torch.tanh(model.actor_mean(alpha_features))
            action_l2 = _l2(alpha_action, normal_action)
            alpha_action_l2[float(alpha)] = action_l2
            if not np.isfinite(alpha_to_threshold) and action_l2 >= float(action_threshold):
                alpha_to_threshold = float(alpha)

    feature_delta_l2 = _l2(variant_features, normal_features)
    pre_tanh_delta_l2 = _l2(variant_pre_tanh, normal_pre_tanh)
    action_delta_l2 = _l2(variant_action, normal_action)
    output = {
        "feature_delta_l2": feature_delta_l2,
        "pre_tanh_delta_l2": pre_tanh_delta_l2,
        "action_delta_l2": action_delta_l2,
        "projection_ratio": _safe_ratio(pre_tanh_delta_l2, feature_delta_l2),
        "tanh_attenuation_ratio": _safe_ratio(action_delta_l2, pre_tanh_delta_l2),
        "feature_to_action_ratio": _safe_ratio(action_delta_l2, feature_delta_l2),
        "alpha_to_action_threshold": alpha_to_threshold,
    }
    for alpha in alphas:
        key = str(float(alpha)).replace(".", "_")
        output[f"action_l2_at_alpha_{key}"] = alpha_action_l2[float(alpha)]
    return output


def classify_actor_head_coupling_result(
    *,
    wrong_rows: int,
    wrong_low_alpha_rows: int,
    wrong_high_alpha_rows: int,
    unique_low_alpha_fault_pairs: int,
    wrong_projection_ratio_mean: float,
    reset_projection_ratio_mean: float,
    wrong_tanh_attenuation_mean: float,
    reset_tanh_attenuation_mean: float,
    wrong_feature_delta_mean: float,
    reset_feature_delta_mean: float,
    min_low_alpha_rows: int,
    min_unique_fault_pairs: int,
    projection_ratio_reset_fraction: float,
    tanh_attenuation_reset_fraction: float,
) -> str:
    if int(wrong_rows) == 0:
        return "matched_state_empty"
    if int(wrong_low_alpha_rows) >= int(min_low_alpha_rows) and int(unique_low_alpha_fault_pairs) >= int(
        min_unique_fault_pairs
    ):
        return "actor_head_coupling_positive"
    if int(wrong_high_alpha_rows) < int(min_low_alpha_rows):
        return "amplification_not_action_relevant"
    if np.isfinite(wrong_projection_ratio_mean) and np.isfinite(reset_projection_ratio_mean):
        if wrong_projection_ratio_mean < float(projection_ratio_reset_fraction) * reset_projection_ratio_mean:
            return "actor_head_projection_washout"
    if np.isfinite(wrong_tanh_attenuation_mean) and np.isfinite(reset_tanh_attenuation_mean):
        if wrong_tanh_attenuation_mean < float(tanh_attenuation_reset_fraction) * reset_tanh_attenuation_mean:
            return "tanh_saturation_washout"
    if np.isfinite(wrong_feature_delta_mean) and np.isfinite(reset_feature_delta_mean):
        if wrong_feature_delta_mean < 0.25 * reset_feature_delta_mean:
            return "feature_delta_too_small"
    return "near_threshold_action_washout"


def _finite_alpha(row: dict[str, Any]) -> float:
    value = _finite_float(row.get("alpha_to_action_threshold"))
    return value if np.isfinite(value) else float("inf")


def _alpha_summary(rows: list[dict[str, Any]], alphas: tuple[float, ...]) -> list[dict[str, Any]]:
    output = []
    for variant in sorted({str(row.get("variant", "")) for row in rows}):
        variant_rows = [row for row in rows if row.get("variant") == variant]
        item: dict[str, Any] = {
            "variant": variant,
            "rows": int(len(variant_rows)),
            "alpha_to_action_threshold_mean": _mean(variant_rows, "alpha_to_action_threshold"),
            "alpha_to_action_threshold_p50": _percentile(variant_rows, "alpha_to_action_threshold", 0.50),
            "alpha_to_action_threshold_p90": _percentile(variant_rows, "alpha_to_action_threshold", 0.90),
        }
        for alpha in alphas:
            key = str(float(alpha)).replace(".", "_")
            item[f"rows_crossing_by_alpha_{key}"] = int(sum(1 for row in variant_rows if _finite_alpha(row) <= alpha))
        output.append(item)
    return output


def _coupling_group_summary(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in rows:
        group_key = tuple(str(row.get(key, "")) for key in keys)
        groups.setdefault(group_key, []).append(row)
    output: list[dict[str, Any]] = []
    for group_key, group_rows in sorted(groups.items()):
        item = {key: value for key, value in zip(keys, group_key, strict=True)}
        item.update(
            {
                "rows": int(len(group_rows)),
                "unique_seeds": int(len({int(row.get("seed", -1)) for row in group_rows})),
                "feature_delta_l2_mean": _mean(group_rows, "feature_delta_l2"),
                "feature_delta_l2_p95": _percentile(group_rows, "feature_delta_l2", 0.95),
                "pre_tanh_delta_l2_mean": _mean(group_rows, "pre_tanh_delta_l2"),
                "pre_tanh_delta_l2_p95": _percentile(group_rows, "pre_tanh_delta_l2", 0.95),
                "action_delta_l2_mean": _mean(group_rows, "action_delta_l2"),
                "action_delta_l2_p95": _percentile(group_rows, "action_delta_l2", 0.95),
                "projection_ratio_mean": _mean(group_rows, "projection_ratio"),
                "tanh_attenuation_ratio_mean": _mean(group_rows, "tanh_attenuation_ratio"),
                "feature_to_action_ratio_mean": _mean(group_rows, "feature_to_action_ratio"),
                "alpha_to_action_threshold_mean": _mean(group_rows, "alpha_to_action_threshold"),
                "margin_gap_mean": _mean(group_rows, "margin_gap"),
                "margin_gap_p95": _percentile(group_rows, "margin_gap", 0.95),
            }
        )
        output.append(item)
    return output


def _pair_metadata(pair_row: dict[str, Any]) -> dict[str, Any]:
    fault_family_pair = f"{pair_row.get('preferred_fault_family')}->{pair_row.get('wrong_fault_family')}"
    return {
        "pair_id": int(pair_row.get("pair_id", -1)),
        "seed": int(pair_row.get("seed", -1)),
        "step": int(pair_row.get("step", -1)),
        "preferred_snapshot_id": int(pair_row.get("preferred_snapshot_id", -1)),
        "wrong_snapshot_id": int(pair_row.get("wrong_snapshot_id", -1)),
        "preferred_fault": str(pair_row.get("preferred_fault", "")),
        "preferred_fault_family": str(pair_row.get("preferred_fault_family", "")),
        "preferred_fault_severity": str(pair_row.get("preferred_fault_severity", "")),
        "wrong_fault": str(pair_row.get("wrong_fault", "")),
        "wrong_fault_family": str(pair_row.get("wrong_fault_family", "")),
        "wrong_fault_severity": str(pair_row.get("wrong_fault_severity", "")),
        "fault_family_pair": fault_family_pair,
        "severity_pair": f"{pair_row.get('preferred_fault_severity')}->{pair_row.get('wrong_fault_severity')}",
        "pairing_rule": str(pair_row.get("pairing_rule", "")),
        "assigned_split": assigned_split(int(pair_row.get("seed", -1)), heldout_fraction=0.2),
        "sentinel_pair": bool(fault_family_pair in SENTINEL_FAULT_PAIRS),
        "normal_margin": _finite_float(pair_row.get("normal_margin")),
    }


def _variant_row(
    *,
    pair_row: dict[str, Any],
    variant: str,
    variant_margin: float,
    margin_gap: float,
    success_drop: bool,
    metrics: dict[str, float],
) -> dict[str, Any]:
    row = _pair_metadata(pair_row)
    row.update(
        {
            "variant": variant,
            "variant_margin": _finite_float(variant_margin),
            "margin_gap": _finite_float(margin_gap),
            "success_drop": bool(success_drop),
            **metrics,
        }
    )
    return row


def run_actor_head_history_signal_coupling_audit(
    *,
    checkpoint_path: Path,
    config_path: Path,
    seed_start: int,
    seed_count: int,
    device: str,
    run_dir: Path,
    alphas: tuple[float, ...] = DEFAULT_ALPHAS,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    config = load_scenario_config(config_path)
    pairing_rules = tuple(config.get("pairing_rules", ()))
    if not pairing_rules:
        raise ValueError("actor-head coupling audit requires config pairing_rules")
    env_config = load_env_config(Path(config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    if not model.is_online_recurrent:
        raise ValueError("actor-head coupling audit requires an online recurrent checkpoint")
    checksum_before = model_parameter_checksum(model)
    response_dim = response_feature_dim_for_model(model)

    faults = [NOMINAL_FAULT, *config["faults"]]
    max_steps = int(config.get("max_steps", 260))
    min_step = int(config.get("min_step", 35))
    snapshot_stride = int(config.get("snapshot_stride", 5))
    max_snapshots_per_scenario = int(config.get("max_snapshots_per_scenario", 4))
    obstacle_longitudinal_min = float(config.get("obstacle_longitudinal_min", -8.0))
    obstacle_longitudinal_max = float(config.get("obstacle_longitudinal_max", 90.0))
    max_pairs = int(config.get("max_pairs", 2048))
    max_continuation_steps = int(config.get("max_continuation_steps", 40))
    min_normal_margin = float(config.get("min_normal_margin", 0.0))
    min_history_margin_gap = float(config.get("min_history_margin_gap", 0.02))
    min_action_l2_gap = float(config.get("min_action_l2_gap", 0.015))
    low_alpha_limit = float(config.get("low_alpha_limit", 4.0))
    high_alpha_limit = float(config.get("high_alpha_limit", 16.0))
    min_low_alpha_rows = int(config.get("min_low_alpha_rows", 30))
    min_unique_fault_pairs = int(config.get("min_unique_fault_pairs", 4))
    projection_ratio_reset_fraction = float(config.get("projection_ratio_reset_fraction", 0.50))
    tanh_attenuation_reset_fraction = float(config.get("tanh_attenuation_reset_fraction", 0.50))

    snapshots: list[ExtremeSnapshot] = []
    scenario_rows: list[dict[str, Any]] = []
    for seed in range(int(seed_start), int(seed_start) + int(seed_count)):
        for fault in faults:
            scenario_snapshots, scenario_row = collect_fault_snapshots(
                model=model,
                env_config=env_config,
                fault=fault,
                seed=int(seed),
                start_snapshot_id=len(snapshots),
                min_step=min_step,
                max_steps=max_steps,
                snapshot_stride=snapshot_stride,
                max_snapshots_per_scenario=max_snapshots_per_scenario,
                obstacle_longitudinal_min=obstacle_longitudinal_min,
                obstacle_longitudinal_max=obstacle_longitudinal_max,
                device=resolved_device,
            )
            snapshots.extend(scenario_snapshots)
            scenario_rows.append(scenario_row)

    snapshots_by_seed: dict[int, list[ExtremeSnapshot]] = {}
    for snapshot in snapshots:
        snapshots_by_seed.setdefault(int(snapshot.seed), []).append(snapshot)

    row_metrics: list[dict[str, Any]] = []
    matched_rows: list[dict[str, Any]] = []
    rollout_rows: list[dict[str, Any]] = []
    unmatched_rows: list[dict[str, Any]] = []
    reset_hidden = model.initial_hidden(1, resolved_device)
    pair_id = 0
    for seed, seed_snapshots in sorted(snapshots_by_seed.items()):
        fault_snapshots = [snapshot for snapshot in seed_snapshots if snapshot.fault.name != "nominal"]
        for snapshot in fault_snapshots:
            if pair_id >= max_pairs:
                break
            matched, match_distance, pairing_rule = find_cross_fault_match(snapshot, seed_snapshots, pairing_rules)
            if matched is None:
                unmatched_rows.append(
                    {
                        "seed": int(seed),
                        "snapshot_id": int(snapshot.snapshot_id),
                        "fault_name": snapshot.fault.name,
                        "fault_family": snapshot.fault.family,
                        "fault_severity": snapshot.fault.severity,
                        "rejection_reason": "matched_state_empty",
                    }
                )
                continue
            pair_row, pair_rollouts, _, _ = evaluate_matched_pair(
                pair_id=pair_id,
                preferred=snapshot,
                wrong_history=matched,
                model=model,
                env_config=env_config,
                response_dim=response_dim,
                max_continuation_steps=max_continuation_steps,
                min_normal_margin=min_normal_margin,
                min_history_margin_gap=min_history_margin_gap,
                min_action_l2_gap=min_action_l2_gap,
                device=resolved_device,
            )
            pair_row["match_distance"] = float(match_distance)
            pair_row["pairing_rule"] = pairing_rule
            matched_rows.append(pair_row)
            rollout_rows.extend(pair_rollouts)
            wrong_metrics = compute_actor_head_coupling(
                model=model,
                observation=snapshot.observation,
                normal_hidden=snapshot.hidden,
                variant_hidden=matched.hidden,
                device=resolved_device,
                alphas=alphas,
                action_threshold=min_action_l2_gap,
            )
            reset_metrics = compute_actor_head_coupling(
                model=model,
                observation=snapshot.observation,
                normal_hidden=snapshot.hidden,
                variant_hidden=reset_hidden,
                device=resolved_device,
                alphas=alphas,
                action_threshold=min_action_l2_gap,
            )
            row_metrics.append(
                _variant_row(
                    pair_row=pair_row,
                    variant="normal_vs_wrong_history",
                    variant_margin=_finite_float(pair_row.get("wrong_margin")),
                    margin_gap=_finite_float(pair_row.get("history_margin_gap")),
                    success_drop=bool(pair_row.get("success_drop", False)),
                    metrics=wrong_metrics,
                )
            )
            row_metrics.append(
                _variant_row(
                    pair_row=pair_row,
                    variant="normal_vs_reset_hidden",
                    variant_margin=_finite_float(pair_row.get("reset_margin")),
                    margin_gap=_finite_float(pair_row.get("reset_margin_gap")),
                    success_drop=bool(pair_row.get("reset_success_drop", False)),
                    metrics=reset_metrics,
                )
            )
            pair_id += 1
        if pair_id >= max_pairs:
            break

    wrong_rows = [row for row in row_metrics if row.get("variant") == "normal_vs_wrong_history"]
    reset_rows = [row for row in row_metrics if row.get("variant") == "normal_vs_reset_hidden"]
    wrong_low_alpha = [row for row in wrong_rows if _finite_alpha(row) <= low_alpha_limit]
    wrong_high_alpha = [row for row in wrong_rows if _finite_alpha(row) <= high_alpha_limit]
    result_class = classify_actor_head_coupling_result(
        wrong_rows=len(wrong_rows),
        wrong_low_alpha_rows=len(wrong_low_alpha),
        wrong_high_alpha_rows=len(wrong_high_alpha),
        unique_low_alpha_fault_pairs=len({str(row.get("fault_family_pair", "")) for row in wrong_low_alpha}),
        wrong_projection_ratio_mean=_mean(wrong_rows, "projection_ratio"),
        reset_projection_ratio_mean=_mean(reset_rows, "projection_ratio"),
        wrong_tanh_attenuation_mean=_mean(wrong_rows, "tanh_attenuation_ratio"),
        reset_tanh_attenuation_mean=_mean(reset_rows, "tanh_attenuation_ratio"),
        wrong_feature_delta_mean=_mean(wrong_rows, "feature_delta_l2"),
        reset_feature_delta_mean=_mean(reset_rows, "feature_delta_l2"),
        min_low_alpha_rows=min_low_alpha_rows,
        min_unique_fault_pairs=min_unique_fault_pairs,
        projection_ratio_reset_fraction=projection_ratio_reset_fraction,
        tanh_attenuation_reset_fraction=tanh_attenuation_reset_fraction,
    )

    variant_summary = _coupling_group_summary(row_metrics, ("variant",))
    pair_variant_summary = _coupling_group_summary(row_metrics, ("fault_family_pair", "variant"))
    sentinel_summary = _coupling_group_summary(
        [row for row in row_metrics if bool(row.get("sentinel_pair", False))],
        ("variant",),
    )
    alpha_summary = _alpha_summary(row_metrics, alphas)
    write_csv_rows(run_dir / "scenario_summary.csv", scenario_rows)
    write_csv_rows(run_dir / "matched_cross_fault_pairs.csv", matched_rows)
    write_csv_rows(run_dir / "intervention_rollouts.csv", rollout_rows)
    write_csv_rows(run_dir / "row_actor_head_coupling.csv", row_metrics)
    write_csv_rows(run_dir / "variant_summary.csv", variant_summary)
    write_csv_rows(run_dir / "fault_family_pair_variant_summary.csv", pair_variant_summary)
    write_csv_rows(run_dir / "sentinel_summary.csv", sentinel_summary)
    write_csv_rows(run_dir / "alpha_summary.csv", alpha_summary)
    write_csv_rows(run_dir / "rejected_rows.csv", unmatched_rows)

    checksum_after = model_parameter_checksum(model)
    summary = {
        "run_type": "actor_head_history_signal_coupling_audit",
        "checkpoint": checkpoint_path,
        "config": config_path,
        "env_config": config.get("env_config"),
        "seed_start": int(seed_start),
        "seed_count": int(seed_count),
        "scenario_count": int(len(scenario_rows)),
        "snapshot_count": int(len(snapshots)),
        "matched_pair_count": int(len(matched_rows)),
        "unmatched_rows": int(len(unmatched_rows)),
        "row_count": int(len(row_metrics)),
        "wrong_rows": int(len(wrong_rows)),
        "reset_rows": int(len(reset_rows)),
        "wrong_low_alpha_rows": int(len(wrong_low_alpha)),
        "wrong_high_alpha_rows": int(len(wrong_high_alpha)),
        "unique_low_alpha_fault_pairs": int(len({str(row.get("fault_family_pair", "")) for row in wrong_low_alpha})),
        "thresholds": {
            "min_action_l2": min_action_l2_gap,
            "low_alpha_limit": low_alpha_limit,
            "high_alpha_limit": high_alpha_limit,
            "min_low_alpha_rows": min_low_alpha_rows,
            "min_unique_fault_pairs": min_unique_fault_pairs,
            "projection_ratio_reset_fraction": projection_ratio_reset_fraction,
            "tanh_attenuation_reset_fraction": tanh_attenuation_reset_fraction,
            "alphas": list(alphas),
        },
        "wrong_stats": {
            **_summary_stats(wrong_rows, "feature_delta_l2"),
            **_summary_stats(wrong_rows, "pre_tanh_delta_l2"),
            **_summary_stats(wrong_rows, "action_delta_l2"),
            **_summary_stats(wrong_rows, "projection_ratio"),
            **_summary_stats(wrong_rows, "tanh_attenuation_ratio"),
            **_summary_stats(wrong_rows, "feature_to_action_ratio"),
            **_summary_stats(wrong_rows, "alpha_to_action_threshold"),
        },
        "reset_stats": {
            **_summary_stats(reset_rows, "feature_delta_l2"),
            **_summary_stats(reset_rows, "pre_tanh_delta_l2"),
            **_summary_stats(reset_rows, "action_delta_l2"),
            **_summary_stats(reset_rows, "projection_ratio"),
            **_summary_stats(reset_rows, "tanh_attenuation_ratio"),
            **_summary_stats(reset_rows, "feature_to_action_ratio"),
            **_summary_stats(reset_rows, "alpha_to_action_threshold"),
        },
        "actor_parameters_changed": bool(checksum_before != checksum_after),
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "promoted": False,
        "result_class": result_class,
        "actor_head_coupling_positive": bool(result_class == "actor_head_coupling_positive"),
        "summary_json": run_dir / "summary.json",
        "row_actor_head_coupling_csv": run_dir / "row_actor_head_coupling.csv",
        "variant_summary_csv": run_dir / "variant_summary.csv",
        "fault_family_pair_variant_summary_csv": run_dir / "fault_family_pair_variant_summary.csv",
        "sentinel_summary_csv": run_dir / "sentinel_summary.csv",
        "alpha_summary_csv": run_dir / "alpha_summary.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit actor-head coupling for fused history feature deltas.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=41000)
    parser.add_argument("--seed-count", type=int, default=512)
    parser.add_argument("--alphas", type=str, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="actor_head_history_signal_coupling")
    summary = run_actor_head_history_signal_coupling_audit(
        checkpoint_path=args.checkpoint,
        config_path=args.config,
        seed_start=args.seed_start,
        seed_count=args.seed_count,
        device=args.device,
        run_dir=run_dir,
        alphas=parse_alphas(args.alphas),
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
