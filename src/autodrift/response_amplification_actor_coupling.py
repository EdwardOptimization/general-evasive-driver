"""Frozen-backbone response-amplification actor-coupling probe."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.bc_v2_head_only_repeat import parse_seed_list
from autodrift.bc_v2_head_only_smoke import freeze_actor
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.response_amplification_shadow import (
    ResponseAmplifierHead,
    _loss_components,
    _predict,
    _split_indices,
    _tensor_batch,
    _weighted_mean,
    summarize_shadow_predictions,
)
from autodrift.sequence_corpus_exact_objective_sanity import (
    load_metadata_csv,
    load_sequence_corpus_npz,
    validate_metadata_alignment,
    validate_sequence_corpus_contract,
)
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import resolve_device
from autodrift.wrong_history_feature_separability_audit import batched_recurrent_outputs
from autodrift.wrong_history_fusion_boundary_probe import build_feature_views


VALID_ACTOR_COUPLING_VIEWS = ("fused_plus_next_hidden",)
EPS = 1e-12


def parse_alpha_list(raw: str) -> tuple[float, ...]:
    values = tuple(float(part.strip()) for part in str(raw).split(",") if part.strip())
    if not values:
        raise argparse.ArgumentTypeError("alpha list cannot be empty")
    if any(value < 0.0 for value in values):
        raise argparse.ArgumentTypeError("alphas must be nonnegative")
    if len(set(values)) != len(values):
        raise argparse.ArgumentTypeError("alphas must not contain duplicates")
    return tuple(sorted(values))


def parse_actor_coupling_view(raw: str) -> str:
    value = str(raw).strip()
    if value not in VALID_ACTOR_COUPLING_VIEWS:
        raise argparse.ArgumentTypeError(
            "actor-coupling view must be one of: " + ", ".join(VALID_ACTOR_COUPLING_VIEWS)
        )
    return value


def _sequence_smoothness(prediction: torch.Tensor, mask: torch.Tensor, weight: torch.Tensor) -> torch.Tensor:
    if prediction.shape[1] <= 1:
        return torch.zeros((), dtype=prediction.dtype, device=prediction.device)
    diff = prediction[:, 1:, :] - prediction[:, :-1, :]
    pair_mask = mask[:, 1:] * mask[:, :-1]
    per_row = (torch.square(diff) * pair_mask[:, :, None]).sum(dim=(1, 2))
    denom = torch.clamp(pair_mask.sum(dim=1) * prediction.shape[2], min=1.0)
    return _weighted_mean(per_row / denom, weight)


def _normal_first_mse(prediction_normal: torch.Tensor, weight: torch.Tensor) -> torch.Tensor:
    per_row = torch.square(prediction_normal[:, 0, :]).mean(dim=1)
    return _weighted_mean(per_row, weight)


def _normal_first_topk_hinge(
    prediction_normal: torch.Tensor,
    *,
    threshold: float,
    fraction: float,
) -> torch.Tensor:
    first_l2 = torch.linalg.norm(prediction_normal[:, 0, :], dim=1)
    hinge = torch.square(torch.relu(first_l2 - float(threshold)))
    if hinge.numel() == 0:
        return torch.zeros((), dtype=prediction_normal.dtype, device=prediction_normal.device)
    k = max(1, int(np.ceil(float(fraction) * int(hinge.numel()))))
    k = min(k, int(hinge.numel()))
    return torch.topk(hinge, k=k, largest=True).values.mean()


def _wrong_first_gap_hinge(
    prediction_normal: torch.Tensor,
    prediction_wrong: torch.Tensor,
    weight: torch.Tensor,
    *,
    target_gap: float,
) -> torch.Tensor:
    first_gap = torch.linalg.norm(prediction_wrong[:, 0, :] - prediction_normal[:, 0, :], dim=1)
    per_row = torch.square(torch.relu(float(target_gap) - first_gap))
    return _weighted_mean(per_row, weight)


def _coupling_loss_components(
    head: ResponseAmplifierHead,
    batch: dict[str, torch.Tensor],
    indices: np.ndarray,
    *,
    wrong_target_coef: float,
    gap_margin_coef: float,
    smoothness_coef: float,
    normal_first_coef: float,
    normal_first_topk_coef: float,
    normal_first_threshold: float,
    normal_first_topk_fraction: float,
    wrong_first_gap_coef: float,
    wrong_first_target_gap: float,
    target_gap: float,
) -> dict[str, torch.Tensor]:
    losses = _loss_components(
        head,
        batch,
        indices,
        wrong_target_coef=wrong_target_coef,
        gap_margin_coef=gap_margin_coef,
        zero_regularizer_coef=0.0,
        target_gap=target_gap,
    )
    index_t = torch.as_tensor(indices, dtype=torch.long, device=batch["mask"].device)
    pred_normal = head(batch["features_normal"].index_select(0, index_t))
    pred_wrong = head(batch["features_variant"].index_select(0, index_t))
    mask = batch["mask"].index_select(0, index_t)
    weight = batch["weight"].index_select(0, index_t)
    smoothness = 0.5 * (
        _sequence_smoothness(pred_normal, mask, weight) + _sequence_smoothness(pred_wrong, mask, weight)
    )
    normal_first = _normal_first_mse(pred_normal, weight)
    normal_topk = _normal_first_topk_hinge(
        pred_normal,
        threshold=normal_first_threshold,
        fraction=normal_first_topk_fraction,
    )
    wrong_first_gap = _wrong_first_gap_hinge(
        pred_normal,
        pred_wrong,
        weight,
        target_gap=wrong_first_target_gap,
    )
    losses["sequence_smoothness_mse"] = smoothness
    losses["normal_first_mse"] = normal_first
    losses["normal_first_topk_hinge"] = normal_topk
    losses["wrong_first_gap_hinge"] = wrong_first_gap
    losses["total_loss"] = (
        losses["total_loss"]
        + float(smoothness_coef) * smoothness
        + float(normal_first_coef) * normal_first
        + float(normal_first_topk_coef) * normal_topk
        + float(wrong_first_gap_coef) * wrong_first_gap
    )
    return losses


def _first_l2(prediction: np.ndarray) -> np.ndarray:
    return np.linalg.norm(prediction[:, 0, :].astype(np.float64), axis=1)


def alpha_candidate_passes(row: dict[str, Any]) -> bool:
    return bool(
        row["split"] == "source_holdout_validation"
        and float(row["alpha"]) > 0.0
        and row["normal_delta_l2_mean"] <= 0.0025
        and row["normal_delta_l2_p95"] <= 0.0060
        and row["predicted_normal_wrong_gap_l2_mean"] >= 0.010
        and row["predicted_normal_wrong_gap_l2_p10"] >= 0.004
        and row["gap_improvement_ratio"] >= 3.0
        and row["wrong_target_mse_improvement"] >= 0.50
        and row["normal_action_drift_first_l2_p95"] <= 0.0060
    )


def evaluate_alpha_ladder(
    *,
    arrays: dict[str, np.ndarray],
    metadata: pd.DataFrame,
    prediction_normal: np.ndarray,
    prediction_wrong: np.ndarray,
    alphas: tuple[float, ...],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    alpha_rows: list[dict[str, Any]] = []
    for alpha in alphas:
        scaled_normal = prediction_normal * float(alpha)
        scaled_wrong = prediction_wrong * float(alpha)
        row_metrics, _source, split_summary, _target = summarize_shadow_predictions(
            arrays,
            metadata,
            prediction_normal=scaled_normal,
            prediction_wrong=scaled_wrong,
        )
        first_normal = _first_l2(scaled_normal)
        first_wrong = _first_l2(scaled_wrong)
        row_metrics = row_metrics.copy()
        row_metrics["normal_action_drift_first_l2"] = first_normal
        row_metrics["wrong_action_drift_first_l2"] = first_wrong
        for split_row in split_summary:
            split = str(split_row["split"])
            split_metrics = row_metrics[row_metrics["split"].astype(str) == split]
            output = {
                "alpha": float(alpha),
                **split_row,
                "normal_action_drift_first_l2_mean": float(split_metrics["normal_action_drift_first_l2"].mean()),
                "normal_action_drift_first_l2_p95": float(
                    np.percentile(split_metrics["normal_action_drift_first_l2"].to_numpy(dtype=float), 95)
                ),
                "wrong_action_drift_first_l2_mean": float(split_metrics["wrong_action_drift_first_l2"].mean()),
                "wrong_action_drift_first_l2_p95": float(
                    np.percentile(split_metrics["wrong_action_drift_first_l2"].to_numpy(dtype=float), 95)
                ),
            }
            output["alpha_candidate_passed"] = alpha_candidate_passes(output)
            alpha_rows.append(output)
    source_holdout_passes = [
        row
        for row in alpha_rows
        if row["split"] == "source_holdout_validation" and bool(row["alpha_candidate_passed"])
    ]
    selected = max(source_holdout_passes, key=lambda row: float(row["alpha"])) if source_holdout_passes else None
    summary = {
        "alpha_passed": bool(selected is not None),
        "selected_alpha": float(selected["alpha"]) if selected is not None else 0.0,
        "selected_source_holdout_normal_delta_l2_mean": float(selected["normal_delta_l2_mean"]) if selected else None,
        "selected_source_holdout_predicted_normal_wrong_gap_l2_mean": float(selected["predicted_normal_wrong_gap_l2_mean"]) if selected else None,
        "selected_source_holdout_gap_improvement_ratio": float(selected["gap_improvement_ratio"]) if selected else None,
        "selected_source_holdout_normal_action_drift_first_l2_p95": float(
            selected["normal_action_drift_first_l2_p95"]
        )
        if selected
        else None,
    }
    return alpha_rows, summary


def train_actor_coupling_seed(
    *,
    arrays: dict[str, np.ndarray],
    metadata: pd.DataFrame,
    features_normal: np.ndarray,
    features_variant: np.ndarray,
    alphas: tuple[float, ...],
    hidden_dim: int,
    epochs: int,
    learning_rate: float,
    weight_decay: float,
    seed: int,
    wrong_target_coef: float,
    gap_margin_coef: float,
    smoothness_coef: float,
    normal_first_coef: float = 0.0,
    normal_first_topk_coef: float = 0.0,
    normal_first_threshold: float = 0.004,
    normal_first_topk_fraction: float = 0.10,
    wrong_first_gap_coef: float = 0.0,
    wrong_first_target_gap: float = 0.006,
    target_gap: float,
    device: torch.device,
) -> tuple[ResponseAmplifierHead, list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    torch.manual_seed(int(seed))
    contract = validate_sequence_corpus_contract(arrays)
    train_indices = _split_indices(metadata, "train")
    val_indices = _split_indices(metadata, "source_holdout_validation")
    if train_indices.size == 0 or val_indices.size == 0:
        raise ValueError("both train and source_holdout_validation splits are required")
    batch = _tensor_batch(arrays, features_normal, features_variant, device)
    head = ResponseAmplifierHead(
        feature_dim=int(features_normal.shape[1]),
        hidden_dim=int(hidden_dim),
        max_sequence_length=contract.max_sequence_length,
        action_dim=contract.action_dim,
    ).to(device)
    optimizer = torch.optim.AdamW(head.parameters(), lr=float(learning_rate), weight_decay=float(weight_decay))
    metric_rows: list[dict[str, Any]] = []
    log_interval = max(1, int(epochs) // 10)

    def append_metrics(epoch: int) -> None:
        with torch.no_grad():
            for split, indices in (("train", train_indices), ("source_holdout_validation", val_indices)):
                losses = _coupling_loss_components(
                    head,
                    batch,
                    indices,
                    wrong_target_coef=wrong_target_coef,
                    gap_margin_coef=gap_margin_coef,
                    smoothness_coef=smoothness_coef,
                    normal_first_coef=normal_first_coef,
                    normal_first_topk_coef=normal_first_topk_coef,
                    normal_first_threshold=normal_first_threshold,
                    normal_first_topk_fraction=normal_first_topk_fraction,
                    wrong_first_gap_coef=wrong_first_gap_coef,
                    wrong_first_target_gap=wrong_first_target_gap,
                    target_gap=target_gap,
                )
                metric_rows.append(
                    {
                        "epoch": int(epoch),
                        "split": split,
                        **{key: float(value.detach().cpu().item()) for key, value in losses.items()},
                    }
                )

    append_metrics(0)
    for epoch in range(1, int(epochs) + 1):
        optimizer.zero_grad()
        losses = _coupling_loss_components(
            head,
            batch,
            train_indices,
            wrong_target_coef=wrong_target_coef,
            gap_margin_coef=gap_margin_coef,
            smoothness_coef=smoothness_coef,
            normal_first_coef=normal_first_coef,
            normal_first_topk_coef=normal_first_topk_coef,
            normal_first_threshold=normal_first_threshold,
            normal_first_topk_fraction=normal_first_topk_fraction,
            wrong_first_gap_coef=wrong_first_gap_coef,
            wrong_first_target_gap=wrong_first_target_gap,
            target_gap=target_gap,
        )
        losses["total_loss"].backward()
        optimizer.step()
        if epoch == int(epochs) or epoch % log_interval == 0:
            append_metrics(epoch)

    prediction_normal = _predict(head, features_normal, device)
    prediction_wrong = _predict(head, features_variant, device)
    alpha_rows, alpha_summary = evaluate_alpha_ladder(
        arrays=arrays,
        metadata=metadata,
        prediction_normal=prediction_normal,
        prediction_wrong=prediction_wrong,
        alphas=alphas,
    )
    summary = {
        "seed": int(seed),
        "feature_dim": int(features_normal.shape[1]),
        "hidden_dim": int(hidden_dim),
        "epochs": int(epochs),
        "learning_rate": float(learning_rate),
        "weight_decay": float(weight_decay),
        "wrong_target_coef": float(wrong_target_coef),
        "gap_margin_coef": float(gap_margin_coef),
        "smoothness_coef": float(smoothness_coef),
        "normal_first_coef": float(normal_first_coef),
        "normal_first_topk_coef": float(normal_first_topk_coef),
        "normal_first_threshold": float(normal_first_threshold),
        "normal_first_topk_fraction": float(normal_first_topk_fraction),
        "wrong_first_gap_coef": float(wrong_first_gap_coef),
        "wrong_first_target_gap": float(wrong_first_target_gap),
        "target_gap": float(target_gap),
        **alpha_summary,
    }
    return head, metric_rows, summary, alpha_rows


def apply_actor_coupling_pass_rules(seed_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    passed = [row for row in seed_summaries if bool(row.get("alpha_passed", False))]
    return {
        "actor_coupling_exact_passed": bool(passed),
        "passed_seed_count": int(len(passed)),
        "best_selected_alpha": float(max((row["selected_alpha"] for row in passed), default=0.0)),
        "passed_seeds": [int(row["seed"]) for row in passed],
    }


def run_response_amplification_actor_coupling(
    *,
    checkpoint_path: Path,
    shadow_corpus_npz: Path,
    metadata_csv: Path,
    view: str,
    seeds: tuple[int, ...],
    alphas: tuple[float, ...],
    target_gap: float,
    epochs: int,
    learning_rate: float,
    weight_decay: float,
    hidden_dim: int,
    wrong_target_coef: float,
    gap_margin_coef: float,
    smoothness_coef: float,
    normal_first_coef: float,
    normal_first_topk_coef: float,
    normal_first_threshold: float,
    normal_first_topk_fraction: float,
    wrong_first_gap_coef: float,
    wrong_first_target_gap: float,
    device: str,
    run_dir: Path,
    batch_size: int = 1024,
) -> dict[str, Any]:
    if view not in VALID_ACTOR_COUPLING_VIEWS:
        raise ValueError(f"unsupported actor-coupling view: {view}")
    run_dir.mkdir(parents=True, exist_ok=True)
    arrays = load_sequence_corpus_npz(shadow_corpus_npz)
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
    features_normal, features_variant = build_feature_views(normal_outputs, variant_outputs, (view,))[view]
    seed_summaries: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    alpha_rows: list[dict[str, Any]] = []
    for seed in seeds:
        seed_dir = run_dir / f"seed_{int(seed)}"
        seed_dir.mkdir(parents=True, exist_ok=True)
        head, metrics, summary, seed_alpha_rows = train_actor_coupling_seed(
            arrays=arrays,
            metadata=metadata,
            features_normal=features_normal,
            features_variant=features_variant,
            alphas=alphas,
            hidden_dim=hidden_dim,
            epochs=epochs,
            learning_rate=learning_rate,
            weight_decay=weight_decay,
            seed=int(seed),
            wrong_target_coef=wrong_target_coef,
            gap_margin_coef=gap_margin_coef,
            smoothness_coef=smoothness_coef,
            normal_first_coef=normal_first_coef,
            normal_first_topk_coef=normal_first_topk_coef,
            normal_first_threshold=normal_first_threshold,
            normal_first_topk_fraction=normal_first_topk_fraction,
            wrong_first_gap_coef=wrong_first_gap_coef,
            wrong_first_target_gap=wrong_first_target_gap,
            target_gap=target_gap,
            device=resolved_device,
        )
        head_path = seed_dir / "residual_sequence_head.pt"
        torch.save(
            {
                "head_state": head.state_dict(),
                "view": view,
                "seed": int(seed),
                "feature_dim": int(features_normal.shape[1]),
                "hidden_dim": int(hidden_dim),
                "max_sequence_length": int(arrays["sequence_mask"].shape[1]),
                "action_dim": 3,
                "execution": "first_residual_only",
            },
            head_path,
        )
        summary.update({"view": view, "head_checkpoint": str(head_path)})
        seed_summaries.append(summary)
        metric_rows.extend({"seed": int(seed), **row} for row in metrics)
        alpha_rows.extend({"seed": int(seed), **row} for row in seed_alpha_rows)

    after_checksum = model_parameter_checksum(model)
    actor_changed = bool(before_checksum != after_checksum)
    for row in seed_summaries:
        row["actor_parameters_changed"] = actor_changed
        row["base_actor_checkpoint_written"] = False
        row["ppo_used"] = False
        row["promoted"] = False
    pass_rules = apply_actor_coupling_pass_rules(seed_summaries)
    write_csv_rows(run_dir / "seed_view_summary.csv", seed_summaries)
    write_csv_rows(run_dir / "train_metrics.csv", metric_rows)
    write_csv_rows(run_dir / "alpha_summary.csv", alpha_rows)
    summary = {
        "run_type": "response_amplification_actor_coupling",
        "checkpoint": checkpoint_path,
        "shadow_corpus_npz": shadow_corpus_npz,
        "metadata_csv": metadata_csv,
        "view": view,
        "rows": int(contract.rows),
        "source_count": int(contract.source_count),
        "seeds": [int(seed) for seed in seeds],
        "alphas": [float(alpha) for alpha in alphas],
        "target_gap": float(target_gap),
        "epochs": int(epochs),
        "learning_rate": float(learning_rate),
        "weight_decay": float(weight_decay),
        "hidden_dim": int(hidden_dim),
        "wrong_target_coef": float(wrong_target_coef),
        "gap_margin_coef": float(gap_margin_coef),
        "smoothness_coef": float(smoothness_coef),
        "normal_first_coef": float(normal_first_coef),
        "normal_first_topk_coef": float(normal_first_topk_coef),
        "normal_first_threshold": float(normal_first_threshold),
        "normal_first_topk_fraction": float(normal_first_topk_fraction),
        "wrong_first_gap_coef": float(wrong_first_gap_coef),
        "wrong_first_target_gap": float(wrong_first_target_gap),
        "model_checksum_before": before_checksum,
        "model_checksum_after": after_checksum,
        "actor_parameters_changed": actor_changed,
        "base_actor_checkpoint_written": False,
        "residual_head_checkpoint_count": int(len(seed_summaries)),
        "ppo_used": False,
        "promoted": False,
        "execution": "first_residual_only",
        "seed_view_summary_csv": run_dir / "seed_view_summary.csv",
        "alpha_summary_csv": run_dir / "alpha_summary.csv",
        **pass_rules,
        "diagnostic_only": True,
        "training_started": True,
        "optimizer_started": True,
        "actor_training_started": False,
        "labels_enter_actor_input": False,
    }
    summary["actor_coupling_exact_passed"] = bool(summary["actor_coupling_exact_passed"] and not actor_changed)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a frozen-backbone residual actor-coupling exact probe.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--shadow-corpus", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--view", type=parse_actor_coupling_view, default="fused_plus_next_hidden")
    parser.add_argument("--seeds", type=parse_seed_list, default=(6740, 6741, 6742))
    parser.add_argument("--alphas", type=parse_alpha_list, default=(0.02, 0.05, 0.10, 0.20, 0.50, 1.00))
    parser.add_argument("--target-gap", type=float, default=0.010)
    parser.add_argument("--epochs", type=int, default=240)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument("--weight-decay", type=float, default=0.0001)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--wrong-target-coef", type=float, default=1.0)
    parser.add_argument("--gap-margin-coef", type=float, default=0.25)
    parser.add_argument("--smoothness-coef", type=float, default=0.05)
    parser.add_argument("--normal-first-coef", type=float, default=0.0)
    parser.add_argument("--normal-first-topk-coef", type=float, default=0.0)
    parser.add_argument("--normal-first-threshold", type=float, default=0.004)
    parser.add_argument("--normal-first-topk-fraction", type=float, default=0.10)
    parser.add_argument("--wrong-first-gap-coef", type=float, default=0.0)
    parser.add_argument("--wrong-first-target-gap", type=float, default=0.006)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="response_amplification_actor_coupling")
    summary = run_response_amplification_actor_coupling(
        checkpoint_path=args.checkpoint,
        shadow_corpus_npz=args.shadow_corpus,
        metadata_csv=args.metadata,
        view=args.view,
        seeds=args.seeds,
        alphas=args.alphas,
        target_gap=args.target_gap,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        hidden_dim=args.hidden_dim,
        wrong_target_coef=args.wrong_target_coef,
        gap_margin_coef=args.gap_margin_coef,
        smoothness_coef=args.smoothness_coef,
        normal_first_coef=args.normal_first_coef,
        normal_first_topk_coef=args.normal_first_topk_coef,
        normal_first_threshold=args.normal_first_threshold,
        normal_first_topk_fraction=args.normal_first_topk_fraction,
        wrong_first_gap_coef=args.wrong_first_gap_coef,
        wrong_first_target_gap=args.wrong_first_target_gap,
        device=args.device,
        run_dir=run_dir,
        batch_size=args.batch_size,
    )
    print(f"run_dir={run_dir}")
    print(f"actor_coupling_exact_passed={summary['actor_coupling_exact_passed']}")
    print(f"passed_seeds={summary['passed_seeds']}")
    print(f"best_selected_alpha={summary['best_selected_alpha']}")
    print(f"summary={run_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
