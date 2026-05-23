"""Export trajectory anchors for failed old-key compact replay rows."""

from __future__ import annotations

import argparse
import copy
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.critical_key_replay_guard import CheckpointPolicy, parse_checkpoint_policy
from autodrift.evaluate import load_env_config
from autodrift.hidden_swap_gate import DecisionSnapshot, clone_hidden
from autodrift.intervention_objectives import load_trajectory_action_anchor
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.old_key_neighborhood_targeted_replay import (
    COMPACT_REQUIRED_COLUMNS,
    _probe_config,
    _randomization,
    _requests_by_condition,
    _require_columns,
    _snapshot,
    _tuple_range,
    collect_targeted_probe_snapshots,
)
from autodrift.outcome_sensitive_corpus import obstacle_override_config, relocate_obstacle_snapshot
from autodrift.paired_perturbation_gate import condition_config
from autodrift.train_ppo import resolve_device


FAILED_REQUIRED_COLUMNS = [
    *COMPACT_REQUIRED_COLUMNS,
    "case_id",
    "candidate_normal_success_regression",
    "candidate_normal_success",
    "candidate_wrong_history_margin",
]

_FAILED_TO_COMPACT_COLUMN_ALIASES = {
    "reference_normal_margin": "baseline_normal_margin",
    "reference_wrong_history_margin": "baseline_wrong_history_margin",
    "reference_margin_gap": "baseline_margin_gap",
}


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def _finite_float(value: Any, default: float = float("nan")) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if np.isfinite(parsed) else default


def normalize_failed_row_schema(frame: pd.DataFrame) -> pd.DataFrame:
    """Map M407 failed-row columns onto the compact old-key schema."""

    normalized = frame.copy()
    for target, source in _FAILED_TO_COMPACT_COLUMN_ALIASES.items():
        if target not in normalized and source in normalized:
            normalized[target] = normalized[source]
    return normalized


def anchor_branch_for_failed_row(row: pd.Series | dict[str, Any]) -> str:
    """Choose which branch should be anchored for an old-key failed row."""

    if _truthy(row.get("candidate_normal_success_regression", False)):
        return "normal"
    if _truthy(row.get("candidate_normal_success", False)) and _finite_float(
        row.get("candidate_wrong_history_margin")
    ) > 0.0:
        return "wrong_history"
    return "wrong_history"


def _record_branch_trajectory(
    *,
    model: torch.nn.Module,
    snapshot: DecisionSnapshot,
    initial_hidden: torch.Tensor | None,
    max_continuation_steps: int,
    device: torch.device,
) -> tuple[list[np.ndarray], list[np.ndarray], list[np.ndarray]]:
    if initial_hidden is None:
        raise ValueError("old-key replay-failure anchor requires a non-empty recurrent hidden state")
    env = copy.deepcopy(snapshot.env)
    obs = snapshot.observation.copy()
    hidden = clone_hidden(initial_hidden)
    if hidden is None:
        raise ValueError("old-key replay-failure anchor could not clone hidden state")
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
        raise ValueError("cannot save an empty old-key replay-failure trajectory anchor")
    np.savez(
        path,
        observation=np.asarray(observation, dtype=np.float32),
        hidden=np.asarray(hidden, dtype=np.float32),
        reference_action=np.asarray(reference_action, dtype=np.float32),
        source_index=np.asarray(source_index, dtype=np.int64),
        step_index=np.asarray(step_index, dtype=np.int64),
        weight=np.asarray(weight, dtype=np.float32),
    )


def export_old_key_replay_failure_trajectory_anchor(
    *,
    checkpoint_policy: CheckpointPolicy,
    reference_manifest: Path,
    failed_rows_csv: Path,
    max_continuation_steps: int,
    wrong_history_weight: float,
    normal_weight: float,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest = read_json(reference_manifest)
    failed = normalize_failed_row_schema(pd.read_csv(failed_rows_csv))
    if "record_type" in failed:
        failed = failed[failed["record_type"].astype(str).eq("m341_mined_case")].copy()
    _require_columns(failed, FAILED_REQUIRED_COLUMNS, label="failed old-key rows")
    if failed.empty:
        raise ValueError("no failed old-key rows available for trajectory anchor export")

    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_policy.path, device=str(resolved_device))
    model.eval()
    base_config = obstacle_override_config(
        load_env_config(Path(manifest["env_config"])),
        distance_range=None,
        half_width_range=None,
        perception_reveal_step=manifest.get("obstacle_perception_reveal_step"),
        perception_reveal_distance=manifest.get("obstacle_perception_reveal_distance"),
    )
    configs = {
        "nominal": condition_config(
            base_config,
            _tuple_range(manifest["nominal_friction_mu_range"]),
            _randomization(manifest.get("nominal_randomization")),
        ),
        "perturbed": condition_config(
            base_config,
            _tuple_range(manifest["perturbed_friction_mu_range"]),
            _randomization(manifest.get("perturbed_randomization")),
        ),
    }
    probe = _probe_config(manifest.get("probe", {}))
    requests = _requests_by_condition(failed)
    snapshots: dict[str, dict[int, dict[int, DecisionSnapshot]]] = {"nominal": {}, "perturbed": {}}
    for condition, seed_requests in requests.items():
        for seed, steps in seed_requests.items():
            snapshots[condition][int(seed)] = collect_targeted_probe_snapshots(
                model=model,
                env_config=configs[condition],
                condition=condition,
                seed=int(seed),
                requested_steps=set(int(step) for step in steps),
                max_probe_steps=int(manifest["max_probe_steps"]),
                probe_config=probe,
            )

    observations: list[np.ndarray] = []
    hidden_states: list[np.ndarray] = []
    reference_actions: list[np.ndarray] = []
    source_indices: list[int] = []
    step_indices: list[int] = []
    weights: list[float] = []
    trajectory_rows: list[dict[str, Any]] = []
    missing_rows: list[dict[str, Any]] = []
    branch_counts = {"normal": 0, "wrong_history": 0}

    for source_index, row in failed.reset_index(drop=True).iterrows():
        seed = int(row["seed"])
        source = str(row["source_condition"])
        paired = "perturbed" if source == "nominal" else "nominal"
        source_snapshot = _snapshot(snapshots, source, seed, int(row["source_step"]))
        paired_snapshot = _snapshot(snapshots, paired, seed, int(row["paired_step"]))
        if source_snapshot is None or paired_snapshot is None:
            missing_rows.append(
                {
                    "case_id": str(row.get("case_id", row.get("key", ""))),
                    "source_condition": source,
                    "source_step": int(row["source_step"]),
                    "paired_step": int(row["paired_step"]),
                    "missing_source": source_snapshot is None,
                    "missing_paired": paired_snapshot is None,
                }
            )
            continue
        relocated = relocate_obstacle_snapshot(
            source_snapshot,
            body_longitudinal=float(row["target_obstacle_distance"]),
            body_lateral=float(row["relocated_obstacle_body_y"]),
            half_width=float(row["relocated_obstacle_half_width"]),
        )
        branch = anchor_branch_for_failed_row(row)
        branch_counts[branch] += 1
        initial_hidden = relocated.hidden if branch == "normal" else paired_snapshot.hidden
        row_weight = float(normal_weight if branch == "normal" else wrong_history_weight)
        obs_seq, hidden_seq, action_seq = _record_branch_trajectory(
            model=model,
            snapshot=relocated,
            initial_hidden=initial_hidden,
            max_continuation_steps=max_continuation_steps,
            device=resolved_device,
        )
        for step_index, (obs, hidden, action) in enumerate(zip(obs_seq, hidden_seq, action_seq)):
            observations.append(obs)
            hidden_states.append(hidden)
            reference_actions.append(action)
            source_indices.append(int(source_index))
            step_indices.append(int(step_index))
            weights.append(row_weight)
            trajectory_rows.append(
                {
                    "case_id": str(row.get("case_id", row.get("key", ""))),
                    "key": str(row["key"]),
                    "branch": branch,
                    "source_index": int(source_index),
                    "step_index": int(step_index),
                    "weight": row_weight,
                    "seed": seed,
                    "seed_block": str(row.get("seed_block", "")),
                    "source_condition": source,
                    "source_step": int(row["source_step"]),
                    "paired_step": int(row["paired_step"]),
                    "reference_steer": float(action[0]),
                    "reference_throttle": float(action[1]),
                    "reference_brake": float(action[2]),
                }
            )
    if not observations:
        raise ValueError("old-key replay-failure trajectory export produced no anchor rows")

    anchor_npz = run_dir / "old_key_replay_failure_trajectory_anchor.npz"
    _save_anchor(
        anchor_npz,
        observation=np.asarray(observations, dtype=np.float32),
        hidden=np.asarray(hidden_states, dtype=np.float32),
        reference_action=np.asarray(reference_actions, dtype=np.float32),
        source_index=np.asarray(source_indices, dtype=np.int64),
        step_index=np.asarray(step_indices, dtype=np.int64),
        weight=np.asarray(weights, dtype=np.float32),
    )
    write_csv_rows(run_dir / "old_key_replay_failure_trajectory_anchor.csv", trajectory_rows)
    if missing_rows:
        write_csv_rows(run_dir / "missing_rows.csv", missing_rows)
    anchor = load_trajectory_action_anchor(
        anchor_npz,
        device=resolved_device,
        obs_dim=int(model.obs_dim),
        hidden_size=int(model.actor_mean.in_features),
        act_dim=int(model.act_dim),
    )
    rows_per_case = pd.DataFrame(trajectory_rows).groupby("case_id").size().to_dict()
    summary = {
        "run_type": "old_key_replay_failure_trajectory_anchor_export",
        "checkpoint": asdict(checkpoint_policy),
        "reference_manifest": reference_manifest,
        "failed_rows_csv": failed_rows_csv,
        "max_continuation_steps": int(max_continuation_steps),
        "wrong_history_weight": float(wrong_history_weight),
        "normal_weight": float(normal_weight),
        "failed_rows": int(len(failed)),
        "missing_rows": int(len(missing_rows)),
        "branch_counts": branch_counts,
        "anchor_rows": int(anchor.size),
        "anchor_npz": anchor_npz,
        "anchor_csv": run_dir / "old_key_replay_failure_trajectory_anchor.csv",
        "anchor_shape": {
            "observation": list(anchor.observation.shape),
            "hidden": list(anchor.hidden.shape),
            "reference_action": list(anchor.reference_action.shape),
        },
        "rows_per_case": {str(key): int(value) for key, value in rows_per_case.items()},
        "forbidden_shortcuts_used": False,
        "ppo_or_actor_update_run": False,
        "actor_inputs_changed": False,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint-policy", type=parse_checkpoint_policy, required=True)
    parser.add_argument("--reference-manifest", type=Path, required=True)
    parser.add_argument("--failed-rows-csv", type=Path, required=True)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--wrong-history-weight", type=float, default=75.0)
    parser.add_argument("--normal-weight", type=float, default=75.0)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    summary = export_old_key_replay_failure_trajectory_anchor(
        checkpoint_policy=args.checkpoint_policy,
        reference_manifest=args.reference_manifest,
        failed_rows_csv=args.failed_rows_csv,
        max_continuation_steps=args.max_continuation_steps,
        wrong_history_weight=args.wrong_history_weight,
        normal_weight=args.normal_weight,
        device=args.device,
        run_dir=args.run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
