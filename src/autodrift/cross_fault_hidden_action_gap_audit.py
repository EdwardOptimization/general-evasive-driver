"""No-training hidden/action gap audit for cross-fault history pairs."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
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


SENTINEL_FAULT_PAIRS = {
    "front_lateral_authority_drop->steering_fault",
    "front_lateral_authority_drop->combined_fault",
    "steering_fault->front_lateral_authority_drop",
    "combined_fault->front_lateral_authority_drop",
}


def _l2(left: torch.Tensor, right: torch.Tensor) -> float:
    return float(torch.linalg.vector_norm(left.detach().float() - right.detach().float()).item())


def _safe_ratio(numerator: float, denominator: float) -> float:
    if not np.isfinite(numerator) or not np.isfinite(denominator) or abs(float(denominator)) <= 1e-12:
        return float("nan")
    return float(numerator / denominator)


def compute_hidden_action_gaps(
    *,
    model: ActorCritic,
    observation: np.ndarray,
    normal_hidden: torch.Tensor,
    variant_hidden: torch.Tensor,
    device: torch.device,
) -> dict[str, float]:
    obs_t = torch.as_tensor(observation, dtype=torch.float32, device=device).unsqueeze(0)
    normal_hidden_t = normal_hidden.to(device=device, dtype=torch.float32)
    variant_hidden_t = variant_hidden.to(device=device, dtype=torch.float32)
    with torch.no_grad():
        normal_features, normal_next_hidden = model.recurrent_features_tensor(obs_t, normal_hidden_t)
        variant_features, variant_next_hidden = model.recurrent_features_tensor(obs_t, variant_hidden_t)
        normal_action = torch.tanh(model.actor_mean(normal_features))
        variant_action = torch.tanh(model.actor_mean(variant_features))
    raw_hidden_l2 = _l2(normal_hidden_t, variant_hidden_t)
    next_hidden_l2 = _l2(normal_next_hidden, variant_next_hidden)
    fused_feature_l2 = _l2(normal_features, variant_features)
    action_l2 = _l2(normal_action, variant_action)
    return {
        "raw_hidden_l2": raw_hidden_l2,
        "next_hidden_l2": next_hidden_l2,
        "fused_feature_l2": fused_feature_l2,
        "action_l2": action_l2,
        "raw_to_next_retention": _safe_ratio(next_hidden_l2, raw_hidden_l2),
        "raw_to_fused_retention": _safe_ratio(fused_feature_l2, raw_hidden_l2),
        "feature_to_action_retention": _safe_ratio(action_l2, fused_feature_l2),
    }


def classify_hidden_action_gap_result(
    *,
    wrong_rows: int,
    wrong_raw_positive_rows: int,
    wrong_fused_positive_rows: int,
    wrong_action_positive_rows: int,
    wrong_outcome_positive_rows: int,
    wrong_joint_positive_rows: int,
    reset_action_positive_rows: int,
    reset_outcome_positive_rows: int,
    unique_wrong_joint_fault_pairs: int,
    min_positive_rows: int,
    min_unique_fault_pairs: int,
) -> str:
    if int(wrong_rows) == 0:
        return "matched_state_empty"
    if int(wrong_joint_positive_rows) >= int(min_positive_rows) and int(unique_wrong_joint_fault_pairs) >= int(
        min_unique_fault_pairs
    ):
        return "history_incompatibility_positive"
    if int(wrong_raw_positive_rows) == 0:
        return "raw_hidden_collapse"
    if int(wrong_fused_positive_rows) == 0:
        return "fusion_washout"
    if int(wrong_action_positive_rows) == 0:
        return "action_washout"
    if int(wrong_outcome_positive_rows) == 0:
        return "outcome_insensitive"
    if int(reset_action_positive_rows) > 0 and int(reset_outcome_positive_rows) > 0:
        return "reset_disruption_only"
    return "history_incompatibility_sparse"


def _mean(rows: list[dict[str, Any]], key: str) -> float:
    values = [_finite_float(row.get(key)) for row in rows]
    finite = [value for value in values if np.isfinite(value)]
    return float(np.mean(finite)) if finite else float("nan")


def _percentile(rows: list[dict[str, Any]], key: str, percentile: float) -> float:
    values = sorted(_finite_float(row.get(key)) for row in rows)
    finite = [value for value in values if np.isfinite(value)]
    if not finite:
        return float("nan")
    index = int(round((len(finite) - 1) * float(percentile)))
    return float(finite[min(max(index, 0), len(finite) - 1)])


def _group_summary(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
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
                "raw_hidden_l2_mean": _mean(group_rows, "raw_hidden_l2"),
                "next_hidden_l2_mean": _mean(group_rows, "next_hidden_l2"),
                "fused_feature_l2_mean": _mean(group_rows, "fused_feature_l2"),
                "action_l2_mean": _mean(group_rows, "action_l2"),
                "action_l2_p95": _percentile(group_rows, "action_l2", 0.95),
                "margin_gap_mean": _mean(group_rows, "margin_gap"),
                "margin_gap_p95": _percentile(group_rows, "margin_gap", 0.95),
                "raw_to_next_retention_mean": _mean(group_rows, "raw_to_next_retention"),
                "raw_to_fused_retention_mean": _mean(group_rows, "raw_to_fused_retention"),
                "feature_to_action_retention_mean": _mean(group_rows, "feature_to_action_retention"),
            }
        )
        output.append(item)
    return output


def _summary_stats(rows: list[dict[str, Any]], key: str) -> dict[str, float]:
    return {
        f"{key}_mean": _mean(rows, key),
        f"{key}_p50": _percentile(rows, key, 0.50),
        f"{key}_p90": _percentile(rows, key, 0.90),
        f"{key}_p95": _percentile(rows, key, 0.95),
        f"{key}_p99": _percentile(rows, key, 0.99),
        f"{key}_max": max(
            [_finite_float(row.get(key)) for row in rows if np.isfinite(_finite_float(row.get(key)))],
            default=float("nan"),
        ),
    }


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
    gaps: dict[str, float],
) -> dict[str, Any]:
    row = _pair_metadata(pair_row)
    row.update(
        {
            "variant": variant,
            "variant_margin": _finite_float(variant_margin),
            "margin_gap": _finite_float(margin_gap),
            "success_drop": bool(success_drop),
            **gaps,
        }
    )
    return row


def run_cross_fault_hidden_action_gap_audit(
    *,
    checkpoint_path: Path,
    config_path: Path,
    seed_start: int,
    seed_count: int,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    config = load_scenario_config(config_path)
    pairing_rules = tuple(config.get("pairing_rules", ()))
    if not pairing_rules:
        raise ValueError("cross-fault hidden/action audit requires config pairing_rules")
    env_config = load_env_config(Path(config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    if not model.is_online_recurrent:
        raise ValueError("cross-fault hidden/action audit requires an online recurrent checkpoint")
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
    min_wrong_raw_hidden_l2 = float(config.get("min_wrong_raw_hidden_l2", 0.05))
    min_wrong_fused_feature_l2 = float(config.get("min_wrong_fused_feature_l2", 0.01))
    min_wrong_margin_gap = float(config.get("min_wrong_margin_gap", min_history_margin_gap))
    min_positive_rows = int(config.get("min_positive_rows", 30))
    min_unique_fault_pairs = int(config.get("min_unique_fault_pairs", 4))

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

    row_gaps: list[dict[str, Any]] = []
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
            wrong_gaps = compute_hidden_action_gaps(
                model=model,
                observation=snapshot.observation,
                normal_hidden=snapshot.hidden,
                variant_hidden=matched.hidden,
                device=resolved_device,
            )
            reset_gaps = compute_hidden_action_gaps(
                model=model,
                observation=snapshot.observation,
                normal_hidden=snapshot.hidden,
                variant_hidden=reset_hidden,
                device=resolved_device,
            )
            row_gaps.append(
                _variant_row(
                    pair_row=pair_row,
                    variant="normal_vs_wrong_history",
                    variant_margin=_finite_float(pair_row.get("wrong_margin")),
                    margin_gap=_finite_float(pair_row.get("history_margin_gap")),
                    success_drop=bool(pair_row.get("success_drop", False)),
                    gaps=wrong_gaps,
                )
            )
            row_gaps.append(
                _variant_row(
                    pair_row=pair_row,
                    variant="normal_vs_reset_hidden",
                    variant_margin=_finite_float(pair_row.get("reset_margin")),
                    margin_gap=_finite_float(pair_row.get("reset_margin_gap")),
                    success_drop=bool(pair_row.get("reset_success_drop", False)),
                    gaps=reset_gaps,
                )
            )
            pair_id += 1
        if pair_id >= max_pairs:
            break

    wrong_rows = [row for row in row_gaps if row.get("variant") == "normal_vs_wrong_history"]
    reset_rows = [row for row in row_gaps if row.get("variant") == "normal_vs_reset_hidden"]
    wrong_raw_positive = [row for row in wrong_rows if _finite_float(row.get("raw_hidden_l2")) >= min_wrong_raw_hidden_l2]
    wrong_fused_positive = [
        row for row in wrong_rows if _finite_float(row.get("fused_feature_l2")) >= min_wrong_fused_feature_l2
    ]
    wrong_action_positive = [row for row in wrong_rows if _finite_float(row.get("action_l2")) >= min_action_l2_gap]
    wrong_outcome_positive = [
        row
        for row in wrong_rows
        if bool(row.get("success_drop", False)) or _finite_float(row.get("margin_gap")) >= min_wrong_margin_gap
    ]
    wrong_joint_positive = [
        row
        for row in wrong_rows
        if _finite_float(row.get("action_l2")) >= min_action_l2_gap
        and (bool(row.get("success_drop", False)) or _finite_float(row.get("margin_gap")) >= min_wrong_margin_gap)
    ]
    reset_action_positive = [row for row in reset_rows if _finite_float(row.get("action_l2")) >= min_action_l2_gap]
    reset_outcome_positive = [
        row
        for row in reset_rows
        if bool(row.get("success_drop", False)) or _finite_float(row.get("margin_gap")) >= min_history_margin_gap
    ]
    result_class = classify_hidden_action_gap_result(
        wrong_rows=len(wrong_rows),
        wrong_raw_positive_rows=len(wrong_raw_positive),
        wrong_fused_positive_rows=len(wrong_fused_positive),
        wrong_action_positive_rows=len(wrong_action_positive),
        wrong_outcome_positive_rows=len(wrong_outcome_positive),
        wrong_joint_positive_rows=len(wrong_joint_positive),
        reset_action_positive_rows=len(reset_action_positive),
        reset_outcome_positive_rows=len(reset_outcome_positive),
        unique_wrong_joint_fault_pairs=len({str(row.get("fault_family_pair", "")) for row in wrong_joint_positive}),
        min_positive_rows=min_positive_rows,
        min_unique_fault_pairs=min_unique_fault_pairs,
    )

    variant_summary = _group_summary(row_gaps, ("variant",))
    pair_variant_summary = _group_summary(row_gaps, ("fault_family_pair", "variant"))
    sentinel_summary = _group_summary([row for row in row_gaps if bool(row.get("sentinel_pair", False))], ("variant",))
    write_csv_rows(run_dir / "scenario_summary.csv", scenario_rows)
    write_csv_rows(run_dir / "matched_cross_fault_pairs.csv", matched_rows)
    write_csv_rows(run_dir / "intervention_rollouts.csv", rollout_rows)
    write_csv_rows(run_dir / "row_hidden_action_gaps.csv", row_gaps)
    write_csv_rows(run_dir / "variant_summary.csv", variant_summary)
    write_csv_rows(run_dir / "fault_family_pair_variant_summary.csv", pair_variant_summary)
    write_csv_rows(run_dir / "sentinel_summary.csv", sentinel_summary)
    write_csv_rows(run_dir / "rejected_rows.csv", unmatched_rows)

    checksum_after = model_parameter_checksum(model)
    summary = {
        "run_type": "cross_fault_hidden_action_gap_audit",
        "checkpoint": checkpoint_path,
        "config": config_path,
        "env_config": config.get("env_config"),
        "seed_start": int(seed_start),
        "seed_count": int(seed_count),
        "scenario_count": int(len(scenario_rows)),
        "snapshot_count": int(len(snapshots)),
        "matched_pair_count": int(len(matched_rows)),
        "unmatched_rows": int(len(unmatched_rows)),
        "row_count": int(len(row_gaps)),
        "wrong_rows": int(len(wrong_rows)),
        "reset_rows": int(len(reset_rows)),
        "wrong_raw_positive_rows": int(len(wrong_raw_positive)),
        "wrong_fused_positive_rows": int(len(wrong_fused_positive)),
        "wrong_action_positive_rows": int(len(wrong_action_positive)),
        "wrong_outcome_positive_rows": int(len(wrong_outcome_positive)),
        "wrong_joint_positive_rows": int(len(wrong_joint_positive)),
        "reset_action_positive_rows": int(len(reset_action_positive)),
        "reset_outcome_positive_rows": int(len(reset_outcome_positive)),
        "unique_wrong_joint_fault_pairs": int(
            len({str(row.get("fault_family_pair", "")) for row in wrong_joint_positive})
        ),
        "sentinel_rows": int(sum(1 for row in row_gaps if bool(row.get("sentinel_pair", False)))),
        "thresholds": {
            "min_wrong_raw_hidden_l2": min_wrong_raw_hidden_l2,
            "min_wrong_fused_feature_l2": min_wrong_fused_feature_l2,
            "min_wrong_action_l2": min_action_l2_gap,
            "min_wrong_margin_gap": min_wrong_margin_gap,
            "min_positive_rows": min_positive_rows,
            "min_unique_fault_pairs": min_unique_fault_pairs,
        },
        "wrong_stats": {
            **_summary_stats(wrong_rows, "raw_hidden_l2"),
            **_summary_stats(wrong_rows, "next_hidden_l2"),
            **_summary_stats(wrong_rows, "fused_feature_l2"),
            **_summary_stats(wrong_rows, "action_l2"),
            **_summary_stats(wrong_rows, "margin_gap"),
        },
        "reset_stats": {
            **_summary_stats(reset_rows, "raw_hidden_l2"),
            **_summary_stats(reset_rows, "next_hidden_l2"),
            **_summary_stats(reset_rows, "fused_feature_l2"),
            **_summary_stats(reset_rows, "action_l2"),
            **_summary_stats(reset_rows, "margin_gap"),
        },
        "actor_parameters_changed": bool(checksum_before != checksum_after),
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "promoted": False,
        "result_class": result_class,
        "history_incompatibility_positive": bool(result_class == "history_incompatibility_positive"),
        "summary_json": run_dir / "summary.json",
        "row_hidden_action_gaps_csv": run_dir / "row_hidden_action_gaps.csv",
        "variant_summary_csv": run_dir / "variant_summary.csv",
        "fault_family_pair_variant_summary_csv": run_dir / "fault_family_pair_variant_summary.csv",
        "sentinel_summary_csv": run_dir / "sentinel_summary.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit cross-fault hidden/action gaps without training.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=41000)
    parser.add_argument("--seed-count", type=int, default=512)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="cross_fault_hidden_action_gap_audit")
    summary = run_cross_fault_hidden_action_gap_audit(
        checkpoint_path=args.checkpoint,
        config_path=args.config,
        seed_start=args.seed_start,
        seed_count=args.seed_count,
        device=args.device,
        run_dir=run_dir,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
