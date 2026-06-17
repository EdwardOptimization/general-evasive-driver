"""Extract the per-corner KINEMATIC SUSPENSION LOOKUPS from the real Chrono Sedan.

This is the foundational, reusable artifact for the Tier-(a) GPU template port
(docs/chrono-template-gpu-translation-plan-2026-06.md): a faithful, cross-vehicle,
GPU-batchable vehicle model = chassis 6-DOF + 4 corners driven by per-corner lookups
of how each wheel's camber / toe / track / wheel-center position and the WHEEL RATE
(effective vertical stiffness at the contact patch, including the motion ratio) vary
with suspension travel and steer -- derived FROM Chrono's actual linkage so the GPU
model matches Chrono's wheel envelope WITHOUT porting the full constraint solver.

METHOD AND WHY (see the deliverable notes at the end of this docstring):

  PRIMARY rig attempt (ChSuspensionTestRigPlatform): Chrono DOES ship the standard
  suspension-kinematics rig and pychrono exposes ChSuspensionTestRigPlatform /
  ChSuspensionTestRigPushrod. We verified it builds and runs on the real Sedan via the
  spec-file constructor + ReadTireJSON tire attach (matching pychrono's own
  demo_VEH_SuspensionTestRig), testing BOTH axles (front DoubleWishbone + rear MultiLink)
  at once. BUT the pychrono rig has three blocking limitations for THIS measurement:
    (1) the shared_ptr<ChWheeledVehicle> rig ctor REJECTS the C++ veh.Sedan().GetVehicle()
        raw reference (TypeError) and SEGFAULTS on a Python-owned veh.WheeledVehicle; only
        the spec-file ctor (vehicle built C++-side) works;
    (2) two rigs cannot coexist in one process, and testing a non-front axle ALONE
        segfaults rig.Initialize -> each sweep would need its own subprocess;
    (3) the rig holds the chassis FIXED on posts that push the TIRE, so GetActuatorForce
        returns only the unsprung weight (~981 N, constant) -- NOT the wheel rate -- and
        the post displacement couples to the wheel through the (stiff) tire, so it does
        not cleanly command suspension travel; the front and rear also fall in different
        ride-height windows (the front spring tops out below ride 0.20 m).

  CHOSEN METHOD (faithful, single-process, no rig pathologies): a FREE-VEHICLE ramped
  vertical-load sweep on the real C++ veh.Sedan() -- the EXACT vehicle the HF backend runs
  (DoubleWishbone front + RackPinion, MultiLink rear, TMeasy tires; stock 1684 kg, no
  chassis-mass override here so the static loads are Chrono's own). The chassis is free; we
  (a) settle under gravity to read the TRUE static (ride) camber/toe/track/position per
  corner, then (b) ramp an extra vertical force on the chassis COM from lift (-0.55 W) to
  push (+1.0 W), which moves all four suspensions through rebound<->jounce while every wheel
  stays grounded, reading the spindle pose, spring force/length and tire normal force at
  each settled level. The true Chrono constraint solver runs the real linkage every step,
  so the kinematics are MEASURED, not approximated. For the front (steered) corners we
  additionally sweep the steering driver input (-1..+1 -> +/- max steer via the real
  RackPinion) and read toe/camber vs steer = the steering kinematics incl. Ackermann.

PER CORNER (FL, FR, RL, RR), vs SUSPENSION TRAVEL z = (wheel_center_z - chassis_z) - static,
positive = jounce (compression):
  - camber angle (deg), toe angle (deg),
  - half-track change = lateral wheel-center shift vs static (m), wheel-center (x, y, z) (m),
  - WHEEL RATE = |d(tire normal force)/dz| near static (N/m) -- the effective vertical
    stiffness at the contact patch INCLUDING the motion ratio (also cross-checked against
    k_spring * |MR| from the measured spring force/length), and the static (ride) values.
FRONT corners also: toe/camber vs steering input (rack travel) = Ackermann steering kin.

Saved to runs/feasibility_audit/phase4_f2/chrono_suspension_kin.npz.

Run inside the pinned chrono env:
    conda run --no-capture-output -n chrono python \
        scripts/feasibility_audit/extract_chrono_suspension_kinematics.py
"""
from __future__ import annotations

import math
import os
from pathlib import Path

import numpy as np
import pychrono as chrono
import pychrono.vehicle as veh

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs/feasibility_audit/phase4_f2/chrono_suspension_kin.npz"

DT = 1e-3
SETTLE_STATIC_STEPS = 3000     # settle under gravity to the static ride point
SETTLE_PER_LOAD_STEPS = 1400   # settle at each load level (quasi-static)
N_LOAD = 23                    # vertical-load sweep points
# Lift/push fractions of vehicle weight. The window is kept inside the range where every
# wheel stays grounded and inside the linkage travel limits: beyond ~ -0.55 W the rear
# over-droops (>0.25 m, off the MultiLink range) and at +1.0 W a front wheel briefly lifts.
LOAD_FRAC_LO = -0.45           # lift fraction of weight (rebound)
LOAD_FRAC_HI = 0.90            # push fraction of weight (jounce)
GROUNDED_FORCE_N = 80.0        # tire normal force above this => wheel grounded (kept)
N_STEER = 21                   # steering sweep points
SETTLE_PER_STEER_STEPS = 600   # settle at each steer level

# corner -> (axle, side, side_sign). Left spindle +Y outboard => sign +1; right => -1.
CORNERS = {
    "FL": (0, veh.LEFT, +1.0),
    "FR": (0, veh.RIGHT, -1.0),
    "RL": (1, veh.LEFT, +1.0),
    "RR": (1, veh.RIGHT, -1.0),
}


def _build_free_sedan():
    veh.SetDataPath(chrono.GetChronoDataPath() + "vehicle/")
    car = veh.Sedan()
    car.SetContactMethod(chrono.ChContactMethod_SMC)
    car.SetChassisFixed(False)
    car.SetChassisCollisionType(veh.CollisionType_NONE)
    car.SetInitPosition(chrono.ChCoordsysd(chrono.ChVector3d(0, 0, 0.45), chrono.QUNIT))
    car.SetTireType(veh.TireModelType_TMEASY)
    car.SetTireStepSize(DT)
    car.Initialize()
    return car


def _camber_toe_deg(q, side_sign: float) -> tuple[float, float]:
    """Camber and toe (deg) from the spindle frame.

    Chrono spindle local +Y is the wheel spin axis; we normalise it OUTBOARD with
    side_sign (+1 left, -1 right).
      camber = tilt of the spin axis out of the horizontal plane (asin of its z).
               Positive => top of wheel leans OUT.
      toe    = plan-view rotation of the spin axis about +Z away from pure lateral.
               Positive => toe-IN (front of the wheel points inward).
    """
    R = chrono.ChMatrix33d(q)
    sy = R.GetAxisY()
    spin = np.array([sy.x, sy.y, sy.z]) * side_sign
    camber = math.degrees(math.asin(max(-1.0, min(1.0, spin[2]))))
    toe = math.degrees(math.atan2(-spin[0], abs(spin[1])))
    return camber, toe


def _read_corners(v, susp, terrain):
    """Return per-corner (camber, toe, wx, wy, wz, Fspring, Lspring, Ftire)."""
    out = {}
    for cname, (axle, side, sign) in CORNERS.items():
        q = v.GetSpindleRot(axle, side)
        p = v.GetSpindlePos(axle, side)
        cam, toe = _camber_toe_deg(q, sign)
        fspr = float(susp[axle].GetSpringForce(side))
        lspr = float(susp[axle].GetSpringLength(side))
        ftire = float(v.GetTire(axle, side).ReportTireForce(terrain).force.z)
        out[cname] = (cam, toe, float(p.x), float(p.y), float(p.z), fspr, lspr, ftire)
    return out


def _advance(car, terrain, inp, n, t):
    for _ in range(n):
        car.Synchronize(t, inp, terrain)
        terrain.Synchronize(t)
        car.Advance(DT)
        terrain.Advance(DT)
        t += DT
    return t


def run_travel_sweep():
    car = _build_free_sedan()
    v = car.GetVehicle()
    body = v.GetChassisBody()
    terrain = veh.FlatTerrain(0.0, 0.9)
    susp = [veh.CastToChDoubleWishbone(v.GetSuspension(0)),
            veh.CastToChMultiLink(v.GetSuspension(1))]
    inp = veh.DriverInputs()
    inp.m_steering = 0.0
    inp.m_throttle = 0.0
    inp.m_braking = 0.0

    t = 0.0
    t = _advance(car, terrain, inp, SETTLE_STATIC_STEPS, t)
    chassis_z0 = float(body.GetPos().z)
    static = _read_corners(v, susp, terrain)
    mass = float(v.GetMass())
    W = mass * 9.81

    # static suspension travel reference = wheel_z - chassis_z at static
    susp_travel_ref = {c: static[c][4] - chassis_z0 for c in CORNERS}

    fracs = np.linspace(LOAD_FRAC_LO, LOAD_FRAC_HI, N_LOAD)
    records = {c: [] for c in CORNERS}
    for frac in fracs:
        Fz = float(frac) * W
        for _ in range(SETTLE_PER_LOAD_STEPS):
            body.EmptyAccumulators()
            body.AccumulateForce(chrono.ChVector3d(0, 0, Fz), body.GetPos(), False)
            car.Synchronize(t, inp, terrain)
            terrain.Synchronize(t)
            car.Advance(DT)
            terrain.Advance(DT)
            t += DT
        cz = float(body.GetPos().z)
        corners = _read_corners(v, susp, terrain)
        for c in CORNERS:
            cam, toe, wx, wy, wz, fspr, lspr, ftire = corners[c]
            travel = (wz - cz) - susp_travel_ref[c]  # +jounce (compression)
            records[c].append((travel, cam, toe, wx, wy, wz, fspr, lspr, ftire, cz))
    car.GetSystem().Clear()
    return records, static, chassis_z0, mass


def run_steer_sweep():
    car = _build_free_sedan()
    v = car.GetVehicle()
    terrain = veh.FlatTerrain(0.0, 0.9)
    inp = veh.DriverInputs()
    inp.m_steering = 0.0
    inp.m_throttle = 0.0
    inp.m_braking = 0.0
    max_steer = float(v.GetMaxSteeringAngle())

    t = 0.0
    t = _advance(car, terrain, inp, SETTLE_STATIC_STEPS, t)

    steer_inputs = np.linspace(-1.0, 1.0, N_STEER)
    records = {"FL": [], "FR": []}
    for s in steer_inputs:
        inp.m_steering = float(s)
        t = _advance(car, terrain, inp, SETTLE_PER_STEER_STEPS, t)
        for cname in ("FL", "FR"):
            axle, side, sign = CORNERS[cname]
            q = v.GetSpindleRot(axle, side)
            cam, toe = _camber_toe_deg(q, sign)
            records[cname].append((float(s), cam, toe))
    car.GetSystem().Clear()
    return records, max_steer


def _wheel_rate_from_tire(travel: np.ndarray, ftire: np.ndarray) -> float:
    """Wheel rate = |d(tire normal force)/d(suspension travel)| near static (travel=0)."""
    order = np.argsort(travel)
    z = travel[order]
    F = ftire[order]
    grounded = F > 50.0
    z = z[grounded]
    F = F[grounded]
    if len(z) < 4:
        return float("nan")
    ctr = int(np.argmin(np.abs(z)))
    sl = slice(max(0, ctr - 5), min(len(z), ctr + 6))
    slope = np.polyfit(z[sl], F[sl], 1)[0]
    return float(abs(slope))


def _wheel_rate_from_spring(travel, fspr, lspr) -> tuple[float, float]:
    """Cross-check wheel rate via |dF_spring/dz * MR|, MR = dL_spring/d(travel) near static."""
    order = np.argsort(travel)
    z = np.asarray(travel)[order]
    F = np.asarray(fspr)[order]
    L = np.asarray(lspr)[order]
    active = F > 200.0
    z = z[active]
    F = F[active]
    L = L[active]
    if len(z) < 5:
        return float("nan"), float("nan")
    ctr = int(np.argmin(np.abs(z)))
    sl = slice(max(0, ctr - 5), min(len(z), ctr + 6))
    dF = float(np.polyfit(z[sl], F[sl], 1)[0])     # dF_spring/dz
    MR = float(np.polyfit(z[sl], L[sl], 1)[0])     # dL_spring/dz (motion ratio)
    return abs(dF * MR), abs(MR)


def main():
    print("=== Chrono Sedan per-corner kinematic suspension extraction ===")
    print("method: FREE veh.Sedan() (DoubleWishbone+RackPinion front / MultiLink rear, TMeasy);")
    print("        gravity-static read + ramped chassis vertical-load travel sweep + steer sweep;")
    print("        TRUE Chrono linkage solver every step. (ChSuspensionTestRig limits noted in docstring.)\n")

    records, static, chassis_z0, mass = run_travel_sweep()
    steer_records, max_steer = run_steer_sweep()

    save: dict = {}
    print("vehicle mass = %.1f kg, static chassis z = %.4f m\n" % (mass, chassis_z0))
    print("%-4s %10s %10s %12s %12s %11s %11s" % (
        "crnr", "stat_cam", "stat_toe", "cam_gain", "toe_change", "k_tire", "k_sprMR"))
    print("%-4s %10s %10s %12s %12s %11s %11s" % (
        "", "deg", "deg", "deg/0.1m", "deg(full)", "kN/m", "kN/m"))
    for cname in ("FL", "FR", "RL", "RR"):
        rec = sorted(records[cname], key=lambda r: r[0])
        travel = np.array([r[0] for r in rec])
        camber = np.array([r[1] for r in rec])
        toe = np.array([r[2] for r in rec])
        wx = np.array([r[3] for r in rec])
        wy = np.array([r[4] for r in rec])
        wz = np.array([r[5] for r in rec])
        fspr = np.array([r[6] for r in rec])
        lspr = np.array([r[7] for r in rec])
        ftire = np.array([r[8] for r in rec])

        # keep only grounded, on-linkage points (trim any airborne / over-droop extreme)
        keep = ftire > GROUNDED_FORCE_N
        travel, camber, toe = travel[keep], camber[keep], toe[keep]
        wx, wy, wz = wx[keep], wy[keep], wz[keep]
        fspr, lspr, ftire = fspr[keep], lspr[keep], ftire[keep]

        scam, stoe = static[cname][0], static[cname][1]
        swy, swz = static[cname][3], static[cname][4]
        track_shift = wy - swy

        rate_tire = _wheel_rate_from_tire(travel, ftire)
        rate_spr, mr = _wheel_rate_from_spring(travel, fspr, lspr)

        zc = travel
        camc = camber
        toec = toe
        order = np.argsort(zc)
        zc, camc, toec = zc[order], camc[order], toec[order]
        cam_slope = float(np.polyfit(zc, camc, 1)[0]) if len(zc) >= 3 else float("nan")
        cam_gain_per_01 = cam_slope * 0.10
        toe_change_full = float(toec[-1] - toec[0]) if len(toec) >= 2 else float("nan")

        print("%-4s %10.3f %10.3f %12.3f %12.3f %11.2f %11.2f" % (
            cname, scam, stoe, cam_gain_per_01, toe_change_full,
            rate_tire / 1000.0, rate_spr / 1000.0))

        save["%s_z_grid" % cname] = travel.astype(np.float64)
        save["%s_camber" % cname] = camber.astype(np.float64)
        save["%s_toe" % cname] = toe.astype(np.float64)
        save["%s_track_shift" % cname] = track_shift.astype(np.float64)
        save["%s_wheel_x" % cname] = wx.astype(np.float64)
        save["%s_wheel_y" % cname] = wy.astype(np.float64)
        save["%s_wheel_z" % cname] = wz.astype(np.float64)
        save["%s_spring_force" % cname] = fspr.astype(np.float64)
        save["%s_spring_length" % cname] = lspr.astype(np.float64)
        save["%s_tire_normal_force" % cname] = ftire.astype(np.float64)
        save["%s_static_camber" % cname] = np.float64(scam)
        save["%s_static_toe" % cname] = np.float64(stoe)
        save["%s_static_wheel_y" % cname] = np.float64(swy)
        save["%s_static_wheel_z" % cname] = np.float64(swz)
        save["%s_wheel_rate_tire_N_per_m" % cname] = np.float64(rate_tire)
        save["%s_wheel_rate_spring_N_per_m" % cname] = np.float64(rate_spr)
        save["%s_motion_ratio" % cname] = np.float64(mr)
        save["%s_cam_gain_deg_per_0p1m" % cname] = np.float64(cam_gain_per_01)
        save["%s_toe_change_full_deg" % cname] = np.float64(toe_change_full)

    # steering kinematics (front)
    save["front_max_steer_rad"] = np.float64(max_steer)
    for cname in ("FL", "FR"):
        rec = steer_records[cname]
        steer_in = np.array([r[0] for r in rec])
        save["%s_steer_input" % cname] = steer_in.astype(np.float64)
        save["%s_steer_angle_rad" % cname] = (steer_in * max_steer).astype(np.float64)
        save["%s_camber_vs_steer" % cname] = np.array([r[1] for r in rec], dtype=np.float64)
        save["%s_toe_vs_steer" % cname] = np.array([r[2] for r in rec], dtype=np.float64)
    fl_toe = save["FL_toe_vs_steer"]
    fr_toe = save["FR_toe_vs_steer"]
    s_in = save["FL_steer_input"]
    idx_full = int(np.argmax(s_in))
    print("\nsteering (front), max steer = %.4f rad (%.1f deg)" % (max_steer, math.degrees(max_steer)))
    print("  at full +lock (input=%.2f): FL toe = %.3f deg, FR toe = %.3f deg (Ackermann split = %.3f deg)" % (
        s_in[idx_full], fl_toe[idx_full], fr_toe[idx_full], fl_toe[idx_full] - fr_toe[idx_full]))

    save["z_axis_convention"] = "suspension_travel = (wheelZ - chassisZ) - static; +jounce"
    save["method"] = "free_veh_Sedan_ramped_chassis_vertical_load_sweep_plus_steer"
    save["corner_order"] = np.array(["FL", "FR", "RL", "RR"])
    save["vehicle_mass_kg"] = np.float64(mass)
    save["static_chassis_z_m"] = np.float64(chassis_z0)
    save["load_frac_grid"] = np.linspace(LOAD_FRAC_LO, LOAD_FRAC_HI, N_LOAD).astype(np.float64)
    save["note"] = (
        "Per-corner kinematic lookups MEASURED from the real Chrono Sedan linkage "
        "(free veh.Sedan(): front DoubleWishbone+RackPinion, rear MultiLink, TMeasy). "
        "z_grid = suspension travel (m) = (wheel_center_z - chassis_z) - static, +jounce. "
        "camber/toe in deg (camber + = top out; toe + = toe-in). track_shift = lateral "
        "wheel-center shift vs static (m). wheel_rate_tire = |d(tire_normal_force)/d(travel)| "
        "(includes the motion ratio); wheel_rate_spring = |dF_spring/dz * MR| cross-check. "
        "Static = gravity-settled. ChSuspensionTestRigPlatform is available and runs but its "
        "fixed-chassis/post force and per-axle ride-height windows make the free-vehicle "
        "sweep the cleaner faithful instrument; see docstring."
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez(OUT, **save)
    print("\nsaved %s" % OUT)
    import sys
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
