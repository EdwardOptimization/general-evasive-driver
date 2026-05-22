"""Probe current-hidden recovery anchors for fragile terminal-margin rows."""

from __future__ import annotations

import argparse
import copy
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec, parse_checkpoint_spec
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.hidden_swap_gate import terminal_reason
from autodrift.intervention_objectives import load_trajectory_action_anchor
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.matched_history_outcome_gate import (
    OutcomeSnapshot,
    collect_requested_outcome_snapshots,
    replay_outcome_variant,
)
from autodrift.train_ppo import resolve_device
from autodrift.wrong_history_boundary_relocation_surface import relocate_outcome_snapshot


REQUIRED_REGISTRY_COLUMNS = {
    "surface",
    "row_id",
    "target",
    "physical_pair_key",
    "left_seed",
    "left_step",
    "relocated_obstacle_body_x",
    "relocated_obstacle_body_y",
    "relocated_obstacle_half_width",
    "normal_margin",
    "required_margin_floor",
    "retention_weight",
}


@dataclass(frozen=True)
class RowKey:
    surface: str
    row_id: int


@dataclass(frozen=True)
class ActionCandidate:
    candidate_id: int
    steer_delta: float
    throttle_delta: float
    brake_delta: float
    action: np.ndarray
    action_l2: float


def parse_float_list(raw: str) -> tuple[float, ...]:
    values = tuple(float(part.strip()) for part in str(raw).split(",") if part.strip())
    if not values:
        raise argparse.ArgumentTypeError("float list must contain at least one value")
    return values


def parse_row_key(raw: str) -> RowKey:
    if ":" not in raw:
        raise argparse.ArgumentTypeError(f"row key must be SURFACE:ROW_ID, got {raw!r}")
    surface, row_id = raw.split(":", 1)
    surface = surface.strip()
    if not surface:
        raise argparse.ArgumentTypeError(f"row key has empty surface: {raw!r}")
    return RowKey(surface=surface, row_id=int(row_id))


def _validate_registry(frame: pd.DataFrame) -> None:
    missing = sorted(REQUIRED_REGISTRY_COLUMNS.difference(frame.columns))
    if missing:
        raise ValueError("terminal-margin registry is missing columns: " + ", ".join(missing))


def _filter_registry_rows(
    registry: pd.DataFrame,
    *,
    row_keys: tuple[RowKey, ...],
    max_rows: int,
) -> pd.DataFrame:
    _validate_registry(registry)
    frame = registry.copy()
    if row_keys:
        selected = []
        for key in row_keys:
            match = frame[
                frame["surface"].astype(str).eq(key.surface)
                & frame["row_id"].astype(int).eq(int(key.row_id))
            ].copy()
            if match.empty:
                raise ValueError(f"required row not found in registry: {key.surface}:{key.row_id}")
            selected.append(match)
        frame = pd.concat(selected, ignore_index=True)
    else:
        frame = frame.sort_values(["surface", "row_id"]).reset_index(drop=True)
    if max_rows > 0:
        frame = frame.head(int(max_rows)).reset_index(drop=True)
    if frame.empty:
        raise ValueError("no registry rows selected")
    return frame.reset_index(drop=True)


def _requests(frame: pd.DataFrame) -> dict[int, set[int]]:
    requests: dict[int, set[int]] = {}
    for _, row in frame.iterrows():
        requests.setdefault(int(row["left_seed"]), set()).add(int(row["left_step"]))
    return requests


def _snapshot(snapshots: dict[tuple[int, int], OutcomeSnapshot], seed: int, step: int) -> OutcomeSnapshot:
    key = (int(seed), int(step))
    if key not in snapshots:
        raise ValueError(f"missing reconstructed snapshot seed={seed} step={step}")
    return snapshots[key]


def build_action_candidates(
    base_action: np.ndarray,
    *,
    steer_deltas: tuple[float, ...],
    throttle_deltas: tuple[float, ...],
    brake_deltas: tuple[float, ...],
) -> list[ActionCandidate]:
    base = np.asarray(base_action, dtype=np.float32)
    if base.shape != (3,):
        raise ValueError(f"base action must have shape (3,), got {base.shape}")
    candidates: list[ActionCandidate] = []
    candidate_id = 0
    for steer_delta in steer_deltas:
        for brake_delta in brake_deltas:
            for throttle_delta in throttle_deltas:
                delta = np.asarray([steer_delta, throttle_delta, brake_delta], dtype=np.float32)
                action = np.clip(base + delta, -1.0, 1.0).astype(np.float32)
                candidates.append(
                    ActionCandidate(
                        candidate_id=candidate_id,
                        steer_delta=float(steer_delta),
                        throttle_delta=float(throttle_delta),
                        brake_delta=float(brake_delta),
                        action=action,
                        action_l2=float(np.linalg.norm(action.astype(np.float64) - base.astype(np.float64))),
                    )
                )
                candidate_id += 1
    return candidates


def _rollout_first_action_override(
    *,
    model: torch.nn.Module,
    snapshot: OutcomeSnapshot,
    first_action: np.ndarray,
    max_continuation_steps: int,
    device: torch.device,
) -> dict[str, Any]:
    env = copy.deepcopy(snapshot.env)
    obs = snapshot.observation.copy()
    hidden = snapshot.hidden.detach().clone()
    action = np.clip(np.asarray(first_action, dtype=np.float32), -1.0, 1.0)
    _, next_hidden = deterministic_action_from_hidden(model, np.asarray(obs, dtype=np.float32), hidden, device)
    max_steps = int(max_continuation_steps)
    if max_steps <= 0:
        max_steps = max(1, env.config.max_steps - int(snapshot.step))

    rewards: list[float] = []
    betas: list[float] = []
    terminated = False
    truncated = False
    info = dict(snapshot.info)

    obs, reward, terminated, truncated, info = env.step(action)
    rewards.append(float(reward))
    betas.append(float(info.get("beta", float("nan"))))
    hidden = next_hidden

    for _ in range(max_steps - 1):
        if terminated or truncated:
            break
        policy_action, next_hidden = deterministic_action_from_hidden(
            model,
            np.asarray(obs, dtype=np.float32),
            hidden,
            device,
        )
        obs, reward, terminated, truncated, info = env.step(policy_action)
        rewards.append(float(reward))
        betas.append(float(info.get("beta", float("nan"))))
        hidden = next_hidden

    beta_abs_peak = float(np.nanmax(np.abs(betas))) if betas else float("nan")
    reason = terminal_reason(info, terminated, truncated, env.config)
    return {
        "steps": int(len(rewards)),
        "return": float(np.sum(rewards)),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "success": not bool(terminated),
        "collision": bool(info.get("collision", False)),
        "off_road": reason == "off_road",
        "spin_out": bool(np.isfinite(beta_abs_peak) and beta_abs_peak > 1.2),
        "terminal_reason": reason,
        "obstacle_completed": bool(info.get("obstacle_completed", False)),
        "min_obstacle_clearance": float(info.get("min_obstacle_clearance", float("nan"))),
        "obstacle_collision_radius": float(info.get("obstacle_collision_radius", float("nan"))),
        "min_clearance_margin": float(info.get("min_clearance_margin", float("nan"))),
        "beta_abs_peak": beta_abs_peak,
        "first_steer": float(action[0]),
        "first_throttle": float(action[1]),
        "first_brake": float(action[2]),
    }


def candidate_acceptance(
    *,
    candidate_margin: float,
    candidate_success: bool,
    baseline_margin: float,
    required_margin_floor: float,
    action_l2: float,
    min_margin_improvement: float,
    max_action_l2: float,
) -> tuple[bool, str]:
    if not bool(candidate_success):
        return False, "candidate_not_successful"
    if not np.isfinite(candidate_margin):
        return False, "candidate_margin_not_finite"
    if not np.isfinite(baseline_margin):
        return False, "baseline_margin_not_finite"
    improvement = float(candidate_margin) - float(baseline_margin)
    if improvement < float(min_margin_improvement):
        return False, "insufficient_margin_improvement"
    if float(candidate_margin) < float(required_margin_floor):
        return False, "below_required_margin_floor"
    if float(action_l2) > float(max_action_l2):
        return False, "outside_action_trust_region"
    return True, "accepted"


def select_best_candidate(candidate_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    accepted = [row for row in candidate_rows if bool(row.get("accepted", False))]
    if not accepted:
        return None
    return max(
        accepted,
        key=lambda row: (
            float(row.get("margin_improvement", float("-inf"))),
            float(row.get("candidate_margin", float("-inf"))),
            -float(row.get("action_l2", float("inf"))),
        ),
    )


def _baseline_result(
    *,
    model: torch.nn.Module,
    snapshot: OutcomeSnapshot,
    response_dim: int,
    max_continuation_steps: int,
    device: torch.device,
) -> dict[str, Any]:
    normal, _ = replay_outcome_variant(
        model=model,
        snapshot=snapshot,
        env_config=snapshot.env.config,
        variant="normal",
        response_dim=response_dim,
        variant_hidden=None,
        normal_first_action=None,
        normal_actions=None,
        max_continuation_steps=max_continuation_steps,
        device=device,
    )
    return normal


def _save_recovery_anchor(
    *,
    output_npz: Path,
    observations: list[np.ndarray],
    hidden_states: list[np.ndarray],
    reference_actions: list[np.ndarray],
    source_indices: list[int],
    step_indices: list[int],
    weights: list[float],
) -> None:
    if not observations:
        raise ValueError("cannot save an empty recovery anchor")
    np.savez(
        output_npz,
        observation=np.asarray(observations, dtype=np.float32),
        hidden=np.asarray(hidden_states, dtype=np.float32),
        reference_action=np.asarray(reference_actions, dtype=np.float32),
        source_index=np.asarray(source_indices, dtype=np.int64),
        step_index=np.asarray(step_indices, dtype=np.int64),
        weight=np.asarray(weights, dtype=np.float32),
    )


def export_recovery_anchor_probe(
    *,
    checkpoint_spec: CheckpointSpec,
    registry_csv: Path,
    env_config_path: Path,
    row_keys: tuple[RowKey, ...],
    max_rows: int,
    steer_deltas: tuple[float, ...],
    throttle_deltas: tuple[float, ...],
    brake_deltas: tuple[float, ...],
    min_margin_improvement: float,
    max_action_l2: float,
    max_continuation_steps: int,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    env_config = load_env_config(env_config_path)
    model, _ = load_actor_critic_checkpoint(checkpoint_spec.path, device=str(resolved_device))
    model.eval()
    response_dim = response_feature_dim_for_model(model)
    registry = _filter_registry_rows(
        pd.read_csv(registry_csv),
        row_keys=row_keys,
        max_rows=max_rows,
    )
    snapshots = collect_requested_outcome_snapshots(
        model=model,
        env_config=env_config,
        requests=_requests(registry),
        device=resolved_device,
    )

    candidate_rows: list[dict[str, Any]] = []
    recovery_rows: list[dict[str, Any]] = []
    unrecovered_rows: list[dict[str, Any]] = []
    observations: list[np.ndarray] = []
    hidden_states: list[np.ndarray] = []
    reference_actions: list[np.ndarray] = []
    source_indices: list[int] = []
    step_indices: list[int] = []
    weights: list[float] = []

    for source_index, row in registry.reset_index(drop=True).iterrows():
        snapshot = _snapshot(snapshots, int(row["left_seed"]), int(row["left_step"]))
        relocated = relocate_outcome_snapshot(
            snapshot,
            body_longitudinal=float(row["relocated_obstacle_body_x"]),
            body_lateral=float(row["relocated_obstacle_body_y"]),
            half_width=float(row["relocated_obstacle_half_width"]),
        )
        baseline = _baseline_result(
            model=model,
            snapshot=relocated,
            response_dim=response_dim,
            max_continuation_steps=max_continuation_steps,
            device=resolved_device,
        )
        base_action, _ = deterministic_action_from_hidden(
            model,
            relocated.observation,
            relocated.hidden,
            resolved_device,
        )
        baseline_margin = float(baseline.get("min_clearance_margin", float("nan")))
        required_margin_floor = float(row["required_margin_floor"])
        row_candidate_rows: list[dict[str, Any]] = []
        candidates = build_action_candidates(
            base_action,
            steer_deltas=steer_deltas,
            throttle_deltas=throttle_deltas,
            brake_deltas=brake_deltas,
        )
        for candidate in candidates:
            result = _rollout_first_action_override(
                model=model,
                snapshot=relocated,
                first_action=candidate.action,
                max_continuation_steps=max_continuation_steps,
                device=resolved_device,
            )
            candidate_margin = float(result.get("min_clearance_margin", float("nan")))
            accepted, rejection_reason = candidate_acceptance(
                candidate_margin=candidate_margin,
                candidate_success=bool(result.get("success", False)),
                baseline_margin=baseline_margin,
                required_margin_floor=required_margin_floor,
                action_l2=candidate.action_l2,
                min_margin_improvement=min_margin_improvement,
                max_action_l2=max_action_l2,
            )
            candidate_row = {
                "surface": str(row["surface"]),
                "row_id": int(row["row_id"]),
                "source_index": int(source_index),
                "candidate_id": int(candidate.candidate_id),
                "target": str(row["target"]),
                "physical_pair_key": str(row["physical_pair_key"]),
                "left_seed": int(row["left_seed"]),
                "left_step": int(row["left_step"]),
                "baseline_success": bool(baseline.get("success", False)),
                "baseline_margin": baseline_margin,
                "registry_normal_margin": float(row["normal_margin"]),
                "required_margin_floor": required_margin_floor,
                "candidate_success": bool(result.get("success", False)),
                "candidate_terminal_reason": str(result.get("terminal_reason", "")),
                "candidate_margin": candidate_margin,
                "margin_improvement": (
                    candidate_margin - baseline_margin
                    if np.isfinite(candidate_margin) and np.isfinite(baseline_margin)
                    else float("nan")
                ),
                "base_steer": float(base_action[0]),
                "base_throttle": float(base_action[1]),
                "base_brake": float(base_action[2]),
                "candidate_steer": float(candidate.action[0]),
                "candidate_throttle": float(candidate.action[1]),
                "candidate_brake": float(candidate.action[2]),
                "steer_delta": float(candidate.steer_delta),
                "throttle_delta": float(candidate.throttle_delta),
                "brake_delta": float(candidate.brake_delta),
                "action_l2": float(candidate.action_l2),
                "accepted": bool(accepted),
                "rejection_reason": rejection_reason,
            }
            candidate_rows.append(candidate_row)
            row_candidate_rows.append(candidate_row)

        best = select_best_candidate(row_candidate_rows)
        if best is None:
            best_any = max(
                row_candidate_rows,
                key=lambda item: (
                    float(item.get("margin_improvement", float("-inf"))),
                    float(item.get("candidate_margin", float("-inf"))),
                    -float(item.get("action_l2", float("inf"))),
                ),
            )
            unrecovered_rows.append(
                {
                    "surface": str(row["surface"]),
                    "row_id": int(row["row_id"]),
                    "source_index": int(source_index),
                    "baseline_margin": baseline_margin,
                    "required_margin_floor": required_margin_floor,
                    "best_candidate_id": int(best_any["candidate_id"]),
                    "best_margin": float(best_any["candidate_margin"]),
                    "best_margin_improvement": float(best_any["margin_improvement"]),
                    "best_action_l2": float(best_any["action_l2"]),
                    "best_rejection_reason": str(best_any["rejection_reason"]),
                }
            )
            continue

        reference_action = np.asarray(
            [best["candidate_steer"], best["candidate_throttle"], best["candidate_brake"]],
            dtype=np.float32,
        )
        observations.append(np.asarray(relocated.observation, dtype=np.float32).copy())
        hidden_states.append(relocated.hidden.detach().cpu().numpy().reshape(-1).astype(np.float32))
        reference_actions.append(reference_action)
        source_indices.append(int(source_index))
        step_indices.append(0)
        weights.append(float(row["retention_weight"]))
        recovery_rows.append(
            {
                "surface": str(row["surface"]),
                "row_id": int(row["row_id"]),
                "source_index": int(source_index),
                "target": str(row["target"]),
                "physical_pair_key": str(row["physical_pair_key"]),
                "left_seed": int(row["left_seed"]),
                "left_step": int(row["left_step"]),
                "candidate_id": int(best["candidate_id"]),
                "baseline_margin": baseline_margin,
                "recovered_margin": float(best["candidate_margin"]),
                "margin_improvement": float(best["margin_improvement"]),
                "required_margin_floor": required_margin_floor,
                "base_steer": float(best["base_steer"]),
                "base_throttle": float(best["base_throttle"]),
                "base_brake": float(best["base_brake"]),
                "reference_steer": float(best["candidate_steer"]),
                "reference_throttle": float(best["candidate_throttle"]),
                "reference_brake": float(best["candidate_brake"]),
                "action_l2": float(best["action_l2"]),
                "weight": float(row["retention_weight"]),
            }
        )

    write_csv_rows(run_dir / "recovery_candidates.csv", candidate_rows)
    write_csv_rows(
        run_dir / "recovery_anchor.csv",
        recovery_rows,
        fieldnames=[
            "surface",
            "row_id",
            "source_index",
            "target",
            "physical_pair_key",
            "left_seed",
            "left_step",
            "candidate_id",
            "baseline_margin",
            "recovered_margin",
            "margin_improvement",
            "required_margin_floor",
            "base_steer",
            "base_throttle",
            "base_brake",
            "reference_steer",
            "reference_throttle",
            "reference_brake",
            "action_l2",
            "weight",
        ],
    )
    write_csv_rows(
        run_dir / "unrecovered_rows.csv",
        unrecovered_rows,
        fieldnames=[
            "surface",
            "row_id",
            "source_index",
            "baseline_margin",
            "required_margin_floor",
            "best_candidate_id",
            "best_margin",
            "best_margin_improvement",
            "best_action_l2",
            "best_rejection_reason",
        ],
    )

    recovery_anchor_npz: Path | None = None
    anchor_shape: dict[str, Any] | None = None
    if recovery_rows:
        recovery_anchor_npz = run_dir / "recovery_anchor.npz"
        _save_recovery_anchor(
            output_npz=recovery_anchor_npz,
            observations=observations,
            hidden_states=hidden_states,
            reference_actions=reference_actions,
            source_indices=source_indices,
            step_indices=step_indices,
            weights=weights,
        )
        anchor = load_trajectory_action_anchor(
            recovery_anchor_npz,
            device=resolved_device,
            obs_dim=int(model.obs_dim),
            hidden_size=int(model.actor_mean.in_features),
            act_dim=int(model.act_dim),
        )
        anchor_shape = {
            "rows": int(anchor.size),
            "observation": list(anchor.observation.shape),
            "hidden": list(anchor.hidden.shape),
            "reference_action": list(anchor.reference_action.shape),
        }

    required_keys = set(row_keys)
    row16_key = RowKey("m183_m170", 16)
    if row16_key not in required_keys and not row_keys:
        required_keys.add(row16_key)
    recovered_key_set = {(str(row["surface"]), int(row["row_id"])) for row in recovery_rows}
    probed_key_set = {(str(row["surface"]), int(row["row_id"])) for _, row in registry.iterrows()}
    candidate_frame = pd.DataFrame(candidate_rows)
    finite_improvements = (
        candidate_frame["margin_improvement"].astype(float)
        if not candidate_frame.empty
        else pd.Series(dtype=float)
    )
    finite_improvements = finite_improvements[np.isfinite(finite_improvements)]
    recovery_frame = pd.DataFrame(recovery_rows)
    recovered_improvements = (
        recovery_frame["margin_improvement"].astype(float)
        if not recovery_frame.empty
        else pd.Series(dtype=float)
    )
    recovered_improvements = recovered_improvements[np.isfinite(recovered_improvements)]
    summary = {
        "run_type": "terminal_margin_recovery_anchor_probe",
        "checkpoint": asdict(checkpoint_spec),
        "registry_csv": registry_csv,
        "env_config": env_config_path,
        "row_keys": [asdict(key) for key in row_keys],
        "max_rows": int(max_rows),
        "steer_deltas": steer_deltas,
        "throttle_deltas": throttle_deltas,
        "brake_deltas": brake_deltas,
        "min_margin_improvement": float(min_margin_improvement),
        "max_action_l2": float(max_action_l2),
        "max_continuation_steps": int(max_continuation_steps),
        "device": str(resolved_device),
        "rows_probed": int(len(registry)),
        "candidate_rollouts": int(len(candidate_rows)),
        "accepted_candidates": int(candidate_frame["accepted"].astype(bool).sum()) if not candidate_frame.empty else 0,
        "recovered_rows": int(len(recovery_rows)),
        "unrecovered_rows": int(len(unrecovered_rows)),
        "required_row16_probed": ("m183_m170", 16) in probed_key_set,
        "required_row16_recovered": ("m183_m170", 16) in recovered_key_set,
        "recovery_anchor_available": bool(recovery_anchor_npz is not None),
        "recovery_anchor_npz": recovery_anchor_npz,
        "recovery_anchor_csv": run_dir / "recovery_anchor.csv",
        "recovery_candidates_csv": run_dir / "recovery_candidates.csv",
        "unrecovered_rows_csv": run_dir / "unrecovered_rows.csv",
        "anchor_shape": anchor_shape,
        "margin_improvement_max": float(finite_improvements.max()) if len(finite_improvements) else float("nan"),
        "margin_improvement_mean": float(finite_improvements.mean()) if len(finite_improvements) else float("nan"),
        "recovered_margin_improvement_min": (
            float(recovered_improvements.min()) if len(recovered_improvements) else float("nan")
        ),
        "recovered_margin_improvement_max": (
            float(recovered_improvements.max()) if len(recovered_improvements) else float("nan")
        ),
        "recovered_margin_improvement_mean": (
            float(recovered_improvements.mean()) if len(recovered_improvements) else float("nan")
        ),
        "forbidden_shortcuts_used": False,
        "ppo_or_actor_update_run": False,
    }
    for key in required_keys:
        if (key.surface, int(key.row_id)) not in probed_key_set:
            raise ValueError(f"required row was not probed: {key.surface}:{key.row_id}")
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint-policy", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--registry-csv", type=Path, required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--row", type=parse_row_key, action="append", default=[])
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--steer-deltas", type=parse_float_list, default=(-0.01, 0.0, 0.01))
    parser.add_argument("--throttle-deltas", type=parse_float_list, default=(-0.02, 0.0))
    parser.add_argument("--brake-deltas", type=parse_float_list, default=(-0.03, -0.015, 0.0, 0.015))
    parser.add_argument("--min-margin-improvement", type=float, default=5e-5)
    parser.add_argument("--max-action-l2", type=float, default=0.05)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()

    summary = export_recovery_anchor_probe(
        checkpoint_spec=args.checkpoint_policy,
        registry_csv=args.registry_csv,
        env_config_path=args.env_config,
        row_keys=tuple(args.row),
        max_rows=args.max_rows,
        steer_deltas=args.steer_deltas,
        throttle_deltas=args.throttle_deltas,
        brake_deltas=args.brake_deltas,
        min_margin_improvement=args.min_margin_improvement,
        max_action_l2=args.max_action_l2,
        max_continuation_steps=args.max_continuation_steps,
        device=args.device,
        run_dir=args.run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
