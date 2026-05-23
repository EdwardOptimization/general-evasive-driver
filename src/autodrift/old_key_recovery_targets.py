"""Export replay-selected old-key local recovery targets."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, read_json, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.intervention_objectives import load_old_key_recovery_snippets
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.old_key_neighborhood_targeted_replay import (
    _probe_config,
    _randomization,
    _requests_by_condition,
    _snapshot,
    _tuple_range,
    collect_targeted_probe_snapshots,
)
from autodrift.old_key_preference_corpus import old_key_case_id
from autodrift.outcome_sensitive_corpus import obstacle_override_config, relocate_obstacle_snapshot
from autodrift.paired_perturbation_gate import condition_config
from autodrift.terminal_margin_recovery_anchor import (
    _rollout_first_action_override,
    build_action_candidates,
    candidate_acceptance,
    parse_float_list,
    select_best_candidate,
)
from autodrift.train_ppo import resolve_device


REQUIRED_ROWS_COLUMNS = (
    "case_id",
    "key",
    "seed",
    "source_condition",
    "source_step",
    "paired_step",
    "target_obstacle_distance",
    "relocated_obstacle_body_y",
    "relocated_obstacle_half_width",
)


def _require_columns(frame: pd.DataFrame, columns: tuple[str, ...], *, label: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{label} is missing columns: {', '.join(missing)}")


def _finite_float(value: Any, default: float = float("nan")) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    return parsed if np.isfinite(parsed) else float(default)


def _selected_rows(frame: pd.DataFrame, *, max_rows: int) -> pd.DataFrame:
    _require_columns(frame, REQUIRED_ROWS_COLUMNS, label="old-key recovery source rows")
    rows = frame.copy()
    if "record_type" in rows:
        rows = rows[rows["record_type"].astype(str).eq("m341_mined_case")].copy()
    if rows.empty:
        raise ValueError("old-key recovery source rows are empty")
    rows = rows.reset_index(drop=True)
    if max_rows > 0:
        rows = rows.head(int(max_rows)).reset_index(drop=True)
    return rows


def recovery_row_weight(
    row: pd.Series,
    *,
    accepted_recovery: bool,
    margin_improvement: float,
    min_margin_improvement: float,
) -> float:
    """Training-only weight based on old-key gap severity and recovery evidence."""

    gap_delta = abs(_finite_float(row.get("candidate_gap_delta", 0.0), 0.0))
    normal_delta = abs(_finite_float(row.get("candidate_normal_delta", 0.0), 0.0))
    severity = 1.0 + min(gap_delta / 5.0e-4, 8.0) + min(normal_delta / 5.0e-4, 8.0)
    if not bool(accepted_recovery):
        return float(0.25 * severity)
    denom = max(float(min_margin_improvement), 1.0e-9)
    improvement_scale = min(max(float(margin_improvement) / denom, 1.0), 8.0)
    return float(severity * improvement_scale)


def _hidden_array(model: torch.nn.Module, hidden: torch.Tensor | None, device: torch.device) -> np.ndarray:
    if hidden is None:
        hidden = model.initial_hidden(1, device)  # type: ignore[attr-defined]
    return hidden.detach().cpu().numpy().reshape(-1).astype(np.float32)


def _action_array(action: np.ndarray) -> np.ndarray:
    value = np.asarray(action, dtype=np.float32).reshape(-1)
    if value.shape != (3,):
        raise ValueError(f"action must have shape (3,), got {value.shape}")
    return np.clip(value, -1.0, 1.0).astype(np.float32)


def _best_any_candidate(candidate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not candidate_rows:
        raise ValueError("cannot choose from an empty candidate list")
    return max(
        candidate_rows,
        key=lambda item: (
            _finite_float(item.get("margin_improvement"), float("-inf")),
            _finite_float(item.get("candidate_margin"), float("-inf")),
            -_finite_float(item.get("action_l2"), float("inf")),
        ),
    )


def select_recovery_target(
    *,
    row: pd.Series,
    row_index: int,
    base_action: np.ndarray,
    rejected_anchor_action: np.ndarray,
    baseline: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    min_margin_improvement: float,
    include_base_retention: bool,
) -> dict[str, Any] | None:
    best = select_best_candidate(candidate_rows)
    baseline_margin = _finite_float(baseline.get("min_clearance_margin"))
    if best is not None:
        recovery_action = np.asarray(
            [best["candidate_steer"], best["candidate_throttle"], best["candidate_brake"]],
            dtype=np.float32,
        )
        accepted_recovery = True
        recovery_status = "recovered"
        selected = best
    elif include_base_retention:
        selected = _best_any_candidate(candidate_rows)
        recovery_action = _action_array(base_action)
        accepted_recovery = False
        recovery_status = "base_retention"
    else:
        return None

    selected_margin = _finite_float(selected.get("candidate_margin"))
    margin_improvement = (
        selected_margin - baseline_margin
        if np.isfinite(selected_margin) and np.isfinite(baseline_margin)
        else float("nan")
    )
    weight = recovery_row_weight(
        row,
        accepted_recovery=accepted_recovery,
        margin_improvement=margin_improvement,
        min_margin_improvement=min_margin_improvement,
    )
    return {
        "row_id": int(row_index),
        "case_id": str(row.get("case_id", old_key_case_id(row))),
        "key": str(row["key"]),
        "seed": int(row["seed"]),
        "source_condition": str(row["source_condition"]),
        "source_step": int(row["source_step"]),
        "paired_step": int(row["paired_step"]),
        "target_obstacle_distance": float(row["target_obstacle_distance"]),
        "relocated_obstacle_body_y": float(row["relocated_obstacle_body_y"]),
        "relocated_obstacle_half_width": float(row["relocated_obstacle_half_width"]),
        "baseline_success": bool(baseline.get("success", False)),
        "baseline_margin": baseline_margin,
        "selected_candidate_id": int(selected["candidate_id"]),
        "selected_candidate_accepted": bool(selected.get("accepted", False)),
        "selected_candidate_rejection_reason": str(selected.get("rejection_reason", "")),
        "selected_margin": selected_margin,
        "margin_improvement": margin_improvement,
        "accepted_recovery": bool(accepted_recovery),
        "recovery_status": recovery_status,
        "base_steer": float(base_action[0]),
        "base_throttle": float(base_action[1]),
        "base_brake": float(base_action[2]),
        "recovery_steer": float(recovery_action[0]),
        "recovery_throttle": float(recovery_action[1]),
        "recovery_brake": float(recovery_action[2]),
        "rejected_anchor_steer": float(rejected_anchor_action[0]),
        "rejected_anchor_throttle": float(rejected_anchor_action[1]),
        "rejected_anchor_brake": float(rejected_anchor_action[2]),
        "action_l2": float(selected.get("action_l2", 0.0)) if accepted_recovery else 0.0,
        "weight": weight,
        "recovery_action": _action_array(recovery_action),
        "rejected_anchor_action": _action_array(rejected_anchor_action),
    }


def _write_old_key_recovery_corpus(
    *,
    output_npz: Path,
    observations: list[np.ndarray],
    preferred_hidden: list[np.ndarray],
    rejected_hidden: list[np.ndarray],
    targets: list[dict[str, Any]],
) -> None:
    if not targets:
        raise ValueError("cannot write an empty old-key recovery corpus")
    np.savez_compressed(
        output_npz,
        observation=np.asarray(observations, dtype=np.float32),
        preferred_hidden=np.asarray(preferred_hidden, dtype=np.float32),
        rejected_hidden=np.asarray(rejected_hidden, dtype=np.float32),
        recovery_action=np.stack([target["recovery_action"] for target in targets]).astype(np.float32),
        rejected_anchor_action=np.stack([target["rejected_anchor_action"] for target in targets]).astype(np.float32),
        weight=np.asarray([target["weight"] for target in targets], dtype=np.float32),
        row_id=np.asarray([target["row_id"] for target in targets], dtype=np.int64),
    )


def export_old_key_local_recovery_targets(
    *,
    checkpoint: Path,
    reference_manifest: Path,
    source_rows_csv: Path,
    run_dir: Path,
    steer_deltas: tuple[float, ...],
    throttle_deltas: tuple[float, ...],
    brake_deltas: tuple[float, ...],
    min_margin_improvement: float,
    max_action_l2: float,
    max_continuation_steps: int,
    include_base_retention: bool,
    max_rows: int,
    device: str,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint, device=str(resolved_device))
    model.eval()
    manifest = read_json(reference_manifest)
    rows = _selected_rows(pd.read_csv(source_rows_csv), max_rows=max_rows)

    base_config = obstacle_override_config(
        load_env_config(Path(manifest["env_config"])),
        distance_range=None,
        half_width_range=None,
        perception_reveal_step=manifest.get("obstacle_perception_reveal_step"),
        perception_reveal_distance=manifest.get("obstacle_perception_reveal_distance"),
    )
    configs = {
        "nominal": condition_config(
            base_config,
            _tuple_range(manifest["nominal_friction_mu_range"]),
            _randomization(manifest.get("nominal_randomization")),
        ),
        "perturbed": condition_config(
            base_config,
            _tuple_range(manifest["perturbed_friction_mu_range"]),
            _randomization(manifest.get("perturbed_randomization")),
        ),
    }
    probe = _probe_config(manifest.get("probe", {}))
    requests = _requests_by_condition(rows)
    snapshots: dict[str, dict[int, dict[int, Any]]] = {"nominal": {}, "perturbed": {}}
    for condition, seed_requests in requests.items():
        for seed, steps in seed_requests.items():
            snapshots[condition][int(seed)] = collect_targeted_probe_snapshots(
                model=model,
                env_config=configs[condition],
                condition=condition,
                seed=int(seed),
                requested_steps=set(int(step) for step in steps),
                max_probe_steps=int(manifest["max_probe_steps"]),
                probe_config=probe,
            )

    candidate_rows: list[dict[str, Any]] = []
    target_rows: list[dict[str, Any]] = []
    observations: list[np.ndarray] = []
    preferred_hiddens: list[np.ndarray] = []
    rejected_hiddens: list[np.ndarray] = []
    skipped_rows: list[dict[str, Any]] = []

    for row_index, row in rows.reset_index(drop=True).iterrows():
        seed = int(row["seed"])
        source = str(row["source_condition"])
        paired = "perturbed" if source == "nominal" else "nominal"
        source_snapshot = _snapshot(snapshots, source, seed, int(row["source_step"]))
        paired_snapshot = _snapshot(snapshots, paired, seed, int(row["paired_step"]))
        if source_snapshot is None or paired_snapshot is None:
            skipped_rows.append(
                {
                    "row_id": int(row_index),
                    "case_id": str(row.get("case_id", old_key_case_id(row))),
                    "skip_reason": "missing_reconstructed_snapshot",
                }
            )
            continue
        relocated = relocate_obstacle_snapshot(
            source_snapshot,
            body_longitudinal=float(row["target_obstacle_distance"]),
            body_lateral=float(row["relocated_obstacle_body_y"]),
            half_width=float(row["relocated_obstacle_half_width"]),
        )
        preferred_hidden = source_snapshot.hidden if source_snapshot.hidden is not None else model.initial_hidden(1, resolved_device)
        rejected_hidden = paired_snapshot.hidden if paired_snapshot.hidden is not None else model.initial_hidden(1, resolved_device)
        base_action, _ = deterministic_action_from_hidden(
            model,
            np.asarray(relocated.observation, dtype=np.float32),
            preferred_hidden,
            resolved_device,
        )
        rejected_anchor_action, _ = deterministic_action_from_hidden(
            model,
            np.asarray(relocated.observation, dtype=np.float32),
            rejected_hidden,
            resolved_device,
        )
        baseline = _rollout_first_action_override(
            model=model,
            snapshot=relocated,
            first_action=base_action,
            max_continuation_steps=max_continuation_steps,
            device=resolved_device,
        )
        baseline_margin = _finite_float(baseline.get("min_clearance_margin"))
        row_candidate_rows: list[dict[str, Any]] = []
        for candidate in build_action_candidates(
            base_action,
            steer_deltas=steer_deltas,
            throttle_deltas=throttle_deltas,
            brake_deltas=brake_deltas,
        ):
            result = _rollout_first_action_override(
                model=model,
                snapshot=relocated,
                first_action=candidate.action,
                max_continuation_steps=max_continuation_steps,
                device=resolved_device,
            )
            candidate_margin = _finite_float(result.get("min_clearance_margin"))
            accepted, rejection_reason = candidate_acceptance(
                candidate_margin=candidate_margin,
                candidate_success=bool(result.get("success", False)),
                baseline_margin=baseline_margin,
                required_margin_floor=baseline_margin,
                action_l2=candidate.action_l2,
                min_margin_improvement=min_margin_improvement,
                max_action_l2=max_action_l2,
            )
            candidate_row = {
                "row_id": int(row_index),
                "case_id": str(row.get("case_id", old_key_case_id(row))),
                "key": str(row["key"]),
                "seed": seed,
                "source_condition": source,
                "source_step": int(row["source_step"]),
                "paired_step": int(row["paired_step"]),
                "candidate_id": int(candidate.candidate_id),
                "baseline_success": bool(baseline.get("success", False)),
                "baseline_margin": baseline_margin,
                "candidate_success": bool(result.get("success", False)),
                "candidate_terminal_reason": str(result.get("terminal_reason", "")),
                "candidate_margin": candidate_margin,
                "margin_improvement": (
                    candidate_margin - baseline_margin
                    if np.isfinite(candidate_margin) and np.isfinite(baseline_margin)
                    else float("nan")
                ),
                "base_steer": float(base_action[0]),
                "base_throttle": float(base_action[1]),
                "base_brake": float(base_action[2]),
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

        target = select_recovery_target(
            row=row,
            row_index=int(row_index),
            base_action=base_action,
            rejected_anchor_action=rejected_anchor_action,
            baseline=baseline,
            candidate_rows=row_candidate_rows,
            min_margin_improvement=min_margin_improvement,
            include_base_retention=include_base_retention,
        )
        if target is None:
            best_any = _best_any_candidate(row_candidate_rows)
            skipped_rows.append(
                {
                    "row_id": int(row_index),
                    "case_id": str(row.get("case_id", old_key_case_id(row))),
                    "skip_reason": "no_recovery_candidate",
                    "best_margin_improvement": best_any.get("margin_improvement", float("nan")),
                    "best_rejection_reason": best_any.get("rejection_reason", ""),
                }
            )
            continue
        observations.append(np.asarray(relocated.observation, dtype=np.float32).copy())
        preferred_hiddens.append(_hidden_array(model, preferred_hidden, resolved_device))
        rejected_hiddens.append(_hidden_array(model, rejected_hidden, resolved_device))
        target_rows.append(target)

    write_csv_rows(run_dir / "recovery_candidates.csv", candidate_rows)
    target_csv_rows = [
        {key: value for key, value in row.items() if key not in {"recovery_action", "rejected_anchor_action"}}
        for row in target_rows
    ]
    write_csv_rows(run_dir / "old_key_recovery_targets.csv", target_csv_rows)
    write_csv_rows(run_dir / "skipped_rows.csv", skipped_rows)

    recovery_npz = run_dir / "old_key_recovery_corpus.npz"
    _write_old_key_recovery_corpus(
        output_npz=recovery_npz,
        observations=observations,
        preferred_hidden=preferred_hiddens,
        rejected_hidden=rejected_hiddens,
        targets=target_rows,
    )
    recovery = load_old_key_recovery_snippets(
        recovery_npz,
        device=resolved_device,
        obs_dim=int(model.obs_dim),
        hidden_size=int(model.actor_mean.in_features),
        act_dim=int(model.act_dim),
    )
    candidate_frame = pd.DataFrame(candidate_rows)
    target_frame = pd.DataFrame(target_csv_rows)
    accepted_improvements = (
        target_frame.loc[target_frame["accepted_recovery"].astype(bool), "margin_improvement"].astype(float)
        if not target_frame.empty
        else pd.Series(dtype=float)
    )
    summary = {
        "run_type": "old_key_local_recovery_targets",
        "checkpoint": checkpoint,
        "reference_manifest": reference_manifest,
        "source_rows_csv": source_rows_csv,
        "device": str(resolved_device),
        "rows_requested": int(len(rows)),
        "candidate_rollouts": int(len(candidate_rows)),
        "candidate_grid": {
            "steer_deltas": steer_deltas,
            "throttle_deltas": throttle_deltas,
            "brake_deltas": brake_deltas,
        },
        "min_margin_improvement": float(min_margin_improvement),
        "max_action_l2": float(max_action_l2),
        "max_continuation_steps": int(max_continuation_steps),
        "include_base_retention": bool(include_base_retention),
        "recovery_rows": int(recovery.size),
        "accepted_recovery_rows": int(target_frame["accepted_recovery"].astype(bool).sum()) if not target_frame.empty else 0,
        "base_retention_rows": int((target_frame["recovery_status"].astype(str) == "base_retention").sum()) if not target_frame.empty else 0,
        "skipped_rows": int(len(skipped_rows)),
        "accepted_margin_improvement_min": float(accepted_improvements.min()) if len(accepted_improvements) else float("nan"),
        "accepted_margin_improvement_mean": float(accepted_improvements.mean()) if len(accepted_improvements) else float("nan"),
        "accepted_margin_improvement_max": float(accepted_improvements.max()) if len(accepted_improvements) else float("nan"),
        "candidate_margin_improvement_max": (
            float(candidate_frame["margin_improvement"].astype(float).max()) if not candidate_frame.empty else float("nan")
        ),
        "old_key_recovery_corpus_npz": recovery_npz,
        "old_key_recovery_targets_csv": run_dir / "old_key_recovery_targets.csv",
        "recovery_candidates_csv": run_dir / "recovery_candidates.csv",
        "skipped_rows_csv": run_dir / "skipped_rows.csv",
        "contract": {
            "rows": int(recovery.size),
            "obs_dim": int(model.obs_dim),
            "hidden_dim": int(model.actor_mean.in_features),
            "act_dim": int(model.act_dim),
        },
        "target_source": "replay_selected_local_action_search",
        "actor_inputs_changed": False,
        "ppo_or_actor_update_run": False,
        "checkpoint_promoted": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--reference-manifest", type=Path, required=True)
    parser.add_argument("--source-rows-csv", type=Path, required=True)
    parser.add_argument("--steer-deltas", type=parse_float_list, default=(-0.04, -0.02, -0.01, 0.0, 0.01, 0.02, 0.04))
    parser.add_argument("--throttle-deltas", type=parse_float_list, default=(-0.02, 0.0, 0.02))
    parser.add_argument("--brake-deltas", type=parse_float_list, default=(-0.04, -0.02, 0.0, 0.02, 0.04))
    parser.add_argument("--min-margin-improvement", type=float, default=1e-5)
    parser.add_argument("--max-action-l2", type=float, default=0.08)
    parser.add_argument("--max-continuation-steps", type=int, default=40)
    parser.add_argument("--include-base-retention", action="store_true")
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="old_key_local_recovery_targets")
    summary = export_old_key_local_recovery_targets(
        checkpoint=args.checkpoint,
        reference_manifest=args.reference_manifest,
        source_rows_csv=args.source_rows_csv,
        run_dir=run_dir,
        steer_deltas=args.steer_deltas,
        throttle_deltas=args.throttle_deltas,
        brake_deltas=args.brake_deltas,
        min_margin_improvement=args.min_margin_improvement,
        max_action_l2=args.max_action_l2,
        max_continuation_steps=args.max_continuation_steps,
        include_base_retention=bool(args.include_base_retention),
        max_rows=int(args.max_rows),
        device=args.device,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
