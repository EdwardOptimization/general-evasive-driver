"""No-update source-balanced BC-v2 objective evaluator."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.sequence_corpus_exact_objective_sanity import (
    load_metadata_csv,
    load_sequence_corpus_npz,
    source_weight_balance,
    validate_metadata_alignment,
    validate_sequence_corpus_contract,
)
from autodrift.train_ppo import ActorCritic, resolve_device


def model_parameter_checksum(model: torch.nn.Module) -> str:
    digest = hashlib.sha256()
    for name, tensor in sorted(model.state_dict().items()):
        digest.update(name.encode("utf-8"))
        array = tensor.detach().cpu().contiguous().numpy()
        digest.update(str(array.dtype).encode("utf-8"))
        digest.update(np.asarray(array.shape, dtype=np.int64).tobytes())
        digest.update(array.tobytes())
    return digest.hexdigest()


def batched_actions_from_hidden(
    model: ActorCritic,
    observations: np.ndarray,
    hidden: np.ndarray,
    *,
    device: torch.device,
    batch_size: int = 1024,
) -> np.ndarray:
    actions: list[np.ndarray] = []
    model.eval()
    with torch.no_grad():
        for start in range(0, observations.shape[0], int(batch_size)):
            end = min(start + int(batch_size), observations.shape[0])
            obs_t = torch.as_tensor(observations[start:end], dtype=torch.float32, device=device)
            hidden_t = torch.as_tensor(hidden[start:end], dtype=torch.float32, device=device)
            features, _ = model.recurrent_features_tensor(obs_t, hidden_t)
            action = torch.tanh(model.actor_mean(features))
            actions.append(action.detach().cpu().numpy().astype(np.float32))
    return np.concatenate(actions, axis=0)


def _masked_sequence_delta_metrics(arrays: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    target = arrays["target_action_sequence"].astype(np.float64)
    base = arrays["normal_base_action_sequence"].astype(np.float64)
    mask = arrays["sequence_mask"].astype(np.float64)
    delta = (target - base) * mask[:, :, None]
    step_l2 = np.linalg.norm(delta, axis=2)
    valid_steps = np.maximum(mask.sum(axis=1), 1.0)
    sequence_mse = np.square(delta).sum(axis=(1, 2)) / np.maximum(valid_steps * target.shape[2], 1.0)
    return {
        "sequence_delta_mse": sequence_mse,
        "sequence_delta_mean_step_l2": step_l2.sum(axis=1) / valid_steps,
        "sequence_delta_max_step_l2": step_l2.max(axis=1),
        "target_first_action": target[:, 0, :],
        "base_first_action": base[:, 0, :],
    }


def compute_bc_v2_row_metrics(
    arrays: dict[str, np.ndarray],
    metadata: pd.DataFrame,
    *,
    normal_action: np.ndarray,
    variant_action: np.ndarray,
) -> pd.DataFrame:
    rows = int(arrays["observation"].shape[0])
    if normal_action.shape != (rows, 3):
        raise ValueError(f"normal_action must have shape ({rows}, 3)")
    if variant_action.shape != (rows, 3):
        raise ValueError(f"variant_action must have shape ({rows}, 3)")

    sequence = _masked_sequence_delta_metrics(arrays)
    target_first = sequence["target_first_action"]
    base_first = sequence["base_first_action"]
    variant_base = arrays["variant_base_action"].astype(np.float64)
    normal = normal_action.astype(np.float64)
    variant = variant_action.astype(np.float64)
    weights = arrays["weight"].astype(np.float64)

    normal_error = normal - target_first
    variant_error = variant - target_first
    base_error = base_first - target_first
    metrics = pd.DataFrame(
        {
            "row_id": arrays["row_id"].astype(int),
            "source_index": arrays["source_index"].astype(int),
            "split": metadata["split"].astype(str).to_numpy(),
            "surface": metadata["surface"].astype(str).to_numpy(),
            "target": metadata["target"].astype(str).to_numpy(),
            "variant": metadata["variant"].astype(str).to_numpy(),
            "grid_name": metadata["grid_name"].astype(str).to_numpy(),
            "sequence_length": arrays["sequence_length"].astype(int),
            "weight": weights,
            "first_action_normal_mse": np.square(normal_error).mean(axis=1),
            "first_action_variant_mse": np.square(variant_error).mean(axis=1),
            "first_action_base_mse": np.square(base_error).mean(axis=1),
            "normal_action_to_base_l2": np.linalg.norm(normal - base_first, axis=1),
            "variant_action_to_stored_l2": np.linalg.norm(variant - variant_base, axis=1),
            "normal_variant_gap_l2": np.linalg.norm(normal - variant, axis=1),
            "sequence_delta_mse": sequence["sequence_delta_mse"],
            "sequence_delta_mean_step_l2": sequence["sequence_delta_mean_step_l2"],
            "sequence_delta_max_step_l2": sequence["sequence_delta_max_step_l2"],
        }
    )
    for column in (
        "first_action_normal_mse",
        "first_action_variant_mse",
        "first_action_base_mse",
        "sequence_delta_mse",
        "sequence_delta_mean_step_l2",
    ):
        metrics[f"weighted_{column}"] = metrics["weight"] * metrics[column]
    return metrics


def _weighted_mean(group: pd.DataFrame, column: str) -> float:
    return float((group["weight"] * group[column]).sum() / max(float(group["weight"].sum()), 1e-12))


def summarize_bc_v2_group(rows: pd.DataFrame, group_column: str) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    total_normal_loss = float(rows["weighted_first_action_normal_mse"].sum())
    for group_value, group in rows.groupby(group_column, observed=True):
        normal_loss_sum = float(group["weighted_first_action_normal_mse"].sum())
        summaries.append(
            {
                group_column: group_value,
                "rows": int(len(group)),
                "sources": int(group["source_index"].nunique()),
                "weight_sum": float(group["weight"].sum()),
                "first_action_normal_mse": _weighted_mean(group, "first_action_normal_mse"),
                "first_action_variant_mse": _weighted_mean(group, "first_action_variant_mse"),
                "first_action_base_mse": _weighted_mean(group, "first_action_base_mse"),
                "sequence_delta_mse": _weighted_mean(group, "sequence_delta_mse"),
                "sequence_delta_mean_step_l2": _weighted_mean(group, "sequence_delta_mean_step_l2"),
                "normal_variant_gap_l2": _weighted_mean(group, "normal_variant_gap_l2"),
                "normal_action_to_base_l2": _weighted_mean(group, "normal_action_to_base_l2"),
                "variant_action_to_stored_l2": _weighted_mean(group, "variant_action_to_stored_l2"),
                "normal_loss_contribution": normal_loss_sum,
                "normal_loss_fraction": normal_loss_sum / max(total_normal_loss, 1e-12),
                "surfaces": ";".join(sorted(group["surface"].astype(str).unique())),
                "targets": ";".join(sorted(group["target"].astype(str).unique())),
                "variants": ";".join(sorted(group["variant"].astype(str).unique())),
                "grids": ";".join(sorted(group["grid_name"].astype(str).unique())),
            }
        )
    return summaries


def _weighted_metric(rows: pd.DataFrame, column: str) -> float:
    return float(rows[f"weighted_{column}"].sum() / max(float(rows["weight"].sum()), 1e-12))


def run_source_balanced_bc_v2_objective(
    *,
    corpus_npz: Path,
    metadata_csv: Path,
    checkpoint_path: Path,
    run_dir: Path,
    device: str = "cpu",
    batch_size: int = 1024,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    arrays = load_sequence_corpus_npz(corpus_npz)
    contract = validate_sequence_corpus_contract(arrays)
    metadata = load_metadata_csv(metadata_csv, expected_rows=contract.rows)
    validate_metadata_alignment(arrays, metadata)

    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    before_checksum = model_parameter_checksum(model)
    normal_action = batched_actions_from_hidden(
        model,
        arrays["observation"],
        arrays["normal_hidden"],
        device=resolved_device,
        batch_size=batch_size,
    )
    variant_action = batched_actions_from_hidden(
        model,
        arrays["observation"],
        arrays["variant_hidden"],
        device=resolved_device,
        batch_size=batch_size,
    )
    after_checksum = model_parameter_checksum(model)

    row_metrics = compute_bc_v2_row_metrics(
        arrays,
        metadata,
        normal_action=normal_action,
        variant_action=variant_action,
    )
    source_summary = summarize_bc_v2_group(row_metrics, "source_index")
    split_summary = summarize_bc_v2_group(row_metrics, "split")
    target_summary = summarize_bc_v2_group(row_metrics, "target")
    balance = source_weight_balance(
        row_metrics.rename(
            columns={
                "sequence_delta_mse": "sequence_mse",
                "sequence_delta_mean_step_l2": "sequence_mean_step_l2",
            }
        )
    )

    write_csv_rows(run_dir / "row_bc_v2_metrics.csv", row_metrics.to_dict(orient="records"))
    write_csv_rows(run_dir / "source_bc_v2_summary.csv", source_summary)
    write_csv_rows(run_dir / "split_bc_v2_summary.csv", split_summary)
    write_csv_rows(run_dir / "target_bc_v2_summary.csv", target_summary)

    split_frame = pd.DataFrame(split_summary).set_index("split") if split_summary else pd.DataFrame()
    train_loss = (
        float(split_frame.loc["train", "first_action_normal_mse"])
        if not split_frame.empty and "train" in split_frame.index
        else None
    )
    heldout_loss = (
        float(split_frame.loc["source_holdout_validation", "first_action_normal_mse"])
        if not split_frame.empty and "source_holdout_validation" in split_frame.index
        else None
    )
    summary = {
        "run_type": "source_balanced_bc_v2_objective",
        "corpus_npz": corpus_npz,
        "metadata_csv": metadata_csv,
        "checkpoint": checkpoint_path,
        "rows": int(contract.rows),
        "source_count": int(contract.source_count),
        "observation_dim": int(contract.observation_dim),
        "hidden_dim": int(contract.hidden_dim),
        "max_sequence_length": int(contract.max_sequence_length),
        "first_action_normal_loss": _weighted_metric(row_metrics, "first_action_normal_mse"),
        "first_action_variant_loss": _weighted_metric(row_metrics, "first_action_variant_mse"),
        "first_action_base_loss": _weighted_metric(row_metrics, "first_action_base_mse"),
        "sequence_delta_target_mse": _weighted_metric(row_metrics, "sequence_delta_mse"),
        "sequence_delta_mean_step_l2": _weighted_metric(row_metrics, "sequence_delta_mean_step_l2"),
        "first_action_gap_l2_mean": _weighted_mean(row_metrics, "normal_variant_gap_l2"),
        "normal_action_to_base_l2_mean": _weighted_mean(row_metrics, "normal_action_to_base_l2"),
        "variant_action_to_stored_l2_mean": _weighted_mean(row_metrics, "variant_action_to_stored_l2"),
        "train_loss": train_loss,
        "source_holdout_validation_loss": heldout_loss,
        "source_weight_balance": balance,
        "finite_metrics": bool(np.isfinite(row_metrics.select_dtypes(include=[np.number]).to_numpy()).all()),
        "model_checksum_before": before_checksum,
        "model_checksum_after": after_checksum,
        "actor_parameters_changed": bool(before_checksum != after_checksum),
        "row_metrics_csv": run_dir / "row_bc_v2_metrics.csv",
        "source_bc_v2_summary_csv": run_dir / "source_bc_v2_summary.csv",
        "split_bc_v2_summary_csv": run_dir / "split_bc_v2_summary.csv",
        "target_bc_v2_summary_csv": run_dir / "target_bc_v2_summary.csv",
        "diagnostic_only": True,
        "training_started": False,
        "optimizer_started": False,
        "labels_enter_actor_input": False,
        "ppo_used": False,
        "promoted": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate exact source-balanced BC-v2 objective metrics.")
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="source_balanced_bc_v2_objective")
    summary = run_source_balanced_bc_v2_objective(
        corpus_npz=args.corpus,
        metadata_csv=args.metadata,
        checkpoint_path=args.checkpoint,
        run_dir=run_dir,
        device=args.device,
        batch_size=args.batch_size,
    )
    print(f"run_dir={run_dir}")
    print(f"rows={summary['rows']}")
    print(f"first_action_normal_loss={summary['first_action_normal_loss']:.8f}")
    print(f"first_action_variant_loss={summary['first_action_variant_loss']:.8f}")
    print(f"actor_parameters_changed={summary['actor_parameters_changed']}")


if __name__ == "__main__":
    main()
