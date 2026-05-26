"""No-training target audit for behavior-improving low-tail direction families."""

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
from autodrift.public_base_controlled_fusion_surface_probe import _mean, _percentile
from autodrift.public_base_low_tail_metric_artifact_audit import (
    _direction_families,
    _direction_vector,
    _grounding_rows,
    _parse_float_tuple,
)
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
from autodrift.public_base_replay_constrained_target_feasibility import (
    DEFAULT_ACTIVE_ROW_IDS,
    DEFAULT_ENV_CONFIG,
    DEFAULT_M267_CORPUS,
    DEFAULT_M912_SUMMARY,
    _candidate_metrics,
    _m267_target_preflight,
    _summarize_m267_preflight,
    _strict_near_masks,
)
from autodrift.train_ppo import resolve_device
from autodrift.v4_sequence_objective_probe import _metadata_missing, _read_csv_rows


DEFAULT_RUN_DIR = Path("runs/m960_v4_public_base_low_tail_direction_family_target_audit")
DEFAULT_AMPLITUDES = (0.001, 0.002, 0.004, 0.006, 0.008)
PRIMARY_FAMILIES = frozenset(
    {
        "throttle_minus",
        "brake_plus",
        "toward_intervention",
        "steer_minus_brake_plus",
    }
)
SECONDARY_FAMILIES = frozenset({"steer_minus", "steer_plus_brake_plus"})
DIAGNOSTIC_ONLY_FAMILIES = frozenset(
    {
        "away_from_intervention",
        "throttle_plus",
        "brake_minus",
        "steer_plus",
    }
)


def classify_direction_family_target_audit(
    *,
    contract_changed: bool,
    training_started: bool,
    ppo_used: bool,
    promoted: bool,
    reconstruction_success_rate: float,
    metadata_missing_rows: int,
    direction_target_family_count: int,
    normal_retained_family_count: int,
    behavior_grounded_family_count: int,
    m267_target_preflight_pass_count: int,
    joint_direction_target_candidate_count: int,
) -> str:
    if bool(contract_changed) or bool(training_started) or bool(ppo_used) or bool(promoted):
        return "low_tail_direction_family_target_audit_contract_artifact"
    if float(reconstruction_success_rate) < 0.98 or int(metadata_missing_rows) > 0:
        return "low_tail_direction_family_target_audit_reconstruction_blocked"
    if int(direction_target_family_count) <= 0:
        return "low_tail_direction_family_target_audit_no_family"
    if int(joint_direction_target_candidate_count) > 0:
        return "low_tail_direction_family_target_audit_joint_candidate"
    if int(behavior_grounded_family_count) > 0 and int(normal_retained_family_count) <= 0:
        return "low_tail_direction_family_target_audit_normal_retention_failure"
    if int(behavior_grounded_family_count) > 0 and int(m267_target_preflight_pass_count) <= 0:
        return "low_tail_direction_family_target_audit_m267_preflight_failure"
    if int(normal_retained_family_count) > 0 and int(behavior_grounded_family_count) <= 0:
        return "low_tail_direction_family_target_audit_no_behavior_grounded_family"
    return "low_tail_direction_family_target_audit_target_source_refresh"


def _family_type(direction_family: str) -> str:
    if direction_family in PRIMARY_FAMILIES:
        return "primary"
    if direction_family in SECONDARY_FAMILIES:
        return "secondary"
    if direction_family in DIAGNOSTIC_ONLY_FAMILIES:
        return "diagnostic_only"
    return "unknown"


def _target_family_name(direction_family: str, amplitude: float) -> str:
    return f"{direction_family}_amp_{float(amplitude):.4f}".replace(".", "_")


def _direction_target_actions(
    *,
    base_normal: torch.Tensor,
    intervention: torch.Tensor,
    low_tail_indices: list[int],
    direction_family: str,
    amplitude: float,
) -> tuple[torch.Tensor, float]:
    candidate = base_normal.clone()
    clipped_rows = 0
    for index in low_tail_indices:
        direction = _direction_vector(direction_family, base_normal[index], intervention[index])
        raw = base_normal[index].detach().cpu().numpy().astype(np.float64) + float(amplitude) * direction
        clipped = np.clip(raw, -1.0, 1.0)
        if not np.allclose(raw, clipped, atol=1e-9, rtol=0.0):
            clipped_rows += 1
        candidate[index] = torch.as_tensor(clipped, dtype=base_normal.dtype, device=base_normal.device)
    clipping_fraction = float(clipped_rows / max(len(low_tail_indices), 1))
    return candidate, clipping_fraction


def _summarize_behavior(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    frame = pd.DataFrame(rows).copy()
    frame["target_family"] = [
        _target_family_name(str(row["direction_family"]), float(row["amplitude"]))
        for row in rows
    ]
    frame["family_type"] = [str(_family_type(str(row["direction_family"]))) for row in rows]
    summary_rows: list[dict[str, Any]] = []
    for target_family, group in frame.groupby("target_family", observed=True):
        terminal = group["terminal_margin_delta"].astype(float)
        success_delta = float(group["candidate_success"].astype(bool).mean() - group["base_success"].astype(bool).mean())
        collision_delta = float(group["candidate_collision"].astype(bool).mean() - group["base_collision"].astype(bool).mean())
        margin_mean_delta = _mean(terminal)
        margin_p10_delta = _percentile(terminal, 10)
        positive_margin_fraction = float(np.mean((terminal.to_numpy(dtype=np.float64) > 0.0).astype(np.float32)))
        direction_family = str(group["direction_family"].iloc[0])
        family_type = _family_type(direction_family)
        behavior_grounded = bool(
            margin_mean_delta > 0.0
            and margin_p10_delta >= 0.0
            and positive_margin_fraction >= 0.80
            and success_delta >= 0.0
            and collision_delta <= 0.0
            and family_type != "diagnostic_only"
        )
        summary_rows.append(
            {
                "target_family": str(target_family),
                "direction_family": direction_family,
                "family_type": family_type,
                "amplitude": float(group["amplitude"].iloc[0]),
                "rows": int(len(group)),
                "terminal_margin_mean_delta": margin_mean_delta,
                "terminal_margin_p10_delta": margin_p10_delta,
                "positive_margin_fraction": positive_margin_fraction,
                "success_delta": success_delta,
                "collision_delta": collision_delta,
                "proxy_improved_fraction": float(group["low_tail_proxy_improved"].astype(bool).mean()),
                "behavior_improved_fraction": float(group["behavior_improved"].astype(bool).mean()),
                "proxy_anti_aligned_but_behavior_grounded": bool(
                    behavior_grounded and float(group["low_tail_proxy_improved"].astype(bool).mean()) < 0.20
                ),
                "behavior_grounded": behavior_grounded,
            }
        )
    return summary_rows


def run_direction_family_target_audit(
    *,
    checkpoint_path: Path,
    positive_rows_path: Path,
    contrast_rows_path: Path,
    scenario_config_path: Path,
    target_rows_path: Path,
    m912_summary_path: Path,
    low_tail_rows_path: Path,
    m267_corpus_path: Path,
    env_config_path: Path,
    run_dir: Path,
    device: str,
    amplitudes: tuple[float, ...],
    max_low_tail_rows: int,
    active_row_ids: tuple[int, ...],
    max_continuation_steps: int,
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
    target_mask, low_tail_mask, target_actions, _target_weights, weight_rows, missing_target_keys = target_weight_vector(
        meta_rows=meta_rows,
        target_rows=target_rows,
        low_tail_rows=low_tail_rows,
        normal_actions=samples["normal_actions"],
    )
    strict_mask, near_mask = _strict_near_masks(meta_rows, target_rows, resolved_device)
    low_tail_indices = _selected_low_tail_indices(low_tail_mask, max_low_tail_rows)
    behavior_rows = _grounding_rows(
        model=model,
        meta_rows=meta_rows,
        samples=samples,
        low_tail_indices=low_tail_indices,
        env_config=env_config,
        amplitudes=amplitudes,
        max_continuation_steps=max_continuation_steps,
        device=resolved_device,
    )
    for row in behavior_rows:
        row["target_family"] = _target_family_name(str(row["direction_family"]), float(row["amplitude"]))
        row["family_type"] = _family_type(str(row["direction_family"]))
    behavior_summary = _summarize_behavior(behavior_rows)
    m912_summary = read_json(m912_summary_path)
    baseline_target_mse = torch.mean(
        (samples["normal_actions"][target_mask] - target_actions[target_mask]).pow(2),
        dim=-1,
    )
    baseline_target_mse_mean = float(baseline_target_mse.mean().detach().item()) if bool(target_mask.any()) else 0.0
    normal_retention_rows: list[dict[str, Any]] = []
    for direction_family in _direction_families():
        for amplitude in amplitudes:
            target_family = _target_family_name(direction_family, float(amplitude))
            candidate, clipping_fraction = _direction_target_actions(
                base_normal=samples["normal_actions"],
                intervention=samples["intervention_actions"],
                low_tail_indices=low_tail_indices,
                direction_family=direction_family,
                amplitude=float(amplitude),
            )
            metrics = _candidate_metrics(
                family=target_family,
                normal_actions=candidate,
                intervention_actions=samples["intervention_actions"],
                base_normal_actions=samples["normal_actions"],
                target_actions=target_actions,
                target_mask=target_mask,
                strict_mask=strict_mask,
                near_mask=near_mask,
                target_gaps=samples["target_gaps"],
                near_base_gap_p10=float(m912_summary["near_base_gap_p10"]),
                near_base_gap_deficit_mean=float(m912_summary["near_base_gap_deficit_mean"]),
                near_base_low_tail_fraction=float(m912_summary["low_tail_fraction"]),
                baseline_target_mse_mean=baseline_target_mse_mean,
            )
            metrics["direction_family"] = direction_family
            metrics["family_type"] = _family_type(direction_family)
            metrics["amplitude"] = float(amplitude)
            metrics["action_clipping_fraction"] = clipping_fraction
            metrics["normal_retention_pass"] = bool(metrics["normal_retention_pass"] and clipping_fraction <= 0.20)
            normal_retention_rows.append(metrics)
    family_names = [str(row["family"]) for row in normal_retention_rows]
    m267_preflight_rows = _m267_target_preflight(
        model=model,
        corpus_csv=m267_corpus_path,
        env_config_path=env_config_path,
        active_row_ids=active_row_ids,
        family_names=family_names,
        device=resolved_device,
        max_continuation_steps=max_continuation_steps,
    )
    m267_summary_rows = _summarize_m267_preflight(m267_preflight_rows)
    behavior_by_family = {str(row["target_family"]): row for row in behavior_summary}
    retention_by_family = {str(row["family"]): row for row in normal_retention_rows}
    m267_by_family = {str(row["family"]): row for row in m267_summary_rows}
    direction_summary_rows: list[dict[str, Any]] = []
    for family in sorted(set(retention_by_family) | set(behavior_by_family) | set(m267_by_family)):
        retention = retention_by_family.get(family, {})
        behavior = behavior_by_family.get(family, {})
        preflight = m267_by_family.get(family, {})
        direction_family = str(retention.get("direction_family", behavior.get("direction_family", "")))
        family_type = str(retention.get("family_type", behavior.get("family_type", _family_type(direction_family))))
        normal_retention_pass = bool(retention.get("normal_retention_pass", False))
        behavior_grounded = bool(behavior.get("behavior_grounded", False))
        m267_pass = bool(preflight.get("gate_pass", False))
        joint_candidate = bool(normal_retention_pass and behavior_grounded and m267_pass and family_type != "diagnostic_only")
        direction_summary_rows.append(
            {
                "target_family": family,
                "direction_family": direction_family,
                "family_type": family_type,
                "amplitude": float(retention.get("amplitude", behavior.get("amplitude", float("nan")))),
                "normal_retention_pass": normal_retention_pass,
                "behavior_grounded": behavior_grounded,
                "m267_target_preflight_pass": m267_pass,
                "joint_direction_target_candidate": joint_candidate,
                "terminal_margin_mean_delta": float(behavior.get("terminal_margin_mean_delta", float("nan"))),
                "terminal_margin_p10_delta": float(behavior.get("terminal_margin_p10_delta", float("nan"))),
                "positive_margin_fraction": float(behavior.get("positive_margin_fraction", float("nan"))),
                "success_delta": float(behavior.get("success_delta", float("nan"))),
                "collision_delta": float(behavior.get("collision_delta", float("nan"))),
                "proxy_improved_fraction": float(behavior.get("proxy_improved_fraction", float("nan"))),
                "proxy_anti_aligned_but_behavior_grounded": bool(
                    behavior.get("proxy_anti_aligned_but_behavior_grounded", False)
                ),
                "normal_anchor_mse_mean": float(retention.get("normal_anchor_mse_mean", float("nan"))),
                "normal_anchor_mse_p95": float(retention.get("normal_anchor_mse_p95", float("nan"))),
                "first_action_drift_from_base_mean": float(retention.get("first_action_drift_from_base_mean", float("nan"))),
                "first_action_drift_from_base_p95": float(retention.get("first_action_drift_from_base_p95", float("nan"))),
                "action_clipping_fraction": float(retention.get("action_clipping_fraction", float("nan"))),
                "old_low_tail_tail_lift_pass": bool(retention.get("tail_lift_pass", False)),
                "old_low_tail_target_tolerance_pass": bool(retention.get("target_tolerance_pass", False)),
                "m267_success_drop_count": int(preflight.get("candidate_success_drop_count", 0) or 0),
                "m267_failed_active_rows": str(preflight.get("failed_active_rows", "")),
            }
        )
    normal_retained_count = sum(
        1
        for row in direction_summary_rows
        if bool(row["normal_retention_pass"]) and str(row["family_type"]) != "diagnostic_only"
    )
    behavior_grounded_count = sum(
        1
        for row in direction_summary_rows
        if bool(row["behavior_grounded"]) and str(row["family_type"]) != "diagnostic_only"
    )
    m267_pass_count = sum(
        1
        for row in direction_summary_rows
        if bool(row["m267_target_preflight_pass"]) and str(row["family_type"]) != "diagnostic_only"
    )
    joint_candidate_rows = [row for row in direction_summary_rows if bool(row["joint_direction_target_candidate"])]
    primary_joint_rows = [row for row in joint_candidate_rows if str(row["family_type"]) == "primary"]
    best_candidates = primary_joint_rows or joint_candidate_rows
    best_joint_candidate_family = ""
    if best_candidates:
        best = max(
            best_candidates,
            key=lambda row: (
                float(row["terminal_margin_p10_delta"]),
                float(row["terminal_margin_mean_delta"]),
                -float(row["first_action_drift_from_base_mean"]),
            ),
        )
        best_joint_candidate_family = str(best["target_family"])
    result_class = classify_direction_family_target_audit(
        contract_changed=False,
        training_started=False,
        ppo_used=False,
        promoted=False,
        reconstruction_success_rate=reconstruction_rate,
        metadata_missing_rows=metadata_missing_rows,
        direction_target_family_count=len(direction_summary_rows),
        normal_retained_family_count=normal_retained_count,
        behavior_grounded_family_count=behavior_grounded_count,
        m267_target_preflight_pass_count=m267_pass_count,
        joint_direction_target_candidate_count=len(joint_candidate_rows),
    )
    if joint_candidate_rows:
        next_blocker = "direction target export and actor-fit objective design"
    elif behavior_grounded_count > 0 and normal_retained_count <= 0:
        next_blocker = "amplitude-calibrated direction target audit"
    elif behavior_grounded_count > 0 and m267_pass_count <= 0:
        next_blocker = "branch-separated direction target refinement"
    else:
        next_blocker = "target-source refresh"
    route_rows = [
        {
            "result_class": result_class,
            "normal_retained_family_count": int(normal_retained_count),
            "behavior_grounded_family_count": int(behavior_grounded_count),
            "m267_target_preflight_pass_count": int(m267_pass_count),
            "joint_direction_target_candidate_count": int(len(joint_candidate_rows)),
            "primary_joint_candidate_count": int(len(primary_joint_rows)),
            "best_joint_candidate_family": best_joint_candidate_family,
            "next_blocker": next_blocker,
        }
    ]
    write_csv_rows(run_dir / "direction_target_rows.csv", behavior_rows)
    write_csv_rows(run_dir / "direction_target_family_summary.csv", direction_summary_rows)
    write_csv_rows(run_dir / "normal_retention_metrics.csv", normal_retention_rows)
    write_csv_rows(run_dir / "m267_direction_target_preflight.csv", m267_summary_rows)
    write_csv_rows(run_dir / "m267_direction_target_preflight_rows.csv", m267_preflight_rows)
    write_csv_rows(run_dir / "route_decision.csv", route_rows)
    write_csv_rows(
        run_dir / "rejected_rows.csv",
        [
            *rejected_rows,
            *({"rejection_reason": "missing_target_join", "key": str(key)} for key in sorted(missing_target_keys)),
        ],
    )
    summary = {
        "run_type": "public_base_low_tail_direction_family_target_audit",
        "checkpoint": checkpoint_path,
        "positive_rows_input": positive_rows_path,
        "contrast_rows_input": contrast_rows_path,
        "scenario_config": scenario_config_path,
        "target_rows": target_rows_path,
        "m912_summary": m912_summary_path,
        "low_tail_rows": low_tail_rows_path,
        "m267_corpus": m267_corpus_path,
        "active_row_ids": list(active_row_ids),
        "positive_rows": int(len(positives)),
        "reconstructed_rows": int(len(meta_rows)),
        "sample_reconstruction_success_rate": reconstruction_rate,
        "metadata_missing_rows": int(metadata_missing_rows),
        "joined_target_rows": int(sum(1 for row in weight_rows if bool(row.get("target_available", False)))),
        "missing_target_keys": int(len(missing_target_keys)),
        "low_tail_rows_count": int(low_tail_mask.detach().cpu().sum().item()),
        "evaluated_low_tail_rows": int(len(low_tail_indices)),
        "amplitudes": [float(value) for value in amplitudes],
        "direction_family_count": int(len(_direction_families())),
        "primary_family_count": int(len(PRIMARY_FAMILIES)),
        "direction_target_family_count": int(len(direction_summary_rows)),
        "normal_retained_family_count": int(normal_retained_count),
        "behavior_grounded_family_count": int(behavior_grounded_count),
        "m267_target_preflight_pass_count": int(m267_pass_count),
        "joint_direction_target_candidate_count": int(len(joint_candidate_rows)),
        "primary_joint_candidate_count": int(len(primary_joint_rows)),
        "best_joint_candidate_family": best_joint_candidate_family,
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
        "direction_target_family_summary_csv": run_dir / "direction_target_family_summary.csv",
        "direction_target_rows_csv": run_dir / "direction_target_rows.csv",
        "normal_retention_metrics_csv": run_dir / "normal_retention_metrics.csv",
        "m267_direction_target_preflight_csv": run_dir / "m267_direction_target_preflight.csv",
        "route_decision_csv": run_dir / "route_decision.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def _parse_int_tuple(raw: str) -> tuple[int, ...]:
    return tuple(int(item) for item in str(raw).split(",") if item.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training low-tail direction-family target audit.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_BASE_CHECKPOINT)
    parser.add_argument("--positive-rows", type=Path, default=DEFAULT_POSITIVE_ROWS)
    parser.add_argument("--contrast-rows", type=Path, default=DEFAULT_CONTRAST_ROWS)
    parser.add_argument("--scenario-config", type=Path, default=DEFAULT_SCENARIO_CONFIG)
    parser.add_argument("--target-rows", type=Path, default=DEFAULT_TARGET_ROWS)
    parser.add_argument("--m912-summary", type=Path, default=DEFAULT_M912_SUMMARY)
    parser.add_argument("--low-tail-rows", type=Path, default=DEFAULT_LOW_TAIL_ROWS)
    parser.add_argument("--m267-corpus", type=Path, default=DEFAULT_M267_CORPUS)
    parser.add_argument("--env-config", type=Path, default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--amplitudes", type=_parse_float_tuple, default=DEFAULT_AMPLITUDES)
    parser.add_argument("--max-low-tail-rows", type=int, default=DEFAULT_MAX_LOW_TAIL_ROWS)
    parser.add_argument("--active-row-ids", type=_parse_int_tuple, default=DEFAULT_ACTIVE_ROW_IDS)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    args = parser.parse_args()
    summary = run_direction_family_target_audit(
        checkpoint_path=args.checkpoint,
        positive_rows_path=args.positive_rows,
        contrast_rows_path=args.contrast_rows,
        scenario_config_path=args.scenario_config,
        target_rows_path=args.target_rows,
        m912_summary_path=args.m912_summary,
        low_tail_rows_path=args.low_tail_rows,
        m267_corpus_path=args.m267_corpus,
        env_config_path=args.env_config,
        run_dir=args.run_dir,
        device=args.device,
        amplitudes=args.amplitudes,
        max_low_tail_rows=args.max_low_tail_rows,
        active_row_ids=args.active_row_ids,
        max_continuation_steps=args.max_continuation_steps,
    )
    print(f"result_class={summary['result_class']}")
    print(f"joint_direction_target_candidate_count={summary['joint_direction_target_candidate_count']}")
    print(f"summary={summary['summary_json']}")


if __name__ == "__main__":
    main()
