"""Export rejected-history trajectory anchors for current-family proof rows."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.boundary_outcome_replay_gate import REQUIRED_CORPUS_COLUMNS, validate_corpus_frame
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec, parse_checkpoint_spec
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.intervention_objectives import load_trajectory_action_anchor
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.matched_history_outcome_gate import OutcomeSnapshot, collect_requested_outcome_snapshots
from autodrift.train_ppo import resolve_device
from autodrift.wrong_history_boundary_relocation_surface import relocate_outcome_snapshot


def parse_int_list(raw: str) -> tuple[int, ...]:
    values = tuple(int(part.strip()) for part in str(raw).split(",") if part.strip())
    if not values:
        raise argparse.ArgumentTypeError("integer list must contain at least one value")
    return values


def _requests(frame: pd.DataFrame) -> dict[int, set[int]]:
    requests: dict[int, set[int]] = {}
    for _, row in frame.iterrows():
        requests.setdefault(int(row["left_seed"]), set()).add(int(row["left_step"]))
        requests.setdefault(int(row["right_seed"]), set()).add(int(row["right_step"]))
    return requests


def _snapshot(snapshots: dict[tuple[int, int], OutcomeSnapshot], seed: int, step: int) -> OutcomeSnapshot:
    key = (int(seed), int(step))
    if key not in snapshots:
        raise ValueError(f"missing reconstructed snapshot seed={seed} step={step}")
    return snapshots[key]


def select_corpus_rows(
    frame: pd.DataFrame,
    *,
    required_row_ids: tuple[int, ...],
    max_rows: int,
) -> pd.DataFrame:
    validate_corpus_frame(frame)
    selected = frame.sort_values(["row_id"]).reset_index(drop=True)
    required = {int(row_id) for row_id in required_row_ids}
    present = {int(row_id) for row_id in selected["row_id"].astype(int).tolist()}
    missing = sorted(required.difference(present))
    if missing:
        raise ValueError(f"required row ids are missing from corpus: {missing}")
    if max_rows > 0:
        selected = selected.head(int(max_rows)).reset_index(drop=True)
        present_after_limit = {int(row_id) for row_id in selected["row_id"].astype(int).tolist()}
        missing_after_limit = sorted(required.difference(present_after_limit))
        if missing_after_limit:
            raise ValueError(f"max_rows omitted required row ids: {missing_after_limit}")
    if selected.empty:
        raise ValueError("no corpus rows selected")
    return selected


def _record_rejected_trajectory(
    *,
    model: torch.nn.Module,
    snapshot: OutcomeSnapshot,
    rejected_hidden: torch.Tensor,
    max_continuation_steps: int,
    device: torch.device,
) -> tuple[list[np.ndarray], list[np.ndarray], list[np.ndarray]]:
    obs = snapshot.observation.copy()
    hidden = rejected_hidden.detach().clone()
    env = snapshot.env
    observations: list[np.ndarray] = []
    hidden_states: list[np.ndarray] = []
    actions: list[np.ndarray] = []
    terminated = False
    truncated = False
    for _ in range(max(1, int(max_continuation_steps))):
        observations.append(np.asarray(obs, dtype=np.float32).copy())
        hidden_states.append(hidden.detach().cpu().numpy().reshape(-1).astype(np.float32))
        action, next_hidden = deterministic_action_from_hidden(
            model,
            np.asarray(obs, dtype=np.float32),
            hidden,
            device,
        )
        actions.append(np.asarray(action, dtype=np.float32).copy())
        obs, _, terminated, truncated, _ = env.step(action)
        hidden = next_hidden
        if terminated or truncated:
            break
    return observations, hidden_states, actions


def _save_anchor(
    path: Path,
    *,
    observation: np.ndarray,
    hidden: np.ndarray,
    reference_action: np.ndarray,
    source_index: np.ndarray,
    step_index: np.ndarray,
    weight: np.ndarray,
) -> None:
    if int(observation.shape[0]) < 1:
        raise ValueError("cannot save an empty trajectory anchor")
    np.savez(
        path,
        observation=np.asarray(observation, dtype=np.float32),
        hidden=np.asarray(hidden, dtype=np.float32),
        reference_action=np.asarray(reference_action, dtype=np.float32),
        source_index=np.asarray(source_index, dtype=np.int64),
        step_index=np.asarray(step_index, dtype=np.int64),
        weight=np.asarray(weight, dtype=np.float32),
    )


def _repeat_rows(array: np.ndarray, repeat: int) -> np.ndarray:
    return np.repeat(array, max(1, int(repeat)), axis=0)


def _combine_anchors(
    *,
    base_anchor_npz: Path,
    rejected_anchor_npz: Path,
    output_npz: Path,
    rejected_repeat: int,
    rejected_source_index_offset: int,
) -> dict[str, Any]:
    base = np.load(base_anchor_npz)
    rejected = np.load(rejected_anchor_npz)
    arrays: dict[str, np.ndarray] = {}
    for field in ("observation", "hidden", "reference_action"):
        arrays[field] = np.concatenate(
            [
                np.asarray(base[field], dtype=np.float32),
                _repeat_rows(np.asarray(rejected[field], dtype=np.float32), rejected_repeat),
            ],
            axis=0,
        ).astype(np.float32)
    for field in ("source_index", "step_index"):
        rejected_values = np.asarray(rejected[field], dtype=np.int64)
        if field == "source_index":
            rejected_values = rejected_values + int(rejected_source_index_offset)
        arrays[field] = np.concatenate(
            [
                np.asarray(base[field], dtype=np.int64),
                _repeat_rows(rejected_values, rejected_repeat),
            ],
            axis=0,
        ).astype(np.int64)
    arrays["weight"] = np.concatenate(
        [
            np.asarray(base["weight"], dtype=np.float32),
            _repeat_rows(np.asarray(rejected["weight"], dtype=np.float32), rejected_repeat),
        ],
        axis=0,
    ).astype(np.float32)
    _save_anchor(output_npz, **arrays)
    return {
        "base_rows": int(np.asarray(base["observation"]).shape[0]),
        "rejected_rows": int(np.asarray(rejected["observation"]).shape[0]),
        "rejected_repeat": int(rejected_repeat),
        "combined_rows": int(arrays["observation"].shape[0]),
        "rejected_source_index_offset": int(rejected_source_index_offset),
    }


def export_rejected_history_trajectory_anchor(
    *,
    checkpoint_spec: CheckpointSpec,
    corpus_csv: Path,
    base_combined_anchor_npz: Path,
    env_config_path: Path,
    required_row_ids: tuple[int, ...],
    max_rows: int,
    max_continuation_steps: int,
    rejected_weight: float,
    failed_row_weight: float,
    rejected_repeat: int,
    rejected_source_index_offset: int,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    env_config = load_env_config(env_config_path)
    model, _ = load_actor_critic_checkpoint(checkpoint_spec.path, device=str(resolved_device))
    model.eval()
    response_feature_dim_for_model(model)
    corpus = select_corpus_rows(
        pd.read_csv(corpus_csv),
        required_row_ids=required_row_ids,
        max_rows=max_rows,
    )
    snapshots = collect_requested_outcome_snapshots(
        model=model,
        env_config=env_config,
        requests=_requests(corpus),
        device=resolved_device,
    )

    observations: list[np.ndarray] = []
    hidden_states: list[np.ndarray] = []
    reference_actions: list[np.ndarray] = []
    source_indices: list[int] = []
    step_indices: list[int] = []
    weights: list[float] = []
    trajectory_rows: list[dict[str, Any]] = []
    required_set = {int(row_id) for row_id in required_row_ids}

    for source_index, row in corpus.reset_index(drop=True).iterrows():
        left = _snapshot(snapshots, int(row["left_seed"]), int(row["left_step"]))
        right = _snapshot(snapshots, int(row["right_seed"]), int(row["right_step"]))
        relocated = relocate_outcome_snapshot(
            left,
            body_longitudinal=float(row["relocated_obstacle_body_x"]),
            body_lateral=float(row["relocated_obstacle_body_y"]),
            half_width=float(row["relocated_obstacle_half_width"]),
        )
        obs_seq, hidden_seq, action_seq = _record_rejected_trajectory(
            model=model,
            snapshot=relocated,
            rejected_hidden=right.hidden,
            max_continuation_steps=max_continuation_steps,
            device=resolved_device,
        )
        row_weight = float(failed_row_weight) if int(row["row_id"]) in required_set else float(rejected_weight)
        for step_index, (obs, hidden, action) in enumerate(zip(obs_seq, hidden_seq, action_seq)):
            observations.append(obs)
            hidden_states.append(hidden)
            reference_actions.append(action)
            source_indices.append(int(source_index))
            step_indices.append(int(step_index))
            weights.append(row_weight)
            trajectory_rows.append(
                {
                    "row_id": int(row["row_id"]),
                    "source_index": int(source_index),
                    "step_index": int(step_index),
                    "weight": row_weight,
                    "target": str(row["target"]),
                    "physical_pair_key": str(row["physical_pair_key"]),
                    "left_seed": int(row["left_seed"]),
                    "right_seed": int(row["right_seed"]),
                    "left_step": int(row["left_step"]),
                    "right_step": int(row["right_step"]),
                    "reference_steer": float(action[0]),
                    "reference_throttle": float(action[1]),
                    "reference_brake": float(action[2]),
                }
            )

    rejected_npz = run_dir / "rejected_trajectory_anchor.npz"
    rejected_arrays = {
        "observation": np.asarray(observations, dtype=np.float32),
        "hidden": np.asarray(hidden_states, dtype=np.float32),
        "reference_action": np.asarray(reference_actions, dtype=np.float32),
        "source_index": np.asarray(source_indices, dtype=np.int64),
        "step_index": np.asarray(step_indices, dtype=np.int64),
        "weight": np.asarray(weights, dtype=np.float32),
    }
    _save_anchor(rejected_npz, **rejected_arrays)
    write_csv_rows(run_dir / "rejected_trajectory_anchor.csv", trajectory_rows)
    rejected_anchor = load_trajectory_action_anchor(
        rejected_npz,
        device=resolved_device,
        obs_dim=int(model.obs_dim),
        hidden_size=int(model.actor_mean.in_features),
        act_dim=int(model.act_dim),
    )

    combined_npz = run_dir / "combined_recovery_rejected_anchor.npz"
    combined_summary = _combine_anchors(
        base_anchor_npz=base_combined_anchor_npz,
        rejected_anchor_npz=rejected_npz,
        output_npz=combined_npz,
        rejected_repeat=rejected_repeat,
        rejected_source_index_offset=rejected_source_index_offset,
    )
    combined_anchor = load_trajectory_action_anchor(
        combined_npz,
        device=resolved_device,
        obs_dim=int(model.obs_dim),
        hidden_size=int(model.actor_mean.in_features),
        act_dim=int(model.act_dim),
    )

    rows_per_source = pd.DataFrame(trajectory_rows).groupby("row_id").size().to_dict()
    summary = {
        "run_type": "current_family_rejected_history_trajectory_anchor_export",
        "checkpoint": asdict(checkpoint_spec),
        "corpus_csv": corpus_csv,
        "base_combined_anchor_npz": base_combined_anchor_npz,
        "env_config": env_config_path,
        "required_row_ids": required_row_ids,
        "max_rows": int(max_rows),
        "max_continuation_steps": int(max_continuation_steps),
        "rejected_weight": float(rejected_weight),
        "failed_row_weight": float(failed_row_weight),
        "rejected_repeat": int(rejected_repeat),
        "rejected_source_index_offset": int(rejected_source_index_offset),
        "rows_selected": int(len(corpus)),
        "required_rows_present": bool(required_set.issubset(set(corpus["row_id"].astype(int).tolist()))),
        "rejected_trajectory_rows": int(rejected_anchor.size),
        "rejected_anchor_npz": rejected_npz,
        "rejected_anchor_csv": run_dir / "rejected_trajectory_anchor.csv",
        "rejected_anchor_shape": {
            "observation": list(rejected_anchor.observation.shape),
            "hidden": list(rejected_anchor.hidden.shape),
            "reference_action": list(rejected_anchor.reference_action.shape),
        },
        "combined_anchor_npz": combined_npz,
        "combined_anchor_shape": {
            "rows": int(combined_anchor.size),
            "observation": list(combined_anchor.observation.shape),
            "hidden": list(combined_anchor.hidden.shape),
            "reference_action": list(combined_anchor.reference_action.shape),
        },
        "combined_summary": combined_summary,
        "rows_per_row_id": {str(int(key)): int(value) for key, value in rows_per_source.items()},
        "forbidden_shortcuts_used": False,
        "ppo_or_actor_update_run": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint-policy", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--corpus-csv", type=Path, required=True)
    parser.add_argument("--base-combined-anchor-npz", type=Path, required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--required-row-ids", type=parse_int_list, default=(4, 6, 11, 13, 15, 16))
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--rejected-weight", type=float, default=10.0)
    parser.add_argument("--failed-row-weight", type=float, default=50.0)
    parser.add_argument("--rejected-repeat", type=int, default=16)
    parser.add_argument("--rejected-source-index-offset", type=int, default=100000)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    summary = export_rejected_history_trajectory_anchor(
        checkpoint_spec=args.checkpoint_policy,
        corpus_csv=args.corpus_csv,
        base_combined_anchor_npz=args.base_combined_anchor_npz,
        env_config_path=args.env_config,
        required_row_ids=tuple(args.required_row_ids),
        max_rows=args.max_rows,
        max_continuation_steps=args.max_continuation_steps,
        rejected_weight=args.rejected_weight,
        failed_row_weight=args.failed_row_weight,
        rejected_repeat=args.rejected_repeat,
        rejected_source_index_offset=args.rejected_source_index_offset,
        device=args.device,
        run_dir=args.run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
