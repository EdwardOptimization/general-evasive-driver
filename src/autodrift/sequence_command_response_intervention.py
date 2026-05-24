"""No-training sequence-level command-response interventions."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import NOMINAL_FAULT, load_scenario_config
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.hidden_swap_gate import action_trajectory_distances, terminal_reason, zero_action_trajectory_distances
from autodrift.matched_history_intervention_gate import PREVIOUS_COMMAND_INDICES, deterministic_action_from_hidden
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.temporal_action_boundary_outcome_miner import (
    _collect_seed_snapshots,
    _find_snapshot,
    _source_summary,
    load_source_rows,
)
from autodrift.temporal_action_response_mismatch import _finite_mean, _finite_percentile, _group_summary
from autodrift.train_ppo import ActorCritic, resolve_device


SEQUENCE_VARIANTS = (
    "zero_command_obs",
    "command_shift_obs",
    "response_delay_obs",
    "reset_hidden_then_normal",
    "reset_hidden_each_step",
)


def _parse_int_list(raw: str) -> tuple[int, ...]:
    values = [part.strip() for part in str(raw).split(",") if part.strip()]
    if not values:
        raise argparse.ArgumentTypeError("expected at least one comma-separated integer")
    return tuple(int(value) for value in values)


def _dominance_fraction(values: list[Any]) -> float:
    if not values:
        return 0.0
    counts: dict[str, int] = {}
    for value in values:
        text = str(value)
        counts[text] = counts.get(text, 0) + 1
    return float(max(counts.values()) / max(len(values), 1))


def corrupt_sequence_observation(
    observation: np.ndarray,
    *,
    variant: str,
    step_index: int,
    horizon: int,
    raw_history: list[np.ndarray],
    response_dim: int,
) -> np.ndarray:
    obs = np.asarray(observation, dtype=np.float32).copy()
    if int(step_index) >= int(horizon):
        return obs
    if variant == "zero_command_obs":
        for command_index in PREVIOUS_COMMAND_INDICES:
            if command_index < obs.shape[0]:
                obs[command_index] = 0.0
    elif variant == "command_shift_obs":
        source = raw_history[-2] if len(raw_history) >= 2 else None
        for command_index in PREVIOUS_COMMAND_INDICES:
            if command_index < obs.shape[0]:
                obs[command_index] = float(source[command_index]) if source is not None and command_index < source.shape[0] else 0.0
    elif variant == "response_delay_obs":
        source = raw_history[-2] if len(raw_history) >= 2 else (raw_history[0] if raw_history else None)
        if source is not None:
            limit = min(int(response_dim), obs.shape[0], source.shape[0])
            obs[:limit] = source[:limit]
    return obs


def _prefix_distance_stats(actions: list[np.ndarray], reference_actions: list[np.ndarray] | None, horizon: int) -> dict[str, float | int]:
    if reference_actions is None:
        return {
            "prefix_l2_mean": float("nan"),
            "prefix_l2_max": float("nan"),
            "prefix_compare_steps": 0,
        }
    common_steps = min(len(actions), len(reference_actions), int(horizon))
    if common_steps <= 0:
        return {
            "prefix_l2_mean": float("nan"),
            "prefix_l2_max": float("nan"),
            "prefix_compare_steps": 0,
        }
    action_array = np.asarray(actions[:common_steps], dtype=np.float32)
    reference_array = np.asarray(reference_actions[:common_steps], dtype=np.float32)
    distances = np.linalg.norm(action_array - reference_array, axis=1)
    return {
        "prefix_l2_mean": float(np.mean(distances)),
        "prefix_l2_max": float(np.max(distances)),
        "prefix_compare_steps": int(common_steps),
    }


def classify_sequence_result(
    *,
    source_candidate_rows: int,
    sequence_action_critical_rows: int,
    sequence_outcome_critical_rows: int,
    unique_source_seeds: int,
    unique_source_preferred_fault_families: int,
    unique_source_fault_family_pairs: int,
    source_max_seed_dominance: float,
    source_max_preferred_family_dominance: float,
    source_sentinel_fraction: float,
    sentinel_false_positive_rate: float,
    normal_history_retention_pass: bool,
    actor_parameters_changed: bool,
    unique_sequence_action_seeds: int = 0,
    unique_sequence_outcome_seeds: int = 0,
    unique_sequence_outcome_fault_family_pairs: int = 0,
    max_sequence_outcome_seed_dominance: float = 0.0,
    min_source_rows: int = 256,
    min_source_seeds: int = 128,
    min_source_families: int = 7,
    min_source_pairs: int = 16,
    max_source_seed_dominance: float = 0.02,
    max_source_family_dominance: float = 0.25,
    min_sentinel_fraction: float = 0.05,
    max_sentinel_fraction: float = 0.15,
    max_sentinel_false_positive_rate: float = 0.05,
    min_sequence_action_rows: int = 300,
    min_sequence_action_seeds: int = 50,
    min_sequence_outcome_rows: int = 20,
    min_sequence_outcome_seeds: int = 10,
    min_sequence_outcome_pairs: int = 4,
    max_sequence_outcome_dominance: float = 0.20,
) -> str:
    if bool(actor_parameters_changed) or float(sentinel_false_positive_rate) > float(max_sentinel_false_positive_rate):
        return "sequence_artifact"
    source_balanced = (
        int(source_candidate_rows) >= int(min_source_rows)
        and int(unique_source_seeds) >= int(min_source_seeds)
        and int(unique_source_preferred_fault_families) >= int(min_source_families)
        and int(unique_source_fault_family_pairs) >= int(min_source_pairs)
        and float(source_max_seed_dominance) <= float(max_source_seed_dominance)
        and float(source_max_preferred_family_dominance) <= float(max_source_family_dominance)
        and float(min_sentinel_fraction) <= float(source_sentinel_fraction) <= float(max_sentinel_fraction)
        and bool(normal_history_retention_pass)
    )
    if not source_balanced:
        return "sequence_source_balance_blocked"
    outcome_positive = (
        int(sequence_outcome_critical_rows) >= int(min_sequence_outcome_rows)
        and int(unique_sequence_outcome_seeds) >= int(min_sequence_outcome_seeds)
        and int(unique_sequence_outcome_fault_family_pairs) >= int(min_sequence_outcome_pairs)
        and float(max_sequence_outcome_seed_dominance) <= float(max_sequence_outcome_dominance)
    )
    if outcome_positive:
        return "sequence_outcome_positive"
    if (
        int(sequence_action_critical_rows) >= int(min_sequence_action_rows)
        and int(unique_sequence_action_seeds) >= int(min_sequence_action_seeds)
    ):
        return "sequence_action_only"
    return "sequence_neutral"


def replay_sequence_variant(
    *,
    model: ActorCritic,
    snapshot: Any,
    env_config: Any,
    variant: str,
    horizon: int,
    response_dim: int,
    normal_actions: list[np.ndarray] | None,
    max_continuation_steps: int,
    device: torch.device,
) -> tuple[dict[str, Any], list[np.ndarray]]:
    env = copy.deepcopy(snapshot.env)
    obs = snapshot.observation.copy()
    hidden = snapshot.hidden.detach().clone()
    if variant in {"reset_hidden_then_normal", "reset_hidden_each_step"}:
        hidden = model.initial_hidden(1, device)
    max_steps = int(max_continuation_steps)
    if max_steps <= 0:
        max_steps = max(1, int(env_config.max_steps) - int(snapshot.step))
    raw_history: list[np.ndarray] = [np.asarray(obs, dtype=np.float32).copy()]
    actions: list[np.ndarray] = []
    rewards: list[float] = []
    betas: list[float] = []
    terminated = False
    truncated = False
    info = dict(snapshot.info)
    for step_index in range(max_steps):
        policy_obs = np.asarray(obs, dtype=np.float32).copy()
        if variant not in {"normal", "reset_hidden_then_normal", "reset_hidden_each_step"}:
            policy_obs = corrupt_sequence_observation(
                policy_obs,
                variant=variant,
                step_index=step_index,
                horizon=horizon,
                raw_history=raw_history,
                response_dim=response_dim,
            )
        if variant == "reset_hidden_each_step" and step_index < int(horizon):
            hidden = model.initial_hidden(1, device)
        action, next_hidden = deterministic_action_from_hidden(model, policy_obs, hidden, device)
        actions.append(action)
        hidden = next_hidden
        obs, reward, terminated, truncated, info = env.step(action)
        raw_history.append(np.asarray(obs, dtype=np.float32).copy())
        rewards.append(float(reward))
        betas.append(float(info.get("beta", float("nan"))))
        if terminated or truncated:
            break
    first_action = actions[0] if actions else np.full(3, float("nan"), dtype=np.float32)
    if variant == "normal":
        trajectory_distances = zero_action_trajectory_distances(len(actions))
        prefix_distances = {"prefix_l2_mean": 0.0, "prefix_l2_max": 0.0, "prefix_compare_steps": min(len(actions), int(horizon))}
    else:
        trajectory_distances = action_trajectory_distances(actions, normal_actions)
        prefix_distances = _prefix_distance_stats(actions, normal_actions, int(horizon))
    beta_abs_peak = float(np.nanmax(np.abs(betas))) if betas else float("nan")
    reason = terminal_reason(info, terminated, truncated, env_config)
    return {
        "variant": variant,
        "horizon": int(horizon),
        "steps": len(rewards),
        "return": float(np.sum(rewards)),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "success": not bool(terminated),
        "collision": bool(info.get("collision", False)),
        "off_road": reason == "off_road",
        "spin_out": bool(np.isfinite(beta_abs_peak) and beta_abs_peak > 1.2),
        "terminal_reason": reason,
        "obstacle_completed": bool(info.get("obstacle_completed", False)),
        "min_obstacle_clearance": _finite_float(info.get("min_obstacle_clearance")),
        "obstacle_collision_radius": _finite_float(info.get("obstacle_collision_radius")),
        "min_clearance_margin": _finite_float(info.get("min_clearance_margin")),
        "beta_abs_peak": beta_abs_peak,
        "first_steer": float(first_action[0]),
        "first_throttle": float(first_action[1]),
        "first_brake": float(first_action[2]),
        **trajectory_distances,
        **prefix_distances,
    }, actions


def _source_meta(source: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "source_index",
        "source_role",
        "proposal_id",
        "selected_index",
        "seed",
        "step",
        "preferred_snapshot_id",
        "wrong_snapshot_id",
        "preferred_fault",
        "preferred_fault_family",
        "preferred_fault_severity",
        "wrong_fault",
        "wrong_fault_family",
        "wrong_fault_severity",
        "fault_family_pair",
        "severity_pair",
        "source_pool",
        "assigned_split",
        "step_bucket",
        "obstacle_distance_bucket",
    )
    return {key: source.get(key, "") for key in keys}


def _row_for_sequence_variant(
    *,
    source: dict[str, Any],
    variant: str,
    horizon: int,
    result: dict[str, Any],
    normal: dict[str, Any],
    action_threshold: float,
    margin_threshold: float,
) -> dict[str, Any]:
    normal_margin = _finite_float(normal.get("min_clearance_margin"))
    variant_margin = _finite_float(result.get("min_clearance_margin"))
    margin_gap = normal_margin - variant_margin if np.isfinite(normal_margin) and np.isfinite(variant_margin) else float("nan")
    normal_success = bool(normal.get("success", False))
    success_drop = bool(normal_success and not bool(result.get("success", False)))
    normal_ok = bool(normal_success or (np.isfinite(normal_margin) and normal_margin >= 0.0))
    prefix_l2_mean = _finite_float(result.get("prefix_l2_mean"), default=0.0)
    trajectory_l2_mean = _finite_float(result.get("action_trajectory_distance_mean"), default=0.0)
    sequence_action_critical = bool(
        normal_ok
        and variant != "normal"
        and max(prefix_l2_mean, trajectory_l2_mean) >= float(action_threshold)
    )
    sequence_outcome_critical = bool(
        normal_ok
        and variant != "normal"
        and (success_drop or (np.isfinite(margin_gap) and margin_gap >= float(margin_threshold)))
    )
    row = _source_meta(source)
    row.update(
        {
            "variant": variant,
            "horizon": int(horizon),
            "normal_success": normal_success,
            "normal_margin": normal_margin,
            "variant_success": bool(result.get("success", False)),
            "variant_margin": variant_margin,
            "margin_gap_from_normal": margin_gap,
            "success_drop_from_normal": success_drop,
            "first_steer": _finite_float(result.get("first_steer")),
            "first_throttle": _finite_float(result.get("first_throttle")),
            "first_brake": _finite_float(result.get("first_brake")),
            "trajectory_l2_mean": trajectory_l2_mean,
            "trajectory_l2_max": _finite_float(result.get("action_trajectory_distance_max")),
            "prefix_l2_mean": prefix_l2_mean,
            "prefix_l2_max": _finite_float(result.get("prefix_l2_max")),
            "prefix_compare_steps": int(result.get("prefix_compare_steps", 0)),
            "terminal_reason": str(result.get("terminal_reason", "")),
            "sequence_action_critical": sequence_action_critical,
            "sequence_outcome_critical": sequence_outcome_critical,
            "temporal_action_critical": sequence_action_critical,
            "temporal_outcome_critical": sequence_outcome_critical,
            "sentinel": str(source.get("source_role", "")) == "sentinel",
        }
    )
    return row


def _sequence_group_summary(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(tuple(str(row.get(key, "")) for key in keys), []).append(row)
    output: list[dict[str, Any]] = []
    for key_values, group_rows in sorted(groups.items()):
        item = {key: value for key, value in zip(keys, key_values, strict=True)}
        prefix = [_finite_float(row.get("prefix_l2_mean")) for row in group_rows]
        margins = [_finite_float(row.get("margin_gap_from_normal")) for row in group_rows]
        item.update(
            {
                "rows": int(len(group_rows)),
                "sequence_action_critical_rows": int(
                    sum(1 for row in group_rows if bool(row.get("sequence_action_critical", False)))
                ),
                "sequence_outcome_critical_rows": int(
                    sum(1 for row in group_rows if bool(row.get("sequence_outcome_critical", False)))
                ),
                "unique_seeds": int(len({int(row.get("seed", -1)) for row in group_rows})),
                "prefix_l2_mean": _finite_mean(prefix),
                "prefix_l2_p95": _finite_percentile(prefix, 0.95),
                "prefix_l2_max": max([value for value in prefix if np.isfinite(value)], default=float("nan")),
                "margin_gap_mean": _finite_mean(margins),
                "margin_gap_p95": _finite_percentile(margins, 0.95),
                "margin_gap_max": max([value for value in margins if np.isfinite(value)], default=float("nan")),
            }
        )
        output.append(item)
    return output


def run_sequence_command_response_intervention(
    *,
    checkpoint_path: Path,
    config_path: Path,
    source_rows_path: Path,
    seed_start: int,
    seed_count: int,
    max_source_rows: int,
    horizons: tuple[int, ...],
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    config = load_scenario_config(config_path)
    env_config = load_env_config(Path(config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    if not model.is_online_recurrent:
        raise ValueError("sequence intervention requires an online recurrent checkpoint")
    checksum_before = model_parameter_checksum(model)
    response_dim = response_feature_dim_for_model(model)
    min_action_l2_gap = float(config.get("min_action_l2_gap", 0.015))
    min_history_margin_gap = float(config.get("min_history_margin_gap", 0.02))
    max_continuation_steps = int(config.get("max_continuation_steps", 50))

    source_rows = load_source_rows(
        source_rows_path,
        seed_start=seed_start,
        seed_count=seed_count,
        max_source_rows=max_source_rows,
        min_action_l2_gap=min_action_l2_gap,
    )
    source_balance = _source_summary(source_rows)
    faults = [NOMINAL_FAULT, *config["faults"]]
    snapshots_by_seed: dict[int, list[Any]] = {}
    for seed in sorted({int(row["seed"]) for row in source_rows}):
        snapshots_by_seed[seed] = _collect_seed_snapshots(
            model=model,
            env_config=env_config,
            faults=faults,
            seed=seed,
            config=config,
            device=resolved_device,
        )

    source_output_rows: list[dict[str, Any]] = []
    rollout_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    for source in source_rows:
        seed = int(source["seed"])
        source_record = dict(source)
        source_output_rows.append(source_record)
        snapshot = _find_snapshot(
            snapshots_by_seed.get(seed, []),
            fault_name=str(source["preferred_fault"]),
            step=int(source["step"]),
        )
        if snapshot is None:
            rejected_rows.append({**_source_meta(source_record), "rejection_reason": "source_snapshot_missing"})
            continue
        normal, normal_actions = replay_sequence_variant(
            model=model,
            snapshot=snapshot,
            env_config=env_config,
            variant="normal",
            horizon=max(horizons),
            response_dim=response_dim,
            normal_actions=None,
            max_continuation_steps=max_continuation_steps,
            device=resolved_device,
        )
        normal_margin = _finite_float(normal.get("min_clearance_margin"))
        normal_ok = bool(normal.get("success", False) or (np.isfinite(normal_margin) and normal_margin >= 0.0))
        for horizon in horizons:
            normal_row = _row_for_sequence_variant(
                source=source_record,
                variant="normal",
                horizon=int(horizon),
                result=normal,
                normal=normal,
                action_threshold=min_action_l2_gap,
                margin_threshold=min_history_margin_gap,
            )
            rollout_rows.append(normal_row)
            for variant in SEQUENCE_VARIANTS:
                result, _ = replay_sequence_variant(
                    model=model,
                    snapshot=snapshot,
                    env_config=env_config,
                    variant=variant,
                    horizon=int(horizon),
                    response_dim=response_dim,
                    normal_actions=normal_actions,
                    max_continuation_steps=max_continuation_steps,
                    device=resolved_device,
                )
                rollout_rows.append(
                    _row_for_sequence_variant(
                        source=source_record,
                        variant=variant,
                        horizon=int(horizon),
                        result=result,
                        normal=normal,
                        action_threshold=min_action_l2_gap,
                        margin_threshold=min_history_margin_gap,
                    )
                )
        if not normal_ok:
            rejected_rows.append({**_source_meta(source_record), "rejection_reason": "normal_history_failed"})

    sequence_action_rows = [row for row in rollout_rows if bool(row.get("sequence_action_critical", False))]
    sequence_outcome_rows = [row for row in rollout_rows if bool(row.get("sequence_outcome_critical", False))]
    sentinel_rows = [row for row in rollout_rows if bool(row.get("sentinel", False))]
    sentinel_false_positive_rows = [
        row for row in sentinel_rows if bool(row.get("sequence_action_critical", False)) and bool(row.get("sequence_outcome_critical", False))
    ]
    normal_rows = [row for row in rollout_rows if row.get("variant") == "normal"]
    normal_failed_rejected = [row for row in rejected_rows if row.get("rejection_reason") == "normal_history_failed"]
    normal_history_retention_pass = bool(
        normal_rows
        and not any(str(row.get("terminal_reason", "")) == "artifact" for row in normal_rows)
        and len(normal_failed_rejected) <= max(1, len(source_rows) // 2)
    )
    sentinel_false_positive_rate = float(len(sentinel_false_positive_rows) / max(len(sentinel_rows), 1))
    outcome_seeds = [int(row.get("seed", -1)) for row in sequence_outcome_rows]
    outcome_pairs = [str(row.get("fault_family_pair", "")) for row in sequence_outcome_rows]
    action_seeds = [int(row.get("seed", -1)) for row in sequence_action_rows]
    checksum_after = model_parameter_checksum(model)
    result_class = classify_sequence_result(
        source_candidate_rows=len(source_rows),
        sequence_action_critical_rows=len(sequence_action_rows),
        sequence_outcome_critical_rows=len(sequence_outcome_rows),
        unique_source_seeds=int(source_balance["source_unique_seeds"]),
        unique_source_preferred_fault_families=int(source_balance["source_unique_preferred_fault_families"]),
        unique_source_fault_family_pairs=int(source_balance["source_unique_fault_family_pairs"]),
        source_max_seed_dominance=float(source_balance["source_max_seed_dominance"]),
        source_max_preferred_family_dominance=float(source_balance["source_max_preferred_family_dominance"]),
        source_sentinel_fraction=float(source_balance["source_sentinel_fraction"]),
        sentinel_false_positive_rate=sentinel_false_positive_rate,
        normal_history_retention_pass=normal_history_retention_pass,
        actor_parameters_changed=bool(checksum_before != checksum_after),
        unique_sequence_action_seeds=len(set(action_seeds)),
        unique_sequence_outcome_seeds=len(set(outcome_seeds)),
        unique_sequence_outcome_fault_family_pairs=len(set(outcome_pairs)),
        max_sequence_outcome_seed_dominance=_dominance_fraction(outcome_seeds),
    )

    write_csv_rows(run_dir / "source_rows.csv", source_output_rows)
    write_csv_rows(run_dir / "intervention_rollouts.csv", rollout_rows)
    write_csv_rows(
        run_dir / "sequence_critical_rows.csv",
        [row for row in rollout_rows if bool(row.get("sequence_action_critical", False)) or bool(row.get("sequence_outcome_critical", False))],
    )
    write_csv_rows(run_dir / "sentinel_rows.csv", sentinel_rows)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
    write_csv_rows(run_dir / "variant_summary.csv", _sequence_group_summary(rollout_rows, ("variant",)))
    write_csv_rows(run_dir / "horizon_summary.csv", _sequence_group_summary(rollout_rows, ("horizon",)))
    write_csv_rows(run_dir / "fault_family_summary.csv", _sequence_group_summary(rollout_rows, ("fault_family_pair", "variant")))

    summary = {
        "run_type": "sequence_command_response_intervention",
        "checkpoint": checkpoint_path,
        "config": config_path,
        "source_rows": source_rows_path,
        "env_config": config.get("env_config"),
        "seed_start": int(seed_start),
        "seed_count": int(seed_count),
        "fault_count": int(len(faults) - 1),
        "source_candidate_rows": int(len(source_rows)),
        **source_balance,
        "horizons": [int(item) for item in horizons],
        "rollout_rows": int(len(rollout_rows)),
        "sequence_action_critical_rows": int(len(sequence_action_rows)),
        "sequence_outcome_critical_rows": int(len(sequence_outcome_rows)),
        "unique_sequence_action_seeds": int(len(set(action_seeds))),
        "unique_sequence_outcome_seeds": int(len(set(outcome_seeds))),
        "unique_sequence_outcome_fault_family_pairs": int(len(set(outcome_pairs))),
        "max_sequence_outcome_seed_dominance": float(_dominance_fraction(outcome_seeds)),
        "normal_failed_rejected": int(len(normal_failed_rejected)),
        "sentinel_rows": int(len(sentinel_rows)),
        "sentinel_false_positive_rows": int(len(sentinel_false_positive_rows)),
        "sentinel_false_positive_rate": sentinel_false_positive_rate,
        "normal_history_retention_pass": bool(normal_history_retention_pass),
        "source_role_counts": {
            role: int(sum(1 for row in source_output_rows if str(row.get("source_role", "")) == role))
            for role in sorted({str(row.get("source_role", "")) for row in source_output_rows})
        },
        "thresholds": {
            "min_action_l2_gap": min_action_l2_gap,
            "min_history_margin_gap": min_history_margin_gap,
            "max_source_rows": int(max_source_rows),
        },
        "actor_parameters_changed": bool(checksum_before != checksum_after),
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "promoted": False,
        "result_class": result_class,
        "sequence_outcome_positive": bool(result_class == "sequence_outcome_positive"),
        "summary_json": run_dir / "summary.json",
        "source_rows_csv": run_dir / "source_rows.csv",
        "intervention_rollouts_csv": run_dir / "intervention_rollouts.csv",
        "sequence_critical_rows_csv": run_dir / "sequence_critical_rows.csv",
        "sentinel_rows_csv": run_dir / "sentinel_rows.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
        "variant_summary_csv": run_dir / "variant_summary.csv",
        "horizon_summary_csv": run_dir / "horizon_summary.csv",
        "fault_family_summary_csv": run_dir / "fault_family_summary.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training sequence-level command-response interventions.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--source-rows", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=72000)
    parser.add_argument("--seed-count", type=int, default=512)
    parser.add_argument("--max-source-rows", type=int, default=512)
    parser.add_argument("--horizons", type=_parse_int_list, default=(2, 4, 6, 8))
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="sequence_command_response_intervention")
    summary = run_sequence_command_response_intervention(
        checkpoint_path=args.checkpoint,
        config_path=args.config,
        source_rows_path=args.source_rows,
        seed_start=args.seed_start,
        seed_count=args.seed_count,
        max_source_rows=args.max_source_rows,
        horizons=tuple(args.horizons),
        device=args.device,
        run_dir=run_dir,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
