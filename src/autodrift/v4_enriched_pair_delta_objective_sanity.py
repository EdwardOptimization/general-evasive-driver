"""Exact no-update sanity metrics for enriched pair-delta objective rows."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import time
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import NOMINAL_FAULT, load_scenario_config
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import resolve_device
from autodrift.v4_low_margin_new_data_route import build_fault_variants
from autodrift.v4_residual_closed_loop_replay import _load_residual_head
from autodrift.v4_wrong_cross_fault_history_intervention import GATE_SUMMARY_FIELDS, _as_int, read_csv_rows, reconstruct_snapshots


ACTION_COMPONENTS = ("steer", "throttle", "brake")


def action_vector(row: dict[str, Any], prefix: str) -> np.ndarray:
    return np.asarray([_finite_float(row.get(f"{prefix}_{name}")) for name in ACTION_COMPONENTS], dtype=np.float32)


def pair_requests(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[int, int, int, int]] = set()
    requests: list[dict[str, Any]] = []
    for row in rows:
        key = (
            _as_int(row.get("left_source_group_id")),
            _as_int(row.get("right_source_group_id")),
            _as_int(row.get("left_step")),
            _as_int(row.get("right_step")),
        )
        if key in seen:
            continue
        seen.add(key)
        requests.append(
            {
                "left_source_group_id": key[0],
                "right_source_group_id": key[1],
                "left_step": key[2],
                "right_step": key[3],
            }
        )
    return requests


def row_weight(row: dict[str, Any]) -> float:
    base = max(_finite_float(row.get("objective_sample_weight"), default=1.0), 0.0)
    outcome = float(np.clip(abs(_finite_float(row.get("abs_margin_delta"), default=0.0)) / 0.01, 1.0, 5.0))
    collision_bonus = 2.0 if str(row.get("terminal_reason", "")).strip() == "collision" else 1.0
    return float(np.clip(base * outcome * collision_bonus, 1.0, 10.0))


def classify_enriched_pair_delta_objective_sanity(
    *,
    tensor_rows_reconstructed: int,
    expected_rows: int,
    missing_tensor_count: int,
    exact_losses_finite: bool,
    improvement_rows_present: bool,
    degradation_rows_present: bool,
    per_split_metrics_written: bool,
    actor_parameters_changed: bool,
) -> str:
    if bool(actor_parameters_changed):
        return "v4_enriched_pair_delta_objective_sanity_metadata_artifact"
    if int(tensor_rows_reconstructed) <= 0 or int(tensor_rows_reconstructed) != int(expected_rows) or int(missing_tensor_count) > 0:
        return "v4_enriched_pair_delta_objective_sanity_reconstruction_blocked"
    if not bool(exact_losses_finite) or not bool(improvement_rows_present) or not bool(degradation_rows_present):
        return "v4_enriched_pair_delta_objective_sanity_degenerate"
    if not bool(per_split_metrics_written):
        return "v4_enriched_pair_delta_objective_sanity_metadata_artifact"
    return "v4_enriched_pair_delta_objective_sanity_pass"


def _split_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("split", ""))].append(row)
    output: list[dict[str, Any]] = []
    for split, group in sorted(grouped.items()):
        values = lambda name: [_finite_float(row.get(name)) for row in group]
        finite_losses = [value for value in values("objective_loss") if np.isfinite(value)]
        output.append(
            {
                "split": split,
                "rows": len(group),
                "improvement_rows": sum(1 for row in group if str(row.get("accepted_class", "")) == "pair_delta_improvement"),
                "degradation_rows": sum(1 for row in group if str(row.get("accepted_class", "")) == "pair_delta_degradation"),
                "objective_loss_mean": float(np.mean(finite_losses)) if finite_losses else float("nan"),
                "normal_logp_mean": _mean(values("normal_logp")),
                "override_logp_mean": _mean(values("override_logp")),
                "logp_gap_mean": _mean(values("logp_gap")),
                "weight_mean": _mean(values("weight")),
            }
        )
    return output


def _mean(values: list[float]) -> float:
    finite = [float(value) for value in values if np.isfinite(float(value))]
    return float(np.mean(finite)) if finite else float("nan")


def _all_finite(values: list[float]) -> bool:
    return bool(values) and all(np.isfinite(float(value)) for value in values)


def _log_prob_action(model: Any, observation: np.ndarray, hidden: torch.Tensor, action: np.ndarray, device: torch.device) -> float:
    obs_t = torch.as_tensor(observation, dtype=torch.float32, device=device).unsqueeze(0)
    hidden_t = hidden.to(device=device, dtype=torch.float32)
    if hidden_t.ndim == 1:
        hidden_t = hidden_t.unsqueeze(0)
    action_t = torch.as_tensor(action, dtype=torch.float32, device=device).unsqueeze(0)
    with torch.no_grad():
        log_prob, _entropy, _value = model.evaluate_actions_recurrent(obs_t, action_t, hidden_t)
    return float(log_prob.squeeze(0).detach().cpu().item())


def _objective_row(
    *,
    row: dict[str, Any],
    normal_logp: float,
    override_logp: float,
    margin: float,
) -> dict[str, Any]:
    accepted_class = str(row.get("accepted_class", ""))
    weight = row_weight(row)
    if accepted_class == "pair_delta_improvement":
        objective_loss = float(weight * torch.nn.functional.softplus(torch.tensor(normal_logp - override_logp + margin)).item())
    elif accepted_class == "pair_delta_degradation":
        objective_loss = float(weight * torch.nn.functional.softplus(torch.tensor(override_logp - normal_logp + margin)).item())
    else:
        objective_loss = float("nan")
    return {
        "split": row.get("split", ""),
        "pair_id": row.get("pair_id", ""),
        "dedup_signature": row.get("dedup_signature", ""),
        "left_source_group_id": row.get("left_source_group_id", ""),
        "left_step": row.get("left_step", ""),
        "accepted_class": accepted_class,
        "margin_delta": row.get("margin_delta", ""),
        "abs_margin_delta": row.get("abs_margin_delta", ""),
        "terminal_reason": row.get("terminal_reason", ""),
        "weight": weight,
        "normal_logp": normal_logp,
        "override_logp": override_logp,
        "logp_gap": float(override_logp - normal_logp),
        "objective_loss": objective_loss,
    }


def _gate_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "gate_name": "tensor_rows_reconstructed",
            "value": summary["tensor_rows_reconstructed"],
            "threshold": summary["expected_rows"],
            "passed": int(summary["tensor_rows_reconstructed"]) == int(summary["expected_rows"]),
            "notes": "all split rows need exact actor state tensors",
        },
        {
            "gate_name": "missing_tensor_count",
            "value": summary["missing_tensor_count"],
            "threshold": "0",
            "passed": int(summary["missing_tensor_count"]) == 0,
            "notes": "no row may silently use reset or mismatched hidden",
        },
        {
            "gate_name": "exact_losses_finite",
            "value": summary["exact_losses_finite"],
            "threshold": "true",
            "passed": bool(summary["exact_losses_finite"]),
            "notes": "objective logprob losses must be finite",
        },
        {
            "gate_name": "improvement_rows_present",
            "value": summary["improvement_rows_present"],
            "threshold": "true",
            "passed": bool(summary["improvement_rows_present"]),
            "notes": "improvement preference term must be represented",
        },
        {
            "gate_name": "degradation_rows_present",
            "value": summary["degradation_rows_present"],
            "threshold": "true",
            "passed": bool(summary["degradation_rows_present"]),
            "notes": "degradation rejection term must be represented",
        },
        {
            "gate_name": "ppo_blocked",
            "value": not bool(summary["ppo_used"]),
            "threshold": "true",
            "passed": not bool(summary["ppo_used"]),
            "notes": "M883 cannot train or promote",
        },
    ]


def run_objective_sanity(
    *,
    checkpoint_path: Path,
    residual_head_path: Path,
    scenario_config_path: Path,
    source_rows_path: Path,
    objective_train_rows_path: Path,
    objective_eval_rows_path: Path,
    source_holdout_rows_path: Path,
    new_signature_holdout_rows_path: Path,
    run_dir: Path,
    device: str,
    margin: float,
    alpha: float,
    max_base_faults: int,
    max_fault_specs: int,
    max_snapshots_per_group: int,
    max_steps: int | None,
    min_step: int | None,
    snapshot_stride: int | None,
    warmup_steps: int,
    steer_amplitude: float,
    brake_amplitude: float,
    warmup_period_steps: int,
) -> dict[str, Any]:
    start = time.time()
    run_dir.mkdir(parents=True, exist_ok=True)
    scenario_config = load_scenario_config(scenario_config_path)
    env_config = load_env_config(Path(scenario_config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    if not model.is_online_recurrent:
        raise ValueError("M883 enriched pair-delta objective sanity requires an online recurrent checkpoint")
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    checksum_before = model_parameter_checksum(model)
    residual_head = _load_residual_head(
        residual_head_path,
        expected_feature_dim=int(model.actor_mean.in_features),
        device=resolved_device,
    )
    residual_head.eval()
    for parameter in residual_head.parameters():
        parameter.requires_grad_(False)
    rows_by_split = {
        "objective_train_public": read_csv_rows(objective_train_rows_path),
        "objective_eval_public": read_csv_rows(objective_eval_rows_path),
        "source_holdout_public": read_csv_rows(source_holdout_rows_path),
        "new_signature_holdout_public": read_csv_rows(new_signature_holdout_rows_path),
    }
    rows: list[dict[str, Any]] = []
    for split, split_rows in rows_by_split.items():
        for row in split_rows:
            rows.append({**row, "split": str(row.get("split", "")) or split})

    fault_specs = build_fault_variants(
        list(scenario_config["faults"]),
        max_base_faults=int(max_base_faults),
        max_fault_specs=int(max_fault_specs),
        activation_deltas=(-3, 3),
        severity_deltas=(-0.04, 0.04),
    )
    fault_by_name = {fault.name: fault for fault in [NOMINAL_FAULT, *fault_specs]}
    max_steps_resolved = int(max_steps) if max_steps is not None else int(scenario_config.get("max_steps", 340))
    min_step_resolved = int(min_step) if min_step is not None else int(scenario_config.get("min_step", 20))
    snapshot_stride_resolved = int(snapshot_stride) if snapshot_stride is not None else int(scenario_config.get("snapshot_stride", 3))
    snapshots, snapshot_rows, snapshot_rejections = reconstruct_snapshots(
        pair_source_rows=pair_requests(rows),
        source_rows=read_csv_rows(source_rows_path),
        fault_by_name=fault_by_name,
        model=model,
        residual_head=residual_head,
        env_config=env_config,
        scenario_config=scenario_config,
        alpha=float(alpha),
        min_step=min_step_resolved,
        max_steps=max_steps_resolved,
        snapshot_stride=snapshot_stride_resolved,
        max_snapshots_per_group=int(max_snapshots_per_group),
        warmup_steps=int(warmup_steps),
        steer_amplitude=float(steer_amplitude),
        brake_amplitude=float(brake_amplitude),
        warmup_period_steps=int(warmup_period_steps),
        device=resolved_device,
    )

    metric_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    for row in rows:
        key = (_as_int(row.get("left_source_group_id")), _as_int(row.get("left_step")))
        snapshot = snapshots.get(key)
        if snapshot is None:
            rejected_rows.append({**row, "rejection_reason": "missing_left_snapshot"})
            continue
        normal_action = action_vector(row, "normal_first")
        override_action = action_vector(row, "first_override")
        if not np.all(np.isfinite(normal_action)) or not np.all(np.isfinite(override_action)):
            rejected_rows.append({**row, "rejection_reason": "nonfinite_action_target"})
            continue
        normal_logp = _log_prob_action(model, np.asarray(snapshot.observation, dtype=np.float32), snapshot.hidden, normal_action, resolved_device)
        override_logp = _log_prob_action(model, np.asarray(snapshot.observation, dtype=np.float32), snapshot.hidden, override_action, resolved_device)
        metric_rows.append(_objective_row(row=row, normal_logp=normal_logp, override_logp=override_logp, margin=float(margin)))

    checksum_after = model_parameter_checksum(model)
    summary_rows = _split_summary(metric_rows)
    exact_losses = [_finite_float(row.get("objective_loss")) for row in metric_rows]
    improvement_rows_present = any(str(row.get("accepted_class", "")) == "pair_delta_improvement" for row in metric_rows)
    degradation_rows_present = any(str(row.get("accepted_class", "")) == "pair_delta_degradation" for row in metric_rows)
    expected_rows = sum(len(split_rows) for split_rows in rows_by_split.values())
    missing_tensor_count = len(rejected_rows)
    result_class = classify_enriched_pair_delta_objective_sanity(
        tensor_rows_reconstructed=len(metric_rows),
        expected_rows=expected_rows,
        missing_tensor_count=missing_tensor_count,
        exact_losses_finite=_all_finite(exact_losses),
        improvement_rows_present=improvement_rows_present,
        degradation_rows_present=degradation_rows_present,
        per_split_metrics_written=bool(summary_rows),
        actor_parameters_changed=bool(checksum_before != checksum_after),
    )
    reconstruction_summary = [
        {
            "expected_rows": expected_rows,
            "tensor_rows_reconstructed": len(metric_rows),
            "missing_tensor_count": missing_tensor_count,
            "snapshot_rows": len(snapshot_rows),
            "snapshot_rejections": len(snapshot_rejections),
            "unique_pair_requests": len(pair_requests(rows)),
        }
    ]
    summary = {
        "run_type": "v4_enriched_pair_delta_objective_sanity",
        "checkpoint": checkpoint_path,
        "residual_head": residual_head_path,
        "scenario_config": scenario_config_path,
        "source_rows": source_rows_path,
        "expected_rows": expected_rows,
        "train_rows_expected": len(rows_by_split["objective_train_public"]),
        "eval_rows_expected": len(rows_by_split["objective_eval_public"]),
        "source_holdout_rows_expected": len(rows_by_split["source_holdout_public"]),
        "new_signature_holdout_rows_expected": len(rows_by_split["new_signature_holdout_public"]),
        "tensor_rows_reconstructed": len(metric_rows),
        "missing_tensor_count": missing_tensor_count,
        "snapshot_rows": len(snapshot_rows),
        "snapshot_rejections": len(snapshot_rejections),
        "objective_loss_mean": _mean(exact_losses),
        "exact_losses_finite": _all_finite(exact_losses),
        "improvement_rows_present": improvement_rows_present,
        "degradation_rows_present": degradation_rows_present,
        "per_split_metrics_written": bool(summary_rows),
        "training_started": False,
        "optimizer_started": False,
        "checkpoint_loaded_for_eval_only": True,
        "ppo_used": False,
        "promoted": False,
        "actor_parameters_changed": bool(checksum_before != checksum_after),
        "result_class": result_class,
        "elapsed_seconds": float(time.time() - start),
        "objective_rows_csv": run_dir / "objective_rows.csv",
        "objective_metrics_csv": run_dir / "objective_metrics.csv",
        "reconstruction_summary_csv": run_dir / "reconstruction_summary.csv",
        "reconstructed_snapshot_rows_csv": run_dir / "reconstructed_snapshot_rows.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
        "gate_summary_csv": run_dir / "gate_summary.csv",
    }
    write_csv_rows(run_dir / "objective_rows.csv", metric_rows)
    write_csv_rows(run_dir / "objective_metrics.csv", summary_rows)
    write_csv_rows(run_dir / "reconstruction_summary.csv", reconstruction_summary)
    write_csv_rows(run_dir / "reconstructed_snapshot_rows.csv", snapshot_rows)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
    write_csv_rows(run_dir / "gate_summary.csv", _gate_rows(summary), fieldnames=GATE_SUMMARY_FIELDS)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run exact no-update enriched pair-delta objective sanity.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--residual-head", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--source-rows", type=Path, required=True)
    parser.add_argument("--objective-train-rows", type=Path, required=True)
    parser.add_argument("--objective-eval-rows", type=Path, required=True)
    parser.add_argument("--source-holdout-rows", type=Path, required=True)
    parser.add_argument("--new-signature-holdout-rows", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--margin", type=float, default=0.05)
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--max-base-faults", type=int, default=10)
    parser.add_argument("--max-fault-specs", type=int, default=18)
    parser.add_argument("--max-snapshots-per-group", type=int, default=1)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--min-step", type=int, default=None)
    parser.add_argument("--snapshot-stride", type=int, default=None)
    parser.add_argument("--warmup-steps", type=int, default=24)
    parser.add_argument("--steer-amplitude", type=float, default=0.08)
    parser.add_argument("--brake-amplitude", type=float, default=0.08)
    parser.add_argument("--warmup-period-steps", type=int, default=8)
    args = parser.parse_args()
    summary = run_objective_sanity(
        checkpoint_path=args.checkpoint,
        residual_head_path=args.residual_head,
        scenario_config_path=args.scenario_config,
        source_rows_path=args.source_rows,
        objective_train_rows_path=args.objective_train_rows,
        objective_eval_rows_path=args.objective_eval_rows,
        source_holdout_rows_path=args.source_holdout_rows,
        new_signature_holdout_rows_path=args.new_signature_holdout_rows,
        run_dir=args.run_dir,
        device=args.device,
        margin=float(args.margin),
        alpha=float(args.alpha),
        max_base_faults=int(args.max_base_faults),
        max_fault_specs=int(args.max_fault_specs),
        max_snapshots_per_group=int(args.max_snapshots_per_group),
        max_steps=args.max_steps,
        min_step=args.min_step,
        snapshot_stride=args.snapshot_stride,
        warmup_steps=int(args.warmup_steps),
        steer_amplitude=float(args.steer_amplitude),
        brake_amplitude=float(args.brake_amplitude),
        warmup_period_steps=int(args.warmup_period_steps),
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
