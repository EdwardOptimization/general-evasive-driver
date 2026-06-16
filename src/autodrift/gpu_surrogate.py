"""GPU-batched vehicle-dynamics surrogate for AutoDrift (Path B).

Chrono::Vehicle is a CPU multibody solver with no GPU-batched-environments path
(its GPU modules are for granular/fluid/rendering, not vehicle dynamics). To get
the thousands-of-parallel-environments throughput that crushes PPO rollout-batch
variance, we move the *dynamics* onto the GPU as a torch-vectorised model and keep
Chrono as the high-fidelity validation reference.

This module is the physics backbone: a fully-vectorised torch port of
``autodrift.dynamics.SingleTrackDriftModel`` (RWD single-track, combined-slip rear
saturation, exact actuator filter, RK4). It is bit-faithful to the numpy model
(``test_analytic_matches_numpy``), so it can run B parallel environments on one GPU.

The grey-box surrogate (analytic backbone + a small learned residual fitting the
known Chrono-vs-analytic discrepancy at the drift saddle) is layered on top in the
next milestone; this file ships the analytic core + the residual hook.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import torch

from autodrift.dynamics import VehicleParams

# state layout: [x, y, psi, vx, vy, yaw_rate, steer, drive_force]
STATE_DIM = 8
ACT_DIM = 3
# VehicleParams fields broadcast per-environment (+ derived static axle loads).
PARAM_KEYS = (
    "mass", "iz", "lf", "lr", "mu", "cf", "cr", "max_steer", "max_steer_rate",
    "max_drive_force", "max_brake_force", "drive_tau", "steer_tau", "drag_coeff",
    "rolling_resistance", "gravity",
)


@dataclass
class ParamBatch:
    """Per-environment vehicle parameters as [N] tensors (+ derived static loads)."""

    t: dict[str, torch.Tensor]

    def __getitem__(self, k: str) -> torch.Tensor:
        return self.t[k]

    @property
    def static_fzf(self) -> torch.Tensor:
        return self.t["mass"] * self.t["gravity"] * self.t["lr"] / (self.t["lf"] + self.t["lr"])

    @property
    def static_fzr(self) -> torch.Tensor:
        return self.t["mass"] * self.t["gravity"] * self.t["lf"] / (self.t["lf"] + self.t["lr"])


def make_param_batch(
    params: VehicleParams | Mapping[str, float] | Mapping[str, torch.Tensor],
    n: int,
    *,
    device: torch.device | str = "cpu",
    dtype: torch.dtype = torch.float64,
) -> ParamBatch:
    """Broadcast a single VehicleParams (or a dict of scalars/[N] tensors) to a [N] ParamBatch."""
    src: dict[str, object] = {}
    if isinstance(params, VehicleParams):
        for k in PARAM_KEYS:
            src[k] = getattr(params, k)
    else:
        src = dict(params)
    t: dict[str, torch.Tensor] = {}
    for k in PARAM_KEYS:
        v = src[k]
        if isinstance(v, torch.Tensor):
            t[k] = v.to(device=device, dtype=dtype).expand(n).clone()
        else:
            t[k] = torch.full((n,), float(v), device=device, dtype=dtype)
    return ParamBatch(t)


def _tire_forces(vx, vy, yaw_rate, steer, drive_force, P: ParamBatch):
    """Vectorised combined-slip tyre model. vx is the speed-safed longitudinal velocity."""
    fzf, fzr = P.static_fzf, P.static_fzr
    absvx = vx.abs()
    alpha_front = torch.atan2(vy + P["lf"] * yaw_rate, absvx) - steer
    alpha_rear = torch.atan2(vy - P["lr"] * yaw_rate, absvx)

    fx_rear_limit = P["mu"] * fzr
    fx_rear = torch.clamp(drive_force, -0.98 * fx_rear_limit, 0.98 * fx_rear_limit)

    front_capacity = torch.clamp(P["mu"] * fzf, min=1.0)
    rear_capacity_total = torch.clamp(P["mu"] * fzr, min=1.0)
    rear_lat_capacity = torch.sqrt(torch.clamp(rear_capacity_total**2 - fx_rear**2, min=1.0))

    fy_front = -front_capacity * torch.tanh(P["cf"] * alpha_front / front_capacity)
    fy_rear = -rear_lat_capacity * torch.tanh(P["cr"] * alpha_rear / rear_lat_capacity)
    return {
        "fy_front": fy_front, "fy_rear": fy_rear, "fx_rear": fx_rear,
        "fz_front": fzf, "fz_rear": fzr, "alpha_front": alpha_front, "alpha_rear": alpha_rear,
    }


def _derivatives(values: torch.Tensor, P: ParamBatch):
    """d/dt of the [N,8] state; returns (deriv[N,8], forces dict). Matches dynamics._derivatives."""
    psi, vx, vy, yaw_rate, steer, drive_force = (values[:, i] for i in (2, 3, 4, 5, 6, 7))
    # vx_safe = copysign(max(|vx|, 0.75), vx if |vx|>1e-6 else 1.0)
    sign = torch.where(vx.abs() > 1e-6, torch.sign(vx), torch.ones_like(vx))
    vx_safe = sign * torch.clamp(vx.abs(), min=0.75)

    f = _tire_forces(vx_safe, vy, yaw_rate, steer, drive_force, P)
    drag = P["drag_coeff"] * vx * vx.abs()
    rolling = P["rolling_resistance"] * torch.tanh(vx)
    fx_body = f["fx_rear"] - f["fy_front"] * torch.sin(steer) - drag - rolling
    fy_body = f["fy_front"] * torch.cos(steer) + f["fy_rear"]

    vx_dot = fx_body / P["mass"] + yaw_rate * vy
    vy_dot = fy_body / P["mass"] - yaw_rate * vx
    yaw_dot = (P["lf"] * f["fy_front"] * torch.cos(steer) - P["lr"] * f["fy_rear"]) / P["iz"]
    x_dot = vx * torch.cos(psi) - vy * torch.sin(psi)
    y_dot = vx * torch.sin(psi) + vy * torch.cos(psi)

    deriv = torch.stack(
        [x_dot, y_dot, yaw_rate, vx_dot, vy_dot, yaw_dot,
         torch.zeros_like(vx), torch.zeros_like(vx)], dim=1)
    return deriv, f


def _rk4(values: torch.Tensor, P: ParamBatch, dt: float):
    k1, _ = _derivatives(values, P)
    k2, _ = _derivatives(values + 0.5 * dt * k1, P)
    k3, _ = _derivatives(values + 0.5 * dt * k2, P)
    k4, forces = _derivatives(values + dt * k3, P)
    nxt = values + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
    nxt[:, 6] = values[:, 6]  # hold actuator states (integrated separately)
    nxt[:, 7] = values[:, 7]
    return nxt, forces


def analytic_step(state: torch.Tensor, action: torch.Tensor, P: ParamBatch, dt: float):
    """One control step of the analytic single-track model, batched over N.

    state [N,8], action [N,3] (steer,throttle,brake in [-1,1]) -> (next_state[N,8], forces).
    Mirrors autodrift.dynamics.SingleTrackDriftModel.step bit-for-bit (RK4, actuator filter)."""
    steer_cmd = torch.clamp(action[:, 0], -1.0, 1.0) * P["max_steer"]
    throttle_cmd = 0.5 * (torch.clamp(action[:, 1], -1.0, 1.0) + 1.0)
    brake_cmd = 0.5 * (torch.clamp(action[:, 2], -1.0, 1.0) + 1.0)

    steer = state[:, 6]
    steer_rate_limit = P["max_steer_rate"] * dt
    steer_lag_delta = torch.clamp(dt / torch.clamp(P["steer_tau"], min=dt), 0.0, 1.0)
    steer_target = steer + (steer_cmd - steer) * steer_lag_delta
    # move_towards: clamp the step to +-rate_limit
    new_steer = steer + torch.clamp(steer_target - steer, -steer_rate_limit, steer_rate_limit)

    drive_force = state[:, 7]
    force_target = throttle_cmd * P["max_drive_force"] - brake_cmd * P["max_brake_force"]
    drive_alpha = torch.clamp(dt / torch.clamp(P["drive_tau"], min=dt), 0.0, 1.0)
    new_drive = drive_force + (force_target - drive_force) * drive_alpha

    values = state.clone()
    values[:, 6] = new_steer
    values[:, 7] = new_drive
    return _rk4(values, P, dt)


# --------------------------------------------------------- grey-box learned residual
class ResidualDynamicsMLP(torch.nn.Module):
    """Learns the (Chrono - analytic) correction to the per-step delta of {vx,vy,yaw_rate}.

    Features: [vx, vy, yaw_rate, steer_state, drive_force_state, steer_cmd, throttle_cmd,
    brake_cmd] (8). Normalisation buffers are set from the training corpus (set_norm)."""

    def __init__(self, in_dim: int = 8, hidden: int = 128):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(in_dim, hidden), torch.nn.SiLU(),
            torch.nn.Linear(hidden, hidden), torch.nn.SiLU(),
            torch.nn.Linear(hidden, 3),
        )
        self.register_buffer("in_mean", torch.zeros(in_dim))
        self.register_buffer("in_std", torch.ones(in_dim))
        self.register_buffer("out_mean", torch.zeros(3))
        self.register_buffer("out_std", torch.ones(3))

    def set_norm(self, feats: torch.Tensor, targets: torch.Tensor) -> None:
        self.in_mean.copy_(feats.mean(0)); self.in_std.copy_(feats.std(0).clamp_min(1e-6))
        self.out_mean.copy_(targets.mean(0)); self.out_std.copy_(targets.std(0).clamp_min(1e-9))

    def forward(self, feat: torch.Tensor) -> torch.Tensor:
        z = (feat - self.in_mean) / self.in_std
        return self.net(z) * self.out_std + self.out_mean


def residual_features(state: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
    """[vx,vy,yaw_rate, steer_state, drive_force_state] (state[:,3:8]) + action (3) = 8."""
    return torch.cat([state[:, 3:8], action], dim=1)


def grey_box_step(state, action, P: ParamBatch, dt: float, residual_mlp: ResidualDynamicsMLP):
    """Analytic single-track step + learned residual on the velocity channels."""
    nxt, forces = analytic_step(state, action, P, dt)
    resid = residual_mlp(residual_features(state, action))
    nxt = nxt.clone()
    nxt[:, 3:6] = nxt[:, 3:6] + resid
    return nxt, forces
