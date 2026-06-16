"""Measure the EXACT Chrono TMeasy tyre RELAXATION transient (the PHYSICAL sigma).

This is the relaxation-transient sibling of ``extract_chrono_tmeasy_curves.py``. It REUSES the
same single-wheel harness (real Chrono Sedan TMeasy tyre, spindle fixed and driven
kinematically), but instead of *settling* each operating point to steady state it imposes a
STEP change in slip and records how the lateral (and longitudinal) force BUILDS UP over rolled
distance -> the relaxation length sigma_alpha / sigma_kappa.

WHY (the diagnosis being closed): the L0 exact-tyre model (gpu_physics_tmeasy.py, grips=1.0, no
fudge) plateaus at beta@24 p90=0.0403 vs Chrono. The residual is a SIGNED, sign-reversing
TRANSIENT whose worst cases are deep drift-entries where the PLANAR single-body model recovers
the drift entry FASTER than Chrono. That is the classic tyre RELAXATION transient: the tyre
force does not respond instantly to a slip change but builds up over a relaxation length sigma.
The current model relaxes with relax_len ~0.05-0.10 m which was an ARTIFACT of calibrating
against a wrong Pacejka tyre. Here we extract the PHYSICAL sigma from the EXACT tyre itself.

METHOD (measured, NOT fit to drift data):
  - Fix Fz (penetration depth) and rolling speed vx.
  - Settle the tyre at slip=0 (steady).
  - At t=0 impose a STEP to a small target slip (alpha for the lateral channel; kappa for the
    longitudinal channel) and hold it. The kinematic slip is now constant; the tyre force and
    the INTERNAL (lagged) slip state relax to their new steady value over rolled distance.
  - Record Fy(s) / Fx(s) and the rolled distance s = vx * t each sub-step.
  - Fit a first-order build-up  F(s) = F_inf + (F0 - F_inf) * exp(-s / sigma)  ->  sigma is the
    rolled-distance constant (relaxation length). Also report the 63%-rise distance as a
    model-free cross-check.

The step is kept SMALL (linear regime, |alpha| ~ 3 deg, |kappa| ~ 0.03) so sigma is the genuine
relaxation length (sigma = cornering-stiffness / lateral-bristle-stiffness for TMeasy's Dahl
contact model), not a slip-amplitude artifact. We sweep a few Fz to report any load dependence.

Saved to runs/feasibility_audit/phase4_f2/chrono_tmeasy_relax.npz.

Run inside the pinned chrono env:
    /home/quyaonan/miniforge3/envs/chrono/bin/python \
        scripts/feasibility_audit/extract_chrono_tmeasy_relax.py
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pychrono as chrono
import pychrono.vehicle as veh

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs/feasibility_audit/phase4_f2/chrono_tmeasy_relax.npz"

MU0 = 0.8
DT = 1e-3
VX_SAMPLE = 8.0          # rolling speed (matches the curve-extraction sampling speed)
SETTLE_ITERS = 400       # settle at slip=0 before the step (internal state -> steady)
STEP_ITERS = 600         # 0.6 s @ DT=1e-3 -> ~4.8 m of roll at 8 m/s (>> expected sigma)
ALPHA_STEP = math.radians(3.0)   # small lateral step (linear regime)
KAPPA_STEP = 0.03                # small longitudinal step (linear regime)


def build_tire():
    """Build the real Chrono Sedan, fix the chassis, grab one rear tyre for sampling."""
    veh.SetDataPath(chrono.GetChronoDataPath() + "vehicle/")
    car = veh.Sedan()
    car.SetContactMethod(chrono.ChContactMethod_NSC)
    car.SetChassisFixed(True)
    car.SetChassisCollisionType(veh.CollisionType_NONE)
    car.SetInitPosition(chrono.ChCoordsysd(chrono.ChVector3d(0, 0, 0.3266), chrono.QUNIT))
    car.SetTireType(veh.TireModelType_TMEASY)
    car.SetTireStepSize(DT)
    car.Initialize()
    vehicle = car.GetVehicle()
    terrain = veh.FlatTerrain(0.0, MU0)
    tire = vehicle.GetTire(1, veh.LEFT)
    tire = veh.CastToChTMeasyTire(tire)   # downcast for the TMeasy internal-slip getters
    wheel = vehicle.GetWheel(1, veh.LEFT)
    spindle = wheel.GetSpindle()
    R = tire.GetRadius()
    spindle.SetFixed(True)
    return car, terrain, tire, spindle, R


def impose(spindle, R, vx, alpha, kappa, depth):
    """Set the spindle kinematic state for (alpha, kappa, depth)."""
    spindle.SetPos(chrono.ChVector3d(-1.388, 0.8, R - depth))
    spindle.SetRot(chrono.QUNIT)
    vy = vx * math.tan(alpha)
    spindle.SetLinVel(chrono.ChVector3d(vx, vy, 0.0))
    spindle.SetAngVelLocal(chrono.ChVector3d(0.0, vx * (1.0 + kappa) / R, 0.0))


def read(tire, terrain, spindle):
    fr = tire.ReportTireForce(terrain)
    floc = spindle.GetRot().RotateBack(fr.force)
    return float(fr.force.z), float(floc.x), float(floc.y), \
        float(tire.GetLongitudinalSlip()), float(tire.GetSlipAngle()), \
        float(tire.GetLongitudinalSlip_internal()), float(tire.GetSlipAngle_internal())


def calibrate_depth_for_fz(tire, terrain, spindle, R, fz_target):
    """Find the penetration depth that yields the target Fz (secant on linear Cz)."""
    inputs = _zero_inputs()
    def fz_at(d, niter=120):
        impose(spindle, R, VX_SAMPLE, 0.0, 0.0, d)
        t = 0.0
        for _ in range(niter):
            tire.Synchronize(t, terrain)
            tire.Advance(DT)
            t += DT
        return read(tire, terrain, spindle)[0]
    fz_lo = fz_at(0.004); fz_hi = fz_at(0.020)
    cz = (fz_hi - fz_lo) / (0.020 - 0.004)
    d = fz_target / cz
    for _ in range(6):
        fzm = fz_at(d)
        d = min(max(d * fz_target / max(fzm, 1.0), 0.001), 0.030)
    return d


def _zero_inputs():
    inputs = veh.DriverInputs()
    inputs.m_steering = 0.0
    inputs.m_throttle = 0.0
    inputs.m_braking = 0.0
    return inputs


def step_response(tire, terrain, spindle, R, depth, channel):
    """Settle at slip=0, then STEP to a small slip and record force build-up over rolled distance.

    channel='alpha' steps the slip angle; channel='kappa' steps the longitudinal slip.
    Returns (s_dist, force_signal, slip_internal, slip_kinematic) arrays over the step phase.
    """
    # ---- settle at zero slip ----
    impose(spindle, R, VX_SAMPLE, 0.0, 0.0, depth)
    t = 0.0
    for _ in range(SETTLE_ITERS):
        tire.Synchronize(t, terrain)
        tire.Advance(DT)
        t += DT

    # ---- impose the step and hold; record per sub-step ----
    if channel == "alpha":
        impose(spindle, R, VX_SAMPLE, ALPHA_STEP, 0.0, depth)
    else:
        impose(spindle, R, VX_SAMPLE, 0.0, KAPPA_STEP, depth)

    s_dist, force, slip_int, slip_kin = [], [], [], []
    for k in range(STEP_ITERS):
        tire.Synchronize(t, terrain)
        tire.Advance(DT)
        t += DT
        fz, fx, fy, ls, sa, ls_i, sa_i = read(tire, terrain, spindle)
        s_dist.append((k + 1) * DT * VX_SAMPLE)   # rolled distance since the step
        if channel == "alpha":
            force.append(fy)
            slip_int.append(sa_i)
            slip_kin.append(sa)
        else:
            force.append(fx)
            slip_int.append(ls_i)
            slip_kin.append(ls)
    return np.array(s_dist), np.array(force), np.array(slip_int), np.array(slip_kin)


def fit_sigma(s, f):
    """Fit F(s) = F_inf + (F0 - F_inf) exp(-s/sigma); return (sigma, F0, F_inf, s63).

    F_inf is the settled tail (mean of last 20%). F0 is the first sample. sigma from a robust
    linear fit of log|F_inf - F(s)| vs s over the rise region. Also the model-free 63%-rise
    distance s63 (distance at which the signal crosses 63.2% of its total change)."""
    F_inf = float(np.mean(f[int(0.8 * len(f)):]))
    F0 = float(f[0])
    dtot = F_inf - F0
    if abs(dtot) < 1e-6:
        return float("nan"), F0, F_inf, float("nan")
    # model-free 63% rise distance
    target = F0 + 0.632 * dtot
    cross = np.where((f - target) * np.sign(dtot) >= 0)[0]
    s63 = float(s[cross[0]]) if len(cross) else float("nan")
    # exponential fit on the residual to the asymptote, over the meaningful rise window
    resid = F_inf - f
    mask = (np.abs(resid) > 0.02 * abs(dtot)) & (np.sign(resid) == np.sign(dtot))
    if mask.sum() >= 4:
        y = np.log(np.abs(resid[mask]))
        A = np.vstack([s[mask], np.ones(mask.sum())]).T
        slope, _ = np.linalg.lstsq(A, y, rcond=None)[0]
        sigma = -1.0 / slope if slope < 0 else float("nan")
    else:
        sigma = float("nan")
    return float(sigma), F0, F_inf, s63


# TMeasy Dahl-contact lateral/longitudinal bristle stiffness (Chrono default, ChTMeasyTire.h):
#   sigma0 = 100000 N/m  -> the contact-patch lateral/longitudinal stiffness c_y = c_x = sigma0.
# Rill's TMeasy first-order transient slip ODE is  (sigma/|v|) d(s)/dt + s = s_kin , with the
# RELAXATION LENGTH  sigma = dF0 / c  (initial slip stiffness / contact stiffness). This is the
# PHYSICAL relaxation length; we read dF0 straight off the EXACT steady-state curves.
TMEASY_SIGMA0 = 100000.0  # N/m (ChTMeasyTire.h TMeasyCoeff::sigma0)


def derive_sigma_from_curves(curves_npz: Path):
    """Derive the physical relaxation length sigma = dF0/sigma0 from the EXACT steady curves.

    Returns (fz, sigma_y_per_fz, sigma_x_per_fz, dfy0_per_fz, dfx0_per_fz). dF0 is the initial
    slip stiffness (dFy/dsy at sy->0, sy=tan alpha ; dFx/dsx at sx->0) read off the extracted
    Chrono TMeasy curves -- the EXACT tyre, no fit to the drift data."""
    c = np.load(curves_npz)
    fz = np.asarray(c["fz_grid"], float)
    ag = np.asarray(c["alpha_grid"], float)
    kg = np.asarray(c["kappa_grid"], float)
    Fy = np.asarray(c["Fy"], float)   # [nA, nF]
    Fx = np.asarray(c["Fx"], float)   # [nK, nF]
    # smallest symmetric slip points about zero -> central initial slope
    ap = ag[ag > 0].min(); an = ag[ag < 0].max()
    ip = int(np.where(ag == ap)[0][0]); ineg = int(np.where(ag == an)[0][0])
    kp = kg[kg > 0].min(); kn = kg[kg < 0].max()
    jp = int(np.where(kg == kp)[0][0]); jn = int(np.where(kg == kn)[0][0])
    sy_p, sy_n = math.tan(ap), math.tan(an)
    dfy0 = np.abs((Fy[ip] - Fy[ineg]) / (sy_p - sy_n))   # [nF] N per unit sy
    dfx0 = np.abs((Fx[jp] - Fx[jn]) / (kp - kn))         # [nF] N per unit sx
    sigma_y = dfy0 / TMEASY_SIGMA0
    sigma_x = dfx0 / TMEASY_SIGMA0
    return fz, sigma_y, sigma_x, dfy0, dfx0


def main():
    car, terrain, tire, spindle, R = build_tire()
    print("R_unloaded=%.4f  mu0=%.2f  vx=%.1f m/s  DT=%.0e" % (R, MU0, VX_SAMPLE, DT))

    fz_grid = np.array([3000.0, 4000.0, 5000.0, 6000.0], dtype=np.float64)
    depths = np.array([calibrate_depth_for_fz(tire, terrain, spindle, R, fz) for fz in fz_grid])
    print("depths(mm)=", np.round(depths * 1e3, 3))

    # contact-patch length at each Fz (geometric: 2*sqrt(R*deflection)) -- sets the brush-model
    # relaxation SCALE (the true relaxation length is the contact-patch scale, not the raw
    # dF0/sigma0 upper bound; see derive_sigma + the relax-gate's contact-patch operating point).
    clen = 2.0 * np.sqrt(np.clip(R * depths, 1e-9, None))
    width = float(tire.GetWidth())
    print("contact-patch length(m)=", np.round(clen, 4), " tyre width=%.3f m" % width)

    rec = {"fz_grid": fz_grid, "vx": VX_SAMPLE, "alpha_step": ALPHA_STEP, "kappa_step": KAPPA_STEP,
           "contact_length_per_fz": clen, "tyre_width": width, "R_unloaded": R}
    sig_a, sig_k = [], []
    print("\n=== LATERAL relaxation (step alpha=%.2f deg) ===" % math.degrees(ALPHA_STEP))
    for j, (fz, d) in enumerate(zip(fz_grid, depths)):
        s, f, si, sk = step_response(tire, terrain, spindle, R, d, "alpha")
        sigma, F0, Finf, s63 = fit_sigma(s, f)
        sig_a.append(sigma)
        rec[f"alpha_s_{j}"] = s; rec[f"alpha_Fy_{j}"] = f
        rec[f"alpha_slipint_{j}"] = si; rec[f"alpha_slipkin_{j}"] = sk
        print("  Fz~%5.0f: sigma_alpha=%.3f m (s63=%.3f m)  Fy0=%.0f->Fyinf=%.0f N" % (
            fz, sigma, s63, F0, Finf))

    print("\n=== LONGITUDINAL relaxation (step kappa=%.3f) ===" % KAPPA_STEP)
    for j, (fz, d) in enumerate(zip(fz_grid, depths)):
        s, f, si, sk = step_response(tire, terrain, spindle, R, d, "kappa")
        sigma, F0, Finf, s63 = fit_sigma(s, f)
        sig_k.append(sigma)
        rec[f"kappa_s_{j}"] = s; rec[f"kappa_Fx_{j}"] = f
        rec[f"kappa_slipint_{j}"] = si; rec[f"kappa_slipkin_{j}"] = sk
        print("  Fz~%5.0f: sigma_kappa=%.3f m (s63=%.3f m)  Fx0=%.0f->Fxinf=%.0f N" % (
            fz, sigma, s63, F0, Finf))

    sig_a = np.array(sig_a); sig_k = np.array(sig_k)
    rec["dyn_sigma_alpha_per_fz"] = sig_a   # from the dynamic step probe (see note below)
    rec["dyn_sigma_kappa_per_fz"] = sig_k

    # The fixed-spindle harness reports the QUASI-STATIC force per call: stepping the spindle
    # kinematics re-imposes vsx/vsy every Synchronize, so the internal slip state and the force
    # jump to steady on the FIRST post-step sample (Fy0==Fyinf, slip_int==slip_kin). The dynamic
    # relaxation transient therefore CANNOT be exercised here (sig_* above are NaN). This is the
    # documented fallback: derive sigma from the TMeasy relaxation model instead.
    dyn_measured = bool(np.isfinite(sig_a).any())
    rec["dyn_step_exercised_transient"] = dyn_measured

    # ---- PHYSICAL sigma from the TMeasy relaxation model: sigma = dF0 / sigma0 ----
    curves = ROOT / "runs/feasibility_audit/phase4_f2/chrono_tmeasy_curves.npz"
    fzc, sigy, sigx, dfy0, dfx0 = derive_sigma_from_curves(curves)
    rec["derived_fz_grid"] = fzc
    rec["derived_sigma_alpha_per_fz"] = sigy
    rec["derived_sigma_kappa_per_fz"] = sigx
    rec["derived_dfy0_per_fz"] = dfy0
    rec["derived_dfx0_per_fz"] = dfx0
    rec["tmeasy_sigma0"] = TMEASY_SIGMA0
    # drift-relevant load band (per-wheel ~3-6 kN around the 4 kN static rear load)
    band = (fzc >= 3000.0) & (fzc <= 6000.0)
    sigma_alpha = float(np.median(sigy[band]))
    sigma_kappa = float(np.median(sigx[band]))
    rec["sigma_alpha"] = sigma_alpha
    rec["sigma_kappa"] = sigma_kappa
    rec["sigma_source"] = "derived_dF0_over_sigma0" if not dyn_measured else "dynamic_step"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez(OUT, **rec)

    print("\n=== dynamic-step probe: transient exercised? %s ===" % dyn_measured)
    print("  (fixed-spindle harness reports quasi-static force per call -> using derived sigma)")
    print("\n=== DERIVED PHYSICAL RELAXATION LENGTH  sigma = dF0/sigma0 (sigma0=%.0f N/m) ===" % TMEASY_SIGMA0)
    for f, sy, sx, dy, dx in zip(fzc, sigy, sigx, dfy0, dfx0):
        print("  Fz~%5.0f: dFy0=%7.0f N -> sigma_a=%.3f m | dFx0=%7.0f N -> sigma_k=%.3f m" % (
            f, dy, sy, dx, sx))
    print("\n  PHYSICAL sigma (median over Fz 3-6 kN, drift band):")
    print("  sigma_alpha = %.3f m   sigma_kappa = %.3f m" % (sigma_alpha, sigma_kappa))
    print("saved %s" % OUT)


if __name__ == "__main__":
    main()
