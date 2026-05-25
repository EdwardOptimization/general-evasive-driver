"""No-training full wrong-history response/action intervention for v4."""

from __future__ import annotations

import argparse
import copy
import csv
from pathlib import Path
import time
from typing import Any

import numpy as np
import torch
from torch import nn

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import NOMINAL_FAULT, load_scenario_config
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.hidden_swap_gate import action_trajectory_distances, terminal_reason, zero_action_trajectory_distances
from autodrift.sequence_command_response_intervention import corrupt_sequence_observation
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.temporal_action_boundary_outcome_miner import relocate_temporal_snapshot
from autodrift.temporal_action_response_mismatch import TemporalSnapshot
from autodrift.train_ppo import resolve_device
from autodrift.v4_extreme_hidden_dynamics_data_route import IdentityResidualGate
from autodrift.v4_low_margin_boundary_window_retarget import _append_progress, parse_bool
from autodrift.v4_low_margin_guard_corpus_refresh import max_share, unique_count
from autodrift.v4_low_margin_new_data_route import build_fault_variants
from autodrift.v4_near_boundary_wrong_history_pair_mining import NEAR_BOUNDARY_PAIR_FIELDS
from autodrift.v4_normal_margin_residual_calibration import calibrated_action_from_hidden
from autodrift.v4_residual_closed_loop_replay import _load_residual_head
from autodrift.v4_wrong_cross_fault_history_intervention import (
    GATE_SUMMARY_FIELDS,
    _action_l2,
    _as_float,
    _as_int,
    _diversity,
    _prefix_l2,
    reconstruct_snapshots,
)


RESPONSE_VARIANTS = (
    "normal",
    "wrong_hidden_only",
    "wrong_ego_response_obs",
    "wrong_action_history_obs",
    "wrong_response_action_obs",
    "wrong_ego_response_hidden",
    "wrong_action_history_hidden",
    "wrong_response_action_hidden",
    "zero_command_obs",
)

PAIR_FIELDS = [
    *NEAR_BOUNDARY_PAIR_FIELDS,
    "left_step",
    "right_step",
]

REPLAY_FIELDS = [
    *PAIR_FIELDS,
    "variant",
    "horizon",
    "alpha",
    "normal_success",
    "normal_collision",
    "normal_margin",
    "variant_success",
    "variant_collision",
    "variant_margin",
    "margin_gap_from_normal",
    "success_drop_from_normal",
    "first_action_l2_vs_normal",
    "prefix_l2_mean_vs_normal",
    "prefix_l2_max_vs_normal",
    "terminal_reason",
    "steps",
]

ACCEPTED_FIELDS = [
    *PAIR_FIELDS,
    "accepted_class",
    "accepted_reason",
    "variant",
    "normal_success",
    "normal_collision",
    "normal_margin",
    "variant_success",
    "variant_collision",
    "variant_margin",
    "margin_gap_from_normal",
    "first_action_l2_vs_normal",
    "prefix_l2_mean_vs_normal",
    "zero_command_margin_gap",
    "zero_dominated",
]

VARIANT_SUMMARY_FIELDS = [
    "variant",
    "rows",
    "success_drop_count",
    "collision_count",
    "margin_gap_min",
    "margin_gap_mean",
    "margin_gap_max",
    "first_action_l2_mean",
    "first_action_l2_max",
    "accepted_primary_rows",
    "accepted_component_rows",
    "accepted_mitigation_rows",
]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def compose_wrong_history_observation(left_obs: np.ndarray, right_obs: np.ndarray, *, variant: str) -> np.ndarray:
    """Return left scene context with selected response/action fields swapped."""

    output = np.asarray(left_obs, dtype=np.float32).copy()
    right = np.asarray(right_obs, dtype=np.float32)
    if output.shape != right.shape:
        raise ValueError("left and right observations must have matching shape")
    if output.shape[0] < 12:
        raise ValueError("expected at least 12 observation fields for response/action streams")
    if variant in {"wrong_ego_response_obs", "wrong_ego_response_hidden", "wrong_response_action_obs", "wrong_response_action_hidden"}:
        output[:9] = right[:9]
    if variant in {"wrong_action_history_obs", "wrong_action_history_hidden", "wrong_response_action_obs", "wrong_response_action_hidden"}:
        output[9:12] = right[9:12]
    return output


def _uses_right_hidden(variant: str) -> bool:
    return variant in {
        "wrong_hidden_only",
        "wrong_ego_response_hidden",
        "wrong_action_history_hidden",
        "wrong_response_action_hidden",
    }


def _pair_rows_from_inputs(
    near_boundary_pairs: list[dict[str, str]],
    accepted_boundary_rows: list[dict[str, str]],
    *,
    max_pairs: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    boundary_by_id = {str(_as_int(row.get("candidate_id"))): row for row in accepted_boundary_rows}
    pairs: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for row in near_boundary_pairs:
        left = boundary_by_id.get(str(_as_int(row.get("left_candidate_id"))))
        right = boundary_by_id.get(str(_as_int(row.get("right_candidate_id"))))
        base = {key: row.get(key, "") for key in NEAR_BOUNDARY_PAIR_FIELDS}
        if left is None or right is None:
            rejected.append({**base, "rejection_reason": "missing_boundary_candidate"})
            continue
        pair = {
            **base,
            "left_step": _as_int(left.get("step")),
            "right_step": _as_int(right.get("step")),
            "left_plan": left,
            "right_plan": right,
        }
        pairs.append(pair)
        if len(pairs) >= int(max_pairs):
            break
    return pairs, rejected


def _snapshot_requests(pair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()
    for index, pair in enumerate(pair_rows):
        left = (int(pair["left_source_group_id"]), int(pair["left_step"]))
        right = (int(pair["right_source_group_id"]), int(pair["right_step"]))
        if left not in seen:
            requests.append(
                {
                    "pair_id": index * 2,
                    "left_source_group_id": left[0],
                    "right_source_group_id": left[0],
                    "left_step": left[1],
                    "right_step": left[1],
                    "left_plan": pair["left_plan"],
                    "right_plan": pair["left_plan"],
                }
            )
            seen.add(left)
        if right not in seen:
            requests.append(
                {
                    "pair_id": index * 2 + 1,
                    "left_source_group_id": right[0],
                    "right_source_group_id": right[0],
                    "left_step": right[1],
                    "right_step": right[1],
                    "left_plan": pair["right_plan"],
                    "right_plan": pair["right_plan"],
                }
            )
            seen.add(right)
    return requests


def replay_response_variant(
    *,
    model: Any,
    residual_head: nn.Module,
    identity_gate: nn.Module,
    left_snapshot: TemporalSnapshot,
    right_snapshot: TemporalSnapshot,
    env_config: Any,
    variant: str,
    horizon: int,
    response_dim: int,
    reference_actions: list[np.ndarray] | None,
    max_continuation_steps: int,
    alpha: float,
    device: torch.device,
) -> tuple[dict[str, Any], list[np.ndarray]]:
    env = copy.deepcopy(left_snapshot.env)
    obs = np.asarray(left_snapshot.observation, dtype=np.float32).copy()
    right_obs0 = np.asarray(right_snapshot.observation, dtype=np.float32).copy()
    hidden = (right_snapshot.hidden if _uses_right_hidden(variant) else left_snapshot.hidden).detach().clone()
    max_steps = int(max_continuation_steps)
    if max_steps <= 0:
        max_steps = max(1, int(env_config.max_steps) - int(left_snapshot.step))
    raw_history: list[np.ndarray] = [obs.copy()]
    actions: list[np.ndarray] = []
    rewards: list[float] = []
    betas: list[float] = []
    terminated = False
    truncated = False
    info = dict(left_snapshot.info)
    for step_index in range(max_steps):
        policy_obs = np.asarray(obs, dtype=np.float32).copy()
        if variant == "zero_command_obs":
            policy_obs = corrupt_sequence_observation(
                policy_obs,
                variant=variant,
                step_index=step_index,
                horizon=int(horizon),
                raw_history=raw_history,
                response_dim=response_dim,
            )
        elif step_index == 0 and variant != "normal" and variant != "wrong_hidden_only":
            policy_obs = compose_wrong_history_observation(policy_obs, right_obs0, variant=variant)
        action, next_hidden, _base_action, _raw_delta, _calibrated_delta, _gate = calibrated_action_from_hidden(
            model,
            residual_head,
            identity_gate,
            policy_obs,
            hidden,
            alpha=float(alpha),
            device=device,
        )
        actions.append(action)
        hidden = next_hidden
        obs, reward, terminated, truncated, info = env.step(action)
        raw_history.append(np.asarray(obs, dtype=np.float32).copy())
        rewards.append(float(reward))
        betas.append(float(info.get("beta", float("nan"))))
        if terminated or truncated:
            break
    first_action = actions[0] if actions else None
    if variant == "normal":
        trajectory_distances = zero_action_trajectory_distances(len(actions))
        prefix = {"prefix_l2_mean": 0.0, "prefix_l2_max": 0.0, "prefix_compare_steps": min(len(actions), int(horizon))}
    else:
        trajectory_distances = action_trajectory_distances(actions, reference_actions)
        prefix = _prefix_l2(actions, reference_actions, int(horizon))
    beta_abs_peak = float(np.nanmax(np.abs(betas))) if betas else float("nan")
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
        "terminal_reason": terminal_reason(info, terminated, truncated, env_config),
        "min_clearance_margin": _finite_float(info.get("min_clearance_margin")),
        "beta_abs_peak": beta_abs_peak,
        "first_action_l2_vs_normal": _action_l2(first_action, reference_actions[0] if reference_actions else None) if variant != "normal" else 0.0,
        **trajectory_distances,
        **prefix,
    }, actions


def replay_pair(
    *,
    pair: dict[str, Any],
    left_snapshot: TemporalSnapshot,
    right_snapshot: TemporalSnapshot,
    model: Any,
    residual_head: nn.Module,
    identity_gate: nn.Module,
    env_config: Any,
    response_dim: int,
    max_continuation_steps: int,
    alpha: float,
    device: torch.device,
) -> list[dict[str, Any]]:
    left_plan = pair["left_plan"]
    right_plan = pair["right_plan"]
    left_relocated = relocate_temporal_snapshot(
        left_snapshot,
        body_longitudinal=_as_float(left_plan.get("target_obstacle_body_x")),
        body_lateral=_as_float(left_plan.get("target_obstacle_body_y")),
        half_width=_as_float(left_plan.get("target_obstacle_half_width")),
    )
    right_relocated = relocate_temporal_snapshot(
        right_snapshot,
        body_longitudinal=_as_float(right_plan.get("target_obstacle_body_x")),
        body_lateral=_as_float(right_plan.get("target_obstacle_body_y")),
        half_width=_as_float(right_plan.get("target_obstacle_half_width")),
    )
    horizon = _as_int(left_plan.get("horizon"), 6)
    normal, normal_actions = replay_response_variant(
        model=model,
        residual_head=residual_head,
        identity_gate=identity_gate,
        left_snapshot=left_relocated,
        right_snapshot=right_relocated,
        env_config=env_config,
        variant="normal",
        horizon=horizon,
        response_dim=response_dim,
        reference_actions=None,
        max_continuation_steps=int(max_continuation_steps),
        alpha=float(alpha),
        device=device,
    )
    normal_margin = _finite_float(normal.get("min_clearance_margin"))
    normal_success = parse_bool(normal.get("success", False))
    normal_collision = parse_bool(normal.get("collision", False))
    rows: list[dict[str, Any]] = []
    meta = {key: pair.get(key, "") for key in PAIR_FIELDS}
    for variant in RESPONSE_VARIANTS:
        if variant == "normal":
            result = normal
        else:
            result, _actions = replay_response_variant(
                model=model,
                residual_head=residual_head,
                identity_gate=identity_gate,
                left_snapshot=left_relocated,
                right_snapshot=right_relocated,
                env_config=env_config,
                variant=variant,
                horizon=horizon,
                response_dim=response_dim,
                reference_actions=normal_actions,
                max_continuation_steps=int(max_continuation_steps),
                alpha=float(alpha),
                device=device,
            )
        variant_margin = _finite_float(result.get("min_clearance_margin"))
        rows.append(
            {
                **meta,
                "variant": variant,
                "horizon": horizon,
                "alpha": float(alpha),
                "normal_success": normal_success,
                "normal_collision": normal_collision,
                "normal_margin": normal_margin,
                "variant_success": parse_bool(result.get("success", False)),
                "variant_collision": parse_bool(result.get("collision", False)),
                "variant_margin": variant_margin,
                "margin_gap_from_normal": normal_margin - variant_margin if np.isfinite(normal_margin) and np.isfinite(variant_margin) and variant != "normal" else 0.0,
                "success_drop_from_normal": bool(normal_success and not parse_bool(result.get("success", False))),
                "first_action_l2_vs_normal": _finite_float(result.get("first_action_l2_vs_normal"), default=0.0),
                "prefix_l2_mean_vs_normal": _finite_float(result.get("prefix_l2_mean"), default=0.0),
                "prefix_l2_max_vs_normal": _finite_float(result.get("prefix_l2_max"), default=0.0),
                "terminal_reason": str(result.get("terminal_reason", "")),
                "steps": int(result.get("steps", 0)),
            }
        )
    return rows


def accepted_rows_for_pair(
    pair_rows: list[dict[str, Any]],
    *,
    boundary_margin_threshold: float,
    primary_margin_gap_threshold: float,
    mitigation_margin_gap_threshold: float,
    action_l2_threshold: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    by_variant = {str(row.get("variant", "")): row for row in pair_rows}
    zero_gap = _finite_float(by_variant.get("zero_command_obs", {}).get("margin_gap_from_normal"))
    primary_variants = {
        "wrong_response_action_obs",
        "wrong_ego_response_hidden",
        "wrong_action_history_hidden",
        "wrong_response_action_hidden",
    }
    component_variants = {
        "wrong_hidden_only": "hidden_only",
        "wrong_ego_response_obs": "ego_response_only",
        "wrong_action_history_obs": "action_history_only",
        "wrong_response_action_obs": "response_action_only",
        "wrong_ego_response_hidden": "ego_response_plus_hidden",
        "wrong_action_history_hidden": "action_history_plus_hidden",
        "wrong_response_action_hidden": "response_action_plus_hidden",
    }
    primary: list[dict[str, Any]] = []
    component: list[dict[str, Any]] = []
    mitigation: list[dict[str, Any]] = []
    for row in pair_rows:
        variant = str(row.get("variant", ""))
        if variant in {"normal", "zero_command_obs"}:
            continue
        normal_margin = _finite_float(row.get("normal_margin"))
        margin_gap = _finite_float(row.get("margin_gap_from_normal"))
        action_gap = max(
            _finite_float(row.get("first_action_l2_vs_normal"), default=float("nan")),
            _finite_float(row.get("prefix_l2_mean_vs_normal"), default=float("nan")),
        )
        normal_ok = (
            parse_bool(row.get("normal_success", False))
            and not parse_bool(row.get("normal_collision", False))
            and np.isfinite(normal_margin)
            and 0.0 <= normal_margin <= float(boundary_margin_threshold)
        )
        margin_pass = bool(np.isfinite(margin_gap) and margin_gap >= float(primary_margin_gap_threshold))
        action_pass = bool(np.isfinite(action_gap) and action_gap >= float(action_l2_threshold))
        outcome_pass = parse_bool(row.get("success_drop_from_normal", False))
        zero_dominated = bool(np.isfinite(zero_gap) and np.isfinite(margin_gap) and zero_gap > margin_gap)
        base = {
            **{key: row.get(key, "") for key in PAIR_FIELDS},
            "variant": variant,
            "normal_success": parse_bool(row.get("normal_success", False)),
            "normal_collision": parse_bool(row.get("normal_collision", False)),
            "normal_margin": normal_margin,
            "variant_success": parse_bool(row.get("variant_success", False)),
            "variant_collision": parse_bool(row.get("variant_collision", False)),
            "variant_margin": _finite_float(row.get("variant_margin")),
            "margin_gap_from_normal": margin_gap,
            "first_action_l2_vs_normal": _finite_float(row.get("first_action_l2_vs_normal")),
            "prefix_l2_mean_vs_normal": _finite_float(row.get("prefix_l2_mean_vs_normal")),
            "zero_command_margin_gap": zero_gap,
            "zero_dominated": zero_dominated,
        }
        if normal_ok and ((margin_pass and action_pass) or outcome_pass) and variant in primary_variants:
            primary.append({**base, "accepted_class": "primary_response_history", "accepted_reason": f"{variant}_margin_action_or_outcome"})
        if normal_ok and ((margin_pass and action_pass) or outcome_pass) and variant in component_variants:
            component.append({**base, "accepted_class": component_variants[variant], "accepted_reason": f"{variant}_component_attribution"})
        if np.isfinite(normal_margin) and np.isfinite(margin_gap) and margin_gap >= float(mitigation_margin_gap_threshold):
            mitigation.append({**base, "accepted_class": "mitigation_response_history", "accepted_reason": f"{variant}_worse_mitigation_margin"})
    return primary, component, mitigation


def _variant_summary(rows: list[dict[str, Any]], accepted_primary: list[dict[str, Any]], accepted_component: list[dict[str, Any]], accepted_mitigation: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for variant in RESPONSE_VARIANTS:
        subset = [row for row in rows if str(row.get("variant")) == variant]
        gaps = [_finite_float(row.get("margin_gap_from_normal")) for row in subset if np.isfinite(_finite_float(row.get("margin_gap_from_normal")))]
        actions = [_finite_float(row.get("first_action_l2_vs_normal")) for row in subset if np.isfinite(_finite_float(row.get("first_action_l2_vs_normal")))]
        output.append(
            {
                "variant": variant,
                "rows": int(len(subset)),
                "success_drop_count": int(sum(1 for row in subset if parse_bool(row.get("success_drop_from_normal", False)))),
                "collision_count": int(sum(1 for row in subset if parse_bool(row.get("variant_collision", False)))),
                "margin_gap_min": min(gaps, default=float("nan")),
                "margin_gap_mean": float(np.mean(gaps)) if gaps else float("nan"),
                "margin_gap_max": max(gaps, default=float("nan")),
                "first_action_l2_mean": float(np.mean(actions)) if actions else float("nan"),
                "first_action_l2_max": max(actions, default=float("nan")),
                "accepted_primary_rows": int(sum(1 for row in accepted_primary if str(row.get("variant")) == variant)),
                "accepted_component_rows": int(sum(1 for row in accepted_component if str(row.get("variant")) == variant)),
                "accepted_mitigation_rows": int(sum(1 for row in accepted_mitigation if str(row.get("variant")) == variant)),
            }
        )
    return output


def _classification(
    *,
    actor_changed: bool,
    residual_changed: bool,
    pair_rows: list[dict[str, Any]],
    accepted_primary: list[dict[str, Any]],
    accepted_component: list[dict[str, Any]],
    zero_command_component_like: list[dict[str, Any]],
    min_primary_rows: int,
    min_fault_pairs: int,
    max_seed_dominance: float,
    max_fault_pair_dominance: float,
) -> str:
    if bool(actor_changed) or bool(residual_changed):
        return "v4_full_wrong_history_response_intervention_contract_violation"
    if not pair_rows:
        return "v4_full_wrong_history_response_intervention_pair_empty"
    if not accepted_primary and zero_command_component_like:
        return "v4_full_wrong_history_response_intervention_zero_command_dominated"
    if not accepted_primary and not accepted_component:
        return "v4_full_wrong_history_response_intervention_all_weak"
    metrics = _diversity(accepted_primary)
    passed = bool(
        len(accepted_primary) >= int(min_primary_rows)
        and metrics["unique_fault_family_pair_count"] >= int(min_fault_pairs)
        and metrics["max_left_seed_dominance"] <= float(max_seed_dominance)
        and metrics["max_right_seed_dominance"] <= float(max_seed_dominance)
        and metrics["max_left_fault_family_dominance"] <= float(max_fault_pair_dominance)
        and metrics["max_right_fault_family_dominance"] <= float(max_fault_pair_dominance)
    )
    if passed:
        return "v4_full_wrong_history_response_intervention_pass"
    return "v4_full_wrong_history_response_intervention_sparse_diagnostic"


def _gate_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "gate_name": "actor_checksum_unchanged",
            "value": not bool(summary["actor_backbone_changed"]),
            "threshold": "true",
            "passed": not bool(summary["actor_backbone_changed"]),
            "notes": "no actor training allowed",
        },
        {
            "gate_name": "residual_head_checksum_unchanged",
            "value": not bool(summary["residual_head_changed"]),
            "threshold": "true",
            "passed": not bool(summary["residual_head_changed"]),
            "notes": "no residual-head training allowed",
        },
        {
            "gate_name": "primary_response_history_rows",
            "value": summary["accepted_primary_response_history_rows"],
            "threshold": summary["min_primary_rows"],
            "passed": int(summary["accepted_primary_response_history_rows"]) >= int(summary["min_primary_rows"]),
            "notes": "zero-command rows are separate",
        },
        {
            "gate_name": "ppo_blocked",
            "value": not bool(summary["ppo_used"]),
            "threshold": "true",
            "passed": not bool(summary["ppo_used"]),
            "notes": "M835 cannot promote",
        },
    ]


def run_full_wrong_history_response_intervention(
    *,
    checkpoint_path: Path,
    residual_head_path: Path,
    scenario_config_path: Path,
    near_boundary_pairs_path: Path,
    accepted_boundary_rows_path: Path,
    source_rows_path: Path,
    candidate_plan_rows_path: Path,
    run_dir: Path,
    device: str,
    alpha: float,
    max_pairs: int,
    max_base_faults: int,
    max_fault_specs: int,
    max_snapshots_per_group: int,
    max_steps: int,
    min_step: int,
    snapshot_stride: int,
    warmup_steps: int,
    steer_amplitude: float,
    brake_amplitude: float,
    warmup_period_steps: int,
    max_continuation_steps: int,
    boundary_margin_threshold: float,
    primary_margin_gap_threshold: float,
    mitigation_margin_gap_threshold: float,
    action_l2_threshold: float,
    min_primary_rows: int,
    min_fault_pairs: int,
    max_seed_dominance: float,
    max_fault_pair_dominance: float,
) -> dict[str, Any]:
    start = time.time()
    run_dir.mkdir(parents=True, exist_ok=True)
    progress_path = run_dir / "progress.jsonl"
    if progress_path.exists():
        progress_path.unlink()

    scenario_config = load_scenario_config(scenario_config_path)
    env_config = load_env_config(Path(scenario_config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    if not model.is_online_recurrent:
        raise ValueError("M835 response intervention requires an online recurrent checkpoint")
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    actor_checksum_before = model_parameter_checksum(model)
    residual_head = _load_residual_head(
        residual_head_path,
        expected_feature_dim=int(model.actor_mean.in_features),
        device=resolved_device,
    )
    residual_head.eval()
    for parameter in residual_head.parameters():
        parameter.requires_grad_(False)
    residual_checksum_before = model_parameter_checksum(residual_head)
    response_dim = response_feature_dim_for_model(model)
    identity_gate = IdentityResidualGate().to(resolved_device)

    pair_rows_raw = read_csv_rows(near_boundary_pairs_path)
    accepted_boundary_rows = read_csv_rows(accepted_boundary_rows_path)
    pair_rows, pair_rejections = _pair_rows_from_inputs(pair_rows_raw, accepted_boundary_rows, max_pairs=int(max_pairs))
    requests = _snapshot_requests(pair_rows)
    fault_specs = build_fault_variants(
        list(scenario_config["faults"]),
        max_base_faults=int(max_base_faults),
        max_fault_specs=int(max_fault_specs),
        activation_deltas=(-3, 3),
        severity_deltas=(-0.04, 0.04),
    )
    fault_by_name = {fault.name: fault for fault in [NOMINAL_FAULT, *fault_specs]}
    snapshots, snapshot_rows, snapshot_rejections = reconstruct_snapshots(
        pair_source_rows=requests,
        source_rows=read_csv_rows(source_rows_path),
        fault_by_name=fault_by_name,
        model=model,
        residual_head=residual_head,
        env_config=env_config,
        scenario_config=scenario_config,
        alpha=float(alpha),
        min_step=int(min_step),
        max_steps=int(max_steps),
        snapshot_stride=int(snapshot_stride),
        max_snapshots_per_group=int(max_snapshots_per_group),
        warmup_steps=int(warmup_steps),
        steer_amplitude=float(steer_amplitude),
        brake_amplitude=float(brake_amplitude),
        warmup_period_steps=int(warmup_period_steps),
        device=resolved_device,
    )

    replay_rows: list[dict[str, Any]] = []
    accepted_primary: list[dict[str, Any]] = []
    accepted_component: list[dict[str, Any]] = []
    accepted_mitigation: list[dict[str, Any]] = []
    replay_rejections: list[dict[str, Any]] = []
    for pair in pair_rows:
        left_snapshot = snapshots.get((int(pair["left_source_group_id"]), int(pair["left_step"])))
        right_snapshot = snapshots.get((int(pair["right_source_group_id"]), int(pair["right_step"])))
        if left_snapshot is None or right_snapshot is None:
            replay_rejections.append({**{key: pair.get(key, "") for key in PAIR_FIELDS}, "rejection_reason": "missing_reconstructed_snapshot"})
            continue
        try:
            rows = replay_pair(
                pair=pair,
                left_snapshot=left_snapshot,
                right_snapshot=right_snapshot,
                model=model,
                residual_head=residual_head,
                identity_gate=identity_gate,
                env_config=env_config,
                response_dim=response_dim,
                max_continuation_steps=int(max_continuation_steps),
                alpha=float(alpha),
                device=resolved_device,
            )
        except Exception as exc:
            replay_rejections.append({**{key: pair.get(key, "") for key in PAIR_FIELDS}, "rejection_reason": f"replay_error:{type(exc).__name__}"})
            continue
        replay_rows.extend(rows)
        primary, component, mitigation = accepted_rows_for_pair(
            rows,
            boundary_margin_threshold=float(boundary_margin_threshold),
            primary_margin_gap_threshold=float(primary_margin_gap_threshold),
            mitigation_margin_gap_threshold=float(mitigation_margin_gap_threshold),
            action_l2_threshold=float(action_l2_threshold),
        )
        accepted_primary.extend(primary)
        accepted_component.extend(component)
        accepted_mitigation.extend(mitigation)
        _append_progress(
            progress_path,
            {"stage": "response_intervention_replay", "pair_id": int(pair["pair_id"]), "rows": len(rows)},
        )

    zero_command_component_like = [
        row
        for row in replay_rows
        if row.get("variant") == "zero_command_obs"
        and _finite_float(row.get("margin_gap_from_normal")) >= float(primary_margin_gap_threshold)
        and _finite_float(row.get("first_action_l2_vs_normal")) >= float(action_l2_threshold)
    ]
    variant_summary = _variant_summary(replay_rows, accepted_primary, accepted_component, accepted_mitigation)
    actor_checksum_after = model_parameter_checksum(model)
    residual_checksum_after = model_parameter_checksum(residual_head)
    result_class = _classification(
        actor_changed=bool(actor_checksum_before != actor_checksum_after),
        residual_changed=bool(residual_checksum_before != residual_checksum_after),
        pair_rows=pair_rows,
        accepted_primary=accepted_primary,
        accepted_component=accepted_component,
        zero_command_component_like=zero_command_component_like,
        min_primary_rows=int(min_primary_rows),
        min_fault_pairs=int(min_fault_pairs),
        max_seed_dominance=float(max_seed_dominance),
        max_fault_pair_dominance=float(max_fault_pair_dominance),
    )
    diversity_summary = {
        "input_pairs": _diversity(pair_rows),
        "accepted_primary_response_history": _diversity(accepted_primary),
        "accepted_component_attribution": _diversity(accepted_component),
        "accepted_mitigation": _diversity(accepted_mitigation),
        "zero_command_component_like": _diversity(zero_command_component_like),
    }
    all_rejections = [*pair_rejections, *snapshot_rejections, *replay_rejections]

    write_csv_rows(run_dir / "response_intervention_pair_rows.csv", [{key: row.get(key, "") for key in PAIR_FIELDS} for row in pair_rows], fieldnames=PAIR_FIELDS)
    write_csv_rows(run_dir / "reconstructed_snapshot_rows.csv", snapshot_rows)
    write_csv_rows(run_dir / "response_intervention_replay_rows.csv", replay_rows, fieldnames=REPLAY_FIELDS)
    write_csv_rows(run_dir / "accepted_primary_response_history_rows.csv", accepted_primary, fieldnames=ACCEPTED_FIELDS)
    write_csv_rows(run_dir / "accepted_component_attribution_rows.csv", accepted_component, fieldnames=ACCEPTED_FIELDS)
    write_csv_rows(run_dir / "accepted_mitigation_rows.csv", accepted_mitigation, fieldnames=ACCEPTED_FIELDS)
    write_csv_rows(run_dir / "variant_summary.csv", variant_summary, fieldnames=VARIANT_SUMMARY_FIELDS)
    write_csv_rows(run_dir / "rejected_rows.csv", all_rejections)
    write_json(run_dir / "diversity_summary.json", diversity_summary)

    summary = {
        "run_type": "v4_full_wrong_history_response_intervention",
        "checkpoint": checkpoint_path,
        "residual_head": residual_head_path,
        "scenario_config": scenario_config_path,
        "near_boundary_pairs": near_boundary_pairs_path,
        "accepted_boundary_rows": accepted_boundary_rows_path,
        "source_rows": source_rows_path,
        "candidate_plan_rows": candidate_plan_rows_path,
        "alpha": float(alpha),
        "raw_pair_rows": int(len(pair_rows_raw)),
        "selected_pair_rows": int(len(pair_rows)),
        "reconstructed_snapshot_rows": int(len(snapshot_rows)),
        "response_intervention_replay_rows": int(len(replay_rows)),
        "accepted_primary_response_history_rows": int(len(accepted_primary)),
        "accepted_component_attribution_rows": int(len(accepted_component)),
        "accepted_mitigation_rows": int(len(accepted_mitigation)),
        "zero_command_component_like_rows": int(len(zero_command_component_like)),
        "rejected_rows": int(len(all_rejections)),
        "boundary_margin_threshold": float(boundary_margin_threshold),
        "primary_margin_gap_threshold": float(primary_margin_gap_threshold),
        "mitigation_margin_gap_threshold": float(mitigation_margin_gap_threshold),
        "action_l2_threshold": float(action_l2_threshold),
        "min_primary_rows": int(min_primary_rows),
        "diversity_summary_json": run_dir / "diversity_summary.json",
        "actor_backbone_changed": bool(actor_checksum_before != actor_checksum_after),
        "residual_head_changed": bool(residual_checksum_before != residual_checksum_after),
        "base_actor_checksum_before": actor_checksum_before,
        "base_actor_checksum_after": actor_checksum_after,
        "residual_head_checksum_before": residual_checksum_before,
        "residual_head_checksum_after": residual_checksum_after,
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "result_class": result_class,
        "elapsed_seconds": float(time.time() - start),
        "summary_json": run_dir / "summary.json",
        "response_intervention_pair_rows_csv": run_dir / "response_intervention_pair_rows.csv",
        "response_intervention_replay_rows_csv": run_dir / "response_intervention_replay_rows.csv",
        "accepted_primary_response_history_rows_csv": run_dir / "accepted_primary_response_history_rows.csv",
        "accepted_component_attribution_rows_csv": run_dir / "accepted_component_attribution_rows.csv",
        "accepted_mitigation_rows_csv": run_dir / "accepted_mitigation_rows.csv",
        "variant_summary_csv": run_dir / "variant_summary.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
        "gate_summary_csv": run_dir / "gate_summary.csv",
        "progress_jsonl": progress_path,
    }
    write_csv_rows(run_dir / "gate_summary.csv", _gate_rows(summary), fieldnames=GATE_SUMMARY_FIELDS)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training v4 full wrong-history response intervention.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--residual-head", type=Path, required=True)
    parser.add_argument("--scenario-config", type=Path, required=True)
    parser.add_argument("--near-boundary-pairs", type=Path, required=True)
    parser.add_argument("--accepted-boundary-rows", type=Path, required=True)
    parser.add_argument("--source-rows", type=Path, required=True)
    parser.add_argument("--candidate-plan-rows", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--max-pairs", type=int, default=160)
    parser.add_argument("--max-base-faults", type=int, default=10)
    parser.add_argument("--max-fault-specs", type=int, default=18)
    parser.add_argument("--max-snapshots-per-group", type=int, default=1)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--min-step", type=int, default=None)
    parser.add_argument("--snapshot-stride", type=int, default=None)
    parser.add_argument("--warmup-steps", type=int, default=24)
    parser.add_argument("--steer-amplitude", type=float, default=0.08)
    parser.add_argument("--brake-amplitude", type=float, default=0.08)
    parser.add_argument("--warmup-period-steps", type=int, default=8)
    parser.add_argument("--max-continuation-steps", type=int, default=None)
    parser.add_argument("--boundary-margin-threshold", type=float, default=0.05)
    parser.add_argument("--primary-margin-gap-threshold", type=float, default=0.01)
    parser.add_argument("--mitigation-margin-gap-threshold", type=float, default=0.02)
    parser.add_argument("--action-l2-threshold", type=float, default=0.014)
    parser.add_argument("--min-primary-rows", type=int, default=80)
    parser.add_argument("--min-fault-pairs", type=int, default=6)
    parser.add_argument("--max-seed-dominance", type=float, default=0.25)
    parser.add_argument("--max-fault-pair-dominance", type=float, default=0.35)
    args = parser.parse_args()

    scenario_config = load_scenario_config(args.scenario_config)
    max_steps = int(args.max_steps) if args.max_steps is not None else int(scenario_config.get("max_steps", 340))
    min_step = int(args.min_step) if args.min_step is not None else int(scenario_config.get("min_step", 20))
    snapshot_stride = int(args.snapshot_stride) if args.snapshot_stride is not None else int(scenario_config.get("snapshot_stride", 3))
    max_continuation_steps = (
        int(args.max_continuation_steps)
        if args.max_continuation_steps is not None
        else int(scenario_config.get("max_continuation_steps", 70))
    )
    summary = run_full_wrong_history_response_intervention(
        checkpoint_path=args.checkpoint,
        residual_head_path=args.residual_head,
        scenario_config_path=args.scenario_config,
        near_boundary_pairs_path=args.near_boundary_pairs,
        accepted_boundary_rows_path=args.accepted_boundary_rows,
        source_rows_path=args.source_rows,
        candidate_plan_rows_path=args.candidate_plan_rows,
        run_dir=args.run_dir,
        device=args.device,
        alpha=float(args.alpha),
        max_pairs=int(args.max_pairs),
        max_base_faults=int(args.max_base_faults),
        max_fault_specs=int(args.max_fault_specs),
        max_snapshots_per_group=int(args.max_snapshots_per_group),
        max_steps=max_steps,
        min_step=min_step,
        snapshot_stride=snapshot_stride,
        warmup_steps=int(args.warmup_steps),
        steer_amplitude=float(args.steer_amplitude),
        brake_amplitude=float(args.brake_amplitude),
        warmup_period_steps=int(args.warmup_period_steps),
        max_continuation_steps=max_continuation_steps,
        boundary_margin_threshold=float(args.boundary_margin_threshold),
        primary_margin_gap_threshold=float(args.primary_margin_gap_threshold),
        mitigation_margin_gap_threshold=float(args.mitigation_margin_gap_threshold),
        action_l2_threshold=float(args.action_l2_threshold),
        min_primary_rows=int(args.min_primary_rows),
        min_fault_pairs=int(args.min_fault_pairs),
        max_seed_dominance=float(args.max_seed_dominance),
        max_fault_pair_dominance=float(args.max_fault_pair_dominance),
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
