"""No-training replay-constrained target feasibility audit for the M399 public base."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.boundary_outcome_replay_gate import validate_corpus_frame
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import load_scenario_config
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.hidden_swap_gate import terminal_reason
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.matched_history_outcome_gate import OutcomeSnapshot, collect_requested_outcome_snapshots
from autodrift.public_base_controlled_fusion_surface_probe import _base_actions, _mean, _percentile
from autodrift.public_base_regenerated_target_residual_probe import target_weight_vector
from autodrift.public_base_target_regeneration import _key
from autodrift.public_base_tail_weighted_residual_probe import (
    DEFICIT_LIFT_TARGET,
    LOW_TAIL_DEFICIT_THRESHOLD,
    LOW_TAIL_FRACTION_LIFT_TARGET,
    LOW_TAIL_GAP_THRESHOLD,
    P10_LIFT_TARGET,
)
from autodrift.public_base_policy_head_trust_region_probe import TARGET_MSE_TOLERANCE
from autodrift.train_ppo import ActorCritic, resolve_device
from autodrift.v4_sequence_objective_probe import _metadata_missing, _read_csv_rows
from autodrift.wrong_history_boundary_relocation_surface import relocate_outcome_snapshot


DEFAULT_BASE_CHECKPOINT = Path("runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt")
DEFAULT_POSITIVE_ROWS = Path("runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv")
DEFAULT_CONTRAST_ROWS = Path("runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv")
DEFAULT_SCENARIO_CONFIG = Path("configs/extreme_fault_distribution_v4_scenarios.json")
DEFAULT_TARGET_ROWS = Path("runs/m919_v4_public_base_expanded_target_regeneration/accepted_target_rows.csv")
DEFAULT_M912_SUMMARY = Path("runs/m912_v4_public_base_sequence_recalibration_audit/summary.json")
DEFAULT_LOW_TAIL_ROWS = Path("runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv")
DEFAULT_M951_ALPHA_METRICS = Path("runs/m951_v4_public_base_rejected_branch_boundary_retune_probe/alpha_metrics.csv")
DEFAULT_M951_M267_PREFLIGHT = Path(
    "runs/m951_v4_public_base_rejected_branch_boundary_retune_probe/m267_preflight_summary.csv"
)
DEFAULT_M267_CORPUS = Path("runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv")
DEFAULT_ENV_CONFIG = Path("configs/m121_human_view_zero_obstacle_relvel.json")
DEFAULT_RUN_DIR = Path("runs/m954_v4_public_base_replay_constrained_target_feasibility")
DEFAULT_ACTIVE_ROW_IDS = (6, 13, 15, 16)
DEFAULT_PROJECTION_DRIFT_BUDGETS = (0.0035, 0.004, 0.005, 0.006, 0.007, 0.008)
DEFAULT_PROJECTION_SCALES = (0.75, 1.0, 1.25)
DEFAULT_TARGET_BLENDS = (0.25, 0.5, 0.75, 1.0)


def classify_target_feasibility(
    *,
    contract_changed: bool,
    training_started: bool,
    ppo_used: bool,
    promoted: bool,
    reconstruction_success_rate: float,
    metadata_missing_rows: int,
    exact_target_candidate_count: int,
    m267_target_preflight_pass_count: int,
    joint_feasible_target_count: int,
) -> str:
    if bool(contract_changed) or bool(training_started) or bool(ppo_used) or bool(promoted):
        return "replay_constrained_target_feasibility_contract_artifact"
    if float(reconstruction_success_rate) < 0.98 or int(metadata_missing_rows) > 0:
        return "replay_constrained_target_feasibility_reconstruction_blocked"
    if int(joint_feasible_target_count) > 0:
        return "replay_constrained_target_feasibility_joint_candidate"
    if int(exact_target_candidate_count) > 0 and int(m267_target_preflight_pass_count) > 0:
        return "replay_constrained_target_feasibility_family_mismatch"
    if int(exact_target_candidate_count) > 0:
        return "replay_constrained_target_feasibility_m267_preflight_failure"
    if int(m267_target_preflight_pass_count) > 0:
        return "replay_constrained_target_feasibility_low_tail_exact_failure"
    return "replay_constrained_target_feasibility_no_candidate"


def _requests(frame: pd.DataFrame) -> dict[int, set[int]]:
    requests: dict[int, set[int]] = {}
    for _, row in frame.iterrows():
        requests.setdefault(int(row["left_seed"]), set()).add(int(row["left_step"]))
        requests.setdefault(int(row["right_seed"]), set()).add(int(row["right_step"]))
    return requests


def _snapshot(snapshots: dict[tuple[int, int], OutcomeSnapshot], seed: int, step: int) -> OutcomeSnapshot:
    key = (int(seed), int(step))
    if key not in snapshots:
        raise ValueError(f"missing reconstructed boundary snapshot seed={seed} step={step}")
    return snapshots[key]


def _clip_action(action: torch.Tensor) -> torch.Tensor:
    return torch.clamp(action, -1.0, 1.0)


def _candidate_metrics(
    *,
    family: str,
    normal_actions: torch.Tensor,
    intervention_actions: torch.Tensor,
    base_normal_actions: torch.Tensor,
    target_actions: torch.Tensor,
    target_mask: torch.Tensor,
    strict_mask: torch.Tensor,
    near_mask: torch.Tensor,
    target_gaps: torch.Tensor,
    near_base_gap_p10: float,
    near_base_gap_deficit_mean: float,
    near_base_low_tail_fraction: float,
    baseline_target_mse_mean: float,
) -> dict[str, Any]:
    normal_delta = normal_actions - base_normal_actions
    normal_drift = torch.linalg.norm(normal_delta, dim=-1).detach().cpu().numpy()
    normal_anchor_mse = torch.mean(normal_delta.pow(2), dim=-1).detach().cpu().numpy()
    gap = torch.linalg.norm(intervention_actions - normal_actions, dim=-1).detach().cpu().numpy()
    target = target_gaps.detach().cpu().numpy()
    gap_deficit = np.maximum(0.0, target - gap)
    low_tail_after = (gap < float(LOW_TAIL_GAP_THRESHOLD)) | (gap_deficit > float(LOW_TAIL_DEFICIT_THRESHOLD))
    target_mse_all = torch.mean((normal_actions - target_actions).pow(2), dim=-1).detach().cpu().numpy()
    target_mask_np = target_mask.detach().cpu().numpy().astype(bool)
    strict_mask_np = strict_mask.detach().cpu().numpy().astype(bool)
    near_mask_np = near_mask.detach().cpu().numpy().astype(bool)
    target_mse = target_mse_all[target_mask_np]
    strict_target_mse = target_mse_all[target_mask_np & strict_mask_np]
    near_target_mse = target_mse_all[target_mask_np & near_mask_np]
    row: dict[str, Any] = {
        "family": str(family),
        "sample_count": int(gap.shape[0]),
        "target_rows": int(np.sum(target_mask_np)),
        "normal_anchor_mse_mean": _mean(normal_anchor_mse),
        "normal_anchor_mse_p95": _percentile(normal_anchor_mse, 95),
        "first_action_drift_from_base_mean": _mean(normal_drift),
        "first_action_drift_from_base_p95": _percentile(normal_drift, 95),
        "normal_intervention_gap_mean": _mean(gap),
        "normal_intervention_gap_p10": _percentile(gap, 10),
        "gap_deficit_mean": _mean(gap_deficit),
        "gap_deficit_p95": _percentile(gap_deficit, 95),
        "low_tail_rows": int(np.sum(low_tail_after)),
        "low_tail_fraction": float(np.mean(low_tail_after.astype(np.float32))) if low_tail_after.size else 0.0,
        "target_action_mse_mean": _mean(target_mse),
        "strict_target_action_mse_mean": _mean(strict_target_mse),
        "near_tail_target_action_mse_mean": _mean(near_target_mse),
        "baseline_target_action_mse_mean": float(baseline_target_mse_mean),
    }
    row["normal_retention_pass"] = bool(
        row["normal_anchor_mse_mean"] <= 0.000004
        and row["normal_anchor_mse_p95"] <= 0.000025
        and row["first_action_drift_from_base_mean"] <= 0.003
        and row["first_action_drift_from_base_p95"] <= 0.008
    )
    row["tail_lift_pass"] = bool(
        row["normal_intervention_gap_p10"] >= float(near_base_gap_p10) + P10_LIFT_TARGET
        and row["gap_deficit_mean"] <= float(near_base_gap_deficit_mean) - DEFICIT_LIFT_TARGET
        and row["low_tail_fraction"] <= float(near_base_low_tail_fraction) - LOW_TAIL_FRACTION_LIFT_TARGET
    )
    row["target_loss_pass"] = bool(
        row["target_action_mse_mean"] < baseline_target_mse_mean
        and row["strict_target_action_mse_mean"] < baseline_target_mse_mean
    )
    row["target_tolerance_pass"] = bool(
        row["target_action_mse_mean"] <= baseline_target_mse_mean + TARGET_MSE_TOLERANCE
        and row["strict_target_action_mse_mean"] <= baseline_target_mse_mean + TARGET_MSE_TOLERANCE
    )
    row["exact_target_candidate"] = bool(
        row["normal_retention_pass"] and row["tail_lift_pass"] and row["target_tolerance_pass"]
    )
    row["normal_safe_low_tail_trend"] = bool(
        row["normal_retention_pass"]
        and row["low_tail_fraction"] < float(near_base_low_tail_fraction)
        and row["gap_deficit_mean"] < float(near_base_gap_deficit_mean)
    )
    return row


def _strict_near_masks(
    meta_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor]:
    target_by_key = {_key(row): row for row in target_rows}
    strict_values = []
    near_values = []
    for row in meta_rows:
        source_label = str(target_by_key.get(_key(row), {}).get("source_label", ""))
        strict_values.append(source_label == "strict_low_tail")
        near_values.append(source_label == "near_tail_coverage")
    return (
        torch.as_tensor(strict_values, dtype=torch.bool, device=device),
        torch.as_tensor(near_values, dtype=torch.bool, device=device),
    )


def _projection_targets(
    *,
    base_normal: torch.Tensor,
    intervention: torch.Tensor,
    target_gaps: torch.Tensor,
    low_tail_mask: torch.Tensor,
    drift_budget: float,
    scale: float,
) -> torch.Tensor:
    candidate = base_normal.clone()
    if not bool(low_tail_mask.any()):
        return candidate
    direction = base_normal - intervention
    norm = torch.linalg.norm(direction, dim=-1, keepdim=True)
    direction = direction / torch.clamp(norm, min=1e-6)
    current_gap = torch.linalg.norm(base_normal - intervention, dim=-1)
    needed = torch.relu(target_gaps - current_gap)
    step = torch.minimum(needed * float(scale), torch.full_like(needed, float(drift_budget)))
    candidate[low_tail_mask] = _clip_action(base_normal[low_tail_mask] + step[low_tail_mask].unsqueeze(-1) * direction[low_tail_mask])
    return candidate


def _blend_targets(
    *,
    base_normal: torch.Tensor,
    accepted_targets: torch.Tensor,
    target_mask: torch.Tensor,
    blend: float,
    drift_budget: float,
) -> torch.Tensor:
    candidate = base_normal.clone()
    if not bool(target_mask.any()):
        return candidate
    delta = accepted_targets - base_normal
    norm = torch.linalg.norm(delta, dim=-1, keepdim=True)
    limited = delta * torch.clamp(float(drift_budget) / torch.clamp(norm, min=1e-6), max=1.0)
    candidate[target_mask] = _clip_action(base_normal[target_mask] + float(blend) * limited[target_mask])
    return candidate


def _read_bool(row: dict[str, Any], key: str) -> bool:
    value = row.get(key, False)
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def _existing_direction_metrics(
    *,
    alpha_metrics_path: Path,
    m267_preflight_path: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    alpha_rows = _read_csv_rows(alpha_metrics_path)
    preflight_by_alpha = {float(row["alpha"]): row for row in _read_csv_rows(m267_preflight_path)}
    offline_rows: list[dict[str, Any]] = []
    preflight_rows: list[dict[str, Any]] = []
    for row in alpha_rows:
        family = f"existing_m951_alpha_{float(row['alpha']):.4f}".replace(".", "_")
        offline = {"family": family, **row}
        offline["exact_target_candidate"] = bool(_read_bool(row, "normal_retention_pass") and _read_bool(row, "tail_lift_pass") and _read_bool(row, "target_tolerance_pass"))
        offline_rows.append(offline)
        preflight = preflight_by_alpha.get(float(row["alpha"]))
        if preflight is not None:
            preflight_rows.append(
                {
                    "family": family,
                    "source": "m951_existing_direction",
                    "rows": int(preflight["rows"]),
                    "candidate_success_drop_count": int(preflight["candidate_success_drop_count"]),
                    "normal_success_delta": float(preflight["normal_success_delta"]),
                    "normal_margin_mean_delta": float(preflight["normal_margin_mean_delta"]),
                    "margin_gap_mean_delta": float(preflight["margin_gap_mean_delta"]),
                    "gate_pass": _read_bool(preflight, "gate_pass"),
                    "active_rows_pass": _read_bool(preflight, "active_rows_pass"),
                    "failed_active_rows": str(preflight.get("failed_active_rows", "")),
                }
            )
    return offline_rows, preflight_rows


def _replay_with_first_action_override(
    *,
    model: ActorCritic,
    snapshot: OutcomeSnapshot,
    hidden: torch.Tensor,
    first_action: np.ndarray,
    env_config: Any,
    response_dim: int,
    max_continuation_steps: int,
    device: torch.device,
) -> dict[str, Any]:
    env = copy.deepcopy(snapshot.env)
    obs = snapshot.observation.copy()
    current_hidden = hidden.detach().clone()
    max_steps = int(max_continuation_steps)
    if max_steps <= 0:
        max_steps = max(1, env_config.max_steps - snapshot.step)
    rewards: list[float] = []
    betas: list[float] = []
    actions: list[np.ndarray] = []
    terminated = False
    truncated = False
    info = dict(snapshot.info)
    for step_index in range(max_steps):
        action, next_hidden = deterministic_action_from_hidden(
            model,
            np.asarray(obs, dtype=np.float32),
            current_hidden,
            device,
        )
        if step_index == 0:
            action = np.asarray(first_action, dtype=np.float32)
        actions.append(action)
        obs, reward, terminated, truncated, info = env.step(action)
        rewards.append(float(reward))
        betas.append(float(info.get("beta", float("nan"))))
        current_hidden = next_hidden
        if terminated or truncated:
            break
    beta_abs_peak = float(np.nanmax(np.abs(betas))) if betas else float("nan")
    reason = terminal_reason(info, terminated, truncated, env_config)
    first = actions[0] if actions else np.full(3, float("nan"), dtype=np.float32)
    return {
        "steps": int(len(rewards)),
        "return": float(np.sum(rewards)),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "success": not bool(terminated),
        "collision": bool(info.get("collision", False)),
        "terminal_reason": reason,
        "obstacle_completed": bool(info.get("obstacle_completed", False)),
        "min_clearance_margin": float(info.get("min_clearance_margin", float("nan"))),
        "beta_abs_peak": beta_abs_peak,
        "first_steer": float(first[0]),
        "first_throttle": float(first[1]),
        "first_brake": float(first[2]),
        "response_dim": int(response_dim),
    }


def _m267_target_preflight(
    *,
    model: ActorCritic,
    corpus_csv: Path,
    env_config_path: Path,
    active_row_ids: tuple[int, ...],
    family_names: list[str],
    device: torch.device,
    max_continuation_steps: int,
) -> list[dict[str, Any]]:
    frame = pd.read_csv(corpus_csv)
    validate_corpus_frame(frame)
    active = frame[frame["row_id"].astype(int).isin([int(row_id) for row_id in active_row_ids])].copy()
    active = active.sort_values("row_id").reset_index(drop=True)
    env_config = load_env_config(env_config_path)
    response_dim = response_feature_dim_for_model(model)
    snapshots = collect_requested_outcome_snapshots(
        model=model,
        env_config=env_config,
        requests=_requests(active),
        device=device,
    )
    rows: list[dict[str, Any]] = []
    for family in family_names:
        for _, source in active.iterrows():
            left = _snapshot(snapshots, int(source["left_seed"]), int(source["left_step"]))
            right = _snapshot(snapshots, int(source["right_seed"]), int(source["right_step"]))
            relocated = relocate_outcome_snapshot(
                left,
                body_longitudinal=float(source["relocated_obstacle_body_x"]),
                body_lateral=float(source["relocated_obstacle_body_y"]),
                half_width=float(source["relocated_obstacle_half_width"]),
            )
            normal_action = _base_actions(
                model,
                torch.as_tensor(relocated.observation[None, :], dtype=torch.float32, device=device),
                relocated.hidden.detach().reshape(1, -1).to(device=device, dtype=torch.float32),
            )[0].detach().cpu().numpy()
            wrong_action = _base_actions(
                model,
                torch.as_tensor(relocated.observation[None, :], dtype=torch.float32, device=device),
                right.hidden.detach().reshape(1, -1).to(device=device, dtype=torch.float32),
            )[0].detach().cpu().numpy()
            normal = _replay_with_first_action_override(
                model=model,
                snapshot=relocated,
                hidden=relocated.hidden,
                first_action=normal_action,
                env_config=env_config,
                response_dim=response_dim,
                max_continuation_steps=max_continuation_steps,
                device=device,
            )
            wrong = _replay_with_first_action_override(
                model=model,
                snapshot=relocated,
                hidden=right.hidden,
                first_action=wrong_action,
                env_config=env_config,
                response_dim=response_dim,
                max_continuation_steps=max_continuation_steps,
                device=device,
            )
            normal_margin = float(normal["min_clearance_margin"])
            wrong_margin = float(wrong["min_clearance_margin"])
            margin_gap = normal_margin - wrong_margin if np.isfinite(normal_margin) and np.isfinite(wrong_margin) else float("nan")
            rows.append(
                {
                    "family": str(family),
                    "row_id": int(source["row_id"]),
                    "target": str(source["target"]),
                    "physical_pair_key": str(source["physical_pair_key"]),
                    "left_seed": int(source["left_seed"]),
                    "right_seed": int(source["right_seed"]),
                    "left_step": int(source["left_step"]),
                    "right_step": int(source["right_step"]),
                    "normal_success": bool(normal["success"]),
                    "wrong_history_success": bool(wrong["success"]),
                    "success_drop": bool(normal["success"] and not bool(wrong["success"])),
                    "normal_margin": normal_margin,
                    "wrong_history_margin": wrong_margin,
                    "margin_gap": margin_gap,
                    "normal_first_steer": float(normal["first_steer"]),
                    "normal_first_throttle": float(normal["first_throttle"]),
                    "normal_first_brake": float(normal["first_brake"]),
                    "wrong_first_steer": float(wrong["first_steer"]),
                    "wrong_first_throttle": float(wrong["first_throttle"]),
                    "wrong_first_brake": float(wrong["first_brake"]),
                }
            )
    return rows


def _summarize_m267_preflight(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    frame = pd.DataFrame(rows)
    summary_rows: list[dict[str, Any]] = []
    for family, group in frame.groupby("family", observed=True):
        normal_success_rate = float(group["normal_success"].astype(bool).mean())
        success_drop_count = int(group["success_drop"].astype(bool).sum())
        margins = group["margin_gap"].astype(float)
        failed_active = group[
            (~group["normal_success"].astype(bool)) | (group["wrong_history_success"].astype(bool))
        ]["row_id"].astype(int)
        summary_rows.append(
            {
                "family": str(family),
                "source": "branch_separated_base_first_action_override",
                "rows": int(len(group)),
                "candidate_success_drop_count": success_drop_count,
                "normal_success_delta": float(normal_success_rate - 1.0),
                "normal_margin_mean_delta": 0.0,
                "margin_gap_mean_delta": 0.0,
                "gate_pass": bool(success_drop_count == len(group) and normal_success_rate >= 1.0),
                "active_rows_pass": bool(len(failed_active) == 0),
                "failed_active_rows": " ".join(str(row_id) for row_id in failed_active),
                "margin_gap_mean": float(margins[np.isfinite(margins)].mean()) if np.isfinite(margins).any() else float("nan"),
            }
        )
    return summary_rows


def run_replay_constrained_target_feasibility(
    *,
    checkpoint_path: Path,
    positive_rows_path: Path,
    contrast_rows_path: Path,
    scenario_config_path: Path,
    target_rows_path: Path,
    m912_summary_path: Path,
    low_tail_rows_path: Path,
    m951_alpha_metrics_path: Path,
    m951_m267_preflight_path: Path,
    m267_corpus_path: Path,
    env_config_path: Path,
    run_dir: Path,
    device: str,
    projection_drift_budgets: tuple[float, ...],
    projection_scales: tuple[float, ...],
    target_blends: tuple[float, ...],
    active_row_ids: tuple[int, ...],
    max_continuation_steps: int,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    scenario_config = load_scenario_config(scenario_config_path)
    env_config = load_env_config(Path(scenario_config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    positives = _read_csv_rows(positive_rows_path)
    contrast_rows = _read_csv_rows(contrast_rows_path)
    target_rows = _read_csv_rows(target_rows_path)
    low_tail_rows = _read_csv_rows(low_tail_rows_path)
    metadata_missing_rows = sum(1 for row in positives if _metadata_missing(row))
    from autodrift.public_base_controlled_fusion_surface_probe import _load_trainable_samples

    samples, meta_rows, rejected_rows = _load_trainable_samples(
        model=model,
        positive_rows=positives,
        contrast_rows=contrast_rows,
        scenario_config=scenario_config,
        env_config=env_config,
        device=resolved_device,
    )
    reconstruction_rate = float(len(meta_rows) / max(len(positives), 1))
    target_mask, low_tail_mask, target_actions, _target_weights, weight_rows, missing_target_keys = target_weight_vector(
        meta_rows=meta_rows,
        target_rows=target_rows,
        low_tail_rows=low_tail_rows,
        normal_actions=samples["normal_actions"],
    )
    strict_mask, near_mask = _strict_near_masks(meta_rows, target_rows, resolved_device)
    m912_summary = read_json(m912_summary_path)
    baseline_target_mse = torch.mean(
        (samples["normal_actions"][target_mask] - target_actions[target_mask]).pow(2),
        dim=-1,
    )
    baseline_target_mse_mean = float(baseline_target_mse.mean().detach().item()) if bool(target_mask.any()) else 0.0
    offline_rows: list[dict[str, Any]] = []
    m267_summary_rows: list[dict[str, Any]] = []
    existing_offline, existing_m267 = _existing_direction_metrics(
        alpha_metrics_path=m951_alpha_metrics_path,
        m267_preflight_path=m951_m267_preflight_path,
    )
    offline_rows.extend(existing_offline)
    m267_summary_rows.extend(existing_m267)
    base_normal = samples["normal_actions"]
    base_intervention = samples["intervention_actions"]
    for drift_budget in projection_drift_budgets:
        for scale in projection_scales:
            family = f"projection_gap_scale_{scale:.2f}_drift_{drift_budget:.4f}".replace(".", "_")
            candidate = _projection_targets(
                base_normal=base_normal,
                intervention=base_intervention,
                target_gaps=samples["target_gaps"],
                low_tail_mask=low_tail_mask,
                drift_budget=float(drift_budget),
                scale=float(scale),
            )
            offline_rows.append(
                _candidate_metrics(
                    family=family,
                    normal_actions=candidate,
                    intervention_actions=base_intervention,
                    base_normal_actions=base_normal,
                    target_actions=target_actions,
                    target_mask=target_mask,
                    strict_mask=strict_mask,
                    near_mask=near_mask,
                    target_gaps=samples["target_gaps"],
                    near_base_gap_p10=float(m912_summary["near_base_gap_p10"]),
                    near_base_gap_deficit_mean=float(m912_summary["near_base_gap_deficit_mean"]),
                    near_base_low_tail_fraction=float(m912_summary["low_tail_fraction"]),
                    baseline_target_mse_mean=baseline_target_mse_mean,
                )
            )
    for drift_budget in projection_drift_budgets:
        for blend in target_blends:
            family = f"accepted_target_blend_{blend:.2f}_drift_{drift_budget:.4f}".replace(".", "_")
            candidate = _blend_targets(
                base_normal=base_normal,
                accepted_targets=target_actions,
                target_mask=target_mask,
                blend=float(blend),
                drift_budget=float(drift_budget),
            )
            offline_rows.append(
                _candidate_metrics(
                    family=family,
                    normal_actions=candidate,
                    intervention_actions=base_intervention,
                    base_normal_actions=base_normal,
                    target_actions=target_actions,
                    target_mask=target_mask,
                    strict_mask=strict_mask,
                    near_mask=near_mask,
                    target_gaps=samples["target_gaps"],
                    near_base_gap_p10=float(m912_summary["near_base_gap_p10"]),
                    near_base_gap_deficit_mean=float(m912_summary["near_base_gap_deficit_mean"]),
                    near_base_low_tail_fraction=float(m912_summary["low_tail_fraction"]),
                    baseline_target_mse_mean=baseline_target_mse_mean,
                )
            )
    synthetic_families = [str(row["family"]) for row in offline_rows if not str(row["family"]).startswith("existing_m951")]
    target_preflight_rows = _m267_target_preflight(
        model=model,
        corpus_csv=m267_corpus_path,
        env_config_path=env_config_path,
        active_row_ids=active_row_ids,
        family_names=synthetic_families,
        device=resolved_device,
        max_continuation_steps=max_continuation_steps,
    )
    write_csv_rows(run_dir / "m267_target_preflight_rows.csv", target_preflight_rows)
    m267_summary_rows.extend(_summarize_m267_preflight(target_preflight_rows))
    offline_by_family = {str(row["family"]): row for row in offline_rows}
    m267_by_family = {str(row["family"]): row for row in m267_summary_rows}
    family_names = sorted(set(offline_by_family) | set(m267_by_family))
    family_summary: list[dict[str, Any]] = []
    row_conflicts: list[dict[str, Any]] = []
    for family in family_names:
        offline = offline_by_family.get(family, {})
        preflight = m267_by_family.get(family, {})
        exact_pass = _read_bool(offline, "exact_target_candidate")
        m267_pass = _read_bool(preflight, "gate_pass")
        joint = bool(exact_pass and m267_pass)
        summary_row = {
            "family": family,
            "exact_target_candidate": exact_pass,
            "normal_retention_pass": _read_bool(offline, "normal_retention_pass"),
            "tail_lift_pass": _read_bool(offline, "tail_lift_pass"),
            "target_tolerance_pass": _read_bool(offline, "target_tolerance_pass"),
            "normal_safe_low_tail_trend": _read_bool(offline, "normal_safe_low_tail_trend"),
            "m267_target_preflight_pass": m267_pass,
            "m267_active_rows_pass": _read_bool(preflight, "active_rows_pass"),
            "joint_feasible_target": joint,
            "candidate_success_drop_count": int(preflight.get("candidate_success_drop_count", 0) or 0),
            "failed_active_rows": str(preflight.get("failed_active_rows", "")),
            "gap_deficit_mean": float(offline.get("gap_deficit_mean", float("nan"))),
            "low_tail_fraction": float(offline.get("low_tail_fraction", float("nan"))),
            "first_action_drift_from_base_mean": float(offline.get("first_action_drift_from_base_mean", float("nan"))),
        }
        family_summary.append(summary_row)
        if exact_pass != m267_pass:
            row_conflicts.append(
                {
                    "family": family,
                    "exact_target_candidate": exact_pass,
                    "m267_target_preflight_pass": m267_pass,
                    "conflict_type": "exact_without_m267" if exact_pass else "m267_without_exact",
                    "failed_active_rows": str(preflight.get("failed_active_rows", "")),
                }
            )
    exact_target_candidate_count = sum(1 for row in family_summary if bool(row["exact_target_candidate"]))
    m267_target_preflight_pass_count = sum(1 for row in family_summary if bool(row["m267_target_preflight_pass"]))
    joint_feasible_target_count = sum(1 for row in family_summary if bool(row["joint_feasible_target"]))
    result_class = classify_target_feasibility(
        contract_changed=False,
        training_started=False,
        ppo_used=False,
        promoted=False,
        reconstruction_success_rate=reconstruction_rate,
        metadata_missing_rows=metadata_missing_rows,
        exact_target_candidate_count=exact_target_candidate_count,
        m267_target_preflight_pass_count=m267_target_preflight_pass_count,
        joint_feasible_target_count=joint_feasible_target_count,
    )
    if joint_feasible_target_count > 0:
        next_blocker = "target export and actor-fit objective design"
    elif exact_target_candidate_count > 0 and m267_target_preflight_pass_count == 0:
        next_blocker = "branch-separated target refinement"
    elif m267_target_preflight_pass_count > 0 and exact_target_candidate_count == 0:
        next_blocker = "low-tail threshold or sequence target audit"
    elif exact_target_candidate_count > 0 and m267_target_preflight_pass_count > 0:
        next_blocker = "target-family alignment audit"
    else:
        next_blocker = "target feasibility branch synthesis before widening actor surface"
    write_csv_rows(run_dir / "offline_exact_target_metrics.csv", offline_rows)
    write_csv_rows(run_dir / "m267_target_preflight.csv", m267_summary_rows)
    write_csv_rows(run_dir / "target_family_summary.csv", family_summary)
    write_csv_rows(run_dir / "row_conflicts.csv", row_conflicts)
    write_csv_rows(
        run_dir / "rejected_rows.csv",
        [
            *rejected_rows,
            *({"rejection_reason": "missing_target_join", "key": str(key)} for key in sorted(missing_target_keys)),
        ],
    )
    summary = {
        "run_type": "public_base_replay_constrained_target_feasibility",
        "checkpoint": checkpoint_path,
        "positive_rows_input": positive_rows_path,
        "contrast_rows_input": contrast_rows_path,
        "scenario_config": scenario_config_path,
        "target_rows": target_rows_path,
        "m912_summary": m912_summary_path,
        "low_tail_rows": low_tail_rows_path,
        "m951_alpha_metrics": m951_alpha_metrics_path,
        "m951_m267_preflight": m951_m267_preflight_path,
        "m267_corpus": m267_corpus_path,
        "active_row_ids": list(active_row_ids),
        "positive_rows": int(len(positives)),
        "reconstructed_rows": int(len(meta_rows)),
        "sample_reconstruction_success_rate": reconstruction_rate,
        "metadata_missing_rows": int(metadata_missing_rows),
        "target_rows_count": int(len(target_rows)),
        "joined_target_rows": int(sum(1 for row in weight_rows if bool(row.get("target_available", False)))),
        "missing_target_keys": int(len(missing_target_keys)),
        "low_tail_rows_count": int(len(low_tail_rows)),
        "offline_target_family_count": int(len(offline_rows)),
        "m267_target_preflight_family_count": int(len(m267_summary_rows)),
        "exact_target_candidate_count": int(exact_target_candidate_count),
        "m267_target_preflight_pass_count": int(m267_target_preflight_pass_count),
        "joint_feasible_target_count": int(joint_feasible_target_count),
        "joint_feasible_families": [row["family"] for row in family_summary if bool(row["joint_feasible_target"])],
        "normal_safe_low_tail_trend_count": int(sum(1 for row in family_summary if bool(row["normal_safe_low_tail_trend"]))),
        "row_conflict_count": int(len(row_conflicts)),
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "actor_input_contract_changed": False,
        "private_holdout_used": False,
        "result_class": result_class,
        "next_blocker": next_blocker,
        "summary_json": run_dir / "summary.json",
        "target_family_summary_csv": run_dir / "target_family_summary.csv",
        "offline_exact_target_metrics_csv": run_dir / "offline_exact_target_metrics.csv",
        "m267_target_preflight_csv": run_dir / "m267_target_preflight.csv",
        "row_conflicts_csv": run_dir / "row_conflicts.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def _parse_float_tuple(raw: str) -> tuple[float, ...]:
    return tuple(float(item) for item in str(raw).split(",") if item.strip())


def _parse_int_tuple(raw: str) -> tuple[int, ...]:
    return tuple(int(item) for item in str(raw).split(",") if item.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training replay-constrained target feasibility audit.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_BASE_CHECKPOINT)
    parser.add_argument("--positive-rows", type=Path, default=DEFAULT_POSITIVE_ROWS)
    parser.add_argument("--contrast-rows", type=Path, default=DEFAULT_CONTRAST_ROWS)
    parser.add_argument("--scenario-config", type=Path, default=DEFAULT_SCENARIO_CONFIG)
    parser.add_argument("--target-rows", type=Path, default=DEFAULT_TARGET_ROWS)
    parser.add_argument("--m912-summary", type=Path, default=DEFAULT_M912_SUMMARY)
    parser.add_argument("--low-tail-rows", type=Path, default=DEFAULT_LOW_TAIL_ROWS)
    parser.add_argument("--m951-alpha-metrics", type=Path, default=DEFAULT_M951_ALPHA_METRICS)
    parser.add_argument("--m951-m267-preflight", type=Path, default=DEFAULT_M951_M267_PREFLIGHT)
    parser.add_argument("--m267-corpus", type=Path, default=DEFAULT_M267_CORPUS)
    parser.add_argument("--env-config", type=Path, default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--projection-drift-budgets", type=_parse_float_tuple, default=DEFAULT_PROJECTION_DRIFT_BUDGETS)
    parser.add_argument("--projection-scales", type=_parse_float_tuple, default=DEFAULT_PROJECTION_SCALES)
    parser.add_argument("--target-blends", type=_parse_float_tuple, default=DEFAULT_TARGET_BLENDS)
    parser.add_argument("--active-row-ids", type=_parse_int_tuple, default=DEFAULT_ACTIVE_ROW_IDS)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    args = parser.parse_args()
    summary = run_replay_constrained_target_feasibility(
        checkpoint_path=args.checkpoint,
        positive_rows_path=args.positive_rows,
        contrast_rows_path=args.contrast_rows,
        scenario_config_path=args.scenario_config,
        target_rows_path=args.target_rows,
        m912_summary_path=args.m912_summary,
        low_tail_rows_path=args.low_tail_rows,
        m951_alpha_metrics_path=args.m951_alpha_metrics,
        m951_m267_preflight_path=args.m951_m267_preflight,
        m267_corpus_path=args.m267_corpus,
        env_config_path=args.env_config,
        run_dir=args.run_dir,
        device=args.device,
        projection_drift_budgets=args.projection_drift_budgets,
        projection_scales=args.projection_scales,
        target_blends=args.target_blends,
        active_row_ids=args.active_row_ids,
        max_continuation_steps=args.max_continuation_steps,
    )
    print(f"result_class={summary['result_class']}")
    print(f"joint_feasible_target_count={summary['joint_feasible_target_count']}")
    print(f"summary={summary['summary_json']}")


if __name__ == "__main__":
    main()
