"""Mine terminal-margin-sensitive trajectory source rows."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.grounded_capability_action_target_miner import SurfaceConfig, parse_surface_config, risk_score
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.matched_history_outcome_gate import OutcomeSnapshot, collect_requested_outcome_snapshots
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.terminal_margin_recovery_anchor import _rollout_first_action_override, parse_float_list
from autodrift.train_ppo import ActorCritic, resolve_device


SOURCE_ROW_FIELDNAMES = [
    "source_row_id",
    "surface",
    "target",
    "variant",
    "split",
    "physical_pair_key",
    "source_index",
    "left_seed",
    "right_seed",
    "left_step",
    "right_step",
    "sequence_length",
]

CANDIDATE_FIELDNAMES = [
    "source_row_id",
    "surface",
    "target",
    "variant",
    "split",
    "physical_pair_key",
    "left_seed",
    "right_seed",
    "left_step",
    "right_step",
    "normal_success",
    "normal_collision",
    "normal_off_road",
    "normal_spin_out",
    "normal_margin",
    "normal_risk",
    "normal_failed_rejected",
    "normal_boundary",
    "base_steer",
    "base_throttle",
    "base_brake",
    "wrong_steer",
    "wrong_throttle",
    "wrong_brake",
    "wrong_success",
    "wrong_collision",
    "wrong_off_road",
    "wrong_spin_out",
    "wrong_margin",
    "wrong_risk",
    "history_margin_gap",
    "history_risk_gap",
    "history_action_critical",
    "margin_sensitivity",
    "risk_sensitivity",
    "success_flip_count",
    "collision_flip_count",
    "off_road_flip_count",
    "spin_flip_count",
    "trajectory_boundary",
    "terminal_cliff",
    "accepted",
    "acceptance_reason",
    "result_label",
    "assigned_split",
]

PERTURBATION_FIELDNAMES = [
    "source_row_id",
    "candidate_id",
    "surface",
    "target",
    "left_seed",
    "left_step",
    "steer_delta",
    "throttle_delta",
    "brake_delta",
    "action_l2",
    "candidate_steer",
    "candidate_throttle",
    "candidate_brake",
    "success",
    "collision",
    "off_road",
    "spin_out",
    "terminal_reason",
    "margin",
    "risk",
    "return",
]


def _finite_float(value: Any, default: float = float("nan")) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    return parsed if np.isfinite(parsed) else float(default)


def _bool(value: Any) -> bool:
    return bool(value)


def _margin(result: dict[str, Any]) -> float:
    return _finite_float(result.get("min_clearance_margin"))


def _result_bool(result: dict[str, Any], key: str) -> bool:
    return bool(result.get(key, False))


def _with_hidden(snapshot: OutcomeSnapshot, hidden: torch.Tensor) -> OutcomeSnapshot:
    return OutcomeSnapshot(
        seed=snapshot.seed,
        step=snapshot.step,
        observation=snapshot.observation.copy(),
        hidden=hidden.detach().clone(),
        env=snapshot.env,
        info=dict(snapshot.info),
    )


def _snapshot(
    snapshots: dict[tuple[int, int], OutcomeSnapshot],
    seed: int,
    step: int,
) -> OutcomeSnapshot | None:
    return snapshots.get((int(seed), int(step)))


def select_source_rows(replay_rows: pd.DataFrame, max_scenarios: int) -> pd.DataFrame:
    required = {
        "surface",
        "target",
        "variant",
        "split",
        "physical_pair_key",
        "source_index",
        "left_seed",
        "right_seed",
        "left_step",
        "right_step",
    }
    missing = sorted(required.difference(replay_rows.columns))
    if missing:
        raise ValueError("source rows missing columns: " + ", ".join(missing))
    frame = replay_rows[
        replay_rows["variant"].astype(str).eq("wrong_matched_history")
    ].copy()
    if frame.empty:
        return frame.reset_index(drop=True)
    if "sequence_length" not in frame.columns:
        frame["sequence_length"] = -1
    frame = frame.sort_values(
        [
            "split",
            "surface",
            "target",
            "physical_pair_key",
            "left_seed",
            "left_step",
            "right_seed",
            "right_step",
        ],
        kind="mergesort",
    )
    duplicate_key = [
        "surface",
        "target",
        "variant",
        "physical_pair_key",
        "left_seed",
        "left_step",
        "right_seed",
        "right_step",
    ]
    frame = frame.drop_duplicates(subset=duplicate_key, keep="first").reset_index(drop=True)
    if int(max_scenarios) > 0:
        frame = frame.head(int(max_scenarios)).reset_index(drop=True)
    frame.insert(0, "source_row_id", np.arange(len(frame), dtype=np.int64))
    return frame[SOURCE_ROW_FIELDNAMES].copy()


def request_steps_for_source_rows(rows: pd.DataFrame) -> dict[int, set[int]]:
    requests: dict[int, set[int]] = {}
    for _, row in rows.iterrows():
        requests.setdefault(int(row["left_seed"]), set()).add(int(row["left_step"]))
        requests.setdefault(int(row["right_seed"]), set()).add(int(row["right_step"]))
    return requests


def build_first_action_perturbations(
    base_action: np.ndarray,
    *,
    steer_deltas: tuple[float, ...],
    throttle_deltas: tuple[float, ...],
    brake_deltas: tuple[float, ...],
) -> list[dict[str, Any]]:
    base = np.asarray(base_action, dtype=np.float32)
    if base.shape != (3,):
        raise ValueError(f"base action must have shape (3,), got {base.shape}")
    perturbations: list[tuple[float, float, float]] = [(0.0, 0.0, 0.0)]
    perturbations.extend((float(delta), 0.0, 0.0) for delta in steer_deltas if float(delta) != 0.0)
    perturbations.extend((0.0, float(delta), 0.0) for delta in throttle_deltas if float(delta) != 0.0)
    perturbations.extend((0.0, 0.0, float(delta)) for delta in brake_deltas if float(delta) != 0.0)
    for steer in steer_deltas:
        for brake in brake_deltas:
            if float(steer) != 0.0 and float(brake) != 0.0:
                perturbations.append((float(steer), 0.0, float(brake)))

    seen: set[tuple[float, float, float]] = set()
    rows: list[dict[str, Any]] = []
    for steer_delta, throttle_delta, brake_delta in perturbations:
        key = (steer_delta, throttle_delta, brake_delta)
        if key in seen:
            continue
        seen.add(key)
        delta = np.asarray([steer_delta, throttle_delta, brake_delta], dtype=np.float32)
        action = np.clip(base + delta, -1.0, 1.0).astype(np.float32)
        rows.append(
            {
                "candidate_id": int(len(rows)),
                "steer_delta": float(steer_delta),
                "throttle_delta": float(throttle_delta),
                "brake_delta": float(brake_delta),
                "action": action,
                "action_l2": float(np.linalg.norm(action.astype(np.float64) - base.astype(np.float64))),
            }
        )
    return rows


def assigned_split(source_row_id: int, heldout_fraction: float) -> str:
    if float(heldout_fraction) <= 0.0:
        return "train"
    period = max(2, int(round(1.0 / max(float(heldout_fraction), 1e-9))))
    return "heldout" if int(source_row_id) % period == 0 else "train"


def classify_source_result(
    *,
    accepted_rows: int,
    trajectory_sensitive_rows: int,
    history_action_critical_rows: int,
    normal_success_candidates: int,
    normal_failed_rejected: int,
    unique_seeds: int,
    unique_sources: int,
    max_seed_dominance: float,
    max_source_dominance: float,
    min_accepted_rows: int,
    min_trajectory_rows: int,
    min_history_rows: int,
    min_unique_seeds: int,
    min_unique_sources: int,
    max_seed_dominance_threshold: float,
    max_source_dominance_threshold: float,
) -> str:
    if int(normal_success_candidates) == 0 and int(normal_failed_rejected) > 0:
        return "normal_failed_only"
    if int(trajectory_sensitive_rows) <= 0 and int(history_action_critical_rows) <= 0:
        return "surface_empty"
    if int(history_action_critical_rows) <= 0 and int(trajectory_sensitive_rows) > 0:
        return "history_insensitive"
    diversity_ok = (
        int(unique_seeds) >= int(min_unique_seeds)
        and int(unique_sources) >= int(min_unique_sources)
        and float(max_seed_dominance) <= float(max_seed_dominance_threshold)
        and float(max_source_dominance) <= float(max_source_dominance_threshold)
    )
    volume_ok = (
        int(accepted_rows) >= int(min_accepted_rows)
        and int(trajectory_sensitive_rows) >= int(min_trajectory_rows)
        and int(history_action_critical_rows) >= int(min_history_rows)
    )
    if volume_ok and diversity_ok:
        return "source_positive"
    return "source_sparse"


def summarize_source_rows(
    candidate_rows: list[dict[str, Any]],
    accepted_rows: list[dict[str, Any]],
    *,
    rows_attempted: int,
    snapshots_collected: int,
    heldout_fraction: float,
    min_accepted_rows: int,
    min_trajectory_rows: int,
    min_history_rows: int,
    min_unique_seeds: int,
    min_unique_sources: int,
    max_seed_dominance_threshold: float,
    max_source_dominance_threshold: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    candidate_frame = pd.DataFrame(candidate_rows)
    accepted_frame = pd.DataFrame(accepted_rows)
    normal_failed_rejected = int(candidate_frame["normal_failed_rejected"].astype(bool).sum()) if not candidate_frame.empty else 0
    normal_success_candidates = int((~candidate_frame["normal_failed_rejected"].astype(bool)).sum()) if not candidate_frame.empty else 0
    trajectory_sensitive_rows = int(candidate_frame["trajectory_boundary"].astype(bool).sum()) if not candidate_frame.empty else 0
    history_action_critical_rows = int(candidate_frame["history_action_critical"].astype(bool).sum()) if not candidate_frame.empty else 0
    terminal_cliff_rows = int(candidate_frame["terminal_cliff"].astype(bool).sum()) if not candidate_frame.empty else 0
    heldout_rows = int(accepted_frame["assigned_split"].astype(str).eq("heldout").sum()) if not accepted_frame.empty else 0
    unique_seeds = int(accepted_frame["left_seed"].nunique()) if not accepted_frame.empty else 0
    unique_sources = int(accepted_frame["physical_pair_key"].nunique()) if not accepted_frame.empty else 0
    if not accepted_frame.empty:
        seed_counts = accepted_frame["left_seed"].value_counts()
        source_counts = accepted_frame["physical_pair_key"].value_counts()
        max_seed_dominance = float(seed_counts.max() / max(len(accepted_frame), 1))
        max_source_dominance = float(source_counts.max() / max(len(accepted_frame), 1))
    else:
        max_seed_dominance = 0.0
        max_source_dominance = 0.0

    margin_sensitivity = candidate_frame["margin_sensitivity"].astype(float) if not candidate_frame.empty else pd.Series(dtype=float)
    risk_sensitivity = candidate_frame["risk_sensitivity"].astype(float) if not candidate_frame.empty else pd.Series(dtype=float)
    result_class = classify_source_result(
        accepted_rows=len(accepted_rows),
        trajectory_sensitive_rows=trajectory_sensitive_rows,
        history_action_critical_rows=history_action_critical_rows,
        normal_success_candidates=normal_success_candidates,
        normal_failed_rejected=normal_failed_rejected,
        unique_seeds=unique_seeds,
        unique_sources=unique_sources,
        max_seed_dominance=max_seed_dominance,
        max_source_dominance=max_source_dominance,
        min_accepted_rows=min_accepted_rows,
        min_trajectory_rows=min_trajectory_rows,
        min_history_rows=min_history_rows,
        min_unique_seeds=min_unique_seeds,
        min_unique_sources=min_unique_sources,
        max_seed_dominance_threshold=max_seed_dominance_threshold,
        max_source_dominance_threshold=max_source_dominance_threshold,
    )

    if accepted_frame.empty:
        source_summary: list[dict[str, Any]] = []
        split_summary: list[dict[str, Any]] = []
    else:
        source_summary = (
            accepted_frame.groupby(["surface", "target"], observed=True)
            .agg(
                rows=("source_row_id", "count"),
                trajectory_boundary_rows=("trajectory_boundary", "sum"),
                history_action_critical_rows=("history_action_critical", "sum"),
                terminal_cliff_rows=("terminal_cliff", "sum"),
            )
            .reset_index()
            .to_dict(orient="records")
        )
        split_summary = (
            accepted_frame.groupby("assigned_split", observed=True)
            .agg(
                rows=("source_row_id", "count"),
                trajectory_boundary_rows=("trajectory_boundary", "sum"),
                history_action_critical_rows=("history_action_critical", "sum"),
                terminal_cliff_rows=("terminal_cliff", "sum"),
            )
            .reset_index()
            .to_dict(orient="records")
        )

    summary = {
        "rows_attempted": int(rows_attempted),
        "snapshots_collected": int(snapshots_collected),
        "normal_success_candidates": int(normal_success_candidates),
        "normal_failed_rejected": int(normal_failed_rejected),
        "trajectory_sensitive_rows": int(trajectory_sensitive_rows),
        "history_action_critical_rows": int(history_action_critical_rows),
        "terminal_cliff_rows": int(terminal_cliff_rows),
        "accepted_rows": int(len(accepted_rows)),
        "heldout_rows": int(heldout_rows),
        "heldout_fraction": float(heldout_fraction),
        "unique_seeds": int(unique_seeds),
        "unique_sources": int(unique_sources),
        "max_seed_dominance": float(max_seed_dominance),
        "max_source_dominance": float(max_source_dominance),
        "margin_sensitivity_mean": float(margin_sensitivity.mean()) if len(margin_sensitivity) else float("nan"),
        "margin_sensitivity_p95": float(np.nanpercentile(margin_sensitivity.to_numpy(), 95)) if len(margin_sensitivity) else float("nan"),
        "risk_sensitivity_mean": float(risk_sensitivity.mean()) if len(risk_sensitivity) else float("nan"),
        "risk_sensitivity_p95": float(np.nanpercentile(risk_sensitivity.to_numpy(), 95)) if len(risk_sensitivity) else float("nan"),
        "success_flip_count": int(candidate_frame["success_flip_count"].astype(int).sum()) if not candidate_frame.empty else 0,
        "collision_flip_count": int(candidate_frame["collision_flip_count"].astype(int).sum()) if not candidate_frame.empty else 0,
        "off_road_flip_count": int(candidate_frame["off_road_flip_count"].astype(int).sum()) if not candidate_frame.empty else 0,
        "spin_flip_count": int(candidate_frame["spin_flip_count"].astype(int).sum()) if not candidate_frame.empty else 0,
        "result_class": result_class,
        "source_positive": bool(result_class == "source_positive"),
    }
    return source_summary, split_summary, summary


def _candidate_result_row(
    *,
    source: pd.Series,
    base_action: np.ndarray,
    wrong_action: np.ndarray,
    baseline: dict[str, Any],
    wrong: dict[str, Any],
    perturbation_rows: list[dict[str, Any]],
    max_boundary_margin: float,
    terminal_cliff_margin: float,
    min_margin_sensitivity: float,
    min_risk_sensitivity: float,
    min_history_margin_gap: float,
    min_history_risk_gap: float,
    heldout_fraction: float,
) -> dict[str, Any]:
    normal_margin = _margin(baseline)
    normal_risk = risk_score(baseline)
    normal_failed = (
        not _result_bool(baseline, "success")
        or _result_bool(baseline, "collision")
        or _result_bool(baseline, "off_road")
        or _result_bool(baseline, "spin_out")
        or not np.isfinite(normal_margin)
        or normal_margin < 0.0
    )
    candidate_margins = np.asarray([_finite_float(row["margin"]) for row in perturbation_rows], dtype=float)
    candidate_risks = np.asarray([_finite_float(row["risk"]) for row in perturbation_rows], dtype=float)
    finite_margins = candidate_margins[np.isfinite(candidate_margins)]
    finite_risks = candidate_risks[np.isfinite(candidate_risks)]
    margin_sensitivity = float(np.max(finite_margins) - np.min(finite_margins)) if len(finite_margins) else float("nan")
    risk_sensitivity = float(np.max(finite_risks) - np.min(finite_risks)) if len(finite_risks) else float("nan")
    success_flip_count = sum(bool(row["success"]) != _result_bool(baseline, "success") for row in perturbation_rows)
    collision_flip_count = sum(bool(row["collision"]) != _result_bool(baseline, "collision") for row in perturbation_rows)
    off_road_flip_count = sum(bool(row["off_road"]) != _result_bool(baseline, "off_road") for row in perturbation_rows)
    spin_flip_count = sum(bool(row["spin_out"]) != _result_bool(baseline, "spin_out") for row in perturbation_rows)

    wrong_margin = _margin(wrong)
    wrong_risk = risk_score(wrong)
    history_margin_gap = normal_margin - wrong_margin if np.isfinite(normal_margin) and np.isfinite(wrong_margin) else float("nan")
    history_risk_gap = wrong_risk - normal_risk if np.isfinite(wrong_risk) and np.isfinite(normal_risk) else float("nan")
    history_worse = (
        (_result_bool(baseline, "success") and not _result_bool(wrong, "success"))
        or (not _result_bool(baseline, "collision") and _result_bool(wrong, "collision"))
        or (not _result_bool(baseline, "off_road") and _result_bool(wrong, "off_road"))
        or (not _result_bool(baseline, "spin_out") and _result_bool(wrong, "spin_out"))
    )
    history_action_critical = bool(
        not normal_failed
        and (
            history_worse
            or (np.isfinite(history_margin_gap) and history_margin_gap >= float(min_history_margin_gap))
            or (np.isfinite(history_risk_gap) and history_risk_gap >= float(min_history_risk_gap))
        )
    )
    trajectory_boundary = bool(
        not normal_failed
        and (
            (np.isfinite(margin_sensitivity) and margin_sensitivity >= float(min_margin_sensitivity))
            or (np.isfinite(risk_sensitivity) and risk_sensitivity >= float(min_risk_sensitivity))
            or success_flip_count > 0
            or collision_flip_count > 0
            or off_road_flip_count > 0
            or spin_flip_count > 0
        )
    )
    terminal_cliff = bool(not normal_failed and np.isfinite(normal_margin) and normal_margin <= float(terminal_cliff_margin))
    accepted = bool(trajectory_boundary or history_action_critical or terminal_cliff)
    if normal_failed:
        reason = "normal_failed_rejected"
        label = "normal_failed"
    elif history_action_critical:
        reason = "history_action_critical"
        label = "history_action_critical"
    elif trajectory_boundary:
        reason = "trajectory_boundary"
        label = "trajectory_boundary"
    elif terminal_cliff:
        reason = "terminal_cliff"
        label = "terminal_cliff"
    else:
        reason = "insensitive"
        label = "insensitive"

    source_row_id = int(source["source_row_id"])
    return {
        "source_row_id": source_row_id,
        "surface": str(source["surface"]),
        "target": str(source["target"]),
        "variant": str(source["variant"]),
        "split": str(source["split"]),
        "physical_pair_key": str(source["physical_pair_key"]),
        "left_seed": int(source["left_seed"]),
        "right_seed": int(source["right_seed"]),
        "left_step": int(source["left_step"]),
        "right_step": int(source["right_step"]),
        "normal_success": _result_bool(baseline, "success"),
        "normal_collision": _result_bool(baseline, "collision"),
        "normal_off_road": _result_bool(baseline, "off_road"),
        "normal_spin_out": _result_bool(baseline, "spin_out"),
        "normal_margin": normal_margin,
        "normal_risk": normal_risk,
        "normal_failed_rejected": bool(normal_failed),
        "normal_boundary": bool(not normal_failed and np.isfinite(normal_margin) and normal_margin <= float(max_boundary_margin)),
        "base_steer": float(base_action[0]),
        "base_throttle": float(base_action[1]),
        "base_brake": float(base_action[2]),
        "wrong_steer": float(wrong_action[0]),
        "wrong_throttle": float(wrong_action[1]),
        "wrong_brake": float(wrong_action[2]),
        "wrong_success": _result_bool(wrong, "success"),
        "wrong_collision": _result_bool(wrong, "collision"),
        "wrong_off_road": _result_bool(wrong, "off_road"),
        "wrong_spin_out": _result_bool(wrong, "spin_out"),
        "wrong_margin": wrong_margin,
        "wrong_risk": wrong_risk,
        "history_margin_gap": history_margin_gap,
        "history_risk_gap": history_risk_gap,
        "history_action_critical": history_action_critical,
        "margin_sensitivity": margin_sensitivity,
        "risk_sensitivity": risk_sensitivity,
        "success_flip_count": int(success_flip_count),
        "collision_flip_count": int(collision_flip_count),
        "off_road_flip_count": int(off_road_flip_count),
        "spin_flip_count": int(spin_flip_count),
        "trajectory_boundary": trajectory_boundary,
        "terminal_cliff": terminal_cliff,
        "accepted": accepted,
        "acceptance_reason": reason,
        "result_label": label,
        "assigned_split": assigned_split(source_row_id, heldout_fraction),
    }


def mine_surface(
    *,
    model: ActorCritic,
    env_config_path: Path,
    source_rows: pd.DataFrame,
    steer_deltas: tuple[float, ...],
    throttle_deltas: tuple[float, ...],
    brake_deltas: tuple[float, ...],
    max_boundary_margin: float,
    terminal_cliff_margin: float,
    min_margin_sensitivity: float,
    min_risk_sensitivity: float,
    min_history_margin_gap: float,
    min_history_risk_gap: float,
    max_continuation_steps: int,
    heldout_fraction: float,
    device: torch.device,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], int]:
    env_config = load_env_config(env_config_path)
    snapshots = collect_requested_outcome_snapshots(
        model=model,
        env_config=env_config,
        requests=request_steps_for_source_rows(source_rows),
        device=device,
    )
    candidate_rows: list[dict[str, Any]] = []
    perturbation_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []

    for _, source in source_rows.iterrows():
        left = _snapshot(snapshots, int(source["left_seed"]), int(source["left_step"]))
        right = _snapshot(snapshots, int(source["right_seed"]), int(source["right_step"]))
        if left is None or right is None:
            rejected_rows.append(
                {
                    "source_row_id": int(source["source_row_id"]),
                    "surface": str(source["surface"]),
                    "target": str(source["target"]),
                    "left_seed": int(source["left_seed"]),
                    "left_step": int(source["left_step"]),
                    "rejection_reason": "snapshot_reconstruction_failed",
                }
            )
            continue
        base_action, _ = deterministic_action_from_hidden(model, left.observation, left.hidden, device)
        wrong_action, _ = deterministic_action_from_hidden(model, left.observation, right.hidden, device)
        baseline = _rollout_first_action_override(
            model=model,
            snapshot=left,
            first_action=base_action,
            max_continuation_steps=max_continuation_steps,
            device=device,
        )
        wrong_snapshot = _with_hidden(left, right.hidden)
        wrong = _rollout_first_action_override(
            model=model,
            snapshot=wrong_snapshot,
            first_action=wrong_action,
            max_continuation_steps=max_continuation_steps,
            device=device,
        )

        row_perturbations: list[dict[str, Any]] = []
        for item in build_first_action_perturbations(
            base_action,
            steer_deltas=steer_deltas,
            throttle_deltas=throttle_deltas,
            brake_deltas=brake_deltas,
        ):
            result = _rollout_first_action_override(
                model=model,
                snapshot=left,
                first_action=item["action"],
                max_continuation_steps=max_continuation_steps,
                device=device,
            )
            row = {
                "source_row_id": int(source["source_row_id"]),
                "candidate_id": int(item["candidate_id"]),
                "surface": str(source["surface"]),
                "target": str(source["target"]),
                "left_seed": int(source["left_seed"]),
                "left_step": int(source["left_step"]),
                "steer_delta": float(item["steer_delta"]),
                "throttle_delta": float(item["throttle_delta"]),
                "brake_delta": float(item["brake_delta"]),
                "action_l2": float(item["action_l2"]),
                "candidate_steer": float(item["action"][0]),
                "candidate_throttle": float(item["action"][1]),
                "candidate_brake": float(item["action"][2]),
                "success": _result_bool(result, "success"),
                "collision": _result_bool(result, "collision"),
                "off_road": _result_bool(result, "off_road"),
                "spin_out": _result_bool(result, "spin_out"),
                "terminal_reason": str(result.get("terminal_reason", "")),
                "margin": _margin(result),
                "risk": risk_score(result),
                "return": _finite_float(result.get("return")),
            }
            perturbation_rows.append(row)
            row_perturbations.append(row)

        candidate = _candidate_result_row(
            source=source,
            base_action=np.asarray(base_action, dtype=np.float32),
            wrong_action=np.asarray(wrong_action, dtype=np.float32),
            baseline=baseline,
            wrong=wrong,
            perturbation_rows=row_perturbations,
            max_boundary_margin=max_boundary_margin,
            terminal_cliff_margin=terminal_cliff_margin,
            min_margin_sensitivity=min_margin_sensitivity,
            min_risk_sensitivity=min_risk_sensitivity,
            min_history_margin_gap=min_history_margin_gap,
            min_history_risk_gap=min_history_risk_gap,
            heldout_fraction=heldout_fraction,
        )
        candidate_rows.append(candidate)
        if not bool(candidate["accepted"]):
            rejected_rows.append(
                {
                    "source_row_id": int(source["source_row_id"]),
                    "surface": str(source["surface"]),
                    "target": str(source["target"]),
                    "left_seed": int(source["left_seed"]),
                    "left_step": int(source["left_step"]),
                    "rejection_reason": str(candidate["acceptance_reason"]),
                    "normal_margin": float(candidate["normal_margin"]),
                    "margin_sensitivity": float(candidate["margin_sensitivity"]),
                    "risk_sensitivity": float(candidate["risk_sensitivity"]),
                    "history_margin_gap": float(candidate["history_margin_gap"]),
                    "history_risk_gap": float(candidate["history_risk_gap"]),
                }
            )
    return candidate_rows, perturbation_rows, rejected_rows, len(snapshots)


def run_trajectory_terminal_boundary_source_miner(
    *,
    checkpoint_path: Path,
    source_rows_csv: Path,
    surface_configs: tuple[SurfaceConfig, ...],
    max_scenarios: int,
    steer_deltas: tuple[float, ...],
    throttle_deltas: tuple[float, ...],
    brake_deltas: tuple[float, ...],
    max_boundary_margin: float,
    terminal_cliff_margin: float,
    min_margin_sensitivity: float,
    min_risk_sensitivity: float,
    min_history_margin_gap: float,
    min_history_risk_gap: float,
    max_continuation_steps: int,
    heldout_fraction: float,
    min_accepted_rows: int,
    min_trajectory_rows: int,
    min_history_rows: int,
    min_unique_seeds: int,
    min_unique_sources: int,
    max_seed_dominance: float,
    max_source_dominance: float,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    checksum_before = model_parameter_checksum(model)
    source_frame = select_source_rows(pd.read_csv(source_rows_csv), max_scenarios=max_scenarios)
    surface_config_by_name = {item.surface: item.env_config_path for item in surface_configs}
    missing_configs = sorted(set(source_frame["surface"].astype(str)).difference(surface_config_by_name)) if not source_frame.empty else []
    if missing_configs:
        raise ValueError(f"missing env configs for surfaces: {missing_configs}")

    candidate_rows: list[dict[str, Any]] = []
    perturbation_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    snapshots_collected = 0
    for surface, surface_rows in source_frame.groupby("surface", observed=True):
        surface_candidates, surface_perturbations, surface_rejected, surface_snapshot_count = mine_surface(
            model=model,
            env_config_path=surface_config_by_name[str(surface)],
            source_rows=surface_rows.reset_index(drop=True),
            steer_deltas=steer_deltas,
            throttle_deltas=throttle_deltas,
            brake_deltas=brake_deltas,
            max_boundary_margin=max_boundary_margin,
            terminal_cliff_margin=terminal_cliff_margin,
            min_margin_sensitivity=min_margin_sensitivity,
            min_risk_sensitivity=min_risk_sensitivity,
            min_history_margin_gap=min_history_margin_gap,
            min_history_risk_gap=min_history_risk_gap,
            max_continuation_steps=max_continuation_steps,
            heldout_fraction=heldout_fraction,
            device=resolved_device,
        )
        candidate_rows.extend(surface_candidates)
        perturbation_rows.extend(surface_perturbations)
        rejected_rows.extend(surface_rejected)
        snapshots_collected += int(surface_snapshot_count)

    accepted_rows = [row for row in candidate_rows if bool(row.get("accepted", False))]
    source_summary, split_summary, aggregate = summarize_source_rows(
        candidate_rows,
        accepted_rows,
        rows_attempted=len(source_frame),
        snapshots_collected=snapshots_collected,
        heldout_fraction=heldout_fraction,
        min_accepted_rows=min_accepted_rows,
        min_trajectory_rows=min_trajectory_rows,
        min_history_rows=min_history_rows,
        min_unique_seeds=min_unique_seeds,
        min_unique_sources=min_unique_sources,
        max_seed_dominance_threshold=max_seed_dominance,
        max_source_dominance_threshold=max_source_dominance,
    )
    checksum_after = model_parameter_checksum(model)
    summary = {
        "run_type": "trajectory_terminal_boundary_source_miner",
        "checkpoint": checkpoint_path,
        "source_rows_csv": source_rows_csv,
        "surface_configs": {item.surface: item.env_config_path for item in surface_configs},
        "max_scenarios": int(max_scenarios),
        "steer_deltas": steer_deltas,
        "throttle_deltas": throttle_deltas,
        "brake_deltas": brake_deltas,
        "max_boundary_margin": float(max_boundary_margin),
        "terminal_cliff_margin": float(terminal_cliff_margin),
        "min_margin_sensitivity": float(min_margin_sensitivity),
        "min_risk_sensitivity": float(min_risk_sensitivity),
        "min_history_margin_gap": float(min_history_margin_gap),
        "min_history_risk_gap": float(min_history_risk_gap),
        "max_continuation_steps": int(max_continuation_steps),
        "min_accepted_rows": int(min_accepted_rows),
        "min_trajectory_rows": int(min_trajectory_rows),
        "min_history_rows": int(min_history_rows),
        "min_unique_seeds": int(min_unique_seeds),
        "min_unique_sources": int(min_unique_sources),
        "max_seed_dominance_threshold": float(max_seed_dominance),
        "max_source_dominance_threshold": float(max_source_dominance),
        "device": str(resolved_device),
        "source_rows_csv_written": run_dir / "source_rows.csv",
        "candidate_rows_csv": run_dir / "candidate_rows.csv",
        "perturbation_rollouts_csv": run_dir / "perturbation_rollouts.csv",
        "accepted_rows_csv": run_dir / "accepted_rows.csv",
        "source_summary_csv": run_dir / "source_summary.csv",
        "split_summary_csv": run_dir / "split_summary.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
        "model_checksum_before": checksum_before,
        "model_checksum_after": checksum_after,
        "actor_parameters_changed": bool(checksum_before != checksum_after),
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        **aggregate,
    }
    write_csv_rows(run_dir / "source_rows.csv", source_frame.to_dict(orient="records"), fieldnames=SOURCE_ROW_FIELDNAMES)
    write_csv_rows(run_dir / "candidate_rows.csv", candidate_rows, fieldnames=CANDIDATE_FIELDNAMES)
    write_csv_rows(run_dir / "perturbation_rollouts.csv", perturbation_rows, fieldnames=PERTURBATION_FIELDNAMES)
    write_csv_rows(run_dir / "accepted_rows.csv", accepted_rows, fieldnames=CANDIDATE_FIELDNAMES)
    write_csv_rows(run_dir / "source_summary.csv", source_summary)
    write_csv_rows(run_dir / "split_summary.csv", split_summary)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine terminal-margin-sensitive trajectory source rows.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--source-rows", type=Path, default=Path("runs/m692_gate_margin_closed_loop_replay/replay_rows.csv"))
    parser.add_argument("--surface-config", type=parse_surface_config, action="append", required=True)
    parser.add_argument("--max-scenarios", type=int, default=256)
    parser.add_argument("--steer-deltas", type=parse_float_list, default=(-0.02, -0.01, 0.01, 0.02))
    parser.add_argument("--throttle-deltas", type=parse_float_list, default=(-0.03, 0.03))
    parser.add_argument("--brake-deltas", type=parse_float_list, default=(-0.03, 0.03))
    parser.add_argument("--max-boundary-margin", type=float, default=0.15)
    parser.add_argument("--terminal-cliff-margin", type=float, default=0.02)
    parser.add_argument("--min-margin-sensitivity", type=float, default=0.02)
    parser.add_argument("--min-risk-sensitivity", type=float, default=0.02)
    parser.add_argument("--min-history-margin-gap", type=float, default=0.01)
    parser.add_argument("--min-history-risk-gap", type=float, default=0.01)
    parser.add_argument("--max-continuation-steps", type=int, default=40)
    parser.add_argument("--heldout-fraction", type=float, default=0.2)
    parser.add_argument("--min-accepted-rows", type=int, default=80)
    parser.add_argument("--min-trajectory-rows", type=int, default=50)
    parser.add_argument("--min-history-rows", type=int, default=20)
    parser.add_argument("--min-unique-seeds", type=int, default=20)
    parser.add_argument("--min-unique-sources", type=int, default=20)
    parser.add_argument("--max-seed-dominance", type=float, default=0.10)
    parser.add_argument("--max-source-dominance", type=float, default=0.25)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="trajectory_terminal_boundary_source_miner")
    summary = run_trajectory_terminal_boundary_source_miner(
        checkpoint_path=args.checkpoint,
        source_rows_csv=args.source_rows,
        surface_configs=tuple(args.surface_config),
        max_scenarios=args.max_scenarios,
        steer_deltas=args.steer_deltas,
        throttle_deltas=args.throttle_deltas,
        brake_deltas=args.brake_deltas,
        max_boundary_margin=args.max_boundary_margin,
        terminal_cliff_margin=args.terminal_cliff_margin,
        min_margin_sensitivity=args.min_margin_sensitivity,
        min_risk_sensitivity=args.min_risk_sensitivity,
        min_history_margin_gap=args.min_history_margin_gap,
        min_history_risk_gap=args.min_history_risk_gap,
        max_continuation_steps=args.max_continuation_steps,
        heldout_fraction=args.heldout_fraction,
        min_accepted_rows=args.min_accepted_rows,
        min_trajectory_rows=args.min_trajectory_rows,
        min_history_rows=args.min_history_rows,
        min_unique_seeds=args.min_unique_seeds,
        min_unique_sources=args.min_unique_sources,
        max_seed_dominance=args.max_seed_dominance,
        max_source_dominance=args.max_source_dominance,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
