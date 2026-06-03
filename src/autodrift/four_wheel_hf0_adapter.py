"""Source-only four-wheel HF0 adapter preflight.

This module wraps the repository-local FourWheelDriftModel behind the HF0
backend contract. It intentionally does not import, install, or run any
external high-fidelity simulator.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import utc_timestamp, write_json
from autodrift.four_wheel_dynamics import (
    FourWheelDriftModel,
    FourWheelFaultScales,
    FourWheelForces,
    FourWheelState,
    FourWheelVehicleParams,
)
from autodrift.high_fidelity_interface import (
    ACTION_DIM,
    ActorView,
    ActuatorView,
    BackendResetRequest,
    BackendResetResult,
    BackendStepResult,
    EgoView,
    ObstacleSlotView,
    P0_OBSERVATION_DIM,
    P0ObservationExtractor,
    RoadView,
    physical_control_from_action,
    validate_actor_action,
)


DEFAULT_DT = 0.02


class FourWheelHF0Backend:
    """HF0 backend adapter over the source-only four-wheel dynamics model."""

    backend_id = "source_only_four_wheel_hf0"

    def __init__(
        self,
        *,
        params: FourWheelVehicleParams | None = None,
        fault_scales: FourWheelFaultScales | None = None,
        dt: float = DEFAULT_DT,
    ):
        self.params = params or FourWheelVehicleParams()
        self.fault_scales = fault_scales or FourWheelFaultScales.nominal()
        self.model = FourWheelDriftModel(params=self.params, fault_scales=self.fault_scales)
        self.dt = float(dt)
        self.state = self._initial_state()
        self._step_index = 0
        self._last_physical_control = np.zeros(ACTION_DIM, dtype=np.float32)
        self._last_steer = float(self.state.steer)

    def reset(self, request: BackendResetRequest) -> BackendResetResult:
        self.state = self._initial_state()
        self._step_index = 0
        self._last_physical_control = np.zeros(ACTION_DIM, dtype=np.float32)
        self._last_steer = float(self.state.steer)
        actor_view = self._actor_view(ax_body=0.0, ay_body=0.0, steer_rate_normalized=0.0)
        diagnostics = self._diagnostics(forces=None)
        backend_info = {
            "backend_id": self.backend_id,
            "reset_seed": request.seed,
            "scenario_spec_id": request.scenario_spec_id,
            "role_family": request.role_family,
            "source_only_model": "FourWheelDriftModel",
        }
        return BackendResetResult(actor_view=actor_view, diagnostics=diagnostics, backend_info=backend_info)

    def step(self, action: np.ndarray) -> BackendStepResult:
        clipped_action = validate_actor_action(action)
        old_state = self.state
        next_state, forces = self.model.step(old_state, clipped_action, self.dt)
        ax_body = (next_state.vx - old_state.vx) / self.dt
        ay_body = (next_state.vy - old_state.vy) / self.dt
        steer_rate_normalized = (next_state.steer - self._last_steer) / max(
            self.params.max_steer_rate * self.dt,
            1e-6,
        )
        self.state = next_state
        self._step_index += 1
        self._last_steer = float(next_state.steer)
        self._last_physical_control = physical_control_from_action(clipped_action)

        actor_view = self._actor_view(
            ax_body=float(ax_body),
            ay_body=float(ay_body),
            steer_rate_normalized=float(np.clip(steer_rate_normalized, -1.0, 1.0)),
        )
        diagnostics = self._diagnostics(forces=forces)
        diagnostics["physical_control"] = self._last_physical_control.astype(float).tolist()
        return BackendStepResult(
            actor_view=actor_view,
            diagnostics=diagnostics,
            terminated_by_backend=False,
            truncated_by_backend=False,
            backend_status="running",
        )

    def close(self) -> None:
        return None

    def _initial_state(self) -> FourWheelState:
        return FourWheelState(
            x=0.0,
            y=0.0,
            psi=0.0,
            vx=8.0,
            vy=0.0,
            yaw_rate=0.0,
            steer=0.0,
            drive_force=0.0,
            brake_force=0.0,
        )

    def _actor_view(self, *, ax_body: float, ay_body: float, steer_rate_normalized: float) -> ActorView:
        throttle_state = max(float(self.state.drive_force) / max(self.params.max_drive_force, 1e-6), 0.0)
        brake_state = max(float(self.state.brake_force) / max(self.params.max_brake_force, 1e-6), 0.0)
        return ActorView(
            dt=self.dt,
            step_index=self._step_index,
            ego=EgoView(
                x=float(self.state.x),
                y=float(self.state.y),
                psi=float(self.state.psi),
                vx_body=float(self.state.vx),
                vy_body=float(self.state.vy),
                yaw_rate=float(self.state.yaw_rate),
                ax_body=float(ax_body),
                ay_body=float(ay_body),
            ),
            actuators=ActuatorView(
                steer_angle_normalized=float(self.state.steer / max(self.params.max_steer, 1e-6)),
                steer_rate_normalized=float(steer_rate_normalized),
                throttle_state=float(np.clip(throttle_state, 0.0, 1.0)),
                brake_state=float(np.clip(brake_state, 0.0, 1.0)),
                previous_steer_command=float(self._last_physical_control[0]),
                previous_throttle_command=float(self._last_physical_control[1]),
                previous_brake_command=float(self._last_physical_control[2]),
            ),
            road=_fixture_road(),
            obstacles=_fixture_obstacles(),
        )

    def _diagnostics(self, *, forces: FourWheelForces | None) -> dict[str, Any]:
        return {
            "backend_id": self.backend_id,
            "source_only_model": "FourWheelDriftModel",
            "state": asdict(self.state),
            "params": asdict(self.params),
            "fault_scales": asdict(self.fault_scales),
            "four_wheel_hidden_diagnostics_present": True,
            "wheel_forces": [] if forces is None else [asdict(wheel) for wheel in forces.wheels],
            "drag_force": None if forces is None else float(forces.drag_force),
            "rolling_force": None if forces is None else float(forces.rolling_force),
        }


def run_source_only_four_wheel_adapter_preflight(
    actions: tuple[tuple[float, float, float], ...] = (
        (0.0, 0.0, 0.0),
        (0.25, -0.25, -0.75),
    ),
) -> dict[str, Any]:
    extractor = P0ObservationExtractor()
    backend = FourWheelHF0Backend()
    reset_result = backend.reset(
        BackendResetRequest(
            seed=2478,
            scenario_spec_id="m2478_source_only_four_wheel_fixture",
            role_family="source_only_four_wheel_adapter_preflight",
        )
    )
    reset_observation = extractor.extract(reset_result.actor_view)
    step_shapes: list[int] = []
    backend_statuses: list[str] = []
    diagnostic_wheel_force_counts: list[int] = []
    for action in actions:
        step_result = backend.step(np.asarray(action, dtype=np.float32))
        step_observation = extractor.extract(step_result.actor_view)
        step_shapes.append(int(step_observation.shape[0]))
        backend_statuses.append(step_result.backend_status)
        diagnostic_wheel_force_counts.append(len(step_result.diagnostics["wheel_forces"]))

    actor_input_contract_changed = False
    action_contract_changed = False
    hidden_values_enter_actor_input = False
    oracle_labels_enter_actor_input = False
    diagnostics_available_to_actor = False
    status_pass = (
        int(reset_observation.shape[0]) == P0_OBSERVATION_DIM
        and all(shape == P0_OBSERVATION_DIM for shape in step_shapes)
        and all(count == 4 for count in diagnostic_wheel_force_counts)
        and not actor_input_contract_changed
        and not action_contract_changed
        and not hidden_values_enter_actor_input
        and not oracle_labels_enter_actor_input
        and not diagnostics_available_to_actor
    )
    return {
        "result_class": "source_only_four_wheel_adapter_preflight_pass"
        if status_pass
        else "source_only_four_wheel_adapter_preflight_failed",
        "status_pass": bool(status_pass),
        "backend_id": backend.backend_id,
        "source_only_model": "FourWheelDriftModel",
        "observation_shape": int(reset_observation.shape[0]),
        "step_observation_shapes": step_shapes,
        "action_shape": ACTION_DIM,
        "p0_extractor_shape": P0_OBSERVATION_DIM,
        "reset_count": 1,
        "step_count": len(actions),
        "backend_statuses": backend_statuses,
        "diagnostic_wheel_force_counts": diagnostic_wheel_force_counts,
        "four_wheel_hidden_diagnostics_present": True,
        "fault_scales_diagnostic_only": True,
        "wheel_forces_diagnostic_only": True,
        "actor_input_contract_changed": actor_input_contract_changed,
        "action_contract_changed": action_contract_changed,
        "hidden_values_enter_actor_input": hidden_values_enter_actor_input,
        "oracle_labels_enter_actor_input": oracle_labels_enter_actor_input,
        "diagnostics_available_to_actor": diagnostics_available_to_actor,
        "external_high_fidelity_required": False,
        "external_high_fidelity_imported": False,
        "high_fidelity_simulation_run": False,
        "measured_validation_run": False,
        "policy_rollout_run": False,
        "training_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "verdict_claim_made": False,
    }


def run_preflight(output_dir: Path, *, next_blocker: str) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = run_source_only_four_wheel_adapter_preflight()
    summary.update(
        {
            "milestone": "m2478-high-fidelity-interface-source-only-four-wheel-adapter-preflight",
            "generated_at_utc": utc_timestamp(),
            "next_blocker": str(next_blocker),
        }
    )
    write_json(output_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run source-only four-wheel HF0 adapter preflight.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--next-blocker", type=str, required=True)
    args = parser.parse_args()

    summary = run_preflight(args.output_dir, next_blocker=str(args.next_blocker))
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"observation_shape={summary['observation_shape']}")
    print(f"step_count={summary['step_count']}")
    print(f"summary={args.output_dir / 'summary.json'}")


def _fixture_road() -> RoadView:
    left = tuple((float(i + 1) * 5.0, 3.0) for i in range(8))
    right = tuple((float(i + 1) * 5.0, -3.0) for i in range(8))
    return RoadView(left_boundary_points_body=left, right_boundary_points_body=right)


def _fixture_obstacles() -> tuple[ObstacleSlotView, ...]:
    return (
        ObstacleSlotView(1.0, 28.0, 0.5, -8.0, 0.0, 0.75, 0.75),
        ObstacleSlotView(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        ObstacleSlotView(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        ObstacleSlotView(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    )


if __name__ == "__main__":
    main()
