"""Capability-belief intervention probes for scaled L3 BC checkpoints."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.bc_capability_repair import CAPABILITY_TARGETS, CapabilityHead
from autodrift.bc_hidden_action_sensitivity_probe import (
    HIDDEN_VARIANTS,
    OBSERVATION_CONTROL_VARIANTS,
    _empirical_hidden_stats,
    _hidden_distance,
    _random_fit_hidden,
    _random_unit_hidden,
)
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec, parse_checkpoint_spec
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.matched_history_intervention_gate import (
    RecurrentSnapshot,
    _limit_pairs,
    _pairs_for_checkpoint,
    _snapshot,
    collect_requested_snapshots,
    requested_snapshot_steps,
    zero_action_history_observation,
    zero_current_response_observation,
)
from autodrift.train_ppo import ActorCritic, resolve_device


NORMAL_VARIANT = "normal"
ALL_CAPABILITY_VARIANTS = (NORMAL_VARIANT,) + HIDDEN_VARIANTS + OBSERVATION_CONTROL_VARIANTS
REAL_HISTORY_VARIANTS = ("wrong_matched_history", "delayed_history", "shuffled_history")


def _as_float_array(values: Any, *, name: str) -> np.ndarray:
    array = np.asarray(values, dtype=np.float32).reshape(-1)
    if array.size != len(CAPABILITY_TARGETS):
        raise ValueError(f"{name} must have {len(CAPABILITY_TARGETS)} values, got {array.size}")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} contains non-finite values")
    return array


def target_std_from_summary(path: Path | str) -> np.ndarray:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return np.maximum(_as_float_array(data.get("target_std", []), name="target_std"), 1e-6)


def load_capability_head(path: Path | str, *, device: torch.device) -> CapabilityHead:
    checkpoint = torch.load(Path(path), map_location=device)
    state_dict = checkpoint.get("state_dict", checkpoint) if isinstance(checkpoint, dict) else checkpoint
    if not isinstance(state_dict, dict):
        raise ValueError("capability head checkpoint must contain a state_dict")
    first_weight = state_dict.get("net.0.weight")
    output_bias = state_dict.get("net.2.bias")
    if first_weight is None or output_bias is None:
        raise ValueError("capability head state_dict is missing expected layers")
    hidden_size = int(first_weight.shape[1])
    output_dim = int(output_bias.shape[0])
    head = CapabilityHead(hidden_size=hidden_size, output_dim=output_dim).to(device)
    head.load_state_dict(state_dict)
    head.eval()
    return head


def capability_prediction_from_hidden(
    *,
    model: ActorCritic,
    head: CapabilityHead,
    observation: np.ndarray,
    hidden: torch.Tensor,
    device: torch.device,
) -> tuple[np.ndarray, torch.Tensor]:
    obs_t = torch.as_tensor(observation, dtype=torch.float32, device=device).unsqueeze(0)
    hidden_t = hidden.to(device=device, dtype=torch.float32)
    with torch.no_grad():
        _, next_hidden = model.recurrent_features_tensor(obs_t, hidden_t)
        prediction = head(next_hidden)
    return prediction.squeeze(0).detach().cpu().numpy().astype(np.float32), next_hidden.detach()


def capability_delta_metrics(
    *,
    normal_prediction: np.ndarray,
    variant_prediction: np.ndarray,
    target_std: np.ndarray,
    min_capability_z_distance: float,
) -> dict[str, Any]:
    normal = np.asarray(normal_prediction, dtype=np.float32).reshape(-1)
    variant = np.asarray(variant_prediction, dtype=np.float32).reshape(-1)
    std = np.maximum(np.asarray(target_std, dtype=np.float32).reshape(-1), 1e-6)
    if normal.shape != variant.shape or normal.shape != std.shape:
        raise ValueError("normal, variant, and target_std must have matching shapes")
    z_delta = (variant - normal) / std
    abs_z = np.abs(z_delta)
    distance = float(np.linalg.norm(z_delta.astype(np.float64)))
    row: dict[str, Any] = {
        "capability_z_distance": distance,
        "capability_z_distance_above_threshold": bool(distance >= float(min_capability_z_distance)),
    }
    for index, target in enumerate(CAPABILITY_TARGETS):
        row[f"normal_{target}"] = float(normal[index])
        row[f"variant_{target}"] = float(variant[index])
        row[f"z_delta_{target}"] = float(z_delta[index])
        row[f"abs_z_{target}"] = float(abs_z[index])
    return row


def variant_kind(variant: str) -> str:
    if variant == NORMAL_VARIANT:
        return "normal"
    if variant == "reset_hidden":
        return "reset_ablation"
    if variant in REAL_HISTORY_VARIANTS:
        return "real_history"
    if variant.startswith("scaled_hidden"):
        return "scaled_hidden"
    if variant.startswith("random_hidden"):
        return "off_manifold"
    if variant in OBSERVATION_CONTROL_VARIANTS:
        return "observation_control"
    return "unknown"


def build_capability_intervention_rows(
    *,
    pair_rows: pd.DataFrame,
    snapshots: dict[tuple[int, int], RecurrentSnapshot],
    model: ActorCritic,
    head: CapabilityHead,
    checkpoint_label: str,
    surface: str,
    response_dim: int,
    delay_steps: int,
    target_std: np.ndarray,
    min_capability_z_distance: float,
    device: torch.device,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    reset_hidden = model.initial_hidden(1, device)
    empirical_mean, empirical_std, empirical_norm = _empirical_hidden_stats(snapshots)
    limited_pairs = pair_rows.reset_index(drop=True)
    left_hidden_cycle: list[torch.Tensor] = []
    for _, pair in limited_pairs.iterrows():
        left = _snapshot(snapshots, int(pair["left_seed"]), int(pair["left_step"]))
        left_hidden_cycle.append(left.hidden.to(device=device, dtype=torch.float32))

    for pair_id, pair in limited_pairs.iterrows():
        left = _snapshot(snapshots, int(pair["left_seed"]), int(pair["left_step"]))
        right = _snapshot(snapshots, int(pair["right_seed"]), int(pair["right_step"]))
        delayed = _snapshot(
            snapshots,
            int(pair["left_seed"]),
            max(0, int(pair["left_step"]) - int(delay_steps)),
        )
        left_hidden = left.hidden.to(device=device, dtype=torch.float32)
        right_hidden = right.hidden.to(device=device, dtype=torch.float32)
        delayed_hidden = delayed.hidden.to(device=device, dtype=torch.float32)
        shuffled_hidden = left_hidden_cycle[(int(pair_id) + 1) % len(left_hidden_cycle)]
        normal_prediction, _ = capability_prediction_from_hidden(
            model=model,
            head=head,
            observation=left.observation,
            hidden=left_hidden,
            device=device,
        )
        variants: dict[str, tuple[np.ndarray, torch.Tensor]] = {
            NORMAL_VARIANT: (left.observation, left_hidden),
            "reset_hidden": (left.observation, reset_hidden),
            "delayed_history": (left.observation, delayed_hidden),
            "wrong_matched_history": (left.observation, right_hidden),
            "shuffled_history": (left.observation, shuffled_hidden),
            "scaled_hidden_0_5": (left.observation, left_hidden * 0.5),
            "scaled_hidden_1_5": (left.observation, left_hidden * 1.5),
            "scaled_hidden_2_0": (left.observation, left_hidden * 2.0),
            "random_hidden_fit": (
                left.observation,
                _random_fit_hidden(
                    empirical_mean=empirical_mean,
                    empirical_std=empirical_std,
                    pair_id=int(pair_id),
                    device=device,
                ),
            ),
            "random_hidden_unit": (
                left.observation,
                _random_unit_hidden(
                    hidden_shape=left_hidden.shape,
                    empirical_norm=empirical_norm,
                    pair_id=int(pair_id),
                    device=device,
                ),
            ),
            "zero_current_response": (zero_current_response_observation(left.observation, response_dim), left_hidden),
            "zero_action_history": (zero_action_history_observation(left.observation), left_hidden),
        }
        for variant, (variant_observation, variant_hidden) in variants.items():
            variant_prediction, _ = capability_prediction_from_hidden(
                model=model,
                head=head,
                observation=variant_observation,
                hidden=variant_hidden,
                device=device,
            )
            row = {
                "pair_id": int(pair_id),
                "checkpoint_label": str(checkpoint_label),
                "source_checkpoint_label": str(
                    pair.get("source_checkpoint_label", pair.get("checkpoint_label", ""))
                ),
                "surface": str(surface),
                "probe_seed": int(pair.get("probe_seed", -1)),
                "target": str(pair["target"]),
                "variant": str(variant),
                "variant_kind": variant_kind(str(variant)),
                "left_seed": int(pair["left_seed"]),
                "right_seed": int(pair["right_seed"]),
                "left_step": int(pair["left_step"]),
                "right_step": int(pair["right_step"]),
                "target_z_delta": float(pair["target_z_delta"]),
                "visible_distance": float(pair["visible_distance"]),
                "hidden_distance": _hidden_distance(left_hidden, variant_hidden),
            }
            row.update(
                capability_delta_metrics(
                    normal_prediction=normal_prediction,
                    variant_prediction=variant_prediction,
                    target_std=target_std,
                    min_capability_z_distance=min_capability_z_distance,
                )
            )
            rows.append(row)
    return rows


def _summary_row(
    *,
    group: pd.DataFrame,
    checkpoint_label: str,
    surface: str,
    variant: str,
    target: str | None = None,
) -> dict[str, Any]:
    distance = group["capability_z_distance"].astype(float)
    threshold_mask = group["capability_z_distance_above_threshold"].astype(bool)
    row: dict[str, Any] = {
        "checkpoint_label": str(checkpoint_label),
        "surface": str(surface),
        "variant": str(variant),
        "variant_kind": variant_kind(str(variant)),
        "pair_count": int(len(group)),
        "hidden_distance_mean": float(group["hidden_distance"].astype(float).mean()),
        "hidden_distance_p90": float(group["hidden_distance"].astype(float).quantile(0.90)),
        "hidden_distance_max": float(group["hidden_distance"].astype(float).max()),
        "capability_z_distance_mean": float(distance.mean()),
        "capability_z_distance_p50": float(distance.quantile(0.50)),
        "capability_z_distance_p90": float(distance.quantile(0.90)),
        "capability_z_distance_max": float(distance.max()),
        "above_threshold_count": int(threshold_mask.sum()),
        "above_threshold_fraction": float(threshold_mask.mean()),
    }
    if target is not None:
        row["target"] = str(target)
    for capability_target in CAPABILITY_TARGETS:
        row[f"abs_z_{capability_target}_mean"] = float(group[f"abs_z_{capability_target}"].astype(float).mean())
        row[f"abs_z_{capability_target}_p90"] = float(
            group[f"abs_z_{capability_target}"].astype(float).quantile(0.90)
        )
    return row


def summarize_capability_intervention_rows(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not rows:
        return [], []
    frame = pd.DataFrame(rows)
    by_target: list[dict[str, Any]] = []
    aggregate: list[dict[str, Any]] = []
    for (checkpoint_label, surface, target, variant), group in frame.groupby(
        ["checkpoint_label", "surface", "target", "variant"],
        observed=True,
    ):
        by_target.append(
            _summary_row(
                group=group,
                checkpoint_label=str(checkpoint_label),
                surface=str(surface),
                target=str(target),
                variant=str(variant),
            )
        )
    for (checkpoint_label, surface, variant), group in frame.groupby(
        ["checkpoint_label", "surface", "variant"],
        observed=True,
    ):
        aggregate.append(
            _summary_row(
                group=group,
                checkpoint_label=str(checkpoint_label),
                surface=str(surface),
                variant=str(variant),
            )
        )
    return by_target, aggregate


def evaluate_actor_finetune_admission(
    aggregate_rows: list[dict[str, Any]],
    *,
    min_mean: float = 0.10,
    min_above_count: int = 16,
) -> dict[str, Any]:
    eligible: list[dict[str, Any]] = []
    for row in aggregate_rows:
        if row["variant"] not in REAL_HISTORY_VARIANTS:
            continue
        if float(row["capability_z_distance_mean"]) >= float(min_mean) and int(row["above_threshold_count"]) >= int(
            min_above_count
        ):
            eligible.append(
                {
                    "checkpoint_label": row["checkpoint_label"],
                    "surface": row["surface"],
                    "variant": row["variant"],
                    "capability_z_distance_mean": float(row["capability_z_distance_mean"]),
                    "above_threshold_count": int(row["above_threshold_count"]),
                    "pair_count": int(row["pair_count"]),
                }
            )
    return {
        "actor_finetune_design_admitted": bool(eligible),
        "eligible_rows": eligible,
        "real_history_variants": list(REAL_HISTORY_VARIANTS),
        "min_mean": float(min_mean),
        "min_above_threshold_count": int(min_above_count),
    }


def run_bc_capability_belief_intervention_probe(
    *,
    checkpoint_specs: tuple[CheckpointSpec, ...],
    capability_head_path: Path,
    capability_summary_path: Path,
    env_config_path: Path,
    pairs_csv: Path,
    surface: str,
    delay_steps: int,
    min_capability_z_distance: float,
    max_pairs_per_target: int,
    pair_label_mode: str,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    env_config = load_env_config(env_config_path)
    pair_frame = pd.read_csv(pairs_csv)
    pair_frame = _limit_pairs(pair_frame, max_pairs_per_checkpoint_target=max_pairs_per_target)
    target_std = target_std_from_summary(capability_summary_path)
    capability_rows: list[dict[str, Any]] = []
    skipped_labels: list[str] = []

    for checkpoint_spec in checkpoint_specs:
        model, _ = load_actor_critic_checkpoint(checkpoint_spec.path, device=str(resolved_device))
        model.eval()
        head = load_capability_head(capability_head_path, device=resolved_device)
        checkpoint_pairs = _pairs_for_checkpoint(pair_frame, checkpoint_spec.label, pair_label_mode)
        if checkpoint_pairs.empty:
            skipped_labels.append(checkpoint_spec.label)
            continue
        response_dim = response_feature_dim_for_model(model)
        snapshots = collect_requested_snapshots(
            model=model,
            env_config=env_config,
            requests=requested_snapshot_steps(checkpoint_pairs, delay_steps=delay_steps),
            device=resolved_device,
        )
        capability_rows.extend(
            build_capability_intervention_rows(
                pair_rows=checkpoint_pairs,
                snapshots=snapshots,
                model=model,
                head=head,
                checkpoint_label=checkpoint_spec.label,
                surface=surface,
                response_dim=response_dim,
                delay_steps=delay_steps,
                target_std=target_std,
                min_capability_z_distance=min_capability_z_distance,
                device=resolved_device,
            )
        )

    variant_rows, aggregate_rows = summarize_capability_intervention_rows(capability_rows)
    admission = evaluate_actor_finetune_admission(aggregate_rows)
    write_csv_rows(run_dir / "capability_intervention_rows.csv", capability_rows)
    write_csv_rows(run_dir / "variant_summary.csv", variant_rows)
    write_csv_rows(run_dir / "variant_aggregate_summary.csv", aggregate_rows)
    summary = {
        "run_type": "bc_capability_belief_intervention_probe",
        "checkpoints": [{"label": spec.label, "path": spec.path} for spec in checkpoint_specs],
        "capability_head": capability_head_path,
        "capability_summary": capability_summary_path,
        "env_config": env_config_path,
        "pairs_csv": pairs_csv,
        "surface": str(surface),
        "delay_steps": int(delay_steps),
        "min_capability_z_distance": float(min_capability_z_distance),
        "max_pairs_per_target": int(max_pairs_per_target),
        "pair_label_mode": str(pair_label_mode),
        "target_std": target_std.tolist(),
        "device": str(resolved_device),
        "input_pair_count": int(len(pair_frame)),
        "capability_row_count": int(len(capability_rows)),
        "variant_summary_rows": int(len(variant_rows)),
        "variant_aggregate_summary_rows": int(len(aggregate_rows)),
        "skipped_labels": skipped_labels,
        "labels_enter_actor_input": False,
        "ppo_used": False,
        "promoted": False,
        "actor_finetune_admission": admission,
        "capability_intervention_rows_csv": run_dir / "capability_intervention_rows.csv",
        "variant_summary_csv": run_dir / "variant_summary.csv",
        "variant_aggregate_summary_csv": run_dir / "variant_aggregate_summary.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe capability-belief movement under recurrent hidden interventions.")
    parser.add_argument("--checkpoint-policy", action="append", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--capability-head", type=Path, required=True)
    parser.add_argument("--capability-summary", type=Path, required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--pairs-csv", type=Path, required=True)
    parser.add_argument("--surface", type=str, required=True)
    parser.add_argument("--delay-steps", type=int, default=2)
    parser.add_argument("--min-capability-z-distance", type=float, default=0.25)
    parser.add_argument("--max-pairs-per-target", type=int, default=120)
    parser.add_argument("--pair-label-mode", choices=("matching", "all"), default="matching")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="bc_capability_belief_intervention_probe")
    summary = run_bc_capability_belief_intervention_probe(
        checkpoint_specs=tuple(args.checkpoint_policy),
        capability_head_path=args.capability_head,
        capability_summary_path=args.capability_summary,
        env_config_path=args.env_config,
        pairs_csv=args.pairs_csv,
        surface=args.surface,
        delay_steps=args.delay_steps,
        min_capability_z_distance=args.min_capability_z_distance,
        max_pairs_per_target=args.max_pairs_per_target,
        pair_label_mode=args.pair_label_mode,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
