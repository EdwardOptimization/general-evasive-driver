"""Measure the EXACT Chrono Sedan BRAKE max torque (the one GUESSED powertrain param).

The L1 faithful rewrite (gpu_physics_relax.py) PASSES the drift gate but is limited on the
avoidance (braking-heavy) regime by vx_rmse 1.31 (vs 0.235 on drift), localised to the
longitudinal/braking physics. The model's ``max_brake_torque`` (2000 N.m/wheel) was the single
GUESSED param. This script MEASURES it from Chrono — two independent ways:

  (A) READ-OFF (primary): instantiate the real Chrono Sedan (the same construction the HF backend
      and extract_chrono_tmeasy_curves.py use — ``veh.Sedan()`` + TMeasy), reach into each axle's
      brake subsystem (``ChAxle.m_brake_left/right``, a ``ChBrakeSimple``), Synchronize it at full
      modulation (1.0) and read ``GetBrakeTorque()``. ChBrakeSimple computes torque = modulation *
      maxtorque, so at modulation=1.0 ``GetBrakeTorque()`` IS the per-wheel max brake torque. We
      read all FOUR wheels (front + rear) — the Sedan brakes ALL FOUR.

  (B) DECEL TEST (independent cross-check): spin the free vehicle up to ~20 m/s straight, apply
      full brake (m_braking=1.0) on a high-mu terrain, and back out the per-wheel brake torque
      from the measured longitudinal deceleration:  4 * T_brake / r_eff ~= m * |a_decel| (when the
      tyres are not saturated), i.e. T_brake ~= m*|a|*r_eff/4. Reported next to the read-off value.

Saves to runs/feasibility_audit/phase4_f2/chrono_brake.npz.

Run inside the pinned chrono env:
    /home/quyaonan/miniforge3/envs/chrono/bin/python \
        scripts/feasibility_audit/extract_chrono_brake.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pychrono as chrono
import pychrono.vehicle as veh

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs/feasibility_audit/phase4_f2/chrono_brake.npz"

MU0 = 0.8
DT = 1e-3
INIT_Z = 0.3266


def build_car(chassis_fixed: bool):
    veh.SetDataPath(chrono.GetChronoDataPath() + "vehicle/")
    car = veh.Sedan()
    car.SetContactMethod(chrono.ChContactMethod_NSC)
    car.SetChassisFixed(chassis_fixed)
    car.SetChassisCollisionType(veh.CollisionType_NONE)
    car.SetInitPosition(chrono.ChCoordsysd(chrono.ChVector3d(0, 0, INIT_Z), chrono.QUNIT))
    car.SetTireType(veh.TireModelType_TMEASY)
    car.SetTireStepSize(DT)
    car.Initialize()
    return car


def read_off_brake_torque():
    """(A) Read the per-wheel max brake torque directly off each axle's ChBrakeSimple."""
    car = build_car(chassis_fixed=True)
    vehicle = car.GetVehicle()
    R = vehicle.GetTire(1, veh.LEFT).GetRadius()
    per_wheel = {}
    template = None
    for ai in range(vehicle.GetNumberAxles()):
        ax = vehicle.GetAxle(ai)
        for side, name in ((ax.m_brake_left, f"axle{ai}_left"), (ax.m_brake_right, f"axle{ai}_right")):
            template = side.GetTemplateName()
            side.Synchronize(1.0)               # full modulation -> GetBrakeTorque() == maxtorque
            per_wheel[name] = float(side.GetBrakeTorque())
    return per_wheel, template, float(R)


def decel_test(brake_torque_hint: float):
    """(B) Independent full-brake straight-line decel test; back out the per-wheel brake torque.

    Spin up to ~20 m/s, apply full brake on high-mu terrain, measure |a_decel| during the linear
    (non-locked) phase, and invert  4*T_brake/r_eff = m*|a|  ->  T_brake = m*|a|*r_eff/4."""
    car = build_car(chassis_fixed=False)
    vehicle = car.GetVehicle()
    R = vehicle.GetTire(1, veh.LEFT).GetRadius()
    body = vehicle.GetChassisBody()
    mass = float(vehicle.GetMass())
    terrain = veh.FlatTerrain(0.0, MU0)
    t = 0.0
    inp = veh.DriverInputs()

    # --- spin up to ~20 m/s ---
    target = 20.0
    inp.m_steering = 0.0; inp.m_braking = 0.0
    for _ in range(20000):
        v = body.GetRot().RotateBack(body.GetPosDt()).x
        if v >= target:
            break
        inp.m_throttle = float(min(max(0.4 * (target - v), 0.1), 1.0))
        car.Synchronize(t, inp, terrain); terrain.Synchronize(t)
        car.Advance(DT); terrain.Advance(DT); t += DT
    v0 = body.GetRot().RotateBack(body.GetPosDt()).x

    # --- full brake; record vx(t) ---
    inp.m_throttle = 0.0; inp.m_braking = 1.0
    ts, vs = [], []
    for _ in range(2500):
        v = body.GetRot().RotateBack(body.GetPosDt()).x
        ts.append(t); vs.append(v)
        if v <= 1.0:
            break
        car.Synchronize(t, inp, terrain); terrain.Synchronize(t)
        car.Advance(DT); terrain.Advance(DT); t += DT
    ts = np.asarray(ts); vs = np.asarray(vs)

    # decel over the steady (non-lock, non-standstill) window: from 90% v0 down to 4 m/s
    hi = 0.9 * v0
    win = (vs <= hi) & (vs >= 4.0)
    if win.sum() >= 5:
        slope = np.polyfit(ts[win], vs[win], 1)[0]   # dv/dt < 0
        a_decel = abs(float(slope))
    else:
        a_decel = abs(float((vs[-1] - vs[0]) / max(ts[-1] - ts[0], 1e-6)))
    # invert: total brake force at wheels ~ m*a (when tyres not saturated). 4 wheels.
    T_brake_per_wheel = mass * a_decel * R / 4.0
    return {
        "v0": float(v0), "mass": mass, "r_eff": float(R), "a_decel": a_decel,
        "T_brake_per_wheel_from_decel": float(T_brake_per_wheel),
        "vx_trace_t": ts, "vx_trace_v": vs,
    }


def main():
    per_wheel, template, R = read_off_brake_torque()
    vals = np.array(list(per_wheel.values()))
    max_brake_torque = float(np.median(vals))
    print("=== (A) READ-OFF from Chrono Sedan brake subsystem (%s) ===" % template)
    for k, v in per_wheel.items():
        print("  %-14s max brake torque = %.1f N.m" % (k, v))
    print("  -> per-wheel max brake torque (all 4 identical) = %.1f N.m" % max_brake_torque)
    print("  -> total (4 wheels) = %.1f N.m   r_eff = %.4f m" % (4 * max_brake_torque, R))

    print("\n=== (B) DECEL TEST cross-check (full brake, mu=%.2f) ===" % MU0)
    dt = decel_test(max_brake_torque)
    print("  v0=%.2f m/s  mass=%.1f kg  r_eff=%.4f m  a_decel=%.3f m/s^2" % (
        dt["v0"], dt["mass"], dt["r_eff"], dt["a_decel"]))
    print("  -> per-wheel brake torque backed out of decel = %.1f N.m" % dt["T_brake_per_wheel_from_decel"])
    print("     (decel test couples tyre friction + load transfer, so it is a sanity bound,")
    print("      not the exact per-wheel torque; the READ-OFF value is the measured param.)")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        OUT,
        max_brake_torque_per_wheel=max_brake_torque,
        per_wheel_left_right=vals,
        per_wheel_names=np.array(list(per_wheel.keys())),
        brake_template=template,
        total_brake_torque_4wheel=4 * max_brake_torque,
        r_eff=R,
        decel_v0=dt["v0"],
        decel_mass=dt["mass"],
        decel_a=dt["a_decel"],
        decel_T_brake_per_wheel=dt["T_brake_per_wheel_from_decel"],
        decel_vx_t=dt["vx_trace_t"],
        decel_vx_v=dt["vx_trace_v"],
        method="read_off_ChBrakeSimple_GetBrakeTorque_at_modulation_1",
        note="Sedan brakes ALL 4 wheels at this per-wheel torque; gpu_physics_relax brakes only "
             "the 2 rear -> front brake torque dropped. gpu_physics_brake brakes all 4.",
    )
    print("\nsaved %s" % OUT)
    print("MEASURED max_brake_torque = %.1f N.m/wheel (all 4 wheels braked => %.0f N.m total)" % (
        max_brake_torque, 4 * max_brake_torque))


if __name__ == "__main__":
    main()
