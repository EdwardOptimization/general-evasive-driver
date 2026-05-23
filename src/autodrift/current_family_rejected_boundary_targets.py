"""Export current-family rejected-history collision-side action targets."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.boundary_outcome_replay_gate import _requests, _snapshot, validate_corpus_frame
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.current_family_conflict_corpus import (
    _action_array,
    _write_current_family_conflict_corpus,
    conflict_row_weight,
    parse_int_list,
)
from autodrift.evaluate import load_env_config
from autodrift.intervention_objectives import load_current_family_conflict_snippets
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.matched_history_outcome_gate import collect_requested_outcome_snapshots
from autodrift.terminal_margin_recovery_anchor import (
    _rollout_first_action_override,
    build_action_candidates,
    parse_float_list,
)
from autodrift.train_ppo import resolve_device
from autodrift.wrong_history_boundary_relocation_surface import relocate_outcome_snapshot


def _finite_float(value: Any, default: float = float("nan")) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    return parsed if np.isfinite(parsed) else float(default)


def rejected_boundary_acceptance(
    *,
    candidate_margin: float,
    candidate_success: bool,
    baseline_margin: float,
    action_l2: float,
    min_margin_decrease: float,
    max_action_l2: float,
) -> tuple[bool, str]:
    """Accept local targets that keep wrong-history rollout safely failed."""

    if bool(candidate_success):
        return False, "candidate_successful"
    if not np.isfinite(candidate_margin):
        return False, "candidate_margin_not_finite"
    if not np.isfinite(baseline_margin):
        return False, "baseline_margin_not_finite"
    margin_decrease = float(baseline_margin) - float(candidate_margin)
    if margin_decrease < float(min_margin_decrease):
        return False, "insufficient_collision_margin_decrease"
    if float(action_l2) > float(max_action_l2):
        return False, "outside_action_trust_region"
    return True, "accepted"


def select_collision_side_target(candidate_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    accepted = [row for row in candidate_rows if bool(row.get("accepted", False))]
    if not accepted:
        return None
    return max(
        accepted,
        key=lambda row: (
            _finite_float(row.get("margin_decrease"), float("-inf")),
            -_finite_float(row.get("candidate_margin"), float("inf")),
            -_finite_float(row.get("action_l2"), float("inf")),
        ),
    )


def _best_any_candidate(candidate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not candidate_rows:
        raise ValueError("cannot choose from an empty candidate list")
    return max(
        candidate_rows,
        key=lambda row: (
            _finite_float(row.get("margin_decrease"), float("-inf")),
            -_finite_float(row.get("candidate_margin"), float("inf")),
            -_finite_float(row.get("action_l2"), float("inf")),
        ),
    )


def export_current_family_rejected_boundary_targets(
    *,
    checkpoint: Path,
    boundary_corpus_npz: Path,
    boundary_corpus_csv: Path,
    env_config: Path,
    row_ids: tuple[int, ...],
    run_dir: Path,
    steer_deltas: tuple[float, ...],
    throttle_deltas: tuple[float, ...],
    brake_deltas: tuple[float, ...],
    min_margin_decrease: float,
    max_action_l2: float,
    max_continuation_steps: int,
    margin_floor: float,
    max_weight: float,
    include_base_retention: bool,
    device: str,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint, device=str(resolved_device))
    model.eval()
    config = load_env_config(env_config)

    data = np.load(boundary_corpus_npz)
    required = {"observation", "preferred_hidden", "rejected_hidden", "weight"}
    missing = sorted(required.difference(data.files))
    if missing:
        raise ValueError(f"boundary corpus npz missing fields: {', '.join(missing)}")
    frame = pd.read_csv(boundary_corpus_csv)
    validate_corpus_frame(frame)

    selected_frames = []
    for row_id in row_ids:
        rows = frame[frame["row_id"].astype(int).eq(int(row_id))].copy()
        if len(rows) != 1:
            raise ValueError(f"expected exactly one boundary corpus row for row_id={row_id}, got {len(rows)}")
        selected_frames.append(rows)
    selected = pd.concat(selected_frames, ignore_index=False)
    snapshots = collect_requested_outcome_snapshots(
        model=model,
        env_config=config,
        requests=_requests(selected),
        device=resolved_device,
    )

    observations: list[np.ndarray] = []
    preferred_hiddens: list[np.ndarray] = []
    rejected_hiddens: list[np.ndarray] = []
    target_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    skipped_rows: list[dict[str, Any]] = []

    for source_index, row in selected.iterrows():
        row_id = int(row["row_id"])
        left = _snapshot(snapshots, int(row["left_seed"]), int(row["left_step"]))
        right = _snapshot(snapshots, int(row["right_seed"]), int(row["right_step"]))
        relocated = relocate_outcome_snapshot(
            left,
            body_longitudinal=float(row["relocated_obstacle_body_x"]),
            body_lateral=float(row["relocated_obstacle_body_y"]),
            half_width=float(row["relocated_obstacle_half_width"]),
        )
        observation = np.asarray(relocated.observation, dtype=np.float32)
        preferred_hidden = relocated.hidden.detach().clone()
        rejected_hidden = right.hidden.detach().clone()
        preferred_action, _ = deterministic_action_from_hidden(
            model,
            observation,
            preferred_hidden,
            resolved_device,
        )
        rejected_action, _ = deterministic_action_from_hidden(
            model,
            observation,
            rejected_hidden,
            resolved_device,
        )
        wrong_snapshot = replace(relocated, hidden=rejected_hidden)
        baseline = _rollout_first_action_override(
            model=model,
            snapshot=wrong_snapshot,
            first_action=rejected_action,
            max_continuation_steps=max_continuation_steps,
            device=resolved_device,
        )
        baseline_margin = _finite_float(baseline.get("min_clearance_margin"))
        row_candidate_rows: list[dict[str, Any]] = []
        for candidate in build_action_candidates(
            rejected_action,
            steer_deltas=steer_deltas,
            throttle_deltas=throttle_deltas,
            brake_deltas=brake_deltas,
        ):
            result = _rollout_first_action_override(
                model=model,
                snapshot=wrong_snapshot,
                first_action=candidate.action,
                max_continuation_steps=max_continuation_steps,
                device=resolved_device,
            )
            candidate_margin = _finite_float(result.get("min_clearance_margin"))
            margin_decrease = (
                baseline_margin - candidate_margin
                if np.isfinite(baseline_margin) and np.isfinite(candidate_margin)
                else float("nan")
            )
            accepted, rejection_reason = rejected_boundary_acceptance(
                candidate_margin=candidate_margin,
                candidate_success=bool(result.get("success", False)),
                baseline_margin=baseline_margin,
                action_l2=float(candidate.action_l2),
                min_margin_decrease=min_margin_decrease,
                max_action_l2=max_action_l2,
            )
            candidate_row = {
                "row_id": row_id,
                "source_index": int(source_index),
                "candidate_id": int(candidate.candidate_id),
                "baseline_success": bool(baseline.get("success", False)),
                "baseline_margin": baseline_margin,
                "candidate_success": bool(result.get("success", False)),
                "candidate_terminal_reason": str(result.get("terminal_reason", "")),
                "candidate_margin": candidate_margin,
                "margin_decrease": margin_decrease,
                "base_steer": float(rejected_action[0]),
                "base_throttle": float(rejected_action[1]),
                "base_brake": float(rejected_action[2]),
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

        target = select_collision_side_target(row_candidate_rows)
        target_status = "collision_side_target"
        if target is None and include_base_retention:
            target = _best_any_candidate(row_candidate_rows)
            target_status = "base_retention"
        if target is None:
            best_any = _best_any_candidate(row_candidate_rows)
            skipped_rows.append(
                {
                    "row_id": row_id,
                    "source_index": int(source_index),
                    "skip_reason": "no_collision_side_target",
                    "baseline_margin": baseline_margin,
                    "best_margin_decrease": best_any.get("margin_decrease", float("nan")),
                    "best_rejection_reason": best_any.get("rejection_reason", ""),
                }
            )
            continue

        selected_action = np.asarray(
            [target["candidate_steer"], target["candidate_throttle"], target["candidate_brake"]],
            dtype=np.float32,
        )
        source_weight = float(np.asarray(data["weight"], dtype=np.float32)[int(source_index)])
        weight = conflict_row_weight(
            boundary_margin=baseline_margin,
            source_weight=source_weight,
            margin_floor=margin_floor,
            max_weight=max_weight,
        )
        target_row = {
            "row_id": row_id,
            "source_index": int(source_index),
            "target": str(row.get("target", "")),
            "physical_pair_key": str(row.get("physical_pair_key", "")),
            "left_step": int(row.get("left_step", -1)),
            "right_step": int(row.get("right_step", -1)),
            "source_weight": source_weight,
            "boundary_margin": baseline_margin,
            "selected_margin": float(target["candidate_margin"]),
            "margin_decrease": float(target["margin_decrease"]),
            "target_status": target_status,
            "selected_candidate_id": int(target["candidate_id"]),
            "selected_candidate_accepted": bool(target.get("accepted", False)),
            "selected_candidate_rejection_reason": str(target.get("rejection_reason", "")),
            "action_l2": float(target["action_l2"]),
            "weight": weight,
            "preferred_anchor_steer": float(preferred_action[0]),
            "preferred_anchor_throttle": float(preferred_action[1]),
            "preferred_anchor_brake": float(preferred_action[2]),
            "rejected_base_steer": float(rejected_action[0]),
            "rejected_base_throttle": float(rejected_action[1]),
            "rejected_base_brake": float(rejected_action[2]),
            "rejected_boundary_steer": float(selected_action[0]),
            "rejected_boundary_throttle": float(selected_action[1]),
            "rejected_boundary_brake": float(selected_action[2]),
            "preferred_anchor_action": _action_array(preferred_action),
            "rejected_boundary_action": _action_array(selected_action),
        }
        observations.append(observation.copy())
        preferred_hiddens.append(preferred_hidden.detach().cpu().numpy().reshape(-1).astype(np.float32))
        rejected_hiddens.append(rejected_hidden.detach().cpu().numpy().reshape(-1).astype(np.float32))
        target_rows.append(target_row)

    write_csv_rows(run_dir / "rejected_boundary_candidates.csv", candidate_rows)
    csv_rows = [
        {key: value for key, value in row.items() if key not in {"preferred_anchor_action", "rejected_boundary_action"}}
        for row in target_rows
    ]
    write_csv_rows(run_dir / "current_family_conflict_rows.csv", csv_rows)
    write_csv_rows(run_dir / "skipped_rows.csv", skipped_rows)

    corpus_npz = run_dir / "current_family_conflict_corpus.npz"
    _write_current_family_conflict_corpus(
        output_npz=corpus_npz,
        observations=observations,
        preferred_hidden=preferred_hiddens,
        rejected_hidden=rejected_hiddens,
        rows=target_rows,
    )
    loaded = load_current_family_conflict_snippets(
        corpus_npz,
        device=resolved_device,
        obs_dim=int(model.obs_dim),
        hidden_size=int(model.actor_mean.in_features),
        act_dim=int(model.act_dim),
    )
    target_frame = pd.DataFrame(csv_rows)
    accepted = (
        target_frame[target_frame["selected_candidate_accepted"].astype(bool)]
        if not target_frame.empty
        else pd.DataFrame()
    )
    summary = {
        "run_type": "current_family_rejected_boundary_targets",
        "checkpoint": checkpoint,
        "boundary_corpus_npz": boundary_corpus_npz,
        "boundary_corpus_csv": boundary_corpus_csv,
        "env_config": env_config,
        "row_ids": row_ids,
        "device": str(resolved_device),
        "rows_requested": int(len(row_ids)),
        "candidate_rollouts": int(len(candidate_rows)),
        "candidate_grid": {
            "steer_deltas": steer_deltas,
            "throttle_deltas": throttle_deltas,
            "brake_deltas": brake_deltas,
        },
        "min_margin_decrease": float(min_margin_decrease),
        "max_action_l2": float(max_action_l2),
        "max_continuation_steps": int(max_continuation_steps),
        "include_base_retention": bool(include_base_retention),
        "exported_rows": int(loaded.size),
        "accepted_target_rows": int(len(accepted)),
        "skipped_rows": int(len(skipped_rows)),
        "accepted_margin_decrease_min": float(accepted["margin_decrease"].astype(float).min()) if len(accepted) else float("nan"),
        "accepted_margin_decrease_mean": float(accepted["margin_decrease"].astype(float).mean()) if len(accepted) else float("nan"),
        "accepted_margin_decrease_max": float(accepted["margin_decrease"].astype(float).max()) if len(accepted) else float("nan"),
        "current_family_conflict_corpus_npz": corpus_npz,
        "current_family_conflict_rows_csv": run_dir / "current_family_conflict_rows.csv",
        "rejected_boundary_candidates_csv": run_dir / "rejected_boundary_candidates.csv",
        "skipped_rows_csv": run_dir / "skipped_rows.csv",
        "contract": {
            "rows": int(loaded.size),
            "obs_dim": int(model.obs_dim),
            "hidden_dim": int(model.actor_mean.in_features),
            "act_dim": int(model.act_dim),
        },
        "target_source": "replay_selected_rejected_history_local_action_search",
        "actor_inputs_changed": False,
        "ppo_or_actor_update_run": False,
        "checkpoint_promoted": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--boundary-corpus-npz", type=Path, required=True)
    parser.add_argument("--boundary-corpus-csv", type=Path, required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--row-ids", type=parse_int_list, default=(15, 6))
    parser.add_argument("--steer-deltas", type=parse_float_list, default=(-0.06, -0.04, -0.02, 0.0, 0.02, 0.04, 0.06))
    parser.add_argument("--throttle-deltas", type=parse_float_list, default=(-0.04, 0.0, 0.04))
    parser.add_argument("--brake-deltas", type=parse_float_list, default=(-0.08, -0.04, 0.0, 0.04, 0.08))
    parser.add_argument("--min-margin-decrease", type=float, default=1.0e-5)
    parser.add_argument("--max-action-l2", type=float, default=0.12)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--margin-floor", type=float, default=1.0e-4)
    parser.add_argument("--max-weight", type=float, default=20.0)
    parser.add_argument("--include-base-retention", action="store_true")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="current_family_rejected_boundary_targets")
    summary = export_current_family_rejected_boundary_targets(
        checkpoint=args.checkpoint,
        boundary_corpus_npz=args.boundary_corpus_npz,
        boundary_corpus_csv=args.boundary_corpus_csv,
        env_config=args.env_config,
        row_ids=args.row_ids,
        run_dir=run_dir,
        steer_deltas=args.steer_deltas,
        throttle_deltas=args.throttle_deltas,
        brake_deltas=args.brake_deltas,
        min_margin_decrease=args.min_margin_decrease,
        max_action_l2=args.max_action_l2,
        max_continuation_steps=args.max_continuation_steps,
        margin_floor=args.margin_floor,
        max_weight=args.max_weight,
        include_base_retention=bool(args.include_base_retention),
        device=args.device,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
