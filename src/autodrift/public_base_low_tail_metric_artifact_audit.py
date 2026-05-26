"""No-training grounding audit for low-tail action-gap target metrics."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import load_scenario_config
from autodrift.matched_history_outcome_gate import collect_requested_outcome_snapshots
from autodrift.public_base_controlled_fusion_surface_probe import _mean, _percentile
from autodrift.public_base_low_tail_sequence_target_audit import (
    DEFAULT_AMPLITUDES,
    DEFAULT_BASE_CHECKPOINT,
    DEFAULT_CONTRAST_ROWS,
    DEFAULT_LOW_TAIL_ROWS,
    DEFAULT_MAX_LOW_TAIL_ROWS,
    DEFAULT_POSITIVE_ROWS,
    DEFAULT_RUN_DIR as _SEQUENCE_RUN_DIR,
    DEFAULT_SCENARIO_CONFIG,
    DEFAULT_TARGET_ROWS,
    _replay_sequence_delta,
    _safe_margin,
    _selected_low_tail_indices,
    _snapshot,
    _unit_direction,
)
from autodrift.public_base_regenerated_target_residual_probe import target_weight_vector
from autodrift.train_ppo import resolve_device
from autodrift.v4_sequence_objective_probe import _metadata_missing, _read_csv_rows


DEFAULT_RUN_DIR = Path("runs/m958_v4_public_base_low_tail_target_metric_artifact_audit")


def classify_metric_artifact_audit(
    *,
    contract_changed: bool,
    training_started: bool,
    ppo_used: bool,
    promoted: bool,
    reconstruction_success_rate: float,
    metadata_missing_rows: int,
    direction_family_count: int,
    target_metric_artifact: bool,
    direction_sign_suspicion: bool,
    threshold_only_issue: bool,
    behavior_improved_family_count: int,
) -> str:
    if bool(contract_changed) or bool(training_started) or bool(ppo_used) or bool(promoted):
        return "low_tail_metric_artifact_audit_contract_artifact"
    if float(reconstruction_success_rate) < 0.98 or int(metadata_missing_rows) > 0:
        return "low_tail_metric_artifact_audit_reconstruction_blocked"
    if int(direction_family_count) <= 0:
        return "low_tail_metric_artifact_audit_no_direction_family"
    if bool(direction_sign_suspicion):
        return "low_tail_metric_artifact_audit_direction_sign_suspicion"
    if bool(target_metric_artifact):
        return "low_tail_metric_artifact_audit_target_metric_artifact"
    if bool(threshold_only_issue):
        return "low_tail_metric_artifact_audit_threshold_only_issue"
    if int(behavior_improved_family_count) <= 0:
        return "low_tail_metric_artifact_audit_target_source_refresh"
    return "low_tail_metric_artifact_audit_inconclusive"


def _parse_float_tuple(raw: str) -> tuple[float, ...]:
    return tuple(float(item) for item in str(raw).split(",") if item.strip())


def _direction_vector(name: str, normal_action: torch.Tensor, intervention_action: torch.Tensor) -> np.ndarray:
    if name == "away_from_intervention":
        return _unit_direction(normal_action, intervention_action)
    if name == "toward_intervention":
        return -_unit_direction(normal_action, intervention_action)
    axis = {
        "steer_plus": np.asarray([1.0, 0.0, 0.0], dtype=np.float64),
        "steer_minus": np.asarray([-1.0, 0.0, 0.0], dtype=np.float64),
        "brake_plus": np.asarray([0.0, 0.0, 1.0], dtype=np.float64),
        "brake_minus": np.asarray([0.0, 0.0, -1.0], dtype=np.float64),
        "throttle_plus": np.asarray([0.0, 1.0, 0.0], dtype=np.float64),
        "throttle_minus": np.asarray([0.0, -1.0, 0.0], dtype=np.float64),
        "steer_plus_brake_plus": np.asarray([1.0, 0.0, 1.0], dtype=np.float64),
        "steer_minus_brake_plus": np.asarray([-1.0, 0.0, 1.0], dtype=np.float64),
    }.get(name)
    if axis is None:
        raise ValueError(f"unknown direction family: {name}")
    norm = float(np.linalg.norm(axis))
    return axis / norm if norm > 0.0 else axis


def _direction_families() -> tuple[str, ...]:
    return (
        "away_from_intervention",
        "toward_intervention",
        "steer_plus",
        "steer_minus",
        "brake_plus",
        "brake_minus",
        "throttle_plus",
        "throttle_minus",
        "steer_plus_brake_plus",
        "steer_minus_brake_plus",
    )


def _safe_spearman(frame: pd.DataFrame, x: str, y: str) -> float:
    values = frame[[x, y]].replace([np.inf, -np.inf], np.nan).dropna()
    if len(values) < 3:
        return float("nan")
    return float(values[x].corr(values[y], method="spearman"))


def _grounding_rows(
    *,
    model: Any,
    meta_rows: list[dict[str, Any]],
    samples: dict[str, torch.Tensor],
    low_tail_indices: list[int],
    env_config: Any,
    amplitudes: tuple[float, ...],
    max_continuation_steps: int,
    device: torch.device,
) -> list[dict[str, Any]]:
    requests: dict[int, set[int]] = {}
    for index in low_tail_indices:
        row = meta_rows[index]
        requests.setdefault(int(row["seed"]), set()).add(int(row["step"]))
    snapshots = collect_requested_outcome_snapshots(
        model=model,
        env_config=env_config,
        requests=requests,
        device=device,
    )
    rows: list[dict[str, Any]] = []
    for index in low_tail_indices:
        row = meta_rows[index]
        snapshot = _snapshot(snapshots, int(row["seed"]), int(row["step"]))
        normal_action = samples["normal_actions"][index]
        intervention_action = samples["intervention_actions"][index]
        target_gap = float(samples["target_gaps"][index].detach().cpu().item())
        base_gap = float(torch.linalg.norm(normal_action - intervention_action).detach().cpu().item())
        base_deficit = max(0.0, target_gap - base_gap)
        base_result, _base_actions = _replay_sequence_delta(
            model=model,
            snapshot=snapshot,
            env_config=env_config,
            hidden=snapshot.hidden,
            direction=np.zeros(3, dtype=np.float64),
            schedule=np.zeros(1, dtype=np.float64),
            max_continuation_steps=max_continuation_steps,
            device=device,
        )
        base_margin = _safe_margin(base_result)
        for direction_name in _direction_families():
            direction = _direction_vector(direction_name, normal_action, intervention_action)
            for amplitude in amplitudes:
                candidate_action_np = np.clip(
                    normal_action.detach().cpu().numpy().astype(np.float64) + float(amplitude) * direction,
                    -1.0,
                    1.0,
                )
                candidate_action = torch.as_tensor(candidate_action_np, dtype=torch.float32, device=normal_action.device)
                candidate_gap = float(torch.linalg.norm(candidate_action - intervention_action).detach().cpu().item())
                candidate_deficit = max(0.0, target_gap - candidate_gap)
                proxy_delta = candidate_gap - base_gap
                deficit_delta = candidate_deficit - base_deficit
                result, _actions = _replay_sequence_delta(
                    model=model,
                    snapshot=snapshot,
                    env_config=env_config,
                    hidden=snapshot.hidden,
                    direction=direction,
                    schedule=np.asarray([float(amplitude)], dtype=np.float64),
                    max_continuation_steps=max_continuation_steps,
                    device=device,
                )
                margin = _safe_margin(result)
                terminal_margin_delta = margin - base_margin if np.isfinite(margin) and np.isfinite(base_margin) else float("nan")
                success_delta = float(bool(result["success"])) - float(bool(base_result["success"]))
                collision_delta = float(bool(result["collision"])) - float(bool(base_result["collision"]))
                proxy_improved = bool(proxy_delta > 0.0 and deficit_delta < 0.0)
                behavior_improved = bool(
                    np.isfinite(terminal_margin_delta)
                    and terminal_margin_delta > 0.0
                    and success_delta >= 0.0
                    and collision_delta <= 0.0
                )
                rows.append(
                    {
                        "direction_family": direction_name,
                        "amplitude": float(amplitude),
                        "contrast_group_id": str(row.get("contrast_group_id", "")),
                        "source_index": str(row.get("source_index", "")),
                        "seed": int(row["seed"]),
                        "step": int(row["step"]),
                        "variant": str(row.get("variant", "")),
                        "base_gap": base_gap,
                        "candidate_gap": candidate_gap,
                        "normal_intervention_gap_delta": proxy_delta,
                        "base_gap_deficit": base_deficit,
                        "candidate_gap_deficit": candidate_deficit,
                        "gap_deficit_delta": deficit_delta,
                        "low_tail_proxy_improved": proxy_improved,
                        "base_margin": base_margin,
                        "candidate_margin": margin,
                        "terminal_margin_delta": terminal_margin_delta,
                        "base_success": bool(base_result["success"]),
                        "candidate_success": bool(result["success"]),
                        "success_delta": success_delta,
                        "base_collision": bool(base_result["collision"]),
                        "candidate_collision": bool(result["collision"]),
                        "collision_delta": collision_delta,
                        "behavior_improved": behavior_improved,
                        "proxy_improved_behavior_worse": bool(proxy_improved and np.isfinite(terminal_margin_delta) and terminal_margin_delta < 0.0),
                    }
                )
    return rows


def _summarize_grounding(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not rows:
        return [], []
    frame = pd.DataFrame(rows)
    summary_rows: list[dict[str, Any]] = []
    corr_rows: list[dict[str, Any]] = []
    for family, group in frame.groupby("direction_family", observed=True):
        proxy_improved = group["low_tail_proxy_improved"].astype(bool)
        behavior_improved = group["behavior_improved"].astype(bool)
        proxy_worse = group["proxy_improved_behavior_worse"].astype(bool)
        proxy_and_behavior = proxy_improved & behavior_improved
        terminal = group["terminal_margin_delta"].astype(float)
        proxy_delta = group["normal_intervention_gap_delta"].astype(float)
        deficit_delta = group["gap_deficit_delta"].astype(float)
        proxy_fraction = float(proxy_improved.mean())
        behavior_fraction = float(behavior_improved.mean())
        proxy_behavior_fraction = float(proxy_and_behavior.mean())
        proxy_worse_fraction = float(proxy_worse.mean())
        artifact_like = bool(proxy_fraction >= 0.50 and proxy_behavior_fraction < 0.20 and proxy_worse_fraction >= 0.50)
        summary_rows.append(
            {
                "direction_family": str(family),
                "rows": int(len(group)),
                "proxy_improved_fraction": proxy_fraction,
                "behavior_improved_fraction": behavior_fraction,
                "proxy_and_behavior_improved_fraction": proxy_behavior_fraction,
                "proxy_improved_behavior_worse_fraction": proxy_worse_fraction,
                "terminal_margin_mean_delta": _mean(terminal),
                "terminal_margin_p10_delta": _percentile(terminal, 10),
                "positive_margin_fraction": float(np.mean((terminal.to_numpy(dtype=np.float64) > 0.0).astype(np.float32))),
                "gap_delta_mean": _mean(proxy_delta),
                "gap_deficit_delta_mean": _mean(deficit_delta),
                "artifact_like": artifact_like,
            }
        )
        corr_rows.append(
            {
                "direction_family": str(family),
                "rows": int(len(group)),
                "spearman_gap_delta_vs_margin": _safe_spearman(group, "normal_intervention_gap_delta", "terminal_margin_delta"),
                "spearman_deficit_delta_vs_margin": _safe_spearman(group, "gap_deficit_delta", "terminal_margin_delta"),
            }
        )
    return summary_rows, corr_rows


def run_low_tail_metric_artifact_audit(
    *,
    checkpoint_path: Path,
    positive_rows_path: Path,
    contrast_rows_path: Path,
    scenario_config_path: Path,
    target_rows_path: Path,
    low_tail_rows_path: Path,
    run_dir: Path,
    device: str,
    amplitudes: tuple[float, ...],
    max_low_tail_rows: int,
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
    _target_mask, low_tail_mask, _target_actions, _target_weights, _weight_rows, missing_target_keys = target_weight_vector(
        meta_rows=meta_rows,
        target_rows=target_rows,
        low_tail_rows=low_tail_rows,
        normal_actions=samples["normal_actions"],
    )
    low_tail_indices = _selected_low_tail_indices(low_tail_mask, max_low_tail_rows)
    row_metrics = _grounding_rows(
        model=model,
        meta_rows=meta_rows,
        samples=samples,
        low_tail_indices=low_tail_indices,
        env_config=env_config,
        amplitudes=amplitudes,
        max_continuation_steps=max_continuation_steps,
        device=resolved_device,
    )
    family_summary, correlation_rows = _summarize_grounding(row_metrics)
    family_by_name = {str(row["direction_family"]): row for row in family_summary}
    away = family_by_name.get("away_from_intervention", {})
    toward = family_by_name.get("toward_intervention", {})
    direction_sign_suspicion = bool(
        float(away.get("proxy_improved_fraction", 0.0)) >= 0.50
        and float(away.get("terminal_margin_mean_delta", 0.0)) < 0.0
        and float(toward.get("terminal_margin_mean_delta", 0.0)) > 0.0
    )
    artifact_families = [row for row in family_summary if bool(row.get("artifact_like", False))]
    target_metric_artifact = bool(artifact_families and not direction_sign_suspicion)
    behavior_improved_family_count = sum(1 for row in family_summary if float(row.get("behavior_improved_fraction", 0.0)) >= 0.20)
    threshold_only_issue = bool(
        not target_metric_artifact
        and not direction_sign_suspicion
        and behavior_improved_family_count > 0
        and any(float(row.get("proxy_and_behavior_improved_fraction", 0.0)) >= 0.20 for row in family_summary)
    )
    result_class = classify_metric_artifact_audit(
        contract_changed=False,
        training_started=False,
        ppo_used=False,
        promoted=False,
        reconstruction_success_rate=reconstruction_rate,
        metadata_missing_rows=metadata_missing_rows,
        direction_family_count=len(family_summary),
        target_metric_artifact=target_metric_artifact,
        direction_sign_suspicion=direction_sign_suspicion,
        threshold_only_issue=threshold_only_issue,
        behavior_improved_family_count=behavior_improved_family_count,
    )
    if target_metric_artifact:
        next_blocker = "low-tail target redefinition design"
    elif direction_sign_suspicion:
        next_blocker = "direction-family target audit"
    elif threshold_only_issue:
        next_blocker = "exact threshold sensitivity audit"
    else:
        next_blocker = "target-source refresh"
    route_rows = [
        {
            "target_metric_artifact": bool(target_metric_artifact),
            "direction_sign_suspicion": bool(direction_sign_suspicion),
            "threshold_only_issue": bool(threshold_only_issue),
            "behavior_improved_family_count": int(behavior_improved_family_count),
            "result_class": result_class,
            "next_blocker": next_blocker,
        }
    ]
    write_csv_rows(run_dir / "row_metric_grounding.csv", row_metrics)
    write_csv_rows(run_dir / "direction_family_summary.csv", family_summary)
    write_csv_rows(run_dir / "proxy_behavior_correlation.csv", correlation_rows)
    write_csv_rows(run_dir / "route_decision.csv", route_rows)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
    summary = {
        "run_type": "public_base_low_tail_metric_artifact_audit",
        "checkpoint": checkpoint_path,
        "positive_rows_input": positive_rows_path,
        "contrast_rows_input": contrast_rows_path,
        "scenario_config": scenario_config_path,
        "target_rows": target_rows_path,
        "low_tail_rows": low_tail_rows_path,
        "positive_rows": int(len(positives)),
        "reconstructed_rows": int(len(meta_rows)),
        "sample_reconstruction_success_rate": reconstruction_rate,
        "metadata_missing_rows": int(metadata_missing_rows),
        "missing_target_keys": int(len(missing_target_keys)),
        "low_tail_rows_count": int(low_tail_mask.detach().cpu().sum().item()),
        "evaluated_low_tail_rows": int(len(low_tail_indices)),
        "amplitudes": [float(value) for value in amplitudes],
        "direction_family_count": int(len(family_summary)),
        "row_metric_count": int(len(row_metrics)),
        "proxy_improved_behavior_worse_family_count": int(len(artifact_families)),
        "behavior_improved_family_count": int(behavior_improved_family_count),
        "direction_sign_suspicion": bool(direction_sign_suspicion),
        "target_metric_artifact": bool(target_metric_artifact),
        "threshold_only_issue": bool(threshold_only_issue),
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
        "direction_family_summary_csv": run_dir / "direction_family_summary.csv",
        "row_metric_grounding_csv": run_dir / "row_metric_grounding.csv",
        "proxy_behavior_correlation_csv": run_dir / "proxy_behavior_correlation.csv",
        "route_decision_csv": run_dir / "route_decision.csv",
        "sequence_run_dir_reference": _SEQUENCE_RUN_DIR,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training low-tail target metric artifact audit.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_BASE_CHECKPOINT)
    parser.add_argument("--positive-rows", type=Path, default=DEFAULT_POSITIVE_ROWS)
    parser.add_argument("--contrast-rows", type=Path, default=DEFAULT_CONTRAST_ROWS)
    parser.add_argument("--scenario-config", type=Path, default=DEFAULT_SCENARIO_CONFIG)
    parser.add_argument("--target-rows", type=Path, default=DEFAULT_TARGET_ROWS)
    parser.add_argument("--low-tail-rows", type=Path, default=DEFAULT_LOW_TAIL_ROWS)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--amplitudes", type=_parse_float_tuple, default=DEFAULT_AMPLITUDES)
    parser.add_argument("--max-low-tail-rows", type=int, default=DEFAULT_MAX_LOW_TAIL_ROWS)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    args = parser.parse_args()
    summary = run_low_tail_metric_artifact_audit(
        checkpoint_path=args.checkpoint,
        positive_rows_path=args.positive_rows,
        contrast_rows_path=args.contrast_rows,
        scenario_config_path=args.scenario_config,
        target_rows_path=args.target_rows,
        low_tail_rows_path=args.low_tail_rows,
        run_dir=args.run_dir,
        device=args.device,
        amplitudes=args.amplitudes,
        max_low_tail_rows=args.max_low_tail_rows,
        max_continuation_steps=args.max_continuation_steps,
    )
    print(f"result_class={summary['result_class']}")
    print(f"target_metric_artifact={summary['target_metric_artifact']}")
    print(f"summary={summary['summary_json']}")


if __name__ == "__main__":
    main()
