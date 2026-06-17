"""Measure the Chrono Sedan shift map at PARTIAL throttle (the cruise/replay operating point).

The full-throttle shift map (extract_chrono_shiftmap.py) matched the model's SHIFT_UP=(4000,4500,..)
which led to "gear is not a bug". But AutomaticTransmissionSimpleMap is THROTTLE-DEPENDENT: at low
throttle it upshifts at much LOWER rpm. This script spins the Sedan up holding a constant PARTIAL
throttle and records, at every step, (v, gear, rpm) so we see exactly what gear Chrono is in at the
cruise speeds 8/9.5/11 m/s and at what engine rpm it upshifts gear 1->2->3.

Run (chrono env).
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pychrono as chrono
import pychrono.vehicle as veh

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs/feasibility_audit/phase4_f2/chrono_shiftmap_partial.npz"
MU = 1.0
DT = 1e-3
INIT_Z = 0.3266
RPM = 60.0 / (2.0 * np.pi)
THROTTLES = [0.08, 0.12, 0.15, 0.20, 0.30]


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


def sweep(thr):
    car = build_car()
    v = car.GetVehicle()
    body = v.GetChassisBody()
    eng = v.GetEngine(); trans = v.GetTransmission()
    terrain = veh.FlatTerrain(0.0, MU)
    inp = veh.DriverInputs(); inp.m_steering = 0.0; inp.m_braking = 0.0
    t = 0.0
    inp.m_throttle = 0.0
    for _ in range(300):
        car.Synchronize(t, inp, terrain); terrain.Synchronize(t)
        car.Advance(DT); terrain.Advance(DT); t += DT
    inp.m_throttle = float(thr)
    prev_gear = int(trans.GetCurrentGear())
    prev_rpm = float(eng.GetMotorSpeed()) * RPM
    upshifts = []      # (from_gear, rpm_before, v)
    gear_at_v = {}     # speed cell -> gear
    cells = [5.0, 8.0, 9.5, 11.0, 14.0]
    for step in range(120000):
        car.Synchronize(t, inp, terrain); terrain.Synchronize(t)
        car.Advance(DT); terrain.Advance(DT); t += DT
        vv = float(body.GetRot().RotateBack(body.GetPosDt()).x)
        g = int(trans.GetCurrentGear())
        rpm = float(eng.GetMotorSpeed()) * RPM
        if g > prev_gear:
            upshifts.append((prev_gear, prev_rpm, vv))
        for c in cells:
            if c not in gear_at_v and abs(vv - c) < 0.05:
                gear_at_v[c] = (g, rpm)
        prev_gear, prev_rpm = g, rpm
        if vv > 16.0 or (step > 8000 and vv < 3.0):
            break
    return upshifts, gear_at_v, cells


def main():
    print("=== Chrono Sedan PARTIAL-throttle shift map @ mu=%.2f ===" % MU)
    for thr in THROTTLES:
        ups, gv, cells = sweep(thr)
        print("\n-- throttle %.2f --" % thr)
        print("  upshifts (from_gear[1-idx] -> rpm_before -> at v):")
        for fg, rpm, vv in ups:
            print("    gear %d -> %d   at rpm=%.0f   v=%.2f m/s" % (fg, fg + 1, rpm, vv))
        print("  gear @ cruise speeds:")
        for c in cells:
            if c in gv:
                g, rpm = gv[c]
                print("    v=%4.1f : gear %d (1-idx)  rpm=%.0f" % (c, g, rpm))


if __name__ == "__main__":
    main()
