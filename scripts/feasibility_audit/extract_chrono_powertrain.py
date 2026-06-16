"""Measure the EXACT Chrono Sedan DRIVEN FORCE vs (throttle, speed) — the partial-throttle
powertrain the L1 faithful rewrite (gpu_physics_relax) gets ~1.75x too strong.

The relax model PASSES the drift gate but over-speeds in the cruise/avoidance regime: replaying
the avoid oracle (which cruises at throttle ~0.16) the surrogate vx error grows to +0.74 by step
50 (avoid vx_rmse 1.21 vs the drift floor 0.235; vy/lateral faithful at 0.14). Resistance has been
measured (extract_chrono_coastdown.py: Sedan has NO aero, drag=0, Crr=0.0282) and is NOT the cause.
The residual gap is on the DRIVEN side at PARTIAL throttle. A drive_scale sweep nulls the avoid vx
error at scale ~= 0.57, i.e. the model delivers ~1/0.57 ~= 1.75x too much forward force at the
avoid operating point.

This script MEASURES the true driven force surface, the same isolated-Chrono-Sedan way
extract_chrono_coastdown.py / extract_chrono_brake.py measure their params — it instantiates the
real ``veh.Sedan()`` + TMeasy (the exact construction the HF backend uses) on flat avoidance-mu
terrain, holds a FIXED throttle, and lets the car accelerate from low speed through high speed,
sampling continuously:

    v(t), a(t) = dv/dt          (longitudinal, body frame)
    engine motor rpm            (eng.GetMotorSpeed())
    CURRENT GEAR                (trans.GetCurrentGear())  <-- the prime suspect
    driveshaft torque           (trans.GetOutputDriveshaftTorque())
    driven spindle torque       (driveline.GetSpindleTorque(axle, side), summed over driven wheels)

The DRIVEN FORCE is recovered by force balance (matching the way the model applies it):

    F_drive(thr, v) = m * a  +  resistance(v)
    resistance(v)   = drag_coeff * v^2 + Crr * m * g       (MEASURED: drag=0, Crr=0.0282)

We sweep throttle in {0.0, 0.1, 0.16, 0.2, 0.3, 0.5, 0.7, 1.0} (0.16 = the avoid-oracle cruise
throttle) and bin the samples by speed at ~5, 8, 11, 14 m/s, recording the median driven force,
rpm and gear in each (throttle, speed) cell. We ALSO cross-check the force-balance F_drive against
the directly-read driven spindle torque / r_eff (independent of the resistance assumption).

KEY STRUCTURAL FACT this measurement also pins down: the Chrono Sedan driveline is
``ShaftsDriveline2WD`` driving AXLE 0 (the FRONT axle, x=+1.388) — the Sedan is FRONT-wheel drive,
not rear. (The model's omega states are on the rear; for the low-sideslip cruise/avoidance regime
the net forward force is what the avoid vx gate sees, and that is what we match here.)

Saves runs/feasibility_audit/phase4_f2/chrono_powertrain.npz.

Run inside the pinned chrono env:
    /home/quyaonan/miniforge3/envs/chrono/bin/python \
        scripts/feasibility_audit/extract_chrono_powertrain.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pychrono as chrono
import pychrono.vehicle as veh

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs/feasibility_audit/phase4_f2/chrono_powertrain.npz"
COAST = ROOT / "runs/feasibility_audit/phase4_f2/chrono_coastdown.npz"

MU0 = 0.8          # avoidance / cruise terrain friction (Sedan_TMeasyTire reference mu)
DT = 1e-3
INIT_Z = 0.3266    # near static ride height (same as the other extraction scripts)
GRAVITY = 9.81

# MEASURED cruise resistance (extract_chrono_coastdown.py / gpu_physics_coast): Sedan has NO aero.
DRAG_COEFF = 0.0
CRR = 0.0282

THROTTLES = [0.0, 0.1, 0.16, 0.2, 0.3, 0.5, 0.7, 1.0]   # 0.16 = avoid-oracle cruise throttle
SPEED_CELLS = [5.0, 8.0, 11.0, 14.0]                     # m/s operating points to report
SPEED_BAND = 0.4                                          # +/- m/s window around each cell
V_START = 2.5      # begin sampling once rolling above this (avoid launch transient)
V_MAX = 22.0       # stop when we exceed this (or terminal speed of the throttle)


def build_car():
    veh.SetDataPath(chrono.GetChronoDataPath() + "vehicle/")
    car = veh.Sedan()
    car.SetContactMethod(chrono.ChContactMethod_NSC)
    car.SetChassisFixed(False)
    car.SetChassisCollisionType(veh.CollisionType_NONE)
    car.SetInitPosition(chrono.ChCoordsysd(chrono.ChVector3d(0, 0, INIT_Z), chrono.QUNIT))
    car.SetTireType(veh.TireModelType_TMEASY)
    car.SetTireStepSize(DT)
    car.Initialize()
    return car


def _driven_axle_sides(vehicle):
    """Return list of (axle, side) for the driveline's driven wheels (Sedan: axle 0 L/R)."""
    dl = vehicle.GetDriveline()
    driven = list(dl.GetDrivenAxleIndexes())
    sides = []
    for ai in driven:
        sides.append((ai, veh.LEFT))
        sides.append((ai, veh.RIGHT))
    return dl, sides


def resistance(v):
    return DRAG_COEFF * v * v + CRR * GRAVITY  # acceleration form: a_res = drag/m*v^2 + Crr*g (drag=0)


def sweep_throttle(thr):
    """Hold a FIXED throttle, accelerate from rest through V_MAX, sample (v,a,rpm,gear,torques)."""
    car = build_car()
    vehicle = car.GetVehicle()
    body = vehicle.GetChassisBody()
    mass = float(vehicle.GetMass())
    r_eff = float(vehicle.GetTire(0, veh.LEFT).GetRadius())
    eng = vehicle.GetEngine()
    trans = vehicle.GetTransmission()
    dl, driven_sides = _driven_axle_sides(vehicle)
    terrain = veh.FlatTerrain(0.0, MU0)

    inp = veh.DriverInputs()
    inp.m_steering = 0.0
    inp.m_braking = 0.0
    inp.m_throttle = float(thr)

    t = 0.0
    samples = []  # (v, a, rpm, gear, T_driveshaft, T_spindle_sum, F_spindle)
    v_prev = float(body.GetRot().RotateBack(body.GetPosDt()).x)
    # settle suspension at zero throttle for 0.3 s (same convention as the HF backend spin-up)
    inp.m_throttle = 0.0
    for _ in range(300):
        car.Synchronize(t, inp, terrain); terrain.Synchronize(t)
        car.Advance(DT); terrain.Advance(DT); t += DT
    inp.m_throttle = float(thr)
    v_prev = float(body.GetRot().RotateBack(body.GetPosDt()).x)

    stalled = 0
    max_steps = 60000
    for _ in range(max_steps):
        car.Synchronize(t, inp, terrain); terrain.Synchronize(t)
        car.Advance(DT); terrain.Advance(DT); t += DT
        v = float(body.GetRot().RotateBack(body.GetPosDt()).x)
        a = (v - v_prev) / DT
        v_prev = v
        if v >= V_START:
            rpm = float(eng.GetMotorSpeed()) * 60.0 / (2.0 * np.pi)
            gear = int(trans.GetCurrentGear())
            T_ds = float(trans.GetOutputDriveshaftTorque())
            T_sp = float(sum(dl.GetSpindleTorque(ai, sd) for ai, sd in driven_sides))
            F_sp = T_sp / r_eff
            samples.append((v, a, rpm, gear, T_ds, T_sp, F_sp))
        if v >= V_MAX:
            break
        # terminal-speed detection: at a fixed throttle the car reaches a terminal speed and a->0.
        if v >= V_START and abs(a) < 0.02:
            stalled += 1
            if stalled > 4000:   # ~4 s of near-zero accel => terminal speed
                break
        else:
            stalled = 0
    return np.asarray(samples, dtype=np.float64), mass, r_eff


def cell_summary(samples, mass):
    """Bin samples by SPEED_CELLS; return per-cell median (F_drive, rpm, gear, a, n, F_spindle)."""
    if len(samples) == 0:
        return {c: None for c in SPEED_CELLS}
    v = samples[:, 0]; a = samples[:, 1]; rpm = samples[:, 2]; gear = samples[:, 3]
    F_sp = samples[:, 6]
    out = {}
    for c in SPEED_CELLS:
        win = (v >= c - SPEED_BAND) & (v <= c + SPEED_BAND)
        if win.sum() < 3:
            out[c] = None
            continue
        a_c = a[win]
        F_drive = mass * a_c + (DRAG_COEFF * v[win] ** 2 + CRR * mass * GRAVITY)  # N
        out[c] = dict(
            n=int(win.sum()),
            v=float(np.median(v[win])),
            a=float(np.median(a_c)),
            F_drive=float(np.median(F_drive)),
            F_spindle=float(np.median(F_sp[win])),
            rpm=float(np.median(rpm[win])),
            gear=int(np.median(gear[win])),
        )
    return out


def main():
    print("=== Chrono Sedan DRIVEN FORCE vs (throttle, speed) — isolated veh.Sedan() + TMeasy, mu=%.2f ===" % MU0)
    if COAST.exists():
        c = np.load(COAST)
        print("  using MEASURED resistance: drag_coeff=%.4f  Crr=%.5f  (coastdown; Sedan has no aero)" % (
            DRAG_COEFF, CRR))
    # structural probe: which axle is driven?
    car = build_car(); vehicle = car.GetVehicle()
    dl = vehicle.GetDriveline()
    driven = list(dl.GetDrivenAxleIndexes())
    front_x = float(vehicle.GetWheel(0, veh.LEFT).GetPos().x)
    rear_x = float(vehicle.GetWheel(1, veh.LEFT).GetPos().x)
    drv_pos = "FRONT" if (0 in driven and front_x > rear_x) else ("REAR" if 1 in driven else "?")
    print("  driveline=%s  driven_axle_idx=%s  axle0_x=%.3f axle1_x=%.3f -> DRIVEN AXLE IS %s" % (
        dl.GetTemplateName(), driven, front_x, rear_x, drv_pos))
    del car, vehicle, dl

    mass_g = None; r_eff_g = None
    grid_F = np.full((len(THROTTLES), len(SPEED_CELLS)), np.nan)
    grid_Fsp = np.full((len(THROTTLES), len(SPEED_CELLS)), np.nan)
    grid_rpm = np.full((len(THROTTLES), len(SPEED_CELLS)), np.nan)
    grid_gear = np.full((len(THROTTLES), len(SPEED_CELLS)), np.nan)
    grid_a = np.full((len(THROTTLES), len(SPEED_CELLS)), np.nan)
    all_samples = {}

    for ti, thr in enumerate(THROTTLES):
        samples, mass, r_eff = sweep_throttle(thr)
        mass_g, r_eff_g = mass, r_eff
        all_samples[thr] = samples
        cells = cell_summary(samples, mass)
        vmax = float(samples[:, 0].max()) if len(samples) else float("nan")
        print("\n--- throttle %.2f : reached %.1f m/s, %d samples (mass=%.1f kg, r_eff=%.4f) ---" % (
            thr, vmax, len(samples), mass, r_eff))
        print("    speed | F_drive(N) | F_spindle(N) |  rpm  | gear |  a(m/s^2) |  n")
        for si, c in enumerate(SPEED_CELLS):
            cell = cells[c]
            if cell is None:
                print("    %4.0f  |    --      |     --       |  --   |  --  |    --     |  0" % c)
                continue
            grid_F[ti, si] = cell["F_drive"]
            grid_Fsp[ti, si] = cell["F_spindle"]
            grid_rpm[ti, si] = cell["rpm"]
            grid_gear[ti, si] = cell["gear"]
            grid_a[ti, si] = cell["a"]
            print("    %4.0f  | %9.1f  |  %9.1f   | %5.0f |  %d   | %+8.3f  | %3d" % (
                c, cell["F_drive"], cell["F_spindle"], cell["rpm"], cell["gear"], cell["a"], cell["n"]))

    # ---- gear-vs-speed schedule Chrono actually uses (across all throttles, by speed cell) ----
    print("\n=== GEAR vs SPEED schedule Chrono uses (median over throttles in each speed cell) ===")
    print("    speed | gear (Chrono)")
    gear_sched = {}
    for si, c in enumerate(SPEED_CELLS):
        col = grid_gear[:, si]
        col = col[~np.isnan(col)]
        if len(col):
            g = int(np.round(np.median(col)))
            gear_sched[c] = g
            print("    %4.0f  |   %d  (range %d-%d over throttles)" % (
                c, g, int(np.nanmin(grid_gear[:, si])), int(np.nanmax(grid_gear[:, si]))))

    # ---- highlight the avoid operating point: throttle 0.16 @ 8 m/s ----
    print("\n=== AVOID OPERATING POINT highlight ===")
    ti16 = THROTTLES.index(0.16); si8 = SPEED_CELLS.index(8.0)
    if not np.isnan(grid_F[ti16, si8]):
        print("  F_drive @ throttle 0.16 / 8 m/s = %.1f N   (spindle cross-check %.1f N)" % (
            grid_F[ti16, si8], grid_Fsp[ti16, si8]))
        print("  Chrono gear @ 8 m/s = %d   engine rpm = %.0f" % (
            int(grid_gear[ti16, si8]), grid_rpm[ti16, si8]))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        OUT,
        mu0=MU0, mass=mass_g, r_eff=r_eff_g, gravity=GRAVITY,
        drag_coeff=DRAG_COEFF, crr=CRR,
        throttles=np.asarray(THROTTLES),
        speed_cells=np.asarray(SPEED_CELLS),
        F_drive=grid_F,            # [nThr, nSpeed] driven force from force balance [N]
        F_spindle=grid_Fsp,        # [nThr, nSpeed] driven force from read-off spindle torque [N]
        rpm=grid_rpm,              # [nThr, nSpeed]
        gear=grid_gear,            # [nThr, nSpeed] Chrono current gear (1-indexed in Chrono)
        accel=grid_a,              # [nThr, nSpeed]
        gear_schedule_speed=np.asarray(list(gear_sched.keys())),
        gear_schedule_gear=np.asarray(list(gear_sched.values())),
        driven_axle="FRONT" if drv_pos == "FRONT" else drv_pos,
        method="fixed_throttle_accel_sweep_force_balance_F=m*a+resistance(drag=0,Crr=0.0282)",
        note="F_drive = m*a + Crr*m*g (drag=0, Sedan no aero). F_spindle = sum(driven spindle "
             "torque)/r_eff is an independent read-off cross-check. Chrono gear is 1-indexed "
             "(gear 1 = first forward ratio). Driven axle is the FRONT (ShaftsDriveline2WD, "
             "driven_axle_idx=[0]).",
    )
    # also save the raw per-throttle samples (object array)
    raw = {f"samples_thr_{thr:.2f}".replace('.', 'p'): all_samples[thr] for thr in THROTTLES}
    np.savez(str(OUT).replace(".npz", "_raw.npz"), **raw)
    print("\nsaved %s" % OUT)


if __name__ == "__main__":
    main()
