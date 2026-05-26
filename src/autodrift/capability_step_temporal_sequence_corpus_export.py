"""Export M994 temporal sequence rows into an exact-auditable tensor corpus."""

from __future__ import annotations

import argparse
import copy
import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.capability_step_sequence_intervention_probe import (
    CROSS_FAULT_SEQUENCE_VARIANTS,
    TEMPORAL_HISTORY_VARIANTS,
    build_variant_hiddens,
    collect_fault_trace_window,
    fault_map_from_config,
)
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import load_scenario_config
from autodrift.hidden_swap_gate import action_trajectory_distances, terminal_reason, zero_action_trajectory_distances
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.train_ppo import ActorCritic, resolve_device


POSITIVE_TEMPORAL_VARIANTS = ("reset_then_warm_history", "delayed_capability_history")
DIAGNOSTIC_ONLY_VARIANTS = tuple(
    sorted(set(CROSS_FAULT_SEQUENCE_VARIANTS) | (set(TEMPORAL_HISTORY_VARIANTS) - set(POSITIVE_TEMPORAL_VARIANTS)))
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def actor_checksum(model: torch.nn.Module) -> float:
    return float(sum(float(param.detach().cpu().double().sum()) for param in model.parameters()))


def load_positive_temporal_rows(m994_run_dir: Path) -> pd.DataFrame:
    accepted_path = m994_run_dir / "accepted_sequence_rows.csv"
    if not accepted_path.exists():
        raise FileNotFoundError(f"missing accepted sequence rows: {accepted_path}")
    rows = pd.read_csv(accepted_path)
    if rows.empty:
        raise ValueError(f"{accepted_path} is empty")
    if "variant" not in rows.columns:
        raise ValueError(f"{accepted_path} must contain a variant column")
    positive = rows[rows["variant"].isin(POSITIVE_TEMPORAL_VARIANTS)].copy()
    positive = positive[positive.get("sequence_outcome_critical", True).astype(bool)].copy()
    if positive.empty:
        raise ValueError("no positive temporal sequence rows found")
    positive.reset_index(drop=True, inplace=True)
    return positive


def load_diagnostic_rows(m994_run_dir: Path) -> pd.DataFrame:
    path = m994_run_dir / "sequence_intervention_rows.csv"
    if not path.exists():
        return pd.DataFrame()
    rows = pd.read_csv(path)
    if rows.empty or "variant" not in rows.columns:
        return pd.DataFrame()
    diagnostic = rows[rows["variant"].isin(DIAGNOSTIC_ONLY_VARIANTS)].copy()
    diagnostic["positive_target"] = False
    diagnostic["diagnostic_only"] = True
    return diagnostic.reset_index(drop=True)


def compute_row_weights(rows: pd.DataFrame) -> np.ndarray:
    if rows.empty:
        return np.zeros((0,), dtype=np.float32)
    variant_counts = rows["variant"].astype(str).value_counts().to_dict()
    pair_counts = rows["fault_pair"].astype(str).value_counts().to_dict()
    weights = []
    for _, row in rows.iterrows():
        variant_count = max(1, int(variant_counts[str(row["variant"])]))
        pair_count = max(1, int(pair_counts[str(row["fault_pair"])]))
        weights.append(1.0 / float(np.sqrt(variant_count * pair_count)))
    output = np.asarray(weights, dtype=np.float32)
    mean = float(output.mean()) if output.size else 1.0
    if mean <= 0.0 or not np.isfinite(mean):
        raise ValueError("row weights have invalid mean")
    return (output / mean).astype(np.float32)


def _pad_2d_sequence(items: list[np.ndarray], *, length: int, width: int) -> tuple[np.ndarray, np.ndarray]:
    values = np.zeros((int(length), int(width)), dtype=np.float32)
    mask = np.zeros((int(length),), dtype=bool)
    for idx, item in enumerate(items[: int(length)]):
        arr = np.asarray(item, dtype=np.float32).reshape(-1)
        if arr.shape[0] != int(width):
            raise ValueError(f"expected width {width}, got {arr.shape[0]}")
        values[idx] = arr
        mask[idx] = True
    return values, mask


def replay_sequence_with_initial_hidden(
    *,
    model: ActorCritic,
    snapshot: Any,
    variant: str,
    initial_hidden: torch.Tensor,
    max_sequence_len: int,
    normal_first_action: np.ndarray | None,
    normal_actions: list[np.ndarray] | None,
    device: torch.device,
) -> tuple[dict[str, Any], list[np.ndarray], list[np.ndarray]]:
    env = copy.deepcopy(snapshot.env)
    obs = np.asarray(snapshot.observation, dtype=np.float32).copy()
    hidden = initial_hidden.detach().clone()
    observations: list[np.ndarray] = []
    actions: list[np.ndarray] = []
    rewards: list[float] = []
    betas: list[float] = []
    terminated = False
    truncated = False
    info = dict(snapshot.info)
    for _ in range(max(1, int(max_sequence_len))):
        observations.append(obs.copy())
        action, next_hidden = deterministic_action_from_hidden(model, obs, hidden, device)
        actions.append(action)
        obs, reward, terminated, truncated, info = env.step(action)
        hidden = next_hidden
        rewards.append(float(reward))
        betas.append(float(info.get("beta", float("nan"))))
        if terminated or truncated:
            break
    first_action = actions[0] if actions else np.full(3, float("nan"), dtype=np.float32)
    first_action_distance = 0.0 if normal_first_action is None else float(np.linalg.norm(first_action - normal_first_action))
    trajectory_distances = (
        zero_action_trajectory_distances(len(actions))
        if normal_actions is None
        else action_trajectory_distances(actions, normal_actions)
    )
    beta_abs_peak = float(np.nanmax(np.abs(betas))) if betas else float("nan")
    reason = terminal_reason(info, terminated, truncated, env.config)
    return (
        {
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
            "min_clearance_margin": float(info.get("min_clearance_margin", float("nan"))),
            "beta_abs_peak": beta_abs_peak,
            "first_steer": float(first_action[0]),
            "first_throttle": float(first_action[1]),
            "first_brake": float(first_action[2]),
            "first_action_distance": first_action_distance,
            **trajectory_distances,
        },
        observations,
        actions,
    )


def _replay_action_l2_max(
    *,
    model: ActorCritic,
    observations: np.ndarray,
    actions: np.ndarray,
    masks: np.ndarray,
    hiddens: np.ndarray,
    device: torch.device,
) -> float:
    max_diff = 0.0
    for row_idx in range(observations.shape[0]):
        hidden = torch.as_tensor(hiddens[row_idx], dtype=torch.float32, device=device).unsqueeze(0)
        for step_idx in range(observations.shape[1]):
            if not bool(masks[row_idx, step_idx]):
                break
            action, hidden = deterministic_action_from_hidden(
                model,
                np.asarray(observations[row_idx, step_idx], dtype=np.float32),
                hidden,
                device,
            )
            diff = float(np.linalg.norm(action - actions[row_idx, step_idx]))
            max_diff = max(max_diff, diff)
    return max_diff


def _sequence_logp_sums(
    *,
    model: ActorCritic,
    observations: np.ndarray,
    actions: np.ndarray,
    masks: np.ndarray,
    hiddens: np.ndarray,
    device: torch.device,
) -> np.ndarray:
    output = np.zeros((observations.shape[0],), dtype=np.float32)
    model.eval()
    with torch.no_grad():
        for row_idx in range(observations.shape[0]):
            length = int(np.asarray(masks[row_idx], dtype=bool).sum())
            if length <= 0:
                output[row_idx] = np.nan
                continue
            obs_t = torch.as_tensor(observations[row_idx, :length], dtype=torch.float32, device=device).unsqueeze(1)
            act_t = torch.as_tensor(actions[row_idx, :length], dtype=torch.float32, device=device).unsqueeze(1)
            done_t = torch.zeros((length, 1), dtype=torch.bool, device=device)
            hidden_t = torch.as_tensor(hiddens[row_idx], dtype=torch.float32, device=device).unsqueeze(0)
            logp, _entropy, _value = model.evaluate_actions_recurrent_sequence(obs_t, act_t, hidden_t, done_t)
            output[row_idx] = float(logp.sum().detach().cpu().item())
    return output


def _variant_ids(variants: pd.Series) -> tuple[np.ndarray, dict[str, int]]:
    names = sorted(str(name) for name in variants.unique())
    mapping = {name: idx for idx, name in enumerate(names)}
    ids = np.asarray([mapping[str(name)] for name in variants], dtype=np.int64)
    return ids, mapping


def export_temporal_sequence_corpus(
    *,
    checkpoint_path: Path,
    config_path: Path,
    m994_run_dir: Path,
    max_sequence_len: int,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    positive_rows = load_positive_temporal_rows(m994_run_dir)
    diagnostic_rows = load_diagnostic_rows(m994_run_dir)
    weights = compute_row_weights(positive_rows)
    config = load_scenario_config(config_path)
    env_config = load_env_config(Path(config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    fault_by_name = fault_map_from_config(config)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    checksum_before = actor_checksum(model)
    hidden_size = int(model.actor_mean.in_features)
    obs_dim = int(model.obs_dim)
    action_dim = int(model.act_dim)
    trace_cache: dict[tuple[int, str, int, int], list[Any]] = {}

    def trace_for(seed: int, fault_name: str, step: int, history_length: int) -> list[Any]:
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

    decision_obs: list[np.ndarray] = []
    normal_hiddens: list[np.ndarray] = []
    variant_hiddens: list[np.ndarray] = []
    normal_obs_seqs: list[np.ndarray] = []
    variant_obs_seqs: list[np.ndarray] = []
    normal_action_seqs: list[np.ndarray] = []
    variant_action_seqs: list[np.ndarray] = []
    normal_masks: list[np.ndarray] = []
    variant_masks: list[np.ndarray] = []
    metadata_rows: list[dict[str, Any]] = []

    for row_id, row in positive_rows.iterrows():
        seed = int(row["seed"])
        preferred_fault = str(row["preferred_fault"])
        wrong_fault = str(row["wrong_fault"])
        preferred_step = int(row["preferred_step"])
        wrong_step = int(row["wrong_step"])
        history_length = int(row["history_length"])
        variant = str(row["variant"])
        if variant not in POSITIVE_TEMPORAL_VARIANTS:
            raise ValueError(f"unexpected positive variant: {variant}")
        preferred_trace = trace_for(seed, preferred_fault, preferred_step, history_length)
        wrong_trace = trace_for(seed, wrong_fault, wrong_step, history_length)
        preferred_snapshot = preferred_trace[-1]
        variant_hidden_map = build_variant_hiddens(
            model=model,
            preferred_trace=preferred_trace,
            wrong_trace=wrong_trace,
            device=resolved_device,
        )
        if variant not in variant_hidden_map:
            raise ValueError(f"variant {variant!r} not reconstructed")
        normal_hidden = preferred_snapshot.hidden.detach().clone()
        variant_hidden = variant_hidden_map[variant].detach().clone()
        normal_result, normal_observations, normal_actions = replay_sequence_with_initial_hidden(
            model=model,
            snapshot=preferred_snapshot,
            variant="normal",
            initial_hidden=normal_hidden,
            max_sequence_len=max_sequence_len,
            normal_first_action=None,
            normal_actions=None,
            device=resolved_device,
        )
        normal_first_action = np.asarray(
            [normal_result["first_steer"], normal_result["first_throttle"], normal_result["first_brake"]],
            dtype=np.float32,
        )
        variant_result, variant_observations, variant_actions = replay_sequence_with_initial_hidden(
            model=model,
            snapshot=preferred_snapshot,
            variant=variant,
            initial_hidden=variant_hidden,
            max_sequence_len=max_sequence_len,
            normal_first_action=normal_first_action,
            normal_actions=normal_actions,
            device=resolved_device,
        )
        normal_obs, normal_mask = _pad_2d_sequence(normal_observations, length=max_sequence_len, width=obs_dim)
        variant_obs, variant_mask = _pad_2d_sequence(variant_observations, length=max_sequence_len, width=obs_dim)
        normal_actions_padded, _ = _pad_2d_sequence(normal_actions, length=max_sequence_len, width=action_dim)
        variant_actions_padded, _ = _pad_2d_sequence(variant_actions, length=max_sequence_len, width=action_dim)
        normal_margin = float(normal_result.get("min_clearance_margin", float("nan")))
        variant_margin = float(variant_result.get("min_clearance_margin", float("nan")))
        margin_gap = normal_margin - variant_margin if np.isfinite(normal_margin) and np.isfinite(variant_margin) else float("nan")
        decision_obs.append(np.asarray(preferred_snapshot.observation, dtype=np.float32).reshape(obs_dim))
        normal_hiddens.append(normal_hidden.detach().cpu().numpy().reshape(hidden_size).astype(np.float32))
        variant_hiddens.append(variant_hidden.detach().cpu().numpy().reshape(hidden_size).astype(np.float32))
        normal_obs_seqs.append(normal_obs)
        variant_obs_seqs.append(variant_obs)
        normal_action_seqs.append(normal_actions_padded)
        variant_action_seqs.append(variant_actions_padded)
        normal_masks.append(normal_mask)
        variant_masks.append(variant_mask)
        metadata_rows.append(
            {
                "row_id": int(row_id),
                "source_index": int(row.get("source_index", row_id)),
                "seed": seed,
                "preferred_fault": preferred_fault,
                "preferred_fault_family": str(row.get("preferred_fault_family", "")),
                "wrong_fault": wrong_fault,
                "wrong_fault_family": str(row.get("wrong_fault_family", "")),
                "fault_pair": str(row.get("fault_pair", "")),
                "history_length": history_length,
                "variant": variant,
                "preferred_step": preferred_step,
                "wrong_step": wrong_step,
                "normal_success": bool(normal_result.get("success", False)),
                "variant_success": bool(variant_result.get("success", False)),
                "success_drop": bool(bool(normal_result.get("success", False)) and not bool(variant_result.get("success", False))),
                "normal_margin": normal_margin,
                "variant_margin": variant_margin,
                "margin_gap": margin_gap,
                "normal_terminal_reason": str(normal_result.get("terminal_reason", "")),
                "variant_terminal_reason": str(variant_result.get("terminal_reason", "")),
                "first_action_l2": float(variant_result.get("first_action_distance", float("nan"))),
                "sequence_action_l2_mean": float(variant_result.get("action_trajectory_distance_mean", float("nan"))),
                "sequence_action_l2_max": float(variant_result.get("action_trajectory_distance_max", float("nan"))),
                "row_weight": float(weights[int(row_id)]),
                "positive_target": True,
                "diagnostic_only": False,
            }
        )

    arrays = {
        "decision_observation": np.stack(decision_obs).astype(np.float32),
        "normal_initial_hidden": np.stack(normal_hiddens).astype(np.float32),
        "variant_initial_hidden": np.stack(variant_hiddens).astype(np.float32),
        "normal_rollout_observations": np.stack(normal_obs_seqs).astype(np.float32),
        "variant_rollout_observations": np.stack(variant_obs_seqs).astype(np.float32),
        "normal_rollout_actions": np.stack(normal_action_seqs).astype(np.float32),
        "variant_rollout_actions": np.stack(variant_action_seqs).astype(np.float32),
        "sequence_mask": np.stack(normal_masks).astype(bool),
        "variant_sequence_mask": np.stack(variant_masks).astype(bool),
        "normal_terminal_margin": np.asarray([row["normal_margin"] for row in metadata_rows], dtype=np.float32),
        "variant_terminal_margin": np.asarray([row["variant_margin"] for row in metadata_rows], dtype=np.float32),
        "terminal_margin_gap": np.asarray([row["margin_gap"] for row in metadata_rows], dtype=np.float32),
        "first_action_l2": np.asarray([row["first_action_l2"] for row in metadata_rows], dtype=np.float32),
        "sequence_action_l2_mean": np.asarray([row["sequence_action_l2_mean"] for row in metadata_rows], dtype=np.float32),
        "sequence_action_l2_max": np.asarray([row["sequence_action_l2_max"] for row in metadata_rows], dtype=np.float32),
        "row_weight": weights.astype(np.float32),
        "history_length": positive_rows["history_length"].astype(np.int64).to_numpy(),
    }
    variant_ids, variant_mapping = _variant_ids(positive_rows["variant"])
    arrays["variant_id"] = variant_ids
    np.savez_compressed(run_dir / "temporal_sequence_corpus.npz", **arrays)

    metadata_frame = pd.DataFrame(metadata_rows)
    write_csv_rows(run_dir / "metadata.csv", metadata_rows)
    write_csv_rows(run_dir / "diagnostic_rows.csv", diagnostic_rows.to_dict("records"))
    variant_summary = (
        metadata_frame.groupby("variant", observed=True)
        .agg(rows=("variant", "size"), unique_seeds=("seed", "nunique"), unique_fault_pairs=("fault_pair", "nunique"))
        .reset_index()
        .to_dict("records")
    )
    pair_summary = (
        metadata_frame.groupby("fault_pair", observed=True)
        .agg(rows=("fault_pair", "size"), unique_seeds=("seed", "nunique"))
        .reset_index()
        .to_dict("records")
    )
    history_summary = (
        metadata_frame.groupby("history_length", observed=True)
        .agg(rows=("history_length", "size"), unique_seeds=("seed", "nunique"), unique_fault_pairs=("fault_pair", "nunique"))
        .reset_index()
        .to_dict("records")
    )
    write_csv_rows(run_dir / "variant_summary.csv", variant_summary)
    write_csv_rows(run_dir / "fault_pair_summary.csv", pair_summary)
    write_csv_rows(run_dir / "history_length_summary.csv", history_summary)

    normal_action_l2_max = _replay_action_l2_max(
        model=model,
        observations=arrays["normal_rollout_observations"],
        actions=arrays["normal_rollout_actions"],
        masks=arrays["sequence_mask"],
        hiddens=arrays["normal_initial_hidden"],
        device=resolved_device,
    )
    variant_action_l2_max = _replay_action_l2_max(
        model=model,
        observations=arrays["variant_rollout_observations"],
        actions=arrays["variant_rollout_actions"],
        masks=arrays["variant_sequence_mask"],
        hiddens=arrays["variant_initial_hidden"],
        device=resolved_device,
    )
    normal_logp = _sequence_logp_sums(
        model=model,
        observations=arrays["normal_rollout_observations"],
        actions=arrays["normal_rollout_actions"],
        masks=arrays["sequence_mask"],
        hiddens=arrays["normal_initial_hidden"],
        device=resolved_device,
    )
    variant_on_normal_logp = _sequence_logp_sums(
        model=model,
        observations=arrays["normal_rollout_observations"],
        actions=arrays["normal_rollout_actions"],
        masks=arrays["sequence_mask"],
        hiddens=arrays["variant_initial_hidden"],
        device=resolved_device,
    )
    preference_margin = 0.05
    temporal_preference_loss = np.logaddexp(0.0, variant_on_normal_logp - normal_logp + preference_margin)
    checksum_after = actor_checksum(model)
    actor_parameters_changed = bool(abs(checksum_after - checksum_before) > 1e-8)
    pair_counts = metadata_frame["fault_pair"].value_counts()
    max_pair_fraction = float(pair_counts.max() / len(metadata_frame)) if len(metadata_frame) else 1.0
    unique_positive_fault_pairs = int(metadata_frame["fault_pair"].nunique())
    unique_positive_seeds = int(metadata_frame["seed"].nunique())
    delayed_rows = int((metadata_frame["variant"] == "delayed_capability_history").sum())
    reset_rows = int((metadata_frame["variant"] == "reset_then_warm_history").sum())
    all_finite = all(bool(np.isfinite(value).all()) for value in arrays.values() if value.dtype.kind in {"f", "i", "u"})
    tensor_sanity_passed = bool(
        all_finite
        and arrays["decision_observation"].shape == (len(metadata_frame), obs_dim)
        and arrays["normal_rollout_actions"].shape[2] == action_dim
        and arrays["normal_initial_hidden"].shape == arrays["variant_initial_hidden"].shape
        and bool(arrays["sequence_mask"].any(axis=1).all())
        and abs(float(arrays["row_weight"].mean()) - 1.0) <= 1e-5
    )
    replay_sanity_passed = bool(normal_action_l2_max <= 1e-5 and variant_action_l2_max <= 1e-5)
    exact_sanity_passed = bool(
        np.isfinite(normal_logp).all()
        and np.isfinite(variant_on_normal_logp).all()
        and np.isfinite(temporal_preference_loss).all()
    )
    source_diversity_passed = bool(
        len(metadata_frame) >= 200
        and unique_positive_fault_pairs >= 8
        and unique_positive_seeds >= 16
        and max_pair_fraction <= 0.25
        and delayed_rows >= 20
    )
    corpus_manifest = {
        "checkpoint_path": checkpoint_path,
        "checkpoint_sha256": sha256_file(checkpoint_path),
        "scenario_config_path": config_path,
        "m994_run_dir": m994_run_dir,
        "accepted_rows_path": m994_run_dir / "accepted_sequence_rows.csv",
        "selected_source_rows_path": m994_run_dir / "selected_source_rows.csv",
        "observation_dim": obs_dim,
        "action_dim": action_dim,
        "hidden_dim": hidden_size,
        "max_sequence_len": int(max_sequence_len),
        "allowed_positive_variants": POSITIVE_TEMPORAL_VARIANTS,
        "diagnostic_variants": DIAGNOSTIC_ONLY_VARIANTS,
        "variant_mapping": variant_mapping,
    }
    write_json(run_dir / "corpus_manifest.json", corpus_manifest)
    summary = {
        "run_type": "capability_step_temporal_sequence_corpus_export",
        "checkpoint": checkpoint_path,
        "config": config_path,
        "m994_run_dir": m994_run_dir,
        "row_count": int(len(metadata_frame)),
        "positive_row_count": int(len(metadata_frame)),
        "diagnostic_row_count": int(len(diagnostic_rows)),
        "unique_positive_fault_pairs": unique_positive_fault_pairs,
        "unique_positive_seeds": unique_positive_seeds,
        "max_fault_pair_fraction": max_pair_fraction,
        "delayed_capability_history_positive_rows": delayed_rows,
        "reset_then_warm_history_positive_rows": reset_rows,
        "normal_failed_rows": int((~metadata_frame["normal_success"].astype(bool)).sum()),
        "accepted_cross_fault_positive_rows": 0,
        "normal_action_replay_l2_max": normal_action_l2_max,
        "variant_action_replay_l2_max": variant_action_l2_max,
        "normal_sequence_logp_mean": float(np.mean(normal_logp)),
        "variant_on_normal_sequence_logp_mean": float(np.mean(variant_on_normal_logp)),
        "temporal_logp_gap_mean": float(np.mean(normal_logp - variant_on_normal_logp)),
        "temporal_preference_loss_mean": float(np.mean(temporal_preference_loss)),
        "normal_sequence_nll_mean": float(np.mean(-normal_logp)),
        "variant_on_normal_sequence_nll_mean": float(np.mean(-variant_on_normal_logp)),
        "tensor_sanity_passed": tensor_sanity_passed,
        "replay_sanity_passed": replay_sanity_passed,
        "exact_sanity_passed": exact_sanity_passed,
        "source_diversity_passed": source_diversity_passed,
        "actor_parameters_changed": actor_parameters_changed,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "result_class": (
            "temporal_sequence_corpus_export_pass"
            if tensor_sanity_passed
            and replay_sanity_passed
            and exact_sanity_passed
            and source_diversity_passed
            and not actor_parameters_changed
            else "temporal_sequence_corpus_export_failed_sanity"
        ),
        "corpus_npz": run_dir / "temporal_sequence_corpus.npz",
        "metadata_csv": run_dir / "metadata.csv",
        "diagnostic_rows_csv": run_dir / "diagnostic_rows.csv",
        "corpus_manifest_json": run_dir / "corpus_manifest.json",
    }
    write_json(run_dir / "summary.json", summary)
    if summary["result_class"] != "temporal_sequence_corpus_export_pass":
        raise RuntimeError(f"M997 corpus export sanity failed: {summary}")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Export temporal sequence corpus from M994 artifacts.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--m994-run-dir", type=Path, required=True)
    parser.add_argument("--max-sequence-len", type=int, default=48)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="temporal_sequence_corpus_export")
    summary = export_temporal_sequence_corpus(
        checkpoint_path=args.checkpoint,
        config_path=args.config,
        m994_run_dir=args.m994_run_dir,
        max_sequence_len=args.max_sequence_len,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
