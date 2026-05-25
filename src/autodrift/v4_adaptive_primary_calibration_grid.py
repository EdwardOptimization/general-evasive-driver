"""Exact fixed-gate calibration grid for M814 adaptive primary rows."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import time
from typing import Any

import numpy as np
import torch
from torch import nn

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import load_scenario_config
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import resolve_device
from autodrift.v4_adaptive_primary_residual_calibration import (
    _build_snapshot_lookup,
    _load_intervention_baseline,
    _relocate_for_row,
    read_csv_rows,
)
from autodrift.v4_low_margin_boundary_window_retarget import parse_bool
from autodrift.v4_normal_margin_residual_calibration import replay_calibrated_sequence_variant
from autodrift.v4_residual_closed_loop_replay import (
    SUPPORTED_VARIANTS,
    _load_residual_head,
    replay_residual_sequence_variant,
)


SCALAR_GATES = (0.0, 0.25, 0.50, 0.75, 0.90, 0.95, 0.98, 0.999, 1.0)
VECTOR_STEER_GATES = (0.0, 0.25, 0.50, 0.75, 1.0)
VECTOR_THROTTLE_GATES = (0.0, 0.50, 1.0)
VECTOR_BRAKE_GATES = (0.50, 0.75, 1.0)
HAND_PICKED_GATES: tuple[tuple[str, tuple[float, float, float]], ...] = (
    ("brake_only", (0.0, 0.0, 1.0)),
    ("steer_only", (1.0, 0.0, 0.0)),
    ("steer_suppressed_brake_retained", (0.0, 1.0, 1.0)),
    ("steer_retained_brake_retained", (1.0, 0.0, 1.0)),
    ("throttle_zeroed", (1.0, 0.0, 1.0)),
)
ACTION_COMPONENTS = ("steer", "throttle", "brake")

CANDIDATE_GRID_FIELDS = [
    "gate_candidate_id",
    "family",
    "label",
    "steer_gate",
    "throttle_gate",
    "brake_gate",
    "is_identity",
    "duplicate_of",
    "selected_on_train",
    "train_rank",
]

NORMAL_ROW_FIELDS = [
    "gate_candidate_id",
    "family",
    "row_candidate_id",
    "split",
    "source_group_id",
    "snapshot_uid",
    "source_index",
    "seed",
    "warmup_mode",
    "fault_family_pair",
    "boundary_axis",
    "identity_margin",
    "calibrated_margin",
    "margin_lift_vs_identity",
    "identity_success",
    "calibrated_success",
    "identity_collision",
    "calibrated_collision",
    "identity_terminal_reason",
    "calibrated_terminal_reason",
    "gate_mean",
    "gate_mean_steer",
    "gate_mean_throttle",
    "gate_mean_brake",
    "prefix_l2_mean_vs_identity",
    "prefix_l2_max_vs_identity",
]

INTERVENTION_ROW_FIELDS = [
    "gate_candidate_id",
    "family",
    "row_candidate_id",
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
    "prefix_l2_mean_vs_identity_normal",
]

METRIC_FIELDS = [
    "gate_candidate_id",
    "family",
    "label",
    "split",
    "steer_gate",
    "throttle_gate",
    "brake_gate",
    "normal_rows",
    "normal_success_count",
    "normal_collision_count",
    "normal_success_rate",
    "normal_collision_rate",
    "normal_margin_min",
    "normal_margin_mean",
    "normal_margin_p05",
    "normal_margin_lift_min",
    "normal_margin_lift_mean",
    "normal_margin_lift_p05",
    "action_drift_mean",
    "action_drift_max",
    "intervention_rows",
    "baseline_intervention_collision_rate",
    "calibrated_intervention_collision_rate",
    "intervention_collision_rate_drop",
    "normal_retention_pass",
    "intervention_retention_pass",
    "old_behavior_pass",
    "selection_pass",
    "holdout_acceptance_pass",
    "strong_candidate_pass",
    "train_rank",
]

GATE_SUMMARY_FIELDS = ["gate_name", "value", "threshold", "passed", "notes"]


class FixedResidualGate(nn.Module):
    """Feature-independent residual gate used for exact no-training grid probes."""

    def __init__(self, gate_values: tuple[float, float, float]) -> None:
        super().__init__()
        values = torch.as_tensor(gate_values, dtype=torch.float32).view(1, 3)
        self.register_buffer("gate_values", values)

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.gate_values.to(features.device).expand(features.shape[0], -1)


def _gate_id(prefix: str, values: tuple[float, float, float]) -> str:
    return (
        f"{prefix}_"
        f"s{values[0]:.3f}_"
        f"t{values[1]:.3f}_"
        f"b{values[2]:.3f}"
    ).replace(".", "p")


def build_gate_candidates(*, include_vector_grid: bool = True) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: dict[tuple[float, float, float], str] = {}

    def add_candidate(
        *,
        family: str,
        label: str,
        values: tuple[float, float, float],
        candidate_id: str | None = None,
    ) -> None:
        rounded = tuple(float(round(value, 6)) for value in values)
        duplicate_of = seen.get(rounded, "")
        if duplicate_of:
            return
        gate_candidate_id = candidate_id or _gate_id(family, rounded)
        seen[rounded] = gate_candidate_id
        candidates.append(
            {
                "gate_candidate_id": gate_candidate_id,
                "family": family,
                "label": label,
                "steer_gate": float(rounded[0]),
                "throttle_gate": float(rounded[1]),
                "brake_gate": float(rounded[2]),
                "is_identity": bool(rounded == (1.0, 1.0, 1.0)),
                "duplicate_of": duplicate_of,
                "selected_on_train": False,
                "train_rank": "",
            }
        )

    add_candidate(family="identity", label="identity", values=(1.0, 1.0, 1.0), candidate_id="identity")
    for gate in SCALAR_GATES:
        add_candidate(
            family="fixed_scalar",
            label=f"scalar_{gate:.3f}",
            values=(float(gate), float(gate), float(gate)),
        )
    if include_vector_grid:
        for steer_gate in VECTOR_STEER_GATES:
            for throttle_gate in VECTOR_THROTTLE_GATES:
                for brake_gate in VECTOR_BRAKE_GATES:
                    add_candidate(
                        family="fixed_vector",
                        label="vector_grid",
                        values=(float(steer_gate), float(throttle_gate), float(brake_gate)),
                    )
    for label, values in HAND_PICKED_GATES:
        add_candidate(family="fixed_template", label=label, values=values, candidate_id=f"template_{label}")
    return candidates


def merge_accepted_rows_with_split(
    accepted_rows: list[dict[str, Any]],
    split_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    accepted_by_id = {str(row.get("candidate_id", "")): row for row in accepted_rows}
    merged: list[dict[str, Any]] = []
    missing_ids: list[str] = []
    for split_row in split_rows:
        candidate_id = str(split_row.get("candidate_id", ""))
        accepted = accepted_by_id.get(candidate_id)
        if accepted is None:
            missing_ids.append(candidate_id)
            continue
        merged.append({**accepted, "split": split_row.get("split", ""), "split_unit": split_row.get("split_unit", "")})
    train_rows = [row for row in merged if row.get("split") == "train"]
    holdout_rows = [row for row in merged if row.get("split") == "holdout"]
    train_groups = {str(row.get("source_group_id", "")) for row in train_rows}
    holdout_groups = {str(row.get("source_group_id", "")) for row in holdout_rows}
    return merged, {
        "merged_rows": int(len(merged)),
        "missing_split_candidate_ids": missing_ids,
        "missing_split_candidate_count": int(len(missing_ids)),
        "train_rows": int(len(train_rows)),
        "holdout_rows": int(len(holdout_rows)),
        "source_group_disjoint": bool(not (train_groups & holdout_groups)),
    }


def _finite_values(values: list[float]) -> list[float]:
    return [float(value) for value in values if np.isfinite(float(value))]


def _mean(values: list[float]) -> float:
    finite = _finite_values(values)
    return float(np.mean(finite)) if finite else float("nan")


def _percentile(values: list[float], percentile: float) -> float:
    finite = _finite_values(values)
    return float(np.percentile(finite, percentile)) if finite else float("nan")


def _candidate_gate_tuple(candidate: dict[str, Any]) -> tuple[float, float, float]:
    return (
        float(candidate["steer_gate"]),
        float(candidate["throttle_gate"]),
        float(candidate["brake_gate"]),
    )


def _candidate_calibrator(candidate: dict[str, Any], *, device: torch.device) -> FixedResidualGate:
    gate = FixedResidualGate(_candidate_gate_tuple(candidate))
    gate.to(device)
    gate.eval()
    return gate


def _candidate_base(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "gate_candidate_id": candidate["gate_candidate_id"],
        "family": candidate["family"],
        "label": candidate["label"],
        "steer_gate": candidate["steer_gate"],
        "throttle_gate": candidate["throttle_gate"],
        "brake_gate": candidate["brake_gate"],
    }


def _normal_metrics(rows: list[dict[str, Any]], candidate: dict[str, Any], *, split: str) -> dict[str, Any]:
    selected_rows = [row for row in rows if row.get("split") == split and row.get("gate_candidate_id") == candidate["gate_candidate_id"]]
    margins = [_finite_float(row.get("calibrated_margin")) for row in selected_rows]
    lifts = [_finite_float(row.get("margin_lift_vs_identity")) for row in selected_rows]
    mean_drifts = [_finite_float(row.get("prefix_l2_mean_vs_identity")) for row in selected_rows]
    max_drifts = [_finite_float(row.get("prefix_l2_max_vs_identity")) for row in selected_rows]
    success_count = sum(1 for row in selected_rows if parse_bool(row.get("calibrated_success", False)))
    collision_count = sum(1 for row in selected_rows if parse_bool(row.get("calibrated_collision", False)))
    return {
        **_candidate_base(candidate),
        "split": split,
        "normal_rows": int(len(selected_rows)),
        "normal_success_count": int(success_count),
        "normal_collision_count": int(collision_count),
        "normal_success_rate": float(success_count / max(len(selected_rows), 1)),
        "normal_collision_rate": float(collision_count / max(len(selected_rows), 1)),
        "normal_margin_min": min(_finite_values(margins), default=float("nan")),
        "normal_margin_mean": _mean(margins),
        "normal_margin_p05": _percentile(margins, 5),
        "normal_margin_lift_min": min(_finite_values(lifts), default=float("nan")),
        "normal_margin_lift_mean": _mean(lifts),
        "normal_margin_lift_p05": _percentile(lifts, 5),
        "action_drift_mean": _mean(mean_drifts),
        "action_drift_max": max(_finite_values(max_drifts), default=float("nan")),
    }


def _intervention_metrics(rows: list[dict[str, Any]], candidate: dict[str, Any], *, split: str) -> dict[str, Any]:
    selected_rows = [row for row in rows if row.get("split") == split and row.get("gate_candidate_id") == candidate["gate_candidate_id"]]
    baseline_collisions = [1.0 if parse_bool(row.get("baseline_collision", False)) else 0.0 for row in selected_rows]
    calibrated_collisions = [1.0 if parse_bool(row.get("calibrated_collision", False)) else 0.0 for row in selected_rows]
    baseline_rate = float(np.mean(baseline_collisions)) if baseline_collisions else float("nan")
    calibrated_rate = float(np.mean(calibrated_collisions)) if calibrated_collisions else float("nan")
    return {
        "intervention_rows": int(len(selected_rows)),
        "baseline_intervention_collision_rate": baseline_rate,
        "calibrated_intervention_collision_rate": calibrated_rate,
        "intervention_collision_rate_drop": float(baseline_rate - calibrated_rate)
        if np.isfinite(baseline_rate) and np.isfinite(calibrated_rate)
        else float("nan"),
    }


def _combine_metrics(
    *,
    normal: dict[str, Any],
    intervention: dict[str, Any],
    max_intervention_collision_drop: float,
    max_mean_action_drift: float,
    max_max_action_drift: float,
    split: str,
) -> dict[str, Any]:
    normal_pass = bool(
        int(normal["normal_rows"]) > 0
        and int(normal["normal_success_count"]) == int(normal["normal_rows"])
        and int(normal["normal_collision_count"]) == 0
    )
    intervention_pass = bool(
        np.isfinite(float(intervention["baseline_intervention_collision_rate"]))
        and np.isfinite(float(intervention["calibrated_intervention_collision_rate"]))
        and float(intervention["calibrated_intervention_collision_rate"])
        >= float(intervention["baseline_intervention_collision_rate"]) - float(max_intervention_collision_drop)
    )
    old_behavior_pass = bool(
        np.isfinite(float(normal["action_drift_mean"]))
        and np.isfinite(float(normal["action_drift_max"]))
        and float(normal["action_drift_mean"]) <= float(max_mean_action_drift)
        and float(normal["action_drift_max"]) <= float(max_max_action_drift)
    )
    holdout_acceptance_pass = bool(
        split == "holdout"
        and normal_pass
        and float(normal["normal_margin_lift_p05"]) >= -1e-12
        and float(normal["normal_margin_lift_mean"]) >= -1e-12
        and intervention_pass
        and old_behavior_pass
    )
    strong_candidate_pass = bool(
        holdout_acceptance_pass
        and (
            float(normal["normal_margin_lift_p05"]) >= 0.00001
            or float(normal["normal_margin_lift_mean"]) >= 0.00002
        )
    )
    return {
        **normal,
        **intervention,
        "normal_retention_pass": normal_pass,
        "intervention_retention_pass": intervention_pass,
        "old_behavior_pass": old_behavior_pass,
        "selection_pass": bool(split == "train" and normal_pass and intervention_pass and old_behavior_pass),
        "holdout_acceptance_pass": holdout_acceptance_pass,
        "strong_candidate_pass": strong_candidate_pass,
        "train_rank": "",
    }


def select_train_candidate(metrics: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    train_metrics = [row for row in metrics if row.get("split") == "train" and parse_bool(row.get("selection_pass", False))]
    if not train_metrics:
        return None, metrics
    ranked = sorted(
        train_metrics,
        key=lambda row: (
            _finite_float(row.get("normal_margin_lift_p05"), default=-1e9),
            _finite_float(row.get("normal_margin_lift_mean"), default=-1e9),
            _finite_float(row.get("calibrated_intervention_collision_rate"), default=-1e9),
            -_finite_float(row.get("action_drift_mean"), default=1e9),
            0 if row.get("family") == "identity" else -1,
        ),
        reverse=True,
    )
    rank_by_id = {str(row["gate_candidate_id"]): index + 1 for index, row in enumerate(ranked)}
    selected = ranked[0]
    updated: list[dict[str, Any]] = []
    for row in metrics:
        candidate_id = str(row.get("gate_candidate_id", ""))
        row = dict(row)
        if candidate_id in rank_by_id:
            row["train_rank"] = int(rank_by_id[candidate_id])
        updated.append(row)
    return selected, updated


def classify_v4_adaptive_primary_calibration_grid(
    *,
    actor_changed: bool,
    residual_changed: bool,
    trained_adaptive_calibrator: bool,
    ppo_used: bool,
    promoted: bool,
    selected_family: str,
    train_selection_pass: bool,
    holdout_normal_pass: bool,
    holdout_intervention_pass: bool,
    holdout_old_behavior_pass: bool,
    holdout_acceptance_pass: bool,
    selected_strong_candidate: bool,
) -> str:
    if bool(actor_changed) or bool(residual_changed) or bool(trained_adaptive_calibrator) or bool(ppo_used) or bool(promoted):
        return "v4_adaptive_primary_calibration_contract_violation"
    if not bool(train_selection_pass):
        return "v4_adaptive_primary_calibration_identity_only"
    if not bool(holdout_old_behavior_pass):
        return "v4_adaptive_primary_calibration_old_behavior_regression"
    if not bool(holdout_intervention_pass):
        return "v4_adaptive_primary_calibration_intervention_washout"
    if not bool(holdout_normal_pass) or not bool(holdout_acceptance_pass):
        return "v4_adaptive_primary_calibration_train_only_overfit"
    if str(selected_family) == "identity" or not bool(selected_strong_candidate):
        return "v4_adaptive_primary_calibration_identity_only"
    if str(selected_family) == "fixed_scalar":
        return "v4_adaptive_primary_calibration_fixed_scalar_candidate"
    if str(selected_family) in {"fixed_vector", "fixed_template"}:
        return "v4_adaptive_primary_calibration_fixed_vector_candidate"
    return "v4_adaptive_primary_calibration_identity_only"


def _evaluate_identity_normal(
    *,
    rows: list[dict[str, Any]],
    snapshots_by_uid: dict[str, Any],
    model: Any,
    residual_head: Any,
    env_config: Any,
    response_dim: int,
    alpha: float,
    horizon: int,
    max_continuation_steps: int,
    device: torch.device,
) -> tuple[dict[str, dict[str, Any]], dict[str, list[np.ndarray]]]:
    identity_by_id: dict[str, dict[str, Any]] = {}
    actions_by_id: dict[str, list[np.ndarray]] = {}
    for row in rows:
        candidate_id = str(row.get("candidate_id", ""))
        snapshot = snapshots_by_uid.get(str(row.get("snapshot_uid", "")))
        if snapshot is None:
            continue
        relocated = _relocate_for_row(snapshot, row)
        result, actions = replay_residual_sequence_variant(
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
        identity_by_id[candidate_id] = result
        actions_by_id[candidate_id] = actions
    return identity_by_id, actions_by_id


def _evaluate_candidate(
    *,
    candidate: dict[str, Any],
    rows: list[dict[str, Any]],
    snapshots_by_uid: dict[str, Any],
    identity_by_id: dict[str, dict[str, Any]],
    identity_actions_by_id: dict[str, list[np.ndarray]],
    intervention_baseline: dict[tuple[str, str], dict[str, Any]],
    model: Any,
    residual_head: Any,
    env_config: Any,
    response_dim: int,
    alpha: float,
    horizon: int,
    max_continuation_steps: int,
    device: torch.device,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    normal_rows: list[dict[str, Any]] = []
    intervention_rows: list[dict[str, Any]] = []
    calibrator = _candidate_calibrator(candidate, device=device)
    for row in rows:
        row_candidate_id = str(row.get("candidate_id", ""))
        snapshot = snapshots_by_uid.get(str(row.get("snapshot_uid", "")))
        identity = identity_by_id.get(row_candidate_id)
        identity_actions = identity_actions_by_id.get(row_candidate_id)
        if snapshot is None or identity is None or identity_actions is None:
            continue
        relocated = _relocate_for_row(snapshot, row)
        calibrated, _ = replay_calibrated_sequence_variant(
            model=model,
            residual_head=residual_head,
            calibrator=calibrator,
            snapshot=relocated,
            env_config=env_config,
            variant="normal",
            horizon=int(horizon),
            response_dim=response_dim,
            reference_actions=identity_actions,
            base_reference_actions=identity_actions,
            max_continuation_steps=int(max_continuation_steps),
            alpha=float(alpha),
            device=device,
        )
        identity_margin = _finite_float(identity.get("min_clearance_margin"))
        calibrated_margin = _finite_float(calibrated.get("min_clearance_margin"))
        normal_rows.append(
            {
                "gate_candidate_id": candidate["gate_candidate_id"],
                "family": candidate["family"],
                "row_candidate_id": row_candidate_id,
                "split": row.get("split", ""),
                "source_group_id": row.get("source_group_id", ""),
                "snapshot_uid": row.get("snapshot_uid", ""),
                "source_index": row.get("source_index", ""),
                "seed": row.get("seed", ""),
                "warmup_mode": row.get("warmup_mode", ""),
                "fault_family_pair": row.get("fault_family_pair", ""),
                "boundary_axis": row.get("boundary_axis", ""),
                "identity_margin": identity_margin,
                "calibrated_margin": calibrated_margin,
                "margin_lift_vs_identity": float(calibrated_margin - identity_margin)
                if np.isfinite(identity_margin) and np.isfinite(calibrated_margin)
                else float("nan"),
                "identity_success": parse_bool(identity.get("success", False)),
                "calibrated_success": parse_bool(calibrated.get("success", False)),
                "identity_collision": parse_bool(identity.get("collision", False)),
                "calibrated_collision": parse_bool(calibrated.get("collision", False)),
                "identity_terminal_reason": identity.get("terminal_reason", ""),
                "calibrated_terminal_reason": calibrated.get("terminal_reason", ""),
                "gate_mean": _finite_float(calibrated.get("gate_mean")),
                "gate_mean_steer": _finite_float(calibrated.get("gate_mean_steer")),
                "gate_mean_throttle": _finite_float(calibrated.get("gate_mean_throttle")),
                "gate_mean_brake": _finite_float(calibrated.get("gate_mean_brake")),
                "prefix_l2_mean_vs_identity": _finite_float(calibrated.get("prefix_l2_mean")),
                "prefix_l2_max_vs_identity": _finite_float(calibrated.get("prefix_l2_max")),
            }
        )
        for variant in sorted(SUPPORTED_VARIANTS):
            intervention_result, _ = replay_calibrated_sequence_variant(
                model=model,
                residual_head=residual_head,
                calibrator=calibrator,
                snapshot=relocated,
                env_config=env_config,
                variant=variant,
                horizon=int(horizon),
                response_dim=response_dim,
                reference_actions=identity_actions,
                base_reference_actions=identity_actions,
                max_continuation_steps=int(max_continuation_steps),
                alpha=float(alpha),
                device=device,
            )
            baseline = intervention_baseline.get((row_candidate_id, variant), {})
            intervention_rows.append(
                {
                    "gate_candidate_id": candidate["gate_candidate_id"],
                    "family": candidate["family"],
                    "row_candidate_id": row_candidate_id,
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
                    "calibrated_collision": parse_bool(intervention_result.get("collision", False)),
                    "baseline_margin": _finite_float(baseline.get("intervention_margin")),
                    "calibrated_margin": _finite_float(intervention_result.get("min_clearance_margin")),
                    "calibrated_success": parse_bool(intervention_result.get("success", False)),
                    "prefix_l2_mean_vs_identity_normal": _finite_float(intervention_result.get("prefix_l2_mean")),
                }
            )
    return normal_rows, intervention_rows


def run_calibration_grid(
    *,
    checkpoint_path: Path,
    residual_head_path: Path,
    accepted_rows_path: Path,
    split_rows_path: Path,
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
    max_intervention_collision_drop: float,
    max_mean_action_drift: float,
    max_max_action_drift: float,
    max_candidates: int | None = None,
) -> dict[str, Any]:
    start = time.time()
    run_dir.mkdir(parents=True, exist_ok=True)

    accepted_rows = read_csv_rows(accepted_rows_path)
    split_rows = read_csv_rows(split_rows_path)
    rows, merge_summary = merge_accepted_rows_with_split(accepted_rows, split_rows)
    write_json(run_dir / "merge_summary.json", merge_summary)
    if merge_summary["missing_split_candidate_count"]:
        raise ValueError(f"split rows missing accepted candidates: {merge_summary['missing_split_candidate_ids'][:5]}")

    candidates = build_gate_candidates(include_vector_grid=True)
    if max_candidates is not None:
        identity = [candidate for candidate in candidates if candidate["gate_candidate_id"] == "identity"]
        non_identity = [candidate for candidate in candidates if candidate["gate_candidate_id"] != "identity"]
        candidates = [*identity, *non_identity[: max(0, int(max_candidates) - len(identity))]]

    scenario_config = load_scenario_config(scenario_config_path)
    env_config = load_env_config(Path(scenario_config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    if not model.is_online_recurrent:
        raise ValueError("M821 calibration grid requires an online recurrent checkpoint")
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

    source_group_ids = {int(row["source_group_id"]) for row in rows if str(row.get("source_group_id", "")).strip()}
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
    identity_by_id, identity_actions_by_id = _evaluate_identity_normal(
        rows=rows,
        snapshots_by_uid=snapshots_by_uid,
        model=model,
        residual_head=residual_head,
        env_config=env_config,
        response_dim=response_dim,
        alpha=float(alpha),
        horizon=int(horizon),
        max_continuation_steps=int(max_continuation_steps),
        device=resolved_device,
    )
    intervention_baseline = _load_intervention_baseline(intervention_rows_path)

    normal_eval_rows: list[dict[str, Any]] = []
    intervention_eval_rows: list[dict[str, Any]] = []
    metrics: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_normal, candidate_intervention = _evaluate_candidate(
            candidate=candidate,
            rows=rows,
            snapshots_by_uid=snapshots_by_uid,
            identity_by_id=identity_by_id,
            identity_actions_by_id=identity_actions_by_id,
            intervention_baseline=intervention_baseline,
            model=model,
            residual_head=residual_head,
            env_config=env_config,
            response_dim=response_dim,
            alpha=float(alpha),
            horizon=int(horizon),
            max_continuation_steps=int(max_continuation_steps),
            device=resolved_device,
        )
        normal_eval_rows.extend(candidate_normal)
        intervention_eval_rows.extend(candidate_intervention)
        for split in ("train", "holdout"):
            normal = _normal_metrics(candidate_normal, candidate, split=split)
            intervention = _intervention_metrics(candidate_intervention, candidate, split=split)
            metrics.append(
                _combine_metrics(
                    normal=normal,
                    intervention=intervention,
                    max_intervention_collision_drop=float(max_intervention_collision_drop),
                    max_mean_action_drift=float(max_mean_action_drift),
                    max_max_action_drift=float(max_max_action_drift),
                    split=split,
                )
            )

    selected_train, metrics = select_train_candidate(metrics)
    selected_candidate_id = str(selected_train["gate_candidate_id"]) if selected_train is not None else ""
    for candidate in candidates:
        candidate["selected_on_train"] = bool(str(candidate["gate_candidate_id"]) == selected_candidate_id)
        ranks = [
            int(row["train_rank"])
            for row in metrics
            if row.get("gate_candidate_id") == candidate["gate_candidate_id"] and row.get("split") == "train" and str(row.get("train_rank", "")).strip()
        ]
        candidate["train_rank"] = ranks[0] if ranks else ""

    train_metrics = [row for row in metrics if row.get("split") == "train"]
    holdout_metrics = [row for row in metrics if row.get("split") == "holdout"]
    selected_train = next(
        (row for row in train_metrics if selected_candidate_id and row["gate_candidate_id"] == selected_candidate_id),
        selected_train,
    )
    selected_holdout = next(
        (row for row in holdout_metrics if selected_train is not None and row["gate_candidate_id"] == selected_train["gate_candidate_id"]),
        None,
    )
    selected_candidate = next((candidate for candidate in candidates if candidate["gate_candidate_id"] == selected_candidate_id), None)
    train_selection_pass = bool(selected_train is not None and parse_bool(selected_train.get("selection_pass", False)))
    holdout_normal_pass = bool(selected_holdout is not None and parse_bool(selected_holdout.get("normal_retention_pass", False)))
    holdout_intervention_pass = bool(selected_holdout is not None and parse_bool(selected_holdout.get("intervention_retention_pass", False)))
    holdout_old_behavior_pass = bool(selected_holdout is not None and parse_bool(selected_holdout.get("old_behavior_pass", False)))
    holdout_acceptance_pass = bool(selected_holdout is not None and parse_bool(selected_holdout.get("holdout_acceptance_pass", False)))
    selected_strong_candidate = bool(selected_holdout is not None and parse_bool(selected_holdout.get("strong_candidate_pass", False)))

    actor_checksum_after = model_parameter_checksum(model)
    residual_checksum_after = model_parameter_checksum(residual_head)
    result_class = classify_v4_adaptive_primary_calibration_grid(
        actor_changed=bool(actor_checksum_before != actor_checksum_after),
        residual_changed=bool(residual_checksum_before != residual_checksum_after),
        trained_adaptive_calibrator=False,
        ppo_used=False,
        promoted=False,
        selected_family=str(selected_candidate.get("family", "")) if selected_candidate is not None else "",
        train_selection_pass=train_selection_pass,
        holdout_normal_pass=holdout_normal_pass,
        holdout_intervention_pass=holdout_intervention_pass,
        holdout_old_behavior_pass=holdout_old_behavior_pass,
        holdout_acceptance_pass=holdout_acceptance_pass,
        selected_strong_candidate=selected_strong_candidate,
    )

    write_csv_rows(run_dir / "candidate_grid.csv", candidates, fieldnames=CANDIDATE_GRID_FIELDS)
    write_csv_rows(run_dir / "normal_eval_rows.csv", normal_eval_rows, fieldnames=NORMAL_ROW_FIELDS)
    write_csv_rows(run_dir / "intervention_candidate_metrics.csv", intervention_eval_rows, fieldnames=INTERVENTION_ROW_FIELDS)
    write_csv_rows(run_dir / "train_candidate_metrics.csv", train_metrics, fieldnames=METRIC_FIELDS)
    write_csv_rows(run_dir / "holdout_candidate_metrics.csv", holdout_metrics, fieldnames=METRIC_FIELDS)

    selected_payload = {
        "selected_candidate": selected_candidate or {},
        "selected_train_metrics": selected_train or {},
        "selected_holdout_metrics": selected_holdout or {},
        "selection_used_holdout": False,
        "result_class": result_class,
    }
    write_json(run_dir / "selected_candidate.json", selected_payload)

    gate_rows = [
        {
            "gate_name": "actor_checksum_unchanged",
            "value": actor_checksum_before == actor_checksum_after,
            "threshold": "true",
            "passed": actor_checksum_before == actor_checksum_after,
            "notes": "",
        },
        {
            "gate_name": "residual_head_checksum_unchanged",
            "value": residual_checksum_before == residual_checksum_after,
            "threshold": "true",
            "passed": residual_checksum_before == residual_checksum_after,
            "notes": "",
        },
        {
            "gate_name": "train_selection_pass",
            "value": train_selection_pass,
            "threshold": "true",
            "passed": train_selection_pass,
            "notes": selected_candidate_id,
        },
        {
            "gate_name": "holdout_acceptance_pass",
            "value": holdout_acceptance_pass,
            "threshold": "true for candidate claim",
            "passed": holdout_acceptance_pass,
            "notes": result_class,
        },
        {
            "gate_name": "selected_strong_candidate",
            "value": selected_strong_candidate,
            "threshold": "p05 lift >= 1e-5 or mean lift >= 2e-5",
            "passed": selected_strong_candidate,
            "notes": "not required for identity-only classification",
        },
    ]
    write_csv_rows(run_dir / "gate_summary.csv", gate_rows, fieldnames=GATE_SUMMARY_FIELDS)

    summary = {
        "run_type": "v4_adaptive_primary_calibration_grid",
        "checkpoint": checkpoint_path,
        "residual_head": residual_head_path,
        "accepted_rows": accepted_rows_path,
        "split_rows": split_rows_path,
        "intervention_rows": intervention_rows_path,
        "scenario_config": scenario_config_path,
        "alpha": float(alpha),
        "candidate_count": int(len(candidates)),
        "normal_eval_row_count": int(len(normal_eval_rows)),
        "intervention_eval_row_count": int(len(intervention_eval_rows)),
        "merge_summary": merge_summary,
        "snapshot_lookup_rows": int(len(snapshots_by_uid)),
        "identity_normal_rows": int(len(identity_by_id)),
        "selected_candidate_id": selected_candidate_id,
        "selected_candidate": selected_candidate or {},
        "selected_train_metrics": selected_train or {},
        "selected_holdout_metrics": selected_holdout or {},
        "selection_used_holdout": False,
        "train_selection_pass": train_selection_pass,
        "holdout_normal_pass": holdout_normal_pass,
        "holdout_intervention_pass": holdout_intervention_pass,
        "holdout_old_behavior_pass": holdout_old_behavior_pass,
        "holdout_acceptance_pass": holdout_acceptance_pass,
        "selected_strong_candidate": selected_strong_candidate,
        "actor_backbone_changed": bool(actor_checksum_before != actor_checksum_after),
        "residual_head_changed": bool(residual_checksum_before != residual_checksum_after),
        "base_actor_checksum_before": actor_checksum_before,
        "base_actor_checksum_after": actor_checksum_after,
        "residual_head_checksum_before": residual_checksum_before,
        "residual_head_checksum_after": residual_checksum_after,
        "trained_adaptive_calibrator": False,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "result_class": result_class,
        "elapsed_seconds": float(time.time() - start),
        "summary_json": run_dir / "summary.json",
        "candidate_grid_csv": run_dir / "candidate_grid.csv",
        "normal_eval_rows_csv": run_dir / "normal_eval_rows.csv",
        "train_candidate_metrics_csv": run_dir / "train_candidate_metrics.csv",
        "holdout_candidate_metrics_csv": run_dir / "holdout_candidate_metrics.csv",
        "intervention_candidate_metrics_csv": run_dir / "intervention_candidate_metrics.csv",
        "gate_summary_csv": run_dir / "gate_summary.csv",
        "selected_candidate_json": run_dir / "selected_candidate.json",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run exact fixed-gate calibration grid for M814 adaptive primary rows.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--residual-head", type=Path, required=True)
    parser.add_argument("--accepted-rows", type=Path, required=True)
    parser.add_argument("--split-rows", type=Path, required=True)
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
    parser.add_argument("--max-intervention-collision-drop", type=float, default=0.05)
    parser.add_argument("--max-mean-action-drift", type=float, default=0.002)
    parser.add_argument("--max-max-action-drift", type=float, default=0.02)
    parser.add_argument("--max-candidates", type=int, default=None)
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
    summary = run_calibration_grid(
        checkpoint_path=args.checkpoint,
        residual_head_path=args.residual_head,
        accepted_rows_path=args.accepted_rows,
        split_rows_path=args.split_rows,
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
        max_intervention_collision_drop=float(args.max_intervention_collision_drop),
        max_mean_action_drift=float(args.max_mean_action_drift),
        max_max_action_drift=float(args.max_max_action_drift),
        max_candidates=args.max_candidates,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
