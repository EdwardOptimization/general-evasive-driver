"""Build and evaluate rejected-history preference objective corpora."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec, parse_checkpoint_spec
from autodrift.intervention_objectives import (
    load_rejected_history_preference_snippets,
    rejected_history_preference_components,
    weighted_mean,
)
from autodrift.train_ppo import resolve_device


ACTION_COLUMNS = ("steer", "throttle", "brake")
REQUIRED_CORPUS_FIELDS = (
    "observation",
    "preferred_hidden",
    "rejected_hidden",
    "preferred_action",
    "weight",
    "preferred_score",
    "rejected_score",
    "score_delta",
    "group_index",
    "target_index",
)


@dataclass(frozen=True)
class PreferenceLossConfig:
    preferred_logprob_margin: float = 0.05
    wrong_logprob_margin: float = 0.05
    wrong_preference_coef: float = 1.0


def parse_int_set(raw: str) -> set[int]:
    return {int(part.strip()) for part in str(raw).split(",") if part.strip()}


def _score(success: bool, margin: float) -> float:
    return (1.0 if bool(success) else 0.0) + float(margin)


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def _load_source_npz(path: Path) -> dict[str, np.ndarray]:
    data = np.load(path)
    missing = [field for field in REQUIRED_CORPUS_FIELDS if field not in data.files]
    if missing:
        raise ValueError(f"source corpus npz missing fields: {missing}")
    return {field: np.asarray(data[field]) for field in data.files}


def _action_array(frame: pd.DataFrame, prefix: str) -> np.ndarray:
    return frame[[f"{prefix}_first_{name}" for name in ACTION_COLUMNS]].to_numpy(dtype=np.float32)


def _row_weights(
    base_weight: np.ndarray,
    wrong_margin: np.ndarray,
    row_id: np.ndarray,
    *,
    failed_rows: set[int],
    recovered_rows: set[int],
    failed_row_bonus: float,
    recovered_row_bonus: float,
    max_weight: float,
) -> np.ndarray:
    bonus = np.ones_like(base_weight, dtype=np.float32)
    for index, row in enumerate(row_id.astype(int).tolist()):
        if row in failed_rows:
            bonus[index] *= float(failed_row_bonus)
        elif row in recovered_rows:
            bonus[index] *= float(recovered_row_bonus)
    near_zero = np.clip(0.001 / np.maximum(np.abs(wrong_margin.astype(np.float32)), 1e-6), 1.0, 4.0)
    return np.clip(base_weight.astype(np.float32) * bonus * near_zero, 0.0, float(max_weight)).astype(np.float32)


def build_preference_corpus(
    *,
    source_npz: Path,
    source_csv: Path,
    base_replay_csv: Path,
    base_policy: str,
    failed_rows: set[int],
    recovered_rows: set[int],
    failed_row_bonus: float,
    recovered_row_bonus: float,
    max_weight: float,
    output_npz: Path,
    output_csv: Path,
) -> dict[str, Any]:
    source = _load_source_npz(source_npz)
    source_frame = pd.read_csv(source_csv).sort_values("row_id").reset_index(drop=True)
    replay = pd.read_csv(base_replay_csv)
    replay = replay[replay["policy"].astype(str) == str(base_policy)].sort_values("row_id").reset_index(drop=True)
    if source_frame.empty or replay.empty:
        raise ValueError("source corpus and base replay rows must be non-empty")
    rows = int(source["observation"].shape[0])
    if len(source_frame) != rows or len(replay) != rows:
        raise ValueError(
            f"row count mismatch: npz={rows} source_csv={len(source_frame)} base_replay_csv={len(replay)}"
        )
    row_id = source_frame["row_id"].to_numpy(dtype=np.int64)
    replay_row_id = replay["row_id"].to_numpy(dtype=np.int64)
    if not np.array_equal(row_id, replay_row_id):
        raise ValueError("source corpus rows and replay rows must have matching row_id order")

    normal_margin = replay["normal_margin"].to_numpy(dtype=np.float32)
    wrong_margin = replay["wrong_history_margin"].to_numpy(dtype=np.float32)
    normal_success = np.asarray([_bool(value) for value in replay["normal_success"].tolist()], dtype=bool)
    wrong_success = np.asarray([_bool(value) for value in replay["wrong_history_success"].tolist()], dtype=bool)
    preferred_score = np.asarray(
        [_score(success, margin) for success, margin in zip(normal_success, normal_margin)],
        dtype=np.float32,
    )
    rejected_score = np.asarray(
        [_score(success, margin) for success, margin in zip(wrong_success, wrong_margin)],
        dtype=np.float32,
    )
    weight = _row_weights(
        np.asarray(source["weight"], dtype=np.float32),
        wrong_margin,
        row_id,
        failed_rows=failed_rows,
        recovered_rows=recovered_rows,
        failed_row_bonus=failed_row_bonus,
        recovered_row_bonus=recovered_row_bonus,
        max_weight=max_weight,
    )
    arrays = {
        "observation": np.asarray(source["observation"], dtype=np.float32),
        "preferred_hidden": np.asarray(source["preferred_hidden"], dtype=np.float32),
        "rejected_hidden": np.asarray(source["rejected_hidden"], dtype=np.float32),
        "preferred_action": _action_array(replay, "normal"),
        "rejected_action": _action_array(replay, "wrong_history"),
        "preferred_score": preferred_score,
        "rejected_score": rejected_score,
        "score_delta": (preferred_score - rejected_score).astype(np.float32),
        "normal_margin": normal_margin,
        "wrong_history_margin": wrong_margin,
        "margin_floor": np.minimum(wrong_margin, -1e-6).astype(np.float32),
        "weight": weight,
        "row_id": row_id,
        "group_index": np.asarray(source["group_index"], dtype=np.int64),
        "target_index": np.asarray(source["target_index"], dtype=np.int64),
    }
    output_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez(output_npz, **arrays)
    metadata_rows = []
    for index, row in source_frame.iterrows():
        metadata_rows.append(
            {
                "row_id": int(row["row_id"]),
                "physical_pair_key": str(row["physical_pair_key"]),
                "target": str(row["target"]),
                "left_seed": int(row["left_seed"]),
                "right_seed": int(row["right_seed"]),
                "left_step": int(row["left_step"]),
                "right_step": int(row["right_step"]),
                "relocated_obstacle_body_x": float(row["relocated_obstacle_body_x"]),
                "relocated_obstacle_body_y": float(row["relocated_obstacle_body_y"]),
                "relocated_obstacle_half_width": float(row["relocated_obstacle_half_width"]),
                "base_wrong_history_terminal_reason": str(replay.loc[index, "wrong_history_terminal_reason"]),
                "normal_margin": float(normal_margin[index]),
                "wrong_history_margin": float(wrong_margin[index]),
                "weight": float(weight[index]),
            }
        )
    write_csv_rows(output_csv, metadata_rows)
    return {
        "rows": rows,
        "output_npz": str(output_npz),
        "output_csv": str(output_csv),
        "base_policy": str(base_policy),
        "failed_rows": sorted(int(row) for row in failed_rows),
        "recovered_rows": sorted(int(row) for row in recovered_rows),
        "weight_min": float(np.min(weight)),
        "weight_mean": float(np.mean(weight)),
        "weight_max": float(np.max(weight)),
    }


def evaluate_checkpoint(
    *,
    checkpoint: CheckpointSpec,
    corpus_npz: Path,
    device: str,
    loss_config: PreferenceLossConfig,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    data = np.load(corpus_npz)
    obs_dim = int(data["observation"].shape[1])
    act_dim = int(data["preferred_action"].shape[1])
    model, _ = load_actor_critic_checkpoint(checkpoint.path, device=device, obs_dim=obs_dim)
    snippets = load_rejected_history_preference_snippets(
        corpus_npz,
        device=next(model.parameters()).device,
        obs_dim=obs_dim,
        hidden_size=int(model.actor_mean.in_features),
        act_dim=act_dim,
    )
    indices = torch.arange(snippets.size, device=snippets.observation.device)
    with torch.no_grad():
        components = rejected_history_preference_components(
            model,
            snippets,
            indices,
            preferred_logprob_margin=loss_config.preferred_logprob_margin,
            wrong_logprob_margin=loss_config.wrong_logprob_margin,
            wrong_preference_coef=loss_config.wrong_preference_coef,
        )
        weighted_loss = weighted_mean(components["combined"], snippets.weight.detach())
    weights = snippets.weight.detach().cpu().numpy()
    combined = components["combined"].detach().cpu().numpy()
    preferred_sep = components["preferred_separation"].detach().cpu().numpy()
    wrong_pref = components["wrong_preference"].detach().cpu().numpy()
    logp_cp = components["logp_correct_preferred"].detach().cpu().numpy()
    logp_wp = components["logp_wrong_preferred"].detach().cpu().numpy()
    logp_wr = components["logp_wrong_rejected"].detach().cpu().numpy()
    row_ids = snippets.row_id.detach().cpu().numpy()
    per_row = []
    for index, row_id in enumerate(row_ids.astype(int).tolist()):
        per_row.append(
            {
                "policy": checkpoint.label,
                "row_id": int(row_id),
                "weight": float(weights[index]),
                "combined_loss": float(combined[index]),
                "preferred_separation": float(preferred_sep[index]),
                "wrong_preference": float(wrong_pref[index]),
                "logp_correct_preferred": float(logp_cp[index]),
                "logp_wrong_preferred": float(logp_wp[index]),
                "logp_wrong_rejected": float(logp_wr[index]),
            }
        )
    summary = {
        "policy": checkpoint.label,
        "checkpoint": str(checkpoint.path),
        "rows": int(snippets.size),
        "weighted_loss": float(weighted_loss.detach().cpu().item()),
        "combined_loss_mean": float(np.mean(combined)),
        "preferred_separation_mean": float(np.mean(preferred_sep)),
        "wrong_preference_mean": float(np.mean(wrong_pref)),
        "weight_mean": float(np.mean(weights)),
    }
    return summary, per_row


def run_objective_sanity(
    *,
    checkpoint_policies: list[CheckpointSpec],
    source_npz: Path,
    source_csv: Path,
    base_replay_csv: Path,
    base_policy: str,
    failed_rows: set[int],
    recovered_rows: set[int],
    failed_row_bonus: float,
    recovered_row_bonus: float,
    max_weight: float,
    device: str,
    loss_config: PreferenceLossConfig,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    corpus_npz = run_dir / "rejected_history_preference_corpus.npz"
    corpus_csv = run_dir / "rejected_history_preference_corpus.csv"
    corpus_summary = build_preference_corpus(
        source_npz=source_npz,
        source_csv=source_csv,
        base_replay_csv=base_replay_csv,
        base_policy=base_policy,
        failed_rows=failed_rows,
        recovered_rows=recovered_rows,
        failed_row_bonus=failed_row_bonus,
        recovered_row_bonus=recovered_row_bonus,
        max_weight=max_weight,
        output_npz=corpus_npz,
        output_csv=corpus_csv,
    )
    resolved_device = str(resolve_device(device))
    policy_rows: list[dict[str, Any]] = []
    per_row: list[dict[str, Any]] = []
    for spec in checkpoint_policies:
        summary, rows = evaluate_checkpoint(
            checkpoint=spec,
            corpus_npz=corpus_npz,
            device=resolved_device,
            loss_config=loss_config,
        )
        policy_rows.append(summary)
        per_row.extend(rows)
    write_csv_rows(run_dir / "policy_summary.csv", policy_rows)
    write_csv_rows(run_dir / "per_row_losses.csv", per_row)

    losses = {row["policy"]: float(row["weighted_loss"]) for row in policy_rows}
    base_loss = losses.get(base_policy)
    ranks_m290_ahead = None
    if base_loss is not None:
        ranks_m290_ahead = all(base_loss < value for label, value in losses.items() if label != base_policy)
    focused_rows = [row for row in per_row if int(row["row_id"]) in {6, 11, 15, 16}]
    write_csv_rows(run_dir / "focused_row_losses.csv", focused_rows)
    summary = {
        "run_type": "rejected_history_preference_objective_sanity",
        "checkpoint_policies": [asdict(spec) for spec in checkpoint_policies],
        "corpus_summary": corpus_summary,
        "device": resolved_device,
        "loss_config": asdict(loss_config),
        "policy_summary_csv": run_dir / "policy_summary.csv",
        "per_row_losses_csv": run_dir / "per_row_losses.csv",
        "focused_row_losses_csv": run_dir / "focused_row_losses.csv",
        "losses": losses,
        "base_policy": base_policy,
        "base_loss_lower_than_candidates": bool(ranks_m290_ahead) if ranks_m290_ahead is not None else None,
        "ppo_or_actor_update_run": False,
        "actor_inputs_changed": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint-policy", type=parse_checkpoint_spec, action="append", required=True)
    parser.add_argument("--source-npz", type=Path, required=True)
    parser.add_argument("--source-csv", type=Path, required=True)
    parser.add_argument("--base-replay-csv", type=Path, required=True)
    parser.add_argument("--base-policy", default="m290x64_a500")
    parser.add_argument("--failed-row-ids", type=parse_int_set, default={6, 15, 16})
    parser.add_argument("--recovered-row-ids", type=parse_int_set, default={11})
    parser.add_argument("--failed-row-bonus", type=float, default=4.0)
    parser.add_argument("--recovered-row-bonus", type=float, default=2.0)
    parser.add_argument("--max-weight", type=float, default=100.0)
    parser.add_argument("--preferred-logprob-margin", type=float, default=0.05)
    parser.add_argument("--wrong-logprob-margin", type=float, default=0.05)
    parser.add_argument("--wrong-preference-coef", type=float, default=1.0)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()

    summary = run_objective_sanity(
        checkpoint_policies=args.checkpoint_policy,
        source_npz=args.source_npz,
        source_csv=args.source_csv,
        base_replay_csv=args.base_replay_csv,
        base_policy=args.base_policy,
        failed_rows=set(args.failed_row_ids),
        recovered_rows=set(args.recovered_row_ids),
        failed_row_bonus=args.failed_row_bonus,
        recovered_row_bonus=args.recovered_row_bonus,
        max_weight=args.max_weight,
        device=args.device,
        loss_config=PreferenceLossConfig(
            preferred_logprob_margin=args.preferred_logprob_margin,
            wrong_logprob_margin=args.wrong_logprob_margin,
            wrong_preference_coef=args.wrong_preference_coef,
        ),
        run_dir=args.run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
