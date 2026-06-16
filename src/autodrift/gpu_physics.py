"""Branchless, GPU-batched PHYSICS vehicle-dynamics model for AutoDrift (Path B, physics rewrite).

This is the *physics* alternative to the learned-residual grey-box in
``autodrift.gpu_surrogate``. Where the grey-box bolts a small MLP onto the analytic
single-track model to absorb the Chrono discrepancy, this module reconstructs the
Chrono Sedan dynamics *from physics* — a 4-wheel (double-track) planar model with a
real RWD powertrain, wheel-spin state, slip-driven TMeasy/Magic-Formula tyres and
quasi-static load transfer — so it reproduces Chrono's drift dynamics with **no
learning**. The parameters are the reverse-engineered Chrono Sedan spec
(``docs/chrono-sedan-physics-extracted.json``).

Everything is BRANCHLESS and BATCHED over N environments: there is no python loop
over N, no per-env ``if``; all regime selection is ``torch.where`` / masking, the
automatic gearbox is an int tensor updated by masked shifts, and piecewise-linear
maps are ``searchsorted`` + vectorised interpolation. It mirrors the style of
``gpu_surrogate.py`` (``ParamBatch``, ``make_param_batch``, ``[N,...]`` torch state).

State layout (PHYS_STATE_DIM = 15):
    [x, y, psi, vx, vy, yaw_rate, steer, throttle, brake, omega_rl, omega_rr,
     ax_f, ay_f, fyf_relax, fyr_relax]
where omega_{rl,rr} are the two rear-wheel angular speeds (the driveline state the
single-track lacked), ax_f/ay_f are the filtered body accelerations feeding
quasi-static load transfer (breaks the Fz<->force fixed point explicitly), and
fyf_relax/fyr_relax are the relaxation-length-lagged axle lateral forces.

The model is validated offline against saved Chrono rollouts by
``scripts/feasibility_audit/surrogate_physics_gate.py`` (same open-loop divergence
gate as the residual: beta-div @24, vx RMSE).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import torch

# ----------------------------------------------------------------------------- layout
# state: [x, y, psi, vx, vy, yaw_rate, steer, throttle, brake, omega_rl, omega_rr,
#         ax_f, ay_f, fyf_relax, fyr_relax]
# fyf_relax/fyr_relax are the relaxation-length-lagged lateral forces (front/rear axle),
# the TMeasy tyre-force transient that holds sideslip up during a drift entry.
PHYS_STATE_DIM = 15
IDX = dict(
    x=0, y=1, psi=2, vx=3, vy=4, yaw_rate=5, steer=6, throttle=7, brake=8,
    omega_rl=9, omega_rr=10, ax_f=11, ay_f=12, fyf_relax=13, fyr_relax=14,
)
ACT_DIM = 3

# Chrono Sedan spec (docs/chrono-sedan-physics-extracted.json) — engine + gearbox tables.
# Full-throttle engine torque map (rpm -> Nm).
ENGINE_RPM = (1000.0, 1400.0, 1600.0, 4500.0, 5000.0, 5500.0, 6000.0, 6500.0)
ENGINE_TQ_FULL = (236.8, 338.3, 370.0, 370.0, 353.3, 321.2, 294.4, 244.6)
# Zero-throttle (engine-braking) map (rpm -> Nm). Extrapolated below 1500 to 0.
ENGINE_BRAKE_RPM = (0.0, 1500.0, 3000.0, 4500.0, 5000.0, 6000.0, 6500.0)
ENGINE_TQ_BRAKE = (0.0, -10.0, -15.0, -30.0, -50.0, -70.0, -100.0)
# 6-speed automatic ratios (Chrono: T_out = T_in / ratio).
GEAR_RATIOS = (0.265, 0.489, 0.784, 1.063, 1.276, 1.499)
# Per-gear shift thresholds in *motor rpm* (down, up). gear index 0..5.
SHIFT_DOWN = (1000.0, 1200.0, 1400.0, 1600.0, 1800.0, 2000.0)
SHIFT_UP = (4000.0, 4500.0, 4500.0, 4500.0, 4500.0, 4500.0)


@dataclass
class PhysParams:
    """Scalar physics parameters for the Chrono Sedan (defaults from the extracted spec).

    A handful are *calibrated* against the saved Chrono drift data (noted inline); the
    rest are read directly off ``docs/chrono-sedan-physics-extracted.json``.
    """

    # --- geometry / mass (extracted spec) ---
    mass: float = 1683.97          # total vehicle mass [kg]
    izz: float = 1053.5            # yaw inertia [kg.m^2]
    wheelbase: float = 2.776       # [m]
    # symmetric suspension placement => lf=lr=wheelbase/2, but front axle load share 0.489.
    front_axle_share: float = 0.489
    h_cg: float = 0.43             # COM height [m] (extracted; effective transfer calibrated via h_cg_scale)
    track_f: float = 1.5958        # front wheeltrack [m]
    track_r: float = 1.6           # rear wheeltrack [m]
    gravity: float = 9.81

    # --- steering / actuators (match gpu_surrogate filter) ---
    max_steer: float = 0.43633     # max road-wheel steer [rad] (= 25 deg)
    max_steer_rate: float = 3.5    # [rad/s]
    steer_tau: float = 0.06        # [s]
    throttle_tau: float = 0.08     # [s] first-order actuator lag on throttle
    brake_tau: float = 0.08        # [s] first-order actuator lag on brake

    # --- tyre (Magic-Formula calibrated to TMeasy peak ~1.3, slip-at-peak from spec) ---
    # The pac_* defaults below are the values found by coordinate-descent calibration against
    # the 160 saved Chrono drift rollouts (surrogate_physics_gate.py --calibrate); see the
    # module docstring / gate script for the held-out divergence numbers they produce.
    mu0: float = 0.8               # reference friction (terrain mu enters as scale = mu/mu0)
    # longitudinal Pacejka: B_x*sx peak near sx~0.10; peak force/Fz = D_x.
    pac_Bx: float = 11.0
    pac_Cx: float = 1.5
    pac_Dx: float = 1.32           # peak Fx/Fz (spec: 1.2-1.4)
    pac_Ex: float = 0.2
    # lateral Pacejka: peak near alpha ~ 0.12 rad. (By/Dy calibrated down from the textbook
    # values to match Chrono's TMeasy axle balance in the drift saddle.)
    pac_By: float = 8.0
    pac_Cy: float = 1.45
    pac_Dy: float = 1.10           # peak Fy/Fz (calibrated)
    pac_Ey: float = -0.5
    # degressive load dependence: peak force/Fz shrinks with load (TMeasy InterpL/Q proxy).
    k_deg: float = 0.10            # mu_eff = D * (1 - k_deg*(Fz/Fz_nom - 1))
    # tyre relaxation length [m]: lateral force lags slip-angle change over this travel
    # distance (TMeasy transient). Calibration drove this near-zero (quasi-static is enough here).
    relax_len_f: float = 0.10
    relax_len_r: float = 0.05
    # front/rear lateral grip scales (calibrated axle balance => drift yaw stability).
    front_grip_scale: float = 1.10
    rear_grip_scale: float = 0.85

    # --- powertrain / driveline ---
    r_eff: float = 0.3237          # effective rolling radius [m]
    i_wheel: float = 0.679         # per-wheel + lumped driveline inertia [kg.m^2]
    final_drive: float = 0.2       # conical final drive (T_axle = T_driveshaft / 0.2)
    max_engine_rpm: float = 6500.0
    idle_rpm: float = 800.0
    max_brake_torque: float = 2000.0  # per-wheel brake torque at full brake [N.m] (calibrated)
    rolling_resist_coeff: float = 0.03   # rolling resistance (fraction of Fz, calibrated up to
                                         # absorb the extra longitudinal decel Chrono shows)
    drag_coeff: float = 0.80       # aero drag 0.5*rho*Cd*A [N/(m/s)^2-ish lumped] (calibrated)

    # --- calibration knobs (tuned against saved Chrono data) ---
    h_cg_scale: float = 1.0        # effective CG-height multiplier for load transfer
    drive_scale: float = 1.0       # overall driveline torque scale
    substeps: int = 4              # internal sub-steps per control step

    def as_dict(self) -> dict[str, float]:
        return {k: float(getattr(self, k)) for k in self.__dataclass_fields__ if k != "substeps"} | {
            "substeps": int(self.substeps)
        }


# Per-env broadcastable scalar keys (everything except the LUT tables, which are shared).
_PARAM_KEYS = (
    "mass", "izz", "wheelbase", "front_axle_share", "h_cg", "track_f", "track_r", "gravity",
    "max_steer", "max_steer_rate", "steer_tau", "throttle_tau", "brake_tau",
    "mu0", "pac_Bx", "pac_Cx", "pac_Dx", "pac_Ex", "pac_By", "pac_Cy", "pac_Dy", "pac_Ey", "k_deg",
    "relax_len_f", "relax_len_r", "front_grip_scale", "rear_grip_scale",
    "r_eff", "i_wheel", "final_drive", "max_engine_rpm", "idle_rpm", "max_brake_torque",
    "rolling_resist_coeff", "drag_coeff", "h_cg_scale", "drive_scale",
)


@dataclass
class PhysParamBatch:
    """Per-environment physics parameters as [N] tensors + shared LUT tables + terrain mu."""

    t: dict[str, torch.Tensor]
    mu: torch.Tensor                       # [N] terrain friction
    substeps: int = 4
    luts: dict[str, torch.Tensor] = field(default_factory=dict)

    def __getitem__(self, k: str) -> torch.Tensor:
        return self.t[k]

    @property
    def device(self) -> torch.device:
        return self.t["mass"].device

    @property
    def dtype(self) -> torch.dtype:
        return self.t["mass"].dtype


def make_phys_param_batch(
    params: PhysParams | Mapping[str, float],
    n: int,
    *,
    mu: float | torch.Tensor = 0.48,
    device: torch.device | str = "cpu",
    dtype: torch.dtype = torch.float32,
) -> PhysParamBatch:
    """Broadcast a PhysParams (or dict of scalars/[N] tensors) to a [N] PhysParamBatch.

    ``mu`` is the per-env terrain friction (scalar or [N] tensor)."""
    if isinstance(params, PhysParams):
        src: dict[str, object] = params.as_dict()
        substeps = int(params.substeps)
    else:
        src = dict(params)
        substeps = int(src.get("substeps", 4))
    t: dict[str, torch.Tensor] = {}
    for k in _PARAM_KEYS:
        v = src[k]
        if isinstance(v, torch.Tensor):
            t[k] = v.to(device=device, dtype=dtype).expand(n).clone()
        else:
            t[k] = torch.full((n,), float(v), device=device, dtype=dtype)
    if isinstance(mu, torch.Tensor):
        mu_t = mu.to(device=device, dtype=dtype).expand(n).clone()
    else:
        mu_t = torch.full((n,), float(mu), device=device, dtype=dtype)

    luts = {
        "eng_rpm": torch.tensor(ENGINE_RPM, device=device, dtype=dtype),
        "eng_full": torch.tensor(ENGINE_TQ_FULL, device=device, dtype=dtype),
        "ebr_rpm": torch.tensor(ENGINE_BRAKE_RPM, device=device, dtype=dtype),
        "ebr_tq": torch.tensor(ENGINE_TQ_BRAKE, device=device, dtype=dtype),
        "ratios": torch.tensor(GEAR_RATIOS, device=device, dtype=dtype),
        "shift_down": torch.tensor(SHIFT_DOWN, device=device, dtype=dtype),
        "shift_up": torch.tensor(SHIFT_UP, device=device, dtype=dtype),
    }
    return PhysParamBatch(t=t, mu=mu_t, substeps=substeps, luts=luts)


# --------------------------------------------------------------------- branchless 1D interp
def _interp1d(x: torch.Tensor, xp: torch.Tensor, fp: torch.Tensor) -> torch.Tensor:
    """Vectorised piecewise-linear interpolation, clamped at the ends. x:[...], xp/fp:[K]."""
    K = xp.shape[0]
    xc = x.clamp(xp[0], xp[-1])
    # bin index in [1, K-1]
    idx = torch.searchsorted(xp, xc.contiguous(), right=True).clamp(1, K - 1)
    x0 = xp[idx - 1]
    x1 = xp[idx]
    y0 = fp[idx - 1]
    y1 = fp[idx]
    w = (xc - x0) / (x1 - x0).clamp_min(1e-9)
    return y0 + w * (y1 - y0)


def _pacejka(slip: torch.Tensor, B: torch.Tensor, C: torch.Tensor, D: torch.Tensor, E: torch.Tensor) -> torch.Tensor:
    """Magic-Formula normalised force (in units of D, i.e. per-Fz when D is the friction peak)."""
    Bs = B * slip
    return D * torch.sin(C * torch.atan(Bs - E * (Bs - torch.atan(Bs))))


# --------------------------------------------------------------------- powertrain (branchless)
def _engine_torque(rpm: torch.Tensor, throttle: torch.Tensor, P: PhysParamBatch) -> torch.Tensor:
    """Blended engine torque T = (1-thr)*brake_map(rpm) + thr*full_map(rpm). [N] -> [N]."""
    rpm_c = torch.minimum(rpm.clamp_min(0.0), P["max_engine_rpm"])
    full = _interp1d(rpm_c, P.luts["eng_rpm"], P.luts["eng_full"])
    brake = _interp1d(rpm_c, P.luts["ebr_rpm"], P.luts["ebr_tq"])
    return (1.0 - throttle) * brake + throttle * full


def _gear_ratio(gear: torch.Tensor, P: PhysParamBatch) -> torch.Tensor:
    """Gather the active gear ratio. gear int tensor [N] in [0,5]."""
    return P.luts["ratios"][gear]


def _update_gear(gear: torch.Tensor, motor_rpm: torch.Tensor, P: PhysParamBatch) -> torch.Tensor:
    """Branchless automatic-gearbox FSM: at most one masked shift per call. gear int64 [N]."""
    up_thresh = P.luts["shift_up"][gear]
    down_thresh = P.luts["shift_down"][gear]
    up = (motor_rpm > up_thresh) & (gear < 5)
    down = (motor_rpm < down_thresh) & (gear > 0)
    return gear + up.long() - down.long()


# --------------------------------------------------------------------- tyre + load transfer
def _normal_loads(ax: torch.Tensor, ay: torch.Tensor, P: PhysParamBatch):
    """Quasi-static per-wheel normal loads [N] for FL,FR,RL,RR. ax,ay are body accelerations.

    Branchless signed-transfer: longitudinal transfer loads the rear under +ax (accel),
    lateral transfer loads the side opposite to +ay. Returns 4 tensors [N]."""
    m = P["mass"]
    g = P["gravity"]
    h = P["h_cg"] * P["h_cg_scale"]
    L = P["wheelbase"]
    share_f = P["front_axle_share"]
    static_f = m * g * share_f * 0.5        # per front wheel
    static_r = m * g * (1.0 - share_f) * 0.5  # per rear wheel

    dFz_long = m * ax * h / L                 # total front->rear transfer (signed by ax)
    # lateral transfer per axle (split by axle load share)
    dFz_lat_f = m * ay * h / P["track_f"] * share_f
    dFz_lat_r = m * ay * h / P["track_r"] * (1.0 - share_f)

    # +ax (accelerate) unloads front, loads rear. +ay loads the wheel on -y side.
    fz_fl = torch.clamp(static_f - 0.5 * dFz_long - dFz_lat_f, min=1.0)
    fz_fr = torch.clamp(static_f - 0.5 * dFz_long + dFz_lat_f, min=1.0)
    fz_rl = torch.clamp(static_r + 0.5 * dFz_long - dFz_lat_r, min=1.0)
    fz_rr = torch.clamp(static_r + 0.5 * dFz_long + dFz_lat_r, min=1.0)
    return fz_fl, fz_fr, fz_rl, fz_rr


def _wheel_forces(sx, alpha, fz, fz_nom, mu_scale, P: PhysParamBatch, grip_scale=1.0):
    """Per-wheel combined-slip Fx,Fy via Magic-Formula with friction-ellipse coupling.

    sx: longitudinal slip, alpha: slip angle [rad], fz: normal load [N], fz_nom: nominal [N].
    grip_scale scales the lateral peak (axle grip balance for drift yaw stability).
    Combined slip uses the standard slip-vector projection: evaluate the curve on the
    combined slip magnitude and split by direction (sx, tan(alpha)). This makes a large
    drive slip eat the lateral budget (power-oversteer), the physics a drift needs.
    Returns (Fx, Fy)."""
    # degressive load dependence on the friction peak (TMeasy InterpL/Q proxy)
    q = fz / fz_nom.clamp_min(1.0)
    deg = (1.0 - P["k_deg"] * (q - 1.0)).clamp(0.4, 1.3)
    Dx = P["pac_Dx"] * deg * mu_scale
    Dy = P["pac_Dy"] * deg * mu_scale * grip_scale

    # theoretical slips: longitudinal sx, lateral sy = tan(alpha). Normalise each by its
    # peak-slip so the combined magnitude lives on a common scale, then re-derive direction.
    sy = torch.tan(alpha.clamp(-1.45, 1.45))
    # peak slips (where each pure curve maxes) ~ pi/(2 C B); use as normalisers.
    sxm = torch.pi / (2.0 * P["pac_Cx"] * P["pac_Bx"])
    sym = torch.pi / (2.0 * P["pac_Cy"] * P["pac_By"])
    nx = sx / sxm
    ny = sy / sym
    s_comb = torch.sqrt(nx * nx + ny * ny + 1e-9)
    # direction cosines on the normalised slip plane
    cx = nx / s_comb
    cy = ny / s_comb
    # evaluate each axis curve at the combined slip, projected back to physical slip scale
    fx0 = _pacejka(s_comb * sxm, P["pac_Bx"], P["pac_Cx"], Dx, P["pac_Ex"]) * fz
    fy0 = _pacejka(s_comb * sym, P["pac_By"], P["pac_Cy"], Dy, P["pac_Ey"]) * fz
    # split the combined force by slip direction; lateral force opposes slip (sign -cy)
    fx = fx0 * cx
    fy = -fy0 * cy
    return fx, fy


def _accel_from_forces(vx, vy, yaw_rate, steer, Fx_f, Fy_f, Fx_r, Fy_r, P: PhysParamBatch):
    """Combine axle forces (front in wheel frame, rotated by steer; rear in body frame).

    Fx_f/Fy_f: front-axle long/lat in the steered-wheel frame; Fx_r/Fy_r: rear-axle in body
    frame. Returns (vx_dot, vy_dot, yaw_dot, ax_body, ay_body)."""
    cs = torch.cos(steer)
    sn = torch.sin(steer)
    Fx_f_body = Fx_f * cs - Fy_f * sn
    Fy_f_body = Fx_f * sn + Fy_f * cs

    # aero drag + rolling resistance oppose vx
    drag = P["drag_coeff"] * vx * vx.abs()
    rolling = P["rolling_resist_coeff"] * P["mass"] * P["gravity"] * torch.tanh(vx)
    Fx_body = Fx_f_body + Fx_r - drag - rolling
    Fy_body = Fy_f_body + Fy_r

    lf = 0.5 * P["wheelbase"]
    lr = 0.5 * P["wheelbase"]
    Mz = lf * Fy_f_body - lr * Fy_r

    ax_body = Fx_body / P["mass"]
    ay_body = Fy_body / P["mass"]
    vx_dot = ax_body + yaw_rate * vy
    vy_dot = ay_body - yaw_rate * vx
    yaw_dot = Mz / P["izz"]
    return vx_dot, vy_dot, yaw_dot, ax_body, ay_body


def _continuous_derivs(vx, vy, yaw_rate, steer, omega_rl, omega_rr, throttle, brake, gear,
                       ax_f, ay_f, fyf_relax, fyr_relax, P: PhysParamBatch):
    """Continuous-time derivatives of (vx,vy,yaw_rate,omega_rl,omega_rr,fyf_relax,fyr_relax).

    fyf_relax/fyr_relax are the relaxation-lagged axle lateral forces (the state that holds
    sideslip up during drift entry). All inputs [N]. Returns
    (vx_dot, vy_dot, yaw_dot, orl_dot, orr_dot, fyf_dot, fyr_dot, ax_body, ay_body)."""
    mu_scale = P.mu / P["mu0"]

    # ---- normal loads from filtered accelerations (explicit, no fixed point) ----
    fz_fl, fz_fr, fz_rl, fz_rr = _normal_loads(ax_f, ay_f, P)
    fz_nom_f = P["mass"] * P["gravity"] * P["front_axle_share"] * 0.5
    fz_nom_r = P["mass"] * P["gravity"] * (1.0 - P["front_axle_share"]) * 0.5

    # ---- slip angles ----
    lf = 0.5 * P["wheelbase"]
    lr = 0.5 * P["wheelbase"]
    sign = torch.where(vx.abs() > 1e-6, torch.sign(vx), torch.ones_like(vx))
    vx_safe = sign * vx.abs().clamp_min(0.75)
    # lateral velocity at each axle
    vy_f = vy + lf * yaw_rate
    vy_r = vy - lr * yaw_rate
    alpha_f = torch.atan2(vy_f, vx_safe.abs()) - steer
    alpha_r = torch.atan2(vy_r, vx_safe.abs())

    # ---- rear longitudinal slip from wheel spin ----
    half_tr = 0.5 * P["track_r"]
    vx_rl = vx - yaw_rate * half_tr
    vx_rr = vx + yaw_rate * half_tr
    vx_rl_safe = torch.sign(vx_rl) * vx_rl.abs().clamp_min(0.75)
    vx_rr_safe = torch.sign(vx_rr) * vx_rr.abs().clamp_min(0.75)
    sx_rl = (P["r_eff"] * omega_rl - vx_rl) / vx_rl_safe.abs().clamp_min(0.5)
    sx_rr = (P["r_eff"] * omega_rr - vx_rr) / vx_rr_safe.abs().clamp_min(0.5)

    # ---- tyre forces (instantaneous / target) ----
    # front wheels: no drive slip (sx=0), lateral from alpha_f. (FWD-less front => free-rolling)
    zero = torch.zeros_like(vx)
    gsf = P["front_grip_scale"]
    gsr = P["rear_grip_scale"]
    fx_fl, fy_fl = _wheel_forces(zero, alpha_f, fz_fl, fz_nom_f, mu_scale, P, gsf)
    fx_fr, fy_fr = _wheel_forces(zero, alpha_f, fz_fr, fz_nom_f, mu_scale, P, gsf)
    fx_rl, fy_rl = _wheel_forces(sx_rl, alpha_r, fz_rl, fz_nom_r, mu_scale, P, gsr)
    fx_rr, fy_rr = _wheel_forces(sx_rr, alpha_r, fz_rr, fz_nom_r, mu_scale, P, gsr)

    Fx_f = fx_fl + fx_fr
    Fx_r = fx_rl + fx_rr
    Fy_f_target = fy_fl + fy_fr
    Fy_r_target = fy_rl + fy_rr

    # ---- relaxation length: lateral axle force lags its target over a travel distance ----
    # dFy/dt = (Fy_target - Fy) * |vx| / relax_len  (first-order, branchless).
    v_relax = vx.abs().clamp_min(1.0)
    fyf_dot = (Fy_f_target - fyf_relax) * v_relax / P["relax_len_f"].clamp_min(0.05)
    fyr_dot = (Fy_r_target - fyr_relax) * v_relax / P["relax_len_r"].clamp_min(0.05)

    vx_dot, vy_dot, yaw_dot, ax_body, ay_body = _accel_from_forces(
        vx, vy, yaw_rate, steer, Fx_f, fyf_relax, Fx_r, fyr_relax, P,
    )

    # ---- powertrain torque to rear wheels ----
    # motor rpm from rear-wheel speed (avg) through final drive + gear ratio.
    omega_axle = 0.5 * (omega_rl + omega_rr)
    ratio = _gear_ratio(gear, P)
    # driveshaft speed = axle speed / final_drive; motor speed = driveshaft / ratio
    motor_rad = omega_axle / P["final_drive"].clamp_min(1e-3) / ratio.clamp_min(1e-3)
    motor_rpm = motor_rad.abs() * 60.0 / (2.0 * torch.pi)
    motor_rpm = torch.minimum(torch.maximum(motor_rpm, P["idle_rpm"]), P["max_engine_rpm"])

    T_eng = _engine_torque(motor_rpm, throttle, P) * P["drive_scale"]
    T_driveshaft = T_eng / ratio.clamp_min(1e-3)
    T_axle = T_driveshaft / P["final_drive"].clamp_min(1e-3)
    T_wheel = 0.5 * T_axle      # open diff splits equally

    # brake torque opposes each wheel's spin direction (all 4 wheels braked).
    T_brake_r = brake * P["max_brake_torque"]
    T_brake_rl = T_brake_r * torch.sign(omega_rl)
    T_brake_rr = T_brake_r * torch.sign(omega_rr)

    omega_rl_dot = (T_wheel - P["r_eff"] * fx_rl - T_brake_rl) / P["i_wheel"]
    omega_rr_dot = (T_wheel - P["r_eff"] * fx_rr - T_brake_rr) / P["i_wheel"]

    return (vx_dot, vy_dot, yaw_dot, omega_rl_dot, omega_rr_dot,
            fyf_dot, fyr_dot, ax_body, ay_body)


# --------------------------------------------------------------------------- step
def physics_step(state: torch.Tensor, action: torch.Tensor, gear: torch.Tensor,
                 P: PhysParamBatch, dt: float):
    """One control step of the branchless physics model, batched over N.

    state [N,15], action [N,3] (steer,throttle,brake in [-1,1]), gear int64 [N].
    Returns (next_state[N,15], next_gear[N], diagnostics dict)."""
    s = state
    vx = s[:, IDX["vx"]]
    vy = s[:, IDX["vy"]]
    yaw_rate = s[:, IDX["yaw_rate"]]
    steer = s[:, IDX["steer"]]
    throttle = s[:, IDX["throttle"]]
    brake = s[:, IDX["brake"]]
    omega_rl = s[:, IDX["omega_rl"]]
    omega_rr = s[:, IDX["omega_rr"]]
    ax_f = s[:, IDX["ax_f"]]
    ay_f = s[:, IDX["ay_f"]]
    fyf_relax = s[:, IDX["fyf_relax"]]
    fyr_relax = s[:, IDX["fyr_relax"]]
    psi = s[:, IDX["psi"]]

    # ---- actuator filters (mirror gpu_surrogate) ----
    steer_cmd = torch.clamp(action[:, 0], -1.0, 1.0) * P["max_steer"]
    throttle_cmd = 0.5 * (torch.clamp(action[:, 1], -1.0, 1.0) + 1.0)
    brake_cmd = 0.5 * (torch.clamp(action[:, 2], -1.0, 1.0) + 1.0)

    steer_rate_limit = P["max_steer_rate"] * dt
    steer_lag = torch.clamp(dt / torch.clamp(P["steer_tau"], min=dt), 0.0, 1.0)
    steer_target = steer + (steer_cmd - steer) * steer_lag
    new_steer = steer + torch.clamp(steer_target - steer, -steer_rate_limit, steer_rate_limit)

    thr_alpha = torch.clamp(dt / torch.clamp(P["throttle_tau"], min=dt), 0.0, 1.0)
    new_throttle = throttle + (throttle_cmd - throttle) * thr_alpha
    brk_alpha = torch.clamp(dt / torch.clamp(P["brake_tau"], min=dt), 0.0, 1.0)
    new_brake = brake + (brake_cmd - brake) * brk_alpha

    # ---- gear update (branchless FSM) once per control step ----
    omega_axle = 0.5 * (omega_rl + omega_rr)
    ratio0 = _gear_ratio(gear, P)
    motor_rad = omega_axle / P["final_drive"].clamp_min(1e-3) / ratio0.clamp_min(1e-3)
    motor_rpm = motor_rad.abs() * 60.0 / (2.0 * torch.pi)
    motor_rpm = torch.minimum(torch.maximum(motor_rpm, P["idle_rpm"]), P["max_engine_rpm"])
    new_gear = _update_gear(gear, motor_rpm, P)

    # ---- sub-stepped semi-implicit Euler integration ----
    nsub = max(int(P.substeps), 1)
    h = dt / nsub
    last_ax, last_ay = ax_f, ay_f
    for _ in range(nsub):
        (vx_dot, vy_dot, yaw_dot, orl_dot, orr_dot,
         fyf_dot, fyr_dot, ax_body, ay_body) = _continuous_derivs(
            vx, vy, yaw_rate, new_steer, omega_rl, omega_rr, new_throttle, new_brake, new_gear,
            last_ax, last_ay, fyf_relax, fyr_relax, P,
        )
        vx = vx + h * vx_dot
        vy = vy + h * vy_dot
        yaw_rate = yaw_rate + h * yaw_dot
        omega_rl = omega_rl + h * orl_dot
        omega_rr = omega_rr + h * orr_dot
        fyf_relax = fyf_relax + h * fyf_dot
        fyr_relax = fyr_relax + h * fyr_dot
        # filter the body accelerations (quasi-static load-transfer source for next sub-step)
        last_ax, last_ay = ax_body, ay_body

    # pose integration (not gated, but kept for completeness)
    new_psi = psi + dt * s[:, IDX["yaw_rate"]]
    new_x = s[:, IDX["x"]] + dt * (s[:, IDX["vx"]] * torch.cos(psi) - s[:, IDX["vy"]] * torch.sin(psi))
    new_y = s[:, IDX["y"]] + dt * (s[:, IDX["vx"]] * torch.sin(psi) + s[:, IDX["vy"]] * torch.cos(psi))

    out = state.clone()
    out[:, IDX["x"]] = new_x
    out[:, IDX["y"]] = new_y
    out[:, IDX["psi"]] = new_psi
    out[:, IDX["vx"]] = vx
    out[:, IDX["vy"]] = vy
    out[:, IDX["yaw_rate"]] = yaw_rate
    out[:, IDX["steer"]] = new_steer
    out[:, IDX["throttle"]] = new_throttle
    out[:, IDX["brake"]] = new_brake
    out[:, IDX["omega_rl"]] = omega_rl
    out[:, IDX["omega_rr"]] = omega_rr
    out[:, IDX["ax_f"]] = last_ax
    out[:, IDX["ay_f"]] = last_ay
    out[:, IDX["fyf_relax"]] = fyf_relax
    out[:, IDX["fyr_relax"]] = fyr_relax

    diag = {"motor_rpm": motor_rpm, "gear": new_gear}
    return out, new_gear, diag


def init_state(vx0: torch.Tensor, vy0: torch.Tensor, yaw0: torch.Tensor, P: PhysParamBatch):
    """Build an [N,15] initial state + gear from initial velocity. Wheel omega seeded to vx/r_eff,
    gear seeded to the highest gear consistent with the motor-speed band (so the gearbox does not
    have to upshift through every gear from a cold start)."""
    n = vx0.shape[0]
    dev, dt_ = P.device, P.dtype
    st = torch.zeros(n, PHYS_STATE_DIM, device=dev, dtype=dt_)
    st[:, IDX["vx"]] = vx0
    st[:, IDX["vy"]] = vy0
    st[:, IDX["yaw_rate"]] = yaw0
    # rolling rear wheels: omega = vx / r_eff (no initial slip)
    st[:, IDX["omega_rl"]] = vx0 / P["r_eff"]
    st[:, IDX["omega_rr"]] = vx0 / P["r_eff"]

    # seed gear: pick the gear whose motor rpm at this omega is inside [down,up].
    omega_axle = vx0 / P["r_eff"]
    ratios = P.luts["ratios"]
    # motor rpm for every gear: [N,6]
    motor_rpm_g = (omega_axle[:, None] / P["final_drive"][:, None].clamp_min(1e-3)
                   / ratios[None, :].clamp_min(1e-3)).abs() * 60.0 / (2.0 * torch.pi)
    up = P.luts["shift_up"][None, :]
    # the right gear is the lowest gear that does NOT exceed its up-threshold.
    ok = motor_rpm_g <= up
    # argmax of the boolean over gears gives the first True; if none, gear 5.
    gear = torch.where(ok.any(dim=1), ok.float().argmax(dim=1), torch.full((n,), 5, device=dev)).long()

    # seed the relaxation-lagged lateral forces to their steady-state targets at the init slip
    # (so the model starts in tyre-force equilibrium rather than ramping from zero).
    mu_scale = P.mu / P["mu0"]
    fz_fl, fz_fr, fz_rl, fz_rr = _normal_loads(torch.zeros_like(vx0), torch.zeros_like(vx0), P)
    fz_nom_f = P["mass"] * P["gravity"] * P["front_axle_share"] * 0.5
    fz_nom_r = P["mass"] * P["gravity"] * (1.0 - P["front_axle_share"]) * 0.5
    lf = 0.5 * P["wheelbase"]
    vx_safe = torch.sign(vx0) * vx0.abs().clamp_min(0.75)
    alpha_f = torch.atan2(vy0 + lf * yaw0, vx_safe.abs())  # steer=0 at init
    alpha_r = torch.atan2(vy0 - lf * yaw0, vx_safe.abs())
    z = torch.zeros_like(vx0)
    gsf = P["front_grip_scale"]; gsr = P["rear_grip_scale"]
    _, fy_fl = _wheel_forces(z, alpha_f, fz_fl, fz_nom_f, mu_scale, P, gsf)
    _, fy_fr = _wheel_forces(z, alpha_f, fz_fr, fz_nom_f, mu_scale, P, gsf)
    _, fy_rl = _wheel_forces(z, alpha_r, fz_rl, fz_nom_r, mu_scale, P, gsr)
    _, fy_rr = _wheel_forces(z, alpha_r, fz_rr, fz_nom_r, mu_scale, P, gsr)
    st[:, IDX["fyf_relax"]] = fy_fl + fy_fr
    st[:, IDX["fyr_relax"]] = fy_rl + fy_rr
    return st, gear
