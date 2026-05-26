"""No-training export for accepted M960 direction targets."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import load_scenario_config
from autodrift.public_base_low_tail_direction_family_target_audit import (
    _direction_target_actions,
)
from autodrift.public_base_low_tail_metric_artifact_audit import _direction_vector
from autodrift.public_base_low_tail_sequence_target_audit import (
    DEFAULT_BASE_CHECKPOINT,
    DEFAULT_CONTRAST_ROWS,
    DEFAULT_LOW_TAIL_ROWS,
    DEFAULT_MAX_LOW_TAIL_ROWS,
    DEFAULT_POSITIVE_ROWS,
    DEFAULT_SCENARIO_CONFIG,
    DEFAULT_TARGET_ROWS,
    _selected_low_tail_indices,
)
from autodrift.public_base_regenerated_target_residual_probe import target_weight_vector
from autodrift.train_ppo import resolve_device
from autodrift.v4_sequence_objective_probe import _metadata_missing, _read_csv_rows


DEFAULT_RUN_DIR = Path("runs/m962_v4_public_base_direction_target_export")
DEFAULT_M960_RUN_DIR = Path("runs/m960_v4_public_base_low_tail_direction_family_target_audit")
DEFAULT_FAMILY_SUMMARY = DEFAULT_M960_RUN_DIR / "direction_target_family_summary.csv"
DEFAULT_TARGET_ROWS_METRICS = DEFAULT_M960_RUN_DIR / "direction_target_rows.csv"
DEFAULT_M267_PREFLIGHT_ROWS = DEFAULT_M960_RUN_DIR / "m267_direction_target_preflight_rows.csv"
DEFAULT_MAX_RETENTION_ANCHORS = 0
FAMILY_WEIGHTS = {
    "throttle_minus": 1.00,
    "toward_intervention": 0.80,
    "brake_plus": 0.80,
    "steer_minus_brake_plus": 0.70,
}


def classify_direction_target_export(
    *,
    contract_changed: bool,
    training_started: bool,
    ppo_used: bool,
    promoted: bool,
    accepted_family_count: int,
    accepted_target_count: int,
    diagnostic_target_count: int,
    proof_target_count: int,
    retention_anchor_count: int,
    max_direction_family_fraction: float,
) -> str:
    if bool(contract_changed) or bool(training_started) or bool(ppo_used) or bool(promoted):
        return "direction_target_export_contract_artifact"
    if int(diagnostic_target_count) > 0:
        return "direction_target_export_diagnostic_family_leak"
    if int(accepted_family_count) <= 0 or int(accepted_target_count) <= 0:
        return "direction_target_export_no_accepted_targets"
    if int(proof_target_count) <= 0:
        return "direction_target_export_missing_proof_targets"
    if int(retention_anchor_count) <= 0:
        return "direction_target_export_missing_retention_anchors"
    if float(max_direction_family_fraction) > 0.40:
        return "direction_target_export_source_dominated"
    return "direction_target_export_pass"


def _read_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def _accepted_families(frame: pd.DataFrame) -> list[dict[str, Any]]:
    accepted = frame[
        (frame["family_type"].astype(str) == "primary")
        & (frame["normal_retention_pass"].map(_read_bool))
        & (frame["behavior_grounded"].map(_read_bool))
        & (frame["m267_target_preflight_pass"].map(_read_bool))
        & (frame["joint_direction_target_candidate"].map(_read_bool))
    ].copy()
    accepted = accepted.sort_values(
        ["terminal_margin_p10_delta", "terminal_margin_mean_delta"],
        ascending=[False, False],
    ).reset_index(drop=True)
    rows: list[dict[str, Any]] = []
    for rank, (_, row) in enumerate(accepted.iterrows(), start=1):
        item = row.to_dict()
        item["family_rank"] = int(rank)
        item["recommended_weight"] = float(FAMILY_WEIGHTS.get(str(row["direction_family"]), 0.5))
        item["export_role"] = "accepted_direction_target"
        rows.append(item)
    return rows


def _rejected_export_candidates(frame: pd.DataFrame, accepted_names: set[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        name = str(row["target_family"])
        if name in accepted_names:
            continue
        family_type = str(row.get("family_type", ""))
        if family_type == "diagnostic_only":
            reason = "diagnostic_only_anti_aligned"
        elif family_type == "secondary":
            reason = "secondary_family_not_training_target"
        elif not _read_bool(row.get("normal_retention_pass", False)):
            reason = "normal_retention_failed"
        elif not _read_bool(row.get("behavior_grounded", False)):
            reason = "behavior_grounding_failed"
        elif not _read_bool(row.get("m267_target_preflight_pass", False)):
            reason = "m267_preflight_failed"
        else:
            reason = "not_accepted"
        rows.append(
            {
                "target_family": name,
                "direction_family": str(row.get("direction_family", "")),
                "family_type": family_type,
                "amplitude": float(row.get("amplitude", float("nan"))),
                "rejection_reason": reason,
                "terminal_margin_mean_delta": float(row.get("terminal_margin_mean_delta", float("nan"))),
                "terminal_margin_p10_delta": float(row.get("terminal_margin_p10_delta", float("nan"))),
                "normal_retention_pass": _read_bool(row.get("normal_retention_pass", False)),
                "behavior_grounded": _read_bool(row.get("behavior_grounded", False)),
                "m267_target_preflight_pass": _read_bool(row.get("m267_target_preflight_pass", False)),
            }
        )
    return rows


def _row_key(row: dict[str, Any]) -> tuple[int, int, str, str]:
    return (
        int(row.get("seed", -1)),
        int(row.get("step", -1)),
        str(row.get("variant", "")),
        str(row.get("source_index", "")),
    )


def _metric_by_family_and_row(metric_rows: list[dict[str, Any]]) -> dict[tuple[str, tuple[int, int, str, str]], dict[str, Any]]:
    return {
        (str(row["target_family"]), _row_key(row)): row
        for row in metric_rows
    }


def _accepted_target_rows(
    *,
    accepted_families: list[dict[str, Any]],
    meta_rows: list[dict[str, Any]],
    normal_actions: torch.Tensor,
    intervention_actions: torch.Tensor,
    low_tail_indices: list[int],
    metric_lookup: dict[tuple[str, tuple[int, int, str, str]], dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family in accepted_families:
        target_family = str(family["target_family"])
        direction_family = str(family["direction_family"])
        amplitude = float(family["amplitude"])
        candidate_actions, _clip = _direction_target_actions(
            base_normal=normal_actions,
            intervention=intervention_actions,
            low_tail_indices=low_tail_indices,
            direction_family=direction_family,
            amplitude=amplitude,
        )
        for index in low_tail_indices:
            meta = meta_rows[index]
            key = _row_key(meta)
            metric = metric_lookup.get((target_family, key), {})
            base = normal_actions[index].detach().cpu().numpy().astype(np.float64)
            target = candidate_actions[index].detach().cpu().numpy().astype(np.float64)
            delta = target - base
            rows.append(
                {
                    "target_id": f"{target_family}|{int(meta['seed'])}|{int(meta['step'])}|{index}",
                    "target_family": target_family,
                    "direction_family": direction_family,
                    "amplitude": amplitude,
                    "family_rank": int(family["family_rank"]),
                    "seed": int(meta["seed"]),
                    "step": int(meta["step"]),
                    "variant": str(meta.get("variant", "")),
                    "contrast_group_id": str(meta.get("contrast_group_id", "")),
                    "source_index": str(meta.get("source_index", "")),
                    "base_steer": float(base[0]),
                    "base_throttle": float(base[1]),
                    "base_brake": float(base[2]),
                    "target_steer": float(target[0]),
                    "target_throttle": float(target[1]),
                    "target_brake": float(target[2]),
                    "delta_steer": float(delta[0]),
                    "delta_throttle": float(delta[1]),
                    "delta_brake": float(delta[2]),
                    "terminal_margin_delta": float(metric.get("terminal_margin_delta", float("nan"))),
                    "terminal_margin_p10_delta_family": float(family.get("terminal_margin_p10_delta", float("nan"))),
                    "positive_margin_fraction_family": float(family.get("positive_margin_fraction", float("nan"))),
                    "normal_anchor_mse_mean_family": float(family.get("normal_anchor_mse_mean", float("nan"))),
                    "first_action_drift_mean_family": float(family.get("first_action_drift_from_base_mean", float("nan"))),
                    "m267_target_preflight_pass": _read_bool(family.get("m267_target_preflight_pass", False)),
                    "target_weight": float(family["recommended_weight"]),
                }
            )
    return rows


def _family_catalog(accepted_families: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in accepted_families:
        rows.append(
            {
                "target_family": str(row["target_family"]),
                "direction_family": str(row["direction_family"]),
                "amplitude": float(row["amplitude"]),
                "family_rank": int(row["family_rank"]),
                "terminal_margin_mean_delta": float(row["terminal_margin_mean_delta"]),
                "terminal_margin_p10_delta": float(row["terminal_margin_p10_delta"]),
                "positive_margin_fraction": float(row["positive_margin_fraction"]),
                "normal_retention_pass": _read_bool(row["normal_retention_pass"]),
                "normal_anchor_mse_mean": float(row["normal_anchor_mse_mean"]),
                "first_action_drift_from_base_mean": float(row["first_action_drift_from_base_mean"]),
                "m267_target_preflight_pass": _read_bool(row["m267_target_preflight_pass"]),
                "recommended_weight": float(row["recommended_weight"]),
                "export_role": str(row["export_role"]),
            }
        )
    return rows


def _proof_targets(preflight_rows: list[dict[str, Any]], accepted_names: set[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in preflight_rows:
        family = str(row["family"])
        if family not in accepted_names:
            continue
        base_normal = [
            float(row["normal_first_steer"]),
            float(row["normal_first_throttle"]),
            float(row["normal_first_brake"]),
        ]
        base_wrong = [
            float(row["wrong_first_steer"]),
            float(row["wrong_first_throttle"]),
            float(row["wrong_first_brake"]),
        ]
        common = {
            "proof_row_id": int(row["row_id"]),
            "target_family": family,
            "target": str(row.get("target", "")),
            "physical_pair_key": str(row.get("physical_pair_key", "")),
            "left_seed": int(row["left_seed"]),
            "right_seed": int(row["right_seed"]),
            "left_step": int(row["left_step"]),
            "right_step": int(row["right_step"]),
            "success_drop_required": True,
        }
        rows.append(
            {
                **common,
                "branch": "normal",
                "base_steer": base_normal[0],
                "base_throttle": base_normal[1],
                "base_brake": base_normal[2],
                "target_steer": base_normal[0],
                "target_throttle": base_normal[1],
                "target_brake": base_normal[2],
                "target_role": "normal_success_anchor",
                "expected_success": True,
                "expected_wrong_history_success": False,
            }
        )
        rows.append(
            {
                **common,
                "branch": "wrong_history",
                "base_steer": base_wrong[0],
                "base_throttle": base_wrong[1],
                "base_brake": base_wrong[2],
                "target_steer": base_wrong[0],
                "target_throttle": base_wrong[1],
                "target_brake": base_wrong[2],
                "target_role": "wrong_failure_anchor",
                "expected_success": False,
                "expected_wrong_history_success": False,
            }
        )
    return rows


def _retention_anchor_rows(
    *,
    meta_rows: list[dict[str, Any]],
    normal_actions: torch.Tensor,
    selected_low_tail_indices: set[int],
    max_rows: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, meta in enumerate(meta_rows):
        if index in selected_low_tail_indices:
            continue
        action = normal_actions[index].detach().cpu().numpy().astype(np.float64)
        rows.append(
            {
                "seed": int(meta["seed"]),
                "step": int(meta["step"]),
                "variant": str(meta.get("variant", "")),
                "source_index": str(meta.get("source_index", "")),
                "base_steer": float(action[0]),
                "base_throttle": float(action[1]),
                "base_brake": float(action[2]),
                "target_steer": float(action[0]),
                "target_throttle": float(action[1]),
                "target_brake": float(action[2]),
                "anchor_weight": 0.5,
                "anchor_role": "non_target_positive_anchor",
            }
        )
        if int(max_rows) > 0 and len(rows) >= int(max_rows):
            break
    return rows


def _direction_family_fraction(target_rows: list[dict[str, Any]]) -> float:
    if not target_rows:
        return 0.0
    frame = pd.DataFrame(target_rows)
    fractions = frame["direction_family"].value_counts(normalize=True)
    return float(fractions.max()) if not fractions.empty else 0.0


def run_direction_target_export(
    *,
    checkpoint_path: Path,
    positive_rows_path: Path,
    contrast_rows_path: Path,
    scenario_config_path: Path,
    target_rows_path: Path,
    low_tail_rows_path: Path,
    family_summary_path: Path,
    target_metrics_path: Path,
    m267_preflight_rows_path: Path,
    run_dir: Path,
    device: str,
    max_low_tail_rows: int,
    max_retention_anchors: int,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    scenario_config = load_scenario_config(scenario_config_path)
    env_config = load_env_config(Path(scenario_config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    positives = _read_csv_rows(positive_rows_path)
    contrast_rows = _read_csv_rows(contrast_rows_path)
    target_rows = _read_csv_rows(target_rows_path)
    low_tail_rows = _read_csv_rows(low_tail_rows_path)
    metadata_missing_rows = sum(1 for row in positives if _metadata_missing(row))

    from autodrift.public_base_controlled_fusion_surface_probe import _load_trainable_samples

    samples, meta_rows, rejected_rows = _load_trainable_samples(
        model=model,
        positive_rows=positives,
        contrast_rows=contrast_rows,
        scenario_config=scenario_config,
        env_config=env_config,
        device=resolved_device,
    )
    reconstruction_rate = float(len(meta_rows) / max(len(positives), 1))
    _target_mask, low_tail_mask, _target_actions, _target_weights, _weight_rows, missing_target_keys = target_weight_vector(
        meta_rows=meta_rows,
        target_rows=target_rows,
        low_tail_rows=low_tail_rows,
        normal_actions=samples["normal_actions"],
    )
    low_tail_indices = _selected_low_tail_indices(low_tail_mask, max_low_tail_rows)
    family_frame = pd.read_csv(family_summary_path)
    accepted_families = _accepted_families(family_frame)
    accepted_names = {str(row["target_family"]) for row in accepted_families}
    rejected_export_rows = _rejected_export_candidates(family_frame, accepted_names)
    target_metric_rows = _read_csv_rows(target_metrics_path)
    metric_lookup = _metric_by_family_and_row(target_metric_rows)
    accepted_targets = _accepted_target_rows(
        accepted_families=accepted_families,
        meta_rows=meta_rows,
        normal_actions=samples["normal_actions"],
        intervention_actions=samples["intervention_actions"],
        low_tail_indices=low_tail_indices,
        metric_lookup=metric_lookup,
    )
    catalog_rows = _family_catalog(accepted_families)
    proof_rows = _proof_targets(_read_csv_rows(m267_preflight_rows_path), accepted_names)
    retention_rows = _retention_anchor_rows(
        meta_rows=meta_rows,
        normal_actions=samples["normal_actions"],
        selected_low_tail_indices=set(low_tail_indices),
        max_rows=max_retention_anchors,
    )
    diagnostic_target_count = sum(1 for row in accepted_targets if str(row["direction_family"]) not in FAMILY_WEIGHTS)
    max_direction_family_fraction = _direction_family_fraction(accepted_targets)
    result_class = classify_direction_target_export(
        contract_changed=False,
        training_started=False,
        ppo_used=False,
        promoted=False,
        accepted_family_count=len(accepted_families),
        accepted_target_count=len(accepted_targets),
        diagnostic_target_count=diagnostic_target_count,
        proof_target_count=len(proof_rows),
        retention_anchor_count=len(retention_rows),
        max_direction_family_fraction=max_direction_family_fraction,
    )
    if result_class == "direction_target_export_pass":
        next_blocker = "direction-target actor-fit objective implementation"
    elif result_class == "direction_target_export_source_dominated":
        next_blocker = "source-diverse direction target refresh"
    elif result_class == "direction_target_export_missing_proof_targets":
        next_blocker = "branch-separated direction target refinement"
    else:
        next_blocker = "direction target export repair"
    route_rows = [
        {
            "result_class": result_class,
            "accepted_family_count": int(len(accepted_families)),
            "accepted_direction_target_count": int(len(accepted_targets)),
            "branch_separated_proof_target_count": int(len(proof_rows)),
            "retention_anchor_count": int(len(retention_rows)),
            "diagnostic_target_count": int(diagnostic_target_count),
            "max_direction_family_fraction": max_direction_family_fraction,
            "next_blocker": next_blocker,
        }
    ]
    write_csv_rows(run_dir / "accepted_direction_targets.csv", accepted_targets)
    write_csv_rows(run_dir / "direction_target_family_catalog.csv", catalog_rows)
    write_csv_rows(run_dir / "branch_separated_proof_targets.csv", proof_rows)
    write_csv_rows(run_dir / "retention_anchor_targets.csv", retention_rows)
    write_csv_rows(run_dir / "rejected_export_candidates.csv", rejected_export_rows)
    write_csv_rows(run_dir / "route_decision.csv", route_rows)
    write_csv_rows(
        run_dir / "rejected_rows.csv",
        [
            *rejected_rows,
            *({"rejection_reason": "missing_target_join", "key": str(key)} for key in sorted(missing_target_keys)),
        ],
    )
    summary = {
        "run_type": "public_base_direction_target_export",
        "checkpoint": checkpoint_path,
        "positive_rows_input": positive_rows_path,
        "contrast_rows_input": contrast_rows_path,
        "scenario_config": scenario_config_path,
        "target_rows": target_rows_path,
        "low_tail_rows": low_tail_rows_path,
        "family_summary": family_summary_path,
        "target_metrics": target_metrics_path,
        "m267_preflight_rows": m267_preflight_rows_path,
        "positive_rows": int(len(positives)),
        "reconstructed_rows": int(len(meta_rows)),
        "sample_reconstruction_success_rate": reconstruction_rate,
        "metadata_missing_rows": int(metadata_missing_rows),
        "missing_target_keys": int(len(missing_target_keys)),
        "low_tail_rows_count": int(low_tail_mask.detach().cpu().sum().item()),
        "evaluated_low_tail_rows": int(len(low_tail_indices)),
        "accepted_family_count": int(len(accepted_families)),
        "accepted_direction_target_count": int(len(accepted_targets)),
        "branch_separated_proof_target_count": int(len(proof_rows)),
        "retention_anchor_count": int(len(retention_rows)),
        "rejected_export_candidate_count": int(len(rejected_export_rows)),
        "diagnostic_target_count": int(diagnostic_target_count),
        "max_direction_family_fraction": max_direction_family_fraction,
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "actor_input_contract_changed": False,
        "private_holdout_used": False,
        "result_class": result_class,
        "next_blocker": next_blocker,
        "summary_json": run_dir / "summary.json",
        "accepted_direction_targets_csv": run_dir / "accepted_direction_targets.csv",
        "direction_target_family_catalog_csv": run_dir / "direction_target_family_catalog.csv",
        "branch_separated_proof_targets_csv": run_dir / "branch_separated_proof_targets.csv",
        "retention_anchor_targets_csv": run_dir / "retention_anchor_targets.csv",
        "rejected_export_candidates_csv": run_dir / "rejected_export_candidates.csv",
        "route_decision_csv": run_dir / "route_decision.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Export accepted direction targets without training.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_BASE_CHECKPOINT)
    parser.add_argument("--positive-rows", type=Path, default=DEFAULT_POSITIVE_ROWS)
    parser.add_argument("--contrast-rows", type=Path, default=DEFAULT_CONTRAST_ROWS)
    parser.add_argument("--scenario-config", type=Path, default=DEFAULT_SCENARIO_CONFIG)
    parser.add_argument("--target-rows", type=Path, default=DEFAULT_TARGET_ROWS)
    parser.add_argument("--low-tail-rows", type=Path, default=DEFAULT_LOW_TAIL_ROWS)
    parser.add_argument("--family-summary", type=Path, default=DEFAULT_FAMILY_SUMMARY)
    parser.add_argument("--target-metrics", type=Path, default=DEFAULT_TARGET_ROWS_METRICS)
    parser.add_argument("--m267-preflight-rows", type=Path, default=DEFAULT_M267_PREFLIGHT_ROWS)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--max-low-tail-rows", type=int, default=DEFAULT_MAX_LOW_TAIL_ROWS)
    parser.add_argument("--max-retention-anchors", type=int, default=DEFAULT_MAX_RETENTION_ANCHORS)
    args = parser.parse_args()
    summary = run_direction_target_export(
        checkpoint_path=args.checkpoint,
        positive_rows_path=args.positive_rows,
        contrast_rows_path=args.contrast_rows,
        scenario_config_path=args.scenario_config,
        target_rows_path=args.target_rows,
        low_tail_rows_path=args.low_tail_rows,
        family_summary_path=args.family_summary,
        target_metrics_path=args.target_metrics,
        m267_preflight_rows_path=args.m267_preflight_rows,
        run_dir=args.run_dir,
        device=args.device,
        max_low_tail_rows=args.max_low_tail_rows,
        max_retention_anchors=args.max_retention_anchors,
    )
    print(f"result_class={summary['result_class']}")
    print(f"accepted_direction_target_count={summary['accepted_direction_target_count']}")
    print(f"summary={summary['summary_json']}")


if __name__ == "__main__":
    main()
