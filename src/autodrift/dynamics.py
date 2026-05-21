"""Single-track drifting dynamics with randomized physical parameters.

The model is intentionally compact. It is not meant to be a final vehicle model;
it gives RL and baseline controllers a physically structured drift task with
friction-limited tires, rear-wheel drive, actuator limits, and parameter
randomization.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from autodrift.math_utils import clamp, move_towards


@dataclass(frozen=True)
class VehicleParams:
    mass: float = 1450.0
    iz: float = 2300.0
    lf: float = 1.35
    lr: float = 1.45
    h_cg: float = 0.52
    mu: float = 0.9
    cf: float = 95000.0
    cr: float = 110000.0
    max_steer: float = 0.62
    max_steer_rate: float = 3.5
    max_drive_force: float = 8200.0
    max_brake_force: float = 6000.0
    drive_tau: float = 0.08
    steer_tau: float = 0.06
    drag_coeff: float = 0.34
    rolling_resistance: float = 75.0
    gravity: float = 9.81

    @property
    def wheelbase(self) -> float:
        return self.lf + self.lr

    @property
    def static_fzf(self) -> float:
        return self.mass * self.gravity * self.lr / self.wheelbase

    @property
    def static_fzr(self) -> float:
        return self.mass * self.gravity * self.lf / self.wheelbase


@dataclass(frozen=True)
class RandomizationConfig:
    mu_range: tuple[float, float] = (0.25, 1.15)
    mass_scale_range: tuple[float, float] = (0.85, 1.20)
    cg_shift_range: tuple[float, float] = (-0.12, 0.12)
    inertia_scale_range: tuple[float, float] = (0.85, 1.25)
    tire_stiffness_scale_range: tuple[float, float] = (0.65, 1.35)
    drive_scale_range: tuple[float, float] = (0.80, 1.15)
    brake_scale_range: tuple[float, float] = (0.80, 1.15)
    actuator_tau_scale_range: tuple[float, float] = (0.75, 1.75)


@dataclass
class VehicleState:
    x: float
    y: float
    psi: float
    vx: float
    vy: float
    yaw_rate: float
    steer: float = 0.0
    drive_force: float = 0.0

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
            ],
            dtype=np.float64,
        )

    @classmethod
    def from_array(cls, values: np.ndarray) -> "VehicleState":
        return cls(*(float(v) for v in values))


@dataclass(frozen=True)
class TireForces:
    fy_front: float
    fy_rear: float
    fx_rear: float
    fz_front: float
    fz_rear: float
    alpha_front: float
    alpha_rear: float


def sample_vehicle_params(
    rng: np.random.Generator,
    base: VehicleParams | None = None,
    config: RandomizationConfig | None = None,
) -> VehicleParams:
    base = base or VehicleParams()
    config = config or RandomizationConfig()

    mass_scale = rng.uniform(*config.mass_scale_range)
    inertia_scale = rng.uniform(*config.inertia_scale_range)
    stiffness_scale = rng.uniform(*config.tire_stiffness_scale_range)
    drive_scale = rng.uniform(*config.drive_scale_range)
    brake_scale = rng.uniform(*config.brake_scale_range)
    tau_scale = rng.uniform(*config.actuator_tau_scale_range)

    wheelbase = base.wheelbase
    cg_shift = rng.uniform(*config.cg_shift_range)
    lf = clamp(base.lf + cg_shift, 0.9, wheelbase - 0.9)
    lr = wheelbase - lf

    return VehicleParams(
        mass=base.mass * mass_scale,
        iz=base.iz * inertia_scale,
        lf=lf,
        lr=lr,
        h_cg=base.h_cg,
        mu=rng.uniform(*config.mu_range),
        cf=base.cf * stiffness_scale,
        cr=base.cr * stiffness_scale,
        max_steer=base.max_steer,
        max_steer_rate=base.max_steer_rate,
        max_drive_force=base.max_drive_force * drive_scale,
        max_brake_force=base.max_brake_force * brake_scale,
        drive_tau=base.drive_tau * tau_scale,
        steer_tau=base.steer_tau * tau_scale,
        drag_coeff=base.drag_coeff,
        rolling_resistance=base.rolling_resistance,
        gravity=base.gravity,
    )


class SingleTrackDriftModel:
    """RWD single-track model with combined-slip rear saturation."""

    def __init__(self, params: VehicleParams | None = None):
        self.params = params or VehicleParams()

    def step(self, state: VehicleState, action: np.ndarray, dt: float) -> tuple[VehicleState, TireForces]:
        action = np.asarray(action, dtype=np.float64)
        if action.shape != (3,):
            raise ValueError(f"expected action shape (3,), got {action.shape}")
        steer_cmd = clamp(float(action[0]), -1.0, 1.0) * self.params.max_steer
        throttle_cmd = 0.5 * (clamp(float(action[1]), -1.0, 1.0) + 1.0)
        brake_cmd = 0.5 * (clamp(float(action[2]), -1.0, 1.0) + 1.0)

        steer_rate_limit = self.params.max_steer_rate * dt
        steer_lag_delta = dt / max(self.params.steer_tau, dt)
        steer_target = state.steer + (steer_cmd - state.steer) * clamp(steer_lag_delta, 0.0, 1.0)
        steer = move_towards(state.steer, steer_target, steer_rate_limit)

        force_target = throttle_cmd * self.params.max_drive_force - brake_cmd * self.params.max_brake_force
        drive_alpha = clamp(dt / max(self.params.drive_tau, dt), 0.0, 1.0)
        drive_force = state.drive_force + (force_target - state.drive_force) * drive_alpha

        values = state.as_array()
        values[6] = steer
        values[7] = drive_force
        next_values, forces = self._rk4(values, dt)
        next_state = VehicleState.from_array(next_values)
        return next_state, forces

    def _rk4(self, values: np.ndarray, dt: float) -> tuple[np.ndarray, TireForces]:
        k1, _ = self._derivatives(values)
        k2, _ = self._derivatives(values + 0.5 * dt * k1)
        k3, _ = self._derivatives(values + 0.5 * dt * k2)
        k4, forces = self._derivatives(values + dt * k3)
        next_values = values + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        next_values[6] = values[6]
        next_values[7] = values[7]
        return next_values, forces

    def _derivatives(self, values: np.ndarray) -> tuple[np.ndarray, TireForces]:
        p = self.params
        _, _, psi, vx, vy, yaw_rate, steer, drive_force = values
        vx_safe = math.copysign(max(abs(vx), 0.75), vx if abs(vx) > 1e-6 else 1.0)

        forces = self.tire_forces(vx_safe, vy, yaw_rate, steer, drive_force)

        drag = p.drag_coeff * vx * abs(vx)
        rolling = p.rolling_resistance * math.tanh(vx)
        fx_body = forces.fx_rear - forces.fy_front * math.sin(steer) - drag - rolling
        fy_body = forces.fy_front * math.cos(steer) + forces.fy_rear

        vx_dot = fx_body / p.mass + yaw_rate * vy
        vy_dot = fy_body / p.mass - yaw_rate * vx
        yaw_dot = (p.lf * forces.fy_front * math.cos(steer) - p.lr * forces.fy_rear) / p.iz

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
    ) -> TireForces:
        p = self.params
        fzf = p.static_fzf
        fzr = p.static_fzr

        alpha_front = math.atan2(vy + p.lf * yaw_rate, abs(vx)) - steer
        alpha_rear = math.atan2(vy - p.lr * yaw_rate, abs(vx))

        fx_rear_limit = p.mu * fzr
        fx_rear = clamp(drive_force, -0.98 * fx_rear_limit, 0.98 * fx_rear_limit)

        front_capacity = max(p.mu * fzf, 1.0)
        rear_capacity_total = max(p.mu * fzr, 1.0)
        rear_lat_capacity = math.sqrt(max(rear_capacity_total**2 - fx_rear**2, 1.0))

        fy_front = -front_capacity * math.tanh(p.cf * alpha_front / front_capacity)
        fy_rear = -rear_lat_capacity * math.tanh(p.cr * alpha_rear / rear_lat_capacity)

        return TireForces(
            fy_front=fy_front,
            fy_rear=fy_rear,
            fx_rear=fx_rear,
            fz_front=fzf,
            fz_rear=fzr,
            alpha_front=alpha_front,
            alpha_rear=alpha_rear,
        )
