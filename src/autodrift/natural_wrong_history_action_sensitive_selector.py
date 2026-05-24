"""Select natural wrong-history rows with action-sensitive short-horizon probes."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.evaluate import load_env_config
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec, parse_checkpoint_spec
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.matched_current_response_ambiguity import source_obstacle_bucket_key
from autodrift.matched_history_outcome_gate import (
    OutcomeSnapshot,
    collect_requested_outcome_snapshots,
    replay_outcome_variant,
)
from autodrift.tail_aligned_wrong_history_gate import parse_tail_offsets
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.train_ppo import ActorCritic, resolve_device


def parse_env_config_map(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise ValueError(f"env config map must be NAME=PATH, got {value!r}")
    name, raw_path = value.split("=", 1)
    name = name.strip()
    if not name:
        raise ValueError(f"env config map has empty name: {value!r}")
    return name, Path(raw_path)


def _clip01(value: float) -> float:
    if not np.isfinite(value):
        return 0.0
    return float(np.clip(value, 0.0, 1.0))


def _label_priority(label: str) -> float:
    return {
        "drift_required": 0.35,
        "unavoidable": 0.25,
        "aes_feasible": 0.10,
    }.get(str(label), 0.0)


def action_sensitive_score(row: dict[str, Any]) -> float:
    visible_threshold = max(float(row.get("visible_threshold", 1.0) or 1.0), 1e-6)
    visible_distance = float(row.get("visible_distance", 0.0) or 0.0)
    visible_bonus = _clip01(1.0 - visible_distance / visible_threshold)
    obstacle_distance = float(row.get("left_obstacle_distance", 30.0) or 30.0)
    near_boundary_proxy = _clip01((30.0 - obstacle_distance) / 30.0)
    return float(
        2.0 * _clip01(float(row.get("action_trajectory_distance_mean", 0.0) or 0.0) / 0.25)
        + _clip01(float(row.get("first_action_distance", 0.0) or 0.0) / 0.25)
        + 0.5 * _clip01(float(row.get("action_trajectory_distance_max", 0.0) or 0.0) / 0.50)
        + 0.5 * _clip01(float(row.get("target_z_delta", 0.0) or 0.0) / 4.0)
        + 0.3 * near_boundary_proxy
        + _label_priority(str(row.get("left_obstacle_label", "")))
        + 0.15 * visible_bonus
    )


def snapshot_requests(pair_rows: pd.DataFrame, offsets: tuple[int, ...]) -> dict[int, set[int]]:
    requests: dict[int, set[int]] = {}
    for _, row in pair_rows.iterrows():
        for offset in offsets:
            for prefix in ("left", "right"):
                seed = int(row[f"{prefix}_seed"])
                step = int(row[f"{prefix}_step"]) + int(offset)
                requests.setdefault(seed, set()).add(step)
    return requests


def _snapshot(
    snapshots: dict[tuple[int, int], OutcomeSnapshot],
    seed: int,
    step: int,
) -> OutcomeSnapshot | None:
    return snapshots.get((int(seed), int(step)))


def _first_action(result: dict[str, Any]) -> np.ndarray:
    return np.asarray(
        [result["first_steer"], result["first_throttle"], result["first_brake"]],
        dtype=np.float32,
    )


def score_pair_offsets(
    *,
    pair_rows: pd.DataFrame,
    snapshots: dict[tuple[int, int], OutcomeSnapshot],
    model: ActorCritic,
    env_config: dict[str, Any],
    env_config_path: Path,
    response_dim: int,
    offsets: tuple[int, ...],
    horizon_steps: int,
    device: torch.device,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    scored: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    for pair_id, pair in pair_rows.reset_index(drop=True).iterrows():
        for offset in offsets:
            left_step = int(pair["left_step"]) + int(offset)
            right_step = int(pair["right_step"]) + int(offset)
            left = _snapshot(snapshots, int(pair["left_seed"]), left_step)
            right = _snapshot(snapshots, int(pair["right_seed"]), right_step)
            if left is None or right is None:
                invalid.append(
                    {
                        "pair_id": int(pair_id),
                        "config": str(pair.get("config", "")),
                        "probe_seed": int(pair.get("probe_seed", -1)),
                        "target": str(pair.get("target", "")),
                        "decision_offset": int(offset),
                        "left_seed": int(pair["left_seed"]),
                        "right_seed": int(pair["right_seed"]),
                        "left_step": int(pair["left_step"]),
                        "right_step": int(pair["right_step"]),
                        "left_decision_step": left_step,
                        "right_decision_step": right_step,
                        "missing_left_snapshot": left is None,
                        "missing_right_snapshot": right is None,
                    }
                )
                continue

            normal, normal_actions = replay_outcome_variant(
                model=model,
                snapshot=left,
                env_config=env_config,
                variant="normal",
                response_dim=response_dim,
                variant_hidden=None,
                normal_first_action=None,
                normal_actions=None,
                max_continuation_steps=horizon_steps,
                device=device,
            )
            wrong, _ = replay_outcome_variant(
                model=model,
                snapshot=left,
                env_config=env_config,
                variant="wrong_matched_history",
                response_dim=response_dim,
                variant_hidden=right.hidden,
                normal_first_action=_first_action(normal),
                normal_actions=normal_actions,
                max_continuation_steps=horizon_steps,
                device=device,
            )
            normal_margin = float(normal.get("min_clearance_margin", float("nan")))
            wrong_margin = float(wrong.get("min_clearance_margin", float("nan")))
            row = dict(pair.to_dict())
            row.update(
                {
                    "pair_id": int(pair_id),
                    "env_config": str(env_config_path),
                    "source_left_step": int(pair["left_step"]),
                    "source_right_step": int(pair["right_step"]),
                    "decision_offset": int(offset),
                    "left_step": left_step,
                    "right_step": right_step,
                    "normal_success": bool(normal.get("success", False)),
                    "wrong_success": bool(wrong.get("success", False)),
                    "normal_collision": bool(normal.get("collision", False)),
                    "wrong_collision": bool(wrong.get("collision", False)),
                    "normal_obstacle_completed": bool(normal.get("obstacle_completed", False)),
                    "wrong_obstacle_completed": bool(wrong.get("obstacle_completed", False)),
                    "normal_min_clearance_margin": normal_margin,
                    "wrong_min_clearance_margin": wrong_margin,
                    "short_horizon_margin_gap": (
                        normal_margin - wrong_margin
                        if np.isfinite(normal_margin) and np.isfinite(wrong_margin)
                        else float("nan")
                    ),
                    "first_action_distance": float(wrong.get("first_action_distance", float("nan"))),
                    "action_trajectory_distance_mean": float(
                        wrong.get("action_trajectory_distance_mean", float("nan"))
                    ),
                    "action_trajectory_distance_max": float(
                        wrong.get("action_trajectory_distance_max", float("nan"))
                    ),
                }
            )
            row["action_sensitive_score"] = action_sensitive_score(row)
            scored.append(row)
    return scored, invalid


def select_action_sensitive_rows(
    candidates: pd.DataFrame,
    *,
    first_action_threshold: float,
    trajectory_mean_threshold: float,
    trajectory_max_threshold: float,
    max_rows: int,
    max_per_probe_seed: int,
    max_per_left_seed: int,
    max_per_label: int,
    max_per_target: int,
    max_per_config: int,
    max_per_offset: int,
    max_per_obstacle_bucket: int,
    obstacle_distance_bucket_width: float,
    obstacle_lateral_bucket_width: float,
) -> pd.DataFrame:
    frame = candidates.copy()
    if frame.empty:
        return frame
    frame["stage1_pass"] = frame["first_action_distance"].astype(float) >= float(first_action_threshold)
    frame["trajectory_pass"] = (
        (frame["action_trajectory_distance_mean"].astype(float) >= float(trajectory_mean_threshold))
        | (frame["action_trajectory_distance_max"].astype(float) >= float(trajectory_max_threshold))
    )
    eligible = frame[frame["stage1_pass"].astype(bool) & frame["trajectory_pass"].astype(bool)].copy()
    if eligible.empty or max_rows == 0:
        return eligible.head(0).copy()
    eligible["obstacle_bucket"] = [
        source_obstacle_bucket_key(
            row,
            distance_width=obstacle_distance_bucket_width,
            lateral_width=obstacle_lateral_bucket_width,
        )
        for row in eligible.to_dict(orient="records")
    ]
    eligible = eligible.sort_values(
        [
            "action_sensitive_score",
            "action_trajectory_distance_mean",
            "first_action_distance",
            "target_z_delta",
            "visible_distance",
        ],
        ascending=[False, False, False, False, True],
    )

    selected: list[dict[str, Any]] = []
    counts: dict[str, dict[Any, int]] = {
        "probe_seed": {},
        "left_seed": {},
        "left_obstacle_label": {},
        "target": {},
        "config": {},
        "decision_offset": {},
        "obstacle_bucket": {},
    }
    caps = {
        "probe_seed": int(max_per_probe_seed),
        "left_seed": int(max_per_left_seed),
        "left_obstacle_label": int(max_per_label),
        "target": int(max_per_target),
        "config": int(max_per_config),
        "decision_offset": int(max_per_offset),
        "obstacle_bucket": int(max_per_obstacle_bucket),
    }
    for row in eligible.to_dict(orient="records"):
        if len(selected) >= int(max_rows):
            break
        blocked = False
        for key, cap in caps.items():
            if cap <= 0:
                continue
            value = row.get(key)
            if counts[key].get(value, 0) >= cap:
                blocked = True
                break
        if blocked:
            continue
        selected.append(row)
        for key in counts:
            value = row.get(key)
            counts[key][value] = counts[key].get(value, 0) + 1
    return pd.DataFrame(selected, columns=list(eligible.columns))


def _counts(frame: pd.DataFrame, key: str) -> dict[str, int]:
    if frame.empty or key not in frame:
        return {}
    return {str(k): int(v) for k, v in frame.groupby(key, observed=True).size().to_dict().items()}


def _max_share(frame: pd.DataFrame, key: str) -> float:
    if frame.empty or key not in frame:
        return 0.0
    counts = frame.groupby(key, observed=True).size()
    return float(counts.max() / len(frame)) if len(frame) else 0.0


def summarize_selection(
    candidates: pd.DataFrame,
    targeted: pd.DataFrame,
    *,
    min_targeted_rows: int,
    min_probe_seed_count: int,
    min_obstacle_label_count: int,
    min_target_count: int,
    min_config_count: int,
    min_offset_count: int,
    max_single_seed_share: float,
    max_single_label_share: float,
    max_single_config_share: float,
    baseline_trajectory_mean: float,
) -> dict[str, Any]:
    if candidates.empty or "stage1_pass" not in candidates:
        stage1 = candidates.head(0).copy()
    else:
        stage1 = candidates[candidates["stage1_pass"].astype(bool)]
    if candidates.empty or "stage1_pass" not in candidates or "trajectory_pass" not in candidates:
        eligible = candidates.head(0).copy()
    else:
        eligible = candidates[
            candidates["stage1_pass"].astype(bool) & candidates["trajectory_pass"].astype(bool)
        ]
    trajectory_mean = (
        float(targeted["action_trajectory_distance_mean"].astype(float).mean()) if len(targeted) else None
    )
    trajectory_p90 = (
        float(targeted["action_trajectory_distance_mean"].astype(float).quantile(0.90)) if len(targeted) else None
    )
    normal_margin_min = float(targeted["normal_min_clearance_margin"].astype(float).min()) if len(targeted) else None
    probe_seed_count = int(targeted["probe_seed"].nunique()) if "probe_seed" in targeted else 0
    label_count = int(targeted["left_obstacle_label"].nunique()) if "left_obstacle_label" in targeted else 0
    target_count = int(targeted["target"].nunique()) if "target" in targeted else 0
    config_count = int(targeted["config"].nunique()) if "config" in targeted else 0
    offset_count = int(targeted["decision_offset"].nunique()) if "decision_offset" in targeted else 0
    single_seed_share = _max_share(targeted, "probe_seed")
    single_label_share = _max_share(targeted, "left_obstacle_label")
    single_config_share = _max_share(targeted, "config")
    source_gate_pass = (
        len(targeted) >= int(min_targeted_rows)
        and probe_seed_count >= int(min_probe_seed_count)
        and label_count >= int(min_obstacle_label_count)
        and target_count >= int(min_target_count)
        and config_count >= int(min_config_count)
        and offset_count >= int(min_offset_count)
        and single_seed_share <= float(max_single_seed_share)
        and single_label_share <= float(max_single_label_share)
        and single_config_share <= float(max_single_config_share)
    )
    materially_stronger = bool(trajectory_mean is not None and trajectory_mean > 2.0 * float(baseline_trajectory_mean))
    return {
        "candidate_row_count": int(len(candidates)),
        "stage1_pass_count": int(len(stage1)),
        "trajectory_pass_count": int(len(eligible)),
        "targeted_pair_count": int(len(targeted)),
        "targeted_probe_seed_count": probe_seed_count,
        "targeted_obstacle_label_count": label_count,
        "targeted_target_count": target_count,
        "targeted_config_count": config_count,
        "targeted_offset_count": offset_count,
        "single_seed_share": single_seed_share,
        "single_label_share": single_label_share,
        "single_config_share": single_config_share,
        "targeted_trajectory_mean": trajectory_mean,
        "targeted_trajectory_p90": trajectory_p90,
        "targeted_normal_margin_min": normal_margin_min,
        "targeted_by_probe_seed": _counts(targeted, "probe_seed"),
        "targeted_by_left_obstacle_label": _counts(targeted, "left_obstacle_label"),
        "targeted_by_target": _counts(targeted, "target"),
        "targeted_by_config": _counts(targeted, "config"),
        "targeted_by_offset": _counts(targeted, "decision_offset"),
        "source_diversity_gate_pass": bool(source_gate_pass),
        "materially_stronger_than_baseline": materially_stronger,
        "action_sensitive_surface_found": bool(source_gate_pass and materially_stronger),
    }


def run_selector(
    *,
    candidate_pairs_csv: Path,
    checkpoint_spec: CheckpointSpec,
    env_config_map: dict[str, Path],
    decision_offsets: tuple[int, ...],
    short_horizon_steps: int,
    first_action_threshold: float,
    trajectory_mean_threshold: float,
    trajectory_max_threshold: float,
    max_rows: int,
    max_per_probe_seed: int,
    max_per_left_seed: int,
    max_per_label: int,
    max_per_target: int,
    max_per_config: int,
    max_per_offset: int,
    max_per_obstacle_bucket: int,
    min_targeted_rows: int,
    min_probe_seed_count: int,
    min_obstacle_label_count: int,
    min_target_count: int,
    min_config_count: int,
    min_offset_count: int,
    max_single_seed_share: float,
    max_single_label_share: float,
    max_single_config_share: float,
    baseline_trajectory_mean: float,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_spec.path, device=str(resolved_device))
    model.eval()
    response_dim = response_feature_dim_for_model(model)
    pairs = pd.read_csv(candidate_pairs_csv)

    all_scored: list[dict[str, Any]] = []
    all_invalid: list[dict[str, Any]] = []
    for config_name, group in pairs.groupby("config", observed=True):
        if str(config_name) not in env_config_map:
            raise ValueError(f"missing env config mapping for config={config_name!r}")
        env_config_path = env_config_map[str(config_name)]
        env_config = load_env_config(env_config_path)
        snapshots = collect_requested_outcome_snapshots(
            model=model,
            env_config=env_config,
            requests=snapshot_requests(group, decision_offsets),
            device=resolved_device,
        )
        scored, invalid = score_pair_offsets(
            pair_rows=group,
            snapshots=snapshots,
            model=model,
            env_config=env_config,
            env_config_path=env_config_path,
            response_dim=response_dim,
            offsets=decision_offsets,
            horizon_steps=short_horizon_steps,
            device=resolved_device,
        )
        all_scored.extend(scored)
        all_invalid.extend(invalid)

    candidate_frame = pd.DataFrame(all_scored)
    if not candidate_frame.empty:
        candidate_frame["stage1_pass"] = (
            candidate_frame["first_action_distance"].astype(float) >= float(first_action_threshold)
        )
        candidate_frame["trajectory_pass"] = (
            (candidate_frame["action_trajectory_distance_mean"].astype(float) >= float(trajectory_mean_threshold))
            | (candidate_frame["action_trajectory_distance_max"].astype(float) >= float(trajectory_max_threshold))
        )
    targeted = select_action_sensitive_rows(
        candidate_frame,
        first_action_threshold=first_action_threshold,
        trajectory_mean_threshold=trajectory_mean_threshold,
        trajectory_max_threshold=trajectory_max_threshold,
        max_rows=max_rows,
        max_per_probe_seed=max_per_probe_seed,
        max_per_left_seed=max_per_left_seed,
        max_per_label=max_per_label,
        max_per_target=max_per_target,
        max_per_config=max_per_config,
        max_per_offset=max_per_offset,
        max_per_obstacle_bucket=max_per_obstacle_bucket,
        obstacle_distance_bucket_width=5.0,
        obstacle_lateral_bucket_width=1.0,
    )
    summary = {
        "run_type": "natural_wrong_history_action_sensitive_selector",
        "candidate_pairs_csv": candidate_pairs_csv,
        "checkpoint": {"label": checkpoint_spec.label, "path": checkpoint_spec.path},
        "env_config_map": env_config_map,
        "decision_offsets": list(decision_offsets),
        "short_horizon_steps": int(short_horizon_steps),
        "first_action_threshold": float(first_action_threshold),
        "trajectory_mean_threshold": float(trajectory_mean_threshold),
        "trajectory_max_threshold": float(trajectory_max_threshold),
        "max_rows": int(max_rows),
        "invalid_snapshot_row_count": int(len(all_invalid)),
        **summarize_selection(
            candidate_frame,
            targeted,
            min_targeted_rows=min_targeted_rows,
            min_probe_seed_count=min_probe_seed_count,
            min_obstacle_label_count=min_obstacle_label_count,
            min_target_count=min_target_count,
            min_config_count=min_config_count,
            min_offset_count=min_offset_count,
            max_single_seed_share=max_single_seed_share,
            max_single_label_share=max_single_label_share,
            max_single_config_share=max_single_config_share,
            baseline_trajectory_mean=baseline_trajectory_mean,
        ),
        "action_sensitive_candidates_csv": run_dir / "action_sensitive_candidates.csv",
        "targeted_pairs_csv": run_dir / "targeted_pairs.csv",
        "invalid_snapshots_csv": run_dir / "invalid_snapshots.csv",
    }
    write_csv_rows(run_dir / "action_sensitive_candidates.csv", candidate_frame.to_dict(orient="records"))
    write_csv_rows(run_dir / "targeted_pairs.csv", targeted.to_dict(orient="records"), fieldnames=list(targeted.columns))
    write_csv_rows(run_dir / "invalid_snapshots.csv", all_invalid)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Select action-sensitive natural wrong-history pairs.")
    parser.add_argument("--candidate-pairs-csv", type=Path, required=True)
    parser.add_argument("--checkpoint-policy", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--env-config-map", action="append", type=parse_env_config_map, required=True)
    parser.add_argument("--decision-offsets", type=parse_tail_offsets, default=(0, 2, 4, 8))
    parser.add_argument("--short-horizon-steps", type=int, default=8)
    parser.add_argument("--first-action-threshold", type=float, default=0.12)
    parser.add_argument("--trajectory-mean-threshold", type=float, default=0.12)
    parser.add_argument("--trajectory-max-threshold", type=float, default=0.25)
    parser.add_argument("--max-rows", type=int, default=360)
    parser.add_argument("--max-per-probe-seed", type=int, default=70)
    parser.add_argument("--max-per-left-seed", type=int, default=8)
    parser.add_argument("--max-per-label", type=int, default=160)
    parser.add_argument("--max-per-target", type=int, default=140)
    parser.add_argument("--max-per-config", type=int, default=180)
    parser.add_argument("--max-per-offset", type=int, default=100)
    parser.add_argument("--max-per-obstacle-bucket", type=int, default=24)
    parser.add_argument("--min-targeted-rows", type=int, default=240)
    parser.add_argument("--min-probe-seed-count", type=int, default=6)
    parser.add_argument("--min-obstacle-label-count", type=int, default=2)
    parser.add_argument("--min-target-count", type=int, default=2)
    parser.add_argument("--min-config-count", type=int, default=2)
    parser.add_argument("--min-offset-count", type=int, default=2)
    parser.add_argument("--max-single-seed-share", type=float, default=0.50)
    parser.add_argument("--max-single-label-share", type=float, default=0.70)
    parser.add_argument("--max-single-config-share", type=float, default=0.70)
    parser.add_argument("--baseline-trajectory-mean", type=float, default=0.055405)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    env_config_map = dict(args.env_config_map)
    run_dir = args.run_dir or make_run_dir(prefix="natural_wrong_history_action_sensitive_selector")
    summary = run_selector(
        candidate_pairs_csv=args.candidate_pairs_csv,
        checkpoint_spec=args.checkpoint_policy,
        env_config_map=env_config_map,
        decision_offsets=tuple(args.decision_offsets),
        short_horizon_steps=args.short_horizon_steps,
        first_action_threshold=args.first_action_threshold,
        trajectory_mean_threshold=args.trajectory_mean_threshold,
        trajectory_max_threshold=args.trajectory_max_threshold,
        max_rows=args.max_rows,
        max_per_probe_seed=args.max_per_probe_seed,
        max_per_left_seed=args.max_per_left_seed,
        max_per_label=args.max_per_label,
        max_per_target=args.max_per_target,
        max_per_config=args.max_per_config,
        max_per_offset=args.max_per_offset,
        max_per_obstacle_bucket=args.max_per_obstacle_bucket,
        min_targeted_rows=args.min_targeted_rows,
        min_probe_seed_count=args.min_probe_seed_count,
        min_obstacle_label_count=args.min_obstacle_label_count,
        min_target_count=args.min_target_count,
        min_config_count=args.min_config_count,
        min_offset_count=args.min_offset_count,
        max_single_seed_share=args.max_single_seed_share,
        max_single_label_share=args.max_single_label_share,
        max_single_config_share=args.max_single_config_share,
        baseline_trajectory_mean=args.baseline_trajectory_mean,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
