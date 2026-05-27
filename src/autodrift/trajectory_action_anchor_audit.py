"""Evaluate trajectory-action anchor MSE for one or more checkpoints."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec, parse_checkpoint_spec
from autodrift.intervention_objectives import load_trajectory_action_anchor, weighted_mean
from autodrift.train_ppo import resolve_device


def trajectory_anchor_mse(model: torch.nn.Module, anchor: Any) -> float:
    with torch.no_grad():
        dist, _, _ = model.forward_recurrent(anchor.observation, anchor.hidden)  # type: ignore[attr-defined]
        action = torch.tanh(dist.mean)
        error = torch.square(action - anchor.reference_action.detach()).mean(dim=-1)
        return float(weighted_mean(error, anchor.weight.detach()).detach().cpu().item())


def _family_rows(anchor_npz: Path, row_errors: np.ndarray, weights: np.ndarray) -> list[dict[str, Any]]:
    data = np.load(anchor_npz)
    if "family_id" not in data.files:
        return []
    family_ids = np.asarray(data["family_id"], dtype=np.int64)
    rows: list[dict[str, Any]] = []
    for family_id in sorted(set(family_ids.tolist())):
        mask = family_ids == int(family_id)
        family_weights = np.clip(weights[mask], 0.0, None)
        denom = float(family_weights.sum(dtype=np.float64))
        mse = float((row_errors[mask] * family_weights).sum(dtype=np.float64) / denom) if denom > 0.0 else float("nan")
        rows.append(
            {
                "family_id": int(family_id),
                "rows": int(mask.sum()),
                "weight_sum": denom,
                "mse": mse,
            }
        )
    return rows


def _row_errors(model: torch.nn.Module, anchor: Any) -> np.ndarray:
    with torch.no_grad():
        dist, _, _ = model.forward_recurrent(anchor.observation, anchor.hidden)  # type: ignore[attr-defined]
        action = torch.tanh(dist.mean)
        error = torch.square(action - anchor.reference_action.detach()).mean(dim=-1)
        return error.detach().cpu().numpy().astype(np.float64)


def audit_trajectory_action_anchor(
    *,
    checkpoints: tuple[CheckpointSpec, ...],
    anchor_npz: Path,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    rows: list[dict[str, Any]] = []
    family_rows: list[dict[str, Any]] = []
    for checkpoint in checkpoints:
        model, _ = load_actor_critic_checkpoint(checkpoint.path, device=str(resolved_device))
        model.eval()
        anchor = load_trajectory_action_anchor(
            anchor_npz,
            device=resolved_device,
            obs_dim=int(model.obs_dim),
            hidden_size=int(model.actor_mean.in_features),
            act_dim=int(model.act_dim),
        )
        row_errors = _row_errors(model, anchor)
        weights = anchor.weight.detach().cpu().numpy().astype(np.float64)
        mse = trajectory_anchor_mse(model, anchor)
        rows.append(
            {
                "checkpoint_label": checkpoint.label,
                "checkpoint": checkpoint.path,
                "anchor_npz": anchor_npz,
                "rows": int(anchor.size),
                "mse": mse,
                "weight_sum": float(np.clip(weights, 0.0, None).sum(dtype=np.float64)),
            }
        )
        for family_row in _family_rows(anchor_npz, row_errors, np.clip(weights, 0.0, None)):
            family_rows.append(
                {
                    "checkpoint_label": checkpoint.label,
                    "checkpoint": checkpoint.path,
                    "anchor_npz": anchor_npz,
                    **family_row,
                }
            )
    rows_csv = run_dir / "trajectory_anchor_mse.csv"
    family_csv = run_dir / "trajectory_anchor_family_mse.csv"
    write_csv_rows(rows_csv, rows)
    write_csv_rows(family_csv, family_rows)
    summary = {
        "run_type": "trajectory_action_anchor_audit",
        "anchor_npz": anchor_npz,
        "checkpoint_count": len(checkpoints),
        "rows": rows,
        "family_rows": family_rows,
        "rows_csv": rows_csv,
        "family_csv": family_csv,
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "replay_started": False,
        "promoted": False,
        "private_holdout_used": False,
        "summary_json": run_dir / "summary.json",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def parse_checkpoint_list(raw: str) -> tuple[CheckpointSpec, ...]:
    values = tuple(parse_checkpoint_spec(part.strip()) for part in str(raw).split(",") if part.strip())
    if not values:
        raise argparse.ArgumentTypeError("at least one checkpoint spec is required")
    return values


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoints", type=parse_checkpoint_list, required=True)
    parser.add_argument("--anchor-npz", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    summary = audit_trajectory_action_anchor(
        checkpoints=args.checkpoints,
        anchor_npz=args.anchor_npz,
        device=args.device,
        run_dir=args.run_dir,
    )
    print(f"checkpoint_count={summary['checkpoint_count']}")
    print(f"summary={summary['summary_json']}")


if __name__ == "__main__":
    main()
