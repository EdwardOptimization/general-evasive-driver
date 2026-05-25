"""Closed-loop no-PPO replay for the M761 v4 residual head."""

from __future__ import annotations

import argparse
import copy
import csv
from pathlib import Path
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import NOMINAL_FAULT, load_scenario_config
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.hidden_swap_gate import action_trajectory_distances, terminal_reason, zero_action_trajectory_distances
from autodrift.sequence_command_response_intervention import corrupt_sequence_observation
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.temporal_action_boundary_outcome_miner import _collect_seed_snapshots, _find_snapshot
from autodrift.train_ppo import ActorCritic, resolve_device
from autodrift.v4_sequence_objective_probe import ResidualHead


DEFAULT_ALPHAS = (0.0, 0.2, 0.5, 1.0)
SUPPORTED_VARIANTS = {"zero_command_obs", "reset_hidden_each_step", "reset_hidden_then_normal"}


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _parse_float_list(raw: str) -> tuple[float, ...]:
    values = [part.strip() for part in str(raw).split(",") if part.strip()]
    if not values:
        raise argparse.ArgumentTypeError("expected at least one comma-separated float")
    return tuple(float(value) for value in values)


def _bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _finite_values(values: list[float] | np.ndarray) -> list[float]:
    return [float(value) for value in values if np.isfinite(float(value))]


def _mean(values: list[float] | np.ndarray) -> float:
    finite = _finite_values(values)
    return float(np.mean(finite)) if finite else float("nan")


def _percentile(values: list[float] | np.ndarray, percentile: float) -> float:
    finite = _finite_values(values)
    if not finite:
        return float("nan")
    return float(np.percentile(np.asarray(finite, dtype=np.float64), float(percentile)))


def _prefix_distance_stats(actions: list[np.ndarray], reference_actions: list[np.ndarray] | None, horizon: int) -> dict[str, float | int]:
    if reference_actions is None:
        return {
            "prefix_l2_mean": float("nan"),
            "prefix_l2_max": float("nan"),
            "prefix_compare_steps": 0,
            "first_action_l2_from_reference": float("nan"),
        }
    common_steps = min(len(actions), len(reference_actions), int(horizon))
    if common_steps <= 0:
        return {
            "prefix_l2_mean": float("nan"),
            "prefix_l2_max": float("nan"),
            "prefix_compare_steps": 0,
            "first_action_l2_from_reference": float("nan"),
        }
    action_array = np.asarray(actions[:common_steps], dtype=np.float32)
    reference_array = np.asarray(reference_actions[:common_steps], dtype=np.float32)
    distances = np.linalg.norm(action_array - reference_array, axis=1)
    return {
        "prefix_l2_mean": float(np.mean(distances)),
        "prefix_l2_max": float(np.max(distances)),
        "prefix_compare_steps": int(common_steps),
        "first_action_l2_from_reference": float(distances[0]),
    }


def _metadata_missing(row: dict[str, Any]) -> bool:
    required = (
        "source_index",
        "seed",
        "step",
        "preferred_fault",
        "variant",
        "horizon",
        "source_pool",
        "claim_boundary_level",
        "contrast_group_id",
    )
    return any(not str(row.get(field, "")).strip() for field in required)


def _source_meta(row: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "contrast_group_id",
        "source_index",
        "source_kind",
        "source_pool",
        "source_role",
        "seed",
        "step",
        "preferred_fault",
        "preferred_fault_family",
        "preferred_fault_severity",
        "wrong_fault",
        "wrong_fault_family",
        "wrong_fault_severity",
        "fault_family_pair",
        "severity_pair",
        "variant",
        "horizon",
        "claim_boundary_level",
    )
    return {key: row.get(key, "") for key in keys}


def _load_residual_head(path: Path, *, expected_feature_dim: int, device: torch.device) -> ResidualHead:
    payload = torch.load(Path(path), map_location=device)
    feature_dim = int(payload.get("feature_dim", -1))
    if feature_dim != int(expected_feature_dim):
        raise ValueError(f"residual feature_dim={feature_dim} does not match actor feature_dim={expected_feature_dim}")
    head = ResidualHead(
        feature_dim=feature_dim,
        max_residual=float(payload.get("max_residual", 0.04)),
    ).to(device)
    head.load_state_dict(payload["state_dict"])
    head.eval()
    for parameter in head.parameters():
        parameter.requires_grad_(False)
    return head


def residual_action_from_hidden(
    model: ActorCritic,
    residual_head: ResidualHead,
    observation: np.ndarray,
    hidden: torch.Tensor,
    *,
    alpha: float,
    device: torch.device,
) -> tuple[np.ndarray, torch.Tensor, np.ndarray, np.ndarray]:
    obs_t = torch.as_tensor(observation, dtype=torch.float32, device=device).unsqueeze(0)
    hidden_t = hidden.to(device=device, dtype=torch.float32)
    with torch.no_grad():
        features, next_hidden = model.recurrent_features_tensor(obs_t, hidden_t)
        base_action = torch.tanh(model.actor_mean(features))
        delta_action = residual_head(features)
        action = torch.clamp(base_action + float(alpha) * delta_action, -1.0, 1.0)
    return (
        action.squeeze(0).detach().cpu().numpy().astype(np.float32),
        next_hidden.detach(),
        base_action.squeeze(0).detach().cpu().numpy().astype(np.float32),
        delta_action.squeeze(0).detach().cpu().numpy().astype(np.float32),
    )


def replay_residual_sequence_variant(
    *,
    model: ActorCritic,
    residual_head: ResidualHead,
    snapshot: Any,
    env_config: Any,
    variant: str,
    horizon: int,
    response_dim: int,
    reference_actions: list[np.ndarray] | None,
    base_reference_actions: list[np.ndarray] | None,
    max_continuation_steps: int,
    alpha: float,
    device: torch.device,
) -> tuple[dict[str, Any], list[np.ndarray]]:
    env = copy.deepcopy(snapshot.env)
    obs = np.asarray(snapshot.observation, dtype=np.float32).copy()
    hidden = snapshot.hidden.detach().clone()
    if variant in {"reset_hidden_then_normal", "reset_hidden_each_step"}:
        hidden = model.initial_hidden(1, device)
    max_steps = int(max_continuation_steps)
    if max_steps <= 0:
        max_steps = max(1, int(env_config.max_steps) - int(snapshot.step))
    raw_history: list[np.ndarray] = [np.asarray(obs, dtype=np.float32).copy()]
    actions: list[np.ndarray] = []
    base_actions: list[np.ndarray] = []
    deltas: list[np.ndarray] = []
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
                horizon=int(horizon),
                raw_history=raw_history,
                response_dim=response_dim,
            )
        if variant == "reset_hidden_each_step" and step_index < int(horizon):
            hidden = model.initial_hidden(1, device)
        action, next_hidden, base_action, delta_action = residual_action_from_hidden(
            model,
            residual_head,
            policy_obs,
            hidden,
            alpha=float(alpha),
            device=device,
        )
        actions.append(action)
        base_actions.append(base_action)
        deltas.append(delta_action)
        hidden = next_hidden
        obs, reward, terminated, truncated, info = env.step(action)
        raw_history.append(np.asarray(obs, dtype=np.float32).copy())
        rewards.append(float(reward))
        betas.append(float(info.get("beta", float("nan"))))
        if terminated or truncated:
            break
    first_action = actions[0] if actions else np.full(3, float("nan"), dtype=np.float32)
    first_delta = deltas[0] if deltas else np.full(3, float("nan"), dtype=np.float32)
    if reference_actions is None:
        trajectory_distances = zero_action_trajectory_distances(len(actions))
        prefix_distances = {
            "prefix_l2_mean": 0.0,
            "prefix_l2_max": 0.0,
            "prefix_compare_steps": min(len(actions), int(horizon)),
            "first_action_l2_from_reference": 0.0,
        }
    else:
        trajectory_distances = action_trajectory_distances(actions, reference_actions)
        prefix_distances = _prefix_distance_stats(actions, reference_actions, int(horizon))
    base_reference_distances = _prefix_distance_stats(actions, base_reference_actions, int(max(horizon, 1)))
    beta_abs_peak = float(np.nanmax(np.abs(betas))) if betas else float("nan")
    reason = terminal_reason(info, terminated, truncated, env_config)
    return {
        "variant": variant,
        "horizon": int(horizon),
        "alpha": float(alpha),
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
        "first_residual_steer": float(first_delta[0]),
        "first_residual_throttle": float(first_delta[1]),
        "first_residual_brake": float(first_delta[2]),
        "residual_l2_mean": _mean([float(np.linalg.norm(delta)) for delta in deltas]),
        "residual_l2_max": max(_finite_values([float(np.linalg.norm(delta)) for delta in deltas]), default=float("nan")),
        **trajectory_distances,
        **prefix_distances,
        "first_action_drift_vs_base_normal": float(base_reference_distances["first_action_l2_from_reference"]),
        "prefix_l2_mean_vs_base_normal": float(base_reference_distances["prefix_l2_mean"]),
        "prefix_l2_max_vs_base_normal": float(base_reference_distances["prefix_l2_max"]),
    }, actions


def classify_v4_residual_closed_loop_replay(
    *,
    actor_backbone_changed: bool,
    optimizer_started: bool,
    ppo_used: bool,
    promoted: bool,
    metadata_missing_rows: int,
    reconstruction_success_rate: float,
    candidate_count: int,
    any_gap_lift: bool,
    any_normal_regression: bool,
) -> str:
    if (
        bool(actor_backbone_changed)
        or bool(optimizer_started)
        or bool(ppo_used)
        or bool(promoted)
        or int(metadata_missing_rows) > 0
    ):
        return "v4_residual_closed_loop_replay_metadata_artifact"
    if float(reconstruction_success_rate) < 0.98:
        return "v4_residual_closed_loop_replay_reconstruction_blocked"
    if int(candidate_count) > 0:
        return "v4_residual_closed_loop_replay_candidate"
    if bool(any_gap_lift) and bool(any_normal_regression):
        return "v4_residual_closed_loop_replay_normal_regression"
    return "v4_residual_closed_loop_replay_no_closed_loop_gap"


def _alpha_summary_rows(objective_rows: list[dict[str, Any]], alphas: tuple[float, ...]) -> list[dict[str, Any]]:
    base_rows = [row for row in objective_rows if float(row["alpha"]) == 0.0]
    base_by_group = {str(row["contrast_group_id"]): row for row in base_rows}
    base_normal_success = _mean([1.0 if _bool(row.get("normal_success")) else 0.0 for row in base_rows])
    base_normal_collision = _mean([1.0 if _bool(row.get("normal_collision")) else 0.0 for row in base_rows])
    base_intervention_gap = _mean([_finite_float(row.get("intervention_prefix_l2_mean")) for row in base_rows])
    base_intervention_gap_p10 = _percentile([_finite_float(row.get("intervention_prefix_l2_mean")) for row in base_rows], 10)
    base_margin_gap = _mean([_finite_float(row.get("margin_gap_from_normal")) for row in base_rows])
    alpha_rows: list[dict[str, Any]] = []
    for alpha in alphas:
        subset = [row for row in objective_rows if float(row["alpha"]) == float(alpha)]
        if not subset:
            continue
        normal_success = _mean([1.0 if _bool(row.get("normal_success")) else 0.0 for row in subset])
        normal_collision = _mean([1.0 if _bool(row.get("normal_collision")) else 0.0 for row in subset])
        normal_margin_regressions: list[float] = []
        normal_first_drift: list[float] = []
        outcome_retained: list[float] = []
        for row in subset:
            base = base_by_group.get(str(row["contrast_group_id"]))
            if base is None:
                continue
            base_normal_margin = _finite_float(base.get("normal_margin"))
            normal_margin = _finite_float(row.get("normal_margin"))
            if np.isfinite(base_normal_margin) and np.isfinite(normal_margin):
                normal_margin_regressions.append(max(0.0, base_normal_margin - normal_margin))
            normal_first_drift.append(_finite_float(row.get("normal_first_action_drift_vs_base")))
            base_margin_gap_row = _finite_float(base.get("margin_gap_from_normal"))
            margin_gap = _finite_float(row.get("margin_gap_from_normal"))
            if np.isfinite(base_margin_gap_row) and np.isfinite(margin_gap):
                outcome_retained.append(1.0 if margin_gap + 0.005 >= base_margin_gap_row else 0.0)
        intervention_gap_values = [_finite_float(row.get("intervention_prefix_l2_mean")) for row in subset]
        margin_gap_values = [_finite_float(row.get("margin_gap_from_normal")) for row in subset]
        row = {
            "alpha": float(alpha),
            "sample_count": int(len(subset)),
            "base_normal_success_rate": base_normal_success,
            "normal_success_rate": normal_success,
            "base_normal_collision_rate": base_normal_collision,
            "normal_collision_rate": normal_collision,
            "normal_margin_regression_mean_vs_base": _mean(normal_margin_regressions),
            "normal_margin_regression_p95_vs_base": _percentile(normal_margin_regressions, 95),
            "normal_first_action_drift_mean_vs_base": _mean(normal_first_drift),
            "normal_first_action_drift_p95_vs_base": _percentile(normal_first_drift, 95),
            "base_intervention_action_gap_mean": base_intervention_gap,
            "base_intervention_action_gap_p10": base_intervention_gap_p10,
            "intervention_action_gap_mean_vs_normal": _mean(intervention_gap_values),
            "intervention_action_gap_p10_vs_normal": _percentile(intervention_gap_values, 10),
            "base_margin_gap_mean": base_margin_gap,
            "normal_minus_intervention_margin_gap_mean": _mean(margin_gap_values),
            "outcome_sensitivity_retention_rate": _mean(outcome_retained),
            "intervention_success_rate": _mean([1.0 if _bool(row.get("intervention_success")) else 0.0 for row in subset]),
            "intervention_collision_rate": _mean([1.0 if _bool(row.get("intervention_collision")) else 0.0 for row in subset]),
            "hard_negative_available_fraction": _mean([1.0 if _bool(row.get("hard_negative_available")) else 0.0 for row in subset]),
        }
        row["normal_retention_pass"] = bool(
            row["normal_success_rate"] >= row["base_normal_success_rate"] - 0.01
            and row["normal_collision_rate"] <= row["base_normal_collision_rate"] + 0.01
            and row["normal_margin_regression_mean_vs_base"] <= 0.01
            and row["normal_first_action_drift_mean_vs_base"] <= 0.004
            and row["normal_first_action_drift_p95_vs_base"] <= 0.012
        )
        row["closed_loop_gap_pass"] = bool(
            float(alpha) > 0.0
            and row["intervention_action_gap_mean_vs_normal"] >= row["base_intervention_action_gap_mean"] + 0.003
            and row["intervention_action_gap_p10_vs_normal"] >= row["base_intervention_action_gap_p10"]
            and row["normal_minus_intervention_margin_gap_mean"] >= row["base_margin_gap_mean"]
            and row["outcome_sensitivity_retention_rate"] >= 0.95
        )
        row["closed_loop_replay_candidate"] = bool(row["normal_retention_pass"] and row["closed_loop_gap_pass"])
        alpha_rows.append(row)
    return alpha_rows


def _group_summary(rows: list[dict[str, Any]], *, key: str, metric: str) -> list[dict[str, Any]]:
    groups: dict[str, list[float]] = {}
    for row in rows:
        groups.setdefault(str(row.get(key, "")), []).append(_finite_float(row.get(metric)))
    return [
        {
            key: group_key,
            "rows": int(len(values)),
            f"{metric}_mean": _mean(values),
            f"{metric}_p10": _percentile(values, 10),
            f"{metric}_p95": _percentile(values, 95),
        }
        for group_key, values in sorted(groups.items())
    ]


def run_v4_residual_closed_loop_replay(
    *,
    checkpoint_path: Path,
    residual_head_path: Path,
    positive_rows_path: Path,
    contrast_rows_path: Path,
    scenario_config_path: Path,
    run_dir: Path,
    device: str,
    alphas: tuple[float, ...] = DEFAULT_ALPHAS,
    max_rows: int | None = None,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    scenario_config = load_scenario_config(scenario_config_path)
    env_config = load_env_config(Path(scenario_config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    if not model.is_online_recurrent:
        raise ValueError("v4 residual closed-loop replay requires an online recurrent checkpoint")
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    feature_dim = int(model.actor_mean.in_features)
    residual_head = _load_residual_head(residual_head_path, expected_feature_dim=feature_dim, device=resolved_device)
    checksum_before = model_parameter_checksum(model)
    response_dim = response_feature_dim_for_model(model)
    max_continuation_steps = int(scenario_config.get("max_continuation_steps", 50))
    positives = _read_csv_rows(positive_rows_path)
    if max_rows is not None:
        positives = positives[: max(0, int(max_rows))]
    contrast_rows = _read_csv_rows(contrast_rows_path)
    hard_available_by_group = {
        str(row.get("contrast_group_id", "")): True
        for row in contrast_rows
        if str(row.get("contrast_role", "")) == "hard_negative_action_only"
    }
    metadata_missing_rows = sum(1 for row in positives if _metadata_missing(row))
    faults = [NOMINAL_FAULT, *scenario_config["faults"]]
    snapshots_by_seed: dict[int, list[Any]] = {}
    for seed in sorted({int(row.get("seed", -1)) for row in positives if str(row.get("seed", "")).strip()}):
        snapshots_by_seed[seed] = _collect_seed_snapshots(
            model=model,
            env_config=env_config,
            faults=faults,
            seed=int(seed),
            config=scenario_config,
            device=resolved_device,
        )

    replay_rows: list[dict[str, Any]] = []
    objective_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    for row in positives:
        meta = _source_meta(row)
        if _metadata_missing(row):
            rejected_rows.append({**meta, "rejection_reason": "metadata_missing"})
            continue
        variant = str(row.get("variant", ""))
        if variant not in SUPPORTED_VARIANTS:
            rejected_rows.append({**meta, "rejection_reason": f"unsupported_variant:{variant}"})
            continue
        seed = int(row["seed"])
        step = int(row["step"])
        horizon = int(row["horizon"])
        snapshot = _find_snapshot(snapshots_by_seed.get(seed, []), fault_name=str(row["preferred_fault"]), step=step)
        if snapshot is None:
            rejected_rows.append({**meta, "rejection_reason": "missing_source_snapshot"})
            continue
        base_normal_actions: list[np.ndarray] | None = None
        normal_by_alpha: dict[float, dict[str, Any]] = {}
        normal_actions_by_alpha: dict[float, list[np.ndarray]] = {}
        intervention_by_alpha: dict[float, dict[str, Any]] = {}
        for alpha in alphas:
            normal, normal_actions = replay_residual_sequence_variant(
                model=model,
                residual_head=residual_head,
                snapshot=snapshot,
                env_config=env_config,
                variant="normal",
                horizon=horizon,
                response_dim=response_dim,
                reference_actions=None,
                base_reference_actions=base_normal_actions,
                max_continuation_steps=max_continuation_steps,
                alpha=float(alpha),
                device=resolved_device,
            )
            if float(alpha) == 0.0:
                base_normal_actions = normal_actions
                normal["first_action_drift_vs_base_normal"] = 0.0
                normal["prefix_l2_mean_vs_base_normal"] = 0.0
                normal["prefix_l2_max_vs_base_normal"] = 0.0
            normal_by_alpha[float(alpha)] = normal
            normal_actions_by_alpha[float(alpha)] = normal_actions
            replay_rows.append({**meta, **normal, "branch": "normal", "hard_negative_available": bool(hard_available_by_group.get(str(row["contrast_group_id"]), False))})
        if base_normal_actions is None:
            rejected_rows.append({**meta, "rejection_reason": "missing_base_normal_actions"})
            continue
        for alpha in alphas:
            intervention, _ = replay_residual_sequence_variant(
                model=model,
                residual_head=residual_head,
                snapshot=snapshot,
                env_config=env_config,
                variant=variant,
                horizon=horizon,
                response_dim=response_dim,
                reference_actions=normal_actions_by_alpha[float(alpha)],
                base_reference_actions=base_normal_actions,
                max_continuation_steps=max_continuation_steps,
                alpha=float(alpha),
                device=resolved_device,
            )
            intervention_by_alpha[float(alpha)] = intervention
            replay_rows.append({**meta, **intervention, "branch": "intervention", "hard_negative_available": bool(hard_available_by_group.get(str(row["contrast_group_id"]), False))})
        for alpha in alphas:
            normal = normal_by_alpha[float(alpha)]
            intervention = intervention_by_alpha[float(alpha)]
            normal_margin = _finite_float(normal.get("min_clearance_margin"))
            intervention_margin = _finite_float(intervention.get("min_clearance_margin"))
            margin_gap = normal_margin - intervention_margin if np.isfinite(normal_margin) and np.isfinite(intervention_margin) else float("nan")
            objective_rows.append(
                {
                    **meta,
                    "alpha": float(alpha),
                    "hard_negative_available": bool(hard_available_by_group.get(str(row["contrast_group_id"]), False)),
                    "normal_success": bool(normal.get("success", False)),
                    "normal_collision": bool(normal.get("collision", False)),
                    "normal_terminal_reason": str(normal.get("terminal_reason", "")),
                    "normal_margin": normal_margin,
                    "normal_first_action_drift_vs_base": _finite_float(normal.get("first_action_drift_vs_base_normal"), default=0.0),
                    "normal_prefix_l2_mean_vs_base": _finite_float(normal.get("prefix_l2_mean_vs_base_normal"), default=0.0),
                    "intervention_success": bool(intervention.get("success", False)),
                    "intervention_collision": bool(intervention.get("collision", False)),
                    "intervention_terminal_reason": str(intervention.get("terminal_reason", "")),
                    "intervention_margin": intervention_margin,
                    "margin_gap_from_normal": margin_gap,
                    "intervention_first_action_l2_from_normal": _finite_float(intervention.get("first_action_l2_from_reference")),
                    "intervention_prefix_l2_mean": _finite_float(intervention.get("prefix_l2_mean")),
                    "intervention_prefix_l2_max": _finite_float(intervention.get("prefix_l2_max")),
                    "intervention_trajectory_l2_mean": _finite_float(intervention.get("action_trajectory_distance_mean")),
                    "intervention_trajectory_l2_max": _finite_float(intervention.get("action_trajectory_distance_max")),
                }
            )

    reconstruction_rate = float((len({str(row["contrast_group_id"]) for row in objective_rows}) / max(len(positives), 1)))
    alpha_rows = _alpha_summary_rows(objective_rows, alphas=alphas)
    candidate_rows = [row for row in alpha_rows if _bool(row.get("closed_loop_replay_candidate", False))]
    any_gap_lift = any(_bool(row.get("closed_loop_gap_pass", False)) for row in alpha_rows)
    any_normal_regression = any(not _bool(row.get("normal_retention_pass", False)) for row in alpha_rows if float(row.get("alpha", 0.0)) > 0.0)
    checksum_after = model_parameter_checksum(model)
    result_class = classify_v4_residual_closed_loop_replay(
        actor_backbone_changed=bool(checksum_before != checksum_after),
        optimizer_started=False,
        ppo_used=False,
        promoted=False,
        metadata_missing_rows=metadata_missing_rows,
        reconstruction_success_rate=reconstruction_rate,
        candidate_count=len(candidate_rows),
        any_gap_lift=any_gap_lift,
        any_normal_regression=any_normal_regression,
    )
    write_csv_rows(run_dir / "replay_rows.csv", replay_rows)
    write_csv_rows(run_dir / "objective_rows.csv", objective_rows)
    write_csv_rows(run_dir / "alpha_metrics.csv", alpha_rows)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
    write_csv_rows(run_dir / "variant_gap_summary.csv", _group_summary(objective_rows, key="variant", metric="intervention_prefix_l2_mean"))
    write_csv_rows(run_dir / "horizon_gap_summary.csv", _group_summary(objective_rows, key="horizon", metric="intervention_prefix_l2_mean"))
    summary = {
        "run_type": "v4_residual_closed_loop_replay",
        "checkpoint": checkpoint_path,
        "residual_head": residual_head_path,
        "positive_rows_input": positive_rows_path,
        "contrast_rows_input": contrast_rows_path,
        "scenario_config": scenario_config_path,
        "positive_rows": int(len(positives)),
        "reconstructed_rows": int(len({str(row["contrast_group_id"]) for row in objective_rows})),
        "sample_reconstruction_success_rate": reconstruction_rate,
        "metadata_missing_rows": int(metadata_missing_rows),
        "rejected_rows": int(len(rejected_rows)),
        "replay_rows": int(len(replay_rows)),
        "objective_rows": int(len(objective_rows)),
        "alphas": [float(alpha) for alpha in alphas],
        "candidate_alpha_count": int(len(candidate_rows)),
        "candidate_alphas": [float(row.get("alpha")) for row in candidate_rows],
        "best_candidate": candidate_rows[0] if candidate_rows else {},
        "actor_backbone_changed": bool(checksum_before != checksum_after),
        "base_actor_checksum_before": checksum_before,
        "base_actor_checksum_after": checksum_after,
        "optimizer_started": False,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "result_class": result_class,
        "summary_json": run_dir / "summary.json",
        "alpha_metrics_csv": run_dir / "alpha_metrics.csv",
        "replay_rows_csv": run_dir / "replay_rows.csv",
        "objective_rows_csv": run_dir / "objective_rows.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-PPO closed-loop replay for the M761 residual head.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--residual-head", type=Path, required=True)
    parser.add_argument("--positive-rows", type=Path, required=True)
    parser.add_argument("--contrast-rows", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--alphas", type=_parse_float_list, default=DEFAULT_ALPHAS)
    parser.add_argument("--max-rows", type=int, default=None)
    args = parser.parse_args()
    summary = run_v4_residual_closed_loop_replay(
        checkpoint_path=args.checkpoint,
        residual_head_path=args.residual_head,
        positive_rows_path=args.positive_rows,
        contrast_rows_path=args.contrast_rows,
        scenario_config_path=args.scenario_config,
        run_dir=args.run_dir,
        device=args.device,
        alphas=tuple(args.alphas),
        max_rows=args.max_rows,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
