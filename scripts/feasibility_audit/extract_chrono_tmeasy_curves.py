"""Extract Chrono's EXACT TMeasy tyre force curves by direct single-wheel sampling.

ROUTE (a): instantiate the real Chrono Sedan (the same construction the HF backend uses
in ``src/autodrift/chrono_vehicle_backend.py`` -- ``veh.Sedan()`` +
``SetTireType(TireModelType_TMEASY)``, mu_0=0.8) and SAMPLE the TMeasy tyre force output
at controlled operating points. We grab one rear tyre, fix its spindle body, and impose
a kinematic state directly on the spindle:

    - penetration depth  -> controls the vertical (normal) load Fz (TMeasy Fz = Cz*depth)
    - linear velocity     -> vx forward + vy = vx*tan(alpha) sets the SLIP ANGLE alpha
    - spin omega          -> omega = vx*(1+kappa)/R sets the LONGITUDINAL SLIP kappa

then ``tire.Synchronize`` + ``tire.Advance`` for enough sub-steps that the internal TMeasy
slip / bristle state settles to steady, and read ``ReportTireForce`` (the EXACT Rill curve
Chrono computes). The reported ``GetLongitudinalSlip`` / ``GetSlipAngle`` give the TRUE
operating-point coordinates (which differ slightly from the imposed targets because of
rolling resistance / contact-patch transport), so we tabulate against the REPORTED slips.

We extract THREE tables, all as functions of normal load Fz (the degressive load
dependence is first-order in TMeasy -- peak Fx/Fz, Fy/Fz shrink strongly with Fz):

    Fx_table[k_grid, fz_grid]            pure longitudinal (alpha=0)
    Fy_table[a_grid, fz_grid]            pure lateral (kappa=0)
    Fcomb_x/Fcomb_y[k_grid, a_grid, fz]  combined-slip 2D surface (friction ellipse)

Saved to runs/feasibility_audit/phase4_f2/chrono_tmeasy_curves.npz.

Run inside the pinned chrono env:
    /home/quyaonan/miniforge3/envs/chrono/bin/python \
        scripts/feasibility_audit/extract_chrono_tmeasy_curves.py
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pychrono as chrono
import pychrono.vehicle as veh

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs/feasibility_audit/phase4_f2/chrono_tmeasy_curves.npz"

MU0 = 0.8           # Sedan_TMeasyTire reference friction (mu enters as muscale = mu/mu0)
SETTLE_ITERS = 250  # sub-steps for the internal TMeasy state to reach steady
DT = 1e-3
VX_SAMPLE = 8.0     # sampling speed (TMeasy is velocity-independent above standstill)


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
    tire = vehicle.GetTire(1, veh.LEFT)          # rear-left
    wheel = vehicle.GetWheel(1, veh.LEFT)
    spindle = wheel.GetSpindle()
    R = tire.GetRadius()
    spindle.SetFixed(True)                        # we drive it kinematically
    return car, terrain, tire, spindle, R


def query(tire, terrain, spindle, R, vx, alpha, kappa, depth, niter=SETTLE_ITERS):
    """Impose (alpha, kappa, depth) on the spindle, settle, read EXACT TMeasy force.

    Returns (Fz, Fx_local, Fy_local, reported_longslip, reported_slipangle)."""
    spindle.SetPos(chrono.ChVector3d(-1.388, 0.8, R - depth))
    spindle.SetRot(chrono.QUNIT)                  # spin axis = body Y, forward = body X
    vy = vx * math.tan(alpha)
    spindle.SetLinVel(chrono.ChVector3d(vx, vy, 0.0))
    spindle.SetAngVelLocal(chrono.ChVector3d(0.0, vx * (1.0 + kappa) / R, 0.0))
    inputs = veh.DriverInputs()
    inputs.m_steering = 0.0
    inputs.m_throttle = 0.0
    inputs.m_braking = 0.0
    t = 0.0
    for _ in range(niter):
        tire.Synchronize(t, terrain)
        tire.Advance(DT)
        t += DT
    fr = tire.ReportTireForce(terrain)
    floc = spindle.GetRot().RotateBack(fr.force)  # project global -> wheel frame
    return float(fr.force.z), float(floc.x), float(floc.y), \
        float(tire.GetLongitudinalSlip()), float(tire.GetSlipAngle())


def calibrate_depth_for_fz(tire, terrain, spindle, R, fz_targets):
    """Find the penetration depth that yields each target Fz (bisection on the linear Cz)."""
    # measure Cz from two points (TMeasy Fz = Cz*depth, linear m_d1; tiny rolling-res cross term)
    fz_lo, *_ = query(tire, terrain, spindle, R, VX_SAMPLE, 0.0, 0.0, 0.004)
    fz_hi, *_ = query(tire, terrain, spindle, R, VX_SAMPLE, 0.0, 0.0, 0.020)
    cz = (fz_hi - fz_lo) / (0.020 - 0.004)
    depths = []
    for fz in fz_targets:
        d = fz / cz                                # initial guess
        for _ in range(6):                         # Newton/secant refine on measured Fz
            fz_meas, *_ = query(tire, terrain, spindle, R, VX_SAMPLE, 0.0, 0.0, d, niter=120)
            d = d * fz / max(fz_meas, 1.0)
            d = min(max(d, 0.001), 0.030)
        depths.append(d)
    return np.array(depths), cz


def main():
    car, terrain, tire, spindle, R = build_tire()
    print("R_unloaded=%.4f  mu0=%.2f" % (R, MU0))

    # ---- Fz grid: spans the per-wheel loads seen in drift (static ~4000 N) +/- transfer ----
    fz_grid = np.array([2000.0, 3000.0, 4000.0, 5000.0, 6000.0, 7000.0, 8500.0], dtype=np.float64)
    depths, cz = calibrate_depth_for_fz(tire, terrain, spindle, R, fz_grid)
    print("Cz~%.0f N/m   depths(mm)=%s" % (cz, np.round(depths * 1e3, 3)))

    # ---- slip grids ----
    kappa_grid = np.array([-0.30, -0.20, -0.15, -0.10, -0.07, -0.05, -0.03, -0.015,
                           0.0, 0.015, 0.03, 0.05, 0.07, 0.10, 0.15, 0.20, 0.30],
                          dtype=np.float64)
    alpha_grid = np.array([-0.40, -0.30, -0.20, -0.15, -0.10, -0.07, -0.05, -0.03, -0.015,
                           0.0, 0.015, 0.03, 0.05, 0.07, 0.10, 0.15, 0.20, 0.30, 0.40],
                          dtype=np.float64)

    nF = len(fz_grid)
    nK = len(kappa_grid)
    nA = len(alpha_grid)

    # ---- pure longitudinal table Fx(kappa, Fz) and the REPORTED kappa per cell ----
    Fx = np.zeros((nK, nF))
    Fz_at_K = np.zeros((nK, nF))
    kappa_rep = np.zeros((nK, nF))
    for j, d in enumerate(depths):
        for i, k in enumerate(kappa_grid):
            fz, fx, fy, ls, sa = query(tire, terrain, spindle, R, VX_SAMPLE, 0.0, k, d)
            Fx[i, j] = fx
            Fz_at_K[i, j] = fz
            kappa_rep[i, j] = ls
        print("  Fx col Fz~%.0f done (peak Fx/Fz=%.3f)" % (fz_grid[j], np.max(np.abs(Fx[:, j])) / fz_grid[j]))

    # ---- pure lateral table Fy(alpha, Fz) and the REPORTED alpha per cell ----
    Fy = np.zeros((nA, nF))
    Fz_at_A = np.zeros((nA, nF))
    alpha_rep = np.zeros((nA, nF))
    for j, d in enumerate(depths):
        for i, a in enumerate(alpha_grid):
            fz, fx, fy, ls, sa = query(tire, terrain, spindle, R, VX_SAMPLE, a, 0.0, d)
            Fy[i, j] = fy
            Fz_at_A[i, j] = fz
            alpha_rep[i, j] = sa
        print("  Fy col Fz~%.0f done (peak Fy/Fz=%.3f)" % (fz_grid[j], np.max(np.abs(Fy[:, j])) / fz_grid[j]))

    # ---- combined-slip 2D surface at the NOMINAL load (friction-ellipse coupling) ----
    # sampled at the mid Fz (~4000 N, j index of closest); records Fx,Fy(kappa,alpha)
    jc = int(np.argmin(np.abs(fz_grid - 4000.0)))
    Fcx = np.zeros((nK, nA))
    Fcy = np.zeros((nK, nA))
    for i, k in enumerate(kappa_grid):
        for m, a in enumerate(alpha_grid):
            fz, fx, fy, ls, sa = query(tire, terrain, spindle, R, VX_SAMPLE, a, k, depths[jc])
            Fcx[i, m] = fx
            Fcy[i, m] = fy
    print("  combined-slip surface @ Fz~%.0f done" % fz_grid[jc])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        OUT,
        mu0=MU0,
        R_unloaded=R,
        Cz=cz,
        fz_grid=fz_grid,
        kappa_grid=kappa_grid,
        alpha_grid=alpha_grid,
        Fx=Fx,             # [nK, nF] pure-longitudinal force [N]
        Fy=Fy,             # [nA, nF] pure-lateral force [N]
        Fz_at_K=Fz_at_K,
        Fz_at_A=Fz_at_A,
        kappa_rep=kappa_rep,
        alpha_rep=alpha_rep,
        Fcomb_kappa_grid=kappa_grid,
        Fcomb_alpha_grid=alpha_grid,
        Fcomb_fz=fz_grid[jc],
        Fcomb_x=Fcx,       # [nK, nA] combined Fx at nominal Fz
        Fcomb_y=Fcy,       # [nK, nA] combined Fy at nominal Fz
        vx_sample=VX_SAMPLE,
    )
    print("saved %s" % OUT)

    # ---- sanity prints (compare vs spec 1.2-1.4 peak) ----
    jn = int(np.argmin(np.abs(fz_grid - 4000.0)))
    def at(grid, table, x, j):
        return float(np.interp(x, grid, table[:, j]))
    print("\n=== SANITY (nominal Fz~%.0f N) ===" % fz_grid[jn])
    print("Fx/Fz @ kappa=0.10 : %.3f" % (at(kappa_grid, Fx, 0.10, jn) / fz_grid[jn]))
    print("Fx/Fz @ kappa=0.20 : %.3f  (peak region)" % (at(kappa_grid, Fx, 0.20, jn) / fz_grid[jn]))
    print("Fy/Fz @ alpha=0.10 : %.3f" % (at(alpha_grid, Fy, 0.10, jn) / fz_grid[jn]))
    print("Fy/Fz @ alpha=0.15 : %.3f  (peak region)" % (at(alpha_grid, Fy, 0.15, jn) / fz_grid[jn]))
    print("peak |Fx|/Fz over Fz grid:", np.round(np.max(np.abs(Fx), 0) / fz_grid, 3))
    print("peak |Fy|/Fz over Fz grid:", np.round(np.max(np.abs(Fy), 0) / fz_grid, 3))


if __name__ == "__main__":
    main()
