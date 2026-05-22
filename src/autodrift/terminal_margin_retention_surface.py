"""Export terminal-margin retention surfaces for fragile replay rows."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import write_json
from autodrift.boundary_outcome_replay_gate import REQUIRED_CORPUS_COLUMNS
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec, parse_checkpoint_spec
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.matched_history_outcome_gate import OutcomeSnapshot, collect_requested_outcome_snapshots
from autodrift.train_ppo import resolve_device
from autodrift.wrong_history_boundary_relocation_surface import relocate_outcome_snapshot


@dataclass(frozen=True)
class SurfaceSpec:
    name: str
    replay_rows_csv: Path


def parse_surface_spec(spec: str) -> SurfaceSpec:
    if "=" not in spec:
        raise argparse.ArgumentTypeError(f"surface spec must be NAME=CSV, got {spec!r}")
    name, raw_path = spec.split("=", 1)
    name = name.strip()
    if not name:
        raise argparse.ArgumentTypeError(f"surface spec has empty name: {spec!r}")
    if not raw_path.strip():
        raise argparse.ArgumentTypeError(f"surface spec has empty path: {spec!r}")
    return SurfaceSpec(name=name, replay_rows_csv=Path(raw_path))


def _validate_replay_rows(frame: pd.DataFrame) -> None:
    required = {
        "policy",
        "normal_success",
        "success_drop",
        "normal_margin",
        "wrong_history_margin",
        "margin_gap",
        *REQUIRED_CORPUS_COLUMNS,
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError("replay rows CSV is missing columns: " + ", ".join(missing))


def _requests(frame: pd.DataFrame) -> dict[int, set[int]]:
    requests: dict[int, set[int]] = {}
    for _, row in frame.iterrows():
        requests.setdefault(int(row["left_seed"]), set()).add(int(row["left_step"]))
    return requests


def _select_fragile_rows(
    surfaces: list[SurfaceSpec],
    *,
    candidate_policy: str,
    max_normal_margin: float,
    force_keys: set[tuple[str, int]],
    allowed_regression: float,
    max_weight: float,
    weight_epsilon: float,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for surface in surfaces:
        frame = pd.read_csv(surface.replay_rows_csv)
        _validate_replay_rows(frame)
        candidate = frame[frame["policy"].astype(str).eq(str(candidate_policy))].copy()
        if candidate.empty:
            raise ValueError(f"surface {surface.name!r} has no rows for candidate policy {candidate_policy!r}")
        for _, row in candidate.iterrows():
            normal_margin = float(row["normal_margin"])
            key = (surface.name, int(row["row_id"]))
            forced = key in force_keys
            fragile = (
                bool(row["normal_success"])
                and bool(row["success_drop"])
                and np.isfinite(normal_margin)
                and normal_margin > 0.0
                and normal_margin <= float(max_normal_margin)
            )
            if not fragile and not forced:
                continue
            row_weight = float(max_normal_margin) / max(normal_margin, float(weight_epsilon))
            row_weight = float(np.clip(row_weight, 1.0, float(max_weight)))
            hard_floor = 0.0
            row_allowed_regression = min(float(allowed_regression), max(0.0, normal_margin - hard_floor))
            rows.append(
                {
                    "surface": surface.name,
                    "source_replay_rows_csv": str(surface.replay_rows_csv),
                    "policy": str(row["policy"]),
                    "row_id": int(row["row_id"]),
                    "target": str(row["target"]),
                    "physical_pair_key": str(row["physical_pair_key"]),
                    "left_seed": int(row["left_seed"]),
                    "right_seed": int(row["right_seed"]),
                    "left_step": int(row["left_step"]),
                    "right_step": int(row["right_step"]),
                    "relocated_obstacle_body_x": float(row["relocated_obstacle_body_x"]),
                    "relocated_obstacle_body_y": float(row["relocated_obstacle_body_y"]),
                    "relocated_obstacle_half_width": float(row["relocated_obstacle_half_width"]),
                    "normal_margin": normal_margin,
                    "wrong_history_margin": float(row["wrong_history_margin"]),
                    "margin_gap": float(row["margin_gap"]),
                    "normal_success": bool(row["normal_success"]),
                    "success_drop": bool(row["success_drop"]),
                    "hard_floor": hard_floor,
                    "allowed_regression": row_allowed_regression,
                    "required_margin_floor": max(hard_floor, normal_margin - row_allowed_regression),
                    "retention_weight": row_weight,
                    "forced": bool(forced),
                }
            )
    if not rows:
        raise ValueError("no fragile rows selected")
    return pd.DataFrame(rows).sort_values(["surface", "row_id"]).reset_index(drop=True)


def _snapshot(snapshots: dict[tuple[int, int], OutcomeSnapshot], seed: int, step: int) -> OutcomeSnapshot:
    key = (int(seed), int(step))
    if key not in snapshots:
        raise ValueError(f"missing reconstructed snapshot seed={seed} step={step}")
    return snapshots[key]


def _record_normal_trajectory(
    *,
    model: torch.nn.Module,
    snapshot: OutcomeSnapshot,
    max_continuation_steps: int,
    device: torch.device,
) -> tuple[list[np.ndarray], list[np.ndarray], list[np.ndarray]]:
    env = snapshot.env
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
        action, next_hidden = deterministic_action_from_hidden(model, np.asarray(obs, dtype=np.float32), hidden, device)
        actions.append(np.asarray(action, dtype=np.float32).copy())
        obs, _, terminated, truncated, _ = env.step(action)
        hidden = next_hidden
        if terminated or truncated:
            break
    return observations, hidden_states, actions


def export_retention_surface(
    *,
    checkpoint_spec: CheckpointSpec,
    candidate_policy: str,
    surfaces: list[SurfaceSpec],
    env_config_path: Path,
    max_normal_margin: float,
    force_keys: set[tuple[str, int]],
    allowed_regression: float,
    max_weight: float,
    weight_epsilon: float,
    max_continuation_steps: int,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    env_config = load_env_config(env_config_path)
    model, _ = load_actor_critic_checkpoint(checkpoint_spec.path, device=str(resolved_device))
    model.eval()
    response_feature_dim_for_model(model)

    fragile_rows = _select_fragile_rows(
        surfaces,
        candidate_policy=candidate_policy,
        max_normal_margin=max_normal_margin,
        force_keys=force_keys,
        allowed_regression=allowed_regression,
        max_weight=max_weight,
        weight_epsilon=weight_epsilon,
    )
    fragile_rows.to_csv(run_dir / "fragile_rows.csv", index=False)
    fragile_rows.to_csv(run_dir / "terminal_margin_registry.csv", index=False)

    snapshots = collect_requested_outcome_snapshots(
        model=model,
        env_config=env_config,
        requests=_requests(fragile_rows),
        device=resolved_device,
    )

    observations: list[np.ndarray] = []
    hidden_states: list[np.ndarray] = []
    reference_actions: list[np.ndarray] = []
    source_indices: list[int] = []
    step_indices: list[int] = []
    weights: list[float] = []
    trajectory_rows: list[dict[str, Any]] = []

    for source_index, row in fragile_rows.reset_index(drop=True).iterrows():
        snapshot = _snapshot(snapshots, int(row["left_seed"]), int(row["left_step"]))
        relocated = relocate_outcome_snapshot(
            snapshot,
            body_longitudinal=float(row["relocated_obstacle_body_x"]),
            body_lateral=float(row["relocated_obstacle_body_y"]),
            half_width=float(row["relocated_obstacle_half_width"]),
        )
        obs_seq, hidden_seq, action_seq = _record_normal_trajectory(
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
            weights.append(float(row["retention_weight"]))
            trajectory_rows.append(
                {
                    "surface": str(row["surface"]),
                    "row_id": int(row["row_id"]),
                    "source_index": int(source_index),
                    "step_index": int(step_index),
                    "weight": float(row["retention_weight"]),
                    "reference_steer": float(action[0]),
                    "reference_throttle": float(action[1]),
                    "reference_brake": float(action[2]),
                }
            )

    if not observations:
        raise ValueError("trajectory export produced no rows")

    retention_npz = run_dir / "retention_trajectory_anchor.npz"
    np.savez(
        retention_npz,
        observation=np.asarray(observations, dtype=np.float32),
        hidden=np.asarray(hidden_states, dtype=np.float32),
        reference_action=np.asarray(reference_actions, dtype=np.float32),
        source_index=np.asarray(source_indices, dtype=np.int64),
        step_index=np.asarray(step_indices, dtype=np.int64),
        weight=np.asarray(weights, dtype=np.float32),
    )
    pd.DataFrame(trajectory_rows).to_csv(run_dir / "retention_trajectory_anchor.csv", index=False)

    recovery_unavailable = {
        "available": False,
        "reason": (
            "Recovery anchors from older source policies are not exported in M275 because "
            "recurrent hidden states are checkpoint-specific. A future recovery anchor must "
            "align source actions to the current checkpoint hidden state before training."
        ),
    }
    write_json(run_dir / "recovery_trajectory_anchor_unavailable.json", recovery_unavailable)

    weights_np = np.asarray(weights, dtype=np.float64)
    summary = {
        "run_type": "terminal_margin_retention_surface_export",
        "checkpoint": asdict(checkpoint_spec),
        "candidate_policy": candidate_policy,
        "env_config": env_config_path,
        "surfaces": [asdict(surface) for surface in surfaces],
        "max_normal_margin": float(max_normal_margin),
        "allowed_regression": float(allowed_regression),
        "max_weight": float(max_weight),
        "weight_epsilon": float(weight_epsilon),
        "fragile_rows": int(len(fragile_rows)),
        "trajectory_rows": int(len(observations)),
        "required_row16_present": bool(
            (
                fragile_rows["surface"].astype(str).eq("m183_m170")
                & fragile_rows["row_id"].astype(int).eq(16)
            ).any()
        ),
        "retention_trajectory_anchor_npz": retention_npz,
        "retention_trajectory_anchor_csv": run_dir / "retention_trajectory_anchor.csv",
        "fragile_rows_csv": run_dir / "fragile_rows.csv",
        "terminal_margin_registry_csv": run_dir / "terminal_margin_registry.csv",
        "recovery_trajectory_anchor_available": False,
        "recovery_trajectory_anchor_unavailable_json": run_dir / "recovery_trajectory_anchor_unavailable.json",
        "weight_min": float(weights_np.min()),
        "weight_max": float(weights_np.max()),
        "weight_mean": float(weights_np.mean()),
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def _parse_force_keys(values: list[str]) -> set[tuple[str, int]]:
    output: set[tuple[str, int]] = set()
    for value in values:
        if ":" not in value:
            raise argparse.ArgumentTypeError(f"force row must be SURFACE:ROW_ID, got {value!r}")
        surface, row_id = value.split(":", 1)
        output.add((surface.strip(), int(row_id)))
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint-policy", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--candidate-policy", required=True)
    parser.add_argument("--surface", type=parse_surface_spec, action="append", required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--max-normal-margin", type=float, default=0.001)
    parser.add_argument("--force-row", action="append", default=[])
    parser.add_argument("--allowed-regression", type=float, default=5e-7)
    parser.add_argument("--max-weight", type=float, default=50.0)
    parser.add_argument("--weight-epsilon", type=float, default=1e-6)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()

    summary = export_retention_surface(
        checkpoint_spec=args.checkpoint_policy,
        candidate_policy=args.candidate_policy,
        surfaces=args.surface,
        env_config_path=args.env_config,
        max_normal_margin=args.max_normal_margin,
        force_keys=_parse_force_keys(args.force_row),
        allowed_regression=args.allowed_regression,
        max_weight=args.max_weight,
        weight_epsilon=args.weight_epsilon,
        max_continuation_steps=args.max_continuation_steps,
        device=args.device,
        run_dir=args.run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
