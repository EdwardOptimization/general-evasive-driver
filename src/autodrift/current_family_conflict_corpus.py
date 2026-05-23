"""Export current-family wrong-history boundary conflict snippets."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.intervention_objectives import load_current_family_conflict_snippets
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.train_ppo import resolve_device


def parse_int_list(raw: str) -> tuple[int, ...]:
    values = tuple(int(part.strip()) for part in str(raw).split(",") if part.strip())
    if not values:
        raise argparse.ArgumentTypeError("row id list must contain at least one integer")
    return values


def conflict_row_weight(
    *,
    boundary_margin: float,
    source_weight: float,
    margin_floor: float,
    max_weight: float,
) -> float:
    """Weight near-zero wrong-history collision margins more strongly."""

    if not np.isfinite(boundary_margin):
        raise ValueError("boundary_margin must be finite")
    if not np.isfinite(source_weight):
        raise ValueError("source_weight must be finite")
    floor = max(float(margin_floor), 1.0e-9)
    denom = max(abs(float(boundary_margin)), 1.0e-9)
    scale = min(max(floor / denom, 1.0), float(max_weight))
    return float(max(float(source_weight), 0.0) * scale)


def _action_array(action: np.ndarray) -> np.ndarray:
    value = np.asarray(action, dtype=np.float32).reshape(-1)
    if value.shape != (3,):
        raise ValueError(f"action must have shape (3,), got {value.shape}")
    return np.clip(value, -1.0, 1.0).astype(np.float32)


def _margin_lookup(path: Path | None, *, policy: str) -> dict[int, float]:
    if path is None:
        return {}
    frame = pd.read_csv(path)
    required = {"policy", "row_id", "wrong_history_margin"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"margin replay CSV missing columns: {', '.join(missing)}")
    rows = frame[frame["policy"].astype(str).eq(policy)].copy()
    if rows.empty:
        raise ValueError(f"no replay rows found for policy {policy!r}")
    return {int(row["row_id"]): float(row["wrong_history_margin"]) for _, row in rows.iterrows()}


def _write_current_family_conflict_corpus(
    *,
    output_npz: Path,
    observations: list[np.ndarray],
    preferred_hidden: list[np.ndarray],
    rejected_hidden: list[np.ndarray],
    rows: list[dict[str, Any]],
) -> None:
    if not rows:
        raise ValueError("cannot write an empty current-family conflict corpus")
    np.savez_compressed(
        output_npz,
        observation=np.asarray(observations, dtype=np.float32),
        preferred_hidden=np.asarray(preferred_hidden, dtype=np.float32),
        rejected_hidden=np.asarray(rejected_hidden, dtype=np.float32),
        preferred_anchor_action=np.stack([row["preferred_anchor_action"] for row in rows]).astype(np.float32),
        rejected_boundary_action=np.stack([row["rejected_boundary_action"] for row in rows]).astype(np.float32),
        weight=np.asarray([row["weight"] for row in rows], dtype=np.float32),
        row_id=np.asarray([row["row_id"] for row in rows], dtype=np.int64),
        boundary_margin=np.asarray([row["boundary_margin"] for row in rows], dtype=np.float32),
    )


def export_current_family_conflict_corpus(
    *,
    checkpoint: Path,
    boundary_corpus_npz: Path,
    boundary_corpus_csv: Path,
    row_ids: tuple[int, ...],
    margin_replay_csv: Path | None,
    margin_policy: str,
    margin_floor: float,
    max_weight: float,
    run_dir: Path,
    device: str,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint, device=str(resolved_device))
    model.eval()

    data = np.load(boundary_corpus_npz)
    required = {"observation", "preferred_hidden", "rejected_hidden", "weight"}
    missing = sorted(required.difference(data.files))
    if missing:
        raise ValueError(f"boundary corpus npz missing fields: {', '.join(missing)}")
    frame = pd.read_csv(boundary_corpus_csv)
    if "row_id" not in frame.columns:
        raise ValueError("boundary corpus CSV missing row_id")
    margin_by_row = _margin_lookup(margin_replay_csv, policy=margin_policy)

    observations: list[np.ndarray] = []
    preferred_hiddens: list[np.ndarray] = []
    rejected_hiddens: list[np.ndarray] = []
    rows: list[dict[str, Any]] = []
    for row_id in row_ids:
        matches = frame.index[frame["row_id"].astype(int).eq(int(row_id))].tolist()
        if len(matches) != 1:
            raise ValueError(f"expected exactly one boundary corpus row for row_id={row_id}, got {len(matches)}")
        index = int(matches[0])
        observation = np.asarray(data["observation"][index], dtype=np.float32)
        preferred_hidden = np.asarray(data["preferred_hidden"][index], dtype=np.float32)
        rejected_hidden = np.asarray(data["rejected_hidden"][index], dtype=np.float32)
        preferred_action, _ = deterministic_action_from_hidden(
            model,
            observation,
            torch.as_tensor(preferred_hidden, dtype=torch.float32, device=resolved_device).unsqueeze(0),
            resolved_device,
        )
        rejected_action, _ = deterministic_action_from_hidden(
            model,
            observation,
            torch.as_tensor(rejected_hidden, dtype=torch.float32, device=resolved_device).unsqueeze(0),
            resolved_device,
        )
        source_weight = float(np.asarray(data["weight"], dtype=np.float32)[index])
        boundary_margin = float(margin_by_row.get(int(row_id), frame.loc[index, "wrong_history_margin"]))
        weight = conflict_row_weight(
            boundary_margin=boundary_margin,
            source_weight=source_weight,
            margin_floor=margin_floor,
            max_weight=max_weight,
        )
        source_row = frame.loc[index]
        row = {
            "row_id": int(row_id),
            "source_index": index,
            "target": str(source_row.get("target", "")),
            "physical_pair_key": str(source_row.get("physical_pair_key", "")),
            "left_step": int(source_row.get("left_step", -1)),
            "right_step": int(source_row.get("right_step", -1)),
            "source_weight": source_weight,
            "boundary_margin": boundary_margin,
            "weight": weight,
            "preferred_anchor_steer": float(preferred_action[0]),
            "preferred_anchor_throttle": float(preferred_action[1]),
            "preferred_anchor_brake": float(preferred_action[2]),
            "rejected_boundary_steer": float(rejected_action[0]),
            "rejected_boundary_throttle": float(rejected_action[1]),
            "rejected_boundary_brake": float(rejected_action[2]),
            "preferred_anchor_action": _action_array(preferred_action),
            "rejected_boundary_action": _action_array(rejected_action),
        }
        observations.append(observation.copy())
        preferred_hiddens.append(preferred_hidden.copy())
        rejected_hiddens.append(rejected_hidden.copy())
        rows.append(row)

    corpus_npz = run_dir / "current_family_conflict_corpus.npz"
    _write_current_family_conflict_corpus(
        output_npz=corpus_npz,
        observations=observations,
        preferred_hidden=preferred_hiddens,
        rejected_hidden=rejected_hiddens,
        rows=rows,
    )
    loaded = load_current_family_conflict_snippets(
        corpus_npz,
        device=resolved_device,
        obs_dim=int(model.obs_dim),
        hidden_size=int(model.actor_mean.in_features),
        act_dim=int(model.act_dim),
    )
    csv_rows = [
        {key: value for key, value in row.items() if key not in {"preferred_anchor_action", "rejected_boundary_action"}}
        for row in rows
    ]
    write_csv_rows(run_dir / "current_family_conflict_rows.csv", csv_rows)
    summary = {
        "run_type": "current_family_conflict_corpus",
        "checkpoint": checkpoint,
        "boundary_corpus_npz": boundary_corpus_npz,
        "boundary_corpus_csv": boundary_corpus_csv,
        "margin_replay_csv": margin_replay_csv,
        "margin_policy": margin_policy,
        "row_ids": row_ids,
        "rows": int(loaded.size),
        "margin_floor": float(margin_floor),
        "max_weight": float(max_weight),
        "weight_sum": float(sum(float(row["weight"]) for row in rows)),
        "boundary_margin_min": float(min(float(row["boundary_margin"]) for row in rows)),
        "boundary_margin_max": float(max(float(row["boundary_margin"]) for row in rows)),
        "current_family_conflict_corpus_npz": corpus_npz,
        "current_family_conflict_rows_csv": run_dir / "current_family_conflict_rows.csv",
        "contract": {
            "rows": int(loaded.size),
            "obs_dim": int(model.obs_dim),
            "hidden_dim": int(model.actor_mean.in_features),
            "act_dim": int(model.act_dim),
        },
        "actor_inputs_changed": False,
        "ppo_or_actor_update_run": False,
        "checkpoint_promoted": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--boundary-corpus-npz", type=Path, required=True)
    parser.add_argument("--boundary-corpus-csv", type=Path, required=True)
    parser.add_argument("--row-ids", type=parse_int_list, default=(15, 6))
    parser.add_argument("--margin-replay-csv", type=Path, default=None)
    parser.add_argument("--margin-policy", type=str, default="m385micro_a0_00075")
    parser.add_argument("--margin-floor", type=float, default=1.0e-4)
    parser.add_argument("--max-weight", type=float, default=20.0)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="current_family_conflict_corpus")
    summary = export_current_family_conflict_corpus(
        checkpoint=args.checkpoint,
        boundary_corpus_npz=args.boundary_corpus_npz,
        boundary_corpus_csv=args.boundary_corpus_csv,
        row_ids=args.row_ids,
        margin_replay_csv=args.margin_replay_csv,
        margin_policy=args.margin_policy,
        margin_floor=args.margin_floor,
        max_weight=args.max_weight,
        run_dir=run_dir,
        device=args.device,
    )
    print(f"rows={summary['rows']} weight_sum={summary['weight_sum']:.6f}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
