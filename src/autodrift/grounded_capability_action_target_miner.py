"""Mine simulator-grounded action targets for capability-action gaps."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.hidden_envelope_multiseed_gate import parse_checkpoint_spec
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.matched_history_outcome_gate import (
    OutcomeSnapshot,
    _snapshot,
    collect_requested_outcome_snapshots,
)
from autodrift.terminal_margin_recovery_anchor import (
    _rollout_first_action_override,
    build_action_candidates,
    parse_float_list,
)
from autodrift.train_ppo import ActorCritic, resolve_device


SUPPORTED_VARIANTS = ("wrong_matched_history", "delayed_history")

ACCEPTED_TARGET_FIELDNAMES = [
    "source_index",
    "selected_source_index",
    "coupling_row_index",
    "surface",
    "target",
    "variant",
    "left_seed",
    "right_seed",
    "left_step",
    "right_step",
    "candidate_id",
    "capability_z_distance",
    "action_distance",
    "coupling_gap",
    "baseline_margin",
    "target_margin",
    "margin_improvement",
    "baseline_risk_score",
    "target_risk_score",
    "risk_improvement",
    "base_steer",
    "base_throttle",
    "base_brake",
    "target_steer",
    "target_throttle",
    "target_brake",
    "variant_base_steer",
    "variant_base_throttle",
    "variant_base_brake",
    "action_l2",
    "acceptance_reason",
    "weight",
]
UNACCEPTED_ROW_FIELDNAMES = [
    "source_index",
    "selected_source_index",
    "coupling_row_index",
    "surface",
    "target",
    "variant",
    "left_seed",
    "right_seed",
    "left_step",
    "right_step",
    "capability_z_distance",
    "action_distance",
    "coupling_gap",
    "baseline_margin",
    "baseline_risk_score",
    "best_candidate_id",
    "best_margin",
    "best_margin_improvement",
    "best_risk_improvement",
    "best_action_l2",
    "best_rejection_reason",
]


@dataclass(frozen=True)
class SurfaceConfig:
    surface: str
    env_config_path: Path


def parse_surface_config(raw: str) -> SurfaceConfig:
    if "=" not in str(raw):
        raise argparse.ArgumentTypeError(f"surface config must be SURFACE=PATH, got {raw!r}")
    surface, path = str(raw).split("=", 1)
    surface = surface.strip()
    if not surface:
        raise argparse.ArgumentTypeError(f"surface config has empty surface: {raw!r}")
    return SurfaceConfig(surface=surface, env_config_path=Path(path.strip()))


def risk_score(result: dict[str, Any]) -> float:
    margin = _finite_float(result.get("min_clearance_margin"), -1.0)
    clipped_margin = float(np.clip(margin, -1.0, 3.0)) if np.isfinite(margin) else -1.0
    return (
        (10.0 if bool(result.get("collision", False)) else 0.0)
        + (6.0 if bool(result.get("off_road", False)) else 0.0)
        + (4.0 if bool(result.get("spin_out", False)) else 0.0)
        - clipped_margin
    )


def _finite_float(value: Any, default: float = float("nan")) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    return parsed if np.isfinite(parsed) else float(default)


def target_candidate_priority(row: pd.Series) -> tuple[int, int, int, float]:
    surface = str(row.get("surface", ""))
    variant = str(row.get("variant", ""))
    target = str(row.get("target", ""))
    surface_rank = 0 if surface == "ood" else 1
    if variant == "wrong_matched_history" and target in {
        "future_lateral_accel_response",
        "future_yaw_response",
    }:
        variant_rank = 0
    elif variant == "wrong_matched_history":
        variant_rank = 1
    elif variant == "delayed_history":
        variant_rank = 2
    else:
        variant_rank = 3
    target_rank = {
        "future_lateral_accel_response": 0,
        "future_yaw_response": 1,
        "future_braking_deceleration": 2,
    }.get(target, 3)
    return (
        surface_rank,
        variant_rank,
        target_rank,
        -_finite_float(row.get("capability_z_distance"), 0.0),
    )


def select_grounding_source_rows(
    rows: pd.DataFrame,
    *,
    include_variants: tuple[str, ...] = SUPPORTED_VARIANTS,
    max_rows_per_surface_variant_target: int = 8,
    max_total_rows: int = 48,
) -> pd.DataFrame:
    required = {
        "candidate_for_grounding",
        "surface",
        "variant",
        "target",
        "capability_z_distance",
        "left_seed",
        "left_step",
        "right_seed",
        "right_step",
    }
    missing = sorted(required.difference(rows.columns))
    if missing:
        raise ValueError("coupling rows missing columns: " + ", ".join(missing))
    frame = rows[
        rows["candidate_for_grounding"].astype(bool)
        & rows["variant"].astype(str).isin(set(include_variants))
    ].copy()
    if frame.empty:
        return frame
    frame = frame.reset_index().rename(columns={"index": "coupling_row_index"})
    selected = []
    duplicate_key = ["surface", "variant", "target", "left_seed", "left_step", "right_seed", "right_step"]
    for _, group in frame.groupby(["surface", "variant", "target"], observed=True):
        ordered = group.sort_values(
            ["capability_z_distance", "coupling_gap"],
            ascending=[False, False],
        ).drop_duplicates(subset=duplicate_key, keep="first")
        if max_rows_per_surface_variant_target > 0:
            ordered = ordered.head(int(max_rows_per_surface_variant_target))
        selected.append(ordered)
    result = pd.concat(selected, ignore_index=True)
    priority = result.apply(target_candidate_priority, axis=1)
    result = result.assign(_priority=priority).sort_values("_priority").drop(columns=["_priority"]).reset_index(drop=True)
    if max_total_rows > 0:
        result = result.head(int(max_total_rows)).reset_index(drop=True)
    result.insert(0, "selected_source_index", np.arange(len(result), dtype=np.int64))
    return result


def _source_index_for_row(row: pd.Series, fallback: int) -> int:
    if "selected_source_index" in row.index:
        return int(row["selected_source_index"])
    return int(fallback)


def request_steps_for_target_rows(rows: pd.DataFrame, *, delay_steps: int) -> dict[int, set[int]]:
    requests: dict[int, set[int]] = {}
    for _, row in rows.iterrows():
        left_seed = int(row["left_seed"])
        left_step = int(row["left_step"])
        requests.setdefault(left_seed, set()).add(left_step)
        variant = str(row["variant"])
        if variant == "wrong_matched_history":
            requests.setdefault(int(row["right_seed"]), set()).add(int(row["right_step"]))
        elif variant == "delayed_history":
            requests.setdefault(left_seed, set()).add(max(0, left_step - int(delay_steps)))
    return requests


def variant_hidden_for_row(
    *,
    row: pd.Series,
    snapshots: dict[tuple[int, int], OutcomeSnapshot],
    delay_steps: int,
) -> torch.Tensor:
    variant = str(row["variant"])
    if variant == "wrong_matched_history":
        return _snapshot(snapshots, int(row["right_seed"]), int(row["right_step"])).hidden
    if variant == "delayed_history":
        return _snapshot(
            snapshots,
            int(row["left_seed"]),
            max(0, int(row["left_step"]) - int(delay_steps)),
        ).hidden
    raise ValueError(f"unsupported target-mining variant: {variant}")


def candidate_acceptance(
    *,
    candidate: dict[str, Any],
    baseline: dict[str, Any],
    action_l2: float,
    min_margin_improvement: float,
    min_risk_improvement: float,
    max_action_l2: float,
) -> tuple[bool, str]:
    if float(action_l2) > float(max_action_l2):
        return False, "outside_action_trust_region"
    if bool(candidate.get("collision", False)):
        return False, "candidate_collision"
    if bool(candidate.get("off_road", False)):
        return False, "candidate_off_road"
    if bool(candidate.get("spin_out", False)):
        return False, "candidate_spin_out"
    baseline_margin = _finite_float(baseline.get("min_clearance_margin"))
    candidate_margin = _finite_float(candidate.get("min_clearance_margin"))
    margin_improvement = (
        candidate_margin - baseline_margin
        if np.isfinite(candidate_margin) and np.isfinite(baseline_margin)
        else float("nan")
    )
    baseline_risk = risk_score(baseline)
    candidate_risk = risk_score(candidate)
    risk_improvement = baseline_risk - candidate_risk
    if bool(baseline.get("collision", False)) and not bool(candidate.get("collision", False)):
        return True, "baseline_collision_avoided"
    if np.isfinite(margin_improvement) and margin_improvement >= float(min_margin_improvement):
        return True, "margin_improved"
    if np.isfinite(risk_improvement) and risk_improvement >= float(min_risk_improvement):
        return True, "risk_improved"
    return False, "insufficient_margin_or_risk_improvement"


def select_best_candidate(candidate_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    accepted = [row for row in candidate_rows if bool(row.get("accepted", False))]
    if not accepted:
        return None
    return max(
        accepted,
        key=lambda row: (
            bool(row.get("baseline_collision", False)) and not bool(row.get("candidate_collision", False)),
            _finite_float(row.get("margin_improvement"), float("-inf")),
            _finite_float(row.get("risk_improvement"), float("-inf")),
            -_finite_float(row.get("action_l2"), float("inf")),
        ),
    )


def source_diversity_weights(rows: list[dict[str, Any]]) -> dict[int, float]:
    if not rows:
        return {}
    frame = pd.DataFrame(rows)
    counts = frame.groupby(["left_seed", "variant", "target"], observed=True).size().to_dict()
    weights: dict[int, float] = {}
    for row in rows:
        key = (int(row["left_seed"]), str(row["variant"]), str(row["target"]))
        count = int(counts.get(key, 1))
        weights[int(row["source_index"])] = float(1.0 / np.sqrt(max(count, 1)))
    return weights


def _hidden_array(hidden: torch.Tensor) -> np.ndarray:
    return hidden.detach().cpu().numpy().reshape(-1).astype(np.float32)


def write_target_corpus(
    *,
    output_npz: Path,
    observations: list[np.ndarray],
    normal_hidden: list[np.ndarray],
    variant_hidden: list[np.ndarray],
    target_actions: list[np.ndarray],
    normal_base_actions: list[np.ndarray],
    variant_base_actions: list[np.ndarray],
    weights: list[float],
    row_ids: list[int],
    source_indices: list[int],
) -> None:
    if not observations:
        raise ValueError("cannot write empty target corpus")
    np.savez_compressed(
        output_npz,
        observation=np.asarray(observations, dtype=np.float32),
        normal_hidden=np.asarray(normal_hidden, dtype=np.float32),
        variant_hidden=np.asarray(variant_hidden, dtype=np.float32),
        target_action=np.asarray(target_actions, dtype=np.float32),
        normal_base_action=np.asarray(normal_base_actions, dtype=np.float32),
        variant_base_action=np.asarray(variant_base_actions, dtype=np.float32),
        weight=np.asarray(weights, dtype=np.float32),
        row_id=np.asarray(row_ids, dtype=np.int64),
        source_index=np.asarray(source_indices, dtype=np.int64),
    )


def mine_targets_for_surface(
    *,
    model: ActorCritic,
    env_config_path: Path,
    rows: pd.DataFrame,
    delay_steps: int,
    steer_deltas: tuple[float, ...],
    throttle_deltas: tuple[float, ...],
    brake_deltas: tuple[float, ...],
    min_margin_improvement: float,
    min_risk_improvement: float,
    max_action_l2: float,
    max_continuation_steps: int,
    device: torch.device,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, list[np.ndarray]]]:
    env_config = load_env_config(env_config_path)
    snapshots = collect_requested_outcome_snapshots(
        model=model,
        env_config=env_config,
        requests=request_steps_for_target_rows(rows, delay_steps=delay_steps),
        device=device,
    )
    candidate_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    unaccepted_rows: list[dict[str, Any]] = []
    corpus: dict[str, list[np.ndarray]] = {
        "observations": [],
        "normal_hidden": [],
        "variant_hidden": [],
        "target_actions": [],
        "normal_base_actions": [],
        "variant_base_actions": [],
    }
    source_weight: dict[int, float] = {}

    for source_index, row in rows.reset_index(drop=True).iterrows():
        global_source_index = _source_index_for_row(row, int(source_index))
        left = _snapshot(snapshots, int(row["left_seed"]), int(row["left_step"]))
        normal_hidden = left.hidden.detach().clone()
        variant_hidden = variant_hidden_for_row(row=row, snapshots=snapshots, delay_steps=delay_steps).detach().clone()
        base_action, _ = deterministic_action_from_hidden(model, left.observation, normal_hidden, device)
        variant_base_action, _ = deterministic_action_from_hidden(model, left.observation, variant_hidden, device)
        baseline = _rollout_first_action_override(
            model=model,
            snapshot=left,
            first_action=base_action,
            max_continuation_steps=max_continuation_steps,
            device=device,
        )
        baseline_risk = risk_score(baseline)
        row_candidate_rows: list[dict[str, Any]] = []
        for candidate in build_action_candidates(
            base_action,
            steer_deltas=steer_deltas,
            throttle_deltas=throttle_deltas,
            brake_deltas=brake_deltas,
        ):
            result = _rollout_first_action_override(
                model=model,
                snapshot=left,
                first_action=candidate.action,
                max_continuation_steps=max_continuation_steps,
                device=device,
            )
            candidate_risk = risk_score(result)
            baseline_margin = _finite_float(baseline.get("min_clearance_margin"))
            candidate_margin = _finite_float(result.get("min_clearance_margin"))
            margin_improvement = (
                candidate_margin - baseline_margin
                if np.isfinite(candidate_margin) and np.isfinite(baseline_margin)
                else float("nan")
            )
            accepted, rejection_reason = candidate_acceptance(
                candidate=result,
                baseline=baseline,
                action_l2=candidate.action_l2,
                min_margin_improvement=min_margin_improvement,
                min_risk_improvement=min_risk_improvement,
                max_action_l2=max_action_l2,
            )
            candidate_row = {
                "source_index": int(global_source_index),
                "coupling_row_index": int(row["coupling_row_index"]) if "coupling_row_index" in row.index else int(source_index),
                "candidate_id": int(candidate.candidate_id),
                "surface": str(row["surface"]),
                "target": str(row["target"]),
                "variant": str(row["variant"]),
                "left_seed": int(row["left_seed"]),
                "right_seed": int(row["right_seed"]),
                "left_step": int(row["left_step"]),
                "right_step": int(row["right_step"]),
                "capability_z_distance": float(row["capability_z_distance"]),
                "action_distance": float(row["action_distance"]),
                "coupling_gap": float(row["coupling_gap"]),
                "baseline_success": bool(baseline.get("success", False)),
                "baseline_collision": bool(baseline.get("collision", False)),
                "baseline_terminal_reason": str(baseline.get("terminal_reason", "")),
                "baseline_margin": baseline_margin,
                "baseline_risk_score": baseline_risk,
                "candidate_success": bool(result.get("success", False)),
                "candidate_collision": bool(result.get("collision", False)),
                "candidate_off_road": bool(result.get("off_road", False)),
                "candidate_spin_out": bool(result.get("spin_out", False)),
                "candidate_terminal_reason": str(result.get("terminal_reason", "")),
                "candidate_margin": candidate_margin,
                "candidate_risk_score": candidate_risk,
                "margin_improvement": margin_improvement,
                "risk_improvement": baseline_risk - candidate_risk,
                "base_steer": float(base_action[0]),
                "base_throttle": float(base_action[1]),
                "base_brake": float(base_action[2]),
                "variant_base_steer": float(variant_base_action[0]),
                "variant_base_throttle": float(variant_base_action[1]),
                "variant_base_brake": float(variant_base_action[2]),
                "candidate_steer": float(candidate.action[0]),
                "candidate_throttle": float(candidate.action[1]),
                "candidate_brake": float(candidate.action[2]),
                "steer_delta": float(candidate.steer_delta),
                "throttle_delta": float(candidate.throttle_delta),
                "brake_delta": float(candidate.brake_delta),
                "action_l2": float(candidate.action_l2),
                "accepted": bool(accepted),
                "rejection_reason": rejection_reason,
            }
            candidate_rows.append(candidate_row)
            row_candidate_rows.append(candidate_row)

        best = select_best_candidate(row_candidate_rows)
        if best is None:
            best_any = max(
                row_candidate_rows,
                key=lambda item: (
                    _finite_float(item.get("margin_improvement"), float("-inf")),
                    _finite_float(item.get("risk_improvement"), float("-inf")),
                    -_finite_float(item.get("action_l2"), float("inf")),
                ),
            )
            unaccepted_rows.append(
                {
                    "source_index": int(global_source_index),
                    "selected_source_index": int(global_source_index),
                    "coupling_row_index": int(row["coupling_row_index"]) if "coupling_row_index" in row.index else int(source_index),
                    "surface": str(row["surface"]),
                    "target": str(row["target"]),
                    "variant": str(row["variant"]),
                    "left_seed": int(row["left_seed"]),
                    "right_seed": int(row["right_seed"]),
                    "left_step": int(row["left_step"]),
                    "right_step": int(row["right_step"]),
                    "capability_z_distance": float(row["capability_z_distance"]),
                    "action_distance": float(row["action_distance"]),
                    "coupling_gap": float(row["coupling_gap"]),
                    "baseline_margin": float(best_any["baseline_margin"]),
                    "baseline_risk_score": float(best_any["baseline_risk_score"]),
                    "best_candidate_id": int(best_any["candidate_id"]),
                    "best_margin": float(best_any["candidate_margin"]),
                    "best_margin_improvement": float(best_any["margin_improvement"]),
                    "best_risk_improvement": float(best_any["risk_improvement"]),
                    "best_action_l2": float(best_any["action_l2"]),
                    "best_rejection_reason": str(best_any["rejection_reason"]),
                }
            )
            continue

        target_action = np.asarray(
            [best["candidate_steer"], best["candidate_throttle"], best["candidate_brake"]],
            dtype=np.float32,
        )
        accepted_rows.append(
            {
                "source_index": int(global_source_index),
                "selected_source_index": int(global_source_index),
                "coupling_row_index": int(row["coupling_row_index"]) if "coupling_row_index" in row.index else int(source_index),
                "surface": str(row["surface"]),
                "target": str(row["target"]),
                "variant": str(row["variant"]),
                "left_seed": int(row["left_seed"]),
                "right_seed": int(row["right_seed"]),
                "left_step": int(row["left_step"]),
                "right_step": int(row["right_step"]),
                "candidate_id": int(best["candidate_id"]),
                "capability_z_distance": float(row["capability_z_distance"]),
                "action_distance": float(row["action_distance"]),
                "coupling_gap": float(row["coupling_gap"]),
                "baseline_margin": float(best["baseline_margin"]),
                "target_margin": float(best["candidate_margin"]),
                "margin_improvement": float(best["margin_improvement"]),
                "baseline_risk_score": float(best["baseline_risk_score"]),
                "target_risk_score": float(best["candidate_risk_score"]),
                "risk_improvement": float(best["risk_improvement"]),
                "base_steer": float(best["base_steer"]),
                "base_throttle": float(best["base_throttle"]),
                "base_brake": float(best["base_brake"]),
                "target_steer": float(best["candidate_steer"]),
                "target_throttle": float(best["candidate_throttle"]),
                "target_brake": float(best["candidate_brake"]),
                "variant_base_steer": float(best["variant_base_steer"]),
                "variant_base_throttle": float(best["variant_base_throttle"]),
                "variant_base_brake": float(best["variant_base_brake"]),
                "action_l2": float(best["action_l2"]),
                "acceptance_reason": str(best["rejection_reason"]),
            }
        )
        corpus["observations"].append(np.asarray(left.observation, dtype=np.float32).copy())
        corpus["normal_hidden"].append(_hidden_array(normal_hidden))
        corpus["variant_hidden"].append(_hidden_array(variant_hidden))
        corpus["target_actions"].append(target_action)
        corpus["normal_base_actions"].append(np.asarray(base_action, dtype=np.float32).copy())
        corpus["variant_base_actions"].append(np.asarray(variant_base_action, dtype=np.float32).copy())

    source_weight = source_diversity_weights(accepted_rows)
    for accepted_row in accepted_rows:
        accepted_row["weight"] = float(
            source_weight.get(int(accepted_row["source_index"]), 1.0)
            * min(4.0, max(1.0, _finite_float(accepted_row["margin_improvement"], 0.0) / max(min_margin_improvement, 1e-9)))
        )
    return candidate_rows, accepted_rows, unaccepted_rows, corpus


def run_grounded_capability_action_target_miner(
    *,
    checkpoint_path: Path,
    coupling_rows_csv: Path,
    surface_configs: tuple[SurfaceConfig, ...],
    include_variants: tuple[str, ...],
    max_rows_per_surface_variant_target: int,
    max_total_rows: int,
    delay_steps: int,
    steer_deltas: tuple[float, ...],
    throttle_deltas: tuple[float, ...],
    brake_deltas: tuple[float, ...],
    min_margin_improvement: float,
    min_risk_improvement: float,
    max_action_l2: float,
    max_continuation_steps: int,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    coupling_rows = pd.read_csv(coupling_rows_csv)
    selected = select_grounding_source_rows(
        coupling_rows,
        include_variants=include_variants,
        max_rows_per_surface_variant_target=max_rows_per_surface_variant_target,
        max_total_rows=max_total_rows,
    )
    surface_config_by_name = {item.surface: item.env_config_path for item in surface_configs}
    missing_configs = sorted(set(selected["surface"].astype(str)).difference(surface_config_by_name)) if not selected.empty else []
    if missing_configs:
        raise ValueError(f"missing env configs for surfaces: {missing_configs}")

    candidate_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    unaccepted_rows: list[dict[str, Any]] = []
    corpus: dict[str, list[np.ndarray]] = {
        "observations": [],
        "normal_hidden": [],
        "variant_hidden": [],
        "target_actions": [],
        "normal_base_actions": [],
        "variant_base_actions": [],
    }
    for surface, surface_rows in selected.groupby("surface", observed=True):
        surface_candidate_rows, surface_accepted_rows, surface_unaccepted_rows, surface_corpus = mine_targets_for_surface(
            model=model,
            env_config_path=surface_config_by_name[str(surface)],
            rows=surface_rows.reset_index(drop=True),
            delay_steps=delay_steps,
            steer_deltas=steer_deltas,
            throttle_deltas=throttle_deltas,
            brake_deltas=brake_deltas,
            min_margin_improvement=min_margin_improvement,
            min_risk_improvement=min_risk_improvement,
            max_action_l2=max_action_l2,
            max_continuation_steps=max_continuation_steps,
            device=resolved_device,
        )
        candidate_rows.extend(surface_candidate_rows)
        accepted_rows.extend(surface_accepted_rows)
        unaccepted_rows.extend(surface_unaccepted_rows)
        for key, values in surface_corpus.items():
            corpus[key].extend(values)

    target_corpus_path: Path | None = None
    if accepted_rows:
        target_corpus_path = run_dir / "target_corpus.npz"
        write_target_corpus(
            output_npz=target_corpus_path,
            observations=corpus["observations"],
            normal_hidden=corpus["normal_hidden"],
            variant_hidden=corpus["variant_hidden"],
            target_actions=corpus["target_actions"],
            normal_base_actions=corpus["normal_base_actions"],
            variant_base_actions=corpus["variant_base_actions"],
            weights=[float(row["weight"]) for row in accepted_rows],
            row_ids=list(range(len(accepted_rows))),
            source_indices=[int(row["source_index"]) for row in accepted_rows],
        )

    write_csv_rows(run_dir / "selected_source_rows.csv", selected.to_dict(orient="records"))
    write_csv_rows(run_dir / "target_candidates.csv", candidate_rows)
    write_csv_rows(run_dir / "accepted_targets.csv", accepted_rows, fieldnames=ACCEPTED_TARGET_FIELDNAMES)
    write_csv_rows(run_dir / "unaccepted_rows.csv", unaccepted_rows, fieldnames=UNACCEPTED_ROW_FIELDNAMES)
    accepted_frame = pd.DataFrame(accepted_rows)
    candidate_frame = pd.DataFrame(candidate_rows)
    unaccepted_frame = pd.DataFrame(unaccepted_rows)
    margin_improvements = (
        accepted_frame["margin_improvement"].astype(float)
        if not accepted_frame.empty
        else pd.Series(dtype=float)
    )
    all_margin_improvements = (
        candidate_frame["margin_improvement"].astype(float)
        if not candidate_frame.empty
        else pd.Series(dtype=float)
    )
    all_risk_improvements = (
        candidate_frame["risk_improvement"].astype(float)
        if not candidate_frame.empty
        else pd.Series(dtype=float)
    )
    small_trust_frame = (
        candidate_frame[candidate_frame["action_l2"].astype(float) <= float(max_action_l2)]
        if not candidate_frame.empty
        else candidate_frame
    )
    summary = {
        "run_type": "grounded_capability_action_target_miner",
        "checkpoint": checkpoint_path,
        "coupling_rows_csv": coupling_rows_csv,
        "surface_configs": {item.surface: item.env_config_path for item in surface_configs},
        "include_variants": include_variants,
        "max_rows_per_surface_variant_target": int(max_rows_per_surface_variant_target),
        "max_total_rows": int(max_total_rows),
        "delay_steps": int(delay_steps),
        "steer_deltas": steer_deltas,
        "throttle_deltas": throttle_deltas,
        "brake_deltas": brake_deltas,
        "min_margin_improvement": float(min_margin_improvement),
        "min_risk_improvement": float(min_risk_improvement),
        "max_action_l2": float(max_action_l2),
        "max_continuation_steps": int(max_continuation_steps),
        "device": str(resolved_device),
        "source_candidate_rows": int(len(coupling_rows)),
        "selected_source_rows": int(len(selected)),
        "candidate_rollouts": int(len(candidate_rows)),
        "accepted_targets": int(len(accepted_rows)),
        "unaccepted_rows": int(len(unaccepted_rows)),
        "accepted_left_seed_count": int(accepted_frame["left_seed"].nunique()) if not accepted_frame.empty else 0,
        "accepted_variant_count": int(accepted_frame["variant"].nunique()) if not accepted_frame.empty else 0,
        "accepted_margin_improvement_mean": float(margin_improvements.mean()) if len(margin_improvements) else float("nan"),
        "accepted_margin_improvement_min": float(margin_improvements.min()) if len(margin_improvements) else float("nan"),
        "accepted_margin_improvement_max": float(margin_improvements.max()) if len(margin_improvements) else float("nan"),
        "candidate_margin_improvement_max": float(all_margin_improvements.max()) if len(all_margin_improvements) else float("nan"),
        "candidate_margin_improvement_mean": float(all_margin_improvements.mean()) if len(all_margin_improvements) else float("nan"),
        "candidate_risk_improvement_max": float(all_risk_improvements.max()) if len(all_risk_improvements) else float("nan"),
        "candidate_risk_improvement_mean": float(all_risk_improvements.mean()) if len(all_risk_improvements) else float("nan"),
        "trust_region_candidate_rollouts": int(len(small_trust_frame)),
        "trust_region_margin_improvement_max": (
            float(small_trust_frame["margin_improvement"].astype(float).max())
            if len(small_trust_frame)
            else float("nan")
        ),
        "trust_region_risk_improvement_max": (
            float(small_trust_frame["risk_improvement"].astype(float).max())
            if len(small_trust_frame)
            else float("nan")
        ),
        "best_unaccepted_margin_improvement": (
            float(unaccepted_frame["best_margin_improvement"].astype(float).max())
            if not unaccepted_frame.empty
            else float("nan")
        ),
        "best_unaccepted_risk_improvement": (
            float(unaccepted_frame["best_risk_improvement"].astype(float).max())
            if not unaccepted_frame.empty
            else float("nan")
        ),
        "candidate_rejection_counts": (
            candidate_frame["rejection_reason"].value_counts().to_dict()
            if not candidate_frame.empty
            else {}
        ),
        "selected_source_counts": (
            selected.groupby(["surface", "variant", "target"], observed=True)
            .size()
            .rename("count")
            .reset_index()
            .to_dict(orient="records")
            if not selected.empty
            else []
        ),
        "target_corpus_npz": target_corpus_path,
        "target_candidates_csv": run_dir / "target_candidates.csv",
        "accepted_targets_csv": run_dir / "accepted_targets.csv",
        "unaccepted_rows_csv": run_dir / "unaccepted_rows.csv",
        "selected_source_rows_csv": run_dir / "selected_source_rows.csv",
        "labels_enter_actor_input": False,
        "actor_parameters_changed": False,
        "ppo_used": False,
        "promoted": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine grounded action targets from capability-action gaps.")
    parser.add_argument("--checkpoint-policy", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--coupling-rows", type=Path, required=True)
    parser.add_argument("--surface-config", type=parse_surface_config, action="append", required=True)
    parser.add_argument("--include-variant", type=str, action="append", default=None)
    parser.add_argument("--max-rows-per-surface-variant-target", type=int, default=8)
    parser.add_argument("--max-total-rows", type=int, default=48)
    parser.add_argument("--delay-steps", type=int, default=2)
    parser.add_argument("--steer-deltas", type=parse_float_list, default=(-0.08, -0.04, -0.02, 0.0, 0.02, 0.04, 0.08))
    parser.add_argument("--throttle-deltas", type=parse_float_list, default=(-0.06, -0.03, 0.0, 0.03))
    parser.add_argument("--brake-deltas", type=parse_float_list, default=(-0.08, -0.04, -0.02, 0.0, 0.02, 0.04, 0.08))
    parser.add_argument("--min-margin-improvement", type=float, default=0.02)
    parser.add_argument("--min-risk-improvement", type=float, default=0.05)
    parser.add_argument("--max-action-l2", type=float, default=0.10)
    parser.add_argument("--max-continuation-steps", type=int, default=40)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="grounded_capability_action_target_miner")
    summary = run_grounded_capability_action_target_miner(
        checkpoint_path=args.checkpoint_policy.path,
        coupling_rows_csv=args.coupling_rows,
        surface_configs=tuple(args.surface_config),
        include_variants=tuple(args.include_variant or SUPPORTED_VARIANTS),
        max_rows_per_surface_variant_target=args.max_rows_per_surface_variant_target,
        max_total_rows=args.max_total_rows,
        delay_steps=args.delay_steps,
        steer_deltas=args.steer_deltas,
        throttle_deltas=args.throttle_deltas,
        brake_deltas=args.brake_deltas,
        min_margin_improvement=args.min_margin_improvement,
        min_risk_improvement=args.min_risk_improvement,
        max_action_l2=args.max_action_l2,
        max_continuation_steps=args.max_continuation_steps,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
