"""Pair active-probe snapshot banks before obstacle relocation."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import load_env_config
from autodrift.hidden_swap_gate import DecisionSnapshot, clone_hidden, hidden_state_distance
from autodrift.matched_action_corpus import visible_observation_distances
from autodrift.outcome_sensitive_corpus import (
    PROBE_STRATEGIES,
    ProbeConfig,
    _float,
    _snapshot_candidate_for_outcome,
    build_outcome_sensitive_row,
    obstacle_override_config,
    parse_float_list,
    parse_float_values,
    probe_action,
    relocate_obstacle_snapshot,
    select_outcome_sensitive_corpus,
    should_probe,
    snapshot_relocation_grid,
    summarize_outcomes,
)
from autodrift.paired_perturbation_gate import (
    condition_config,
    load_seed_csv,
    parse_randomization_overrides,
    parse_range,
)
from autodrift.train_ppo import ActorCritic, HUMAN_VIEW_OBS_DIM


OUTCOME_ARRAY_KEYS = {
    "observation",
    "preferred_hidden",
    "rejected_hidden",
    "preferred_action",
}


def _probe_stats(
    probe_steps: int,
    probe_steer_abs_sum: float,
    probe_brake_sum: float,
) -> dict[str, float | int]:
    return {
        "active_probe_steps": int(probe_steps),
        "active_probe_steer_abs_mean": probe_steer_abs_sum / max(probe_steps, 1) if probe_steps else 0.0,
        "active_probe_brake_mean": probe_brake_sum / max(probe_steps, 1) if probe_steps else 0.0,
    }


def collect_active_probe_snapshot_bank(
    model: ActorCritic,
    env_config: DriftEnvConfig,
    condition: str,
    seed: int,
    *,
    min_probe_steps: int,
    max_probe_steps: int,
    require_friction_step: bool,
    min_hidden_updates_after_friction: int,
    obstacle_distance_range: tuple[float, float],
    stride_steps: int,
    max_snapshots: int,
    probe_config: ProbeConfig,
) -> list[DecisionSnapshot]:
    env = AutoDriftEnv(env_config)
    obs, info = env.reset(seed=seed)
    hidden = None
    bank: list[DecisionSnapshot] = []
    terminated = False
    truncated = False
    probe_steps = 0
    probe_steer_abs_sum = 0.0
    probe_brake_sum = 0.0
    last_collected_step = -10**9
    stride = max(int(stride_steps), 1)
    min_distance, max_distance = obstacle_distance_range

    while not (terminated or truncated):
        step = int(info.get("step", 0))
        if _snapshot_candidate_for_outcome(
            info,
            min_probe_steps,
            require_friction_step,
            min_hidden_updates_after_friction,
        ):
            obstacle_distance = _float(info.get("obstacle_distance", float("nan")))
            in_distance_window = bool(
                np.isfinite(obstacle_distance)
                and float(min_distance) <= obstacle_distance <= float(max_distance)
            )
            if in_distance_window and step - last_collected_step >= stride:
                snapshot_info = dict(info)
                snapshot_info["active_probe_strategy"] = probe_config.strategy
                snapshot_info.update(_probe_stats(probe_steps, probe_steer_abs_sum, probe_brake_sum))
                bank.append(
                    DecisionSnapshot(
                        condition=condition,
                        seed=seed,
                        step=step,
                        observation=np.asarray(obs, dtype=np.float32).copy(),
                        hidden=clone_hidden(hidden),
                        env=copy.deepcopy(env),
                        info=snapshot_info,
                        obstacle_distance=float(obstacle_distance),
                        snapshot_score=0.0,
                    )
                )
                last_collected_step = step
                if len(bank) >= int(max_snapshots):
                    break
        if step >= max_probe_steps:
            break
        policy_action, _, _, next_hidden = model.act_recurrent(obs, hidden, deterministic=True)
        hidden = next_hidden
        if should_probe(info, probe_config):
            action = probe_action(probe_config.strategy, step, probe_config)
            probe_steps += 1
            probe_steer_abs_sum += abs(float(action[0]))
            probe_brake_sum += max((float(action[2]) + 1.0) * 0.5, 0.0)
        else:
            action = policy_action
        obs, _, terminated, truncated, info = env.step(action)
    return bank


def _hidden_array(model: ActorCritic, hidden: Any) -> np.ndarray:
    if hidden is None:
        hidden = model.initial_hidden(1)
    return hidden.detach().cpu().numpy().reshape(-1).astype(np.float32)


def _outcome_intervention_weight(
    normal_margin: float,
    wrong_margin: float,
    normal_success: bool,
    *,
    min_margin_gap: float,
    boundary_margin_scale: float,
) -> float:
    if not normal_success:
        return 0.0
    if not (np.isfinite(normal_margin) and np.isfinite(wrong_margin)):
        return 0.0
    margin_gap = float(normal_margin) - float(wrong_margin)
    if margin_gap <= float(min_margin_gap):
        return 0.0
    boundary_scale = max(float(boundary_margin_scale), 1e-6)
    boundary_weight = boundary_scale / (boundary_scale + max(float(normal_margin), 0.0))
    return float(margin_gap * boundary_weight)


def append_outcome_intervention_example(
    examples: list[dict[str, Any]],
    *,
    model: ActorCritic,
    source: DecisionSnapshot,
    paired: DecisionSnapshot,
    row: dict[str, Any],
    source_prefix: str,
    min_margin_gap: float,
    boundary_margin_scale: float,
) -> None:
    normal_margin = float(row.get(f"{source_prefix}_normal_margin", float("nan")))
    wrong_margin = float(row.get(f"{source_prefix}_wrong_history_margin", float("nan")))
    normal_success = bool(row.get(f"{source_prefix}_normal_success", False))
    weight = _outcome_intervention_weight(
        normal_margin,
        wrong_margin,
        normal_success,
        min_margin_gap=min_margin_gap,
        boundary_margin_scale=boundary_margin_scale,
    )
    if weight <= 0.0:
        return
    preferred_action, _, _, _ = model.act_recurrent(source.observation, source.hidden, deterministic=True)
    examples.append(
        {
            "seed": int(source.seed),
            "source_condition": source_prefix,
            "source_step": int(source.step),
            "paired_step": int(paired.step),
            "normal_margin": normal_margin,
            "wrong_history_margin": wrong_margin,
            "margin_gap": normal_margin - wrong_margin,
            "weight": float(weight),
            "observation": np.asarray(source.observation, dtype=np.float32).copy(),
            "preferred_hidden": _hidden_array(model, source.hidden),
            "rejected_hidden": _hidden_array(model, paired.hidden),
            "preferred_action": np.asarray(preferred_action, dtype=np.float32).copy(),
        }
    )


def outcome_intervention_arrays(examples: list[dict[str, Any]]) -> dict[str, np.ndarray]:
    if not examples:
        return {}
    return {
        "observation": np.stack([example["observation"] for example in examples]).astype(np.float32),
        "preferred_hidden": np.stack([example["preferred_hidden"] for example in examples]).astype(np.float32),
        "rejected_hidden": np.stack([example["rejected_hidden"] for example in examples]).astype(np.float32),
        "preferred_action": np.stack([example["preferred_action"] for example in examples]).astype(np.float32),
        "weight": np.asarray([example["weight"] for example in examples], dtype=np.float32),
    }


def outcome_intervention_metadata(examples: list[dict[str, Any]]) -> pd.DataFrame:
    rows = [
        {key: value for key, value in example.items() if key not in OUTCOME_ARRAY_KEYS}
        for example in examples
    ]
    return pd.DataFrame(rows)


def pair_snapshot_banks(
    nominal_bank: list[DecisionSnapshot],
    perturbed_bank: list[DecisionSnapshot],
    env_config: DriftEnvConfig,
    *,
    max_pairs: int,
    max_pre_visible_distance: float | None = None,
    max_pre_response_distance: float | None = None,
    max_pre_context_distance: float | None = None,
    visible_dim: int = HUMAN_VIEW_OBS_DIM,
) -> list[tuple[dict[str, Any], DecisionSnapshot, DecisionSnapshot]]:
    pairs: list[tuple[dict[str, Any], DecisionSnapshot, DecisionSnapshot]] = []
    for nominal in nominal_bank:
        for perturbed in perturbed_bank:
            distances = visible_observation_distances(
                nominal.observation,
                perturbed.observation,
                env_config,
                visible_dim=visible_dim,
            )
            if max_pre_visible_distance is not None and distances["visible_observation_distance"] > max_pre_visible_distance:
                continue
            if max_pre_response_distance is not None and distances["visible_response_distance"] > max_pre_response_distance:
                continue
            if max_pre_context_distance is not None and distances["visible_context_distance"] > max_pre_context_distance:
                continue
            score = distances["visible_response_distance"] + distances["visible_context_distance"]
            pairs.append(
                (
                    {
                        "pre_pair_score": float(score),
                        "pre_visible_observation_distance": distances["visible_observation_distance"],
                        "pre_visible_response_distance": distances["visible_response_distance"],
                        "pre_visible_context_distance": distances["visible_context_distance"],
                        "pre_hidden_state_distance": hidden_state_distance(nominal.hidden, perturbed.hidden),
                        "nominal_bank_step": int(nominal.step),
                        "perturbed_bank_step": int(perturbed.step),
                        "nominal_bank_obstacle_distance": float(nominal.obstacle_distance),
                        "perturbed_bank_obstacle_distance": float(perturbed.obstacle_distance),
                    },
                    nominal,
                    perturbed,
                )
            )
    pairs.sort(key=lambda item: (item[0]["pre_pair_score"], item[0]["pre_visible_observation_distance"]))
    return pairs[: max(0, int(max_pairs))]


def run_snapshot_bank_relocation(
    *,
    model: ActorCritic,
    base_config: DriftEnvConfig,
    seeds: list[int],
    nominal_friction_mu_range: tuple[float, float],
    perturbed_friction_mu_range: tuple[float, float],
    nominal_randomization: dict[str, tuple[float, float]],
    perturbed_randomization: dict[str, tuple[float, float]],
    obstacle_perception_reveal_step: int | None,
    obstacle_perception_reveal_distance: float | None,
    bank_obstacle_distance_range: tuple[float, float],
    bank_stride_steps: int,
    bank_max_snapshots: int,
    bank_max_pairs_per_seed: int,
    max_pre_visible_distance: float | None,
    max_pre_response_distance: float | None,
    max_pre_context_distance: float | None,
    snapshot_relocation_distances: list[float],
    snapshot_relocation_lateral_offsets: list[float] | None,
    snapshot_relocation_half_widths: list[float] | None,
    min_probe_steps: int,
    max_probe_steps: int,
    require_friction_step: bool,
    min_hidden_updates_after_friction: int,
    max_visible_distance: float,
    max_response_distance: float | None,
    max_context_distance: float | None,
    min_margin_gap: float,
    min_normal_margin: float | None,
    max_normal_margin: float | None,
    require_normal_success: bool,
    max_continuation_steps: int | None,
    top_k: int,
    probe_config: ProbeConfig,
    outcome_export_min_margin_gap: float,
    outcome_export_boundary_margin_scale: float,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, np.ndarray]]:
    base_config = obstacle_override_config(
        base_config,
        distance_range=None,
        half_width_range=None,
        perception_reveal_step=obstacle_perception_reveal_step,
        perception_reveal_distance=obstacle_perception_reveal_distance,
    )
    configs = {
        "nominal": condition_config(base_config, nominal_friction_mu_range, nominal_randomization),
        "perturbed": condition_config(base_config, perturbed_friction_mu_range, perturbed_randomization),
    }
    relocation_grid = snapshot_relocation_grid(
        snapshot_relocation_distances,
        snapshot_relocation_lateral_offsets,
        snapshot_relocation_half_widths,
    )
    rows: list[dict[str, Any]] = []
    replay_rows: list[dict[str, Any]] = []
    outcome_examples: list[dict[str, Any]] = []
    for seed in seeds:
        banks = {
            condition: collect_active_probe_snapshot_bank(
                model,
                env_config,
                condition,
                seed,
                min_probe_steps=min_probe_steps,
                max_probe_steps=max_probe_steps,
                require_friction_step=require_friction_step,
                min_hidden_updates_after_friction=min_hidden_updates_after_friction,
                obstacle_distance_range=bank_obstacle_distance_range,
                stride_steps=bank_stride_steps,
                max_snapshots=bank_max_snapshots,
                probe_config=probe_config,
            )
            for condition, env_config in configs.items()
        }
        pairs = pair_snapshot_banks(
            banks["nominal"],
            banks["perturbed"],
            configs["nominal"],
            max_pairs=bank_max_pairs_per_seed,
            max_pre_visible_distance=max_pre_visible_distance,
            max_pre_response_distance=max_pre_response_distance,
            max_pre_context_distance=max_pre_context_distance,
        )
        if not pairs:
            rows.append(
                {
                    "seed": int(seed),
                    "pair_status": "missing_bank_pair",
                    "nominal_bank_size": len(banks["nominal"]),
                    "perturbed_bank_size": len(banks["perturbed"]),
                    "accepted_visible_match": False,
                    "accepted_outcome_sensitive": False,
                    "accepted_nominal_outcome_sensitive": False,
                    "accepted_perturbed_outcome_sensitive": False,
                }
            )
            continue
        for pair_rank, (pair_meta, nominal, perturbed) in enumerate(pairs):
            for relocation_distance, relocation_lateral, relocation_half_width in relocation_grid:
                relocated_nominal = relocate_obstacle_snapshot(
                    nominal,
                    body_longitudinal=float(relocation_distance),
                    body_lateral=float(relocation_lateral),
                    half_width=relocation_half_width,
                )
                relocated_perturbed = relocate_obstacle_snapshot(
                    perturbed,
                    body_longitudinal=float(relocation_distance),
                    body_lateral=float(relocation_lateral),
                    half_width=relocation_half_width,
                )
                row, replays = build_outcome_sensitive_row(
                    seed,
                    float(relocation_distance),
                    relocated_nominal,
                    relocated_perturbed,
                    model,
                    configs["nominal"],
                    configs["perturbed"],
                    max_visible_distance=max_visible_distance,
                    max_response_distance=max_response_distance,
                    max_context_distance=max_context_distance,
                    min_margin_gap=min_margin_gap,
                    min_normal_margin=min_normal_margin,
                    max_normal_margin=max_normal_margin,
                    require_normal_success=require_normal_success,
                    max_continuation_steps=max_continuation_steps,
                )
                row.update(pair_meta)
                row.update(
                    {
                        "bank_pair_rank": int(pair_rank),
                        "nominal_bank_size": len(banks["nominal"]),
                        "perturbed_bank_size": len(banks["perturbed"]),
                        "snapshot_relocated": True,
                        "relocated_obstacle_body_x": float(relocation_distance),
                        "relocated_obstacle_body_y": float(relocation_lateral),
                        "relocated_obstacle_half_width": (
                            float("nan") if relocation_half_width is None else float(relocation_half_width)
                        ),
                        "active_probe_strategy": probe_config.strategy,
                        "nominal_active_probe_steps": int(
                            relocated_nominal.info.get("active_probe_steps", 0)
                        ),
                        "perturbed_active_probe_steps": int(
                            relocated_perturbed.info.get("active_probe_steps", 0)
                        ),
                    }
                )
                append_outcome_intervention_example(
                    outcome_examples,
                    model=model,
                    source=relocated_nominal,
                    paired=relocated_perturbed,
                    row=row,
                    source_prefix="nominal",
                    min_margin_gap=outcome_export_min_margin_gap,
                    boundary_margin_scale=outcome_export_boundary_margin_scale,
                )
                append_outcome_intervention_example(
                    outcome_examples,
                    model=model,
                    source=relocated_perturbed,
                    paired=relocated_nominal,
                    row=row,
                    source_prefix="perturbed",
                    min_margin_gap=outcome_export_min_margin_gap,
                    boundary_margin_scale=outcome_export_boundary_margin_scale,
                )
                rows.append(row)
                for replay in replays:
                    replay.update(
                        {
                            "bank_pair_rank": int(pair_rank),
                            "pre_pair_score": pair_meta["pre_pair_score"],
                            "relocated_obstacle_body_x": float(relocation_distance),
                            "relocated_obstacle_body_y": float(relocation_lateral),
                            "relocated_obstacle_half_width": (
                                float("nan") if relocation_half_width is None else float(relocation_half_width)
                            ),
                        }
                    )
                    replay_rows.append(replay)

    candidates = pd.DataFrame(rows)
    replays = pd.DataFrame(replay_rows)
    corpus = select_outcome_sensitive_corpus(candidates, top_k=top_k)
    summary = summarize_outcomes(candidates)
    outcome_metadata = outcome_intervention_metadata(outcome_examples)
    snippets = outcome_intervention_arrays(outcome_examples)
    if len(summary):
        summary.loc[0, "outcome_intervention_snippets"] = int(len(outcome_metadata))
        summary.loc[0, "outcome_intervention_weight_sum"] = (
            float(outcome_metadata["weight"].sum()) if "weight" in outcome_metadata else 0.0
        )
        summary.loc[0, "outcome_intervention_margin_gap_max"] = (
            float(outcome_metadata["margin_gap"].max()) if "margin_gap" in outcome_metadata else 0.0
        )
    return candidates, replays, corpus, summary, outcome_metadata, snippets


def main() -> None:
    parser = argparse.ArgumentParser(description="Run snapshot-bank obstacle relocation mining.")
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=80)
    parser.add_argument("--seed", type=int, default=8400)
    parser.add_argument("--seed-csv", type=Path, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--nominal-friction-mu-range", type=parse_range, default=(0.85, 1.15))
    parser.add_argument("--perturbed-friction-mu-range", type=parse_range, default=(0.25, 0.35))
    parser.add_argument("--nominal-randomization", action="append", default=[])
    parser.add_argument("--perturbed-randomization", action="append", default=[])
    parser.add_argument("--obstacle-perception-reveal-step", type=int, default=None)
    parser.add_argument("--obstacle-perception-reveal-distance", type=float, default=None)
    parser.add_argument("--bank-obstacle-distance-range", type=parse_range, default=(5.0, 12.0))
    parser.add_argument("--bank-stride-steps", type=int, default=2)
    parser.add_argument("--bank-max-snapshots", type=int, default=80)
    parser.add_argument("--bank-max-pairs-per-seed", type=int, default=16)
    parser.add_argument("--max-pre-visible-distance", type=float, default=None)
    parser.add_argument("--max-pre-response-distance", type=float, default=None)
    parser.add_argument("--max-pre-context-distance", type=float, default=None)
    parser.add_argument("--snapshot-relocation-distances", type=parse_float_list, required=True)
    parser.add_argument("--snapshot-relocation-lateral-offsets", type=parse_float_values, default=None)
    parser.add_argument("--snapshot-relocation-half-widths", type=parse_float_list, default=None)
    parser.add_argument("--min-probe-steps", type=int, default=10)
    parser.add_argument("--max-probe-steps", type=int, default=180)
    parser.add_argument("--allow-pre-friction-snapshot", action="store_true")
    parser.add_argument("--min-hidden-updates-after-friction", type=int, default=2)
    parser.add_argument("--max-visible-distance", type=float, default=0.75)
    parser.add_argument("--max-response-distance", type=float, default=0.35)
    parser.add_argument("--max-context-distance", type=float, default=0.05)
    parser.add_argument("--min-margin-gap", type=float, default=0.01)
    parser.add_argument("--min-normal-margin", type=float, default=0.0)
    parser.add_argument("--max-normal-margin", type=float, default=None)
    parser.add_argument("--allow-normal-failure", action="store_true")
    parser.add_argument("--max-continuation-steps", type=int, default=0)
    parser.add_argument("--probe-strategy", choices=PROBE_STRATEGIES, default="steer_brake")
    parser.add_argument("--probe-steer-amplitude", type=float, default=0.25)
    parser.add_argument("--probe-brake-level", type=float, default=0.20)
    parser.add_argument("--probe-throttle-level", type=float, default=0.0)
    parser.add_argument("--probe-period-steps", type=int, default=20)
    parser.add_argument("--probe-until-step", type=int, default=None)
    parser.add_argument("--probe-until-distance", type=float, default=None)
    parser.add_argument("--outcome-export-min-margin-gap", type=float, default=0.0)
    parser.add_argument("--outcome-export-boundary-margin-scale", type=float, default=0.20)
    parser.add_argument("--top-k", type=int, default=40)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="snapshot_bank_relocation", seed=args.seed)
    run_dir.mkdir(parents=True, exist_ok=True)

    base_config = load_env_config(args.env_config)
    target_obs_dim = int(AutoDriftEnv(base_config).observation_space.shape[0])
    model, _ = load_actor_critic_checkpoint(args.checkpoint, device=args.device, obs_dim=target_obs_dim)
    if not model.is_online_recurrent:
        raise ValueError("snapshot-bank relocation requires an online recurrent checkpoint")

    seeds = load_seed_csv(args.seed_csv) if args.seed_csv is not None else [args.seed + index for index in range(args.episodes)]
    nominal_randomization = parse_randomization_overrides(args.nominal_randomization)
    perturbed_randomization = parse_randomization_overrides(args.perturbed_randomization)
    probe_config = ProbeConfig(
        strategy=args.probe_strategy,
        steer_amplitude=args.probe_steer_amplitude,
        brake_level=args.probe_brake_level,
        throttle_level=args.probe_throttle_level,
        period_steps=args.probe_period_steps,
        until_step=args.probe_until_step,
        until_distance=args.probe_until_distance,
    )
    candidates, replays, corpus, summary, outcome_metadata, outcome_snippets = run_snapshot_bank_relocation(
        model=model,
        base_config=base_config,
        seeds=seeds,
        nominal_friction_mu_range=args.nominal_friction_mu_range,
        perturbed_friction_mu_range=args.perturbed_friction_mu_range,
        nominal_randomization=nominal_randomization,
        perturbed_randomization=perturbed_randomization,
        obstacle_perception_reveal_step=args.obstacle_perception_reveal_step,
        obstacle_perception_reveal_distance=args.obstacle_perception_reveal_distance,
        bank_obstacle_distance_range=args.bank_obstacle_distance_range,
        bank_stride_steps=args.bank_stride_steps,
        bank_max_snapshots=args.bank_max_snapshots,
        bank_max_pairs_per_seed=args.bank_max_pairs_per_seed,
        max_pre_visible_distance=args.max_pre_visible_distance,
        max_pre_response_distance=args.max_pre_response_distance,
        max_pre_context_distance=args.max_pre_context_distance,
        snapshot_relocation_distances=args.snapshot_relocation_distances,
        snapshot_relocation_lateral_offsets=args.snapshot_relocation_lateral_offsets,
        snapshot_relocation_half_widths=args.snapshot_relocation_half_widths,
        min_probe_steps=args.min_probe_steps,
        max_probe_steps=args.max_probe_steps,
        require_friction_step=not args.allow_pre_friction_snapshot,
        min_hidden_updates_after_friction=args.min_hidden_updates_after_friction,
        max_visible_distance=args.max_visible_distance,
        max_response_distance=args.max_response_distance,
        max_context_distance=args.max_context_distance,
        min_margin_gap=args.min_margin_gap,
        min_normal_margin=args.min_normal_margin,
        max_normal_margin=args.max_normal_margin,
        require_normal_success=not args.allow_normal_failure,
        max_continuation_steps=args.max_continuation_steps,
        top_k=args.top_k,
        probe_config=probe_config,
        outcome_export_min_margin_gap=args.outcome_export_min_margin_gap,
        outcome_export_boundary_margin_scale=args.outcome_export_boundary_margin_scale,
    )

    candidates_csv = run_dir / "outcome_candidates.csv"
    replays_csv = run_dir / "replays.csv"
    corpus_csv = run_dir / "outcome_sensitive_snippets.csv"
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
            "run_type": "snapshot_bank_relocation",
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
            "obstacle_perception_reveal_step": args.obstacle_perception_reveal_step,
            "obstacle_perception_reveal_distance": args.obstacle_perception_reveal_distance,
            "bank_obstacle_distance_range": args.bank_obstacle_distance_range,
            "bank_stride_steps": args.bank_stride_steps,
            "bank_max_snapshots": args.bank_max_snapshots,
            "bank_max_pairs_per_seed": args.bank_max_pairs_per_seed,
            "max_pre_visible_distance": args.max_pre_visible_distance,
            "max_pre_response_distance": args.max_pre_response_distance,
            "max_pre_context_distance": args.max_pre_context_distance,
            "snapshot_relocation": {
                "distances": args.snapshot_relocation_distances,
                "lateral_offsets": args.snapshot_relocation_lateral_offsets,
                "half_widths": args.snapshot_relocation_half_widths,
            },
            "min_probe_steps": args.min_probe_steps,
            "max_probe_steps": args.max_probe_steps,
            "require_friction_step": not args.allow_pre_friction_snapshot,
            "min_hidden_updates_after_friction": args.min_hidden_updates_after_friction,
            "max_visible_distance": args.max_visible_distance,
            "max_response_distance": args.max_response_distance,
            "max_context_distance": args.max_context_distance,
            "min_margin_gap": args.min_margin_gap,
            "min_normal_margin": args.min_normal_margin,
            "max_normal_margin": args.max_normal_margin,
            "require_normal_success": not args.allow_normal_failure,
            "max_continuation_steps": args.max_continuation_steps,
            "probe": {
                "strategy": probe_config.strategy,
                "steer_amplitude": probe_config.steer_amplitude,
                "brake_level": probe_config.brake_level,
                "throttle_level": probe_config.throttle_level,
                "period_steps": probe_config.period_steps,
                "until_step": probe_config.until_step,
                "until_distance": probe_config.until_distance,
            },
            "outcome_export": {
                "min_margin_gap": args.outcome_export_min_margin_gap,
                "boundary_margin_scale": args.outcome_export_boundary_margin_scale,
            },
            "top_k": args.top_k,
            "artifacts": {
                "outcome_candidates_csv": candidates_csv,
                "replays_csv": replays_csv,
                "outcome_sensitive_snippets_csv": corpus_csv,
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
