"""Exact objective sanity checks for source-diverse sequence target corpora."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json


REQUIRED_ARRAYS = (
    "observation",
    "normal_hidden",
    "variant_hidden",
    "target_action_sequence",
    "normal_base_action_sequence",
    "sequence_mask",
    "variant_base_action",
    "weight",
    "row_id",
    "source_index",
    "sequence_length",
)
METADATA_REQUIRED_COLUMNS = (
    "source_index",
    "split",
    "surface",
    "target",
    "variant",
    "grid_name",
    "corpus_weight",
)


@dataclass(frozen=True)
class SequenceCorpusContract:
    rows: int
    observation_dim: int
    hidden_dim: int
    max_sequence_length: int
    action_dim: int
    source_count: int


def load_sequence_corpus_npz(path: Path) -> dict[str, np.ndarray]:
    loaded = np.load(path)
    arrays = {key: loaded[key] for key in loaded.files}
    validate_sequence_corpus_contract(arrays)
    return arrays


def validate_sequence_corpus_contract(arrays: dict[str, np.ndarray]) -> SequenceCorpusContract:
    missing = [key for key in REQUIRED_ARRAYS if key not in arrays]
    if missing:
        raise ValueError("sequence corpus is missing arrays: " + ", ".join(missing))

    observation = arrays["observation"]
    normal_hidden = arrays["normal_hidden"]
    variant_hidden = arrays["variant_hidden"]
    target_sequence = arrays["target_action_sequence"]
    base_sequence = arrays["normal_base_action_sequence"]
    mask = arrays["sequence_mask"]
    variant_base_action = arrays["variant_base_action"]
    weight = arrays["weight"]
    row_id = arrays["row_id"]
    source_index = arrays["source_index"]
    sequence_length = arrays["sequence_length"]

    if observation.ndim != 2:
        raise ValueError("observation must be 2D")
    rows = int(observation.shape[0])
    if rows <= 0:
        raise ValueError("sequence corpus cannot be empty")
    if normal_hidden.ndim != 2 or variant_hidden.ndim != 2:
        raise ValueError("hidden arrays must be 2D")
    if normal_hidden.shape != variant_hidden.shape or normal_hidden.shape[0] != rows:
        raise ValueError("hidden arrays must share row count")
    if target_sequence.ndim != 3 or base_sequence.ndim != 3:
        raise ValueError("action sequences must be 3D")
    if target_sequence.shape != base_sequence.shape:
        raise ValueError("target and base action sequences must share shape")
    if target_sequence.shape[0] != rows or target_sequence.shape[2] != 3:
        raise ValueError("action sequences must have shape (rows, K, 3)")
    if mask.shape != target_sequence.shape[:2]:
        raise ValueError("sequence_mask must have shape (rows, K)")
    if variant_base_action.shape != (rows, 3):
        raise ValueError("variant_base_action must have shape (rows, 3)")
    for key, expected_shape in (
        ("weight", (rows,)),
        ("row_id", (rows,)),
        ("source_index", (rows,)),
        ("sequence_length", (rows,)),
    ):
        if arrays[key].shape != expected_shape:
            raise ValueError(f"{key} must have shape {expected_shape}")
    float_keys = (
        "observation",
        "normal_hidden",
        "variant_hidden",
        "target_action_sequence",
        "normal_base_action_sequence",
        "sequence_mask",
        "variant_base_action",
        "weight",
    )
    for key in float_keys:
        if not np.isfinite(arrays[key]).all():
            raise ValueError(f"{key} contains non-finite values")
    if np.any(weight <= 0.0):
        raise ValueError("weight must be strictly positive")
    if np.any(sequence_length <= 0) or np.any(sequence_length > target_sequence.shape[1]):
        raise ValueError("sequence_length must be in [1, K]")
    if not np.allclose(mask, np.round(mask)):
        raise ValueError("sequence_mask must be binary")
    for index, length in enumerate(sequence_length.astype(int).tolist()):
        expected = np.zeros(target_sequence.shape[1], dtype=np.float32)
        expected[:length] = 1.0
        if not np.allclose(mask[index], expected):
            raise ValueError("sequence_mask must be a prefix mask matching sequence_length")
    if not np.array_equal(row_id.astype(int), np.arange(rows, dtype=np.int64)):
        raise ValueError("row_id must match corpus row order")
    return SequenceCorpusContract(
        rows=rows,
        observation_dim=int(observation.shape[1]),
        hidden_dim=int(normal_hidden.shape[1]),
        max_sequence_length=int(target_sequence.shape[1]),
        action_dim=int(target_sequence.shape[2]),
        source_count=int(np.unique(source_index.astype(int)).size),
    )


def load_metadata_csv(path: Path, expected_rows: int) -> pd.DataFrame:
    metadata = pd.read_csv(path)
    missing = [column for column in METADATA_REQUIRED_COLUMNS if column not in metadata.columns]
    if missing:
        raise ValueError("metadata is missing columns: " + ", ".join(missing))
    if len(metadata) != int(expected_rows):
        raise ValueError(f"metadata row count {len(metadata)} does not match corpus rows {expected_rows}")
    return metadata.reset_index(drop=True)


def validate_metadata_alignment(arrays: dict[str, np.ndarray], metadata: pd.DataFrame) -> None:
    sources = metadata["source_index"].astype(int).to_numpy()
    if not np.array_equal(sources, arrays["source_index"].astype(int)):
        raise ValueError("metadata source_index does not match corpus source_index")
    weights = metadata["corpus_weight"].astype(float).to_numpy()
    if not np.allclose(weights, arrays["weight"].astype(float), rtol=1e-6, atol=1e-8):
        raise ValueError("metadata corpus_weight does not match corpus weight")
    if "sequence_length" in metadata.columns:
        lengths = metadata["sequence_length"].astype(int).to_numpy()
        if not np.array_equal(lengths, arrays["sequence_length"].astype(int)):
            raise ValueError("metadata sequence_length does not match corpus sequence_length")
    if metadata["split"].isna().any():
        raise ValueError("metadata split contains missing values")


def compute_row_metrics(arrays: dict[str, np.ndarray], metadata: pd.DataFrame) -> pd.DataFrame:
    target = arrays["target_action_sequence"].astype(np.float64)
    base = arrays["normal_base_action_sequence"].astype(np.float64)
    mask = arrays["sequence_mask"].astype(np.float64)
    weights = arrays["weight"].astype(np.float64)
    delta = (target - base) * mask[:, :, None]
    step_l2 = np.linalg.norm(delta, axis=2)
    valid_steps = np.maximum(mask.sum(axis=1), 1.0)
    squared_sum = np.square(delta).sum(axis=(1, 2))
    valid_action_count = np.maximum(valid_steps * target.shape[2], 1.0)
    sequence_mse = squared_sum / valid_action_count
    rows = pd.DataFrame(
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
            "sequence_mse": sequence_mse,
            "sequence_rmse": np.sqrt(sequence_mse),
            "sequence_mean_step_l2": step_l2.sum(axis=1) / valid_steps,
            "sequence_max_step_l2": step_l2.max(axis=1),
            "first_step_l2": step_l2[:, 0],
            "steer_abs_delta_mean": (np.abs(delta[:, :, 0]).sum(axis=1) / valid_steps),
            "throttle_abs_delta_mean": (np.abs(delta[:, :, 1]).sum(axis=1) / valid_steps),
            "brake_abs_delta_mean": (np.abs(delta[:, :, 2]).sum(axis=1) / valid_steps),
        }
    )
    rows["weighted_sequence_mse"] = rows["weight"] * rows["sequence_mse"]
    rows["weighted_mean_step_l2"] = rows["weight"] * rows["sequence_mean_step_l2"]
    return rows


def summarize_group(rows: pd.DataFrame, group_column: str) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    total_weighted_loss = float(rows["weighted_sequence_mse"].sum())
    for group_value, group in rows.groupby(group_column, observed=True):
        weight_sum = float(group["weight"].sum())
        weighted_loss_sum = float(group["weighted_sequence_mse"].sum())
        weighted_l2_sum = float(group["weighted_mean_step_l2"].sum())
        summaries.append(
            {
                group_column: group_value,
                "rows": int(len(group)),
                "sources": int(group["source_index"].nunique()),
                "weight_sum": weight_sum,
                "weighted_sequence_mse_mean": weighted_loss_sum / max(weight_sum, 1e-12),
                "weighted_mean_step_l2": weighted_l2_sum / max(weight_sum, 1e-12),
                "weighted_loss_contribution": weighted_loss_sum,
                "weighted_loss_fraction": weighted_loss_sum / max(total_weighted_loss, 1e-12),
                "max_sequence_step_l2": float(group["sequence_max_step_l2"].max()),
                "mean_first_step_l2": float(group["first_step_l2"].mean()),
                "surfaces": ";".join(sorted(group["surface"].astype(str).unique())),
                "targets": ";".join(sorted(group["target"].astype(str).unique())),
                "variants": ";".join(sorted(group["variant"].astype(str).unique())),
                "grids": ";".join(sorted(group["grid_name"].astype(str).unique())),
            }
        )
    return summaries


def source_weight_balance(rows: pd.DataFrame) -> dict[str, Any]:
    source_weights = rows.groupby("source_index", observed=True)["weight"].sum().astype(float)
    expected = 1.0 / max(int(source_weights.size), 1)
    return {
        "source_count": int(source_weights.size),
        "expected_source_weight": float(expected),
        "min_source_weight": float(source_weights.min()),
        "max_source_weight": float(source_weights.max()),
        "max_abs_source_weight_error": float(np.max(np.abs(source_weights.to_numpy() - expected))),
        "source_weight_balanced": bool(np.allclose(source_weights.to_numpy(), expected, rtol=1e-5, atol=1e-7)),
        "total_weight": float(source_weights.sum()),
    }


def outside_mask_abs_max(arrays: dict[str, np.ndarray]) -> float:
    mask = arrays["sequence_mask"].astype(bool)
    outside = ~mask
    if not outside.any():
        return 0.0
    target_tail = np.abs(arrays["target_action_sequence"][outside])
    base_tail = np.abs(arrays["normal_base_action_sequence"][outside])
    return float(max(target_tail.max(initial=0.0), base_tail.max(initial=0.0)))


def run_sequence_corpus_exact_objective_sanity(
    *,
    corpus_npz: Path,
    metadata_csv: Path,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    arrays = load_sequence_corpus_npz(corpus_npz)
    contract = validate_sequence_corpus_contract(arrays)
    metadata = load_metadata_csv(metadata_csv, expected_rows=contract.rows)
    validate_metadata_alignment(arrays, metadata)

    row_metrics = compute_row_metrics(arrays, metadata)
    source_summary = summarize_group(row_metrics, "source_index")
    split_summary = summarize_group(row_metrics, "split")
    target_summary = summarize_group(row_metrics, "target")
    balance = source_weight_balance(row_metrics)

    write_csv_rows(run_dir / "row_objective_metrics.csv", row_metrics.to_dict(orient="records"))
    write_csv_rows(run_dir / "source_objective_summary.csv", source_summary)
    write_csv_rows(run_dir / "split_objective_summary.csv", split_summary)
    write_csv_rows(run_dir / "target_objective_summary.csv", target_summary)

    nonzero_rows = int((row_metrics["sequence_mean_step_l2"] > 1e-8).sum())
    total_weight = float(row_metrics["weight"].sum())
    summary = {
        "run_type": "sequence_corpus_exact_objective_sanity",
        "corpus_npz": corpus_npz,
        "metadata_csv": metadata_csv,
        "rows": int(contract.rows),
        "observation_dim": int(contract.observation_dim),
        "hidden_dim": int(contract.hidden_dim),
        "max_sequence_length": int(contract.max_sequence_length),
        "action_dim": int(contract.action_dim),
        "source_count": int(contract.source_count),
        "splits": {str(key): int(value) for key, value in row_metrics["split"].value_counts().to_dict().items()},
        "targets": {str(key): int(value) for key, value in row_metrics["target"].value_counts().to_dict().items()},
        "nonzero_delta_rows": nonzero_rows,
        "all_rows_have_nonzero_target_delta": bool(nonzero_rows == contract.rows),
        "weighted_sequence_mse_mean": float(row_metrics["weighted_sequence_mse"].sum() / max(total_weight, 1e-12)),
        "weighted_mean_step_l2": float(row_metrics["weighted_mean_step_l2"].sum() / max(total_weight, 1e-12)),
        "max_sequence_step_l2": float(row_metrics["sequence_max_step_l2"].max()),
        "outside_mask_abs_max": outside_mask_abs_max(arrays),
        "finite_metrics": bool(np.isfinite(row_metrics.select_dtypes(include=[np.number]).to_numpy()).all()),
        "source_weight_balance": balance,
        "row_metrics_csv": run_dir / "row_objective_metrics.csv",
        "source_objective_summary_csv": run_dir / "source_objective_summary.csv",
        "split_objective_summary_csv": run_dir / "split_objective_summary.csv",
        "target_objective_summary_csv": run_dir / "target_objective_summary.csv",
        "diagnostic_only": True,
        "training_started": False,
        "actor_parameters_changed": False,
        "labels_enter_actor_input": False,
        "ppo_used": False,
        "promoted": False,
        "optimizer_admission": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run exact sanity checks on a sequence target corpus.")
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="sequence_corpus_exact_objective_sanity")
    summary = run_sequence_corpus_exact_objective_sanity(
        corpus_npz=args.corpus,
        metadata_csv=args.metadata,
        run_dir=run_dir,
    )
    print(f"run_dir={run_dir}")
    print(f"rows={summary['rows']}")
    print(f"weighted_sequence_mse_mean={summary['weighted_sequence_mse_mean']:.8f}")
    print(f"source_weight_balanced={summary['source_weight_balance']['source_weight_balanced']}")


if __name__ == "__main__":
    main()
