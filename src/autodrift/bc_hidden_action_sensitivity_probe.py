"""Hidden-to-action sensitivity probes for scaled L3 BC checkpoints."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec, parse_checkpoint_spec
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.matched_history_intervention_gate import (
    RecurrentSnapshot,
    _limit_pairs,
    _pairs_for_checkpoint,
    _snapshot,
    action_distance,
    collect_requested_snapshots,
    deterministic_action_from_hidden,
    requested_snapshot_steps,
    zero_action_history_observation,
    zero_current_response_observation,
)
from autodrift.train_ppo import ActorCritic, resolve_device


HIDDEN_VARIANTS = (
    "reset_hidden",
    "delayed_history",
    "wrong_matched_history",
    "shuffled_history",
    "scaled_hidden_0_5",
    "scaled_hidden_1_5",
    "scaled_hidden_2_0",
    "random_hidden_fit",
    "random_hidden_unit",
)
OBSERVATION_CONTROL_VARIANTS = (
    "zero_current_response",
    "zero_action_history",
)
ALL_VARIANTS = HIDDEN_VARIANTS + OBSERVATION_CONTROL_VARIANTS


def _tensor_to_numpy(value: torch.Tensor) -> np.ndarray:
    return value.detach().cpu().numpy().astype(np.float32)


def _hidden_distance(left: torch.Tensor, right: torch.Tensor) -> float:
    return float(torch.linalg.vector_norm(left.detach().cpu() - right.detach().cpu()).item())


def _safe_correlation(x_values: pd.Series, y_values: pd.Series) -> float:
    x = x_values.astype(float).to_numpy(dtype=np.float64)
    y = y_values.astype(float).to_numpy(dtype=np.float64)
    finite = np.isfinite(x) & np.isfinite(y)
    if int(np.sum(finite)) < 2:
        return float("nan")
    x = x[finite]
    y = y[finite]
    if float(np.std(x)) <= 1e-12 or float(np.std(y)) <= 1e-12:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def fusion_weight_chunk_summary(model: ActorCritic, *, checkpoint_label: str) -> dict[str, Any]:
    if model.response_context_fusion is None:
        raise ValueError("hidden-action sensitivity probe requires a human-view online recurrent actor")
    first_layer = model.response_context_fusion[0]
    if not isinstance(first_layer, torch.nn.Linear):
        raise ValueError("expected response_context_fusion first layer to be Linear")
    weight = first_layer.weight.detach().cpu()
    if weight.shape[1] % 3 != 0:
        raise ValueError("response_context_fusion input dimension must be divisible by three")
    chunk_dim = int(weight.shape[1] // 3)
    hidden_weight = weight[:, :chunk_dim]
    context_weight = weight[:, chunk_dim : 2 * chunk_dim]
    interaction_weight = weight[:, 2 * chunk_dim :]
    hidden_norm = float(torch.linalg.matrix_norm(hidden_weight).item())
    context_norm = float(torch.linalg.matrix_norm(context_weight).item())
    interaction_norm = float(torch.linalg.matrix_norm(interaction_weight).item())
    total = hidden_norm + context_norm + interaction_norm
    return {
        "checkpoint_label": str(checkpoint_label),
        "chunk_dim": int(chunk_dim),
        "hidden_chunk_norm": hidden_norm,
        "context_chunk_norm": context_norm,
        "interaction_chunk_norm": interaction_norm,
        "hidden_chunk_share": hidden_norm / total if total > 0.0 else float("nan"),
        "context_chunk_share": context_norm / total if total > 0.0 else float("nan"),
        "interaction_chunk_share": interaction_norm / total if total > 0.0 else float("nan"),
        "actor_mean_weight_norm": float(torch.linalg.matrix_norm(model.actor_mean.weight.detach().cpu()).item()),
    }


def _empirical_hidden_stats(snapshots: dict[tuple[int, int], RecurrentSnapshot]) -> tuple[np.ndarray, np.ndarray, float]:
    if not snapshots:
        raise ValueError("cannot compute empirical hidden stats from empty snapshots")
    values = np.concatenate([_tensor_to_numpy(snapshot.hidden) for snapshot in snapshots.values()], axis=0)
    mean = values.mean(axis=0, keepdims=True).astype(np.float32)
    std = values.std(axis=0, keepdims=True).astype(np.float32)
    std = np.where(std > 1e-6, std, 1.0).astype(np.float32)
    norm = float(np.mean(np.linalg.norm(values, axis=1)))
    return mean, std, norm


def _random_fit_hidden(
    *,
    empirical_mean: np.ndarray,
    empirical_std: np.ndarray,
    pair_id: int,
    device: torch.device,
) -> torch.Tensor:
    rng = np.random.default_rng(5900 + int(pair_id))
    value = empirical_mean + empirical_std * rng.standard_normal(size=empirical_mean.shape).astype(np.float32)
    return torch.as_tensor(value, dtype=torch.float32, device=device)


def _random_unit_hidden(
    *,
    hidden_shape: torch.Size,
    empirical_norm: float,
    pair_id: int,
    device: torch.device,
) -> torch.Tensor:
    rng = np.random.default_rng(6900 + int(pair_id))
    value = rng.standard_normal(size=tuple(hidden_shape)).astype(np.float32)
    value_norm = float(np.linalg.norm(value))
    if value_norm > 1e-12:
        value = value / value_norm * float(empirical_norm)
    return torch.as_tensor(value, dtype=torch.float32, device=device)


def build_hidden_action_sensitivity_rows(
    *,
    pair_rows: pd.DataFrame,
    snapshots: dict[tuple[int, int], RecurrentSnapshot],
    model: ActorCritic,
    checkpoint_label: str,
    surface: str,
    response_dim: int,
    delay_steps: int,
    min_action_distance: float,
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
        normal_action, _ = deterministic_action_from_hidden(model, left.observation, left_hidden, device)
        right_action, _ = deterministic_action_from_hidden(model, right.observation, right_hidden, device)
        normal_pair_action_distance = action_distance(normal_action, right_action)
        shuffled_hidden = left_hidden_cycle[(int(pair_id) + 1) % len(left_hidden_cycle)]
        variants: dict[str, tuple[np.ndarray, torch.Tensor]] = {
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
            variant_action, _ = deterministic_action_from_hidden(model, variant_observation, variant_hidden, device)
            variant_distance = action_distance(normal_action, variant_action)
            variant_to_right_distance = action_distance(right_action, variant_action)
            hidden_distance = _hidden_distance(left_hidden, variant_hidden)
            rows.append(
                {
                    "pair_id": int(pair_id),
                    "checkpoint_label": str(checkpoint_label),
                    "source_checkpoint_label": str(
                        pair.get("source_checkpoint_label", pair.get("checkpoint_label", ""))
                    ),
                    "surface": str(surface),
                    "probe_seed": int(pair.get("probe_seed", -1)),
                    "target": str(pair["target"]),
                    "variant": variant,
                    "left_seed": int(pair["left_seed"]),
                    "right_seed": int(pair["right_seed"]),
                    "left_step": int(pair["left_step"]),
                    "right_step": int(pair["right_step"]),
                    "target_z_delta": float(pair["target_z_delta"]),
                    "visible_distance": float(pair["visible_distance"]),
                    "hidden_distance": hidden_distance,
                    "normal_pair_action_distance": normal_pair_action_distance,
                    "action_distance": variant_distance,
                    "action_distance_above_threshold": bool(variant_distance >= float(min_action_distance)),
                    "variant_to_right_action_distance": variant_to_right_distance,
                    "wrong_history_closer_to_right_action": bool(
                        variant == "wrong_matched_history"
                        and variant_to_right_distance < normal_pair_action_distance
                    ),
                    "normal_steer": float(normal_action[0]),
                    "normal_throttle": float(normal_action[1]),
                    "normal_brake": float(normal_action[2]),
                    "variant_steer": float(variant_action[0]),
                    "variant_throttle": float(variant_action[1]),
                    "variant_brake": float(variant_action[2]),
                    "abs_steer_delta": float(abs(normal_action[0] - variant_action[0])),
                    "abs_throttle_delta": float(abs(normal_action[1] - variant_action[1])),
                    "abs_brake_delta": float(abs(normal_action[2] - variant_action[2])),
                }
            )
    return rows


def summarize_hidden_action_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not rows:
        return [], []
    frame = pd.DataFrame(rows)
    variant_rows: list[dict[str, Any]] = []
    correlation_rows: list[dict[str, Any]] = []
    for (checkpoint_label, surface, target, variant), group in frame.groupby(
        ["checkpoint_label", "surface", "target", "variant"],
        observed=True,
    ):
        action_distance_values = group["action_distance"].astype(float)
        hidden_distance_values = group["hidden_distance"].astype(float)
        threshold_mask = group["action_distance_above_threshold"].astype(bool)
        wrong_closer = (
            group["wrong_history_closer_to_right_action"].astype(bool)
            if "wrong_history_closer_to_right_action" in group
            else pd.Series([False] * len(group))
        )
        row = {
            "checkpoint_label": str(checkpoint_label),
            "surface": str(surface),
            "target": str(target),
            "variant": str(variant),
            "pair_count": int(len(group)),
            "hidden_distance_mean": float(hidden_distance_values.mean()),
            "hidden_distance_p90": float(hidden_distance_values.quantile(0.90)),
            "hidden_distance_max": float(hidden_distance_values.max()),
            "action_distance_mean": float(action_distance_values.mean()),
            "action_distance_p50": float(action_distance_values.quantile(0.50)),
            "action_distance_p90": float(action_distance_values.quantile(0.90)),
            "action_distance_max": float(action_distance_values.max()),
            "above_threshold_count": int(threshold_mask.sum()),
            "above_threshold_fraction": float(threshold_mask.mean()),
            "normal_pair_action_distance_mean": float(group["normal_pair_action_distance"].astype(float).mean()),
            "variant_to_right_action_distance_mean": float(
                group["variant_to_right_action_distance"].astype(float).mean()
            ),
            "wrong_history_closer_to_right_fraction": float(wrong_closer.mean()),
            "abs_steer_delta_mean": float(group["abs_steer_delta"].astype(float).mean()),
            "abs_throttle_delta_mean": float(group["abs_throttle_delta"].astype(float).mean()),
            "abs_brake_delta_mean": float(group["abs_brake_delta"].astype(float).mean()),
        }
        variant_rows.append(row)
        correlation_rows.append(
            {
                "checkpoint_label": str(checkpoint_label),
                "surface": str(surface),
                "target": str(target),
                "variant": str(variant),
                "pair_count": int(len(group)),
                "hidden_action_distance_corr": _safe_correlation(
                    group["hidden_distance"],
                    group["action_distance"],
                ),
            }
        )
    return variant_rows, correlation_rows


def run_bc_hidden_action_sensitivity_probe(
    *,
    checkpoint_specs: tuple[CheckpointSpec, ...],
    env_config_path: Path,
    pairs_csv: Path,
    surface: str,
    delay_steps: int,
    min_action_distance: float,
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
    action_rows: list[dict[str, Any]] = []
    weight_rows: list[dict[str, Any]] = []
    skipped_action_labels: list[str] = []

    for checkpoint_spec in checkpoint_specs:
        model, _ = load_actor_critic_checkpoint(checkpoint_spec.path, device=str(resolved_device))
        model.eval()
        weight_rows.append(fusion_weight_chunk_summary(model, checkpoint_label=checkpoint_spec.label))
        checkpoint_pairs = _pairs_for_checkpoint(pair_frame, checkpoint_spec.label, pair_label_mode)
        if checkpoint_pairs.empty:
            skipped_action_labels.append(checkpoint_spec.label)
            continue
        response_dim = response_feature_dim_for_model(model)
        snapshots = collect_requested_snapshots(
            model=model,
            env_config=env_config,
            requests=requested_snapshot_steps(checkpoint_pairs, delay_steps=delay_steps),
            device=resolved_device,
        )
        action_rows.extend(
            build_hidden_action_sensitivity_rows(
                pair_rows=checkpoint_pairs,
                snapshots=snapshots,
                model=model,
                checkpoint_label=checkpoint_spec.label,
                surface=surface,
                response_dim=response_dim,
                delay_steps=delay_steps,
                min_action_distance=min_action_distance,
                device=resolved_device,
            )
        )

    variant_rows, correlation_rows = summarize_hidden_action_rows(action_rows)
    write_csv_rows(run_dir / "weight_chunk_summary.csv", weight_rows)
    write_csv_rows(run_dir / "action_sensitivity_rows.csv", action_rows)
    write_csv_rows(run_dir / "variant_summary.csv", variant_rows)
    write_csv_rows(run_dir / "correlation_summary.csv", correlation_rows)
    summary = {
        "run_type": "bc_hidden_action_sensitivity_probe",
        "checkpoints": [{"label": spec.label, "path": spec.path} for spec in checkpoint_specs],
        "env_config": env_config_path,
        "pairs_csv": pairs_csv,
        "surface": str(surface),
        "delay_steps": int(delay_steps),
        "min_action_distance": float(min_action_distance),
        "max_pairs_per_target": int(max_pairs_per_target),
        "pair_label_mode": str(pair_label_mode),
        "device": str(resolved_device),
        "input_pair_count": int(len(pair_frame)),
        "action_row_count": int(len(action_rows)),
        "variant_summary_rows": int(len(variant_rows)),
        "correlation_summary_rows": int(len(correlation_rows)),
        "weight_summary_rows": int(len(weight_rows)),
        "skipped_action_labels": skipped_action_labels,
        "weight_chunk_summary_csv": run_dir / "weight_chunk_summary.csv",
        "action_sensitivity_rows_csv": run_dir / "action_sensitivity_rows.csv",
        "variant_summary_csv": run_dir / "variant_summary.csv",
        "correlation_summary_csv": run_dir / "correlation_summary.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe hidden-to-action sensitivity for BC online-GRU actors.")
    parser.add_argument("--checkpoint-policy", action="append", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--pairs-csv", type=Path, required=True)
    parser.add_argument("--surface", type=str, required=True)
    parser.add_argument("--delay-steps", type=int, default=2)
    parser.add_argument("--min-action-distance", type=float, default=0.02)
    parser.add_argument("--max-pairs-per-target", type=int, default=120)
    parser.add_argument("--pair-label-mode", choices=("matching", "all"), default="matching")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="bc_hidden_action_sensitivity_probe")
    summary = run_bc_hidden_action_sensitivity_probe(
        checkpoint_specs=tuple(args.checkpoint_policy),
        env_config_path=args.env_config,
        pairs_csv=args.pairs_csv,
        surface=args.surface,
        delay_steps=args.delay_steps,
        min_action_distance=args.min_action_distance,
        max_pairs_per_target=args.max_pairs_per_target,
        pair_label_mode=args.pair_label_mode,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
