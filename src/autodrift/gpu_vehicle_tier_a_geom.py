"""Tier-a FAITHFUL GPU vehicle model: chassis 6-DOF + 4 KINEMATIC suspension corners.

This is the cross-vehicle "translate Chrono's TEMPLATE framework once" model (docs/
chrono-template-gpu-translation-plan-2026-06.md, Tier (a)). It REPLACES the planar single-body +
quasi-static load transfer of ``gpu_physics_pwr`` with a chassis 6-DOF rigid body riding on 4
kinematic suspension corners, so the per-corner vertical load Fz_i (and hence the lateral/long.
tyre force balance) comes from the DYNAMIC chassis roll/pitch/heave + corner travel -- not from an
algebraic m*a*h/L transfer. That dynamic load transfer is the residual the planar model omitted
(the avoid vx-0.90 / cornering gap).

EVERYTHING IS MEASURED FROM THE REAL CHRONO SEDAN (no re-fit):
  * Per-corner KINEMATIC lookups (camber/toe/track-shift/contact-patch-Fz vs suspension travel,
    + the front Ackermann toe-vs-steer) from ``chrono_suspension_kin.npz`` (extracted by solving
    the real Chrono DoubleWishbone(front)/MultiLink(rear)/RackPinion linkage every step).
  * The EXACT TMeasy Fx/Fy(slip,Fz) curves from ``chrono_tmeasy_curves.npz`` (+ tyre vertical
    stiffness Cz=456 716 N/m, used for the corner vertical-spring series).
  * The FWD powertrain (driven axle FRONT, gear schedule, final drive 0.2, engine blend) and the
    measured cruise resistance (drag=0, Crr=0.0282) from ``chrono_powertrain.npz`` /
    ``chrono_coastdown.npz``.
  * The suspension DAMPER coefficients (the ONE thing the kinematic extraction did not capture)
    read straight off the shipped Chrono Sedan suspension JSON ForceFunctors:
        FRONT (Sedan_DoubleWishbone.json "Shock"):  Damping Coefficient = 10000 N.s/m
        REAR  (Sedan_MultiLink.json     "Shock"):  Damping Coefficient = 15000 N.s/m
    These are the SHOCK-line coefficients; the WHEEL-rate damping is c_shock * MR^2 (motion ratio
    MR_front=0.763, MR_rear=0.335, from the same extraction), giving c_wheel ~5822 (front) / 1683
    (rear) N.s/m -> damping ratios zeta_f~0.69, zeta_r~0.30 (physically reasonable; NOT a guessed
    critical-damping fraction). See ``CORNER`` below.

The TMeasy tyre + slip-relaxation transient + FWD powertrain + masked gear-FSM logic is carried
OVER UNCHANGED from ``gpu_physics_pwr`` (same EXACT force tables, same measured sigma, same engine/
gear FSM). The NEW physics is the chassis-6DOF + per-corner kinematic suspension that supplies the
per-wheel Fz, camber, toe and contact-point velocity.

Branchless + batched over N envs: no python loop over N, no per-env ``if``; the 4 corners are a
fixed [N,4] tensor dimension; all regime selection is ``torch.where`` / ``searchsorted`` /
``gather``. Runs on cuda for N>=1000. Differentiable (all ops are autograd-friendly; the gear FSM
uses integer ``gather`` which is the only non-differentiable piece, as in the planar models).

State layout (TIER_A_STATE_DIM = 30), all [N]:
    chassis (12):  x, y, z, roll, pitch, yaw, vx, vy, vz, wx, wy, wz      (body-frame velocities,
                   body-frame angular rates; roll/pitch/yaw are the chassis Euler angles)
    corners (8):   zc_FL, zc_FR, zc_RL, zc_RR   (suspension travel, +jounce, [m])
                   zd_FL, zd_FR, zd_RL, zd_RR   (travel rate [m/s])
    wheels (4):    om_FL, om_FR, om_RL, om_RR   (wheel spin [rad/s]; FRONT are driven)
    actuators (3): steer, throttle, brake        (filtered)
    relax (3):     alpha_f_lag, alpha_r_lag, sx_f_lag   (tyre SLIP relaxation, carried from pwr;
                   front long-slip lag is shared L/R, rear is free-rolling lateral only)
gear is carried OUTSIDE the float state as an int64 [N] tensor (as in gpu_physics_pwr).

Validate offline against the saved Chrono rollouts with
``scripts/feasibility_audit/gpu_tier_a_gate.py`` (drift beta@24 + vx_rmse; avoid vx_rmse + vy_rmse),
side-by-side with the planar gpu_physics_pwr baseline.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

import numpy as np
import torch

_ROOT = Path(__file__).resolve().parents[2]
_CURVE_NPZ = _ROOT / "runs/feasibility_audit/phase4_f2/chrono_tmeasy_curves.npz"
_SUSP_NPZ = _ROOT / "runs/feasibility_audit/phase4_f2/chrono_suspension_kin.npz"

# ---------------------------------------------------------------------------- engine / gear tables
# (identical to gpu_physics_pwr / gpu_physics_relax -- the measured Chrono Sedan powertrain)
ENGINE_RPM = (1000.0, 1400.0, 1600.0, 4500.0, 5000.0, 5500.0, 6000.0, 6500.0)
ENGINE_TQ_FULL = (236.8, 338.3, 370.0, 370.0, 353.3, 321.2, 294.4, 244.6)
ENGINE_BRAKE_RPM = (0.0, 1500.0, 3000.0, 4500.0, 5000.0, 6000.0, 6500.0)
ENGINE_TQ_BRAKE = (0.0, -10.0, -15.0, -30.0, -50.0, -70.0, -100.0)
GEAR_RATIOS = (0.265, 0.489, 0.784, 1.063, 1.276, 1.499)
SHIFT_DOWN = (1000.0, 1200.0, 1400.0, 1600.0, 1800.0, 2000.0)
SHIFT_UP = (4000.0, 4500.0, 4500.0, 4500.0, 4500.0, 4500.0)

# corner order is fixed FL, FR, RL, RR everywhere (matches the npz corner_order).
CORNER_ORDER = ("FL", "FR", "RL", "RR")
# Ackermann inner/outer steer-spread gain: 0.0 = symmetric front road-wheel steer (= the planar
# model's road-wheel angle, faithful to the action->steer mapping that generated the data); 1.0 =
# the full measured toe-vs-steer spread. The measured spread is a small second-order effect that
# does not materially change the axle lateral force; default 0.0 keeps the front symmetric.
ACKERMANN_GAIN = 0.0
# Longitudinal-force yaw-moment scale (the -y_arm*Fx term in Mz). 1.0 = the full rigid-body moment.
YAW_FX_SCALE = 1.0
FRONT_MASK = (1.0, 1.0, 0.0, 0.0)   # which corners are front (steered + driven)
LEFT_MASK = (1.0, 0.0, 1.0, 0.0)    # which corners are left (+y)

# T3a FALSIFICATION TOGGLE: True = use the INSTANTANEOUS quasi-static geometric per-corner Fz
# (pwr3's load-transfer path, ay~vx*wz) instead of the slow roll-DOF travel-based Fz. The decisive
# test of whether the full-DAE's geometric load transfer would close tier_a's drift regression.
GEOMETRIC_FZ = True

# ----------------------------------------------------------------------------------- state layout
TIER_A_STATE_DIM = 30
IDX = dict(
    x=0, y=1, z=2, roll=3, pitch=4, yaw=5,
    vx=6, vy=7, vz=8, wx=9, wy=10, wz=11,
    zc0=12, zc1=13, zc2=14, zc3=15,          # corner travels FL,FR,RL,RR
    zd0=16, zd1=17, zd2=18, zd3=19,          # corner travel rates
    om0=20, om1=21, om2=22, om3=23,          # wheel spin FL,FR,RL,RR
    steer=24, throttle=25, brake=26,
    alpha_f_lag=27, alpha_r_lag=28, sx_f_lag=29,
)
_ZC = (IDX["zc0"], IDX["zc1"], IDX["zc2"], IDX["zc3"])
_ZD = (IDX["zd0"], IDX["zd1"], IDX["zd2"], IDX["zd3"])
_OM = (IDX["om0"], IDX["om1"], IDX["om2"], IDX["om3"])
ACT_DIM = 3


@dataclass
class CornerSpec:
    """Per-corner measured suspension constants (read off chrono_suspension_kin.npz at load)."""

    # MEASURED shock-line damping coefficients (Sedan suspension JSON "Shock" ForceFunctor).
    damp_shock_front: float = 10000.0   # N.s/m  (Sedan_DoubleWishbone.json)
    damp_shock_rear: float = 15000.0    # N.s/m  (Sedan_MultiLink.json)
    # unsprung mass per corner [kg] (typical passenger-car corner; the tyre series stiffness
    # dominates the fast vertical mode, so this is a lightly-weighted inertia, NOT a calibration).
    m_unsprung_front: float = 45.0
    m_unsprung_rear: float = 45.0


@dataclass
class TierAParams:
    """Scalar physics parameters for the Tier-a Sedan (defaults = measured Chrono Sedan spec).

    Mirrors ``gpu_physics_pwr.PhysParams`` field-for-field where they overlap (so the gate can
    re-parameterise mass/izz/wheelbase/front_axle_share the same way), and ADDS the chassis 3-axis
    inertia + corner suspension constants the 6-DOF model needs.
    """

    # --- mass / inertia ---
    mass: float = 1683.97              # total sprung+unsprung mass [kg]
    izz: float = 1053.5                # yaw inertia [kg.m^2] (about CG, z)
    ixx: float = 540.0                 # roll inertia [kg.m^2] (about CG, x) -- scaled from a Sedan
    iyy: float = 1800.0                # pitch inertia [kg.m^2] (about CG, y)
    wheelbase: float = 2.776           # [m]
    front_axle_share: float = 0.489    # static front-axle load share
    h_cg: float = 0.43                 # CG height above ground [m] (measured)
    track_f: float = 1.5868            # front wheeltrack [m] (2*static_wheel_y front)
    track_r: float = 1.6056            # rear wheeltrack [m] (2*static_wheel_y rear)
    gravity: float = 9.81

    # --- steering / actuators (match gpu_physics_pwr) ---
    max_steer: float = 0.43633
    max_steer_rate: float = 3.5
    steer_tau: float = 0.06
    throttle_tau: float = 0.08
    brake_tau: float = 0.08

    # --- tyre (EXACT TMeasy curves; no calibration) ---
    mu0: float = 0.8
    sigma_alpha: float = 0.651
    sigma_kappa: float = 0.796
    sigma_scale: float = 1.0
    front_grip_scale: float = 1.0
    rear_grip_scale: float = 1.0

    # --- powertrain / driveline (FWD; identical to gpu_physics_pwr) ---
    r_eff: float = 0.3237
    i_wheel: float = 0.679
    final_drive: float = 0.2
    max_engine_rpm: float = 6500.0
    idle_rpm: float = 800.0
    max_brake_torque: float = 2000.0
    rolling_resist_coeff: float = 0.0282
    drag_coeff: float = 0.0

    # --- numerics ---
    # 8 internal sub-steps/control step: the 6-DOF chassis (roll/pitch + the front-omega kinematic
    # relaxation) carries faster modes than the planar model, so 4 sub-steps under-resolves the
    # high-mu aggressive maneuvers (a spurious yaw transient); 8 converges (16 is identical).
    substeps: int = 8

    def as_dict(self) -> dict[str, float]:
        return {k: float(getattr(self, k)) for k in self.__dataclass_fields__ if k != "substeps"} | {
            "substeps": int(self.substeps)
        }


_PARAM_KEYS = (
    "mass", "izz", "ixx", "iyy", "wheelbase", "front_axle_share", "h_cg", "track_f", "track_r",
    "gravity", "max_steer", "max_steer_rate", "steer_tau", "throttle_tau", "brake_tau",
    "mu0", "sigma_alpha", "sigma_kappa", "sigma_scale", "front_grip_scale", "rear_grip_scale",
    "r_eff", "i_wheel", "final_drive", "max_engine_rpm", "idle_rpm", "max_brake_torque",
    "rolling_resist_coeff", "drag_coeff",
)


@dataclass
class TierAParamBatch:
    """Per-env scalar params [N] + shared LUT tensors (tyre curves + per-corner suspension)."""

    t: dict[str, torch.Tensor]
    mu: torch.Tensor
    substeps: int = 4
    luts: dict[str, torch.Tensor] = field(default_factory=dict)
    corner: dict[str, torch.Tensor] = field(default_factory=dict)

    def __getitem__(self, k: str) -> torch.Tensor:
        return self.t[k]

    @property
    def device(self) -> torch.device:
        return self.t["mass"].device

    @property
    def dtype(self) -> torch.dtype:
        return self.t["mass"].dtype


# ------------------------------------------------------------------------- npz caches
_CURVE_CACHE: dict[str, dict] = {}
_SUSP_CACHE: dict[str, dict] = {}


def _load_arrays(path, cache) -> dict:
    key = str(path)
    c = cache.get(key)
    if c is not None:
        return c
    d = np.load(path, allow_pickle=True)
    arr = {k: d[k] for k in d.files}
    cache[key] = arr
    return arr


# ------------------------------------------------------------------------- tyre LUT (from pwr)
def _curve_luts(arrays, device, dtype) -> dict[str, torch.Tensor]:
    """EXACT-TMeasy force-ratio surfaces + measured slip-relaxation length(Fz). Same as pwr."""
    fz_grid = np.asarray(arrays["fz_grid"], np.float64)
    kappa_grid = np.asarray(arrays["kappa_grid"], np.float64)
    alpha_grid = np.asarray(arrays["alpha_grid"], np.float64)
    Fx = np.asarray(arrays["Fx"], np.float64)
    Fy = np.asarray(arrays["Fy"], np.float64)
    Fz_at_K = np.asarray(arrays["Fz_at_K"], np.float64)
    Fz_at_A = np.asarray(arrays["Fz_at_A"], np.float64)
    fx_ratio = Fx / np.clip(Fz_at_K, 1.0, None)
    fy_ratio = Fy / np.clip(Fz_at_A, 1.0, None)
    kappa_peak = kappa_grid[np.argmax(np.abs(Fx), axis=0)]
    alpha_peak = alpha_grid[np.argmax(np.abs(Fy), axis=0)]

    TMEASY_SIGMA0 = 100000.0
    ap = alpha_grid[alpha_grid > 0].min(); an = alpha_grid[alpha_grid < 0].max()
    ip = int(np.where(alpha_grid == ap)[0][0]); ineg = int(np.where(alpha_grid == an)[0][0])
    kp = kappa_grid[kappa_grid > 0].min(); kn = kappa_grid[kappa_grid < 0].max()
    jp = int(np.where(kappa_grid == kp)[0][0]); jn = int(np.where(kappa_grid == kn)[0][0])
    dfy0 = np.abs((Fy[ip] - Fy[ineg]) / (np.tan(ap) - np.tan(an)))
    dfx0 = np.abs((Fx[jp] - Fx[jn]) / (kp - kn))
    sigma_alpha_fz = np.clip(dfy0 / TMEASY_SIGMA0, 0.02, None)
    sigma_kappa_fz = np.clip(dfx0 / TMEASY_SIGMA0, 0.02, None)

    tt = lambda a: torch.tensor(a, device=device, dtype=dtype)  # noqa: E731
    return {
        "tm_fz_grid": tt(fz_grid),
        "tm_kappa_grid": tt(kappa_grid),
        "tm_alpha_grid": tt(alpha_grid),
        "tm_fx_ratio": tt(fx_ratio),
        "tm_fy_ratio": tt(fy_ratio),
        "tm_kappa_peak": tt(kappa_peak),
        "tm_alpha_peak": tt(alpha_peak),
        "tm_sigma_alpha_fz": tt(sigma_alpha_fz),
        "tm_sigma_kappa_fz": tt(sigma_kappa_fz),
        "tm_Cz": tt(float(arrays["Cz"])),          # tyre vertical stiffness [N/m]
        "tm_mu0": tt(float(arrays["mu0"])),
    }


# --------------------------------------------------------------- per-corner kinematic suspension LUT
def _corner_luts(susp, cspec: CornerSpec, device, dtype) -> dict[str, torch.Tensor]:
    """Stack the per-corner camber/toe/track/contact-Fz vs-travel lookups into [4,K] tensors,
    plus the static corner geometry (lever arms) and the measured shock damping.

    The CONTACT-PATCH vertical load vs travel is taken directly from the extracted
    ``<C>_tire_normal_force`` curve (the real Chrono linkage's contact Fz vs suspension travel,
    which already folds in the spring + motion ratio + the static gravity settle). We additionally
    record the per-corner ride rate ``k_ride = d(Fz)/d(travel)`` and the spring-line + tyre
    stiffnesses for the corner vertical dynamics.
    """
    # shared travel grid (per corner, but near-identical); store each corner's own grid.
    z_grids = np.stack([susp[c + "_z_grid"] for c in CORNER_ORDER]).astype(np.float64)   # [4,23]
    camber = np.stack([susp[c + "_camber"] for c in CORNER_ORDER]).astype(np.float64)    # deg
    toe = np.stack([susp[c + "_toe"] for c in CORNER_ORDER]).astype(np.float64)          # deg
    track = np.stack([susp[c + "_track_shift"] for c in CORNER_ORDER]).astype(np.float64)
    fz_curve = np.stack([susp[c + "_tire_normal_force"] for c in CORNER_ORDER]).astype(np.float64)

    # static corner geometry: longitudinal x and lateral y of the wheel centre (CG-relative
    # computed at runtime from front_axle_share/wheelbase, but the measured y gives the track).
    i0 = np.array([int(np.argmin(np.abs(z_grids[i]))) for i in range(4)])
    wheel_x = np.array([susp[c + "_wheel_x"][i0[i]] for i, c in enumerate(CORNER_ORDER)])
    wheel_y = np.array([float(susp[c + "_static_wheel_y"]) for c in CORNER_ORDER])
    static_fz = np.array([fz_curve[i, i0[i]] for i in range(4)])
    static_camber = np.array([float(susp[c + "_static_camber"]) for c in CORNER_ORDER])
    static_toe = np.array([float(susp[c + "_static_toe"]) for c in CORNER_ORDER])

    # ride rate (contact Fz per unit travel) near static, per corner.
    k_ride = np.array([
        (fz_curve[i, i0[i] + 1] - fz_curve[i, i0[i] - 1]) /
        (z_grids[i, i0[i] + 1] - z_grids[i, i0[i] - 1]) for i in range(4)
    ])

    # measured shock damping -> wheel-rate damping c_wheel = c_shock * MR^2 (motion ratio).
    mr = np.array([float(susp[c + "_motion_ratio"]) for c in CORNER_ORDER])
    c_shock = np.array([cspec.damp_shock_front, cspec.damp_shock_front,
                        cspec.damp_shock_rear, cspec.damp_shock_rear])
    c_wheel = c_shock * mr * mr

    m_uns = np.array([cspec.m_unsprung_front, cspec.m_unsprung_front,
                      cspec.m_unsprung_rear, cspec.m_unsprung_rear])

    # Ackermann: front toe(deg) vs commanded steer angle (rad), per front corner.
    steer_ang = susp["FL_steer_angle_rad"].astype(np.float64)              # [21] (shared L/R)
    toe_vs_steer = np.stack([susp["FL_toe_vs_steer"], susp["FR_toe_vs_steer"]]).astype(np.float64)

    tt = lambda a: torch.tensor(a, device=device, dtype=dtype)  # noqa: E731
    return {
        "z_grid": tt(z_grids),                  # [4,K]
        "camber": tt(np.deg2rad(camber)),       # [4,K] rad
        "toe": tt(np.deg2rad(toe)),             # [4,K] rad (bump steer; +toe-in)
        "track": tt(track),                     # [4,K] m
        "fz_curve": tt(fz_curve),               # [4,K] N (contact-patch Fz vs travel)
        "k_ride": tt(k_ride),                   # [4]
        "c_wheel": tt(c_wheel),                 # [4] wheel-rate damping
        "m_uns": tt(m_uns),                     # [4]
        "wheel_x": tt(wheel_x),                 # [4]
        "wheel_y": tt(wheel_y),                 # [4]
        "static_fz": tt(static_fz),             # [4]
        "static_camber": tt(np.deg2rad(static_camber)),
        "static_toe": tt(np.deg2rad(static_toe)),
        "front_mask": tt(np.array(FRONT_MASK)),
        "left_mask": tt(np.array(LEFT_MASK)),
        "steer_ang": tt(steer_ang),             # [21]
        "toe_vs_steer": tt(np.deg2rad(toe_vs_steer)),   # [2,21] rad
    }


def make_tier_a_param_batch(
    params: TierAParams | Mapping[str, float],
    n: int,
    *,
    mu: float | torch.Tensor = 0.48,
    device: torch.device | str = "cpu",
    dtype: torch.dtype = torch.float32,
    corner: CornerSpec | None = None,
    curves=None,
    susp=None,
) -> TierAParamBatch:
    """Broadcast a TierAParams to a [N] batch with the shared tyre + per-corner suspension LUTs."""
    if isinstance(params, TierAParams):
        src: dict[str, object] = params.as_dict()
        substeps = int(params.substeps)
    else:
        src = dict(params)
        substeps = int(src.get("substeps", 4))
    t: dict[str, torch.Tensor] = {}
    for k in _PARAM_KEYS:
        v = src.get(k)
        if v is None:                       # allow a partial dict (gate reparam) -> fall back to default
            v = getattr(TierAParams(), k)
        if isinstance(v, torch.Tensor):
            t[k] = v.to(device=device, dtype=dtype).expand(n).clone()
        else:
            t[k] = torch.full((n,), float(v), device=device, dtype=dtype)
    mu_t = (mu.to(device=device, dtype=dtype).expand(n).clone()
            if isinstance(mu, torch.Tensor) else torch.full((n,), float(mu), device=device, dtype=dtype))

    luts = {
        "eng_rpm": torch.tensor(ENGINE_RPM, device=device, dtype=dtype),
        "eng_full": torch.tensor(ENGINE_TQ_FULL, device=device, dtype=dtype),
        "ebr_rpm": torch.tensor(ENGINE_BRAKE_RPM, device=device, dtype=dtype),
        "ebr_tq": torch.tensor(ENGINE_TQ_BRAKE, device=device, dtype=dtype),
        "ratios": torch.tensor(GEAR_RATIOS, device=device, dtype=dtype),
        "shift_down": torch.tensor(SHIFT_DOWN, device=device, dtype=dtype),
        "shift_up": torch.tensor(SHIFT_UP, device=device, dtype=dtype),
    }
    arrays = curves if isinstance(curves, dict) else _load_arrays(_CURVE_NPZ if curves is None else curves, _CURVE_CACHE)
    luts.update(_curve_luts(arrays, device, dtype))

    susp_arr = susp if isinstance(susp, dict) else _load_arrays(_SUSP_NPZ if susp is None else susp, _SUSP_CACHE)
    corner_luts = _corner_luts(susp_arr, corner or CornerSpec(), device, dtype)
    return TierAParamBatch(t=t, mu=mu_t, substeps=substeps, luts=luts, corner=corner_luts)


# ------------------------------------------------------------------------- branchless interpolation
def _interp1d(x, xp, fp):
    """Vectorised clamped piecewise-linear interp. x:[...], xp/fp:[K]. (same as pwr)"""
    K = xp.shape[0]
    xc = x.clamp(xp[0], xp[-1])
    idx = torch.searchsorted(xp, xc.contiguous(), right=True).clamp(1, K - 1)
    x0 = xp[idx - 1]; x1 = xp[idx]
    y0 = fp[idx - 1]; y1 = fp[idx]
    w = (xc - x0) / (x1 - x0).clamp_min(1e-9)
    return y0 + w * (y1 - y0)


def _interp1d_rows(x, xp_rows, fp_rows):
    """Per-corner clamped 1-D interp. x:[N,4]; xp_rows/fp_rows:[4,K] (each corner its own grid).

    Branchless: per-corner searchsorted via a vectorised bucketize over the [N,4] travel against
    each corner's [K] grid. Returns [N,4]."""
    N, C = x.shape
    K = xp_rows.shape[1]
    x0 = xp_rows[:, 0]                       # [4]
    xN = xp_rows[:, -1]                      # [4]
    xc = torch.maximum(torch.minimum(x, xN[None, :]), x0[None, :])   # clamp per corner
    # bucket index: count how many grid points are < xc (right=True semantics). xp_rows[None]:[1,4,K]
    # compare [N,4,1] > [1,4,K] -> sum over K
    ge = (xc.unsqueeze(-1) >= xp_rows.unsqueeze(0)).sum(dim=-1)      # [N,4] in [1..K]
    idx = ge.clamp(1, K - 1)                                        # bin upper index
    # gather the two bracketing grid/value points per corner
    ar = torch.arange(C, device=x.device)
    xa = xp_rows[ar, idx - 1]; xb = xp_rows[ar, idx]                # [N,4]
    fa = fp_rows[ar, idx - 1]; fb = fp_rows[ar, idx]
    w = (xc - xa) / (xb - xa).clamp_min(1e-9)
    return fa + w * (fb - fa)


def _interp2d_bilinear(x, y, xp, yp, table):
    """Branchless bilinear interp of table[i_x,j_y] at (x,y). Clamped. (same as pwr)"""
    Kx = xp.shape[0]; Ky = yp.shape[0]
    xc = x.clamp(xp[0], xp[-1]); yc = y.clamp(yp[0], yp[-1])
    ix = torch.searchsorted(xp, xc.contiguous(), right=True).clamp(1, Kx - 1)
    iy = torch.searchsorted(yp, yc.contiguous(), right=True).clamp(1, Ky - 1)
    x0 = xp[ix - 1]; x1 = xp[ix]; y0 = yp[iy - 1]; y1 = yp[iy]
    wx = (xc - x0) / (x1 - x0).clamp_min(1e-12)
    wy = (yc - y0) / (y1 - y0).clamp_min(1e-12)
    flat = table.reshape(-1)
    corner = lambda a, b: flat[a * Ky + b]   # noqa: E731
    f00 = corner(ix - 1, iy - 1); f10 = corner(ix, iy - 1)
    f01 = corner(ix - 1, iy); f11 = corner(ix, iy)
    f0 = f00 + wx * (f10 - f00); f1 = f01 + wx * (f11 - f01)
    return f0 + wy * (f1 - f0)


# --------------------------------------------------------------------------- powertrain (from pwr)
def _engine_torque(rpm, throttle, P):
    rpm_c = torch.minimum(rpm.clamp_min(0.0), P["max_engine_rpm"])
    full = _interp1d(rpm_c, P.luts["eng_rpm"], P.luts["eng_full"])
    brake = _interp1d(rpm_c, P.luts["ebr_rpm"], P.luts["ebr_tq"])
    return (1.0 - throttle) * brake + throttle * full


def _gear_ratio(gear, P):
    return P.luts["ratios"][gear]


def _update_gear(gear, motor_rpm, P):
    up = (motor_rpm > P.luts["shift_up"][gear]) & (gear < 5)
    down = (motor_rpm < P.luts["shift_down"][gear]) & (gear > 0)
    return gear + up.long() - down.long()


# --------------------------------------------------------------------------- tyre force (from pwr)
def _wheel_forces(sx, alpha, fz, mu_scale, P, grip_scale):
    """Per-wheel combined-slip Fx,Fy from the EXACT TMeasy curves. sx/alpha/fz/[...] are [N,4]
    (or any broadcastable shape). Identical force law to gpu_physics_pwr._wheel_forces."""
    fz_grid = P.luts["tm_fz_grid"]
    kappa_grid = P.luts["tm_kappa_grid"]
    alpha_grid = P.luts["tm_alpha_grid"]
    fz_c = fz.clamp(fz_grid[0], fz_grid[-1])

    kappa_pk = _interp1d(fz_c, fz_grid, P.luts["tm_kappa_peak"]).abs().clamp_min(0.02)
    alpha_pk = _interp1d(fz_c, fz_grid, P.luts["tm_alpha_peak"]).abs().clamp_min(0.02)

    sy = torch.tan(alpha.clamp(-1.45, 1.45))
    nx = sx / kappa_pk
    ny = sy / torch.tan(alpha_pk)
    s_comb = torch.sqrt(nx * nx + ny * ny + 1e-12)
    cx = nx / s_comb
    cy = ny / s_comb

    kappa_eval = s_comb * kappa_pk
    alpha_eval = torch.atan(s_comb * torch.tan(alpha_pk)).clamp(alpha_grid[0], alpha_grid[-1])

    fx_ratio = _interp2d_bilinear(kappa_eval.clamp(kappa_grid[0], kappa_grid[-1]), fz_c,
                                  kappa_grid, fz_grid, P.luts["tm_fx_ratio"])
    fy_ratio = _interp2d_bilinear(alpha_eval, fz_c, alpha_grid, fz_grid, P.luts["tm_fy_ratio"])
    fx0 = fx_ratio.abs() * fz * mu_scale
    fy0 = fy_ratio.abs() * fz * mu_scale * grip_scale
    return fx0 * cx, -fy0 * cy


def _sigma_at(fz, P, channel):
    fz_grid = P.luts["tm_fz_grid"]
    fz_c = fz.clamp(fz_grid[0], fz_grid[-1])
    lut = P.luts["tm_sigma_alpha_fz"] if channel == "alpha" else P.luts["tm_sigma_kappa_fz"]
    return (_interp1d(fz_c, fz_grid, lut) * P["sigma_scale"]).clamp_min(0.02)


# ------------------------------------------------------------------------- corner kinematics
def _corner_arms(P):
    """CG-relative static corner lever arms (x fwd, y left) as [N,4] tensors.

    x: front corners at +lf, rear at -lr (lf=share*L ... using front_axle_share so the model is
    reparameterisable per vehicle). y: from the measured static wheel_y (track), sign per corner."""
    L = P["wheelbase"][:, None]                       # [N,1]
    share_f = P["front_axle_share"][:, None]
    lf = (1.0 - share_f) * L                           # CG->front axle = lr_frac*L (share is front LOAD)
    lr = share_f * L                                   # CG->rear axle
    # NOTE: with front_axle_share = static FRONT load fraction, the CG sits closer to the front,
    # so the CG->front distance lf = (1-share_f)*L and CG->rear lr = share_f*L (lever-arm balance).
    fm = P.corner["front_mask"][None, :]               # [1,4]
    x_arm = fm * lf + (1.0 - fm) * (-lr)               # [N,4]
    half_tf = 0.5 * P["track_f"][:, None]
    half_tr = 0.5 * P["track_r"][:, None]
    lm = P.corner["left_mask"][None, :]
    half_track = fm * half_tf + (1.0 - fm) * half_tr
    y_arm = (2.0 * lm - 1.0) * half_track              # +half on left (+y), -half on right
    return x_arm, y_arm


def _continuous_derivs(s_dyn, steer, throttle, brake, gear, P, h,
                       alpha_f_lag, alpha_r_lag, sx_f_lag):
    """6-DOF chassis + 4-corner derivatives at the current state. All inputs [N] / [N,4].

    s_dyn packs (z, roll, pitch, vx, vy, vz, wx, wy, wz, zc[N,4], zd[N,4], om[N,4]).
    Returns the time-derivatives + the advanced relaxation slips + diagnostics.
    """
    (z, roll, pitch, vx, vy, vz, wx, wy, wz, zc, zd, om) = s_dyn
    mu_scale = (P.mu / P["mu0"])[:, None]               # [N,1]
    g = P["gravity"]
    N = vx.shape[0]
    ar = torch.arange(4, device=vx.device)

    x_arm, y_arm = _corner_arms(P)                     # [N,4] CG-relative

    # ---- corner vertical kinematics: chassis pose -> corner travel target ----
    # vertical displacement of the chassis mount above each corner (small-angle):
    #   dz_mount = z_cg + x_arm*pitch_down - y_arm*roll  ... sign conventions below.
    # roll(+) = right side down (+ve roll about +x => left up / right down in this body frame);
    # pitch(+) = nose up. The corner travel is the chassis mount sinking onto the wheel = +jounce.
    # zc is the STATE travel; the kinematics only enter via the corner velocity (the vertical
    # dynamics integrate zc), so here we form the corner vertical velocity from the chassis motion.
    zc_t = P.corner["z_grid"]                          # [4,K]
    Cz = P.luts["tm_Cz"]

    # ---- contact-patch vertical load vs travel (measured curve) ----
    fz_meas = _interp1d_rows(zc, zc_t, P.corner["fz_curve"])    # [N,4] contact Fz(travel)
    # damper force at the wheel from the travel rate (measured shock coeff * MR^2)
    c_wheel = P.corner["c_wheel"][None, :]                      # [1,4]
    fz_damp = c_wheel * zd                                      # [N,4]
    fz_slow = (fz_meas + fz_damp).clamp_min(1.0)                # per-corner normal load (slow roll-DOF)
    # ---- T3a FALSIFICATION: inject the INSTANTANEOUS quasi-static GEOMETRIC load transfer ----
    # The dig localized tier_a's drift regression (beta@24 0.0756 vs pwr3 0.028) to the load-transfer
    # PATH: Chrono's lateral transfer is ~99% instantaneous-geometric, but tier_a routes it through the
    # SLOW chassis roll DOF, so the per-corner Fz lags during the fast drift. Here we bypass the slow
    # travel-based Fz and use pwr3's exact quasi-static path with an INSTANTANEOUS ay~vx*wz (centripetal)
    # and ax~-vy*wz (coriolis). If this closes the drift regression, the load-transfer-path hypothesis is
    # confirmed and the full-DAE (real geometric linkage) would capture it -> T3 GO. Else -> NO-GO.
    m = P["mass"]; hcg = P["h_cg"]; L = P["wheelbase"]
    trf = P["track_f"]; trr = P["track_r"]; sf = P["front_axle_share"]
    ay_geom = (vx * wz)[:, None]                                # [N,1] body centripetal lateral accel
    ax_geom = (-vy * wz)[:, None]                               # [N,1] coriolis longitudinal (drift: small)
    static = P.corner["static_fz"][None, :]                     # [1,4] FL,FR,RL,RR
    front = torch.tensor([1., 1., 0., 0.], device=vx.device, dtype=vx.dtype)[None, :]
    left = torch.tensor([1., 0., 1., 0.], device=vx.device, dtype=vx.dtype)[None, :]
    dFz_long = m[:, None] * ax_geom * hcg[:, None] / L[:, None]              # [N,1] +ax loads rear
    dFz_lat_f = m[:, None] * ay_geom * hcg[:, None] / trf[:, None] * sf[:, None]
    dFz_lat_r = m[:, None] * ay_geom * hcg[:, None] / trr[:, None] * (1.0 - sf[:, None])
    fz_long = -0.5 * dFz_long * front + 0.5 * dFz_long * (1.0 - front)       # front unloads, rear loads
    lat_axle = dFz_lat_f * front + dFz_lat_r * (1.0 - front)
    fz_lat = -lat_axle * left + lat_axle * (1.0 - left)                      # +ay loads right (non-left)
    fz_geom = (static + fz_long + fz_lat).clamp_min(1.0)
    fz = fz_geom if GEOMETRIC_FZ else fz_slow                  # per-corner normal load

    # ---- corner camber / toe vs travel (bump steer) ----
    camber = P.corner["static_camber"][None, :] + (
        _interp1d_rows(zc, zc_t, P.corner["camber"]) - P.corner["static_camber"][None, :])
    bump_toe = _interp1d_rows(zc, zc_t, P.corner["toe"])        # [N,4] rad (incl. static)

    # ---- front road-wheel steer: planar base (= filtered steer, road-wheel rad) + MEASURED
    #      Ackermann DIFFERENTIAL. The filtered ``steer`` IS the road-wheel steer angle (the action
    #      is mapped through max_steer exactly as the data-generating Chrono / planar model), so the
    #      AVERAGE front road-wheel angle = steer (faithful to the actions that produced the data).
    #      The toe-vs-steer table (TOE convention, |.| = the wheel's deflection) gives only the small
    #      inner/outer ACKERMANN SPREAD d = 0.5*(|toe_FL| - |toe_FR|) (~+-2.3 deg at full lock,
    #      inner steers more): delta_FL = steer + sgn*d_fl, delta_FR = steer + sgn*d_fr with the
    #      spread centred so the mean stays = steer. This adds the real Ackermann the planar model
    #      omitted WITHOUT importing the linkage's overall steering-gain (which the action mapping
    #      already accounts for). ----
    steer_ang = P.corner["steer_ang"]                          # [21]
    sgn = torch.sign(steer + 1e-12)
    toe_fl = _interp1d(steer, steer_ang, P.corner["toe_vs_steer"][0]).abs()   # [N] |deflection| (rad)
    toe_fr = _interp1d(steer, steer_ang, P.corner["toe_vs_steer"][1]).abs()
    ack_mean = 0.5 * (toe_fl + toe_fr)                         # symmetric magnitude
    # Ackermann spread d (inner-outer split); applied at a small gain so the front lateral stays
    # symmetric to leading order (the spread is a second-order toe effect, not a steering-gain).
    d_fl = (toe_fl - ack_mean) * ACKERMANN_GAIN
    d_fr = (toe_fr - ack_mean) * ACKERMANN_GAIN
    delta = torch.zeros(N, 4, device=vx.device, dtype=vx.dtype)
    delta[:, 0] = steer + sgn * d_fl
    delta[:, 1] = steer + sgn * d_fr

    # ---- contact-point velocity in the body frame (6-DOF rigid body) ----
    # v_contact = v_cg + omega x r, with r = (x_arm, y_arm, -h_cg). The slip uses the in-plane
    # (x,y) components at each contact; with roll/pitch the contact x/y velocity picks up the
    # extra wz*r and roll/pitch coupling the planar model could not represent.
    h_cg = P["h_cg"][:, None]
    rz = -h_cg.expand(N, 4)
    wx4 = wx[:, None]; wy4 = wy[:, None]; wz4 = wz[:, None]
    vcx = vx[:, None] + (wy4 * rz - wz4 * y_arm)
    vcy = vy[:, None] + (wz4 * x_arm - wx4 * rz)

    # ---- slip angles per corner (wheel frame: subtract the road-wheel steer delta) ----
    sign = torch.where(vcx.abs() > 1e-6, torch.sign(vcx), torch.ones_like(vcx))
    vcx_safe = sign * vcx.abs().clamp_min(0.75)
    alpha_inst = torch.atan2(vcy, vcx_safe.abs()) - delta   # [N,4]
    alpha_f_inst = 0.5 * (alpha_inst[:, 0] + alpha_inst[:, 1])
    alpha_r_inst = 0.5 * (alpha_inst[:, 2] + alpha_inst[:, 3])

    # ---- LONGITUDINAL slip: KEEP the planar gpu_physics_pwr treatment (rear omega pair + measured
    #      FRONT friction cap). The Sedan is FWD, but the planar pwr model -- which passes drift --
    #      carries the drive longitudinal slip on the REAR-omega pair (om[2],om[3]) and caps the net
    #      drive force by the measured FRONT friction circle (the Sedan's traction-limited driven
    #      axle). Tier-a carries that powertrain UNCHANGED (per the build spec: keep tyre/powertrain/
    #      relaxation) and only swaps the QUASI-STATIC Fz for the chassis-6DOF per-corner Fz. The
    #      rear contact long. velocity uses the 6-DOF contact vx (so the per-corner load + roll still
    #      enter the rear long. slip), but the omega DYNAMICS / drive / cap are pwr's. ----
    r_eff = P["r_eff"][:, None]
    om_rl = om[:, 2]; om_rr = om[:, 3]
    vx_rl = vcx[:, 2]; vx_rr = vcx[:, 3]
    vx_rl_safe = torch.sign(vx_rl) * vx_rl.abs().clamp_min(0.75)
    vx_rr_safe = torch.sign(vx_rr) * vx_rr.abs().clamp_min(0.75)
    sx_rl_inst = (r_eff.squeeze(-1) * om_rl - vx_rl) / vx_rl_safe.abs().clamp_min(0.5)
    sx_rr_inst = (r_eff.squeeze(-1) * om_rr - vx_rr) / vx_rr_safe.abs().clamp_min(0.5)

    # ---- SLIP RELAXATION (measured sigma; carried from pwr): front/rear lateral + the two rear
    #      longitudinal lags. (sx_f_lag now holds the rear-pair longitudinal lags packed L|R via a
    #      length-2 view; we keep two scalars by reusing the same carried state for L and a derived
    #      R -- but to stay faithful to pwr's two independent rear long lags we store them in the
    #      single sx_f_lag slot as the MEAN and reconstruct per-wheel from the instantaneous spread.)
    v_relax = vx.abs().clamp_min(1.0)
    fz_f = 0.5 * (fz[:, 0] + fz[:, 1])
    fz_rl = fz[:, 2]; fz_rr = fz[:, 3]
    sig_a_f = _sigma_at(fz_f, P, "alpha")
    sig_a_r = _sigma_at(0.5 * (fz_rl + fz_rr), P, "alpha")
    sig_k_rl = _sigma_at(fz_rl, P, "kappa")
    sig_k_rr = _sigma_at(fz_rr, P, "kappa")
    af = 1.0 - torch.exp(-(v_relax / sig_a_f) * h)
    arr = 1.0 - torch.exp(-(v_relax / sig_a_r) * h)
    krl = 1.0 - torch.exp(-(v_relax / sig_k_rl) * h)
    krr = 1.0 - torch.exp(-(v_relax / sig_k_rr) * h)
    alpha_f_lag = alpha_f_lag + af * (alpha_f_inst - alpha_f_lag)
    alpha_r_lag = alpha_r_lag + arr * (alpha_r_inst - alpha_r_lag)
    # rear long. lags packed in sx_f_lag (mean) + reconstruct per-wheel spread instantaneously.
    sx_r_mean_inst = 0.5 * (sx_rl_inst + sx_rr_inst)
    kr = 0.5 * (krl + krr)
    sx_f_lag = sx_f_lag + kr * (sx_r_mean_inst - sx_f_lag)
    sx_rl_lag = sx_f_lag + (sx_rl_inst - sx_r_mean_inst)
    sx_rr_lag = sx_f_lag + (sx_rr_inst - sx_r_mean_inst)

    # per-corner lagged slip angle (preserve each corner's Fz/steer asymmetry about the axle mean).
    alpha_lag = alpha_inst.clone()
    alpha_lag[:, 0] = alpha_f_lag + (alpha_inst[:, 0] - alpha_f_inst)
    alpha_lag[:, 1] = alpha_f_lag + (alpha_inst[:, 1] - alpha_f_inst)
    alpha_lag[:, 2] = alpha_r_lag + (alpha_inst[:, 2] - alpha_r_inst)
    alpha_lag[:, 3] = alpha_r_lag + (alpha_inst[:, 3] - alpha_r_inst)

    # ---- tyre forces (ALL 4 CORNERS in ONE batched call over the [N,4] corner dim) ----
    # Front wheels carry NO longitudinal-slip force in the pwr powertrain (the drive enters via the
    # FRONT friction CAP, and the front is the lateral axle), so their sx is 0; the rear pair carry
    # the relaxed drive longitudinal slip. Per-wheel grip scale = front/rear scale by the corner mask.
    sx_all = torch.stack([torch.zeros_like(sx_rl_lag), torch.zeros_like(sx_rr_lag),
                          sx_rl_lag, sx_rr_lag], dim=1)        # [N,4]
    grip = torch.where(P.corner["front_mask"][None, :] > 0.5,
                       P["front_grip_scale"][:, None], P["rear_grip_scale"][:, None])   # [N,4]
    fx_w, fy_w = _wheel_forces(sx_all, alpha_lag, fz, mu_scale, P, grip)   # [N,4] each
    # named handles for the front-cap (which needs the two front lateral forces explicitly).
    fy_fl = fy_w[:, 0]; fy_fr = fy_w[:, 1]; fx_rl = fx_w[:, 2]; fx_rr = fx_w[:, 3]
    gsf = P["front_grip_scale"]

    # ---- rotate wheel-frame forces into the body frame by the per-corner steer delta ----
    cs = torch.cos(delta); sn = torch.sin(delta)
    fx_b = fx_w * cs - fy_w * sn       # [N,4]
    fy_b = fx_w * sn + fy_w * cs

    # ---- chassis resistance (drag=0, rolling) on the body x ----
    drag = P["drag_coeff"] * vx * vx.abs()
    rolling = P["rolling_resist_coeff"] * P["mass"] * g * torch.tanh(vx)

    # ---- net body forces / moments about CG ----
    Fx_body = fx_b.sum(dim=1) - drag - rolling
    Fy_body = fy_b.sum(dim=1)
    # vertical: sum corner loads - weight (corner loads already are contact normal forces)
    Fz_body = fz.sum(dim=1) - P["mass"] * g

    # moments about CG: roll (x), pitch (y), yaw (z).
    # Mx (roll) = sum( y_arm * Fz - rz * Fy )   (Fz acts up at the contact, lever y; Fy lever -h)
    # My (pitch)= sum( rz * Fx - x_arm * Fz )
    # Mz (yaw)  = sum( x_arm * Fy - y_arm * Fx )
    Mx = (y_arm * fz - rz * fy_b).sum(dim=1)
    My = (rz * fx_b - x_arm * fz).sum(dim=1)
    # yaw moment: the lateral-force term (x_arm*Fy) is the primary; the longitudinal-force term
    # (-y_arm*Fx) is the per-wheel-drive/brake differential yaw (small for an open diff, but the
    # dynamic L/R load split makes the two driven-wheel Fx unequal). It is scaled by yaw_fx_scale
    # (default 1.0 = full rigid-body moment).
    Mz = (x_arm * fy_b - YAW_FX_SCALE * y_arm * fx_b).sum(dim=1)

    m = P["mass"]; Ixx = P["ixx"]; Iyy = P["iyy"]; Izz = P["izz"]
    ax_body = Fx_body / m
    ay_body = Fy_body / m
    az_body = Fz_body / m

    # rigid-body translational EOM in the (yaw-following) body frame incl. Coriolis from yaw & roll/pitch
    vx_dot = ax_body + wz * vy - wy * vz
    vy_dot = ay_body + wx * vz - wz * vx
    vz_dot = az_body + wy * vx - wx * vy
    # rotational EOM (Euler, diagonal inertia approx -- the off-diagonal products are small here)
    wx_dot = (Mx - (Izz - Iyy) * wy * wz) / Ixx
    wy_dot = (My - (Ixx - Izz) * wz * wx) / Iyy
    wz_dot = (Mz - (Iyy - Ixx) * wx * wy) / Izz

    # ---- corner vertical KINEMATICS (Tier-a kinematic-suspension reduction) ----
    # The corner travel is RIGIDLY tied to the chassis pose: with the wheel held on the ground, a
    # corner's suspension travel = how far the chassis mount has sunk toward the (ground-fixed)
    # wheel. The mount's vertical velocity (z-comp of v_cg + omega x r, r=(x_arm,y_arm,-h_cg)) is
    #   vmount_z = vz + (wx*y_arm - wy*x_arm).
    # +jounce (travel +) is the mount moving DOWN, so zc_dot = -vmount_z. We integrate zc from this
    # kinematic rate (the chassis roll/pitch/heave dynamics ARE the load transfer); zd carries the
    # SAME kinematic travel rate so the measured shock damper c_wheel*zd is the real damping force.
    # This removes the spurious stiff (~70 Hz) unsprung-tyre hop mode that explicit Euler can't hold
    # at the Sedan control rate while KEEPING the dynamic, roll/pitch-driven per-corner load
    # transfer (the residual the planar quasi-static model omitted). m_uns is unused at this tier
    # (kept for a future Tier-a+ second-order corner if a corner needs the wheel-hop mode).
    vmount_z = vz[:, None] + (wx[:, None] * y_arm - wy[:, None] * x_arm)  # [N,4]
    zc_dot = -vmount_z
    zd_target = zc_dot                                  # the kinematic travel rate (for the damper)

    # ---- powertrain (KEEP gpu_physics_pwr exactly: rear-omega drive + MEASURED FRONT traction cap) ----
    # The drive longitudinal slip lives on the rear-omega pair om[2],om[3]; the net per-wheel drive
    # force is capped by the FRONT friction circle sqrt((mu*Fz_front)^2 - Fy_front^2) -- the Sedan's
    # measured front-axle traction limit (the planar pwr fix that closes the avoid over-force without
    # breaking drift). The ONLY Tier-a change vs pwr: Fz_front / Fz_rear are now the chassis-6DOF
    # per-corner DYNAMIC loads, not the quasi-static m*a*h/L transfer.
    om_axle = 0.5 * (om_rl + om_rr)
    ratio = _gear_ratio(gear, P)
    motor_rad = om_axle / P["final_drive"].clamp_min(1e-3) / ratio.clamp_min(1e-3)
    motor_rpm = (motor_rad.abs() * 60.0 / (2.0 * torch.pi)).clamp(P["idle_rpm"], P["max_engine_rpm"])
    T_eng = _engine_torque(motor_rpm, throttle, P)
    T_axle = T_eng / ratio.clamp_min(1e-3) / P["final_drive"].clamp_min(1e-3)
    T_wheel = 0.5 * T_axle                            # open diff splits equally

    # MEASURED FRONT-AXLE traction cap (friction circle, floored at half mu*Fz; same as pwr) -- but
    # SYMMETRIC over the two driven wheels. The Sedan front differential is OPEN, so it delivers
    # EQUAL torque to both front wheels; the relevant traction limit is the front AXLE budget, the
    # SUM of the two front friction circles. Capping each rear drive wheel by its own-side front
    # load (as the planar pwr did with its quasi-static, near-symmetric front loads) becomes
    # unstable here because the Tier-a DYNAMIC lateral load transfer makes the front L/R loads very
    # unequal in a hard corner -> a large L/R drive-torque split -> a spurious self-sustaining spin.
    # Using the front-axle TOTAL budget per driven wheel keeps the measured front traction limit
    # (closes the avoid over-force) without the per-side asymmetry that an open diff cannot produce.
    mu0 = P["mu0"]
    fmu_fl = mu_scale.squeeze(-1) * mu0 * fz[:, 0] * gsf
    fmu_fr = mu_scale.squeeze(-1) * mu0 * fz[:, 1] * gsf
    fx_cap_l = torch.sqrt((fmu_fl * fmu_fl - fy_fl * fy_fl).clamp_min(0.0) + 1.0).clamp_min(0.5 * fmu_fl)
    fx_cap_r = torch.sqrt((fmu_fr * fmu_fr - fy_fr * fy_fr).clamp_min(0.0) + 1.0).clamp_min(0.5 * fmu_fr)
    # symmetric per-driven-wheel cap = half the front-axle total budget (open diff => equal torque).
    T_cap = 0.5 * (fx_cap_l + fx_cap_r) * r_eff.squeeze(-1)
    T_wheel_l = torch.clamp(T_wheel, -T_cap, T_cap)
    T_wheel_r = torch.clamp(T_wheel, -T_cap, T_cap)

    T_brake = brake * P["max_brake_torque"]
    T_brake_rl = T_brake * torch.sign(om_rl)
    T_brake_rr = T_brake * torch.sign(om_rr)
    om_rl_dot = (T_wheel_l - r_eff.squeeze(-1) * fx_rl - T_brake_rl) / P["i_wheel"]
    om_rr_dot = (T_wheel_r - r_eff.squeeze(-1) * fx_rr - T_brake_rr) / P["i_wheel"]
    # front wheels are kinematically rolling (om_f = vx/r_eff): they carry no drive-omega state in
    # the pwr powertrain. We return the front rolling-speed TARGET so the step sets it directly (a
    # stiff (target-om)/h derivative would be a non-physical fast mode); the gear FSM / diagnostics
    # then read a sane front wheel speed.
    om_f_target = vcx[:, :2].mean(dim=1) / r_eff.squeeze(-1)
    om_dot = torch.zeros(N, 4, device=vx.device, dtype=vx.dtype)
    om_dot[:, 2] = om_rl_dot
    om_dot[:, 3] = om_rr_dot

    derivs = dict(
        z_dot=vz, roll_dot=wx, pitch_dot=wy,
        vx_dot=vx_dot, vy_dot=vy_dot, vz_dot=vz_dot,
        wx_dot=wx_dot, wy_dot=wy_dot, wz_dot=wz_dot,
        zc_dot=zc_dot, zd_target=zd_target, om_dot=om_dot, om_f_target=om_f_target,
    )
    diag = dict(fz=fz, ax_body=ax_body, ay_body=ay_body, roll=roll, pitch=pitch,
                motor_rpm=motor_rpm)
    return derivs, alpha_f_lag, alpha_r_lag, sx_f_lag, diag


# --------------------------------------------------------------------------------- step
def physics_step(state: torch.Tensor, action: torch.Tensor, gear: torch.Tensor,
                 P: TierAParamBatch, dt: float):
    """One control step of the Tier-a chassis-6DOF + 4-corner model, batched over N.

    state [N,30], action [N,3] (steer,throttle,brake in [-1,1]), gear int64 [N].
    Returns (next_state[N,30], next_gear[N], diagnostics dict)."""
    s = state
    N = s.shape[0]
    dev, dt_ = s.device, s.dtype

    # unpack chassis
    yaw = s[:, IDX["yaw"]]
    vx = s[:, IDX["vx"]]; vy = s[:, IDX["vy"]]; vz = s[:, IDX["vz"]]
    wx = s[:, IDX["wx"]]; wy = s[:, IDX["wy"]]; wz = s[:, IDX["wz"]]
    z = s[:, IDX["z"]]; roll = s[:, IDX["roll"]]; pitch = s[:, IDX["pitch"]]
    zc = s[:, _ZC[0]:_ZC[3] + 1].clone()        # [N,4]
    zd = s[:, _ZD[0]:_ZD[3] + 1].clone()
    om = s[:, _OM[0]:_OM[3] + 1].clone()
    steer = s[:, IDX["steer"]]; throttle = s[:, IDX["throttle"]]; brake = s[:, IDX["brake"]]
    alpha_f_lag = s[:, IDX["alpha_f_lag"]]
    alpha_r_lag = s[:, IDX["alpha_r_lag"]]
    sx_f_lag = s[:, IDX["sx_f_lag"]]

    # ---- actuator filters (mirror gpu_physics_pwr) ----
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

    # ---- gear FSM once per control step (rear-omega axle, as in gpu_physics_pwr) ----
    om_axle = 0.5 * (om[:, 2] + om[:, 3])
    ratio0 = _gear_ratio(gear, P)
    motor_rad = om_axle / P["final_drive"].clamp_min(1e-3) / ratio0.clamp_min(1e-3)
    motor_rpm = (motor_rad.abs() * 60.0 / (2.0 * torch.pi)).clamp(P["idle_rpm"], P["max_engine_rpm"])
    new_gear = _update_gear(gear, motor_rpm, P)

    # ---- sub-stepped semi-implicit Euler ----
    nsub = max(int(P.substeps), 1)
    h = dt / nsub
    diag = {}
    for _ in range(nsub):
        s_dyn = (z, roll, pitch, vx, vy, vz, wx, wy, wz, zc, zd, om)
        derivs, alpha_f_lag, alpha_r_lag, sx_f_lag, diag = _continuous_derivs(
            s_dyn, new_steer, new_throttle, new_brake, new_gear, P, h,
            alpha_f_lag, alpha_r_lag, sx_f_lag,
        )
        vx = vx + h * derivs["vx_dot"]
        vy = vy + h * derivs["vy_dot"]
        vz = vz + h * derivs["vz_dot"]
        wx = wx + h * derivs["wx_dot"]
        wy = wy + h * derivs["wy_dot"]
        wz = wz + h * derivs["wz_dot"]
        z = z + h * derivs["z_dot"]
        roll = roll + h * derivs["roll_dot"]
        pitch = pitch + h * derivs["pitch_dot"]
        zc = (zc + h * derivs["zc_dot"]).clamp(-0.069, 0.069)
        zd = derivs["zd_target"]          # kinematic travel rate (drives the measured shock damper)
        om = om + h * derivs["om_dot"]
        om[:, 0] = derivs["om_f_target"]  # front wheels roll kinematically (no drive-omega state)
        om[:, 1] = derivs["om_f_target"]

    # ---- pose integration (yaw on the ground; planar x,y for the gate) ----
    new_yaw = yaw + dt * wz
    new_x = s[:, IDX["x"]] + dt * (vx * torch.cos(yaw) - vy * torch.sin(yaw))
    new_y = s[:, IDX["y"]] + dt * (vx * torch.sin(yaw) + vy * torch.cos(yaw))

    out = state.clone()
    out[:, IDX["x"]] = new_x; out[:, IDX["y"]] = new_y; out[:, IDX["z"]] = z
    out[:, IDX["roll"]] = roll; out[:, IDX["pitch"]] = pitch; out[:, IDX["yaw"]] = new_yaw
    out[:, IDX["vx"]] = vx; out[:, IDX["vy"]] = vy; out[:, IDX["vz"]] = vz
    out[:, IDX["wx"]] = wx; out[:, IDX["wy"]] = wy; out[:, IDX["wz"]] = wz
    out[:, _ZC[0]:_ZC[3] + 1] = zc
    out[:, _ZD[0]:_ZD[3] + 1] = zd
    out[:, _OM[0]:_OM[3] + 1] = om
    out[:, IDX["steer"]] = new_steer
    out[:, IDX["throttle"]] = new_throttle
    out[:, IDX["brake"]] = new_brake
    out[:, IDX["alpha_f_lag"]] = alpha_f_lag
    out[:, IDX["alpha_r_lag"]] = alpha_r_lag
    out[:, IDX["sx_f_lag"]] = sx_f_lag

    diag_out = {"motor_rpm": motor_rpm, "gear": new_gear,
                "fz": diag.get("fz"), "roll": roll, "pitch": pitch,
                "ax_body": diag.get("ax_body"), "ay_body": diag.get("ay_body")}
    return out, new_gear, diag_out


def init_state(vx0: torch.Tensor, vy0: torch.Tensor, yaw_rate0: torch.Tensor, P: TierAParamBatch):
    """Build an [N,30] initial state + gear from initial planar velocity (vx,vy,yaw_rate).

    The chassis settles to its static heave/corner travel (travel=0 = gravity-settled ride height);
    wheel omega seeded to vx/r_eff; relaxation slips seeded to instantaneous; gear seeded to the
    band-consistent gear (same logic as gpu_physics_pwr)."""
    n = vx0.shape[0]
    dev, dt_ = P.device, P.dtype
    st = torch.zeros(n, TIER_A_STATE_DIM, device=dev, dtype=dt_)
    st[:, IDX["vx"]] = vx0
    st[:, IDX["vy"]] = vy0
    st[:, IDX["wz"]] = yaw_rate0           # yaw_rate is body wz
    st[:, IDX["z"]] = 0.0                   # static ride height datum
    # corner travels start at the gravity-settled point (travel=0 == the static curve point).
    for j, c in zip(_OM, range(4)):
        st[:, j] = vx0 / P["r_eff"]

    # seed gear (lowest gear not exceeding its up-threshold at this wheel speed)
    om_axle = vx0 / P["r_eff"]
    ratios = P.luts["ratios"]
    motor_rpm_g = (om_axle[:, None] / P["final_drive"][:, None].clamp_min(1e-3)
                   / ratios[None, :].clamp_min(1e-3)).abs() * 60.0 / (2.0 * torch.pi)
    up = P.luts["shift_up"][None, :]
    ok = motor_rpm_g <= up
    gear = torch.where(ok.any(dim=1), ok.float().argmax(dim=1),
                       torch.full((n,), 5, device=dev)).long()

    # seed relaxation slips to instantaneous (front/rear axle slip; steer=0 at init)
    L = P["wheelbase"]
    share_f = P["front_axle_share"]
    lf = (1.0 - share_f) * L
    lr = share_f * L
    vx_safe = torch.sign(vx0) * vx0.abs().clamp_min(0.75)
    alpha_f0 = torch.atan2(vy0 + lf * yaw_rate0, vx_safe.abs())
    alpha_r0 = torch.atan2(vy0 - lr * yaw_rate0, vx_safe.abs())
    st[:, IDX["alpha_f_lag"]] = alpha_f0
    st[:, IDX["alpha_r_lag"]] = alpha_r0
    st[:, IDX["sx_f_lag"]] = 0.0
    return st, gear
