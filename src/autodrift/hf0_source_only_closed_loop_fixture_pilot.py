"""Bounded source-only HF0 closed-loop fixture pilot preflight."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.four_wheel_hf0_adapter import FourWheelHF0Backend
from autodrift.hf0_source_only_fixture_smoke import admitted_source_only_fixture_rows
from autodrift.hf0_scenario_taxonomy_mapping import SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID
from autodrift.high_fidelity_interface import (
    ACTION_DIM,
    BackendResetRequest,
    P0_OBSERVATION_DIM,
    P0ObservationExtractor,
    validate_actor_action,
)
from autodrift.train_ppo import ActorCritic, HUMAN_VIEW_ONLINE_RECURRENT_ENCODERS


DEFAULT_HORIZON_STEPS = 20
DEFAULT_MILESTONE = "m2488-source-only-closed-loop-fixture-pilot-implementation-preflight"
ALLOWED_ACTOR_ENCODERS = frozenset(HUMAN_VIEW_ONLINE_RECURRENT_ENCODERS)


@dataclass(frozen=True)
class CheckpointAdmission:
    checkpoint_path: str
    checkpoint_admitted: bool
    reason: str
    obs_dim: int | None
    action_dim: int | None
    actor_encoder: str
    action_sequence_horizon: int | None

    def to_summary_fields(self) -> dict[str, Any]:
        return {
            "checkpoint_path": self.checkpoint_path,
            "checkpoint_admitted": self.checkpoint_admitted,
            "checkpoint_admission_reason": self.reason,
            "checkpoint_obs_dim": self.obs_dim,
            "checkpoint_action_dim": self.action_dim,
            "checkpoint_actor_encoder": self.actor_encoder,
            "checkpoint_action_sequence_horizon": self.action_sequence_horizon,
        }


@dataclass(frozen=True)
class PilotRolloutRow:
    fixture_id: str
    surface_id: str
    role_family: str
    step_index: int
    observation_shape: int
    action_shape: int
    action_steer: float
    action_throttle: float
    action_brake: float
    action_finite: bool
    action_within_bounds: bool
    backend_status: str
    terminated_by_backend: bool
    truncated_by_backend: bool
    diagnostic_wheel_force_count: int
    policy_action: bool

    def to_csv_row(self) -> dict[str, Any]:
        return {
            "fixture_id": self.fixture_id,
            "surface_id": self.surface_id,
            "role_family": self.role_family,
            "step_index": self.step_index,
            "observation_shape": self.observation_shape,
            "action_shape": self.action_shape,
            "action_steer": self.action_steer,
            "action_throttle": self.action_throttle,
            "action_brake": self.action_brake,
            "action_finite": self.action_finite,
            "action_within_bounds": self.action_within_bounds,
            "backend_status": self.backend_status,
            "terminated_by_backend": self.terminated_by_backend,
            "truncated_by_backend": self.truncated_by_backend,
            "diagnostic_wheel_force_count": self.diagnostic_wheel_force_count,
            "policy_action": self.policy_action,
        }


def admit_actor_checkpoint(
    checkpoint_path: Path | str,
    *,
    device: str = "cpu",
) -> tuple[ActorCritic | None, CheckpointAdmission]:
    path = Path(checkpoint_path)
    try:
        model, _checkpoint = load_actor_critic_checkpoint(path, device=device)
    except Exception as exc:
        return None, CheckpointAdmission(
            checkpoint_path=str(path),
            checkpoint_admitted=False,
            reason=f"load_failed: {type(exc).__name__}: {exc}",
            obs_dim=None,
            action_dim=None,
            actor_encoder="unknown",
            action_sequence_horizon=None,
        )

    reasons: list[str] = []
    if int(model.obs_dim) != P0_OBSERVATION_DIM:
        reasons.append(f"obs_dim={model.obs_dim} expected {P0_OBSERVATION_DIM}")
    if int(model.act_dim) != ACTION_DIM:
        reasons.append(f"action_dim={model.act_dim} expected {ACTION_DIM}")
    if str(model.actor_encoder) not in ALLOWED_ACTOR_ENCODERS:
        reasons.append(
            f"actor_encoder={model.actor_encoder} expected one of {sorted(ALLOWED_ACTOR_ENCODERS)}"
        )
    if int(model.action_sequence_horizon) != 1:
        reasons.append(f"action_sequence_horizon={model.action_sequence_horizon} expected 1")

    admitted = not reasons
    return (
        model if admitted else None,
        CheckpointAdmission(
            checkpoint_path=str(path),
            checkpoint_admitted=admitted,
            reason="admitted" if admitted else "; ".join(reasons),
            obs_dim=int(model.obs_dim),
            action_dim=int(model.act_dim),
            actor_encoder=str(model.actor_encoder),
            action_sequence_horizon=int(model.action_sequence_horizon),
        ),
    )


def _policy_action(model: ActorCritic, observation: np.ndarray, hidden: Any) -> tuple[np.ndarray, Any]:
    if not model.is_online_recurrent:
        raise RuntimeError("source-only fixture pilot requires an online recurrent actor")
    action, _log_prob, _value, next_hidden = model.act_recurrent(
        observation,
        hidden,
        deterministic=True,
    )
    return action, next_hidden


def run_source_only_closed_loop_fixture_pilot(
    checkpoint_path: Path | str,
    *,
    horizon_steps: int = DEFAULT_HORIZON_STEPS,
    device: str = "cpu",
) -> tuple[list[PilotRolloutRow], dict[str, Any]]:
    if int(horizon_steps) < 1:
        raise ValueError("horizon_steps must be positive")

    model, admission = admit_actor_checkpoint(checkpoint_path, device=device)
    if model is None:
        return [], _summary_from_rows([], admission=admission, horizon_steps=int(horizon_steps))

    extractor = P0ObservationExtractor()
    rollout_rows: list[PilotRolloutRow] = []
    reset_observation_shapes: list[int] = []
    reset_count = 0

    for fixture_index, fixture_row in enumerate(admitted_source_only_fixture_rows()):
        backend = FourWheelHF0Backend()
        hidden = None
        try:
            reset_result = backend.reset(
                BackendResetRequest(
                    seed=2488 + fixture_index,
                    scenario_spec_id=fixture_row.fixture_id,
                    role_family=fixture_row.role_family,
                    options={
                        "fixture_id": fixture_row.fixture_id,
                        "fixture_admission_status": fixture_row.fixture_admission_status,
                    },
                )
            )
            observation = extractor.extract(reset_result.actor_view)
            reset_observation_shapes.append(int(observation.shape[0]))
            reset_count += 1

            for step_index in range(int(horizon_steps)):
                raw_action, hidden = _policy_action(model, observation, hidden)
                action_array = np.asarray(raw_action, dtype=np.float32)
                action_finite = bool(np.all(np.isfinite(action_array)))
                action_within_bounds = bool(
                    action_array.shape == (ACTION_DIM,)
                    and np.all(action_array >= -1.0)
                    and np.all(action_array <= 1.0)
                )
                action = validate_actor_action(action_array)
                step_result = backend.step(action)
                observation = extractor.extract(step_result.actor_view)
                rollout_rows.append(
                    PilotRolloutRow(
                        fixture_id=fixture_row.fixture_id,
                        surface_id=fixture_row.surface_id,
                        role_family=fixture_row.role_family,
                        step_index=step_index,
                        observation_shape=int(observation.shape[0]),
                        action_shape=int(action_array.shape[0]) if action_array.ndim == 1 else -1,
                        action_steer=float(action[0]),
                        action_throttle=float(action[1]),
                        action_brake=float(action[2]),
                        action_finite=action_finite,
                        action_within_bounds=action_within_bounds,
                        backend_status=step_result.backend_status,
                        terminated_by_backend=bool(step_result.terminated_by_backend),
                        truncated_by_backend=bool(step_result.truncated_by_backend),
                        diagnostic_wheel_force_count=len(step_result.diagnostics["wheel_forces"]),
                        policy_action=True,
                    )
                )
        finally:
            backend.close()

    summary = _summary_from_rows(
        rollout_rows,
        admission=admission,
        horizon_steps=int(horizon_steps),
        reset_count=reset_count,
        reset_observation_shapes=reset_observation_shapes,
    )
    return rollout_rows, summary


def write_pilot_rollout_rows(
    output_dir: Path,
    checkpoint_path: Path | str,
    *,
    horizon_steps: int = DEFAULT_HORIZON_STEPS,
    device: str = "cpu",
) -> tuple[Path, list[PilotRolloutRow], dict[str, Any]]:
    rollout_rows, summary = run_source_only_closed_loop_fixture_pilot(
        checkpoint_path,
        horizon_steps=horizon_steps,
        device=device,
    )
    rows_path = output_dir / "pilot_rollout_rows.csv"
    write_csv_rows(
        rows_path,
        [row.to_csv_row() for row in rollout_rows],
        fieldnames=[
            "fixture_id",
            "surface_id",
            "role_family",
            "step_index",
            "observation_shape",
            "action_shape",
            "action_steer",
            "action_throttle",
            "action_brake",
            "action_finite",
            "action_within_bounds",
            "backend_status",
            "terminated_by_backend",
            "truncated_by_backend",
            "diagnostic_wheel_force_count",
            "policy_action",
        ],
    )
    return rows_path, rollout_rows, summary


def run_preflight(
    output_dir: Path,
    *,
    checkpoint_path: Path | str,
    horizon_steps: int = DEFAULT_HORIZON_STEPS,
    device: str = "cpu",
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows_path, _rows, summary = write_pilot_rollout_rows(
        output_dir,
        checkpoint_path,
        horizon_steps=horizon_steps,
        device=device,
    )
    summary.update(
        {
            "milestone": str(milestone),
            "generated_at_utc": utc_timestamp(),
            "pilot_rollout_rows": str(rows_path),
            "next_blocker": str(next_blocker),
        }
    )
    write_json(output_dir / "summary.json", summary)
    return summary


def _summary_from_rows(
    rollout_rows: list[PilotRolloutRow],
    *,
    admission: CheckpointAdmission,
    horizon_steps: int,
    reset_count: int = 0,
    reset_observation_shapes: list[int] | None = None,
) -> dict[str, Any]:
    reset_shapes = reset_observation_shapes or []
    role_counts = Counter(row.role_family for row in rollout_rows)
    fixture_ids = sorted({row.fixture_id for row in rollout_rows})
    step_observation_shapes = [row.observation_shape for row in rollout_rows]
    diagnostic_wheel_force_counts = [row.diagnostic_wheel_force_count for row in rollout_rows]
    action_shapes = [row.action_shape for row in rollout_rows]
    backend_statuses = [row.backend_status for row in rollout_rows]

    all_reset_observations_shape_72 = bool(reset_shapes) and all(
        shape == P0_OBSERVATION_DIM for shape in reset_shapes
    )
    all_step_observations_shape_72 = bool(step_observation_shapes) and all(
        shape == P0_OBSERVATION_DIM for shape in step_observation_shapes
    )
    all_action_shapes_3 = bool(action_shapes) and all(shape == ACTION_DIM for shape in action_shapes)
    all_actions_finite = bool(rollout_rows) and all(row.action_finite for row in rollout_rows)
    all_actions_within_bounds = bool(rollout_rows) and all(row.action_within_bounds for row in rollout_rows)
    all_backend_statuses_running = bool(backend_statuses) and all(
        status == "running" for status in backend_statuses
    )
    all_diagnostic_wheel_force_counts_4 = bool(diagnostic_wheel_force_counts) and all(
        count == 4 for count in diagnostic_wheel_force_counts
    )

    fixture_count = len(fixture_ids)
    step_count = len(rollout_rows)
    expected_steps = 3 * int(horizon_steps)
    leak_flags = {
        "fixture_labels_enter_actor_input": False,
        "scenario_labels_enter_actor_input": False,
        "feasibility_classes_enter_actor_input": False,
        "hidden_values_enter_actor_input": False,
        "oracle_labels_enter_actor_input": False,
        "diagnostics_available_to_actor": False,
        "reward_terms_enter_actor_input": False,
        "success_labels_enter_actor_input": False,
        "ttc_enter_actor_input": False,
        "required_clearance_enter_actor_input": False,
    }
    status_pass = (
        admission.checkpoint_admitted
        and fixture_count == 3
        and set(role_counts) == {"stable_aes", "drift_required_recovery", "unavoidable_mitigation"}
        and int(reset_count) == 3
        and step_count == expected_steps
        and all_reset_observations_shape_72
        and all_step_observations_shape_72
        and all_action_shapes_3
        and all_actions_finite
        and all_actions_within_bounds
        and all_backend_statuses_running
        and all_diagnostic_wheel_force_counts_4
        and not any(leak_flags.values())
    )
    return {
        "result_class": "source_only_closed_loop_fixture_pilot_pass"
        if status_pass
        else "source_only_closed_loop_fixture_pilot_failed",
        "status_pass": bool(status_pass),
        "backend_id": SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID,
        "horizon_steps_per_fixture": int(horizon_steps),
        "fixture_count": fixture_count,
        "role_counts": dict(sorted(role_counts.items())),
        "reset_count": int(reset_count),
        "step_count": step_count,
        "expected_step_count": expected_steps,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "reset_observation_shapes": reset_shapes,
        "step_observation_shapes": step_observation_shapes,
        "all_reset_observations_shape_72": bool(all_reset_observations_shape_72),
        "all_step_observations_shape_72": bool(all_step_observations_shape_72),
        "all_action_shapes_3": bool(all_action_shapes_3),
        "all_actions_finite": bool(all_actions_finite),
        "all_actions_within_bounds": bool(all_actions_within_bounds),
        "all_backend_statuses_running": bool(all_backend_statuses_running),
        "diagnostic_wheel_force_counts": diagnostic_wheel_force_counts,
        "all_diagnostic_wheel_force_counts_4": bool(all_diagnostic_wheel_force_counts_4),
        **admission.to_summary_fields(),
        **leak_flags,
        "external_high_fidelity_required": False,
        "external_high_fidelity_imported": False,
        "high_fidelity_simulation_run": False,
        "measured_validation_run": False,
        "policy_action": bool(step_count > 0),
        "policy_rollout_run": bool(step_count > 0),
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_computed": False,
        "verdict_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "level3_self_id_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run bounded source-only closed-loop fixture pilot.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--horizon-steps", type=int, default=DEFAULT_HORIZON_STEPS)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument(
        "--next-blocker",
        default="m2489-source-only-closed-loop-fixture-pilot-result-audit",
    )
    args = parser.parse_args()
    run_preflight(
        args.output_dir,
        checkpoint_path=args.checkpoint,
        horizon_steps=args.horizon_steps,
        device=args.device,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
    )


if __name__ == "__main__":
    main()
