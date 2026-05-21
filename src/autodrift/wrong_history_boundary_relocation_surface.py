"""Boundary-tightened wrong-history outcome surface for matched pairs."""

from __future__ import annotations

import argparse
import copy
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import load_env_config
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec, parse_checkpoint_spec
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.matched_history_intervention_gate import ACTION_VARIANTS, requested_snapshot_steps
from autodrift.matched_history_outcome_gate import (
    OUTCOME_VARIANTS,
    OutcomeSnapshot,
    collect_requested_outcome_snapshots,
    replay_outcome_variant,
)
from autodrift.scenarios import classify_obstacle_scenario
from autodrift.train_ppo import resolve_device


DEFAULT_REPORT_VARIANTS = (
    "wrong_matched_history",
    "reset_hidden",
    "zero_current_response",
    "zero_action_history",
    "delayed_history",
)
DEFAULT_TARGET_NORMAL_MARGINS = (0.005, 0.01, 0.02, 0.05, 0.10, 0.15)


def parse_float_list(raw: str) -> tuple[float, ...]:
    values = tuple(float(part.strip()) for part in raw.split(",") if part.strip())
    if not values:
        raise argparse.ArgumentTypeError("list must contain at least one value")
    return values


def parse_variants(raw: str) -> tuple[str, ...]:
    variants = tuple(part.strip() for part in raw.split(",") if part.strip())
    if not variants:
        raise argparse.ArgumentTypeError("at least one variant is required")
    unknown = sorted(set(variants).difference(ACTION_VARIANTS))
    if unknown:
        raise argparse.ArgumentTypeError(f"unknown variants: {unknown}")
    return variants


def obstacle_body_geometry(snapshot: OutcomeSnapshot) -> tuple[float, float, float]:
    env = snapshot.env
    if env.obstacle_scenario is None or env.obstacle_position is None:
        raise ValueError("snapshot has no obstacle geometry")
    body = env._body_point(env.obstacle_position)
    return (
        float(body[0]),
        float(body[1]),
        float(env.obstacle_scenario.obstacle_half_width),
    )


def _body_to_world(env: AutoDriftEnv, body_x: float, body_y: float) -> np.ndarray:
    cos_psi = math.cos(env.state.psi)
    sin_psi = math.sin(env.state.psi)
    return np.array(
        [
            env.state.x + cos_psi * float(body_x) - sin_psi * float(body_y),
            env.state.y + sin_psi * float(body_x) + cos_psi * float(body_y),
        ],
        dtype=np.float64,
    )


def relocate_outcome_snapshot(
    snapshot: OutcomeSnapshot,
    *,
    body_longitudinal: float,
    body_lateral: float,
    half_width: float,
) -> OutcomeSnapshot:
    if body_longitudinal <= 0.0:
        raise ValueError("body_longitudinal must be positive")
    if half_width <= 0.0:
        raise ValueError("half_width must be positive")
    env = copy.deepcopy(snapshot.env)
    if env.obstacle_scenario is None:
        raise ValueError("cannot relocate a snapshot without an obstacle scenario")

    speed = max(math.hypot(env.state.vx, env.state.vy), 1e-6)
    env.obstacle_scenario = classify_obstacle_scenario(
        speed=speed,
        mu=env.params.mu,
        obstacle_distance=float(body_longitudinal),
        obstacle_half_width=float(half_width),
        config=env.config.obstacle.scenario_config(speed=speed, mu=env.params.mu),
    )
    env.obstacle_position = _body_to_world(env, body_longitudinal, body_lateral)
    env.min_obstacle_clearance = float("inf")
    env.collision = False
    env.obstacle_completed = False
    frame = env.track.frame(env.state.x, env.state.y, env.state.psi)
    env._update_obstacle_status(frame)

    relocated_base = env._base_observation()
    if env.obs_history:
        env.obs_history[0] = relocated_base.copy()
    else:
        env.obs_history = [relocated_base.copy() for _ in range(env.config.history_length)]
    relocated_observation = np.asarray(env._observation(), dtype=np.float32).copy()
    relocated_info = env._info(frame)
    relocated_info.update(
        {
            "snapshot_relocated": True,
            "source_obstacle_distance": snapshot.info.get("obstacle_distance", float("nan")),
            "source_obstacle_lateral_offset": snapshot.info.get("obstacle_lateral_offset", float("nan")),
            "relocated_obstacle_body_x": float(body_longitudinal),
            "relocated_obstacle_body_y": float(body_lateral),
            "relocated_obstacle_half_width": float(half_width),
        }
    )
    return OutcomeSnapshot(
        seed=snapshot.seed,
        step=snapshot.step,
        observation=relocated_observation,
        hidden=snapshot.hidden.detach().clone(),
        env=env,
        info=relocated_info,
    )


def candidate_half_widths(
    *,
    base_half_width: float,
    original_normal_margin: float,
    target_normal_margins: tuple[float, ...],
    half_width_inflations: tuple[float, ...],
    min_half_width: float,
    max_half_width: float,
) -> list[float]:
    candidates: list[float] = []
    for inflation in half_width_inflations:
        candidates.append(float(base_half_width) + float(inflation))
    if np.isfinite(float(original_normal_margin)):
        for target_margin in target_normal_margins:
            inflation = max(0.0, float(original_normal_margin) - float(target_margin))
            candidates.append(float(base_half_width) + inflation)
    cleaned: list[float] = []
    seen: set[float] = set()
    for value in candidates:
        if not np.isfinite(value):
            continue
        if value < float(min_half_width) or value > float(max_half_width):
            continue
        rounded = round(float(value), 6)
        if rounded in seen:
            continue
        seen.add(rounded)
        cleaned.append(float(value))
    return sorted(cleaned)


def select_wrong_history_candidates(
    outcome_frame: pd.DataFrame,
    *,
    max_pairs_per_checkpoint_target: int,
    min_base_action_distance: float,
    min_base_margin_gap: float | None,
) -> pd.DataFrame:
    required = {
        "variant",
        "checkpoint_label",
        "target",
        "left_seed",
        "right_seed",
        "left_step",
        "right_step",
        "normal_margin",
        "margin_gap",
        "first_action_distance",
    }
    missing = required.difference(outcome_frame.columns)
    if missing:
        raise ValueError(f"outcome CSV is missing columns: {sorted(missing)}")
    frame = outcome_frame[outcome_frame["variant"].astype(str) == "wrong_matched_history"].copy()
    frame = frame[np.isfinite(frame["normal_margin"].astype(float))]
    frame = frame[np.isfinite(frame["margin_gap"].astype(float))]
    frame = frame[np.isfinite(frame["first_action_distance"].astype(float))]
    frame = frame[frame["first_action_distance"].astype(float) >= float(min_base_action_distance)]
    if min_base_margin_gap is not None:
        frame = frame[frame["margin_gap"].astype(float) >= float(min_base_margin_gap)]
    if max_pairs_per_checkpoint_target <= 0:
        return frame.reset_index(drop=True)
    selected = []
    for _, group in frame.groupby(["checkpoint_label", "target"], observed=True):
        selected.append(
            group.sort_values(["margin_gap", "first_action_distance"], ascending=[False, False]).head(
                int(max_pairs_per_checkpoint_target)
            )
        )
    if not selected:
        return frame.head(0).copy()
    return pd.concat(selected, ignore_index=True)


def _make_requests(candidate_rows: pd.DataFrame, delay_steps: int) -> dict[int, set[int]]:
    return requested_snapshot_steps(candidate_rows, delay_steps=delay_steps)


def _result_fields(prefix: str, result: dict[str, Any]) -> dict[str, Any]:
    return {
        f"{prefix}_success": bool(result.get("success", False)),
        f"{prefix}_collision": bool(result.get("collision", False)),
        f"{prefix}_obstacle_completed": bool(result.get("obstacle_completed", False)),
        f"{prefix}_terminal_reason": str(result.get("terminal_reason", "")),
        f"{prefix}_return": float(result.get("return", float("nan"))),
        f"{prefix}_steps": int(result.get("steps", 0)),
        f"{prefix}_margin": float(result.get("min_clearance_margin", float("nan"))),
        f"{prefix}_first_steer": float(result.get("first_steer", float("nan"))),
        f"{prefix}_first_throttle": float(result.get("first_throttle", float("nan"))),
        f"{prefix}_first_brake": float(result.get("first_brake", float("nan"))),
        f"{prefix}_first_action_distance": float(result.get("first_action_distance", float("nan"))),
        f"{prefix}_trajectory_distance_mean": float(result.get("action_trajectory_distance_mean", float("nan"))),
    }


def build_boundary_relocation_rows(
    *,
    candidate_rows: pd.DataFrame,
    snapshots: dict[tuple[int, int], OutcomeSnapshot],
    model: Any,
    env_config: DriftEnvConfig,
    response_dim: int,
    delay_steps: int,
    max_continuation_steps: int,
    target_normal_margins: tuple[float, ...],
    half_width_inflations: tuple[float, ...],
    body_longitudinals: tuple[float, ...] | None,
    body_laterals: tuple[float, ...] | None,
    min_half_width: float,
    max_half_width: float,
    min_normal_margin: float,
    max_normal_margin: float,
    min_margin_gap: float,
    report_variants: tuple[str, ...],
    device: Any,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate_id, candidate in candidate_rows.reset_index(drop=True).iterrows():
        left_key = (int(candidate["left_seed"]), int(candidate["left_step"]))
        right_key = (int(candidate["right_seed"]), int(candidate["right_step"]))
        delayed_key = (
            int(candidate["left_seed"]),
            max(0, int(candidate["left_step"]) - int(delay_steps)),
        )
        if left_key not in snapshots or right_key not in snapshots or delayed_key not in snapshots:
            raise ValueError(f"missing snapshots for candidate row {candidate_id}")
        left = snapshots[left_key]
        right = snapshots[right_key]
        delayed = snapshots[delayed_key]
        source_body_x, source_body_y, source_half_width = obstacle_body_geometry(left)
        if body_longitudinals is None and source_body_x <= 0.0:
            continue
        geometry_body_x = tuple(body_longitudinals) if body_longitudinals is not None else (source_body_x,)
        geometry_body_y = tuple(body_laterals) if body_laterals is not None else (source_body_y,)
        widths = candidate_half_widths(
            base_half_width=source_half_width,
            original_normal_margin=float(candidate["normal_margin"]),
            target_normal_margins=target_normal_margins,
            half_width_inflations=half_width_inflations,
            min_half_width=min_half_width,
            max_half_width=max_half_width,
        )
        for body_x in geometry_body_x:
            for body_y in geometry_body_y:
                for half_width in widths:
                    relocated = relocate_outcome_snapshot(
                        left,
                        body_longitudinal=float(body_x),
                        body_lateral=float(body_y),
                        half_width=float(half_width),
                    )
                    normal, normal_actions = replay_outcome_variant(
                        model=model,
                        snapshot=relocated,
                        env_config=env_config,
                        variant="normal",
                        response_dim=response_dim,
                        variant_hidden=None,
                        normal_first_action=None,
                        normal_actions=None,
                        max_continuation_steps=max_continuation_steps,
                        device=device,
                    )
                    normal_first_action = np.asarray(
                        [normal["first_steer"], normal["first_throttle"], normal["first_brake"]],
                        dtype=np.float32,
                    )
                    variant_hidden = {
                        "wrong_matched_history": right.hidden,
                        "delayed_history": delayed.hidden,
                    }
                    for variant in report_variants:
                        if variant not in OUTCOME_VARIANTS:
                            raise ValueError(f"unknown variant: {variant}")
                        result, _ = replay_outcome_variant(
                            model=model,
                            snapshot=relocated,
                            env_config=env_config,
                            variant=variant,
                            response_dim=response_dim,
                            variant_hidden=variant_hidden.get(variant),
                            normal_first_action=normal_first_action,
                            normal_actions=normal_actions,
                            max_continuation_steps=max_continuation_steps,
                            device=device,
                        )
                        normal_margin = float(normal.get("min_clearance_margin", float("nan")))
                        variant_margin = float(result.get("min_clearance_margin", float("nan")))
                        margin_gap = (
                            normal_margin - variant_margin
                            if np.isfinite(normal_margin) and np.isfinite(variant_margin)
                            else float("nan")
                        )
                        normal_success = bool(normal.get("success", False))
                        variant_success = bool(result.get("success", False))
                        success_drop = bool(normal_success and not variant_success)
                        normal_near_boundary = bool(
                            normal_success
                            and np.isfinite(normal_margin)
                            and normal_margin >= float(min_normal_margin)
                            and normal_margin <= float(max_normal_margin)
                        )
                        margin_accept = bool(np.isfinite(margin_gap) and margin_gap >= float(min_margin_gap))
                        accepted = bool(normal_near_boundary and (success_drop or margin_accept))
                        rows.append(
                            {
                                "candidate_id": int(candidate_id),
                                "source_pair_id": int(candidate.get("pair_id", candidate_id)),
                                "checkpoint_label": str(candidate.get("checkpoint_label", "")),
                                "probe_seed": int(candidate.get("probe_seed", -1)),
                                "target": str(candidate.get("target", "")),
                                "variant": variant,
                                "left_seed": int(candidate["left_seed"]),
                                "right_seed": int(candidate["right_seed"]),
                                "left_step": int(candidate["left_step"]),
                                "right_step": int(candidate["right_step"]),
                                "target_z_delta": float(candidate.get("target_z_delta", float("nan"))),
                                "visible_distance": float(candidate.get("visible_distance", float("nan"))),
                                "base_normal_margin": float(candidate["normal_margin"]),
                                "base_wrong_margin_gap": float(candidate["margin_gap"]),
                                "base_wrong_first_action_distance": float(candidate["first_action_distance"]),
                                "source_obstacle_body_x": float(source_body_x),
                                "source_obstacle_body_y": float(source_body_y),
                                "source_obstacle_half_width": float(source_half_width),
                                "relocated_obstacle_body_x": float(body_x),
                                "relocated_obstacle_body_y": float(body_y),
                                "relocated_obstacle_half_width": float(half_width),
                                "half_width_inflation": float(half_width - source_half_width),
                                "normal_margin": normal_margin,
                                "variant_margin": variant_margin,
                                "margin_gap": margin_gap,
                                "normal_success": normal_success,
                                "variant_success": variant_success,
                                "success_drop": success_drop,
                                "normal_near_boundary": normal_near_boundary,
                                "accepted": accepted,
                                **_result_fields("normal", normal),
                                **_result_fields("variant", result),
                            }
                        )
    return rows


def summarize_boundary_relocation_rows(
    rows: list[dict[str, Any]],
    *,
    min_accepted_wrong_rows: int,
) -> list[dict[str, Any]]:
    if not rows:
        return [
            {
                "checkpoint_label": "__aggregate__",
                "target": "__all__",
                "variant": "__all__",
                "row_count": 0,
                "accepted_count": 0,
                "surface_found": False,
                "min_accepted_wrong_rows": int(min_accepted_wrong_rows),
            }
        ]
    frame = pd.DataFrame(rows)
    summary_rows: list[dict[str, Any]] = []
    for (checkpoint_label, target, variant), group in frame.groupby(
        ["checkpoint_label", "target", "variant"],
        observed=True,
    ):
        gaps = group["margin_gap"].astype(float)
        finite_gaps = gaps[np.isfinite(gaps)]
        summary_rows.append(
            {
                "checkpoint_label": str(checkpoint_label),
                "target": str(target),
                "variant": str(variant),
                "row_count": int(len(group)),
                "accepted_count": int(group["accepted"].astype(bool).sum()),
                "normal_near_boundary_count": int(group["normal_near_boundary"].astype(bool).sum()),
                "success_drop_count": int(group["success_drop"].astype(bool).sum()),
                "normal_success_rate": float(group["normal_success"].astype(bool).mean()),
                "variant_success_rate": float(group["variant_success"].astype(bool).mean()),
                "normal_margin_mean": float(group["normal_margin"].astype(float).mean()),
                "variant_margin_mean": float(group["variant_margin"].astype(float).mean()),
                "margin_gap_mean": float(finite_gaps.mean()) if len(finite_gaps) else float("nan"),
                "margin_gap_max": float(finite_gaps.max()) if len(finite_gaps) else float("nan"),
                "base_wrong_margin_gap_mean": float(group["base_wrong_margin_gap"].astype(float).mean()),
                "base_wrong_first_action_distance_mean": float(
                    group["base_wrong_first_action_distance"].astype(float).mean()
                ),
            }
        )

    wrong = frame[frame["variant"].astype(str) == "wrong_matched_history"]
    reset = frame[frame["variant"].astype(str) == "reset_hidden"]
    zero_current = frame[frame["variant"].astype(str) == "zero_current_response"]
    accepted_wrong = wrong[wrong["accepted"].astype(bool)]
    aggregate = {
        "checkpoint_label": "__aggregate__",
        "target": "__all__",
        "variant": "__all__",
        "row_count": int(len(frame)),
        "unique_candidates": int(frame["candidate_id"].nunique()),
        "unique_source_pairs": int(frame["source_pair_id"].nunique()),
        "accepted_count": int(frame["accepted"].astype(bool).sum()),
        "accepted_wrong_history_rows": int(len(accepted_wrong)),
        "accepted_wrong_history_pairs": int(accepted_wrong["source_pair_id"].nunique()) if len(accepted_wrong) else 0,
        "accepted_reset_rows": int(reset["accepted"].astype(bool).sum()) if len(reset) else 0,
        "accepted_zero_current_rows": int(zero_current["accepted"].astype(bool).sum()) if len(zero_current) else 0,
        "wrong_history_success_drop_count": int(wrong["success_drop"].astype(bool).sum()) if len(wrong) else 0,
        "wrong_history_margin_gap_max": float(wrong["margin_gap"].astype(float).max()) if len(wrong) else float("nan"),
        "wrong_history_normal_margin_min": float(wrong["normal_margin"].astype(float).min()) if len(wrong) else float("nan"),
        "min_accepted_wrong_rows": int(min_accepted_wrong_rows),
        "surface_found": bool(len(accepted_wrong) >= int(min_accepted_wrong_rows)),
    }
    summary_rows.append(aggregate)
    return summary_rows


def run_wrong_history_boundary_relocation_surface(
    *,
    checkpoint_specs: tuple[CheckpointSpec, ...],
    env_config_path: Path,
    outcome_csv: Path,
    delay_steps: int,
    max_continuation_steps: int,
    max_pairs_per_checkpoint_target: int,
    min_base_action_distance: float,
    min_base_margin_gap: float | None,
    target_normal_margins: tuple[float, ...],
    half_width_inflations: tuple[float, ...],
    body_longitudinals: tuple[float, ...] | None,
    body_laterals: tuple[float, ...] | None,
    min_half_width: float,
    max_half_width: float,
    min_normal_margin: float,
    max_normal_margin: float,
    min_margin_gap: float,
    min_accepted_wrong_rows: int,
    report_variants: tuple[str, ...],
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    env_config = load_env_config(env_config_path)
    outcome_frame = pd.read_csv(outcome_csv)
    candidate_frame = select_wrong_history_candidates(
        outcome_frame,
        max_pairs_per_checkpoint_target=max_pairs_per_checkpoint_target,
        min_base_action_distance=min_base_action_distance,
        min_base_margin_gap=min_base_margin_gap,
    )
    all_rows: list[dict[str, Any]] = []
    for checkpoint_spec in checkpoint_specs:
        checkpoint_candidates = candidate_frame[
            candidate_frame["checkpoint_label"].astype(str) == checkpoint_spec.label
        ]
        if checkpoint_candidates.empty:
            continue
        model, _ = load_actor_critic_checkpoint(checkpoint_spec.path, device=str(resolved_device))
        model.eval()
        response_dim = response_feature_dim_for_model(model)
        snapshots = collect_requested_outcome_snapshots(
            model=model,
            env_config=env_config,
            requests=_make_requests(checkpoint_candidates, delay_steps=delay_steps),
            device=resolved_device,
        )
        all_rows.extend(
            build_boundary_relocation_rows(
                candidate_rows=checkpoint_candidates,
                snapshots=snapshots,
                model=model,
                env_config=env_config,
                response_dim=response_dim,
                delay_steps=delay_steps,
                max_continuation_steps=max_continuation_steps,
                target_normal_margins=target_normal_margins,
                half_width_inflations=half_width_inflations,
                body_longitudinals=body_longitudinals,
                body_laterals=body_laterals,
                min_half_width=min_half_width,
                max_half_width=max_half_width,
                min_normal_margin=min_normal_margin,
                max_normal_margin=max_normal_margin,
                min_margin_gap=min_margin_gap,
                report_variants=report_variants,
                device=resolved_device,
            )
        )

    summary_rows = summarize_boundary_relocation_rows(
        all_rows,
        min_accepted_wrong_rows=min_accepted_wrong_rows,
    )
    accepted_wrong_rows = [
        row for row in all_rows if row.get("variant") == "wrong_matched_history" and bool(row.get("accepted", False))
    ]
    write_csv_rows(run_dir / "boundary_relocation_rows.csv", all_rows)
    write_csv_rows(run_dir / "accepted_wrong_history_rows.csv", accepted_wrong_rows)
    write_csv_rows(run_dir / "surface_summary.csv", summary_rows)
    aggregate = summary_rows[-1] if summary_rows else {}
    summary = {
        "run_type": "wrong_history_boundary_relocation_surface",
        "checkpoints": [{"label": spec.label, "path": spec.path} for spec in checkpoint_specs],
        "env_config": env_config_path,
        "outcome_csv": outcome_csv,
        "delay_steps": int(delay_steps),
        "max_continuation_steps": int(max_continuation_steps),
        "max_pairs_per_checkpoint_target": int(max_pairs_per_checkpoint_target),
        "min_base_action_distance": float(min_base_action_distance),
        "min_base_margin_gap": min_base_margin_gap,
        "target_normal_margins": target_normal_margins,
        "half_width_inflations": half_width_inflations,
        "body_longitudinals": body_longitudinals,
        "body_laterals": body_laterals,
        "min_half_width": float(min_half_width),
        "max_half_width": float(max_half_width),
        "min_normal_margin": float(min_normal_margin),
        "max_normal_margin": float(max_normal_margin),
        "min_margin_gap": float(min_margin_gap),
        "min_accepted_wrong_rows": int(min_accepted_wrong_rows),
        "report_variants": report_variants,
        "device": str(resolved_device),
        "candidate_count": int(len(candidate_frame)),
        "row_count": int(len(all_rows)),
        "accepted_wrong_history_rows": int(aggregate.get("accepted_wrong_history_rows", 0)),
        "accepted_wrong_history_pairs": int(aggregate.get("accepted_wrong_history_pairs", 0)),
        "accepted_reset_rows": int(aggregate.get("accepted_reset_rows", 0)),
        "accepted_zero_current_rows": int(aggregate.get("accepted_zero_current_rows", 0)),
        "wrong_history_success_drop_count": int(aggregate.get("wrong_history_success_drop_count", 0)),
        "surface_found": bool(aggregate.get("surface_found", False)),
        "boundary_relocation_rows_csv": run_dir / "boundary_relocation_rows.csv",
        "accepted_wrong_history_rows_csv": run_dir / "accepted_wrong_history_rows.csv",
        "surface_summary_csv": run_dir / "surface_summary.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Construct a boundary-tightened wrong-history outcome surface.")
    parser.add_argument("--checkpoint-policy", action="append", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--outcome-csv", type=Path, required=True)
    parser.add_argument("--delay-steps", type=int, default=10)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--max-pairs-per-checkpoint-target", type=int, default=20)
    parser.add_argument("--min-base-action-distance", type=float, default=0.0)
    parser.add_argument("--min-base-margin-gap", type=float, default=None)
    parser.add_argument("--target-normal-margins", type=parse_float_list, default=DEFAULT_TARGET_NORMAL_MARGINS)
    parser.add_argument("--half-width-inflations", type=parse_float_list, default=(0.0,))
    parser.add_argument("--body-longitudinals", type=parse_float_list, default=None)
    parser.add_argument("--body-laterals", type=parse_float_list, default=None)
    parser.add_argument("--min-half-width", type=float, default=0.3)
    parser.add_argument("--max-half-width", type=float, default=2.5)
    parser.add_argument("--min-normal-margin", type=float, default=0.0)
    parser.add_argument("--max-normal-margin", type=float, default=0.20)
    parser.add_argument("--min-margin-gap", type=float, default=0.02)
    parser.add_argument("--min-accepted-wrong-rows", type=int, default=10)
    parser.add_argument("--report-variants", type=parse_variants, default=DEFAULT_REPORT_VARIANTS)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="wrong_history_boundary_relocation_surface")
    summary = run_wrong_history_boundary_relocation_surface(
        checkpoint_specs=tuple(args.checkpoint_policy),
        env_config_path=args.env_config,
        outcome_csv=args.outcome_csv,
        delay_steps=args.delay_steps,
        max_continuation_steps=args.max_continuation_steps,
        max_pairs_per_checkpoint_target=args.max_pairs_per_checkpoint_target,
        min_base_action_distance=args.min_base_action_distance,
        min_base_margin_gap=args.min_base_margin_gap,
        target_normal_margins=args.target_normal_margins,
        half_width_inflations=args.half_width_inflations,
        body_longitudinals=args.body_longitudinals,
        body_laterals=args.body_laterals,
        min_half_width=args.min_half_width,
        max_half_width=args.max_half_width,
        min_normal_margin=args.min_normal_margin,
        max_normal_margin=args.max_normal_margin,
        min_margin_gap=args.min_margin_gap,
        min_accepted_wrong_rows=args.min_accepted_wrong_rows,
        report_variants=args.report_variants,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
