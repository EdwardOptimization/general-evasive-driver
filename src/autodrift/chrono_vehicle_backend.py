"""Project Chrono (pychrono) vehicle dynamics backend for the HF0 contract.

This module implements the ``DynamicsBackend`` protocol from
``autodrift.high_fidelity_interface`` on top of a pychrono wheeled-vehicle
model (Sedan, ~1684 kg, RWD, TMeasy handling tires) stepping at an internal
1 kHz rate with a 50 Hz control interface (dt = 0.02 s, 20 internal substeps
per control step), matching the AutoDrift control rate.

Design decisions (see docs/feasibility-route-hf-backend-2026-06.md):

- The fidelity upgrade is concentrated in the *vehicle dynamics* only. Road
  boundary features, obstacle slot features, off-track / collision / pass
  judgments and termination semantics reuse AutoDrift's analytic geometry
  (``autodrift.tasks.CircleTrack`` + the exact ``autodrift.env`` formulas),
  fed by the Chrono chassis pose/velocity. Task semantics are unchanged.
- Scenario hidden parameters are mapped where Chrono allows:
  mu -> flat-terrain friction coefficient (swappable at the friction step),
  mass -> chassis body mass override (total vehicle mass matched),
  drive/brake scale -> throttle/brake input scaling (clipped at 1.0),
  steer/drive tau + steer rate limit -> an AutoDrift-identical first-order
  actuator command filter in front of the Chrono driver inputs.
  Unmappable parameters are listed in ``KNOWN_DIFFERENCES``.
- Episodes start with a deterministic high-friction straight-line spin-up
  followed by an exact rigid teleport + rigid velocity-field boost onto the
  scenario's initial pose (x, y, psi, vx, vy, yaw_rate). This avoids the
  large cold-start driveline transient (~2 m/s speed loss) while keeping the
  multibody state internally consistent.

pychrono is imported lazily so that this module can be imported (for the
scenario helpers) in environments without pychrono installed. The backend
itself must run inside the pinned ``chrono`` conda environment
(pychrono 10.0.0, python 3.10).

This module is deterministic: no wall-clock, no unseeded RNG, and Chrono
itself was verified bitwise-deterministic for repeated identical episodes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np

from autodrift.high_fidelity_interface import (
    ACTION_DIM,
    ActorView,
    ActuatorView,
    BackendResetRequest,
    BackendResetResult,
    BackendStepResult,
    EgoView,
    ObstacleSlotView,
    OBSTACLE_SLOT_COUNT,
    P0ObservationExtractor,
    ROAD_LOOKAHEAD_COUNT,
    RoadView,
    validate_actor_action,
)
from autodrift.tasks import CircleTrack

BACKEND_ID = "chrono_sedan_tmeasy_hf_backend"
INTERNAL_STEP_S = 1e-3
SPINUP_TERRAIN_MU = 1.0
SPINUP_SETTLE_STEPS = 300  # 0.3 s suspension settle before throttle
SPINUP_MAX_STEPS = 40000  # 40 s simulated hard cap
INIT_CHASSIS_Z = 0.23  # near static ride height (measured equilibrium 0.2145)

# AutoDrift base actuator constants (autodrift.dynamics.VehicleParams defaults)
BASE_MAX_DRIVE_FORCE = 8200.0
BASE_MAX_BRAKE_FORCE = 6000.0


@dataclass(frozen=True)
class ChronoVehicleVariant:
    variant_id: str
    constructor_name: str
    tire_model: str = "TMEASY"
    init_chassis_z: float = INIT_CHASSIS_Z
    description: str = ""


DEFAULT_CHRONO_VEHICLE_VARIANT = "sedan_tmeasy"
CHRONO_VEHICLE_VARIANTS: dict[str, ChronoVehicleVariant] = {
    DEFAULT_CHRONO_VEHICLE_VARIANT: ChronoVehicleVariant(
        variant_id=DEFAULT_CHRONO_VEHICLE_VARIANT,
        constructor_name="Sedan",
        tire_model="TMEASY",
        init_chassis_z=INIT_CHASSIS_Z,
        description="Default HF4-preserving Chrono Sedan with TMeasy tires.",
    ),
    "bmw_e90_tmeasy": ChronoVehicleVariant(
        variant_id="bmw_e90_tmeasy",
        constructor_name="BMW_E90",
        tire_model="TMEASY",
        init_chassis_z=0.35,
        description="BMW_E90 wrapper smoke target for S4-HF-lite vehicle selection.",
    ),
    "uazbus_tmeasy": ChronoVehicleVariant(
        variant_id="uazbus_tmeasy",
        constructor_name="UAZBUS",
        tire_model="TMEASY",
        init_chassis_z=0.35,
        description="UAZBUS wrapper smoke target near the upper passenger-car mass envelope.",
    ),
}

KNOWN_DIFFERENCES = (
    "vehicle model: default Chrono Sedan (double wishbone / multilink, TMeasy tires, RWD, "
    "4-speed automatic) vs AutoDrift single-track analytic model; explicit S4-HF-lite "
    "smoke variants can select BMW_E90 or UAZBUS through scenario chrono_vehicle_variant",
    "total mass matched by chassis-mass override; inertia, CG height/shift and "
    "per-axle load split remain the selected Chrono vehicle's, so iz / cg_shift / inertia_scale "
    "hidden parameters are NOT mapped",
    "tire stiffness scales (cf/cr) NOT mapped (TMeasy parameters fixed by the "
    "Sedan tire JSON); effective grip at a given mu differs from mu*g "
    "(measured ~1.1-1.25x at full braking)",
    "drive_scale / brake_scale mapped multiplicatively onto throttle/brake "
    "inputs and clipped at 1.0, so scales > 1.0 saturate",
    "max steering angle: Chrono Sedan 0.4363 rad at full lock vs AutoDrift "
    "max_steer 0.62 rad; the normalized steer command maps full-scale to "
    "full lock, so the physical steer gain is ~0.70x",
    "steer/drive first-order lags + steer rate limit replicated exactly at the "
    "50 Hz control layer in front of the Chrono driver inputs; Chrono's own "
    "engine/transmission/brake dynamics act in addition (double shaping)",
    "initial state: pose and planar velocity (x, y, psi, vx, vy, yaw_rate) "
    "matched exactly at handoff after spin-up; suspension/driveline internal "
    "state is the spun-up straight-line state, not a curved steady state",
    "reset observation reports ax=ay=0 and zero actuator states (current-sim "
    "reports force-model accelerations at reset)",
    "ego acceleration channels are body-frame finite differences of vx/vy over "
    "the 0.02 s control step (current-sim uses instantaneous force-model "
    "accelerations)",
    "friction step changes terrain mu for the tires; AutoDrift additionally "
    "resamples speed_ref (reward-only, no actor/dynamics effect)",
    "AutoDrift aerodynamic drag/rolling resistance coefficients are not "
    "transferred; the selected Chrono vehicle's own drag and rolling resistance apply",
)


# ---------------------------------------------------------------------------
# Scenario helpers (importable without pychrono)
# ---------------------------------------------------------------------------

def smoke_scenario(seed: int, mu: float, *, max_steps: int = 360) -> dict[str, Any]:
    """Deterministic procedural smoke scenario mirroring AutoDriftEnv defaults."""

    rng = np.random.default_rng(int(seed))
    gravity = 9.81
    radius = 18.0
    friction_speed = math.sqrt(max(mu * gravity * radius, 1e-6))
    speed_low, speed_high = 5.0, 12.0
    speed_high = min(speed_high, friction_speed * 0.92)
    speed_ref = float(rng.uniform(speed_low, max(speed_high, speed_low + 1e-6)))
    beta = float(rng.normal(0.0, 0.04))
    angle = float(rng.uniform(-math.pi, math.pi))
    radial_noise = float(rng.normal(0.0, 0.3))
    x = (radius + radial_noise) * math.cos(angle)
    y = (radius + radial_noise) * math.sin(angle)
    tangent_heading = angle + math.pi / 2.0
    psi = tangent_heading - beta + float(rng.normal(0.0, 0.03))
    vx = speed_ref * math.cos(beta)
    vy = speed_ref * math.sin(beta)
    obstacle_distance = float(rng.uniform(20.0, 30.0))
    obstacle_half_width = float(rng.uniform(0.6, 1.0))
    tangent = (math.cos(tangent_heading), math.sin(tangent_heading))
    obstacle_x = x + tangent[0] * obstacle_distance
    obstacle_y = y + tangent[1] * obstacle_distance
    return {
        "scenario_id": f"chrono-smoke-seed{int(seed)}-mu{mu:g}",
        "dt": 0.02,
        "max_steps": int(max_steps),
        "track_kind": "circle",
        "track_radius": radius,
        "track_width": 5.0,
        "road_lookahead_count": ROAD_LOOKAHEAD_COUNT,
        "road_lookahead_spacing": 5.0,
        "obstacle_slots": OBSTACLE_SLOT_COUNT,
        "obstacle_relative_velocity_mode": "ego",
        "soft_offtrack_metric_enabled": False,
        "soft_offtrack_tolerance_m": 0.0,
        "params": {
            "mass": 1450.0,
            "mu": float(mu),
            "max_steer": 0.62,
            "max_steer_rate": 3.5,
            "max_drive_force": BASE_MAX_DRIVE_FORCE,
            "max_brake_force": BASE_MAX_BRAKE_FORCE,
            "drive_tau": 0.08,
            "steer_tau": 0.06,
        },
        "initial_state": {
            "x": x,
            "y": y,
            "psi": psi,
            "vx": vx,
            "vy": vy,
            "yaw_rate": speed_ref / radius,
        },
        "speed_ref": speed_ref,
        "obstacle": {
            "enabled": True,
            "x": obstacle_x,
            "y": obstacle_y,
            "half_width": obstacle_half_width,
            "ego_half_width": 0.90,
            "perception_reveal_step": 20,
            "perception_reveal_distance": None,
            "finish_on_pass": True,
            "finish_pass_distance": 2.0,
        },
        "warmup_gate": {"enabled": False},
        "friction_step": {"at": None, "new_mu": None},
        "terminate_on_failure": True,
    }


def scenario_from_env(env: Any, *, friction_step_new_mu: float | None = None) -> dict[str, Any]:
    """Snapshot a freshly-reset AutoDriftEnv into the backend scenario format.

    ``env`` must be an AutoDriftEnv (or wrapper exposing ``unwrapped``) right
    after ``reset(seed=...)``. The friction-step replacement mu cannot be read
    without consuming the env RNG draw, so the caller must supply it (consume
    the draw on a sacrificial reset of a second env instance).
    """

    e = getattr(env, "unwrapped", env)
    config = e.config
    if config.track_kind != "circle":
        raise ValueError(f"chrono backend supports track_kind=circle only, got {config.track_kind}")
    if config.friction_step.enabled and e.friction_step_at is not None and friction_step_new_mu is None:
        raise ValueError("friction step is armed; friction_step_new_mu must be provided")
    obstacle: dict[str, Any] = {"enabled": bool(config.obstacle.enabled)}
    if config.obstacle.enabled:
        if e.obstacle_scenario is None or e.obstacle_position is None:
            raise ValueError("obstacle enabled but not materialized after reset")
        obstacle.update(
            {
                "x": float(e.obstacle_position[0]),
                "y": float(e.obstacle_position[1]),
                "half_width": float(e.obstacle_scenario.obstacle_half_width),
                "ego_half_width": float(config.obstacle.ego_half_width),
                "perception_reveal_step": int(config.obstacle.perception_reveal_step),
                "perception_reveal_distance": (
                    None
                    if config.obstacle.perception_reveal_distance is None
                    else float(config.obstacle.perception_reveal_distance)
                ),
                "finish_on_pass": bool(config.obstacle.finish_on_pass),
                "finish_pass_distance": float(config.obstacle.finish_pass_distance),
                "label": str(e.obstacle_scenario.label),
            }
        )
    gate: dict[str, Any] = {"enabled": bool(config.warmup_gate.enabled and e.warmup_gate_position is not None)}
    if gate["enabled"]:
        gate.update(
            {
                "x": float(e.warmup_gate_position[0]),
                "y": float(e.warmup_gate_position[1]),
                "half_width": float(e.warmup_gate_half_width),
                "ego_half_width": float(config.obstacle.ego_half_width),
                "reveal_step": int(config.warmup_gate.reveal_step),
                "max_active_steps": int(config.warmup_gate.max_active_steps),
                "finish_pass_distance": float(config.warmup_gate.finish_pass_distance),
            }
        )
    return {
        "scenario_id": "from_env_reset",
        "dt": float(config.dt),
        "max_steps": int(config.max_steps),
        "track_kind": str(config.track_kind),
        "track_radius": float(config.track_radius),
        "track_width": float(config.track_width),
        "road_lookahead_count": int(config.road_lookahead_count),
        "road_lookahead_spacing": float(config.road_lookahead_spacing),
        "obstacle_slots": int(config.obstacle_slots),
        "obstacle_relative_velocity_mode": str(config.obstacle_relative_velocity_mode),
        "soft_offtrack_metric_enabled": bool(config.soft_offtrack_metric_enabled),
        "soft_offtrack_tolerance_m": float(config.soft_offtrack_tolerance_m),
        "params": {
            "mass": float(e.params.mass),
            "mu": float(e.params.mu),
            "max_steer": float(e.params.max_steer),
            "max_steer_rate": float(e.params.max_steer_rate),
            "max_drive_force": float(e.params.max_drive_force),
            "max_brake_force": float(e.params.max_brake_force),
            "drive_tau": float(e.params.drive_tau),
            "steer_tau": float(e.params.steer_tau),
            "iz": float(e.params.iz),
            "lf": float(e.params.lf),
            "lr": float(e.params.lr),
            "cf": float(e.params.cf),
            "cr": float(e.params.cr),
        },
        "initial_state": {
            "x": float(e.state.x),
            "y": float(e.state.y),
            "psi": float(e.state.psi),
            "vx": float(e.state.vx),
            "vy": float(e.state.vy),
            "yaw_rate": float(e.state.yaw_rate),
        },
        "speed_ref": float(e.speed_ref),
        "obstacle": obstacle,
        "warmup_gate": gate,
        "friction_step": {
            "at": None if e.friction_step_at is None else int(e.friction_step_at),
            "new_mu": None if friction_step_new_mu is None else float(friction_step_new_mu),
        },
        "terminate_on_failure": True,
    }


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _move_towards(value: float, target: float, max_delta: float) -> float:
    if target > value:
        return min(value + max_delta, target)
    return max(value - max_delta, target)


def _float_or_nan(value: Any) -> float:
    try:
        number = float(value)
    except Exception:
        return float("nan")
    return number if math.isfinite(number) else float("nan")


def _vec3_xyz(vector: Any) -> tuple[float, float, float]:
    return (
        _float_or_nan(getattr(vector, "x", float("nan"))),
        _float_or_nan(getattr(vector, "y", float("nan"))),
        _float_or_nan(getattr(vector, "z", float("nan"))),
    )


def _max_abs(rows: list[dict[str, Any]], key: str) -> float:
    values = [abs(value) for row in rows if math.isfinite(value := _float_or_nan(row.get(key, float("nan"))))]
    return max(values) if values else float("nan")


def _min_value(rows: list[dict[str, Any]], key: str) -> float:
    values = [value for row in rows if math.isfinite(value := _float_or_nan(row.get(key, float("nan"))))]
    return min(values) if values else float("nan")


def _max_value(rows: list[dict[str, Any]], key: str) -> float:
    values = [value for row in rows if math.isfinite(value := _float_or_nan(row.get(key, float("nan"))))]
    return max(values) if values else float("nan")


def _collect_tire_telemetry_from_vehicle(
    vehicle: Any,
    veh_module: Any,
    terrain: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Collect per-wheel tire truth from a Chrono vehicle without touching obs72."""

    axles = vehicle.GetAxles()
    axle_count = len(axles)
    sides = (("left", veh_module.LEFT), ("right", veh_module.RIGHT))
    rows: list[dict[str, Any]] = []
    for axle_index in range(axle_count):
        if axle_index == 0:
            axle_name = "front"
        elif axle_index == axle_count - 1:
            axle_name = "rear"
        else:
            axle_name = f"axle{axle_index}"
        for side_name, side_value in sides:
            tire = vehicle.GetTire(axle_index, side_value)
            wheel = vehicle.GetWheel(axle_index, side_value)
            force_report = tire.ReportTireForce(terrain)
            force_x, force_y, force_z = _vec3_xyz(force_report.force)
            wheel_state = wheel.GetState()
            local_force = wheel_state.rot.RotateBack(force_report.force)
            local_force_x, local_force_y, local_force_z = _vec3_xyz(local_force)
            row = {
                "axle_index": int(axle_index),
                "axle": axle_name,
                "side": side_name,
                "side_index": int(side_value),
                "slip_angle_rad": _float_or_nan(tire.GetSlipAngle()),
                "longitudinal_slip": _float_or_nan(tire.GetLongitudinalSlip()),
                "camber_angle_rad": _float_or_nan(tire.GetCamberAngle()),
                "tire_radius_m": _float_or_nan(tire.GetRadius()),
                "wheel_omega_rad_s": _float_or_nan(getattr(wheel_state, "omega", float("nan"))),
                "force_x_n": force_x,
                "force_y_n": force_y,
                "force_z_n": force_z,
                "local_force_x_n": local_force_x,
                "local_force_y_n": local_force_y,
                "local_force_z_n": local_force_z,
                "normal_load_n": abs(force_z),
            }
            rows.append(row)
    aggregate = {
        "tire_telemetry_available": bool(rows),
        "tire_telemetry_wheel_count": int(len(rows)),
        "tire_telemetry_force_frame": "global_report_force_plus_wheel_state_local_projection",
        "max_abs_tire_slip_angle_rad": _max_abs(rows, "slip_angle_rad"),
        "max_abs_tire_longitudinal_slip": _max_abs(rows, "longitudinal_slip"),
        "max_abs_tire_camber_angle_rad": _max_abs(rows, "camber_angle_rad"),
        "max_abs_tire_longitudinal_force_n": _max_abs(rows, "local_force_x_n"),
        "max_abs_tire_lateral_force_n": _max_abs(rows, "local_force_y_n"),
        "max_tire_normal_load_n": _max_value(rows, "normal_load_n"),
        "min_tire_normal_load_n": _min_value(rows, "normal_load_n"),
    }
    return rows, aggregate


class ChronoVehicleBackend:
    """HF dynamics backend: Chrono Sedan vehicle + AutoDrift task geometry."""

    backend_id = BACKEND_ID

    def __init__(self, *, internal_step: float = INTERNAL_STEP_S):
        import pychrono as chrono  # lazy: requires the pinned chrono env
        import pychrono.vehicle as veh

        self._chrono = chrono
        self._veh = veh
        veh.SetDataPath(chrono.GetChronoDataPath() + "vehicle/")
        self.internal_step = float(internal_step)
        self.dt = 0.02
        self.scenario: dict[str, Any] = {}
        self._car = None
        self._vehicle = None
        self._chassis_body = None
        self._terrain = None
        self._d_ref_local = None  # vehicle ref frame origin expressed in chassis COG frame
        self._time = 0.0
        self._extractor = P0ObservationExtractor()
        self.track: CircleTrack | None = None

    # -- DynamicsBackend protocol ------------------------------------------------

    def reset(self, request: BackendResetRequest) -> BackendResetResult:
        scenario = dict(request.options or {}).get("scenario")
        if not isinstance(scenario, Mapping):
            raise ValueError("BackendResetRequest.options['scenario'] dict is required")
        self.scenario = dict(scenario)
        self.dt = float(self.scenario["dt"])
        self._substeps = max(1, int(round(self.dt / self.internal_step)))
        self.track = CircleTrack(radius=float(self.scenario["track_radius"]))
        self._params = dict(self.scenario["params"])
        self._variant = self._resolve_vehicle_variant(self.scenario)
        self._drive_scale = float(self._params["max_drive_force"]) / BASE_MAX_DRIVE_FORCE
        self._brake_scale = float(self._params["max_brake_force"]) / BASE_MAX_BRAKE_FORCE

        spinup_report = self._build_and_handoff()

        # AutoDrift-equivalent bookkeeping (env.reset semantics)
        self.step_count = 0
        self.termination_reason = ""
        self.completion_reason = ""
        self.collision = False
        self.obstacle_completed = False
        self.obstacle_passed_raw = False
        self.min_obstacle_clearance = float("inf")
        self.max_off_track_overshoot = 0.0
        self.first_failure_events: list[dict[str, Any]] = []
        gate = self.scenario.get("warmup_gate") or {}
        self.gate_enabled = bool(gate.get("enabled"))
        self.gate_active = self.gate_enabled
        self.gate_passed = False
        self.gate_collision = False
        self.gate_min_clearance = float("inf")
        self.friction_step_applied = False
        self._mu_current = float(self._params["mu"])
        # actuator filter state (AutoDrift semantics: steer rad, drive force N)
        self._steer_state = 0.0
        self._drive_force_state = 0.0
        self._last_steer_rate = 0.0
        self._last_control = np.zeros(3, dtype=np.float64)
        x, y, psi, vx, vy, wz = self._read_chassis_planar_state()
        self._prev_vx = vx
        self._prev_vy = vy
        if self.gate_enabled:
            self._update_gate_status()
        if (self.scenario.get("obstacle") or {}).get("enabled"):
            self._update_obstacle_status()

        actor_view = self._actor_view(ax_body=0.0, ay_body=0.0)
        diagnostics = self._diagnostics()
        diagnostics["spinup"] = spinup_report
        backend_info = {
            "backend_id": self.backend_id,
            "reset_seed": request.seed,
            "scenario_spec_id": request.scenario_spec_id or str(self.scenario.get("scenario_id", "")),
            "role_family": request.role_family,
            "internal_step_s": self.internal_step,
            "substeps_per_control_step": self._substeps,
            "vehicle_total_mass": self._total_mass(),
            "target_mass": float(self._params["mass"]),
            "chrono_vehicle_variant": self._variant.variant_id,
            "chrono_vehicle_model": self._variant.constructor_name,
            "chrono_tire_model": self._variant.tire_model,
            "chrono_variant_description": self._variant.description,
            "chrono_base_vehicle_mass": float(self._base_vehicle_mass),
            "chrono_base_chassis_mass": float(self._base_chassis_mass),
            "chrono_max_steer_rad": float(self._vehicle.GetMaxSteeringAngle()),
            "chrono_wheelbase_m": self._chrono_wheelbase(),
            "chrono_wheeltrack_m": self._chrono_wheeltracks(),
            "chrono_chassis_inertia_xx_kgm2": self._chrono_chassis_inertia_xx(),
            "known_differences": list(KNOWN_DIFFERENCES),
        }
        return BackendResetResult(actor_view=actor_view, diagnostics=diagnostics, backend_info=backend_info)

    def step(self, action: np.ndarray) -> BackendStepResult:
        chrono = self._chrono
        veh = self._veh
        clipped = validate_actor_action(action)
        self.step_count += 1
        self._maybe_apply_friction_step()

        control = self._update_actuators(np.asarray(clipped, dtype=np.float64))

        inputs = veh.DriverInputs()
        inputs.m_steering = float(_clamp(self._steer_state / max(self._params["max_steer"], 1e-6), -1.0, 1.0))
        throttle_state, brake_state = self._drive_actuator_states()
        inputs.m_throttle = float(_clamp(throttle_state * self._drive_scale, 0.0, 1.0))
        inputs.m_braking = float(_clamp(brake_state * self._brake_scale, 0.0, 1.0))

        for _ in range(self._substeps):
            self._car.Synchronize(self._time, inputs, self._terrain)
            self._terrain.Synchronize(self._time)
            self._car.Advance(self.internal_step)
            self._terrain.Advance(self.internal_step)
            self._time += self.internal_step

        x, y, psi, vx, vy, wz = self._read_chassis_planar_state()
        ax_body = (vx - self._prev_vx) / self.dt
        ay_body = (vy - self._prev_vy) / self.dt
        self._prev_vx = vx
        self._prev_vy = vy
        self._last_control = control

        frame = self.track.frame(x, y, psi)
        if self.gate_enabled:
            self._update_gate_status()
        if (self.scenario.get("obstacle") or {}).get("enabled"):
            self._update_obstacle_status()
        overshoot = max(abs(frame.lateral_error) - float(self.scenario["track_width"]), 0.0)
        self.max_off_track_overshoot = max(self.max_off_track_overshoot, overshoot)

        self.termination_reason = self._termination_reason(frame, vx, vy, wz) or ""
        terminated = bool(self.termination_reason)
        self.obstacle_passed_raw = self._obstacle_completed_raw(frame)
        self.obstacle_completed = self.obstacle_passed_raw and not terminated
        truncated = self.obstacle_completed or self.step_count >= int(self.scenario["max_steps"])
        if self.obstacle_completed:
            self.completion_reason = "obstacle_pass"
        elif terminated:
            self.completion_reason = self.termination_reason
        elif truncated:
            self.completion_reason = "max_steps"
        else:
            self.completion_reason = ""

        if terminated and not bool(self.scenario.get("terminate_on_failure", True)):
            if not any(e["reason"] == self.termination_reason for e in self.first_failure_events):
                self.first_failure_events.append({"step": self.step_count, "reason": self.termination_reason})
            terminated = False

        actor_view = self._actor_view(ax_body=ax_body, ay_body=ay_body)
        diagnostics = self._diagnostics()
        return BackendStepResult(
            actor_view=actor_view,
            diagnostics=diagnostics,
            terminated_by_backend=terminated,
            truncated_by_backend=bool(truncated),
            backend_status=self.termination_reason or ("obstacle_pass" if self.obstacle_completed else "running"),
        )

    def close(self) -> None:
        self._car = None
        self._vehicle = None
        self._chassis_body = None
        self._terrain = None

    def observation(self, actor_view: ActorView) -> np.ndarray:
        return self._extractor.extract(actor_view)

    # -- Chrono construction / handoff --------------------------------------------

    def _resolve_vehicle_variant(self, scenario: Mapping[str, Any]) -> ChronoVehicleVariant:
        requested: Any = scenario.get("chrono_vehicle_variant", DEFAULT_CHRONO_VEHICLE_VARIANT)
        if isinstance(requested, Mapping):
            requested = requested.get("variant_id", requested.get("id", DEFAULT_CHRONO_VEHICLE_VARIANT))
        variant_id = str(requested or DEFAULT_CHRONO_VEHICLE_VARIANT)
        if variant_id not in CHRONO_VEHICLE_VARIANTS:
            allowed = ", ".join(sorted(CHRONO_VEHICLE_VARIANTS))
            raise ValueError(f"unknown chrono_vehicle_variant {variant_id!r}; allowed: {allowed}")
        return CHRONO_VEHICLE_VARIANTS[variant_id]

    def _tire_model_type(self):
        enum_name = f"TireModelType_{self._variant.tire_model.upper()}"
        if not hasattr(self._veh, enum_name):
            raise ValueError(f"chrono tire model {self._variant.tire_model!r} is not exposed as {enum_name}")
        return getattr(self._veh, enum_name)

    def _build_and_handoff(self) -> dict[str, Any]:
        chrono = self._chrono
        veh = self._veh
        init = self.scenario["initial_state"]
        target_speed = math.hypot(float(init["vx"]), float(init["vy"]))

        constructor = getattr(veh, self._variant.constructor_name)
        car = constructor()
        car.SetContactMethod(chrono.ChContactMethod_NSC)
        car.SetChassisFixed(False)
        car.SetChassisCollisionType(veh.CollisionType_NONE)
        car.SetInitPosition(
            chrono.ChCoordsysd(chrono.ChVector3d(0.0, 0.0, self._variant.init_chassis_z), chrono.QUNIT)
        )
        car.SetTireType(self._tire_model_type())
        car.SetTireStepSize(self.internal_step)
        car.Initialize()
        self._car = car
        self._vehicle = car.GetVehicle()
        self._chassis_body = self._vehicle.GetChassisBody()
        # constant: vehicle ref-frame origin in chassis COG frame (valid right after Initialize)
        ref_pos = self._vehicle.GetPos()
        cog_pos = self._chassis_body.GetPos()
        self._d_ref_local = self._chassis_body.GetRot().RotateBack(ref_pos - cog_pos)

        # mass mapping: match total vehicle mass via chassis body mass override
        target_mass = float(self._params["mass"])
        self._base_vehicle_mass = float(self._vehicle.GetMass())
        self._base_chassis_mass = float(self._chassis_body.GetMass())
        non_chassis = self._base_vehicle_mass - self._base_chassis_mass
        self._non_chassis_mass = non_chassis
        self._chassis_body.SetMass(max(target_mass - non_chassis, 50.0))

        # spin-up on high-friction terrain
        spin_terrain = veh.FlatTerrain(0.0, SPINUP_TERRAIN_MU)
        self._time = 0.0
        inputs = veh.DriverInputs()
        inputs.m_steering = 0.0
        inputs.m_throttle = 0.0
        inputs.m_braking = 0.0
        n = 0
        body = self._chassis_body
        while n < SPINUP_MAX_STEPS:
            if n >= SPINUP_SETTLE_STEPS:
                v_now = body.GetRot().RotateBack(body.GetPosDt()).x
                if v_now >= target_speed:
                    break
                inputs.m_throttle = float(_clamp(0.5 * (target_speed - v_now), 0.05, 0.85))
            self._car.Synchronize(self._time, inputs, spin_terrain)
            spin_terrain.Synchronize(self._time)
            self._car.Advance(self.internal_step)
            spin_terrain.Advance(self.internal_step)
            self._time += self.internal_step
            n += 1
        spinup_speed = float(body.GetRot().RotateBack(body.GetPosDt()).x)

        self._teleport_and_boost(
            x=float(init["x"]),
            y=float(init["y"]),
            psi=float(init["psi"]),
            vx=float(init["vx"]),
            vy=float(init["vy"]),
            yaw_rate=float(init["yaw_rate"]),
        )
        # scenario terrain at the scenario's initial mu
        self._terrain = veh.FlatTerrain(0.0, float(self._params["mu"]))
        return {
            "spinup_steps": n,
            "spinup_target_speed": target_speed,
            "spinup_achieved_speed": spinup_speed,
            "spinup_speed_gap": float(target_speed - spinup_speed),
        }

    def _teleport_and_boost(self, *, x: float, y: float, psi: float, vx: float, vy: float, yaw_rate: float) -> None:
        chrono = self._chrono
        body = self._chassis_body
        system = self._vehicle.GetSystem()
        bodies = list(system.GetBodies())

        e = body.GetRot().Rotate(chrono.ChVector3d(1.0, 0.0, 0.0))
        psi_cur = math.atan2(e.y, e.x)
        qd = chrono.QuatFromAngleZ(psi - psi_cur)
        ref_cur = body.GetPos() + body.GetRot().Rotate(self._d_ref_local)
        ref_tgt = chrono.ChVector3d(x, y, ref_cur.z)
        for b in bodies:
            rel = b.GetPos() - ref_cur
            b.SetPos(ref_tgt + qd.Rotate(rel))
            b.SetRot(qd * b.GetRot())
            b.SetPosDt(qd.Rotate(b.GetPosDt()))
            b.SetAngVelParent(qd.Rotate(b.GetAngVelParent()))
        # rigid velocity-field boost to exact target planar velocity + yaw rate
        rot_new = body.GetRot()
        v_des = rot_new.Rotate(chrono.ChVector3d(vx, vy, 0.0))
        v_cur = body.GetPosDt()
        dv = chrono.ChVector3d(v_des.x - v_cur.x, v_des.y - v_cur.y, 0.0)
        w_cur = body.GetAngVelParent()
        dw = chrono.ChVector3d(0.0, 0.0, yaw_rate - w_cur.z)
        pivot = body.GetPos()
        for b in bodies:
            r = b.GetPos() - pivot
            b.SetPosDt(b.GetPosDt() + dv + dw.Cross(r))
            b.SetAngVelParent(b.GetAngVelParent() + dw)

    def _total_mass(self) -> float:
        return float(self._chassis_body.GetMass()) + float(self._non_chassis_mass)

    def _chrono_wheelbase(self) -> float | None:
        try:
            return float(self._vehicle.GetWheelbase())
        except Exception:
            return None

    def _chrono_wheeltracks(self) -> list[float]:
        tracks: list[float] = []
        try:
            axles = self._vehicle.GetAxles()
        except Exception:
            return tracks
        for index in range(len(axles)):
            try:
                tracks.append(float(self._vehicle.GetWheeltrack(index)))
            except Exception:
                continue
        return tracks

    def _chrono_chassis_inertia_xx(self) -> list[float]:
        inertia = self._chassis_body.GetInertiaXX()
        return [float(inertia.x), float(inertia.y), float(inertia.z)]

    # -- state extraction ----------------------------------------------------------

    def _read_chassis_planar_state(self) -> tuple[float, float, float, float, float, float]:
        chrono = self._chrono
        body = self._chassis_body
        rot = body.GetRot()
        ref = body.GetPos() + rot.Rotate(self._d_ref_local)
        e = rot.Rotate(chrono.ChVector3d(1.0, 0.0, 0.0))
        psi = math.atan2(e.y, e.x)
        v_loc = rot.RotateBack(body.GetPosDt())
        wz = float(body.GetAngVelLocal().z)
        return float(ref.x), float(ref.y), float(psi), float(v_loc.x), float(v_loc.y), wz

    def _chassis_z(self) -> float:
        ref = self._chassis_body.GetPos() + self._chassis_body.GetRot().Rotate(self._d_ref_local)
        return float(ref.z)

    # -- AutoDrift actuator-layer replica (autodrift.dynamics.SingleTrackDriftModel.step) --

    def _update_actuators(self, action: np.ndarray) -> np.ndarray:
        p = self._params
        steer_cmd = _clamp(float(action[0]), -1.0, 1.0) * float(p["max_steer"])
        throttle_cmd = 0.5 * (_clamp(float(action[1]), -1.0, 1.0) + 1.0)
        brake_cmd = 0.5 * (_clamp(float(action[2]), -1.0, 1.0) + 1.0)

        dt = self.dt
        steer_rate_limit = float(p["max_steer_rate"]) * dt
        steer_lag_delta = _clamp(dt / max(float(p["steer_tau"]), dt), 0.0, 1.0)
        steer_target = self._steer_state + (steer_cmd - self._steer_state) * steer_lag_delta
        new_steer = _move_towards(self._steer_state, steer_target, steer_rate_limit)
        self._last_steer_rate = (new_steer - self._steer_state) / dt
        self._steer_state = new_steer

        force_target = throttle_cmd * float(p["max_drive_force"]) - brake_cmd * float(p["max_brake_force"])
        drive_alpha = _clamp(dt / max(float(p["drive_tau"]), dt), 0.0, 1.0)
        self._drive_force_state += (force_target - self._drive_force_state) * drive_alpha
        return np.array([_clamp(float(action[0]), -1.0, 1.0), throttle_cmd, brake_cmd], dtype=np.float64)

    def _drive_actuator_states(self) -> tuple[float, float]:
        if self._drive_force_state >= 0.0:
            return self._drive_force_state / max(float(self._params["max_drive_force"]), 1e-6), 0.0
        return 0.0, -self._drive_force_state / max(float(self._params["max_brake_force"]), 1e-6)

    # -- task semantics (exact autodrift.env replicas on the analytic geometry) ----

    def _maybe_apply_friction_step(self) -> None:
        fs = self.scenario.get("friction_step") or {}
        at = fs.get("at")
        if at is None or self.friction_step_applied or self.step_count < int(at):
            return
        new_mu = fs.get("new_mu")
        if new_mu is None:
            raise ValueError("friction step due but scenario has no new_mu")
        self._terrain = self._veh.FlatTerrain(0.0, float(new_mu))
        self._mu_current = float(new_mu)
        self.friction_step_applied = True

    def _body_point(self, px: float, py: float, x: float, y: float, psi: float) -> tuple[float, float]:
        dx = px - x
        dy = py - y
        c = math.cos(psi)
        s = math.sin(psi)
        return c * dx + s * dy, -s * dx + c * dy

    def _update_obstacle_status(self) -> None:
        ob = self.scenario.get("obstacle") or {}
        if not ob.get("enabled"):
            return
        x, y, _, _, _, _ = self._read_chassis_planar_state()
        clearance = math.hypot(float(ob["x"]) - x, float(ob["y"]) - y)
        self.min_obstacle_clearance = min(self.min_obstacle_clearance, clearance)
        collision_radius = float(ob["ego_half_width"]) + float(ob["half_width"])
        self.collision = clearance <= collision_radius

    def _update_gate_status(self) -> None:
        gate = self.scenario.get("warmup_gate") or {}
        if not self.gate_enabled:
            return
        x, y, psi, _, _, _ = self._read_chassis_planar_state()
        clearance = math.hypot(float(gate["x"]) - x, float(gate["y"]) - y)
        self.gate_min_clearance = min(self.gate_min_clearance, clearance)
        collision_radius = float(gate["ego_half_width"]) + float(gate["half_width"])
        self.gate_collision = clearance <= collision_radius
        frame = self.track.frame(x, y, psi)
        longitudinal = (float(gate["x"]) - x) * frame.tangent[0] + (float(gate["y"]) - y) * frame.tangent[1]
        if longitudinal <= -float(gate["finish_pass_distance"]):
            self.gate_passed = True
            self.gate_active = False
        elif self.step_count >= int(gate["max_active_steps"]):
            self.gate_active = False

    def _gate_visible(self) -> bool:
        gate = self.scenario.get("warmup_gate") or {}
        return bool(self.gate_enabled and self.gate_active and self.step_count >= int(gate.get("reveal_step", 0)))

    def _obstacle_longitudinal(self, frame, x: float, y: float) -> float:
        ob = self.scenario.get("obstacle") or {}
        if not ob.get("enabled"):
            return float("inf")
        return (float(ob["x"]) - x) * frame.tangent[0] + (float(ob["y"]) - y) * frame.tangent[1]

    def _obstacle_visible(self, longitudinal: float) -> bool:
        ob = self.scenario.get("obstacle") or {}
        if not ob.get("enabled"):
            return False
        if self.step_count < int(ob.get("perception_reveal_step", 0)):
            return False
        reveal_distance = ob.get("perception_reveal_distance")
        if reveal_distance is not None and longitudinal > float(reveal_distance):
            return False
        return True

    def _active_obstacle_slot(self, frame, x: float, y: float) -> tuple[str, float, float, float]:
        """Returns (kind, world_x, world_y, half_width) mirroring _active_obstacle_slot_geometry."""

        gate = self.scenario.get("warmup_gate") or {}
        if self._gate_visible():
            return "warmup_gate", float(gate["x"]), float(gate["y"]), float(gate["half_width"])
        ob = self.scenario.get("obstacle") or {}
        if ob.get("enabled"):
            longitudinal_body = self._body_point(float(ob["x"]), float(ob["y"]), x, y, self._last_psi)[0]
            if self._obstacle_visible(longitudinal_body):
                return "emergency_obstacle", float(ob["x"]), float(ob["y"]), float(ob["half_width"])
        return "none", float("nan"), float("nan"), float("nan")

    def _termination_reason(self, frame, vx: float, vy: float, wz: float) -> str | None:
        speed = math.hypot(vx, vy)
        values = (frame.lateral_error, vx, vy, wz)
        if not all(math.isfinite(v) for v in values):
            return "non_finite_state"
        overshoot = max(abs(frame.lateral_error) - float(self.scenario["track_width"]), 0.0)
        if bool(self.scenario.get("soft_offtrack_metric_enabled")):
            if overshoot > float(self.scenario.get("soft_offtrack_tolerance_m", 0.0)):
                return "off_track"
        elif overshoot > 0.0:
            return "off_track"
        if self.collision:
            return "obstacle_collision"
        if speed < 1.0:
            return "speed_too_low"
        if speed > 32.0:
            return "speed_too_high"
        if abs(wz) > 6.0:
            return "yaw_rate_limit"
        return None

    def _obstacle_completed_raw(self, frame) -> bool:
        ob = self.scenario.get("obstacle") or {}
        if not ob.get("enabled") or not ob.get("finish_on_pass"):
            return False
        x, y, _, _, _, _ = self._read_chassis_planar_state()
        return self._obstacle_longitudinal(frame, x, y) <= -float(ob["finish_pass_distance"])

    # -- actor view ------------------------------------------------------------------

    def _actor_view(self, *, ax_body: float, ay_body: float) -> ActorView:
        x, y, psi, vx, vy, wz = self._read_chassis_planar_state()
        self._last_psi = psi
        p = self._params

        spacing = float(self.scenario["road_lookahead_spacing"])
        count = int(self.scenario["road_lookahead_count"])
        distances = spacing * np.arange(1, count + 1)
        center_points, tangents = self.track.lookahead_centerline(x, y, distances)
        half_width = 0.5 * float(self.scenario["track_width"])
        left_points = []
        right_points = []
        for point, tangent in zip(center_points, tangents):
            normal_left = (-tangent[1], tangent[0])
            left_points.append(
                self._body_point(point[0] + normal_left[0] * half_width, point[1] + normal_left[1] * half_width, x, y, psi)
            )
            right_points.append(
                self._body_point(point[0] - normal_left[0] * half_width, point[1] - normal_left[1] * half_width, x, y, psi)
            )

        frame = self.track.frame(x, y, psi)
        slots: list[ObstacleSlotView] = []
        kind, ox, oy, ohw = self._active_obstacle_slot(frame, x, y)
        if kind != "none" and math.isfinite(ohw):
            bx, by = self._body_point(ox, oy, x, y, psi)
            if str(self.scenario.get("obstacle_relative_velocity_mode", "ego")) == "ego":
                rel_vx = -vx + wz * by
                rel_vy = -vy - wz * bx
            else:
                rel_vx = 0.0
                rel_vy = 0.0
            slots.append(
                ObstacleSlotView(
                    present=1.0,
                    x_body=float(bx),
                    y_body=float(by),
                    vx_body=float(rel_vx),
                    vy_body=float(rel_vy),
                    half_width=float(ohw),
                    half_length=float(ohw),
                )
            )
        while len(slots) < int(self.scenario["obstacle_slots"]):
            slots.append(ObstacleSlotView(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))

        throttle_state, brake_state = self._drive_actuator_states()
        return ActorView(
            dt=self.dt,
            step_index=self.step_count,
            ego=EgoView(
                x=x,
                y=y,
                psi=psi,
                vx_body=vx,
                vy_body=vy,
                yaw_rate=wz,
                ax_body=float(ax_body),
                ay_body=float(ay_body),
            ),
            actuators=ActuatorView(
                steer_angle_normalized=float(self._steer_state / max(float(p["max_steer"]), 1e-6)),
                steer_rate_normalized=float(self._last_steer_rate / max(float(p["max_steer_rate"]), 1e-6)),
                throttle_state=float(throttle_state),
                brake_state=float(brake_state),
                previous_steer_command=float(self._last_control[0]),
                previous_throttle_command=float(self._last_control[1]),
                previous_brake_command=float(self._last_control[2]),
            ),
            road=RoadView(
                left_boundary_points_body=tuple((float(a), float(b)) for a, b in left_points),
                right_boundary_points_body=tuple((float(a), float(b)) for a, b in right_points),
            ),
            obstacles=tuple(slots),
        )

    def _diagnostics(self) -> dict[str, Any]:
        x, y, psi, vx, vy, wz = self._read_chassis_planar_state()
        frame = self.track.frame(x, y, psi)
        ob = self.scenario.get("obstacle") or {}
        collision_radius = (
            float(ob["ego_half_width"]) + float(ob["half_width"]) if ob.get("enabled") else float("nan")
        )
        min_clearance_margin = (
            float(self.min_obstacle_clearance - collision_radius) if ob.get("enabled") else float("nan")
        )
        try:
            tire_telemetry, tire_aggregates = _collect_tire_telemetry_from_vehicle(
                self._vehicle,
                self._veh,
                self._terrain,
            )
            tire_error = ""
        except Exception as exc:
            tire_telemetry = []
            tire_aggregates = {
                "tire_telemetry_available": False,
                "tire_telemetry_wheel_count": 0,
                "tire_telemetry_force_frame": "",
                "max_abs_tire_slip_angle_rad": float("nan"),
                "max_abs_tire_longitudinal_slip": float("nan"),
                "max_abs_tire_camber_angle_rad": float("nan"),
                "max_abs_tire_longitudinal_force_n": float("nan"),
                "max_abs_tire_lateral_force_n": float("nan"),
                "max_tire_normal_load_n": float("nan"),
                "min_tire_normal_load_n": float("nan"),
            }
            tire_error = f"{type(exc).__name__}: {exc}"
        diagnostics = {
            "backend_id": self.backend_id,
            "step": int(self.step_count),
            "mu": float(self._mu_current),
            "x": x,
            "y": y,
            "psi": psi,
            "z": self._chassis_z(),
            "vx_body": vx,
            "vy_body": vy,
            "yaw_rate": wz,
            "speed": math.hypot(vx, vy),
            "lateral_error": float(frame.lateral_error),
            "heading_error": float(frame.heading_error),
            "off_track_overshoot": max(abs(frame.lateral_error) - float(self.scenario["track_width"]), 0.0),
            "max_off_track_overshoot": float(self.max_off_track_overshoot),
            "collision": bool(self.collision),
            "obstacle_completed": bool(self.obstacle_completed),
            "obstacle_passed_raw": bool(self.obstacle_passed_raw),
            "min_obstacle_clearance": float(self.min_obstacle_clearance),
            "min_clearance_margin": min_clearance_margin,
            "obstacle_longitudinal": float(self._obstacle_longitudinal(frame, x, y)),
            "termination_reason": str(self.termination_reason),
            "completion_reason": str(self.completion_reason),
            "friction_step_applied": bool(self.friction_step_applied),
            "warmup_gate_active": bool(self.gate_active),
            "warmup_gate_passed": bool(self.gate_passed),
            "warmup_gate_collision": bool(self.gate_collision),
            "failure_events": list(self.first_failure_events),
            "throttle_input": float(_clamp(self._drive_actuator_states()[0] * self._drive_scale, 0.0, 1.0)),
            "brake_input": float(_clamp(self._drive_actuator_states()[1] * self._brake_scale, 0.0, 1.0)),
            "tire_telemetry": tire_telemetry,
            "tire_telemetry_error": tire_error,
        }
        diagnostics.update(tire_aggregates)
        return diagnostics
