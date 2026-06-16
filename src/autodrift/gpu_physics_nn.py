"""NN-FITTED-TMeasy branchless GPU physics vehicle-dynamics model for AutoDrift (faithful rewrite).

This is the NN-tyre sibling of ``autodrift.gpu_physics_tmeasy`` (the TABLE variant). Both are
faithful rewrites of ``gpu_physics``: where ``gpu_physics`` uses a Magic-Formula (Pacejka) tyre
*calibrated* to TMeasy peaks with fudge factors (``front_grip_scale``/``rear_grip_scale``,
``pac_Dy``/``pac_By`` tuned down), these two modules replace the tyre with Chrono's **EXACT
TMeasy force curves**, sampled directly off the running Chrono Sedan TMeasy tyre by
``scripts/feasibility_audit/extract_chrono_tmeasy_curves.py`` and saved to
``runs/feasibility_audit/phase4_f2/chrono_tmeasy_curves.npz``.

The ONLY difference between this module and ``gpu_physics_tmeasy`` is the tyre force-ratio
representation: the TABLE variant bilinear-interpolates the sampled ``Fx/Fz(kappa, Fz)`` and
``Fy/Fz(alpha, Fz)`` surfaces; THIS variant evaluates two small fitted MLPs at the runtime
``(slip, Fz)`` every sub-step (a true runtime NN tyre, branchless and batched). The MLPs are
fitted to the same sampled curve points (slip + actual Fz -> force ratio) by
``scripts/feasibility_audit/fit_tmeasy_tyre_nn.py`` and loaded from
``runs/feasibility_audit/phase4_f2/tmeasy_tyre_nn.pt``. The whole point is a head-to-head
comparison of the TWO tyre representations against the same gate; if the NN matches the table
(~0.04 beta@24 p90), the residual is representation-invariant (i.e. NOT the tyre).

Combined slip uses the same slip-vector projection the TABLE variant uses (mirroring Chrono's
``tmxy_combined`` + ``CombinedCoulombForces`` friction ellipse). Terrain friction enters as
``muscale = mu / mu0`` (mu0 = 0.8), exactly as Chrono scales the TMeasy force caps. There are
NO grip fudge factors: ``front_grip_scale = rear_grip_scale = 1.0`` and no ``pac_*``
calibration — the curve IS the Chrono curve.

Everything else (geometry, mass, RWD powertrain, 6-speed auto gearbox, quasi-static load
transfer, relaxation-length transient, sub-stepped semi-implicit integration) is identical to
``gpu_physics`` — only the tyre force law changed. The parameters are the reverse-engineered
Chrono Sedan spec (``docs/chrono-sedan-physics-extracted.json``).

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
from pathlib import Path
from typing import Mapping

import numpy as np
import torch

# Default location of the EXACT TMeasy curves extracted from the running Chrono Sedan tyre.
_CURVE_NPZ = Path(__file__).resolve().parents[2] / "runs/feasibility_audit/phase4_f2/chrono_tmeasy_curves.npz"
# Default location of the fitted NN tyre weights (slip,Fz)->force-ratio, by fit_tmeasy_tyre_nn.py.
_NN_PT = Path(__file__).resolve().parents[2] / "runs/feasibility_audit/phase4_f2/tmeasy_tyre_nn.pt"

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

    # --- tyre (EXACT Chrono TMeasy curves; NO Pacejka calibration, NO grip fudge) ---
    # The pac_* / k_deg fields below are UNUSED by the exact-TMeasy tyre (the force law is the
    # tabulated Chrono curve in chrono_tmeasy_curves.npz). They are retained only so this
    # PhysParams is a drop-in for gpu_physics.PhysParams (same field set / calibration script).
    mu0: float = 0.8               # reference friction (terrain mu enters as scale = mu/mu0)
    pac_Bx: float = 11.0           # UNUSED (exact-TMeasy)
    pac_Cx: float = 1.5            # UNUSED
    pac_Dx: float = 1.32           # UNUSED
    pac_Ex: float = 0.2            # UNUSED
    pac_By: float = 8.0            # UNUSED
    pac_Cy: float = 1.45           # UNUSED
    pac_Dy: float = 1.10           # UNUSED
    pac_Ey: float = -0.5           # UNUSED
    k_deg: float = 0.10            # UNUSED (degressive load dependence is IN the table)
    # tyre relaxation length [m]: lateral force lags slip-angle change over this travel
    # distance (TMeasy transient). Quasi-static is nearly enough; kept from gpu_physics.
    relax_len_f: float = 0.10
    relax_len_r: float = 0.05
    # front/rear lateral grip scales: FAITHFUL REWRITE => both 1.0 (no fudge). The exact
    # TMeasy axle balance comes from the curve + load transfer, not a hand-tuned scale.
    front_grip_scale: float = 1.0
    rear_grip_scale: float = 1.0

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


# cache the raw numpy curve arrays so repeated batch builds don't re-read the npz from disk.
_CURVE_CACHE: dict[str, "np.ndarray"] = {}


def _load_curve_arrays(path: Path | str = _CURVE_NPZ) -> dict[str, "np.ndarray"]:
    """Load (and cache) the extracted EXACT-TMeasy curve arrays from the npz file."""
    key = str(path)
    cached = _CURVE_CACHE.get(key)
    if cached is not None:
        return cached
    d = np.load(path)
    arrays = {k: d[k] for k in d.files}
    _CURVE_CACHE[key] = arrays
    return arrays


# cache the loaded NN tyre payload so repeated batch builds don't re-read the .pt from disk.
_NN_CACHE: dict[str, dict] = {}


def _load_nn_payload(path: Path | str = _NN_PT) -> dict:
    """Load (and cache) the fitted NN-tyre payload (MLP weights + norm stats + arch)."""
    key = str(path)
    cached = _NN_CACHE.get(key)
    if cached is not None:
        return cached
    payload = torch.load(path, map_location="cpu", weights_only=False)
    _NN_CACHE[key] = payload
    return payload


def _nn_luts(payload: dict, device, dtype) -> dict[str, torch.Tensor]:
    """Flatten the two fitted tyre MLPs into branchless LUT tensors for the runtime forward.

    Stores each Linear layer's weight/bias as a stacked LUT list plus the input/output
    normalisation scalars (slip z-score, Fz affine-to-[-1,1], output z-score). The runtime
    forward (``_mlp_forward``) is a plain batched matmul+tanh chain over these — no nn.Module,
    fully branchless and batched over N envs."""
    tt = lambda a: torch.as_tensor(a, device=device, dtype=dtype)  # noqa: E731

    def layer_tensors(state: dict[str, torch.Tensor]) -> tuple[list, list]:
        # nn.Sequential layout: net.0 (Linear), net.1 (Tanh), net.2 (Linear), ... last is Linear.
        ws, bs = [], []
        i = 0
        while f"net.{i}.weight" in state:
            ws.append(tt(state[f"net.{i}.weight"]))   # [out,in]
            bs.append(tt(state[f"net.{i}.bias"]))     # [out]
            i += 2                                    # skip the Tanh between Linears
        return ws, bs

    wx, bx = layer_tensors(payload["mlp_x_state"])
    wy, by = layer_tensors(payload["mlp_y_state"])
    stx, sty = payload["stx"], payload["sty"]
    out = {
        "nn_n_layers_x": len(wx),
        "nn_n_layers_y": len(wy),
    }
    for i, (w, b) in enumerate(zip(wx, bx)):
        out[f"nn_x_w{i}"] = w
        out[f"nn_x_b{i}"] = b
    for i, (w, b) in enumerate(zip(wy, by)):
        out[f"nn_y_w{i}"] = w
        out[f"nn_y_b{i}"] = b
    # normalisation scalars (kept as python floats on the LUT dict; used in the forward).
    out["nn_stx"] = stx
    out["nn_sty"] = sty
    return out


def _curve_luts(arrays: dict[str, "np.ndarray"], device, dtype) -> dict[str, torch.Tensor]:
    """Convert the loaded TMeasy curve arrays into shared LUT tensors for the tyre interpolation.

    The tyre uses pure Fx(kappa,Fz)/Fy(alpha,Fz) surfaces stored as Fx/Fz and Fy/Fz vs the
    REPORTED slip coordinate (so the table is normalised by load and bilinear-interpolated by
    (slip, Fz)). The peak-slip locations are precomputed for the combined-slip projection.

    NOTE (NN variant): the fx_ratio/fy_ratio surfaces are NOT used by the runtime tyre here
    (the MLPs replace them); only the grids + per-load peak-slip locations are used (for the
    same combined-slip projection as the TABLE variant)."""
    fz_grid = np.asarray(arrays["fz_grid"], dtype=np.float64)
    kappa_grid = np.asarray(arrays["kappa_grid"], dtype=np.float64)
    alpha_grid = np.asarray(arrays["alpha_grid"], dtype=np.float64)
    Fx = np.asarray(arrays["Fx"], dtype=np.float64)   # [nK, nF]
    Fy = np.asarray(arrays["Fy"], dtype=np.float64)   # [nA, nF]
    Fz_at_K = np.asarray(arrays["Fz_at_K"], dtype=np.float64)
    Fz_at_A = np.asarray(arrays["Fz_at_A"], dtype=np.float64)
    # store as force RATIOS (Fx/Fz, Fy/Fz) per (slip, Fz) so interpolation by load is exact and
    # the tyre simply multiplies by the wheel's actual Fz at runtime.
    fx_ratio = Fx / np.clip(Fz_at_K, 1.0, None)       # [nK, nF]
    fy_ratio = Fy / np.clip(Fz_at_A, 1.0, None)       # [nA, nF]
    # peak-slip location per Fz column (where each pure curve maxes) for combined-slip normaliser.
    kappa_peak = kappa_grid[np.argmax(np.abs(Fx), axis=0)]    # [nF]
    alpha_peak = alpha_grid[np.argmax(np.abs(Fy), axis=0)]    # [nF]
    tt = lambda a: torch.tensor(a, device=device, dtype=dtype)  # noqa: E731
    return {
        "tm_fz_grid": tt(fz_grid),
        "tm_kappa_grid": tt(kappa_grid),
        "tm_alpha_grid": tt(alpha_grid),
        "tm_fx_ratio": tt(fx_ratio),
        "tm_fy_ratio": tt(fy_ratio),
        "tm_kappa_peak": tt(kappa_peak),
        "tm_alpha_peak": tt(alpha_peak),
        "tm_mu0": tt(float(arrays["mu0"])),
    }


def make_phys_param_batch(
    params: PhysParams | Mapping[str, float],
    n: int,
    *,
    mu: float | torch.Tensor = 0.48,
    device: torch.device | str = "cpu",
    dtype: torch.dtype = torch.float32,
    curves: Path | str | dict | None = None,
    nn_weights: Path | str | dict | None = None,
) -> PhysParamBatch:
    """Broadcast a PhysParams (or dict of scalars/[N] tensors) to a [N] PhysParamBatch.

    ``mu`` is the per-env terrain friction (scalar or [N] tensor). ``curves`` selects the
    extracted TMeasy curve npz (default: chrono_tmeasy_curves.npz next to runs/). ``nn_weights``
    selects the fitted NN-tyre .pt (default: tmeasy_tyre_nn.pt) whose MLPs replace the bilinear
    table lookup at runtime."""
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
    # EXACT-TMeasy curve grids + per-load peak-slip (combined-slip projection). The fx/fy ratio
    # SURFACES are loaded but unused here — the fitted MLPs replace the table lookup.
    if isinstance(curves, dict):
        arrays = curves
    else:
        arrays = _load_curve_arrays(_CURVE_NPZ if curves is None else curves)
    luts.update(_curve_luts(arrays, device, dtype))
    # NN-FITTED tyre: load the two MLPs (slip,Fz)->force-ratio and flatten into LUT tensors.
    if isinstance(nn_weights, dict):
        payload = nn_weights
    else:
        payload = _load_nn_payload(_NN_PT if nn_weights is None else nn_weights)
    luts.update(_nn_luts(payload, device, dtype))
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


def _interp2d_bilinear(x, y, xp, yp, table):
    """Branchless bilinear interpolation of ``table[i_x, j_y]`` at (x, y). Clamped at edges.

    x, y are [...] tensors; xp:[Kx], yp:[Ky] are the (sorted) grids; table:[Kx, Ky]. Used for
    the EXACT-TMeasy force-ratio surfaces Fx/Fz(kappa, Fz) and Fy/Fz(alpha, Fz)."""
    Kx = xp.shape[0]
    Ky = yp.shape[0]
    xc = x.clamp(xp[0], xp[-1])
    yc = y.clamp(yp[0], yp[-1])
    ix = torch.searchsorted(xp, xc.contiguous(), right=True).clamp(1, Kx - 1)
    iy = torch.searchsorted(yp, yc.contiguous(), right=True).clamp(1, Ky - 1)
    x0 = xp[ix - 1]; x1 = xp[ix]
    y0 = yp[iy - 1]; y1 = yp[iy]
    wx = ((xc - x0) / (x1 - x0).clamp_min(1e-12)).unsqueeze(-1) if x.dim() == 0 else (xc - x0) / (x1 - x0).clamp_min(1e-12)
    wy = (yc - y0) / (y1 - y0).clamp_min(1e-12)
    # gather the four corners (flatten the [Kx,Ky] table for index_select)
    flat = table.reshape(-1)
    def corner(a, b):
        return flat[a * Ky + b]
    f00 = corner(ix - 1, iy - 1)
    f10 = corner(ix, iy - 1)
    f01 = corner(ix - 1, iy)
    f11 = corner(ix, iy)
    f0 = f00 + wx * (f10 - f00)
    f1 = f01 + wx * (f11 - f01)
    return f0 + wy * (f1 - f0)


# --------------------------------------------------------------------- NN tyre forward (branchless)
def _mlp_forward(slip: torch.Tensor, fz: torch.Tensor, P: PhysParamBatch, branch: str) -> torch.Tensor:
    """Batched branchless forward of a fitted tyre MLP: (slip, Fz)[N] -> force ratio [N].

    ``branch`` is 'x' (Fx/Fz from kappa) or 'y' (Fy/Fz from alpha). Mirrors the training-time
    normalisation: slip z-score, Fz affine to [-1,1] over the fit grid, output z-score inverse.
    The whole net is a plain matmul + tanh chain over the LUT weight tensors — no nn.Module,
    fully batched over N envs, no per-env python branch."""
    L = P.luts
    st = L["nn_stx"] if branch == "x" else L["nn_sty"]
    n_layers = L["nn_n_layers_x"] if branch == "x" else L["nn_n_layers_y"]
    # normalise inputs exactly as in fit_tmeasy_tyre_nn.py._encode
    slip_n = (slip - st["slip_mean"]) / st["slip_std"]
    fz_n = 2.0 * (fz - st["fz_lo"]) / (st["fz_hi"] - st["fz_lo"]) - 1.0
    h = torch.stack([slip_n, fz_n], dim=-1)              # [N, 2]
    for i in range(n_layers):
        w = L[f"nn_{branch}_w{i}"]                       # [out, in]
        b = L[f"nn_{branch}_b{i}"]                       # [out]
        h = h @ w.t() + b                                # [N, out]
        if i < n_layers - 1:                             # tanh on every layer but the last
            h = torch.tanh(h)
    ratio_n = h.squeeze(-1)                              # [N]
    return ratio_n * st["ratio_std"] + st["ratio_mean"]


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
    """Per-wheel combined-slip Fx,Fy from the fitted NN of Chrono's EXACT TMeasy curves.

    sx: longitudinal slip, alpha: slip angle [rad], fz: normal load [N]. ``fz_nom`` and
    ``grip_scale`` are kept for signature parity with gpu_physics (grip_scale=1.0 in the
    faithful rewrite; it only multiplies the lateral force and is a no-op at 1.0).

    The tyre evaluates the two fitted MLPs mlp_x(kappa,Fz)->Fx/Fz and mlp_y(alpha,Fz)->Fy/Fz
    at the runtime (combined slip, actual Fz) — they reproduce the same sampled force-RATIO
    surfaces (degressive load dependence included) as the TABLE variant, only via a smooth net
    instead of a bilinear LUT. Combined slip uses the SAME slip-vector projection as the TABLE
    variant / Chrono ``tmxy_combined``/``CombinedCoulombForces`` ellipse: normalise each slip by
    its per-load peak-slip, evaluate both pure curves on the combined magnitude, then split the
    force by slip direction. Terrain mu enters as ``mu_scale = mu/mu0`` on the caps.
    Returns (Fx, Fy)."""
    fz_grid = P.luts["tm_fz_grid"]
    kappa_grid = P.luts["tm_kappa_grid"]
    alpha_grid = P.luts["tm_alpha_grid"]
    fz_c = fz.clamp(fz_grid[0], fz_grid[-1])

    # per-load peak-slip locations (combined-slip normalisers), interpolated in Fz.
    kappa_pk = _interp1d(fz_c, fz_grid, P.luts["tm_kappa_peak"]).abs().clamp_min(0.02)
    alpha_pk = _interp1d(fz_c, fz_grid, P.luts["tm_alpha_peak"]).abs().clamp_min(0.02)

    # theoretical lateral slip sy = tan(alpha); normalise both slips by their peak-slip.
    sy = torch.tan(alpha.clamp(-1.45, 1.45))
    nx = sx / kappa_pk
    ny = sy / torch.tan(alpha_pk)
    s_comb = torch.sqrt(nx * nx + ny * ny + 1e-12)
    cx = nx / s_comb
    cy = ny / s_comb

    # combined slips projected back to physical scale for the NN evaluation.
    kappa_eval = s_comb * kappa_pk
    alpha_eval = torch.atan(s_comb * torch.tan(alpha_pk)).clamp(alpha_grid[0], alpha_grid[-1])

    # NN forward of the EXACT force ratios (Fx/Fz, Fy/Fz) at (combined slip, Fz). The slip is
    # clamped to the fitted slip range (same edge-clamp as the TABLE variant) so the net is never
    # asked to extrapolate beyond the sampled curve — a faithful drop-in for the bilinear lookup.
    fx_ratio = _mlp_forward(kappa_eval.clamp(kappa_grid[0], kappa_grid[-1]), fz_c, P, "x")
    fy_ratio = _mlp_forward(alpha_eval, fz_c, P, "y")
    # the curve is signed in slip; we evaluated at |combined| via the positive-slip branch,
    # so take magnitudes and re-apply the slip direction. mu_scale scales the friction caps.
    fx0 = fx_ratio.abs() * fz * mu_scale
    fy0 = fy_ratio.abs() * fz * mu_scale * grip_scale

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
