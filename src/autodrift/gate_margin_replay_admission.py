"""Replay admission gate for M689 gate-margin residual heads."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.bc_v2_head_only_smoke import freeze_actor
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.grounded_capability_action_target_miner import SurfaceConfig, parse_surface_config, risk_score
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.matched_history_outcome_gate import OutcomeSnapshot, collect_requested_outcome_snapshots
from autodrift.response_amplification_actor_coupling import (
    GatedResponseAmplifierHead,
    _predict_with_aux,
)
from autodrift.sequence_corpus_exact_objective_sanity import (
    load_metadata_csv,
    load_sequence_corpus_npz,
    validate_metadata_alignment,
    validate_sequence_corpus_contract,
)
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.terminal_margin_recovery_anchor import _rollout_first_action_override
from autodrift.train_ppo import ActorCritic, resolve_device
from autodrift.wrong_history_feature_separability_audit import batched_recurrent_outputs
from autodrift.wrong_history_fusion_boundary_probe import build_feature_views


VALID_VIEW = "fused_plus_next_hidden"
SUPPORTED_VARIANTS = {"wrong_matched_history"}


def _finite_float(value: Any, default: float = float("nan")) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    return parsed if np.isfinite(parsed) else float(default)


def _requested_steps(rows: pd.DataFrame) -> dict[int, set[int]]:
    requests: dict[int, set[int]] = {}
    for _, row in rows.iterrows():
        requests.setdefault(int(row["left_seed"]), set()).add(int(row["left_step"]))
        if str(row["variant"]) == "wrong_matched_history":
            requests.setdefault(int(row["right_seed"]), set()).add(int(row["right_step"]))
    return requests


def _snapshot(
    snapshots: dict[tuple[int, int], OutcomeSnapshot],
    seed: int,
    step: int,
) -> OutcomeSnapshot | None:
    return snapshots.get((int(seed), int(step)))


def _with_hidden(snapshot: OutcomeSnapshot, hidden: torch.Tensor) -> OutcomeSnapshot:
    return OutcomeSnapshot(
        seed=snapshot.seed,
        step=snapshot.step,
        observation=snapshot.observation.copy(),
        hidden=hidden.detach().clone(),
        env=snapshot.env,
        info=dict(snapshot.info),
    )


def _first_action(
    model: ActorCritic,
    observation: np.ndarray,
    hidden: torch.Tensor,
    device: torch.device,
) -> np.ndarray:
    action, _ = deterministic_action_from_hidden(model, np.asarray(observation, dtype=np.float32), hidden, device)
    return np.asarray(action, dtype=np.float32)


def _margin(result: dict[str, Any]) -> float:
    return _finite_float(result.get("min_clearance_margin"))


def _result_prefix(prefix: str, result: dict[str, Any]) -> dict[str, Any]:
    return {
        f"{prefix}_success": bool(result.get("success", False)),
        f"{prefix}_collision": bool(result.get("collision", False)),
        f"{prefix}_off_road": bool(result.get("off_road", False)),
        f"{prefix}_spin_out": bool(result.get("spin_out", False)),
        f"{prefix}_terminal_reason": str(result.get("terminal_reason", "")),
        f"{prefix}_margin": _margin(result),
        f"{prefix}_risk": float(risk_score(result)),
        f"{prefix}_return": _finite_float(result.get("return")),
    }


def load_residual_head(path: Path, device: torch.device) -> tuple[GatedResponseAmplifierHead, dict[str, Any]]:
    payload = torch.load(path, map_location=device)
    if str(payload.get("head_type")) != "gated":
        raise ValueError(f"M692 replay admission currently expects gated residual heads, got {payload.get('head_type')!r}")
    head = GatedResponseAmplifierHead(
        feature_dim=int(payload["feature_dim"]),
        hidden_dim=int(payload["hidden_dim"]),
        max_sequence_length=int(payload["max_sequence_length"]),
        action_dim=int(payload.get("action_dim", 3)),
        max_residual=float(payload.get("max_residual", 0.04)),
    ).to(device)
    head.load_state_dict(payload["head_state"])
    head.eval()
    return head, dict(payload)


def select_replay_rows(metadata: pd.DataFrame, max_source_holdout_rows: int) -> pd.DataFrame:
    rows = metadata[
        (metadata["split"].astype(str) == "source_holdout_validation")
        & metadata["variant"].astype(str).isin(SUPPORTED_VARIANTS)
    ].copy()
    if rows.empty:
        return rows.reset_index(drop=False).rename(columns={"index": "row_index"})
    rows = rows.sort_values(
        ["surface", "target", "source_index", "sequence_length"],
        kind="mergesort",
    )
    if int(max_source_holdout_rows) > 0:
        rows = rows.head(int(max_source_holdout_rows))
    return rows.reset_index(drop=False).rename(columns={"index": "row_index"})


def summarize_replay_rows(
    rows: list[dict[str, Any]],
    *,
    max_first_action_l2: float,
    min_wrong_risk_improvement: float,
    max_normal_margin_regression: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not rows:
        summary = {
            "normal_first_action_l2_p95": float("nan"),
            "normal_margin_regression_mean": float("nan"),
            "normal_margin_regression_p95": float("nan"),
            "wrong_margin_improvement_mean": float("nan"),
            "wrong_risk_improvement_mean": float("nan"),
            "wrong_success_improvement_count": 0,
            "wrong_collision_reduction_count": 0,
            "replay_result_class": "surface_reconstruction_failure",
            "replay_admission_passed": False,
        }
        return [], summary

    frame = pd.DataFrame(rows)
    split_rows: list[dict[str, Any]] = []
    for (head_seed, split), group in frame.groupby(["head_seed", "split"], observed=True):
        normal_l2 = group["normal_first_action_l2"].astype(float).to_numpy()
        normal_regression = group["normal_margin_regression"].astype(float).to_numpy()
        wrong_margin = group["wrong_margin_improvement"].astype(float).to_numpy()
        wrong_risk = group["wrong_risk_improvement"].astype(float).to_numpy()
        split_rows.append(
            {
                "head_seed": int(head_seed),
                "split": str(split),
                "rows": int(len(group)),
                "normal_first_action_l2_p95": float(np.nanpercentile(normal_l2, 95)),
                "normal_margin_regression_mean": float(np.nanmean(normal_regression)),
                "normal_margin_regression_p95": float(np.nanpercentile(normal_regression, 95)),
                "wrong_margin_improvement_mean": float(np.nanmean(wrong_margin)),
                "wrong_risk_improvement_mean": float(np.nanmean(wrong_risk)),
                "wrong_success_improvement_count": int(group["wrong_success_improved"].astype(bool).sum()),
                "wrong_collision_reduction_count": int(group["wrong_collision_reduced"].astype(bool).sum()),
            }
        )

    normal_l2 = frame["normal_first_action_l2"].astype(float).to_numpy()
    normal_regression = frame["normal_margin_regression"].astype(float).to_numpy()
    wrong_margin = frame["wrong_margin_improvement"].astype(float).to_numpy()
    wrong_risk = frame["wrong_risk_improvement"].astype(float).to_numpy()
    aggregate = {
        "normal_first_action_l2_p95": float(np.nanpercentile(normal_l2, 95)),
        "normal_margin_regression_mean": float(np.nanmean(normal_regression)),
        "normal_margin_regression_p95": float(np.nanpercentile(normal_regression, 95)),
        "wrong_margin_improvement_mean": float(np.nanmean(wrong_margin)),
        "wrong_risk_improvement_mean": float(np.nanmean(wrong_risk)),
        "wrong_success_improvement_count": int(frame["wrong_success_improved"].astype(bool).sum()),
        "wrong_collision_reduction_count": int(frame["wrong_collision_reduced"].astype(bool).sum()),
    }
    normal_rejected = bool(
        aggregate["normal_first_action_l2_p95"] > float(max_first_action_l2)
        or aggregate["normal_margin_regression_mean"] > float(max_normal_margin_regression)
    )
    if normal_rejected:
        result_class = "normal_regression"
    elif (
        aggregate["wrong_risk_improvement_mean"] >= float(min_wrong_risk_improvement)
        or aggregate["wrong_success_improvement_count"] > 0
        or aggregate["wrong_collision_reduction_count"] > 0
    ):
        result_class = "replay_positive"
    else:
        result_class = "replay_neutral"
    aggregate["replay_result_class"] = result_class
    aggregate["replay_admission_passed"] = bool(result_class == "replay_positive")
    return split_rows, aggregate


def _summary_contract(
    *,
    before_checksum: str,
    after_checksum: str,
    run_dir: Path,
    replay_rows: list[dict[str, Any]],
    split_rows: list[dict[str, Any]],
    aggregate: dict[str, Any],
    rows_attempted: int,
    rows_reconstructable: int,
    source_holdout_rows: int,
    residual_head_count: int,
    selected_alpha: float,
    checkpoint_path: Path,
    shadow_corpus_npz: Path,
    metadata_csv: Path,
) -> dict[str, Any]:
    actor_changed = bool(before_checksum != after_checksum)
    return {
        "run_type": "gate_margin_replay_admission",
        "checkpoint": checkpoint_path,
        "shadow_corpus_npz": shadow_corpus_npz,
        "metadata_csv": metadata_csv,
        "rows_attempted": int(rows_attempted),
        "rows_reconstructable": int(rows_reconstructable),
        "rows_replayed": int(len(replay_rows)),
        "source_holdout_rows": int(source_holdout_rows),
        "residual_head_count": int(residual_head_count),
        "selected_alpha": float(selected_alpha),
        "actor_parameters_changed": actor_changed,
        "base_actor_checkpoint_written": False,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "model_checksum_before": before_checksum,
        "model_checksum_after": after_checksum,
        "replay_rows_csv": run_dir / "replay_rows.csv",
        "seed_summary_csv": run_dir / "seed_summary.csv",
        "split_summary_csv": run_dir / "split_summary.csv",
        **aggregate,
        "replay_admission_passed": bool(aggregate.get("replay_admission_passed", False) and not actor_changed),
        "split_summary_rows": int(len(split_rows)),
    }


def run_gate_margin_replay_admission(
    *,
    checkpoint_path: Path,
    shadow_corpus_npz: Path,
    metadata_csv: Path,
    residual_heads: tuple[Path, ...],
    alpha: float,
    surface_configs: tuple[SurfaceConfig, ...],
    max_source_holdout_rows: int,
    max_continuation_steps: int,
    max_first_action_l2: float,
    min_wrong_risk_improvement: float,
    max_normal_margin_regression: float,
    device: str,
    run_dir: Path,
    batch_size: int = 4096,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    arrays = load_sequence_corpus_npz(shadow_corpus_npz)
    contract = validate_sequence_corpus_contract(arrays)
    metadata = load_metadata_csv(metadata_csv, expected_rows=contract.rows)
    validate_metadata_alignment(arrays, metadata)
    replay_source = select_replay_rows(metadata, max_source_holdout_rows=max_source_holdout_rows)
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
    features_normal, features_variant = build_feature_views(normal_outputs, variant_outputs, (VALID_VIEW,))[VALID_VIEW]
    surface_config_map = {config.surface: config.env_config_path for config in surface_configs}
    replay_rows: list[dict[str, Any]] = []
    skipped_rows: list[dict[str, Any]] = []
    rows_reconstructable = 0

    heads: list[tuple[Path, GatedResponseAmplifierHead, dict[str, Any], np.ndarray, np.ndarray]] = []
    for head_path in residual_heads:
        head, payload = load_residual_head(head_path, resolved_device)
        if int(payload.get("max_sequence_length", arrays["sequence_mask"].shape[1])) != int(arrays["sequence_mask"].shape[1]):
            raise ValueError(f"head {head_path} sequence length does not match corpus")
        pred_normal, _raw_normal, _gate_normal = _predict_with_aux(head, features_normal, resolved_device)
        pred_wrong, _raw_wrong, _gate_wrong = _predict_with_aux(head, features_variant, resolved_device)
        heads.append((head_path, head, payload, pred_normal, pred_wrong))

    response_dim = response_feature_dim_for_model(model)
    for surface, group in replay_source.groupby("surface", observed=True):
        surface_name = str(surface)
        if surface_name not in surface_config_map:
            for _, row in group.iterrows():
                skipped_rows.append(
                    {
                        "row_index": int(row["row_index"]),
                        "surface": surface_name,
                        "skip_reason": "missing_surface_config",
                    }
                )
            continue
        env_config = load_env_config(surface_config_map[surface_name])
        snapshots = collect_requested_outcome_snapshots(
            model=model,
            env_config=env_config,
            requests=_requested_steps(group),
            device=resolved_device,
        )
        for _, row in group.iterrows():
            row_index = int(row["row_index"])
            left = _snapshot(snapshots, int(row["left_seed"]), int(row["left_step"]))
            right = _snapshot(snapshots, int(row["right_seed"]), int(row["right_step"]))
            if left is None or right is None:
                skipped_rows.append(
                    {
                        "row_index": row_index,
                        "surface": surface_name,
                        "skip_reason": "missing_reconstructed_snapshot",
                    }
                )
                continue
            rows_reconstructable += 1
            normal_hidden = torch.as_tensor(arrays["normal_hidden"][row_index], dtype=torch.float32, device=resolved_device).reshape(1, -1)
            variant_hidden = torch.as_tensor(arrays["variant_hidden"][row_index], dtype=torch.float32, device=resolved_device).reshape(1, -1)
            normal_snapshot = _with_hidden(left, normal_hidden)
            wrong_snapshot = _with_hidden(left, variant_hidden)
            base_normal_action = _first_action(model, normal_snapshot.observation, normal_snapshot.hidden, resolved_device)
            base_wrong_action = _first_action(model, wrong_snapshot.observation, wrong_snapshot.hidden, resolved_device)
            base_normal = _rollout_first_action_override(
                model=model,
                snapshot=normal_snapshot,
                first_action=base_normal_action,
                max_continuation_steps=max_continuation_steps,
                device=resolved_device,
            )
            base_wrong = _rollout_first_action_override(
                model=model,
                snapshot=wrong_snapshot,
                first_action=base_wrong_action,
                max_continuation_steps=max_continuation_steps,
                device=resolved_device,
            )
            for head_path, _head, payload, pred_normal, pred_wrong in heads:
                head_seed = int(payload.get("seed", -1))
                residual_normal = np.asarray(pred_normal[row_index, 0, :], dtype=np.float32) * float(alpha)
                residual_wrong = np.asarray(pred_wrong[row_index, 0, :], dtype=np.float32) * float(alpha)
                corrected_normal_action = np.clip(base_normal_action + residual_normal, -1.0, 1.0).astype(np.float32)
                corrected_wrong_action = np.clip(base_wrong_action + residual_wrong, -1.0, 1.0).astype(np.float32)
                normal_result = _rollout_first_action_override(
                    model=model,
                    snapshot=normal_snapshot,
                    first_action=corrected_normal_action,
                    max_continuation_steps=max_continuation_steps,
                    device=resolved_device,
                )
                wrong_result = _rollout_first_action_override(
                    model=model,
                    snapshot=wrong_snapshot,
                    first_action=corrected_wrong_action,
                    max_continuation_steps=max_continuation_steps,
                    device=resolved_device,
                )
                base_normal_margin = _margin(base_normal)
                corrected_normal_margin = _margin(normal_result)
                base_wrong_margin = _margin(base_wrong)
                corrected_wrong_margin = _margin(wrong_result)
                normal_regression = (
                    base_normal_margin - corrected_normal_margin
                    if np.isfinite(base_normal_margin) and np.isfinite(corrected_normal_margin)
                    else float("nan")
                )
                wrong_improvement = (
                    corrected_wrong_margin - base_wrong_margin
                    if np.isfinite(base_wrong_margin) and np.isfinite(corrected_wrong_margin)
                    else float("nan")
                )
                base_wrong_risk = risk_score(base_wrong)
                corrected_wrong_risk = risk_score(wrong_result)
                replay_rows.append(
                    {
                        "row_index": row_index,
                        "source_index": int(row["source_index"]),
                        "physical_pair_key": str(row["physical_pair_key"]),
                        "surface": surface_name,
                        "target": str(row["target"]),
                        "variant": str(row["variant"]),
                        "split": str(row["split"]),
                        "left_seed": int(row["left_seed"]),
                        "right_seed": int(row["right_seed"]),
                        "left_step": int(row["left_step"]),
                        "right_step": int(row["right_step"]),
                        "sequence_length": int(row["sequence_length"]),
                        "head_seed": head_seed,
                        "head_path": str(head_path),
                        "alpha": float(alpha),
                        "base_normal_steer": float(base_normal_action[0]),
                        "base_normal_throttle": float(base_normal_action[1]),
                        "base_normal_brake": float(base_normal_action[2]),
                        "residual_normal_steer": float(residual_normal[0]),
                        "residual_normal_throttle": float(residual_normal[1]),
                        "residual_normal_brake": float(residual_normal[2]),
                        "corrected_normal_steer": float(corrected_normal_action[0]),
                        "corrected_normal_throttle": float(corrected_normal_action[1]),
                        "corrected_normal_brake": float(corrected_normal_action[2]),
                        "base_wrong_steer": float(base_wrong_action[0]),
                        "base_wrong_throttle": float(base_wrong_action[1]),
                        "base_wrong_brake": float(base_wrong_action[2]),
                        "residual_wrong_steer": float(residual_wrong[0]),
                        "residual_wrong_throttle": float(residual_wrong[1]),
                        "residual_wrong_brake": float(residual_wrong[2]),
                        "corrected_wrong_steer": float(corrected_wrong_action[0]),
                        "corrected_wrong_throttle": float(corrected_wrong_action[1]),
                        "corrected_wrong_brake": float(corrected_wrong_action[2]),
                        "normal_first_action_l2": float(
                            np.linalg.norm(corrected_normal_action.astype(np.float64) - base_normal_action.astype(np.float64))
                        ),
                        "wrong_first_action_l2": float(
                            np.linalg.norm(corrected_wrong_action.astype(np.float64) - base_wrong_action.astype(np.float64))
                        ),
                        "normal_margin_regression": float(normal_regression),
                        "wrong_margin_improvement": float(wrong_improvement),
                        "wrong_risk_improvement": float(base_wrong_risk - corrected_wrong_risk),
                        "wrong_success_improved": bool(
                            (not bool(base_wrong.get("success", False))) and bool(wrong_result.get("success", False))
                        ),
                        "wrong_collision_reduced": bool(
                            bool(base_wrong.get("collision", False)) and not bool(wrong_result.get("collision", False))
                        ),
                        **_result_prefix("base_normal", base_normal),
                        **_result_prefix("corrected_normal", normal_result),
                        **_result_prefix("base_wrong", base_wrong),
                        **_result_prefix("corrected_wrong", wrong_result),
                    }
                )

    split_rows, aggregate = summarize_replay_rows(
        replay_rows,
        max_first_action_l2=max_first_action_l2,
        min_wrong_risk_improvement=min_wrong_risk_improvement,
        max_normal_margin_regression=max_normal_margin_regression,
    )
    seed_rows = []
    if replay_rows:
        frame = pd.DataFrame(replay_rows)
        for head_seed, group in frame.groupby("head_seed", observed=True):
            _split, head_summary = summarize_replay_rows(
                group.to_dict("records"),
                max_first_action_l2=max_first_action_l2,
                min_wrong_risk_improvement=min_wrong_risk_improvement,
                max_normal_margin_regression=max_normal_margin_regression,
            )
            seed_rows.append({"head_seed": int(head_seed), "rows": int(len(group)), **head_summary})
    after_checksum = model_parameter_checksum(model)
    summary = _summary_contract(
        before_checksum=before_checksum,
        after_checksum=after_checksum,
        run_dir=run_dir,
        replay_rows=replay_rows,
        split_rows=split_rows,
        aggregate=aggregate,
        rows_attempted=int(len(replay_source)),
        rows_reconstructable=rows_reconstructable,
        source_holdout_rows=int((replay_source["split"].astype(str) == "source_holdout_validation").sum()) if not replay_source.empty else 0,
        residual_head_count=len(heads),
        selected_alpha=alpha,
        checkpoint_path=checkpoint_path,
        shadow_corpus_npz=shadow_corpus_npz,
        metadata_csv=metadata_csv,
    )
    write_csv_rows(run_dir / "replay_rows.csv", replay_rows)
    write_csv_rows(run_dir / "seed_summary.csv", seed_rows)
    write_csv_rows(run_dir / "split_summary.csv", split_rows)
    write_csv_rows(run_dir / "skipped_rows.csv", skipped_rows)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run M692 gate-margin residual closed-loop replay admission.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--shadow-corpus", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--residual-head", action="append", type=Path, required=True)
    parser.add_argument("--alpha", type=float, default=1.0)
    parser.add_argument("--surface-config", action="append", type=parse_surface_config, required=True)
    parser.add_argument("--max-source-heldout-rows", type=int, default=120)
    parser.add_argument("--max-continuation-steps", type=int, default=40)
    parser.add_argument("--max-first-action-l2", type=float, default=0.006)
    parser.add_argument("--min-wrong-risk-improvement", type=float, default=0.01)
    parser.add_argument("--max-normal-margin-regression", type=float, default=0.005)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--batch-size", type=int, default=4096)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="gate_margin_replay_admission")
    summary = run_gate_margin_replay_admission(
        checkpoint_path=args.checkpoint,
        shadow_corpus_npz=args.shadow_corpus,
        metadata_csv=args.metadata,
        residual_heads=tuple(args.residual_head),
        alpha=args.alpha,
        surface_configs=tuple(args.surface_config),
        max_source_holdout_rows=args.max_source_heldout_rows,
        max_continuation_steps=args.max_continuation_steps,
        max_first_action_l2=args.max_first_action_l2,
        min_wrong_risk_improvement=args.min_wrong_risk_improvement,
        max_normal_margin_regression=args.max_normal_margin_regression,
        device=args.device,
        run_dir=run_dir,
        batch_size=args.batch_size,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
