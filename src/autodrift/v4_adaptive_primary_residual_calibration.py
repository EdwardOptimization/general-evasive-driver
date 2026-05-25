"""Source-heldout residual calibration probe for M814 adaptive primary rows."""

from __future__ import annotations

import argparse
import csv
import hashlib
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
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.temporal_action_boundary_outcome_miner import relocate_temporal_snapshot
from autodrift.train_ppo import resolve_device
from autodrift.v4_adaptive_boundary_bracketing import _snapshot_uid
from autodrift.v4_low_margin_boundary_window_retarget import parse_bool
from autodrift.v4_low_margin_guard_corpus_refresh import max_share, unique_count
from autodrift.v4_low_margin_new_data_route import (
    WARMUP_MODES,
    build_fault_variants,
    build_source_groups,
    collect_warmup_snapshots,
)
from autodrift.v4_normal_margin_residual_calibration import (
    ResidualGate,
    replay_calibrated_sequence_variant,
)
from autodrift.v4_residual_closed_loop_replay import (
    SUPPORTED_VARIANTS,
    _load_residual_head,
    replay_residual_sequence_variant,
)


SPLIT_FIELDS = [
    "candidate_id",
    "split",
    "split_unit",
    "source_group_id",
    "snapshot_uid",
    "source_index",
    "seed",
    "warmup_mode",
    "fault_family_pair",
    "boundary_axis",
    "min_clearance_margin",
]

EVAL_FIELDS = [
    "candidate_id",
    "split",
    "source_group_id",
    "snapshot_uid",
    "source_index",
    "seed",
    "warmup_mode",
    "fault_family_pair",
    "boundary_axis",
    "baseline_csv_margin",
    "baseline_replay_margin",
    "calibrated_margin",
    "baseline_replay_success",
    "calibrated_success",
    "baseline_replay_collision",
    "calibrated_collision",
    "baseline_terminal_reason",
    "calibrated_terminal_reason",
    "calibrated_first_gate",
    "calibrated_gate_mean",
    "calibrated_prefix_l2_mean_vs_baseline",
    "calibrated_prefix_l2_max_vs_baseline",
]

INTERVENTION_FIELDS = [
    "candidate_id",
    "split",
    "source_group_id",
    "snapshot_uid",
    "source_index",
    "seed",
    "warmup_mode",
    "fault_family_pair",
    "boundary_axis",
    "intervention_variant",
    "baseline_collision",
    "calibrated_collision",
    "baseline_margin",
    "calibrated_margin",
    "calibrated_success",
    "calibrated_prefix_l2_mean_vs_normal",
]

GATE_FIELDS = ["gate_name", "value", "threshold", "passed", "notes"]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _stable_hash(value: str) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def split_unit(row: dict[str, Any]) -> str:
    return "|".join(
        [
            str(row.get("source_group_id", "")),
            str(row.get("seed", "")),
            str(row.get("fault_family_pair", "")),
        ]
    )


def split_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": int(len(rows)),
        "unique_source_groups": unique_count(rows, "source_group_id"),
        "unique_seeds": unique_count(rows, "seed"),
        "unique_fault_family_pairs": unique_count(rows, "fault_family_pair"),
        "unique_boundary_axes": unique_count(rows, "boundary_axis"),
        "unique_warmup_modes": unique_count(rows, "warmup_mode"),
        "max_seed_dominance": max_share(rows, "seed"),
        "max_axis_dominance": max_share(rows, "boundary_axis"),
    }


def make_source_heldout_split(
    rows: list[dict[str, Any]],
    *,
    holdout_fraction: float,
    min_holdout_rows: int,
    min_holdout_axes: int,
    min_holdout_fault_pairs: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    units: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        units.setdefault(split_unit(row), []).append(row)
    ordered_units = sorted(units, key=lambda value: (_stable_hash(value), value))
    if not ordered_units:
        return [], {"split_valid": False, "split_invalid_reason": "no_units"}
    target_holdout = max(int(min_holdout_rows), int(round(len(rows) * float(holdout_fraction))))
    best_rows: list[dict[str, Any]] = []
    best_score: tuple[int, int, int, float] | None = None
    period = max(2, int(round(1.0 / max(float(holdout_fraction), 1e-6))))
    for offset in range(period):
        holdout_units = {unit for index, unit in enumerate(ordered_units) if index % period == offset}
        labeled: list[dict[str, Any]] = []
        for row in rows:
            split = "holdout" if split_unit(row) in holdout_units else "train"
            labeled.append({**row, "split": split, "split_unit": split_unit(row)})
        holdout_rows = [row for row in labeled if row["split"] == "holdout"]
        train_rows = [row for row in labeled if row["split"] == "train"]
        score = (
            min(len(holdout_rows), target_holdout),
            unique_count(holdout_rows, "boundary_axis"),
            unique_count(holdout_rows, "fault_family_pair"),
            -abs(len(holdout_rows) - target_holdout),
        )
        if train_rows and (best_score is None or score > best_score):
            best_rows = labeled
            best_score = score
    train_rows = [row for row in best_rows if row.get("split") == "train"]
    holdout_rows = [row for row in best_rows if row.get("split") == "holdout"]
    split_valid = bool(
        train_rows
        and len(holdout_rows) >= int(min_holdout_rows)
        and unique_count(holdout_rows, "boundary_axis") >= int(min_holdout_axes)
        and unique_count(holdout_rows, "fault_family_pair") >= int(min_holdout_fault_pairs)
        and not ({str(row.get("source_group_id", "")) for row in train_rows} & {str(row.get("source_group_id", "")) for row in holdout_rows})
    )
    reason = ""
    if not split_valid:
        reason = "holdout_diversity_or_disjointness_failed"
    summary = {
        "split_valid": split_valid,
        "split_invalid_reason": reason,
        "holdout_fraction": float(holdout_fraction),
        "split_units": int(len(units)),
        "train": split_summary(train_rows),
        "holdout": split_summary(holdout_rows),
    }
    return best_rows, summary


def _group_rows(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get(key, "")), []).append(row)
    return grouped


def _load_intervention_baseline(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    output: dict[tuple[str, str], dict[str, Any]] = {}
    for row in read_csv_rows(path):
        output[(str(row.get("candidate_id", "")), str(row.get("intervention_variant", "")))] = row
    return output


def _feature_for_snapshot(model: Any, snapshot: Any, *, device: torch.device) -> torch.Tensor:
    obs_t = torch.as_tensor(snapshot.observation, dtype=torch.float32, device=device).unsqueeze(0)
    hidden_t = snapshot.hidden.to(device=device, dtype=torch.float32)
    with torch.no_grad():
        features, _ = model.recurrent_features_tensor(obs_t, hidden_t)
    return features.detach()


def train_identity_calibrator(
    features: torch.Tensor,
    *,
    output_dim: int,
    initial_gate: float,
    target_gate: float,
    epochs: int,
    lr: float,
    seed: int,
) -> tuple[ResidualGate, list[dict[str, Any]]]:
    torch.manual_seed(int(seed))
    feature_dim = int(features.shape[1])
    calibrator = ResidualGate(feature_dim=feature_dim, output_dim=int(output_dim), initial_gate=float(initial_gate))
    optimizer = torch.optim.Adam(calibrator.parameters(), lr=float(lr))
    target = torch.full((features.shape[0], int(output_dim)), float(target_gate), dtype=torch.float32)
    history: list[dict[str, Any]] = []
    for epoch in range(int(epochs)):
        optimizer.zero_grad()
        gate = calibrator(features)
        loss = torch.mean((gate - target) ** 2)
        l2 = torch.zeros((), dtype=torch.float32)
        for parameter in calibrator.parameters():
            l2 = l2 + parameter.pow(2).mean()
        total = loss + 1e-6 * l2
        total.backward()
        optimizer.step()
        history.append(
            {
                "epoch": int(epoch + 1),
                "loss": float(total.detach().item()),
                "gate_mse": float(loss.detach().item()),
                "gate_mean": float(gate.detach().mean().item()),
                "gate_min": float(gate.detach().min().item()),
                "gate_max": float(gate.detach().max().item()),
            }
        )
    calibrator.eval()
    return calibrator, history


def _build_snapshot_lookup(
    *,
    model: Any,
    residual_head: Any,
    env_config: Any,
    scenario_config: dict[str, Any],
    source_group_ids: set[int],
    seed_start: int,
    seed_count: int,
    max_base_faults: int,
    max_fault_specs: int,
    max_source_groups: int,
    max_snapshots_per_group: int,
    max_steps: int,
    min_step: int,
    snapshot_stride: int,
    warmup_steps: int,
    steer_amplitude: float,
    brake_amplitude: float,
    warmup_period_steps: int,
    alpha: float,
    device: torch.device,
) -> dict[str, Any]:
    fault_specs = build_fault_variants(
        list(scenario_config["faults"]),
        max_base_faults=int(max_base_faults),
        max_fault_specs=int(max_fault_specs),
        activation_deltas=(-3, 3),
        severity_deltas=(-0.04, 0.04),
    )
    fault_by_name = {fault.name: fault for fault in [NOMINAL_FAULT, *fault_specs]}
    source_groups = build_source_groups(
        seed_start=int(seed_start),
        seed_count=int(seed_count),
        fault_specs=fault_specs,
        warmup_modes=WARMUP_MODES,
        max_source_groups=int(max_source_groups),
    )
    snapshots_by_uid: dict[str, Any] = {}
    snapshot_index = 0
    for group in source_groups:
        fault = fault_by_name[str(group["preferred_fault"])]
        snapshots, _, _ = collect_warmup_snapshots(
            model=model,
            residual_head=residual_head,
            env_config=env_config,
            fault=fault,
            source_group=group,
            alpha=float(alpha),
            min_step=int(min_step),
            max_steps=int(max_steps),
            snapshot_stride=int(snapshot_stride),
            max_snapshots_per_group=int(max_snapshots_per_group),
            obstacle_longitudinal_min=float(scenario_config.get("obstacle_longitudinal_min", -14.0)),
            obstacle_longitudinal_max=float(scenario_config.get("obstacle_longitudinal_max", 115.0)),
            history_window_steps=int(scenario_config.get("temporal_history_window_steps", 30)),
            warmup_steps=int(warmup_steps),
            steer_amplitude=float(steer_amplitude),
            brake_amplitude=float(brake_amplitude),
            period_steps=int(warmup_period_steps),
            start_snapshot_id=snapshot_index,
            device=device,
        )
        if int(group["source_group_id"]) in source_group_ids:
            for snapshot in snapshots:
                snapshots_by_uid[_snapshot_uid(int(group["source_group_id"]), snapshot)] = snapshot
        snapshot_index += len(snapshots)
    return snapshots_by_uid


def _relocate_for_row(snapshot: Any, row: dict[str, Any]) -> Any:
    return relocate_temporal_snapshot(
        snapshot,
        body_longitudinal=float(row["target_obstacle_body_x"]),
        body_lateral=float(row["target_obstacle_body_y"]),
        half_width=float(row["target_obstacle_half_width"]),
    )


def _evaluate_rows(
    *,
    rows: list[dict[str, Any]],
    snapshots_by_uid: dict[str, Any],
    model: Any,
    residual_head: Any,
    calibrator: ResidualGate,
    env_config: Any,
    response_dim: int,
    alpha: float,
    horizon: int,
    max_continuation_steps: int,
    device: torch.device,
) -> tuple[list[dict[str, Any]], dict[str, list[np.ndarray]], dict[str, Any]]:
    eval_rows: list[dict[str, Any]] = []
    baseline_actions_by_candidate: dict[str, list[np.ndarray]] = {}
    missing = 0
    for row in rows:
        candidate_id = str(row.get("candidate_id", ""))
        snapshot = snapshots_by_uid.get(str(row.get("snapshot_uid", "")))
        if snapshot is None:
            missing += 1
            continue
        relocated = _relocate_for_row(snapshot, row)
        baseline, baseline_actions = replay_residual_sequence_variant(
            model=model,
            residual_head=residual_head,
            snapshot=relocated,
            env_config=env_config,
            variant="normal",
            horizon=int(horizon),
            response_dim=response_dim,
            reference_actions=None,
            base_reference_actions=None,
            max_continuation_steps=int(max_continuation_steps),
            alpha=float(alpha),
            device=device,
        )
        calibrated, _ = replay_calibrated_sequence_variant(
            model=model,
            residual_head=residual_head,
            calibrator=calibrator,
            snapshot=relocated,
            env_config=env_config,
            variant="normal",
            horizon=int(horizon),
            response_dim=response_dim,
            reference_actions=baseline_actions,
            base_reference_actions=baseline_actions,
            max_continuation_steps=int(max_continuation_steps),
            alpha=float(alpha),
            device=device,
        )
        baseline_actions_by_candidate[candidate_id] = baseline_actions
        eval_rows.append(
            {
                "candidate_id": candidate_id,
                "split": row.get("split", ""),
                "source_group_id": row.get("source_group_id", ""),
                "snapshot_uid": row.get("snapshot_uid", ""),
                "source_index": row.get("source_index", ""),
                "seed": row.get("seed", ""),
                "warmup_mode": row.get("warmup_mode", ""),
                "fault_family_pair": row.get("fault_family_pair", ""),
                "boundary_axis": row.get("boundary_axis", ""),
                "baseline_csv_margin": _finite_float(row.get("min_clearance_margin")),
                "baseline_replay_margin": _finite_float(baseline.get("min_clearance_margin")),
                "calibrated_margin": _finite_float(calibrated.get("min_clearance_margin")),
                "baseline_replay_success": parse_bool(baseline.get("success", False)),
                "calibrated_success": parse_bool(calibrated.get("success", False)),
                "baseline_replay_collision": parse_bool(baseline.get("collision", False)),
                "calibrated_collision": parse_bool(calibrated.get("collision", False)),
                "baseline_terminal_reason": baseline.get("terminal_reason", ""),
                "calibrated_terminal_reason": calibrated.get("terminal_reason", ""),
                "calibrated_first_gate": _finite_float(calibrated.get("first_gate")),
                "calibrated_gate_mean": _finite_float(calibrated.get("gate_mean")),
                "calibrated_prefix_l2_mean_vs_baseline": _finite_float(calibrated.get("prefix_l2_mean")),
                "calibrated_prefix_l2_max_vs_baseline": _finite_float(calibrated.get("prefix_l2_max")),
            }
        )
    return eval_rows, baseline_actions_by_candidate, {"missing_snapshots": int(missing)}


def _evaluate_interventions(
    *,
    rows: list[dict[str, Any]],
    snapshots_by_uid: dict[str, Any],
    baseline_actions_by_candidate: dict[str, list[np.ndarray]],
    intervention_baseline: dict[tuple[str, str], dict[str, Any]],
    model: Any,
    residual_head: Any,
    calibrator: ResidualGate,
    env_config: Any,
    response_dim: int,
    alpha: float,
    horizon: int,
    max_continuation_steps: int,
    device: torch.device,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        candidate_id = str(row.get("candidate_id", ""))
        snapshot = snapshots_by_uid.get(str(row.get("snapshot_uid", "")))
        if snapshot is None:
            continue
        relocated = _relocate_for_row(snapshot, row)
        baseline_actions = baseline_actions_by_candidate.get(candidate_id)
        if baseline_actions is None:
            continue
        for variant in sorted(SUPPORTED_VARIANTS):
            calibrated, _ = replay_calibrated_sequence_variant(
                model=model,
                residual_head=residual_head,
                calibrator=calibrator,
                snapshot=relocated,
                env_config=env_config,
                variant=variant,
                horizon=int(horizon),
                response_dim=response_dim,
                reference_actions=baseline_actions,
                base_reference_actions=baseline_actions,
                max_continuation_steps=int(max_continuation_steps),
                alpha=float(alpha),
                device=device,
            )
            baseline = intervention_baseline.get((candidate_id, variant), {})
            output.append(
                {
                    "candidate_id": candidate_id,
                    "split": row.get("split", ""),
                    "source_group_id": row.get("source_group_id", ""),
                    "snapshot_uid": row.get("snapshot_uid", ""),
                    "source_index": row.get("source_index", ""),
                    "seed": row.get("seed", ""),
                    "warmup_mode": row.get("warmup_mode", ""),
                    "fault_family_pair": row.get("fault_family_pair", ""),
                    "boundary_axis": row.get("boundary_axis", ""),
                    "intervention_variant": variant,
                    "baseline_collision": parse_bool(baseline.get("intervention_collision", False)),
                    "calibrated_collision": parse_bool(calibrated.get("collision", False)),
                    "baseline_margin": _finite_float(baseline.get("intervention_margin")),
                    "calibrated_margin": _finite_float(calibrated.get("min_clearance_margin")),
                    "calibrated_success": parse_bool(calibrated.get("success", False)),
                    "calibrated_prefix_l2_mean_vs_normal": _finite_float(calibrated.get("prefix_l2_mean")),
                }
            )
    return output


def _rate(rows: list[dict[str, Any]], field: str) -> float:
    if not rows:
        return float("nan")
    return float(np.mean([1.0 if parse_bool(row.get(field, False)) else 0.0 for row in rows]))


def _normal_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    collisions = sum(1 for row in rows if parse_bool(row.get("calibrated_collision", False)))
    successes = sum(1 for row in rows if parse_bool(row.get("calibrated_success", False)))
    drifts = [_finite_float(row.get("calibrated_prefix_l2_mean_vs_baseline")) for row in rows]
    return {
        "rows": int(len(rows)),
        "success_count": int(successes),
        "collision_count": int(collisions),
        "success_rate": float(successes / max(len(rows), 1)),
        "collision_rate": float(collisions / max(len(rows), 1)),
        "mean_action_drift": float(np.nanmean(drifts)) if drifts else float("nan"),
        "max_action_drift": float(np.nanmax(drifts)) if drifts else float("nan"),
    }


def _intervention_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": int(len(rows)),
        "baseline_collision_rate": _rate(rows, "baseline_collision"),
        "calibrated_collision_rate": _rate(rows, "calibrated_collision"),
    }


def classify_v4_adaptive_primary_residual_calibration(
    *,
    split_valid: bool,
    actor_changed: bool,
    residual_changed: bool,
    optimizer_updates_only_calibrator: bool,
    train_normal_pass: bool,
    holdout_normal_pass: bool,
    train_intervention_pass: bool,
    holdout_intervention_pass: bool,
    old_behavior_pass: bool,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if bool(actor_changed) or bool(residual_changed) or not bool(optimizer_updates_only_calibrator) or bool(ppo_used) or bool(promoted):
        return "v4_adaptive_primary_residual_calibration_contract_violation"
    if not bool(split_valid):
        return "v4_adaptive_primary_residual_calibration_split_invalid"
    if bool(train_normal_pass) and not bool(holdout_normal_pass):
        return "v4_adaptive_primary_residual_calibration_objective_overfit"
    if not bool(holdout_normal_pass):
        return "v4_adaptive_primary_residual_calibration_holdout_regression"
    if not bool(train_intervention_pass) or not bool(holdout_intervention_pass):
        return "v4_adaptive_primary_residual_calibration_intervention_washout"
    if not bool(old_behavior_pass):
        return "v4_adaptive_primary_residual_calibration_old_gate_regression"
    return "v4_adaptive_primary_residual_calibration_candidate"


def run_calibration_probe(
    *,
    checkpoint_path: Path,
    residual_head_path: Path,
    accepted_rows_path: Path,
    intervention_rows_path: Path,
    scenario_config_path: Path,
    run_dir: Path,
    device: str,
    alpha: float,
    seed_start: int,
    seed_count: int,
    max_base_faults: int,
    max_fault_specs: int,
    max_source_groups: int,
    max_snapshots_per_group: int,
    max_steps: int,
    min_step: int,
    snapshot_stride: int,
    warmup_steps: int,
    steer_amplitude: float,
    brake_amplitude: float,
    warmup_period_steps: int,
    max_continuation_steps: int,
    horizon: int,
    holdout_fraction: float,
    min_holdout_rows: int,
    min_holdout_axes: int,
    min_holdout_fault_pairs: int,
    calibrator_mode: str,
    initial_gate: float,
    target_gate: float,
    epochs: int,
    lr: float,
    train_seed: int,
    max_intervention_collision_drop: float,
    max_mean_action_drift: float,
    max_max_action_drift: float,
) -> dict[str, Any]:
    start = time.time()
    run_dir.mkdir(parents=True, exist_ok=True)
    rows = read_csv_rows(accepted_rows_path)
    split_rows, split_info = make_source_heldout_split(
        rows,
        holdout_fraction=float(holdout_fraction),
        min_holdout_rows=int(min_holdout_rows),
        min_holdout_axes=int(min_holdout_axes),
        min_holdout_fault_pairs=int(min_holdout_fault_pairs),
    )
    write_csv_rows(run_dir / "split_rows.csv", split_rows, fieldnames=SPLIT_FIELDS)
    write_json(run_dir / "split_summary.json", split_info)

    scenario_config = load_scenario_config(scenario_config_path)
    env_config = load_env_config(Path(scenario_config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    if not model.is_online_recurrent:
        raise ValueError("M817 calibration requires an online recurrent checkpoint")
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    actor_checksum_before = model_parameter_checksum(model)
    residual_head = _load_residual_head(
        residual_head_path,
        expected_feature_dim=int(model.actor_mean.in_features),
        device=resolved_device,
    )
    residual_checksum_before = model_parameter_checksum(residual_head)
    response_dim = response_feature_dim_for_model(model)

    source_group_ids = {int(row["source_group_id"]) for row in split_rows if str(row.get("source_group_id", "")).strip()}
    snapshots_by_uid = _build_snapshot_lookup(
        model=model,
        residual_head=residual_head,
        env_config=env_config,
        scenario_config=scenario_config,
        source_group_ids=source_group_ids,
        seed_start=int(seed_start),
        seed_count=int(seed_count),
        max_base_faults=int(max_base_faults),
        max_fault_specs=int(max_fault_specs),
        max_source_groups=int(max_source_groups),
        max_snapshots_per_group=int(max_snapshots_per_group),
        max_steps=int(max_steps),
        min_step=int(min_step),
        snapshot_stride=int(snapshot_stride),
        warmup_steps=int(warmup_steps),
        steer_amplitude=float(steer_amplitude),
        brake_amplitude=float(brake_amplitude),
        warmup_period_steps=int(warmup_period_steps),
        alpha=float(alpha),
        device=resolved_device,
    )

    train_rows = [row for row in split_rows if row.get("split") == "train"]
    train_features: list[torch.Tensor] = []
    for row in train_rows:
        snapshot = snapshots_by_uid.get(str(row.get("snapshot_uid", "")))
        if snapshot is None:
            continue
        relocated = _relocate_for_row(snapshot, row)
        train_features.append(_feature_for_snapshot(model, relocated, device=resolved_device).detach().cpu())
    if train_features:
        feature_tensor = torch.cat(train_features, dim=0)
    else:
        feature_tensor = torch.empty((0, int(model.actor_mean.in_features)), dtype=torch.float32)
    output_dim = 3 if str(calibrator_mode) == "vector_gate" else 1
    if parse_bool(split_info.get("split_valid", False)) and feature_tensor.shape[0] > 0:
        calibrator, training_rows = train_identity_calibrator(
            feature_tensor,
            output_dim=output_dim,
            initial_gate=float(initial_gate),
            target_gate=float(target_gate),
            epochs=int(epochs),
            lr=float(lr),
            seed=int(train_seed),
        )
    else:
        calibrator = ResidualGate(
            feature_dim=int(model.actor_mean.in_features),
            output_dim=output_dim,
            initial_gate=float(initial_gate),
        )
        training_rows = []
    calibrator.to(resolved_device)
    calibrator.eval()

    torch.save(
        {
            "state_dict": calibrator.state_dict(),
            "feature_dim": int(model.actor_mean.in_features),
            "hidden_dim": int(calibrator.hidden_dim),
            "output_dim": int(calibrator.output_dim),
            "initial_gate": float(calibrator.initial_gate),
            "calibrator_mode": str(calibrator_mode),
            "target_gate": float(target_gate),
            "alpha": float(alpha),
        },
        run_dir / "calibrator.pt",
    )
    write_csv_rows(run_dir / "training_metrics.csv", training_rows)

    eval_rows, baseline_actions_by_candidate, eval_meta = _evaluate_rows(
        rows=split_rows,
        snapshots_by_uid=snapshots_by_uid,
        model=model,
        residual_head=residual_head,
        calibrator=calibrator,
        env_config=env_config,
        response_dim=response_dim,
        alpha=float(alpha),
        horizon=int(horizon),
        max_continuation_steps=int(max_continuation_steps),
        device=resolved_device,
    )
    train_eval_rows = [row for row in eval_rows if row.get("split") == "train"]
    holdout_eval_rows = [row for row in eval_rows if row.get("split") == "holdout"]
    write_csv_rows(run_dir / "train_eval_rows.csv", train_eval_rows, fieldnames=EVAL_FIELDS)
    write_csv_rows(run_dir / "holdout_eval_rows.csv", holdout_eval_rows, fieldnames=EVAL_FIELDS)

    intervention_baseline = _load_intervention_baseline(intervention_rows_path)
    intervention_rows = _evaluate_interventions(
        rows=split_rows,
        snapshots_by_uid=snapshots_by_uid,
        baseline_actions_by_candidate=baseline_actions_by_candidate,
        intervention_baseline=intervention_baseline,
        model=model,
        residual_head=residual_head,
        calibrator=calibrator,
        env_config=env_config,
        response_dim=response_dim,
        alpha=float(alpha),
        horizon=int(horizon),
        max_continuation_steps=int(max_continuation_steps),
        device=resolved_device,
    )
    write_csv_rows(run_dir / "intervention_eval_rows.csv", intervention_rows, fieldnames=INTERVENTION_FIELDS)

    train_normal = _normal_metrics(train_eval_rows)
    holdout_normal = _normal_metrics(holdout_eval_rows)
    train_intervention = _intervention_metrics([row for row in intervention_rows if row.get("split") == "train"])
    holdout_intervention = _intervention_metrics([row for row in intervention_rows if row.get("split") == "holdout"])
    train_normal_pass = bool(train_normal["rows"] > 0 and train_normal["collision_count"] == 0 and train_normal["success_count"] == train_normal["rows"])
    holdout_normal_pass = bool(
        holdout_normal["rows"] > 0
        and holdout_normal["collision_count"] == 0
        and holdout_normal["success_count"] == holdout_normal["rows"]
    )
    train_intervention_pass = bool(
        np.isfinite(train_intervention["baseline_collision_rate"])
        and np.isfinite(train_intervention["calibrated_collision_rate"])
        and train_intervention["calibrated_collision_rate"]
        >= train_intervention["baseline_collision_rate"] - float(max_intervention_collision_drop)
    )
    holdout_intervention_pass = bool(
        np.isfinite(holdout_intervention["baseline_collision_rate"])
        and np.isfinite(holdout_intervention["calibrated_collision_rate"])
        and holdout_intervention["calibrated_collision_rate"]
        >= holdout_intervention["baseline_collision_rate"] - float(max_intervention_collision_drop)
    )
    all_normal = _normal_metrics(eval_rows)
    old_behavior_pass = bool(
        np.isfinite(all_normal["mean_action_drift"])
        and np.isfinite(all_normal["max_action_drift"])
        and all_normal["mean_action_drift"] <= float(max_mean_action_drift)
        and all_normal["max_action_drift"] <= float(max_max_action_drift)
    )
    actor_checksum_after = model_parameter_checksum(model)
    residual_checksum_after = model_parameter_checksum(residual_head)
    calibrator_checksum = model_parameter_checksum(calibrator)
    result_class = classify_v4_adaptive_primary_residual_calibration(
        split_valid=parse_bool(split_info.get("split_valid", False)),
        actor_changed=bool(actor_checksum_before != actor_checksum_after),
        residual_changed=bool(residual_checksum_before != residual_checksum_after),
        optimizer_updates_only_calibrator=True,
        train_normal_pass=train_normal_pass,
        holdout_normal_pass=holdout_normal_pass,
        train_intervention_pass=train_intervention_pass,
        holdout_intervention_pass=holdout_intervention_pass,
        old_behavior_pass=old_behavior_pass,
        ppo_used=False,
        promoted=False,
    )

    gate_rows = [
        {
            "gate_name": "split_valid",
            "value": parse_bool(split_info.get("split_valid", False)),
            "threshold": "true",
            "passed": parse_bool(split_info.get("split_valid", False)),
            "notes": split_info.get("split_invalid_reason", ""),
        },
        {
            "gate_name": "holdout_normal_collision_count",
            "value": holdout_normal["collision_count"],
            "threshold": "0",
            "passed": holdout_normal_pass,
            "notes": "holdout normal rows must remain successful and non-collision",
        },
        {
            "gate_name": "holdout_intervention_collision_rate",
            "value": holdout_intervention["calibrated_collision_rate"],
            "threshold": f">= baseline - {max_intervention_collision_drop}",
            "passed": holdout_intervention_pass,
            "notes": f"baseline={holdout_intervention['baseline_collision_rate']}",
        },
        {
            "gate_name": "old_behavior_action_drift",
            "value": all_normal["mean_action_drift"],
            "threshold": f"mean<={max_mean_action_drift}, max<={max_max_action_drift}",
            "passed": old_behavior_pass,
            "notes": f"max={all_normal['max_action_drift']}",
        },
    ]
    write_csv_rows(run_dir / "gate_summary.csv", gate_rows, fieldnames=GATE_FIELDS)

    summary = {
        "run_type": "v4_adaptive_primary_residual_calibration",
        "checkpoint": checkpoint_path,
        "residual_head": residual_head_path,
        "accepted_rows": accepted_rows_path,
        "intervention_rows": intervention_rows_path,
        "scenario_config": scenario_config_path,
        "alpha": float(alpha),
        "calibrator_mode": str(calibrator_mode),
        "initial_gate": float(initial_gate),
        "target_gate": float(target_gate),
        "epochs": int(epochs),
        "lr": float(lr),
        "split_valid": parse_bool(split_info.get("split_valid", False)),
        "split_summary": split_info,
        "snapshot_lookup_rows": int(len(snapshots_by_uid)),
        "missing_snapshots": int(eval_meta.get("missing_snapshots", 0)),
        "train_rows": int(len(train_eval_rows)),
        "holdout_rows": int(len(holdout_eval_rows)),
        "train_normal": train_normal,
        "holdout_normal": holdout_normal,
        "train_intervention": train_intervention,
        "holdout_intervention": holdout_intervention,
        "train_normal_pass": train_normal_pass,
        "holdout_normal_pass": holdout_normal_pass,
        "train_intervention_pass": train_intervention_pass,
        "holdout_intervention_pass": holdout_intervention_pass,
        "old_behavior_pass": old_behavior_pass,
        "max_intervention_collision_drop": float(max_intervention_collision_drop),
        "max_mean_action_drift": float(max_mean_action_drift),
        "max_max_action_drift": float(max_max_action_drift),
        "actor_backbone_changed": bool(actor_checksum_before != actor_checksum_after),
        "residual_head_changed": bool(residual_checksum_before != residual_checksum_after),
        "base_actor_checksum_before": actor_checksum_before,
        "base_actor_checksum_after": actor_checksum_after,
        "residual_head_checksum_before": residual_checksum_before,
        "residual_head_checksum_after": residual_checksum_after,
        "calibrator_checksum": calibrator_checksum,
        "calibrator_parameter_count": int(sum(parameter.numel() for parameter in calibrator.parameters())),
        "optimizer_updates_only_calibrator": True,
        "training_started": bool(training_rows),
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "result_class": result_class,
        "elapsed_seconds": float(time.time() - start),
        "summary_json": run_dir / "summary.json",
        "split_rows_csv": run_dir / "split_rows.csv",
        "split_summary_json": run_dir / "split_summary.json",
        "training_metrics_csv": run_dir / "training_metrics.csv",
        "train_eval_rows_csv": run_dir / "train_eval_rows.csv",
        "holdout_eval_rows_csv": run_dir / "holdout_eval_rows.csv",
        "intervention_eval_rows_csv": run_dir / "intervention_eval_rows.csv",
        "gate_summary_csv": run_dir / "gate_summary.csv",
        "calibrator_pt": run_dir / "calibrator.pt",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run source-heldout v4 adaptive primary residual calibration probe.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--residual-head", type=Path, required=True)
    parser.add_argument("--accepted-rows", type=Path, required=True)
    parser.add_argument("--intervention-rows", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--seed-start", type=int, default=None)
    parser.add_argument("--seed-count", type=int, default=12)
    parser.add_argument("--max-base-faults", type=int, default=8)
    parser.add_argument("--max-fault-specs", type=int, default=14)
    parser.add_argument("--max-source-groups", type=int, default=96)
    parser.add_argument("--max-snapshots-per-group", type=int, default=2)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--min-step", type=int, default=None)
    parser.add_argument("--snapshot-stride", type=int, default=None)
    parser.add_argument("--warmup-steps", type=int, default=20)
    parser.add_argument("--steer-amplitude", type=float, default=0.08)
    parser.add_argument("--brake-amplitude", type=float, default=0.08)
    parser.add_argument("--warmup-period-steps", type=int, default=8)
    parser.add_argument("--max-continuation-steps", type=int, default=None)
    parser.add_argument("--horizon", type=int, default=6)
    parser.add_argument("--holdout-fraction", type=float, default=0.30)
    parser.add_argument("--min-holdout-rows", type=int, default=20)
    parser.add_argument("--min-holdout-axes", type=int, default=2)
    parser.add_argument("--min-holdout-fault-pairs", type=int, default=3)
    parser.add_argument("--calibrator-mode", choices=["scalar_gate", "vector_gate"], default="scalar_gate")
    parser.add_argument("--initial-gate", type=float, default=0.999)
    parser.add_argument("--target-gate", type=float, default=0.999)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--train-seed", type=int, default=817)
    parser.add_argument("--max-intervention-collision-drop", type=float, default=0.10)
    parser.add_argument("--max-mean-action-drift", type=float, default=0.002)
    parser.add_argument("--max-max-action-drift", type=float, default=0.02)
    args = parser.parse_args()

    scenario_config = load_scenario_config(args.scenario_config)
    seed_start = int(args.seed_start) if args.seed_start is not None else int(scenario_config.get("low_margin_refresh_targets", {}).get("seed_start", 78048))
    max_steps = int(args.max_steps) if args.max_steps is not None else int(scenario_config.get("max_steps", 340))
    min_step = int(args.min_step) if args.min_step is not None else int(scenario_config.get("min_step", 20))
    snapshot_stride = int(args.snapshot_stride) if args.snapshot_stride is not None else int(scenario_config.get("snapshot_stride", 3))
    max_continuation_steps = (
        int(args.max_continuation_steps)
        if args.max_continuation_steps is not None
        else int(scenario_config.get("max_continuation_steps", 70))
    )
    summary = run_calibration_probe(
        checkpoint_path=args.checkpoint,
        residual_head_path=args.residual_head,
        accepted_rows_path=args.accepted_rows,
        intervention_rows_path=args.intervention_rows,
        scenario_config_path=args.scenario_config,
        run_dir=args.run_dir,
        device=args.device,
        alpha=float(args.alpha),
        seed_start=seed_start,
        seed_count=int(args.seed_count),
        max_base_faults=int(args.max_base_faults),
        max_fault_specs=int(args.max_fault_specs),
        max_source_groups=int(args.max_source_groups),
        max_snapshots_per_group=int(args.max_snapshots_per_group),
        max_steps=max_steps,
        min_step=min_step,
        snapshot_stride=snapshot_stride,
        warmup_steps=int(args.warmup_steps),
        steer_amplitude=float(args.steer_amplitude),
        brake_amplitude=float(args.brake_amplitude),
        warmup_period_steps=int(args.warmup_period_steps),
        max_continuation_steps=max_continuation_steps,
        horizon=int(args.horizon),
        holdout_fraction=float(args.holdout_fraction),
        min_holdout_rows=int(args.min_holdout_rows),
        min_holdout_axes=int(args.min_holdout_axes),
        min_holdout_fault_pairs=int(args.min_holdout_fault_pairs),
        calibrator_mode=str(args.calibrator_mode),
        initial_gate=float(args.initial_gate),
        target_gate=float(args.target_gate),
        epochs=int(args.epochs),
        lr=float(args.lr),
        train_seed=int(args.train_seed),
        max_intervention_collision_drop=float(args.max_intervention_collision_drop),
        max_mean_action_drift=float(args.max_mean_action_drift),
        max_max_action_drift=float(args.max_max_action_drift),
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
