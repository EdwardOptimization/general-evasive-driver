"""Mine outcome-sensitive normal-vs-ablation snippets for recurrent actors."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import load_env_config
from autodrift.hidden_swap_gate import (
    DecisionSnapshot,
    collect_decision_snapshot,
    replay_continuation,
)
from autodrift.outcome_sensitive_corpus import parse_float_list
from autodrift.paired_perturbation_gate import load_seed_csv
from autodrift.snapshot_bank_relocation import (
    _outcome_intervention_weight,
    outcome_intervention_arrays,
    outcome_intervention_metadata,
)
from autodrift.train_ppo import ActorCritic


OUTCOME_VARIANTS = ("reset", "zero_response")


def _hidden_array(model: ActorCritic, hidden: torch.Tensor | None) -> np.ndarray:
    if hidden is None:
        hidden = model.initial_hidden(1)
    return hidden.detach().cpu().numpy().reshape(-1).astype(np.float32)


def _initial_hidden_array(model: ActorCritic) -> np.ndarray:
    return model.initial_hidden(1).detach().cpu().numpy().reshape(-1).astype(np.float32)


def _finite_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _variant_row(rows: list[dict[str, Any]], variant: str) -> dict[str, Any]:
    for row in rows:
        if row.get("variant") == variant:
            return row
    raise ValueError(f"missing replay variant {variant!r}")


def build_history_ablation_rows(
    *,
    snapshot: DecisionSnapshot,
    model: ActorCritic,
    env_config: DriftEnvConfig,
    max_continuation_steps: int | None,
    min_margin_gap: float,
    min_normal_margin: float | None,
    max_normal_margin: float | None,
    require_normal_success: bool,
    outcome_export_min_margin_gap: float,
    outcome_export_boundary_margin_scale: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    normal, normal_actions = replay_continuation(
        model,
        snapshot,
        env_config=env_config,
        variant="normal",
        max_continuation_steps=max_continuation_steps,
    )
    normal_first_action = np.array(
        [normal["first_steer"], normal["first_throttle"], normal["first_brake"]],
        dtype=np.float32,
    )
    replays: list[dict[str, Any]] = [
        {
            "seed": int(snapshot.seed),
            "target_obstacle_distance": float(snapshot.obstacle_distance),
            "source_step": int(snapshot.step),
            "variant": "normal",
            **normal,
        }
    ]
    for variant in OUTCOME_VARIANTS:
        replay, _ = replay_continuation(
            model,
            snapshot,
            env_config=env_config,
            variant=variant,
            normal_first_action=normal_first_action,
            normal_actions=normal_actions,
            max_continuation_steps=max_continuation_steps,
        )
        replays.append(
            {
                "seed": int(snapshot.seed),
                "target_obstacle_distance": float(snapshot.obstacle_distance),
                "source_step": int(snapshot.step),
                "variant": variant,
                **replay,
            }
        )

    normal_row = _variant_row(replays, "normal")
    normal_success = bool(normal_row.get("success", False))
    normal_margin = _finite_float(normal_row.get("min_clearance_margin", float("nan")))
    normal_margin_ok = True
    if min_normal_margin is not None and np.isfinite(normal_margin):
        normal_margin_ok = normal_margin_ok and normal_margin >= float(min_normal_margin)
    if max_normal_margin is not None and np.isfinite(normal_margin):
        normal_margin_ok = normal_margin_ok and normal_margin <= float(max_normal_margin)
    normal_success_ok = normal_success or not require_normal_success

    rows: list[dict[str, Any]] = []
    examples: list[dict[str, Any]] = []
    for variant in OUTCOME_VARIANTS:
        intervention = _variant_row(replays, variant)
        intervention_success = bool(intervention.get("success", False))
        intervention_margin = _finite_float(intervention.get("min_clearance_margin", float("nan")))
        success_drop = bool(normal_success and not intervention_success)
        margin_gap = (
            normal_margin - intervention_margin
            if np.isfinite(normal_margin) and np.isfinite(intervention_margin)
            else float("nan")
        )
        margin_gap_accept = bool(np.isfinite(margin_gap) and margin_gap >= float(min_margin_gap))
        accepted = bool(normal_success_ok and normal_margin_ok and (success_drop or margin_gap_accept))
        row = {
            "seed": int(snapshot.seed),
            "source_step": int(snapshot.step),
            "target_obstacle_distance": float(snapshot.obstacle_distance),
            "variant": variant,
            "accepted_outcome_sensitive": accepted,
            "normal_success": normal_success,
            "intervention_success": intervention_success,
            "success_drop": success_drop,
            "normal_margin": normal_margin,
            "intervention_margin": intervention_margin,
            "margin_gap": margin_gap,
            "normal_return": _finite_float(normal_row.get("return", float("nan"))),
            "intervention_return": _finite_float(intervention.get("return", float("nan"))),
            "margin_gap_accept": margin_gap_accept,
            "normal_terminal_reason": str(normal_row.get("terminal_reason", "")),
            "intervention_terminal_reason": str(intervention.get("terminal_reason", "")),
            "first_action_distance": _finite_float(intervention.get("first_action_distance", float("nan"))),
            "action_trajectory_distance_mean": _finite_float(
                intervention.get("action_trajectory_distance_mean", float("nan"))
            ),
        }
        rows.append(row)

        if variant != "reset":
            continue
        weight = _outcome_intervention_weight(
            normal_margin,
            intervention_margin,
            normal_success,
            min_margin_gap=outcome_export_min_margin_gap,
            boundary_margin_scale=outcome_export_boundary_margin_scale,
        )
        if weight <= 0.0:
            continue
        examples.append(
            {
                "seed": int(snapshot.seed),
                "source_step": int(snapshot.step),
                "variant": variant,
                "normal_margin": normal_margin,
                "intervention_margin": intervention_margin,
                "margin_gap": margin_gap,
                "weight": float(weight),
                "observation": np.asarray(snapshot.observation, dtype=np.float32).copy(),
                "preferred_hidden": _hidden_array(model, snapshot.hidden),
                "rejected_hidden": _initial_hidden_array(model),
                "preferred_action": normal_first_action.copy(),
            }
        )

    return rows, replays, examples


def summarize_history_ablation(frame: pd.DataFrame, outcome_metadata: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(
            [
                {
                    "candidates": 0,
                    "accepted_outcome_sensitive_rows": 0,
                    "reset_accepted_rows": 0,
                    "zero_response_accepted_rows": 0,
                    "outcome_intervention_snippets": 0,
                    "outcome_intervention_weight_sum": 0.0,
                    "margin_gap_max": 0.0,
                }
            ]
        )
    accepted = frame["accepted_outcome_sensitive"].fillna(False).astype(bool)
    reset = frame["variant"].astype(str) == "reset"
    zero = frame["variant"].astype(str) == "zero_response"
    margin_gap = frame["margin_gap"].astype(float)
    return pd.DataFrame(
        [
            {
                "candidates": int(len(frame)),
                "accepted_outcome_sensitive_rows": int(accepted.sum()),
                "reset_accepted_rows": int((accepted & reset).sum()),
                "zero_response_accepted_rows": int((accepted & zero).sum()),
                "outcome_intervention_snippets": int(len(outcome_metadata)),
                "outcome_intervention_weight_sum": (
                    float(outcome_metadata["weight"].sum()) if "weight" in outcome_metadata else 0.0
                ),
                "margin_gap_max": float(margin_gap.max()) if len(margin_gap) else 0.0,
            }
        ]
    )


def run_history_ablation_snippets(
    *,
    model: ActorCritic,
    env_config: DriftEnvConfig,
    seeds: list[int],
    target_obstacle_distances: list[float],
    min_probe_steps: int,
    max_probe_steps: int,
    require_friction_step: bool,
    min_hidden_updates_after_friction: int,
    max_continuation_steps: int | None,
    min_margin_gap: float,
    min_normal_margin: float | None,
    max_normal_margin: float | None,
    require_normal_success: bool,
    outcome_export_min_margin_gap: float,
    outcome_export_boundary_margin_scale: float,
    top_k: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, np.ndarray]]:
    rows: list[dict[str, Any]] = []
    replay_rows: list[dict[str, Any]] = []
    examples: list[dict[str, Any]] = []
    for seed in seeds:
        for target_distance in target_obstacle_distances:
            snapshot = collect_decision_snapshot(
                model,
                env_config,
                "normal",
                seed,
                target_obstacle_distance=float(target_distance),
                min_probe_steps=min_probe_steps,
                max_probe_steps=max_probe_steps,
                require_friction_step=require_friction_step,
                min_hidden_updates_after_friction=min_hidden_updates_after_friction,
            )
            if snapshot is None:
                rows.append(
                    {
                        "seed": int(seed),
                        "target_obstacle_distance": float(target_distance),
                        "variant": "missing_snapshot",
                        "accepted_outcome_sensitive": False,
                    }
                )
                continue
            candidate_rows, replays, snippet_examples = build_history_ablation_rows(
                snapshot=snapshot,
                model=model,
                env_config=env_config,
                max_continuation_steps=max_continuation_steps,
                min_margin_gap=min_margin_gap,
                min_normal_margin=min_normal_margin,
                max_normal_margin=max_normal_margin,
                require_normal_success=require_normal_success,
                outcome_export_min_margin_gap=outcome_export_min_margin_gap,
                outcome_export_boundary_margin_scale=outcome_export_boundary_margin_scale,
            )
            for row in candidate_rows:
                row["requested_target_obstacle_distance"] = float(target_distance)
            rows.extend(candidate_rows)
            replay_rows.extend(replays)
            examples.extend(snippet_examples)

    candidates = pd.DataFrame(rows)
    replays = pd.DataFrame(replay_rows)
    accepted = candidates[candidates["accepted_outcome_sensitive"].fillna(False).astype(bool)].copy()
    if len(accepted):
        accepted = accepted.sort_values(["margin_gap", "seed"], ascending=[False, True]).head(max(0, int(top_k)))
    outcome_metadata = outcome_intervention_metadata(examples)
    snippets = outcome_intervention_arrays(examples)
    summary = summarize_history_ablation(candidates, outcome_metadata)
    return candidates, replays, accepted.reset_index(drop=True), summary, outcome_metadata, snippets


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine normal-vs-ablation outcome snippets.")
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=80)
    parser.add_argument("--seed", type=int, default=9600)
    parser.add_argument("--seed-csv", type=Path, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--target-obstacle-distances", type=parse_float_list, default=[8.0, 10.0, 12.0])
    parser.add_argument("--min-probe-steps", type=int, default=10)
    parser.add_argument("--max-probe-steps", type=int, default=180)
    parser.add_argument("--allow-pre-friction-snapshot", action="store_true")
    parser.add_argument("--min-hidden-updates-after-friction", type=int, default=2)
    parser.add_argument("--max-continuation-steps", type=int, default=0)
    parser.add_argument("--min-margin-gap", type=float, default=0.01)
    parser.add_argument("--min-normal-margin", type=float, default=0.0)
    parser.add_argument("--max-normal-margin", type=float, default=None)
    parser.add_argument("--allow-normal-failure", action="store_true")
    parser.add_argument("--outcome-export-min-margin-gap", type=float, default=0.0)
    parser.add_argument("--outcome-export-boundary-margin-scale", type=float, default=0.20)
    parser.add_argument("--top-k", type=int, default=100)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="history_ablation_snippets", seed=args.seed)
    run_dir.mkdir(parents=True, exist_ok=True)
    env_config = load_env_config(args.env_config)
    target_obs_dim = int(AutoDriftEnv(env_config).observation_space.shape[0])
    model, _ = load_actor_critic_checkpoint(args.checkpoint, device=args.device, obs_dim=target_obs_dim)
    if not model.is_online_recurrent:
        raise ValueError("history-ablation snippets require an online recurrent checkpoint")
    seeds = load_seed_csv(args.seed_csv) if args.seed_csv is not None else [args.seed + index for index in range(args.episodes)]
    candidates, replays, corpus, summary, outcome_metadata, outcome_snippets = run_history_ablation_snippets(
        model=model,
        env_config=env_config,
        seeds=seeds,
        target_obstacle_distances=args.target_obstacle_distances,
        min_probe_steps=args.min_probe_steps,
        max_probe_steps=args.max_probe_steps,
        require_friction_step=not args.allow_pre_friction_snapshot,
        min_hidden_updates_after_friction=args.min_hidden_updates_after_friction,
        max_continuation_steps=args.max_continuation_steps,
        min_margin_gap=args.min_margin_gap,
        min_normal_margin=args.min_normal_margin,
        max_normal_margin=args.max_normal_margin,
        require_normal_success=not args.allow_normal_failure,
        outcome_export_min_margin_gap=args.outcome_export_min_margin_gap,
        outcome_export_boundary_margin_scale=args.outcome_export_boundary_margin_scale,
        top_k=args.top_k,
    )

    candidates_csv = run_dir / "history_ablation_candidates.csv"
    replays_csv = run_dir / "replays.csv"
    corpus_csv = run_dir / "history_ablation_outcome_snippets.csv"
    summary_csv = run_dir / "summary.csv"
    outcome_metadata_csv = run_dir / "outcome_intervention_snippets.csv"
    outcome_npz = run_dir / "outcome_intervention_snippets.npz"
    candidates.to_csv(candidates_csv, index=False)
    replays.to_csv(replays_csv, index=False)
    corpus.to_csv(corpus_csv, index=False)
    summary.to_csv(summary_csv, index=False)
    outcome_metadata.to_csv(outcome_metadata_csv, index=False)
    if outcome_snippets:
        np.savez_compressed(outcome_npz, **outcome_snippets)
    write_json(run_dir / "summary.json", summary.iloc[0].to_dict() if len(summary) else {})
    write_json(
        run_dir / "manifest.json",
        {
            "run_type": "history_ablation_snippets",
            "env_config": args.env_config,
            "checkpoint": args.checkpoint,
            "episodes": len(seeds),
            "seed": args.seed,
            "seed_csv": args.seed_csv,
            "device": args.device,
            "target_obstacle_distances": args.target_obstacle_distances,
            "min_probe_steps": args.min_probe_steps,
            "max_probe_steps": args.max_probe_steps,
            "require_friction_step": not args.allow_pre_friction_snapshot,
            "min_hidden_updates_after_friction": args.min_hidden_updates_after_friction,
            "max_continuation_steps": args.max_continuation_steps,
            "min_margin_gap": args.min_margin_gap,
            "min_normal_margin": args.min_normal_margin,
            "max_normal_margin": args.max_normal_margin,
            "require_normal_success": not args.allow_normal_failure,
            "outcome_export_min_margin_gap": args.outcome_export_min_margin_gap,
            "outcome_export_boundary_margin_scale": args.outcome_export_boundary_margin_scale,
            "top_k": args.top_k,
            "artifacts": {
                "history_ablation_candidates_csv": candidates_csv,
                "replays_csv": replays_csv,
                "history_ablation_outcome_snippets_csv": corpus_csv,
                "summary_csv": summary_csv,
                "outcome_intervention_snippets_csv": outcome_metadata_csv,
                "outcome_intervention_snippets_npz": outcome_npz if outcome_snippets else None,
            },
        },
    )
    print(summary.to_string(index=False))
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
