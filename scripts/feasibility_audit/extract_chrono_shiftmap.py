"""Measure the EXACT Chrono Sedan automatic-transmission SHIFT-UP / SHIFT-DOWN rpm map — the
per-gear engine-speed bands the running ``veh.Sedan()`` actually uses to upshift/downshift.

WHY: gpu_physics_pwr hard-codes SHIFT_UP=(4000,4500,4500,4500,4500,4500) (from the shipped JSON
``Sedan_AutomaticTransmissionSimpleMap.json``). The faithful-rewrite gap decomposition
(docs/gpu-surrogate-design-2026-06.md) flagged the gearbox as one gear too LOW at 8 m/s, so the
model sits at a low gear ratio (high driveshaft torque) and over-accelerates in the avoidance
throttle ramp. This script MEASURES the true shift map empirically, the same isolated-Chrono way
the brake / powertrain / coastdown params were measured: instantiate the real ``veh.Sedan()`` +
TMeasy, instrument ``trans.GetCurrentGear()`` + ``eng.GetMotorSpeed()`` at every step, and record:

  - SHIFT-UP rpm per gear: at FULL throttle the car accelerates; record the engine rpm at the
    step BEFORE each upshift fires (the model's gearbox FSM compares motor_rpm > SHIFT_UP[gear]).
  - SHIFT-DOWN rpm per gear: after reaching top speed, lift throttle and brake gently so the car
    decelerates through every gear; record the engine rpm at the step BEFORE each downshift.

The Chrono ``AutomaticTransmissionSimpleMap`` shift logic compares the ENGINE (motorshaft) speed to
the per-gear (down, up) band. ``GetCurrentGear()`` is 1-indexed in Chrono (gear 1 = first forward
ratio = ratios[0] in the model's 0-indexed GEAR_RATIOS). We report both the per-gear measured band
AND the model's current SHIFT_UP/SHIFT_DOWN for side-by-side.

Saves runs/feasibility_audit/phase4_f2/chrono_shiftmap.npz.

Run inside the pinned chrono env:
    /home/quyaonan/miniforge3/envs/chrono/bin/python \
        scripts/feasibility_audit/extract_chrono_shiftmap.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pychrono as chrono
import pychrono.vehicle as veh

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs/feasibility_audit/phase4_f2/chrono_shiftmap.npz"

MU0 = 0.8
DT = 1e-3
INIT_Z = 0.3266
GRAVITY = 9.81
RPM = 60.0 / (2.0 * np.pi)   # rad/s -> rpm

# the model's current (pwr) shift map, for side-by-side.
MODEL_SHIFT_UP = (4000.0, 4500.0, 4500.0, 4500.0, 4500.0, 4500.0)
MODEL_SHIFT_DOWN = (1000.0, 1200.0, 1400.0, 1600.0, 1800.0, 2000.0)
MODEL_GEAR_RATIOS = (0.265, 0.489, 0.784, 1.063, 1.276, 1.499)


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


def run_accel_then_decel():
    """Full-throttle accel (capture upshifts), then lift+brake decel (capture downshifts).

    Returns (up_events, down_events, trace) where each event is a dict
    {from_gear, to_gear, rpm_before, v} captured at the step where GetCurrentGear() changes."""
    car = build_car()
    vehicle = car.GetVehicle()
    body = vehicle.GetChassisBody()
    eng = vehicle.GetEngine()
    trans = vehicle.GetTransmission()
    terrain = veh.FlatTerrain(0.0, MU0)
    inp = veh.DriverInputs()
    inp.m_steering = 0.0

    t = 0.0
    # settle 0.3 s at zero throttle
    inp.m_throttle = 0.0; inp.m_braking = 0.0
    for _ in range(300):
        car.Synchronize(t, inp, terrain); terrain.Synchronize(t)
        car.Advance(DT); terrain.Advance(DT); t += DT

    up_events, down_events, trace = [], [], []
    prev_gear = int(trans.GetCurrentGear())
    prev_rpm = float(eng.GetMotorSpeed()) * RPM

    # ----- PHASE 1: full throttle accelerate to top speed (capture UPSHIFTS) -----
    inp.m_throttle = 1.0; inp.m_braking = 0.0
    v_top = 0.0
    for step in range(60000):
        car.Synchronize(t, inp, terrain); terrain.Synchronize(t)
        car.Advance(DT); terrain.Advance(DT); t += DT
        v = float(body.GetRot().RotateBack(body.GetPosDt()).x)
        g = int(trans.GetCurrentGear())
        rpm = float(eng.GetMotorSpeed()) * RPM
        trace.append((t, v, g, rpm, 1.0, 0.0))
        if g > prev_gear:   # an UPSHIFT just happened; rpm_before is the previous step's rpm
            up_events.append(dict(from_gear=prev_gear, to_gear=g, rpm_before=prev_rpm, v=v))
        prev_gear, prev_rpm = g, rpm
        v_top = max(v_top, v)
        # stop once at terminal speed (accel ~ 0 sustained) or top gear reached and fast
        if step > 2000 and g >= 6 and v > 30.0:
            break
        if v > 45.0:
            break

    # ----- PHASE 2: lift + gentle brake to decelerate through every gear (capture DOWNSHIFTS) -----
    inp.m_throttle = 0.0; inp.m_braking = 0.18   # light brake so it rolls down through the gears
    for step in range(80000):
        car.Synchronize(t, inp, terrain); terrain.Synchronize(t)
        car.Advance(DT); terrain.Advance(DT); t += DT
        v = float(body.GetRot().RotateBack(body.GetPosDt()).x)
        g = int(trans.GetCurrentGear())
        rpm = float(eng.GetMotorSpeed()) * RPM
        trace.append((t, v, g, rpm, 0.0, 0.18))
        if g < prev_gear:   # a DOWNSHIFT just happened
            down_events.append(dict(from_gear=prev_gear, to_gear=g, rpm_before=prev_rpm, v=v))
        prev_gear, prev_rpm = g, rpm
        if v < 0.6:
            break
    return up_events, down_events, np.asarray(trace), v_top


def main():
    print("=== Chrono Sedan SHIFT MAP — isolated veh.Sedan() + TMeasy, full-throttle accel + brake decel ===")
    car = build_car(); v = car.GetVehicle()
    trans = v.GetTransmission()
    print("  transmission template:", trans.GetTemplateName(),
          " max gear:", int(trans.GetMaxGear()))
    del car, v

    up_events, down_events, trace, v_top = run_accel_then_decel()
    print("  reached top speed ~ %.1f m/s" % v_top)

    # ---- measured SHIFT-UP rpm per gear (Chrono 1-indexed gear g -> model 0-indexed gear g-1) ----
    # the model upshifts from gear-index i when motor_rpm > SHIFT_UP[i]. Chrono upshift from gear g
    # (1-indexed) to g+1 => model index i = g-1.
    measured_up = {}     # model gear index (0-based) -> measured shift-up rpm
    print("\n=== UPSHIFT events (full throttle) ===")
    print("  from_gear(Chrono 1-idx) -> to_gear   rpm_before_shift   v(m/s)   [model gear-idx]")
    for e in up_events:
        i = e["from_gear"] - 1   # model 0-indexed gear that triggered the upshift
        # keep the FIRST (cleanest) upshift rpm per gear
        if i not in measured_up:
            measured_up[i] = e["rpm_before"]
        print("    gear %d -> %d    rpm=%.0f    v=%.1f    [model idx %d]" % (
            e["from_gear"], e["to_gear"], e["rpm_before"], e["v"], i))

    measured_down = {}
    print("\n=== DOWNSHIFT events (lift + light brake) ===")
    print("  from_gear(Chrono 1-idx) -> to_gear   rpm_before_shift   v(m/s)   [model gear-idx target]")
    for e in down_events:
        # the model downshifts from gear-index i when motor_rpm < SHIFT_DOWN[i]; Chrono downshift
        # from gear g (1-idx) to g-1 => model index i = g-1.
        i = e["from_gear"] - 1
        if i not in measured_down:
            measured_down[i] = e["rpm_before"]
        print("    gear %d -> %d    rpm=%.0f    v=%.1f    [model idx %d]" % (
            e["from_gear"], e["to_gear"], e["rpm_before"], e["v"], i))

    # ---- assemble the per-gear measured map (model 0-indexed, 6 gears), side-by-side ----
    nG = 6
    shift_up = np.array([measured_up.get(i, MODEL_SHIFT_UP[i]) for i in range(nG)], np.float64)
    shift_down = np.array([measured_down.get(i, MODEL_SHIFT_DOWN[i]) for i in range(nG)], np.float64)

    print("\n=== MEASURED SHIFT MAP (model 0-indexed gears) vs CURRENT pwr model ===")
    print("  gear-idx | ratio  | measured UP | model UP | measured DOWN | model DOWN")
    for i in range(nG):
        mu_up = ("%.0f" % shift_up[i]) if i in measured_up else "(n/a:%.0f)" % MODEL_SHIFT_UP[i]
        mu_dn = ("%.0f" % shift_down[i]) if i in measured_down else "(n/a:%.0f)" % MODEL_SHIFT_DOWN[i]
        print("     %d     | %.3f | %11s | %8.0f | %13s | %10.0f" % (
            i, MODEL_GEAR_RATIOS[i], mu_up, MODEL_SHIFT_UP[i], mu_dn, MODEL_SHIFT_DOWN[i]))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        OUT,
        shift_up=shift_up,                 # [6] measured shift-up rpm per model gear-idx
        shift_down=shift_down,             # [6] measured shift-down rpm per model gear-idx
        measured_up_gears=np.array(sorted(measured_up.keys())),
        measured_down_gears=np.array(sorted(measured_down.keys())),
        model_shift_up=np.asarray(MODEL_SHIFT_UP),
        model_shift_down=np.asarray(MODEL_SHIFT_DOWN),
        gear_ratios=np.asarray(MODEL_GEAR_RATIOS),
        trace=trace,                       # [T,6] (t, v, gear, rpm, throttle, brake)
        v_top=v_top,
        method="empirical_shift_detection_full_throttle_accel_plus_brake_decel_on_running_Sedan",
        note="shift_up[i]/shift_down[i] are the measured ENGINE rpm at which the running veh.Sedan() "
             "AutomaticTransmissionSimpleMap up/down-shifts FROM model gear-index i (0-based; Chrono "
             "gear is 1-indexed, model idx = Chrono gear - 1). Gears never visited keep the model "
             "default (shipped JSON value).",
    )
    print("\nsaved %s" % OUT)
    print("MEASURED SHIFT_UP   = (%s)" % ", ".join("%.0f" % x for x in shift_up))
    print("MEASURED SHIFT_DOWN = (%s)" % ", ".join("%.0f" % x for x in shift_down))


if __name__ == "__main__":
    main()
