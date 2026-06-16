"""Measure the EXACT Chrono Sedan COASTDOWN longitudinal resistance (drag + rolling).

The L1 faithful rewrite (gpu_physics_relax.py) PASSES the drift gate but runs TOO FAST in the
cruise / avoidance regime: replaying the avoid oracle, the surrogate vx error grows from ~0.03 at
step 0 to +0.74 by step 50 (vx_rmse 1.21 vs the drift floor 0.235; vy/lateral is faithful at
~0.14). The diagnosis is a LONGITUDINAL FORCE-BALANCE gap: the two longitudinal resistance params
``drag_coeff`` (0.80) and ``rolling_resist_coeff`` (0.03) were CALIBRATED on the drift saddle
(high-sideslip, ~9 m/s) where the dominant longitudinal sink is induced drag from the sideslipping
tyres, NOT the cruise resistance. At low sideslip (cruise/avoidance) those calibrated values are
too LOW, so the model under-resists and over-speeds.

This script MEASURES the cruise resistance directly, the same way ``extract_chrono_brake.py`` /
``extract_chrono_tmeasy_curves.py`` measure their params -- it instantiates the REAL Chrono Sedan
(``veh.Sedan()`` + TMeasy, mu0=0.8, the exact construction the HF backend
``chrono_vehicle_backend.py`` uses), brings it to a target speed on flat avoidance-mu terrain, then
ZEROS throttle and brake (engine in gear, no driver torque) and lets it COAST. We record vx(t) and
fit the model's own resistance law to the measured deceleration:

    Chrono coastdown decel  a(v) = -dv/dt   (measured)
    model resistance accel  a(v) = (drag_coeff / m) * v^2 + rolling_resist_coeff * g
        (this is EXACTLY what gpu_physics_relax._accel_from_forces applies:
             drag    = drag_coeff * vx * |vx|              [N]
             rolling = rolling_resist_coeff * m * g * tanh(vx)  [N]
         so the deceleration is drag/m + rolling/m = (drag_coeff/m) v^2 + Crr*g for vx>~1.)

A linear least-squares fit of a(v) vs (v^2, 1) yields:

    slope  = drag_coeff / m      ->  MEASURED drag_coeff = slope * m
    offset = rolling_resist_coeff * g  ->  MEASURED Crr   = offset / g

We coast TWICE -- once from the avoidance/cruise speed band (~12-15 m/s) and once from the drift
speed (~9 m/s) -- to check the resistance is consistent across the two regimes and report whether a
single (drag, Crr) pair describes both. The coast is on the SCENARIO terrain mu (~0.8); the
free-rolling tyres see no sideslip, so this isolates the CRUISE longitudinal resistance the
avoidance regime needs (aero + rolling + driveline/engine-brake drag through the gearbox -- whatever
the coastdown actually shows IS the measurement; the Sedan has no explicit aero body, so the v^2
term here lumps any speed-squared resistance the multibody+tyre+driveline produce).

Saves to runs/feasibility_audit/phase4_f2/chrono_coastdown.npz.

Run inside the pinned chrono env:
    /home/quyaonan/miniforge3/envs/chrono/bin/python \
        scripts/feasibility_audit/extract_chrono_coastdown.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pychrono as chrono
import pychrono.vehicle as veh

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs/feasibility_audit/phase4_f2/chrono_coastdown.npz"

MU0 = 0.8          # avoidance / cruise terrain friction (Sedan_TMeasyTire reference mu)
DT = 1e-3
INIT_Z = 0.3266    # near static ride height (same as extract_chrono_brake.py)
GRAVITY = 9.81

# calibrated drift-saddle values currently in gpu_physics_relax.PhysParams (for comparison)
CAL_DRAG = 0.80
CAL_ROLL = 0.03


def build_car():
    """Build the real Chrono Sedan exactly as the HF backend / extraction scripts do."""
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


def spin_up_to(car, terrain, body, target, t0):
    """Throttle the free vehicle up to `target` m/s straight-line on `terrain`. Returns time."""
    inp = veh.DriverInputs()
    inp.m_steering = 0.0
    inp.m_braking = 0.0
    t = t0
    for _ in range(40000):
        v = body.GetRot().RotateBack(body.GetPosDt()).x
        if v >= target:
            break
        inp.m_throttle = float(min(max(0.4 * (target - v), 0.1), 1.0))
        car.Synchronize(t, inp, terrain)
        terrain.Synchronize(t)
        car.Advance(DT)
        terrain.Advance(DT)
        t += DT
    return t


def coastdown(car, terrain, body, t0, v_floor=2.0, max_steps=60000):
    """Zero throttle + brake; let the vehicle coast. Record (t, vx). Stop at v_floor."""
    inp = veh.DriverInputs()
    inp.m_steering = 0.0
    inp.m_throttle = 0.0          # no driver torque -> engine/driveline drag only
    inp.m_braking = 0.0           # NO brake -- pure coastdown resistance
    t = t0
    ts, vs = [], []
    for _ in range(max_steps):
        v = body.GetRot().RotateBack(body.GetPosDt()).x
        ts.append(t)
        vs.append(v)
        if v <= v_floor:
            break
        car.Synchronize(t, inp, terrain)
        terrain.Synchronize(t)
        car.Advance(DT)
        terrain.Advance(DT)
        t += DT
    return np.asarray(ts), np.asarray(vs)


def decel_from_trace(ts, vs, v_lo, v_hi):
    """Numeric a(v) = -dv/dt over the steady coast window v in [v_lo, v_hi].

    Smooths vx with a short moving average, central-differences to get -dv/dt, and bins by speed.
    Returns (v_bins, a_bins) for the LS resistance fit."""
    # short moving-average smoothing of the (already smooth) vx trace to kill 1 kHz ripple
    k = 25
    kernel = np.ones(k) / k
    vsm = np.convolve(vs, kernel, mode="same")
    # use the interior (avoid convolution edge transients)
    lo, hi = k, len(vsm) - k
    tc = ts[lo:hi]
    vc = vsm[lo:hi]
    # -dv/dt by central difference
    a = -np.gradient(vc, tc)
    win = (vc >= v_lo) & (vc <= v_hi) & (a > 0.0)
    return vc[win], a[win]


def fit_resistance(v, a):
    """LS fit a(v) = (drag_coeff/m) v^2 + Crr*g  ->  return (slope, offset, drag/m, Crr*g)."""
    # design matrix [v^2, 1]; a = slope*v^2 + offset
    Xd = np.vstack([v * v, np.ones_like(v)]).T
    coef, *_ = np.linalg.lstsq(Xd, a, rcond=None)
    slope, offset = float(coef[0]), float(coef[1])
    return slope, offset


def measure(label, target, v_lo, v_hi, mass_holder):
    car = build_car()
    vehicle = car.GetVehicle()
    body = vehicle.GetChassisBody()
    # TOTAL vehicle mass (chassis + suspension + wheels) -- the mass the resistance decelerates.
    mass = float(vehicle.GetMass())
    mass_holder["mass"] = mass
    terrain = veh.FlatTerrain(0.0, MU0)
    t = 0.0
    t = spin_up_to(car, terrain, body, target, t)
    v0 = float(body.GetRot().RotateBack(body.GetPosDt()).x)
    ts, vs = coastdown(car, terrain, body, t)
    v_fit, a_fit = decel_from_trace(ts, vs, v_lo, v_hi)
    slope, offset = fit_resistance(v_fit, a_fit)
    drag_coeff = slope * mass
    crr = offset / GRAVITY
    print("=== COASTDOWN: %s (target %.1f m/s, fit window %.1f-%.1f m/s) ===" % (
        label, target, v_lo, v_hi))
    print("  v0=%.2f m/s  coast lasted %.2f s  mass=%.1f kg  fit points=%d" % (
        v0, ts[-1] - ts[0], mass, len(v_fit)))
    print("  a(v) = (drag/m) v^2 + Crr*g :  slope=%.6e /m  offset=%.4f m/s^2" % (slope, offset))
    print("  -> MEASURED drag_coeff = %.4f   rolling_resist_coeff (Crr) = %.5f" % (drag_coeff, crr))
    print("     decel @ %4.1f m/s : measured=%.4f  model-fit=%.4f m/s^2" % (
        target, np.interp(target, v_fit[np.argsort(v_fit)], a_fit[np.argsort(v_fit)]) if len(v_fit) else float("nan"),
        slope * target * target + offset))
    return dict(
        label=label, target=float(target), v0=v0, mass=mass,
        ts=ts, vs=vs, v_fit=v_fit, a_fit=a_fit,
        slope=slope, offset=offset, drag_coeff=float(drag_coeff), crr=float(crr),
        v_lo=float(v_lo), v_hi=float(v_hi),
    )


def main():
    mass_holder: dict[str, float] = {}
    # (1) avoidance / cruise band: spin to 15, fit the steady coast 13 -> 5 m/s.
    cruise = measure("cruise/avoidance", target=15.0, v_lo=5.0, v_hi=13.0, mass_holder=mass_holder)
    # (2) drift speed band: spin to 10, fit the steady coast 9 -> 4 m/s (consistency check).
    drift = measure("drift-speed", target=10.0, v_lo=4.0, v_hi=9.0, mass_holder=mass_holder)

    # ---- joint fit over BOTH bands (single drag, single Crr describing all coast data) ----
    v_all = np.concatenate([cruise["v_fit"], drift["v_fit"]])
    a_all = np.concatenate([cruise["a_fit"], drift["a_fit"]])
    slope_j, offset_j = fit_resistance(v_all, a_all)
    drag_j = slope_j * mass_holder["mass"]
    crr_j = offset_j / GRAVITY
    print("\n=== JOINT fit over BOTH coast bands (one drag + one Crr) ===")
    print("  -> MEASURED drag_coeff = %.4f   rolling_resist_coeff (Crr) = %.5f   (mass=%.1f kg)" % (
        drag_j, crr_j, mass_holder["mass"]))
    print("  per-band consistency: cruise(drag=%.4f Crr=%.5f) vs drift(drag=%.4f Crr=%.5f)" % (
        cruise["drag_coeff"], cruise["crr"], drift["drag_coeff"], drift["crr"]))

    print("\n=== vs CALIBRATED (drift-saddle) gpu_physics_relax defaults ===")
    print("  calibrated: drag_coeff=%.2f  rolling_resist_coeff=%.3f" % (CAL_DRAG, CAL_ROLL))
    print("  measured  : drag_coeff=%.4f  rolling_resist_coeff=%.5f  (JOINT fit)" % (drag_j, crr_j))
    # decel comparison at a representative cruise speed
    vrep = 13.0
    a_cal = (CAL_DRAG / mass_holder["mass"]) * vrep * vrep + CAL_ROLL * GRAVITY
    a_meas = slope_j * vrep * vrep + offset_j
    print("  resistance accel @ %.0f m/s: calibrated=%.4f  measured=%.4f m/s^2  (ratio %.2fx)" % (
        vrep, a_cal, a_meas, a_meas / max(a_cal, 1e-6)))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        OUT,
        mu0=MU0,
        mass=mass_holder["mass"],
        gravity=GRAVITY,
        # joint (recommended) measured resistance
        drag_coeff_measured=drag_j,
        rolling_resist_coeff_measured=crr_j,
        slope_joint=slope_j,
        offset_joint=offset_j,
        # per-band fits
        cruise_drag_coeff=cruise["drag_coeff"],
        cruise_crr=cruise["crr"],
        cruise_slope=cruise["slope"],
        cruise_offset=cruise["offset"],
        cruise_v0=cruise["v0"],
        cruise_ts=cruise["ts"],
        cruise_vs=cruise["vs"],
        cruise_v_fit=cruise["v_fit"],
        cruise_a_fit=cruise["a_fit"],
        drift_drag_coeff=drift["drag_coeff"],
        drift_crr=drift["crr"],
        drift_slope=drift["slope"],
        drift_offset=drift["offset"],
        drift_v0=drift["v0"],
        drift_ts=drift["ts"],
        drift_vs=drift["vs"],
        drift_v_fit=drift["v_fit"],
        drift_a_fit=drift["a_fit"],
        # calibrated reference
        drag_coeff_calibrated=CAL_DRAG,
        rolling_resist_coeff_calibrated=CAL_ROLL,
        method="coastdown_zero_throttle_zero_brake_LS_fit_a(v)=drag/m*v^2+Crr*g",
        note="Sedan has no explicit aero body; the v^2 term lumps any speed-squared resistance the "
             "multibody+tyre+driveline produce during a free coast. Crr captures rolling + the "
             "constant driveline/engine-brake drag in gear. Fit in gpu_physics_relax model units.",
    )
    print("\nsaved %s" % OUT)


if __name__ == "__main__":
    main()
