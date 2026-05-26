"""No-training sequence interventions for capability-step reset-only rows."""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import (
    FaultSpec,
    _frame_info,
    apply_fault_to_env,
    fault_from_dict,
    load_scenario_config,
)
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.hidden_swap_gate import action_trajectory_distances, terminal_reason, zero_action_trajectory_distances
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden, zero_action_history_observation
from autodrift.train_ppo import ActorCritic, resolve_device


TEMPORAL_HISTORY_VARIANTS = (
    "delayed_capability_history",
    "reset_then_warm_history",
    "zero_command_history_window",
)
CROSS_FAULT_SEQUENCE_VARIANTS = (
    "cross_fault_response_window",
    "wrong_commands_preferred_response",
    "wrong_response_preferred_commands",
)


@dataclass
class TracePoint:
    seed: int
    fault: FaultSpec
    step: int
    observation: np.ndarray
    hidden: torch.Tensor
    env: AutoDriftEnv
    info: dict[str, Any]


def parse_int_list(text: str) -> tuple[int, ...]:
    values = tuple(int(item.strip()) for item in str(text).split(",") if item.strip())
    if not values:
        raise argparse.ArgumentTypeError("expected at least one integer")
    if any(value <= 0 for value in values):
        raise argparse.ArgumentTypeError("history lengths must be positive")
    return values


def source_pair_key(row: pd.Series) -> str:
    pair = str(row.get("pairing_rule", "")).strip()
    if pair:
        return pair
    return f"{row.get('preferred_fault_family', '')}->{row.get('wrong_fault_family', '')}"


def select_source_rows(
    rows: pd.DataFrame,
    *,
    max_source_rows: int,
    per_fault_pair_cap: int,
) -> pd.DataFrame:
    if rows.empty:
        return rows.copy()
    frame = rows.copy()
    frame["_fault_pair"] = frame.apply(source_pair_key, axis=1)
    sort_columns = [
        column
        for column in ("reset_margin_gap", "reset_action_l2_gap", "normal_margin")
        if column in frame.columns
    ]
    ascending = [False] * len(sort_columns)
    if sort_columns:
        frame = frame.sort_values(sort_columns, ascending=ascending)
    selected = []
    for _, group in frame.groupby("_fault_pair", observed=True):
        selected.append(group.head(max(1, int(per_fault_pair_cap))))
    if not selected:
        return frame.head(0).drop(columns=["_fault_pair"], errors="ignore")
    output = pd.concat(selected, ignore_index=True)
    if int(max_source_rows) > 0:
        output = output.head(int(max_source_rows))
    return output.drop(columns=["_fault_pair"], errors="ignore").reset_index(drop=True)


def load_snapshot_step_lookup(source_rows_path: Path) -> dict[int, int]:
    snapshot_path = source_rows_path.parent / "snapshot_candidates.csv"
    if not snapshot_path.exists():
        raise FileNotFoundError(f"missing snapshot candidate file: {snapshot_path}")
    frame = pd.read_csv(snapshot_path)
    if "snapshot_id" not in frame.columns or "step" not in frame.columns:
        raise ValueError(f"{snapshot_path} must contain snapshot_id and step columns")
    return {int(row["snapshot_id"]): int(row["step"]) for _, row in frame.iterrows()}


def fault_map_from_config(config: dict[str, Any]) -> dict[str, FaultSpec]:
    faults = config.get("faults", [])
    mapping = {str(fault.name): fault for fault in faults}
    if not mapping:
        raise ValueError("scenario config has no faults")
    return mapping


def collect_fault_trace_window(
    *,
    model: ActorCritic,
    env_config: DriftEnvConfig,
    fault: FaultSpec,
    seed: int,
    target_step: int,
    history_length: int,
    device: torch.device,
) -> list[TracePoint]:
    if history_length < 1:
        raise ValueError("history_length must be positive")
    env = AutoDriftEnv(env_config)
    points: list[TracePoint] = []
    try:
        obs, info = env.reset(seed=int(seed))
        hidden = model.initial_hidden(1, device)
        fault_applied = False
        if int(fault.activation_step) <= 0:
            apply_fault_to_env(env, fault)
            fault_applied = True
            info = _frame_info(env)
        window_start = max(0, int(target_step) - int(history_length))
        terminated = False
        truncated = False
        while not (terminated or truncated) and int(env.step_count) <= int(target_step):
            step = int(env.step_count)
            if not fault_applied and step >= int(fault.activation_step):
                apply_fault_to_env(env, fault)
                fault_applied = True
                info = _frame_info(env)
            if step >= window_start:
                points.append(
                    TracePoint(
                        seed=int(seed),
                        fault=fault,
                        step=step,
                        observation=np.asarray(obs, dtype=np.float32).copy(),
                        hidden=hidden.detach().clone(),
                        env=copy.deepcopy(env),
                        info=dict(info),
                    )
                )
            if step >= int(target_step):
                break
            action, next_hidden = deterministic_action_from_hidden(
                model,
                np.asarray(obs, dtype=np.float32),
                hidden,
                device,
            )
            obs, _, terminated, truncated, info = env.step(action)
            hidden = next_hidden
    finally:
        env.close()
    if not points or points[-1].step != int(target_step):
        raise ValueError(f"failed to reconstruct seed={seed} fault={fault.name} step={target_step}")
    return points


def roll_hidden_over_observations(
    model: ActorCritic,
    hidden: torch.Tensor,
    observations: list[np.ndarray],
    device: torch.device,
) -> torch.Tensor:
    current = hidden.detach().clone().to(device=device, dtype=torch.float32)
    with torch.no_grad():
        for observation in observations:
            obs_t = torch.as_tensor(observation, dtype=torch.float32, device=device).unsqueeze(0)
            _, current = model.recurrent_features_tensor(obs_t, current)
    return current.detach()


def mismatch_observation(
    preferred: np.ndarray,
    wrong: np.ndarray,
    mode: str,
) -> np.ndarray:
    preferred_obs = np.asarray(preferred, dtype=np.float32)
    wrong_obs = np.asarray(wrong, dtype=np.float32)
    if preferred_obs.shape != wrong_obs.shape:
        raise ValueError(f"observation shapes differ: {preferred_obs.shape} vs {wrong_obs.shape}")
    output = preferred_obs.copy()
    if mode == "wrong_commands_preferred_response":
        output[9:12] = wrong_obs[9:12]
    elif mode == "wrong_response_preferred_commands":
        output[:9] = wrong_obs[:9]
    else:
        raise ValueError(f"unknown mismatch mode {mode!r}")
    return output


def zero_command_observation(observation: np.ndarray) -> np.ndarray:
    return zero_action_history_observation(np.asarray(observation, dtype=np.float32))


def build_variant_hiddens(
    *,
    model: ActorCritic,
    preferred_trace: list[TracePoint],
    wrong_trace: list[TracePoint],
    device: torch.device,
) -> dict[str, torch.Tensor]:
    preferred_prefix = [point.observation for point in preferred_trace[:-1]]
    wrong_prefix = [point.observation for point in wrong_trace[:-1]]
    common = min(len(preferred_prefix), len(wrong_prefix))
    preferred_prefix = preferred_prefix[-common:] if common else []
    wrong_prefix = wrong_prefix[-common:] if common else []
    preferred_start = preferred_trace[-(common + 1)].hidden if common else preferred_trace[-1].hidden
    wrong_start = wrong_trace[-(common + 1)].hidden if common else wrong_trace[-1].hidden
    reset_hidden = model.initial_hidden(1, device)

    wrong_commands = [
        mismatch_observation(preferred_obs, wrong_obs, "wrong_commands_preferred_response")
        for preferred_obs, wrong_obs in zip(preferred_prefix, wrong_prefix, strict=False)
    ]
    wrong_response = [
        mismatch_observation(preferred_obs, wrong_obs, "wrong_response_preferred_commands")
        for preferred_obs, wrong_obs in zip(preferred_prefix, wrong_prefix, strict=False)
    ]
    zero_commands = [zero_command_observation(obs) for obs in preferred_prefix]

    return {
        "delayed_capability_history": preferred_start.detach().clone(),
        "cross_fault_response_window": roll_hidden_over_observations(model, wrong_start, wrong_prefix, device),
        "wrong_commands_preferred_response": roll_hidden_over_observations(
            model,
            preferred_start,
            wrong_commands,
            device,
        ),
        "wrong_response_preferred_commands": roll_hidden_over_observations(
            model,
            preferred_start,
            wrong_response,
            device,
        ),
        "zero_command_history_window": roll_hidden_over_observations(
            model,
            preferred_start,
            zero_commands,
            device,
        ),
        "reset_then_warm_history": roll_hidden_over_observations(model, reset_hidden, preferred_prefix, device),
    }


def replay_with_initial_hidden(
    *,
    model: ActorCritic,
    snapshot: TracePoint,
    variant: str,
    initial_hidden: torch.Tensor,
    max_continuation_steps: int,
    normal_first_action: np.ndarray | None,
    normal_actions: list[np.ndarray] | None,
    device: torch.device,
) -> tuple[dict[str, Any], list[np.ndarray]]:
    env = copy.deepcopy(snapshot.env)
    obs = snapshot.observation.copy()
    hidden = initial_hidden.detach().clone()
    max_steps = int(max_continuation_steps)
    if max_steps <= 0:
        max_steps = max(1, env.config.max_steps - snapshot.step)
    rewards: list[float] = []
    actions: list[np.ndarray] = []
    betas: list[float] = []
    terminated = False
    truncated = False
    info = dict(snapshot.info)
    for _ in range(max_steps):
        action, next_hidden = deterministic_action_from_hidden(model, np.asarray(obs, dtype=np.float32), hidden, device)
        actions.append(action)
        obs, reward, terminated, truncated, info = env.step(action)
        hidden = next_hidden
        rewards.append(float(reward))
        betas.append(float(info.get("beta", float("nan"))))
        if terminated or truncated:
            break
    first_action = actions[0] if actions else np.full(3, float("nan"), dtype=np.float32)
    if normal_first_action is None:
        first_action_distance = 0.0
    else:
        first_action_distance = float(np.linalg.norm(first_action - normal_first_action))
    trajectory_distances = (
        zero_action_trajectory_distances(len(actions))
        if normal_actions is None
        else action_trajectory_distances(actions, normal_actions)
    )
    beta_abs_peak = float(np.nanmax(np.abs(betas))) if betas else float("nan")
    reason = terminal_reason(info, terminated, truncated, env.config)
    return {
        "variant": variant,
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
        "min_obstacle_clearance": float(info.get("min_obstacle_clearance", float("nan"))),
        "obstacle_collision_radius": float(info.get("obstacle_collision_radius", float("nan"))),
        "min_clearance_margin": float(info.get("min_clearance_margin", float("nan"))),
        "beta_abs_peak": beta_abs_peak,
        "first_steer": float(first_action[0]),
        "first_throttle": float(first_action[1]),
        "first_brake": float(first_action[2]),
        "first_action_distance": first_action_distance,
        **trajectory_distances,
    }, actions


def _finite(value: Any, default: float = float("nan")) -> float:
    try:
        output = float(value)
    except (TypeError, ValueError):
        return default
    return output if np.isfinite(output) else default


def _summarize_groups(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    if not rows:
        return []
    frame = pd.DataFrame(rows)
    summary_rows: list[dict[str, Any]] = []
    for group_key, group in frame.groupby(list(keys), observed=True):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        accepted = group[group["sequence_outcome_critical"].astype(bool)]
        item = {key: value for key, value in zip(keys, group_key, strict=True)}
        item.update(
            {
                "rows": int(len(group)),
                "accepted_rows": int(len(accepted)),
                "normal_success_rate": float(group["normal_success"].astype(bool).mean()),
                "variant_success_rate": float(group["variant_success"].astype(bool).mean()),
                "success_drop_rate": float(group["success_drop"].astype(bool).mean()),
                "margin_gap_mean": float(group["margin_gap"].astype(float).mean()),
                "sequence_action_l2_mean": float(group["sequence_action_l2_mean"].astype(float).mean()),
                "unique_seeds": int(group["seed"].nunique()),
                "unique_fault_pairs": int(group["fault_pair"].nunique()),
            }
        )
        summary_rows.append(item)
    return summary_rows


def _result_class(
    *,
    accepted_rows: int,
    accepted_cross_fault_rows: int,
    accepted_temporal_rows: int,
    action_critical_rows: int,
    normal_failed_rows: int,
    total_rows: int,
    unique_cross_fault_pairs: int,
    unique_cross_fault_seeds: int,
    unique_temporal_fault_pairs: int,
    unique_temporal_seeds: int,
) -> str:
    if total_rows == 0:
        return "sequence_no_rows"
    if normal_failed_rows >= total_rows:
        return "sequence_normal_failed"
    if accepted_cross_fault_rows > 0 and unique_cross_fault_pairs >= 3 and unique_cross_fault_seeds >= 6:
        return "sequence_cross_fault_positive"
    if accepted_cross_fault_rows > 0:
        return "sequence_cross_fault_sparse"
    if accepted_temporal_rows > 0 and unique_temporal_fault_pairs >= 3 and unique_temporal_seeds >= 6:
        return "sequence_temporal_history_positive"
    if accepted_temporal_rows > 0:
        return "sequence_temporal_history_sparse"
    if accepted_rows > 0:
        return "sequence_other_positive"
    if action_critical_rows > 0:
        return "sequence_action_only"
    return "sequence_no_signal"


def run_capability_step_sequence_intervention_probe(
    *,
    checkpoint_path: Path,
    config_path: Path,
    source_rows_path: Path,
    max_source_rows: int,
    per_fault_pair_cap: int,
    history_lengths: tuple[int, ...],
    max_continuation_steps: int,
    min_margin_gap: float,
    min_sequence_action_l2: float,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    config = load_scenario_config(config_path)
    env_config = load_env_config(Path(config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    fault_by_name = fault_map_from_config(config)
    source_frame = pd.read_csv(source_rows_path)
    selected_rows = select_source_rows(
        source_frame,
        max_source_rows=max_source_rows,
        per_fault_pair_cap=per_fault_pair_cap,
    )
    snapshot_steps = load_snapshot_step_lookup(source_rows_path)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    checksum_before = sum(float(param.detach().cpu().double().sum()) for param in model.parameters())
    response_dim = response_feature_dim_for_model(model)
    del response_dim  # Response dimension is indirectly fixed by the loaded model contract.

    intervention_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    trace_cache: dict[tuple[int, str, int, int], list[TracePoint]] = {}

    def trace_for(seed: int, fault_name: str, step: int, history_length: int) -> list[TracePoint]:
        key = (int(seed), str(fault_name), int(step), int(history_length))
        if key not in trace_cache:
            trace_cache[key] = collect_fault_trace_window(
                model=model,
                env_config=env_config,
                fault=fault_by_name[str(fault_name)],
                seed=int(seed),
                target_step=int(step),
                history_length=int(history_length),
                device=resolved_device,
            )
        return trace_cache[key]

    for source_index, row in selected_rows.reset_index(drop=True).iterrows():
        seed = int(row["seed"])
        preferred_fault = str(row["preferred_fault"])
        wrong_fault = str(row["wrong_fault"])
        preferred_step = int(row["step"])
        wrong_snapshot_id = int(row["wrong_snapshot_id"])
        wrong_step = int(snapshot_steps[wrong_snapshot_id])
        fault_pair = source_pair_key(row)
        for history_length in history_lengths:
            try:
                preferred_trace = trace_for(seed, preferred_fault, preferred_step, int(history_length))
                wrong_trace = trace_for(seed, wrong_fault, wrong_step, int(history_length))
                preferred_snapshot = preferred_trace[-1]
                normal, normal_actions = replay_with_initial_hidden(
                    model=model,
                    snapshot=preferred_snapshot,
                    variant="normal",
                    initial_hidden=preferred_snapshot.hidden,
                    max_continuation_steps=max_continuation_steps,
                    normal_first_action=None,
                    normal_actions=None,
                    device=resolved_device,
                )
                normal_first_action = np.asarray(
                    [normal["first_steer"], normal["first_throttle"], normal["first_brake"]],
                    dtype=np.float32,
                )
                variant_hiddens = build_variant_hiddens(
                    model=model,
                    preferred_trace=preferred_trace,
                    wrong_trace=wrong_trace,
                    device=resolved_device,
                )
            except Exception as exc:  # pragma: no cover - surfaced in artifacts.
                rejected_rows.append(
                    {
                        "source_index": int(source_index),
                        "seed": seed,
                        "preferred_fault": preferred_fault,
                        "wrong_fault": wrong_fault,
                        "fault_pair": fault_pair,
                        "history_length": int(history_length),
                        "rejection_reason": "trace_reconstruction_failed",
                        "error": str(exc),
                    }
                )
                continue
            normal_success = bool(normal.get("success", False))
            normal_margin = _finite(normal.get("min_clearance_margin"))
            normal_viable = bool(normal_success and normal_margin >= 0.0)
            for variant, variant_hidden in variant_hiddens.items():
                result, _ = replay_with_initial_hidden(
                    model=model,
                    snapshot=preferred_snapshot,
                    variant=variant,
                    initial_hidden=variant_hidden,
                    max_continuation_steps=max_continuation_steps,
                    normal_first_action=normal_first_action,
                    normal_actions=normal_actions,
                    device=resolved_device,
                )
                variant_margin = _finite(result.get("min_clearance_margin"))
                margin_gap = normal_margin - variant_margin if np.isfinite(normal_margin) and np.isfinite(variant_margin) else float("nan")
                success_drop = bool(normal_success and not bool(result.get("success", False)))
                sequence_action_l2 = _finite(result.get("action_trajectory_distance_mean"), default=0.0)
                sequence_action_critical = bool(sequence_action_l2 >= float(min_sequence_action_l2))
                sequence_outcome_critical = bool(
                    normal_viable
                    and sequence_action_critical
                    and (success_drop or (np.isfinite(margin_gap) and margin_gap >= float(min_margin_gap)))
                )
                intervention_rows.append(
                    {
                        "source_index": int(source_index),
                        "seed": seed,
                        "preferred_fault": preferred_fault,
                        "preferred_fault_family": str(row.get("preferred_fault_family", "")),
                        "wrong_fault": wrong_fault,
                        "wrong_fault_family": str(row.get("wrong_fault_family", "")),
                        "fault_pair": fault_pair,
                        "history_length": int(history_length),
                        "variant": variant,
                        "preferred_step": int(preferred_step),
                        "wrong_step": int(wrong_step),
                        "normal_success": normal_success,
                        "variant_success": bool(result.get("success", False)),
                        "success_drop": success_drop,
                        "normal_margin": normal_margin,
                        "variant_margin": variant_margin,
                        "margin_gap": margin_gap,
                        "normal_terminal_reason": str(normal.get("terminal_reason", "")),
                        "variant_terminal_reason": str(result.get("terminal_reason", "")),
                        "first_action_l2": _finite(result.get("first_action_distance"), default=0.0),
                        "sequence_action_l2_mean": sequence_action_l2,
                        "sequence_action_l2_max": _finite(result.get("action_trajectory_distance_max"), default=0.0),
                        "sequence_action_critical": sequence_action_critical,
                        "sequence_outcome_critical": sequence_outcome_critical,
                    }
                )

    accepted = [row for row in intervention_rows if bool(row.get("sequence_outcome_critical", False))]
    accepted_cross_fault = [
        row for row in accepted if str(row.get("variant", "")) in CROSS_FAULT_SEQUENCE_VARIANTS
    ]
    accepted_temporal = [row for row in accepted if str(row.get("variant", "")) in TEMPORAL_HISTORY_VARIANTS]
    action_critical = [row for row in intervention_rows if bool(row.get("sequence_action_critical", False))]
    normal_failed = [row for row in intervention_rows if not bool(row.get("normal_success", False)) or _finite(row.get("normal_margin")) < 0.0]
    checksum_after = sum(float(param.detach().cpu().double().sum()) for param in model.parameters())
    actor_parameters_changed = bool(abs(checksum_after - checksum_before) > 1e-8)
    variant_summary = _summarize_groups(intervention_rows, ("variant",))
    fault_pair_summary = _summarize_groups(intervention_rows, ("fault_pair",))
    history_length_summary = _summarize_groups(intervention_rows, ("history_length",))
    result_class = _result_class(
        accepted_rows=len(accepted),
        accepted_cross_fault_rows=len(accepted_cross_fault),
        accepted_temporal_rows=len(accepted_temporal),
        action_critical_rows=len(action_critical),
        normal_failed_rows=len(normal_failed),
        total_rows=len(intervention_rows),
        unique_cross_fault_pairs=len({str(row.get("fault_pair", "")) for row in accepted_cross_fault}),
        unique_cross_fault_seeds=len({int(row.get("seed", -1)) for row in accepted_cross_fault}),
        unique_temporal_fault_pairs=len({str(row.get("fault_pair", "")) for row in accepted_temporal}),
        unique_temporal_seeds=len({int(row.get("seed", -1)) for row in accepted_temporal}),
    )

    write_csv_rows(run_dir / "selected_source_rows.csv", selected_rows.to_dict("records"))
    write_csv_rows(run_dir / "sequence_intervention_rows.csv", intervention_rows)
    write_csv_rows(run_dir / "accepted_sequence_rows.csv", accepted)
    write_csv_rows(run_dir / "rejected_sequence_rows.csv", rejected_rows)
    write_csv_rows(run_dir / "variant_summary.csv", variant_summary)
    write_csv_rows(run_dir / "fault_pair_summary.csv", fault_pair_summary)
    write_csv_rows(run_dir / "history_length_summary.csv", history_length_summary)
    summary = {
        "run_type": "capability_step_sequence_intervention_probe",
        "checkpoint": checkpoint_path,
        "config": config_path,
        "source_rows": source_rows_path,
        "selected_source_rows": int(len(selected_rows)),
        "history_lengths": history_lengths,
        "max_continuation_steps": int(max_continuation_steps),
        "min_margin_gap": float(min_margin_gap),
        "min_sequence_action_l2": float(min_sequence_action_l2),
        "intervention_rows": int(len(intervention_rows)),
        "accepted_sequence_rows": int(len(accepted)),
        "accepted_cross_fault_sequence_rows": int(len(accepted_cross_fault)),
        "accepted_temporal_sequence_rows": int(len(accepted_temporal)),
        "sequence_action_critical_rows": int(len(action_critical)),
        "normal_failed_rows": int(len(normal_failed)),
        "rejected_trace_rows": int(len(rejected_rows)),
        "unique_accepted_fault_pairs": int(len({str(row.get("fault_pair", "")) for row in accepted})),
        "unique_accepted_seeds": int(len({int(row.get("seed", -1)) for row in accepted})),
        "unique_cross_fault_accepted_fault_pairs": int(
            len({str(row.get("fault_pair", "")) for row in accepted_cross_fault})
        ),
        "unique_cross_fault_accepted_seeds": int(len({int(row.get("seed", -1)) for row in accepted_cross_fault})),
        "unique_temporal_accepted_fault_pairs": int(
            len({str(row.get("fault_pair", "")) for row in accepted_temporal})
        ),
        "unique_temporal_accepted_seeds": int(len({int(row.get("seed", -1)) for row in accepted_temporal})),
        "variant_count": int(len({str(row.get("variant", "")) for row in intervention_rows})),
        "result_class": result_class,
        "actor_parameters_changed": actor_parameters_changed,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "selected_source_rows_csv": run_dir / "selected_source_rows.csv",
        "sequence_intervention_rows_csv": run_dir / "sequence_intervention_rows.csv",
        "accepted_sequence_rows_csv": run_dir / "accepted_sequence_rows.csv",
        "rejected_sequence_rows_csv": run_dir / "rejected_sequence_rows.csv",
        "variant_summary_csv": run_dir / "variant_summary.csv",
        "fault_pair_summary_csv": run_dir / "fault_pair_summary.csv",
        "history_length_summary_csv": run_dir / "history_length_summary.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training capability-step sequence interventions.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--source-rows", type=Path, required=True)
    parser.add_argument("--max-source-rows", type=int, default=384)
    parser.add_argument("--per-fault-pair-cap", type=int, default=48)
    parser.add_argument("--history-lengths", type=parse_int_list, default=(4, 8, 12))
    parser.add_argument("--max-continuation-steps", type=int, default=48)
    parser.add_argument("--min-margin-gap", type=float, default=0.012)
    parser.add_argument("--min-sequence-action-l2", type=float, default=0.025)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="capability_step_sequence_intervention_probe")
    summary = run_capability_step_sequence_intervention_probe(
        checkpoint_path=args.checkpoint,
        config_path=args.config,
        source_rows_path=args.source_rows,
        max_source_rows=args.max_source_rows,
        per_fault_pair_cap=args.per_fault_pair_cap,
        history_lengths=tuple(args.history_lengths),
        max_continuation_steps=args.max_continuation_steps,
        min_margin_gap=args.min_margin_gap,
        min_sequence_action_l2=args.min_sequence_action_l2,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
