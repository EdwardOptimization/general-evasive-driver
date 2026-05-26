"""Export M183/M170 row16 normal-branch trajectory anchor for Candidate B."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.boundary_outcome_replay_gate import validate_corpus_frame
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.intervention_objectives import load_trajectory_action_anchor
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.matched_history_outcome_gate import (
    OutcomeSnapshot,
    collect_requested_outcome_snapshots,
    replay_outcome_variant,
)
from autodrift.train_ppo import resolve_device
from autodrift.wrong_history_boundary_relocation_surface import relocate_outcome_snapshot


DEFAULT_CHECKPOINT = Path(
    "runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt"
)
DEFAULT_CORPUS = Path("runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv")
DEFAULT_ENV_CONFIG = Path("configs/m121_human_view_zero_obstacle_relvel.json")
DEFAULT_RUN_DIR = Path("runs/m1034_candidate_b_m183_row16_active_set_anchor_export")


def parse_row_ids(raw: str) -> tuple[int, ...]:
    values = tuple(int(part.strip()) for part in str(raw).split(",") if part.strip())
    if not values:
        raise argparse.ArgumentTypeError("row-id list must contain at least one integer")
    return values


def select_required_rows(corpus: pd.DataFrame, *, row_ids: tuple[int, ...]) -> pd.DataFrame:
    validate_corpus_frame(corpus)
    selected = []
    for row_id in row_ids:
        match = corpus[corpus["row_id"].astype(int).eq(int(row_id))].copy()
        if match.empty:
            raise ValueError(f"required row_id is missing from corpus: {int(row_id)}")
        selected.append(match)
    return pd.concat(selected, ignore_index=True).sort_values(["row_id"]).reset_index(drop=True)


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


def record_normal_trajectory(
    *,
    model: torch.nn.Module,
    snapshot: OutcomeSnapshot,
    max_continuation_steps: int,
    device: torch.device,
) -> tuple[list[np.ndarray], list[np.ndarray], list[np.ndarray]]:
    env = copy.deepcopy(snapshot.env)
    obs = snapshot.observation.copy()
    hidden = snapshot.hidden.detach().clone()
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


def save_trajectory_anchor(
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
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        path,
        observation=np.asarray(observation, dtype=np.float32),
        hidden=np.asarray(hidden, dtype=np.float32),
        reference_action=np.asarray(reference_action, dtype=np.float32),
        source_index=np.asarray(source_index, dtype=np.int64),
        step_index=np.asarray(step_index, dtype=np.int64),
        weight=np.asarray(weight, dtype=np.float32),
    )


def export_m183_row16_active_set_anchor(
    *,
    checkpoint: Path,
    corpus_csv: Path,
    env_config_path: Path,
    row_ids: tuple[int, ...],
    max_continuation_steps: int,
    row_weight: float,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    env_config = load_env_config(env_config_path)
    model, _ = load_actor_critic_checkpoint(checkpoint, device=str(resolved_device))
    model.eval()
    response_dim = response_feature_dim_for_model(model)
    selected = select_required_rows(pd.read_csv(corpus_csv), row_ids=row_ids)
    snapshots = collect_requested_outcome_snapshots(
        model=model,
        env_config=env_config,
        requests=_requests(selected),
        device=resolved_device,
    )

    observations: list[np.ndarray] = []
    hidden_states: list[np.ndarray] = []
    reference_actions: list[np.ndarray] = []
    source_indices: list[int] = []
    step_indices: list[int] = []
    weights: list[float] = []
    trajectory_rows: list[dict[str, Any]] = []
    replay_rows: list[dict[str, Any]] = []

    for source_index, row in selected.reset_index(drop=True).iterrows():
        left = _snapshot(snapshots, int(row["left_seed"]), int(row["left_step"]))
        right = _snapshot(snapshots, int(row["right_seed"]), int(row["right_step"]))
        relocated = relocate_outcome_snapshot(
            left,
            body_longitudinal=float(row["relocated_obstacle_body_x"]),
            body_lateral=float(row["relocated_obstacle_body_y"]),
            half_width=float(row["relocated_obstacle_half_width"]),
        )
        normal, normal_actions = replay_outcome_variant(
            model=model,
            snapshot=relocated,
            env_config=env_config,
            variant="normal",
            response_dim=response_dim,
            variant_hidden=None,
            normal_first_action=None,
            normal_actions=None,
            max_continuation_steps=max_continuation_steps,
            device=resolved_device,
        )
        normal_first_action = np.asarray(
            [normal["first_steer"], normal["first_throttle"], normal["first_brake"]],
            dtype=np.float32,
        )
        wrong, _ = replay_outcome_variant(
            model=model,
            snapshot=relocated,
            env_config=env_config,
            variant="wrong_matched_history",
            response_dim=response_dim,
            variant_hidden=right.hidden,
            normal_first_action=normal_first_action,
            normal_actions=normal_actions,
            max_continuation_steps=max_continuation_steps,
            device=resolved_device,
        )
        replay_rows.append(
            {
                "row_id": int(row["row_id"]),
                "target": str(row["target"]),
                "physical_pair_key": str(row["physical_pair_key"]),
                "normal_success": bool(normal["success"]),
                "wrong_history_success": bool(wrong["success"]),
                "normal_margin": float(normal["min_clearance_margin"]),
                "wrong_history_margin": float(wrong["min_clearance_margin"]),
                "normal_first_steer": float(normal["first_steer"]),
                "normal_first_throttle": float(normal["first_throttle"]),
                "normal_first_brake": float(normal["first_brake"]),
                "wrong_history_first_steer": float(wrong["first_steer"]),
                "wrong_history_first_throttle": float(wrong["first_throttle"]),
                "wrong_history_first_brake": float(wrong["first_brake"]),
            }
        )
        obs_seq, hidden_seq, action_seq = record_normal_trajectory(
            model=model,
            snapshot=relocated,
            max_continuation_steps=max_continuation_steps,
            device=resolved_device,
        )
        for step_index, (obs, hidden, action) in enumerate(zip(obs_seq, hidden_seq, action_seq)):
            observations.append(obs)
            hidden_states.append(hidden)
            reference_actions.append(action)
            source_indices.append(int(source_index))
            step_indices.append(int(step_index))
            weights.append(float(row_weight))
            trajectory_rows.append(
                {
                    "row_id": int(row["row_id"]),
                    "source_index": int(source_index),
                    "step_index": int(step_index),
                    "branch": "normal",
                    "weight": float(row_weight),
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

    anchor_npz = run_dir / "m183_row16_normal_trajectory_anchor.npz"
    save_trajectory_anchor(
        anchor_npz,
        observation=np.asarray(observations, dtype=np.float32),
        hidden=np.asarray(hidden_states, dtype=np.float32),
        reference_action=np.asarray(reference_actions, dtype=np.float32),
        source_index=np.asarray(source_indices, dtype=np.int64),
        step_index=np.asarray(step_indices, dtype=np.int64),
        weight=np.asarray(weights, dtype=np.float32),
    )
    anchor = load_trajectory_action_anchor(
        anchor_npz,
        device=resolved_device,
        obs_dim=int(model.obs_dim),
        hidden_size=int(model.actor_mean.in_features),
        act_dim=int(model.act_dim),
    )
    anchor_csv = run_dir / "m183_row16_normal_trajectory_anchor.csv"
    replay_csv = run_dir / "row16_replay_sanity.csv"
    write_csv_rows(anchor_csv, trajectory_rows)
    write_csv_rows(replay_csv, replay_rows)
    summary = {
        "run_type": "m183_row16_active_set_anchor_export",
        "checkpoint": checkpoint,
        "corpus_csv": corpus_csv,
        "env_config": env_config_path,
        "row_ids": list(row_ids),
        "max_continuation_steps": int(max_continuation_steps),
        "row_weight": float(row_weight),
        "selected_rows": int(len(selected)),
        "anchor_rows": int(anchor.size),
        "anchor_npz": anchor_npz,
        "anchor_csv": anchor_csv,
        "replay_sanity_csv": replay_csv,
        "anchor_shape": {
            "observation": list(anchor.observation.shape),
            "hidden": list(anchor.hidden.shape),
            "reference_action": list(anchor.reference_action.shape),
        },
        "normal_branch_only": True,
        "normal_success_all": all(bool(row["normal_success"]) for row in replay_rows),
        "wrong_history_success_any": any(bool(row["wrong_history_success"]) for row in replay_rows),
        "normal_margin_min": float(min(float(row["normal_margin"]) for row in replay_rows)),
        "wrong_history_margin_min": float(min(float(row["wrong_history_margin"]) for row in replay_rows)),
        "actor_inputs_changed": False,
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "private_holdout_used": False,
        "result_class": "m183_row16_active_set_anchor_export_pass",
        "summary_json": run_dir / "summary.json",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Export M183/M170 row16 normal active-set trajectory anchor.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--env-config", type=Path, default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--row-ids", type=parse_row_ids, default=(16,))
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--row-weight", type=float, default=10.0)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    args = parser.parse_args()
    summary = export_m183_row16_active_set_anchor(
        checkpoint=args.checkpoint,
        corpus_csv=args.corpus,
        env_config_path=args.env_config,
        row_ids=args.row_ids,
        max_continuation_steps=args.max_continuation_steps,
        row_weight=args.row_weight,
        device=args.device,
        run_dir=args.run_dir,
    )
    print(f"result_class={summary['result_class']}")
    print(f"anchor_rows={summary['anchor_rows']}")
    print(f"summary={summary['summary_json']}")


if __name__ == "__main__":
    main()
