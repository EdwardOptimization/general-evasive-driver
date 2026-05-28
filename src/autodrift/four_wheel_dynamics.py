"""Source-only four-wheel vehicle dynamics primitives for asymmetric fault mining.

This module is intentionally compact. It is not a high-fidelity vehicle engine
and it does not replace the main Gym environment. Its purpose is to expose the
left-right force channel missing from the single-track source miners so later
milestones can construct per-wheel fault source candidates.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from autodrift.dynamics import VehicleParams
from autodrift.math_utils import clamp, move_towards


WHEEL_NAMES = ("front_left", "front_right", "rear_left", "rear_right")


@dataclass(frozen=True)
class FourWheelVehicleParams:
    mass: float = 1450.0
    iz: float = 2300.0
    lf: float = 1.35
    lr: float = 1.45
    track_width: float = 1.62
    h_cg: float = 0.52
    mu: float = 0.9
    cf: float = 95000.0
    cr: float = 110000.0
    max_steer: float = 0.62
    max_steer_rate: float = 3.5
    max_drive_force: float = 8200.0
    max_brake_force: float = 6000.0
    front_brake_bias: float = 0.62
    drive_tau: float = 0.08
    brake_tau: float = 0.06
    steer_tau: float = 0.06
    drag_coeff: float = 0.34
    rolling_resistance: float = 75.0
    gravity: float = 9.81

    @classmethod
    def from_single_track(cls, params: VehicleParams) -> "FourWheelVehicleParams":
        return cls(
            mass=params.mass,
            iz=params.iz,
            lf=params.lf,
            lr=params.lr,
            h_cg=params.h_cg,
            mu=params.mu,
            cf=params.cf,
            cr=params.cr,
            max_steer=params.max_steer,
            max_steer_rate=params.max_steer_rate,
            max_drive_force=params.max_drive_force,
            max_brake_force=params.max_brake_force,
            drive_tau=params.drive_tau,
            brake_tau=params.drive_tau,
            steer_tau=params.steer_tau,
            drag_coeff=params.drag_coeff,
            rolling_resistance=params.rolling_resistance,
            gravity=params.gravity,
        )

    @property
    def wheelbase(self) -> float:
        return self.lf + self.lr

    @property
    def static_front_load(self) -> float:
        return self.mass * self.gravity * self.lr / self.wheelbase

    @property
    def static_rear_load(self) -> float:
        return self.mass * self.gravity * self.lf / self.wheelbase


@dataclass(frozen=True)
class FourWheelFaultScales:
    mu: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    lateral_stiffness: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    brake: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    drive: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    longitudinal_drag: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)

    @staticmethod
    def nominal() -> "FourWheelFaultScales":
        return FourWheelFaultScales()

    @staticmethod
    def split_mu(*, left_scale: float, right_scale: float) -> "FourWheelFaultScales":
        return FourWheelFaultScales(
            mu=(float(left_scale), float(right_scale), float(left_scale), float(right_scale))
        )

    @staticmethod
    def uniform_grip(
        *,
        mu_scale: float,
        lateral_stiffness_scale: float | None = None,
    ) -> "FourWheelFaultScales":
        lateral = float(lateral_stiffness_scale if lateral_stiffness_scale is not None else mu_scale)
        return FourWheelFaultScales(
            mu=(float(mu_scale), float(mu_scale), float(mu_scale), float(mu_scale)),
            lateral_stiffness=(lateral, lateral, lateral, lateral),
        )

    @staticmethod
    def single_wheel_grip_collapse(
        wheel: str,
        *,
        mu_scale: float,
        lateral_stiffness_scale: float | None = None,
    ) -> "FourWheelFaultScales":
        index = _wheel_index(wheel)
        mu = [1.0, 1.0, 1.0, 1.0]
        lateral = [1.0, 1.0, 1.0, 1.0]
        mu[index] = float(mu_scale)
        lateral[index] = float(lateral_stiffness_scale if lateral_stiffness_scale is not None else mu_scale)
        return FourWheelFaultScales(mu=tuple(mu), lateral_stiffness=tuple(lateral))

    @staticmethod
    def single_wheel_brake_pull(wheel: str, *, brake_scale: float) -> "FourWheelFaultScales":
        index = _wheel_index(wheel)
        brake = [1.0, 1.0, 1.0, 1.0]
        brake[index] = float(brake_scale)
        return FourWheelFaultScales(brake=tuple(brake))

    @staticmethod
    def halfshaft_torque_loss(wheel: str, *, drive_scale: float) -> "FourWheelFaultScales":
        index = _wheel_index(wheel)
        drive = [1.0, 1.0, 1.0, 1.0]
        drive[index] = float(drive_scale)
        return FourWheelFaultScales(drive=tuple(drive))

    @staticmethod
    def tire_blowout_like(
        wheel: str,
        *,
        mu_scale: float,
        lateral_stiffness_scale: float,
        drag_force: float,
    ) -> "FourWheelFaultScales":
        index = _wheel_index(wheel)
        mu = [1.0, 1.0, 1.0, 1.0]
        lateral = [1.0, 1.0, 1.0, 1.0]
        drag = [0.0, 0.0, 0.0, 0.0]
        mu[index] = float(mu_scale)
        lateral[index] = float(lateral_stiffness_scale)
        drag[index] = float(drag_force)
        return FourWheelFaultScales(
            mu=tuple(mu),
            lateral_stiffness=tuple(lateral),
            longitudinal_drag=tuple(drag),
        )


@dataclass
class FourWheelState:
    x: float
    y: float
    psi: float
    vx: float
    vy: float
    yaw_rate: float
    steer: float = 0.0
    drive_force: float = 0.0
    brake_force: float = 0.0

    def as_array(self) -> np.ndarray:
        return np.array(
            [
                self.x,
                self.y,
                self.psi,
                self.vx,
                self.vy,
                self.yaw_rate,
                self.steer,
                self.drive_force,
                self.brake_force,
            ],
            dtype=np.float64,
        )

    @classmethod
    def from_array(cls, values: np.ndarray) -> "FourWheelState":
        return cls(*(float(v) for v in values))


@dataclass(frozen=True)
class WheelForce:
    name: str
    x: float
    y: float
    steer: float
    fx_body: float
    fy_body: float
    fx_wheel: float
    fy_wheel: float
    fz: float
    mu_capacity: float
    alpha: float

    @property
    def yaw_moment(self) -> float:
        return self.x * self.fy_body - self.y * self.fx_body


@dataclass(frozen=True)
class FourWheelForces:
    wheels: tuple[WheelForce, WheelForce, WheelForce, WheelForce]
    drag_force: float
    rolling_force: float

    @property
    def total_fx(self) -> float:
        return float(sum(wheel.fx_body for wheel in self.wheels) - self.drag_force - self.rolling_force)

    @property
    def total_fy(self) -> float:
        return float(sum(wheel.fy_body for wheel in self.wheels))

    @property
    def yaw_moment(self) -> float:
        return float(sum(wheel.yaw_moment for wheel in self.wheels))

    def wheel(self, name: str) -> WheelForce:
        for wheel in self.wheels:
            if wheel.name == name:
                return wheel
        raise KeyError(name)


class FourWheelDriftModel:
    """Compact four-contact-patch model for source-fault experiments."""

    def __init__(
        self,
        params: FourWheelVehicleParams | None = None,
        fault_scales: FourWheelFaultScales | None = None,
    ):
        self.params = params or FourWheelVehicleParams()
        self.fault_scales = fault_scales or FourWheelFaultScales.nominal()

    def step(self, state: FourWheelState, action: np.ndarray, dt: float) -> tuple[FourWheelState, FourWheelForces]:
        action = np.asarray(action, dtype=np.float64)
        if action.shape != (3,):
            raise ValueError(f"expected action shape (3,), got {action.shape}")
        p = self.params
        steer_cmd = clamp(float(action[0]), -1.0, 1.0) * p.max_steer
        throttle_cmd = 0.5 * (clamp(float(action[1]), -1.0, 1.0) + 1.0)
        brake_cmd = 0.5 * (clamp(float(action[2]), -1.0, 1.0) + 1.0)

        steer_rate_limit = p.max_steer_rate * dt
        steer_lag_delta = dt / max(p.steer_tau, dt)
        steer_target = state.steer + (steer_cmd - state.steer) * clamp(steer_lag_delta, 0.0, 1.0)
        steer = move_towards(state.steer, steer_target, steer_rate_limit)

        drive_alpha = clamp(dt / max(p.drive_tau, dt), 0.0, 1.0)
        brake_alpha = clamp(dt / max(p.brake_tau, dt), 0.0, 1.0)
        drive_force = state.drive_force + (throttle_cmd * p.max_drive_force - state.drive_force) * drive_alpha
        brake_force = state.brake_force + (brake_cmd * p.max_brake_force - state.brake_force) * brake_alpha

        values = state.as_array()
        values[6] = steer
        values[7] = drive_force
        values[8] = brake_force
        next_values, forces = self._rk4(values, dt)
        next_state = FourWheelState.from_array(next_values)
        return next_state, forces

    def _rk4(self, values: np.ndarray, dt: float) -> tuple[np.ndarray, FourWheelForces]:
        k1, _ = self._derivatives(values)
        k2, _ = self._derivatives(values + 0.5 * dt * k1)
        k3, _ = self._derivatives(values + 0.5 * dt * k2)
        k4, forces = self._derivatives(values + dt * k3)
        next_values = values + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        next_values[6] = values[6]
        next_values[7] = values[7]
        next_values[8] = values[8]
        return next_values, forces

    def _derivatives(self, values: np.ndarray) -> tuple[np.ndarray, FourWheelForces]:
        p = self.params
        _, _, psi, vx, vy, yaw_rate, steer, drive_force, brake_force = values
        vx_safe = math.copysign(max(abs(vx), 0.75), vx if abs(vx) > 1e-6 else 1.0)
        forces = self.tire_forces(vx_safe, vy, yaw_rate, steer, drive_force, brake_force)

        vx_dot = forces.total_fx / p.mass + yaw_rate * vy
        vy_dot = forces.total_fy / p.mass - yaw_rate * vx
        yaw_dot = forces.yaw_moment / p.iz

        x_dot = vx * math.cos(psi) - vy * math.sin(psi)
        y_dot = vx * math.sin(psi) + vy * math.cos(psi)

        return (
            np.array(
                [
                    x_dot,
                    y_dot,
                    yaw_rate,
                    vx_dot,
                    vy_dot,
                    yaw_dot,
                    0.0,
                    0.0,
                    0.0,
                ],
                dtype=np.float64,
            ),
            forces,
        )

    def tire_forces(
        self,
        vx: float,
        vy: float,
        yaw_rate: float,
        steer: float,
        drive_force: float,
        brake_force: float,
    ) -> FourWheelForces:
        p = self.params
        half_track = 0.5 * p.track_width
        positions = (
            ("front_left", p.lf, half_track, steer, p.cf, 0.5 * p.static_front_load),
            ("front_right", p.lf, -half_track, steer, p.cf, 0.5 * p.static_front_load),
            ("rear_left", -p.lr, half_track, 0.0, p.cr, 0.5 * p.static_rear_load),
            ("rear_right", -p.lr, -half_track, 0.0, p.cr, 0.5 * p.static_rear_load),
        )
        front_brake = float(brake_force) * clamp(p.front_brake_bias, 0.0, 1.0)
        rear_brake = float(brake_force) - front_brake
        brake_targets = (-0.5 * front_brake, -0.5 * front_brake, -0.5 * rear_brake, -0.5 * rear_brake)
        drive_targets = (0.0, 0.0, 0.5 * float(drive_force), 0.5 * float(drive_force))

        wheels: list[WheelForce] = []
        for index, (name, wheel_x, wheel_y, steer_angle, stiffness, fz) in enumerate(positions):
            local_vx = float(vx) - float(yaw_rate) * wheel_y
            local_vy = float(vy) + float(yaw_rate) * wheel_x
            vx_abs = max(abs(local_vx), 0.75)
            alpha = math.atan2(local_vy, vx_abs) - steer_angle

            mu_capacity = max(p.mu * self.fault_scales.mu[index] * fz, 1.0)
            desired_fx = drive_targets[index] * self.fault_scales.drive[index]
            desired_fx += brake_targets[index] * self.fault_scales.brake[index]
            desired_fx -= math.copysign(abs(self.fault_scales.longitudinal_drag[index]), local_vx)
            fx_wheel = clamp(desired_fx, -0.98 * mu_capacity, 0.98 * mu_capacity)
            lateral_capacity = math.sqrt(max(mu_capacity**2 - fx_wheel**2, 1.0))
            cornering = stiffness * self.fault_scales.lateral_stiffness[index]
            fy_wheel = -lateral_capacity * math.tanh(cornering * alpha / lateral_capacity)

            cos_delta = math.cos(steer_angle)
            sin_delta = math.sin(steer_angle)
            fx_body = fx_wheel * cos_delta - fy_wheel * sin_delta
            fy_body = fx_wheel * sin_delta + fy_wheel * cos_delta
            wheels.append(
                WheelForce(
                    name=name,
                    x=float(wheel_x),
                    y=float(wheel_y),
                    steer=float(steer_angle),
                    fx_body=float(fx_body),
                    fy_body=float(fy_body),
                    fx_wheel=float(fx_wheel),
                    fy_wheel=float(fy_wheel),
                    fz=float(fz),
                    mu_capacity=float(mu_capacity),
                    alpha=float(alpha),
                )
            )

        drag = p.drag_coeff * float(vx) * abs(float(vx))
        rolling = p.rolling_resistance * math.tanh(float(vx))
        return FourWheelForces(
            wheels=(wheels[0], wheels[1], wheels[2], wheels[3]),
            drag_force=float(drag),
            rolling_force=float(rolling),
        )


def _wheel_index(wheel: str) -> int:
    try:
        return WHEEL_NAMES.index(str(wheel))
    except ValueError as exc:
        raise ValueError(f"unknown wheel {wheel!r}; expected one of {WHEEL_NAMES}") from exc
