"""Frozen feature-view probe for wrong-history fusion-boundary diagnosis."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.bc_v2_head_only_repeat import parse_seed_list
from autodrift.bc_v2_head_only_smoke import freeze_actor
from autodrift.bc_v2_wrong_history_contrast import train_one_contrast_seed
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.sequence_corpus_exact_objective_sanity import (
    load_metadata_csv,
    load_sequence_corpus_npz,
    source_weight_balance,
    validate_metadata_alignment,
    validate_sequence_corpus_contract,
)
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import resolve_device
from autodrift.wrong_history_feature_separability_audit import batched_recurrent_outputs


VALID_VIEWS = ("fused", "next_hidden", "fused_plus_next_hidden")


def parse_views(value: str) -> tuple[str, ...]:
    views = tuple(item.strip() for item in value.split(",") if item.strip())
    if not views:
        raise argparse.ArgumentTypeError("views cannot be empty")
    invalid = [view for view in views if view not in VALID_VIEWS]
    if invalid:
        raise argparse.ArgumentTypeError(f"invalid views: {', '.join(invalid)}")
    if len(set(views)) != len(views):
        raise argparse.ArgumentTypeError("views must not contain duplicates")
    return views


def build_feature_views(
    normal_outputs: dict[str, np.ndarray],
    variant_outputs: dict[str, np.ndarray],
    views: tuple[str, ...],
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    output: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for view in views:
        if view == "fused":
            output[view] = (normal_outputs["features"], variant_outputs["features"])
        elif view == "next_hidden":
            output[view] = (normal_outputs["next_hidden"], variant_outputs["next_hidden"])
        elif view == "fused_plus_next_hidden":
            output[view] = (
                np.concatenate([normal_outputs["features"], normal_outputs["next_hidden"]], axis=1).astype(np.float32),
                np.concatenate([variant_outputs["features"], variant_outputs["next_hidden"]], axis=1).astype(np.float32),
            )
        else:  # pragma: no cover - parse_views prevents this.
            raise ValueError(f"unknown view: {view}")
    return output


def diagnostic_view_passes(summary: dict[str, Any], fused_same_seed_l2: float) -> bool:
    return bool(
        summary["normal_validation_delta_mse"] <= 0.0010
        and summary["wrong_validation_gap_mse"] >= 0.00010
        and summary["wrong_validation_prediction_gap_l2"] >= 0.005
        and summary["wrong_validation_prediction_gap_l2"] >= 3.0 * max(float(fused_same_seed_l2), 1e-12)
    )


def _view_summary_by_seed(seed_summaries: list[dict[str, Any]]) -> dict[tuple[int, str], dict[str, Any]]:
    return {(int(row["seed"]), str(row["view"])): row for row in seed_summaries}


def apply_view_pass_rules(seed_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    by_key = _view_summary_by_seed(seed_summaries)
    view_counts: dict[str, int] = {view: 0 for view in VALID_VIEWS}
    fused_weak_count = 0
    for row in seed_summaries:
        if row["view"] == "fused" and row["wrong_validation_prediction_gap_l2"] < 0.005:
            fused_weak_count += 1
    for row in seed_summaries:
        view = str(row["view"])
        if view == "fused":
            row["diagnostic_view_passed"] = False
            continue
        fused = by_key.get((int(row["seed"]), "fused"))
        fused_l2 = float(fused["wrong_validation_prediction_gap_l2"]) if fused is not None else 0.0
        row["same_seed_fused_wrong_validation_prediction_gap_l2"] = fused_l2
        row["wrong_validation_prediction_gap_l2_vs_fused_ratio"] = float(row["wrong_validation_prediction_gap_l2"]) / max(fused_l2, 1e-12)
        row["diagnostic_view_passed"] = diagnostic_view_passes(row, fused_l2)
        if row["diagnostic_view_passed"]:
            view_counts[view] = view_counts.get(view, 0) + 1
    for row in seed_summaries:
        if row["view"] == "fused":
            row["same_seed_fused_wrong_validation_prediction_gap_l2"] = row["wrong_validation_prediction_gap_l2"]
            row["wrong_validation_prediction_gap_l2_vs_fused_ratio"] = 1.0
    passed_views = [view for view, count in view_counts.items() if view != "fused" and count >= 2]
    return {
        "diagnostic_passed": bool(passed_views),
        "passed_views": passed_views,
        "view_pass_counts": view_counts,
        "fused_weak_seed_count": int(fused_weak_count),
    }


def run_wrong_history_fusion_boundary_probe(
    *,
    corpus_npz: Path,
    metadata_csv: Path,
    checkpoint_path: Path,
    seeds: tuple[int, ...],
    epochs: int,
    learning_rate: float,
    weight_decay: float,
    hidden_dim: int,
    contrast_coef: float,
    wrong_zero_coef: float,
    margin_mse: float,
    views: tuple[str, ...],
    device: str,
    run_dir: Path,
    batch_size: int = 1024,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    arrays = load_sequence_corpus_npz(corpus_npz)
    contract = validate_sequence_corpus_contract(arrays)
    metadata = load_metadata_csv(metadata_csv, expected_rows=contract.rows)
    validate_metadata_alignment(arrays, metadata)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    freeze_actor(model)
    before_checksum = model_parameter_checksum(model)
    normal_outputs = batched_recurrent_outputs(
        model,
        arrays["observation"],
        arrays["normal_hidden"],
        device=resolved_device,
        batch_size=batch_size,
    )
    variant_outputs = batched_recurrent_outputs(
        model,
        arrays["observation"],
        arrays["variant_hidden"],
        device=resolved_device,
        batch_size=batch_size,
    )
    feature_views = build_feature_views(normal_outputs, variant_outputs, views)
    seed_summaries: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    row_contrast_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    target_rows: list[dict[str, Any]] = []
    history_rows: list[dict[str, Any]] = []
    view_feature_dims: dict[str, int] = {}
    for view_name, (features_normal, features_variant) in feature_views.items():
        view_feature_dims[view_name] = int(features_normal.shape[1])
        for seed in seeds:
            seed_dir = run_dir / f"seed_{int(seed)}" / f"view_{view_name}"
            summary, metrics, row_metrics, source_summary, target_summary, history_summary = train_one_contrast_seed(
                seed=int(seed),
                arrays=arrays,
                metadata=metadata,
                features_normal=features_normal,
                features_variant=features_variant,
                epochs=epochs,
                learning_rate=learning_rate,
                weight_decay=weight_decay,
                hidden_dim=hidden_dim,
                contrast_coef=contrast_coef,
                wrong_zero_coef=wrong_zero_coef,
                margin_mse=margin_mse,
                device=resolved_device,
                seed_dir=seed_dir,
            )
            summary.update({"view": view_name, "view_feature_dim": int(features_normal.shape[1])})
            seed_summaries.append(summary)
            metric_rows.extend({"view": view_name, **row} for row in metrics)
            row_contrast_rows.extend({"view": view_name, "seed": int(seed), **row} for row in row_metrics.to_dict("records"))
            source_rows.extend({"view": view_name, "seed": int(seed), **row} for row in source_summary)
            target_rows.extend({"view": view_name, "seed": int(seed), **row} for row in target_summary)
            history_rows.extend({"view": view_name, "seed": int(seed), **row} for row in history_summary)
    after_checksum = model_parameter_checksum(model)
    actor_changed = bool(before_checksum != after_checksum)
    for row in seed_summaries:
        row["actor_parameters_changed"] = actor_changed
        row["actor_checkpoint_written"] = False
    diagnostic = apply_view_pass_rules(seed_summaries)
    write_csv_rows(run_dir / "seed_view_summary.csv", seed_summaries)
    write_csv_rows(run_dir / "view_metrics.csv", metric_rows)
    write_csv_rows(run_dir / "view_row_contrast_metrics.csv", row_contrast_rows)
    write_csv_rows(run_dir / "view_source_summary.csv", source_rows)
    write_csv_rows(run_dir / "view_target_summary.csv", target_rows)
    write_csv_rows(run_dir / "view_history_variant_summary.csv", history_rows)
    summary = {
        "run_type": "wrong_history_fusion_boundary_probe",
        "corpus_npz": corpus_npz,
        "metadata_csv": metadata_csv,
        "checkpoint": checkpoint_path,
        "rows": int(contract.rows),
        "source_count": int(contract.source_count),
        "seeds": [int(seed) for seed in seeds],
        "views": list(views),
        "view_feature_dims": view_feature_dims,
        "epochs": int(epochs),
        "learning_rate": float(learning_rate),
        "weight_decay": float(weight_decay),
        "hidden_dim": int(hidden_dim),
        "contrast_coef": float(contrast_coef),
        "wrong_zero_coef": float(wrong_zero_coef),
        "margin_mse": float(margin_mse),
        "device": str(resolved_device),
        "batch_size": int(batch_size),
        "model_checksum_before": before_checksum,
        "model_checksum_after": after_checksum,
        "actor_parameters_changed": actor_changed,
        "actor_checkpoint_written": False,
        "diagnostic_head_checkpoints_written": bool(list(run_dir.rglob("sequence_delta_head_best_validation.pt"))),
        "seed_view_summary_csv": run_dir / "seed_view_summary.csv",
        "view_metrics_csv": run_dir / "view_metrics.csv",
        "view_row_contrast_metrics_csv": run_dir / "view_row_contrast_metrics.csv",
        "view_source_summary_csv": run_dir / "view_source_summary.csv",
        "view_target_summary_csv": run_dir / "view_target_summary.csv",
        "view_history_variant_summary_csv": run_dir / "view_history_variant_summary.csv",
        "diagnostic": diagnostic,
        "source_weight_balance": source_weight_balance(
            pd.DataFrame(
                {
                    "source_index": arrays["source_index"].astype(int),
                    "weight": arrays["weight"].astype(float),
                }
            )
        ),
        "diagnostic_only": True,
        "training_started": True,
        "optimizer_started": True,
        "actor_training_started": False,
        "labels_enter_actor_input": False,
        "ppo_used": False,
        "promoted": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run frozen feature-view wrong-history probe.")
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--seeds", type=parse_seed_list, required=True)
    parser.add_argument("--epochs", type=int, default=240)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument("--weight-decay", type=float, default=0.0001)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--contrast-coef", type=float, default=1.0)
    parser.add_argument("--wrong-zero-coef", type=float, default=0.05)
    parser.add_argument("--margin-mse", type=float, default=0.00025)
    parser.add_argument("--views", type=parse_views, default="fused,next_hidden,fused_plus_next_hidden")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="wrong_history_fusion_boundary_probe")
    summary = run_wrong_history_fusion_boundary_probe(
        corpus_npz=args.corpus,
        metadata_csv=args.metadata,
        checkpoint_path=args.checkpoint,
        seeds=args.seeds,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        hidden_dim=args.hidden_dim,
        contrast_coef=args.contrast_coef,
        wrong_zero_coef=args.wrong_zero_coef,
        margin_mse=args.margin_mse,
        views=args.views,
        device=args.device,
        batch_size=args.batch_size,
        run_dir=run_dir,
    )
    print(f"run_dir={run_dir}")
    print(f"diagnostic_passed={summary['diagnostic']['diagnostic_passed']}")
    print(f"passed_views={','.join(summary['diagnostic']['passed_views'])}")
    print(f"summary={run_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
