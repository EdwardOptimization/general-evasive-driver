"""Mine matched visible-state pairs with hidden-dynamics action divergence."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.env import AutoDriftEnv, DriftEnvConfig, OBSTACLE_SLOT_DIM, ROAD_POINT_DIM
from autodrift.evaluate import load_env_config
from autodrift.hidden_swap_gate import (
    DecisionSnapshot,
    collect_decision_snapshot,
    hidden_state_distance,
    response_feature_indices,
)
from autodrift.paired_perturbation_gate import (
    condition_config,
    load_seed_csv,
    parse_randomization_overrides,
    parse_range,
)
from autodrift.train_ppo import HUMAN_VIEW_OBS_DIM, ActorCritic


def visible_observation_distances(
    source_observation: np.ndarray,
    paired_observation: np.ndarray,
    env_config: DriftEnvConfig,
    *,
    visible_dim: int = HUMAN_VIEW_OBS_DIM,
) -> dict[str, float]:
    source = np.asarray(source_observation, dtype=np.float32)
    paired = np.asarray(paired_observation, dtype=np.float32)
    if source.shape != paired.shape:
        raise ValueError(f"cannot compare observation shapes {source.shape} and {paired.shape}")
    if len(source) < visible_dim:
        raise ValueError(f"observation has {len(source)} values, expected at least {visible_dim}")
    source_visible = source[:visible_dim]
    paired_visible = paired[:visible_dim]
    response_indices = np.asarray(response_feature_indices(env_config, visible_dim), dtype=np.int64)
    response_mask = np.zeros(visible_dim, dtype=bool)
    response_mask[response_indices] = True
    diff = source_visible - paired_visible
    distances = {
        "visible_observation_distance": float(np.linalg.norm(diff)),
        "visible_response_distance": float(np.linalg.norm(diff[response_mask])),
        "visible_context_distance": float(np.linalg.norm(diff[~response_mask])),
    }
    response_end = int(np.max(response_indices)) + 1 if len(response_indices) else 0
    road_start = response_end
    road_end = min(road_start + 2 * env_config.road_lookahead_count * ROAD_POINT_DIM, visible_dim)
    obstacle_start = road_end
    obstacle_end = min(obstacle_start + env_config.obstacle_slots * OBSTACLE_SLOT_DIM, visible_dim)
    road_diff = diff[road_start:road_end]
    obstacle_diff = diff[obstacle_start:obstacle_end]
    distances["visible_road_context_distance"] = float(np.linalg.norm(road_diff))
    distances["visible_obstacle_context_distance"] = float(np.linalg.norm(obstacle_diff))
    if len(obstacle_diff) >= OBSTACLE_SLOT_DIM:
        slots = obstacle_diff.reshape((-1, OBSTACLE_SLOT_DIM))
        distances["visible_obstacle_geometry_distance"] = float(np.linalg.norm(slots[:, [0, 1, 2, 5, 6]]))
        distances["visible_obstacle_rel_velocity_distance"] = float(np.linalg.norm(slots[:, [3, 4]]))
    else:
        distances["visible_obstacle_geometry_distance"] = float("nan")
        distances["visible_obstacle_rel_velocity_distance"] = float("nan")
    return distances


def hybrid_privileged_observation(
    source_observation: np.ndarray,
    paired_observation: np.ndarray,
    *,
    visible_dim: int = HUMAN_VIEW_OBS_DIM,
) -> np.ndarray:
    source = np.asarray(source_observation, dtype=np.float32)
    paired = np.asarray(paired_observation, dtype=np.float32)
    if source.shape != paired.shape:
        raise ValueError(f"cannot build hybrid observation from shapes {source.shape} and {paired.shape}")
    hybrid = source.copy()
    if len(hybrid) > visible_dim:
        hybrid[visible_dim:] = paired[visible_dim:]
    return hybrid


def _action_from_snapshot(model: ActorCritic, observation: np.ndarray, hidden: Any) -> np.ndarray:
    action, _, _, _ = model.act_recurrent(observation, hidden, deterministic=True)
    return np.asarray(action, dtype=np.float32)


def _action_distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(np.asarray(a, dtype=np.float32) - np.asarray(b, dtype=np.float32)))


def _finite_nanmax(values: list[float]) -> float:
    finite = [float(value) for value in values if np.isfinite(float(value))]
    return max(finite) if finite else float("nan")


def _privileged_tail_distance(
    source_observation: np.ndarray,
    paired_observation: np.ndarray,
    *,
    visible_dim: int = HUMAN_VIEW_OBS_DIM,
) -> float:
    source = np.asarray(source_observation, dtype=np.float32)
    paired = np.asarray(paired_observation, dtype=np.float32)
    if len(source) <= visible_dim:
        return float("nan")
    return float(np.linalg.norm(source[visible_dim:] - paired[visible_dim:]))


def build_matched_action_row(
    seed: int,
    nominal: DecisionSnapshot | None,
    perturbed: DecisionSnapshot | None,
    model: ActorCritic,
    env_config: DriftEnvConfig,
    *,
    max_visible_distance: float,
    max_response_distance: float | None = None,
    max_context_distance: float | None = None,
    min_action_distance: float,
    visible_dim: int = HUMAN_VIEW_OBS_DIM,
) -> dict[str, Any]:
    if nominal is None or perturbed is None:
        if nominal is None and perturbed is None:
            pair_status = "missing_both"
        elif nominal is None:
            pair_status = "missing_nominal"
        else:
            pair_status = "missing_perturbed"
        return {
            "seed": int(seed),
            "pair_status": pair_status,
            "accepted_visible_match": False,
            "accepted_visible_total": False,
            "accepted_response_match": False,
            "accepted_context_match": False,
            "accepted_action_divergent": False,
            "accepted_paired_action_divergent": False,
            "accepted_wrong_history_divergent": False,
            "accepted_privileged_packet_divergent": False,
        }

    distances = visible_observation_distances(nominal.observation, perturbed.observation, env_config, visible_dim=visible_dim)
    accepted_visible_total = distances["visible_observation_distance"] <= float(max_visible_distance)
    accepted_response = (
        True
        if max_response_distance is None
        else distances["visible_response_distance"] <= float(max_response_distance)
    )
    accepted_context = (
        True if max_context_distance is None else distances["visible_context_distance"] <= float(max_context_distance)
    )
    accepted_visible = accepted_visible_total and accepted_response and accepted_context

    nominal_action = _action_from_snapshot(model, nominal.observation, nominal.hidden)
    perturbed_action = _action_from_snapshot(model, perturbed.observation, perturbed.hidden)
    nominal_wrong_history = _action_from_snapshot(model, nominal.observation, perturbed.hidden)
    perturbed_wrong_history = _action_from_snapshot(model, perturbed.observation, nominal.hidden)
    nominal_swapped_privileged = _action_from_snapshot(
        model,
        hybrid_privileged_observation(nominal.observation, perturbed.observation, visible_dim=visible_dim),
        nominal.hidden,
    )
    perturbed_swapped_privileged = _action_from_snapshot(
        model,
        hybrid_privileged_observation(perturbed.observation, nominal.observation, visible_dim=visible_dim),
        perturbed.hidden,
    )

    paired_action_distance = _action_distance(nominal_action, perturbed_action)
    nominal_wrong_history_distance = _action_distance(nominal_action, nominal_wrong_history)
    perturbed_wrong_history_distance = _action_distance(perturbed_action, perturbed_wrong_history)
    nominal_privileged_packet_distance = _action_distance(nominal_action, nominal_swapped_privileged)
    perturbed_privileged_packet_distance = _action_distance(perturbed_action, perturbed_swapped_privileged)
    max_wrong_history_action_distance = max(nominal_wrong_history_distance, perturbed_wrong_history_distance)
    max_privileged_packet_action_distance = max(
        nominal_privileged_packet_distance,
        perturbed_privileged_packet_distance,
    )
    max_action_distance = _finite_nanmax(
        [
            paired_action_distance,
            max_wrong_history_action_distance,
            max_privileged_packet_action_distance,
        ]
    )
    accepted_action = bool(accepted_visible and max_action_distance >= float(min_action_distance))
    accepted_paired_action = bool(accepted_visible and paired_action_distance >= float(min_action_distance))
    accepted_wrong_history = bool(accepted_visible and max_wrong_history_action_distance >= float(min_action_distance))
    accepted_privileged_packet = bool(
        accepted_visible and max_privileged_packet_action_distance >= float(min_action_distance)
    )
    visibility_penalty = distances["visible_observation_distance"] / max(float(max_visible_distance), 1e-9)
    action_divergence_score = max_action_distance - 0.25 * visibility_penalty

    return {
        "seed": int(seed),
        "pair_status": "paired",
        "accepted_visible_match": bool(accepted_visible),
        "accepted_visible_total": bool(accepted_visible_total),
        "accepted_response_match": bool(accepted_response),
        "accepted_context_match": bool(accepted_context),
        "accepted_action_divergent": accepted_action,
        "accepted_paired_action_divergent": accepted_paired_action,
        "accepted_wrong_history_divergent": accepted_wrong_history,
        "accepted_privileged_packet_divergent": accepted_privileged_packet,
        "nominal_step": int(nominal.step),
        "perturbed_step": int(perturbed.step),
        "nominal_obstacle_distance": float(nominal.obstacle_distance),
        "perturbed_obstacle_distance": float(perturbed.obstacle_distance),
        "nominal_mu": float(nominal.info.get("mu", float("nan"))),
        "perturbed_mu": float(perturbed.info.get("mu", float("nan"))),
        "nominal_brake_scale": float(nominal.info.get("brake_scale", float("nan"))),
        "perturbed_brake_scale": float(perturbed.info.get("brake_scale", float("nan"))),
        "nominal_steer_tau_scale": float(nominal.info.get("steer_tau_scale", float("nan"))),
        "perturbed_steer_tau_scale": float(perturbed.info.get("steer_tau_scale", float("nan"))),
        "hidden_state_distance": hidden_state_distance(nominal.hidden, perturbed.hidden),
        "privileged_tail_distance": _privileged_tail_distance(nominal.observation, perturbed.observation, visible_dim=visible_dim),
        "paired_action_distance": paired_action_distance,
        "nominal_wrong_history_action_distance": nominal_wrong_history_distance,
        "perturbed_wrong_history_action_distance": perturbed_wrong_history_distance,
        "nominal_privileged_packet_action_distance": nominal_privileged_packet_distance,
        "perturbed_privileged_packet_action_distance": perturbed_privileged_packet_distance,
        "max_wrong_history_action_distance": max_wrong_history_action_distance,
        "max_privileged_packet_action_distance": max_privileged_packet_action_distance,
        "max_action_distance": max_action_distance,
        "action_divergence_score": action_divergence_score,
        "nominal_steer": float(nominal_action[0]),
        "nominal_throttle": float(nominal_action[1]),
        "nominal_brake": float(nominal_action[2]),
        "perturbed_steer": float(perturbed_action[0]),
        "perturbed_throttle": float(perturbed_action[1]),
        "perturbed_brake": float(perturbed_action[2]),
        **distances,
    }


def summarize_matched_actions(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(
            [
                {
                    "pairs": 0,
                    "accepted_visible_matches": 0,
                    "accepted_action_divergent_pairs": 0,
                    "visible_match_rate": 0.0,
                    "action_divergent_rate": 0.0,
                    "max_action_distance_mean": 0.0,
                    "action_divergence_score_max": 0.0,
                }
            ]
        )
    accepted_visible = frame["accepted_visible_match"].astype(bool)
    accepted_action = frame["accepted_action_divergent"].astype(bool)
    accepted_paired_action = (
        frame["accepted_paired_action_divergent"].astype(bool)
        if "accepted_paired_action_divergent" in frame
        else accepted_action
    )
    accepted_wrong_history = (
        frame["accepted_wrong_history_divergent"].astype(bool)
        if "accepted_wrong_history_divergent" in frame
        else accepted_action
    )
    accepted_privileged_packet = (
        frame["accepted_privileged_packet_divergent"].astype(bool)
        if "accepted_privileged_packet_divergent" in frame
        else accepted_action
    )
    paired_rows = (
        int((frame["pair_status"].astype(str) == "paired").sum())
        if "pair_status" in frame
        else int(len(frame))
    )
    return pd.DataFrame(
        [
            {
                "pairs": int(len(frame)),
                "paired_rows": paired_rows,
                "accepted_visible_matches": int(accepted_visible.sum()),
                "accepted_action_divergent_pairs": int(accepted_action.sum()),
                "accepted_paired_action_divergent_pairs": int(accepted_paired_action.sum()),
                "accepted_wrong_history_divergent_pairs": int(accepted_wrong_history.sum()),
                "accepted_privileged_packet_divergent_pairs": int(accepted_privileged_packet.sum()),
                "visible_match_rate": float(accepted_visible.mean()),
                "action_divergent_rate": float(accepted_action.mean()),
                "privileged_packet_divergent_rate": float(accepted_privileged_packet.mean()),
                "visible_observation_distance_mean": float(frame["visible_observation_distance"].mean()),
                "visible_context_distance_mean": float(frame["visible_context_distance"].mean()),
                "hidden_state_distance_mean": float(frame["hidden_state_distance"].mean()),
                "privileged_tail_distance_mean": float(frame["privileged_tail_distance"].mean()),
                "paired_action_distance_mean": float(frame["paired_action_distance"].mean()),
                "wrong_history_action_distance_mean": float(
                    0.5
                    * (
                        frame["nominal_wrong_history_action_distance"].mean()
                        + frame["perturbed_wrong_history_action_distance"].mean()
                    )
                ),
                "privileged_packet_action_distance_mean": float(
                    0.5
                    * (
                        frame["nominal_privileged_packet_action_distance"].mean()
                        + frame["perturbed_privileged_packet_action_distance"].mean()
                    )
                ),
                "max_action_distance_mean": float(frame["max_action_distance"].mean()),
                "max_action_distance_max": float(frame["max_action_distance"].max()),
                "action_divergence_score_max": float(frame["action_divergence_score"].max()),
            }
        ]
    )


def select_action_divergent_corpus(frame: pd.DataFrame, *, top_k: int) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    selected = frame[frame["accepted_action_divergent"].astype(bool)].copy()
    selected = selected.sort_values(["action_divergence_score", "max_action_distance", "seed"], ascending=[False, False, True])
    return selected.head(max(0, int(top_k))).reset_index(drop=True)


def run_matched_action_corpus(
    *,
    model: ActorCritic,
    base_config: DriftEnvConfig,
    seeds: list[int],
    nominal_friction_mu_range: tuple[float, float],
    perturbed_friction_mu_range: tuple[float, float],
    nominal_randomization: dict[str, tuple[float, float]],
    perturbed_randomization: dict[str, tuple[float, float]],
    target_obstacle_distance: float,
    min_probe_steps: int,
    max_probe_steps: int,
    require_friction_step: bool,
    min_hidden_updates_after_friction: int,
    max_visible_distance: float,
    max_response_distance: float | None,
    max_context_distance: float | None,
    min_action_distance: float,
    top_k: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    configs = {
        "nominal": condition_config(base_config, nominal_friction_mu_range, nominal_randomization),
        "perturbed": condition_config(base_config, perturbed_friction_mu_range, perturbed_randomization),
    }
    rows: list[dict[str, Any]] = []
    for seed in seeds:
        snapshots = {
            condition: collect_decision_snapshot(
                model,
                env_config,
                condition,
                seed,
                target_obstacle_distance=target_obstacle_distance,
                min_probe_steps=min_probe_steps,
                max_probe_steps=max_probe_steps,
                require_friction_step=require_friction_step,
                min_hidden_updates_after_friction=min_hidden_updates_after_friction,
            )
            for condition, env_config in configs.items()
        }
        rows.append(
            build_matched_action_row(
                seed,
                snapshots["nominal"],
                snapshots["perturbed"],
                model,
                configs["nominal"],
                max_visible_distance=max_visible_distance,
                max_response_distance=max_response_distance,
                max_context_distance=max_context_distance,
                min_action_distance=min_action_distance,
            )
        )
    pairs = pd.DataFrame(rows)
    corpus = select_action_divergent_corpus(pairs, top_k=top_k)
    summary = summarize_matched_actions(pairs)
    return pairs, corpus, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine matched visible-state action-divergent hidden-dynamics pairs.")
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=80)
    parser.add_argument("--seed", type=int, default=6800)
    parser.add_argument("--seed-csv", type=Path, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--nominal-friction-mu-range", type=parse_range, default=(0.85, 1.15))
    parser.add_argument("--perturbed-friction-mu-range", type=parse_range, default=(0.25, 0.35))
    parser.add_argument("--nominal-randomization", action="append", default=[])
    parser.add_argument("--perturbed-randomization", action="append", default=[])
    parser.add_argument("--target-obstacle-distance", type=float, default=12.0)
    parser.add_argument("--min-probe-steps", type=int, default=10)
    parser.add_argument("--max-probe-steps", type=int, default=180)
    parser.add_argument("--allow-pre-friction-snapshot", action="store_true")
    parser.add_argument("--min-hidden-updates-after-friction", type=int, default=2)
    parser.add_argument("--max-visible-distance", type=float, default=0.75)
    parser.add_argument("--max-response-distance", type=float, default=0.25)
    parser.add_argument("--max-context-distance", type=float, default=0.05)
    parser.add_argument("--min-action-distance", type=float, default=0.05)
    parser.add_argument("--top-k", type=int, default=40)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="matched_action_corpus", seed=args.seed)
    run_dir.mkdir(parents=True, exist_ok=True)

    base_config = load_env_config(args.env_config)
    target_obs_dim = int(AutoDriftEnv(base_config).observation_space.shape[0])
    model, _ = load_actor_critic_checkpoint(args.checkpoint, device=args.device, obs_dim=target_obs_dim)
    if not model.is_online_recurrent:
        raise ValueError("matched action-divergent corpus mining requires an online recurrent checkpoint")
    seeds = load_seed_csv(args.seed_csv) if args.seed_csv is not None else [args.seed + index for index in range(args.episodes)]
    nominal_randomization = parse_randomization_overrides(args.nominal_randomization)
    perturbed_randomization = parse_randomization_overrides(args.perturbed_randomization)
    pairs, corpus, summary = run_matched_action_corpus(
        model=model,
        base_config=base_config,
        seeds=seeds,
        nominal_friction_mu_range=args.nominal_friction_mu_range,
        perturbed_friction_mu_range=args.perturbed_friction_mu_range,
        nominal_randomization=nominal_randomization,
        perturbed_randomization=perturbed_randomization,
        target_obstacle_distance=args.target_obstacle_distance,
        min_probe_steps=args.min_probe_steps,
        max_probe_steps=args.max_probe_steps,
        require_friction_step=not args.allow_pre_friction_snapshot,
        min_hidden_updates_after_friction=args.min_hidden_updates_after_friction,
        max_visible_distance=args.max_visible_distance,
        max_response_distance=args.max_response_distance,
        max_context_distance=args.max_context_distance,
        min_action_distance=args.min_action_distance,
        top_k=args.top_k,
    )

    pairs_csv = run_dir / "matched_pairs.csv"
    corpus_csv = run_dir / "action_divergent_snippets.csv"
    summary_csv = run_dir / "summary.csv"
    pairs.to_csv(pairs_csv, index=False)
    corpus.to_csv(corpus_csv, index=False)
    summary.to_csv(summary_csv, index=False)
    write_json(
        run_dir / "summary.json",
        summary.iloc[0].to_dict() if len(summary) else {},
    )
    write_json(
        run_dir / "manifest.json",
        {
            "run_type": "matched_action_corpus",
            "env_config": args.env_config,
            "checkpoint": args.checkpoint,
            "episodes": len(seeds),
            "seed": args.seed,
            "seed_csv": args.seed_csv,
            "device": args.device,
            "nominal_friction_mu_range": args.nominal_friction_mu_range,
            "perturbed_friction_mu_range": args.perturbed_friction_mu_range,
            "nominal_randomization": nominal_randomization,
            "perturbed_randomization": perturbed_randomization,
            "target_obstacle_distance": args.target_obstacle_distance,
            "min_probe_steps": args.min_probe_steps,
            "max_probe_steps": args.max_probe_steps,
            "require_friction_step": not args.allow_pre_friction_snapshot,
            "min_hidden_updates_after_friction": args.min_hidden_updates_after_friction,
            "max_visible_distance": args.max_visible_distance,
            "max_response_distance": args.max_response_distance,
            "max_context_distance": args.max_context_distance,
            "min_action_distance": args.min_action_distance,
            "top_k": args.top_k,
            "artifacts": {
                "matched_pairs_csv": pairs_csv,
                "action_divergent_snippets_csv": corpus_csv,
                "summary_csv": summary_csv,
            },
        },
    )
    print(summary.to_string(index=False))
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
