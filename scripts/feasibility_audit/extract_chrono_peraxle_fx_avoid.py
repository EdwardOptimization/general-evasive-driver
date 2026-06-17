"""APPROACH B — MEASURED per-axle longitudinal tyre Fx on the AVOID envelope.

Drives the avoid oracle (saved actions) on the REAL isolated veh.Sedan() (mass 1450, FWD,
TMeasy) on avoidance-mu terrain, replicating the ChronoVehicleBackend actuator/teleport path,
and dumps the CLEAN per-AXLE longitudinal tyre force each control step. The point (vs the noisy
local-frame fx in avoid_term_decomp_chrono.py) is to extract the actual FRONT and REAR
longitudinal tyre Fx vs (throttle, speed, steer) using:

  - FRONT (driven) drive force  = sum_LR GetSpindleTorque(0,side) / r_eff   [clean driveshaft -> tyre]
  - per-wheel tyre Fx in BODY frame = ReportTireForce.force rotated to chassis frame, x-component
    (this is the longitudinal tyre force the body actually feels; for the front it folds in the
    steer rotation; it is the noisy ReportTireForce but resolved in the BODY frame, kept only as a
    cross-check on the clean spindle-derived drive force).
  - REAR drive force = 0 in Chrono FWD (rear axle is not driven); rear tyre Fx is pure
    rolling-resistance / induced-slip longitudinal force, captured per-wheel in the body frame.

We also record the per-axle Fz (load) and the front/rear longitudinal tyre force resolved in the
BODY frame so the per-axle split can be compared to pwr3 directly. The conditioning variables
(throttle_in, vx, steer, gear, mu) are recorded so a per-axle additive/multiplicative correction
can be built as a function of (throttle, speed, steer) — NOT tuned to the gate.

Covers a SPREAD across all 4 avoid mu levels (accel-heavy episodes).

Run inside the pinned chrono env:
    /home/quyaonan/miniforge3/envs/chrono/bin/python \
        scripts/feasibility_audit/extract_chrono_peraxle_fx_avoid.py
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pychrono as chrono
import pychrono.vehicle as veh

ROOT = Path(__file__).resolve().parents[2]
AVOID = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_avoid_labels.npz"
OUT = ROOT / "runs/feasibility_audit/phase4_f2/avoid_peraxle_fx_chrono.npz"

# spread across all 4 avoid mu levels (accel-heavy episodes); a handful per level.
EPISODES = [
    # mu=0.3625
    48, 49, 50, 51, 72, 73, 74, 75,
    # mu=0.5875
    6, 7, 8, 9, 11, 12,
    # mu=0.8125
    10, 13, 14, 15, 17, 22,
    # mu=1.0375
    16, 18, 19, 20, 21, 23,
]

DT = 0.02
INTERNAL = 1e-3
SUBSTEPS = 20
INIT_Z = 0.23
SPINUP_MU = 1.0
SETTLE = 300
SPINUP_MAX = 12000
TCAP = 120  # control steps to capture (throttle phase + early coast)

BASE_MAX_DRIVE_FORCE = 8200.0
BASE_MAX_BRAKE_FORCE = 6000.0


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _move_towards(value, target, max_delta):
    if target > value:
        return min(value + max_delta, target)
    return max(value - max_delta, target)


def build_car(mass_target):
    veh.SetDataPath(chrono.GetChronoDataPath() + "vehicle/")
    car = veh.Sedan()
    car.SetContactMethod(chrono.ChContactMethod_NSC)
    car.SetChassisFixed(False)
    car.SetChassisCollisionType(veh.CollisionType_NONE)
    car.SetInitPosition(chrono.ChCoordsysd(chrono.ChVector3d(0, 0, INIT_Z), chrono.QUNIT))
    car.SetTireType(veh.TireModelType_TMEASY)
    car.SetTireStepSize(INTERNAL)
    car.Initialize()
    vehicle = car.GetVehicle()
    chassis = vehicle.GetChassisBody()
    base_veh = float(vehicle.GetMass())
    base_chassis = float(chassis.GetMass())
    non_chassis = base_veh - base_chassis
    chassis.SetMass(max(mass_target - non_chassis, 50.0))
    return car, vehicle, chassis, non_chassis


def teleport_boost(vehicle, chassis, d_ref_local, x, y, psi, vx, vy, yaw_rate):
    system = vehicle.GetSystem()
    bodies = list(system.GetBodies())
    e = chassis.GetRot().Rotate(chrono.ChVector3d(1.0, 0.0, 0.0))
    psi_cur = math.atan2(e.y, e.x)
    qd = chrono.QuatFromAngleZ(psi - psi_cur)
    ref_cur = chassis.GetPos() + chassis.GetRot().Rotate(d_ref_local)
    ref_tgt = chrono.ChVector3d(x, y, ref_cur.z)
    for b in bodies:
        rel = b.GetPos() - ref_cur
        b.SetPos(ref_tgt + qd.Rotate(rel))
        b.SetRot(qd * b.GetRot())
        b.SetPosDt(qd.Rotate(b.GetPosDt()))
        b.SetAngVelParent(qd.Rotate(b.GetAngVelParent()))
    rot_new = chassis.GetRot()
    v_des = rot_new.Rotate(chrono.ChVector3d(vx, vy, 0.0))
    v_cur = chassis.GetPosDt()
    dv = chrono.ChVector3d(v_des.x - v_cur.x, v_des.y - v_cur.y, 0.0)
    w_cur = chassis.GetAngVelParent()
    dw = chrono.ChVector3d(0.0, 0.0, yaw_rate - w_cur.z)
    pivot = chassis.GetPos()
    for b in bodies:
        r = b.GetPos() - pivot
        b.SetPosDt(b.GetPosDt() + dv + dw.Cross(r))
        b.SetAngVelParent(b.GetAngVelParent() + dw)


def read_planar(chassis, d_ref_local):
    rot = chassis.GetRot()
    ref = chassis.GetPos() + rot.Rotate(d_ref_local)
    e = rot.Rotate(chrono.ChVector3d(1.0, 0.0, 0.0))
    psi = math.atan2(e.y, e.x)
    v_loc = rot.RotateBack(chassis.GetPosDt())
    wz = float(chassis.GetAngVelLocal().z)
    return float(ref.x), float(ref.y), float(psi), float(v_loc.x), float(v_loc.y), wz


def axle_telemetry(vehicle, chassis, terrain):
    """Per-AXLE longitudinal tyre Fx resolved in the BODY (chassis) frame + Fz + drive torque.

    Returns front/rear sums of: Fx_body (tyre longitudinal force the chassis feels), Fz."""
    rot = chassis.GetRot()
    out = {}
    for ai, tag in ((0, "f"), (1, "r")):
        fx_body = 0.0
        fy_body = 0.0
        fz = 0.0
        kappa = 0.0
        alpha = 0.0
        for side in (veh.LEFT, veh.RIGHT):
            tire = vehicle.GetTire(ai, side)
            fr = tire.ReportTireForce(terrain)
            # resolve the tyre contact force into the CHASSIS frame (body long/lat).
            f_body = rot.RotateBack(fr.force)
            fx_body += float(f_body.x)
            fy_body += float(f_body.y)
            fz += abs(float(rot.RotateBack(fr.force).z))
            kappa += float(tire.GetLongitudinalSlip())
            alpha += float(tire.GetSlipAngle())
        out[f"{tag}_fx_body"] = fx_body
        out[f"{tag}_fy_body"] = fy_body
        out[f"{tag}_fz"] = fz
        out[f"{tag}_kappa"] = 0.5 * kappa
        out[f"{tag}_alpha"] = 0.5 * alpha
    return out


def run_episode(actions, init, mu, mass):
    car, vehicle, chassis, non_chassis = build_car(mass)
    ref_pos = vehicle.GetPos(); cog_pos = chassis.GetPos()
    d_ref_local = chassis.GetRot().RotateBack(ref_pos - cog_pos)

    eng = vehicle.GetEngine()
    trans = vehicle.GetTransmission()
    dl = vehicle.GetDriveline()
    driven = list(dl.GetDrivenAxleIndexes())
    driven_sides = [(ai, veh.LEFT) for ai in driven] + [(ai, veh.RIGHT) for ai in driven]

    target_speed = math.hypot(float(init[3]), float(init[4]))
    spin_terrain = veh.FlatTerrain(0.0, SPINUP_MU)
    t = 0.0
    inp = veh.DriverInputs()
    inp.m_steering = 0.0; inp.m_throttle = 0.0; inp.m_braking = 0.0
    for n in range(SPINUP_MAX):
        if n >= SETTLE:
            v_now = chassis.GetRot().RotateBack(chassis.GetPosDt()).x
            if v_now >= target_speed:
                break
            inp.m_throttle = float(_clamp(0.5 * (target_speed - v_now), 0.05, 0.85))
        car.Synchronize(t, inp, spin_terrain); spin_terrain.Synchronize(t)
        car.Advance(INTERNAL); spin_terrain.Advance(INTERNAL); t += INTERNAL

    teleport_boost(vehicle, chassis, d_ref_local,
                   float(init[0]), float(init[1]), float(init[2]),
                   float(init[3]), float(init[4]), float(init[5]))
    terrain = veh.FlatTerrain(0.0, float(mu))

    params = dict(max_steer=0.62, max_steer_rate=3.5, max_drive_force=BASE_MAX_DRIVE_FORCE,
                  max_brake_force=BASE_MAX_BRAKE_FORCE, drive_tau=0.08, steer_tau=0.06)
    drive_scale = params["max_drive_force"] / BASE_MAX_DRIVE_FORCE
    brake_scale = params["max_brake_force"] / BASE_MAX_BRAKE_FORCE
    steer_state = 0.0
    drive_force_state = 0.0

    x, y, psi, vx, vy, wz = read_planar(chassis, d_ref_local)
    prev_vx = vx
    r_eff = float(vehicle.GetTire(0, veh.LEFT).GetRadius())
    recs = []
    T = min(len(actions), TCAP)
    for k in range(T):
        a = actions[k]
        steer_cmd = _clamp(float(a[0]), -1.0, 1.0) * params["max_steer"]
        throttle_cmd = 0.5 * (_clamp(float(a[1]), -1.0, 1.0) + 1.0)
        brake_cmd = 0.5 * (_clamp(float(a[2]), -1.0, 1.0) + 1.0)
        steer_rate_limit = params["max_steer_rate"] * DT
        steer_lag = _clamp(DT / max(params["steer_tau"], DT), 0.0, 1.0)
        steer_target = steer_state + (steer_cmd - steer_state) * steer_lag
        steer_state = _move_towards(steer_state, steer_target, steer_rate_limit)
        force_target = throttle_cmd * params["max_drive_force"] - brake_cmd * params["max_brake_force"]
        drive_alpha = _clamp(DT / max(params["drive_tau"], DT), 0.0, 1.0)
        drive_force_state += (force_target - drive_force_state) * drive_alpha
        if drive_force_state >= 0.0:
            thr_state = drive_force_state / max(params["max_drive_force"], 1e-6); brk_state = 0.0
        else:
            thr_state = 0.0; brk_state = -drive_force_state / max(params["max_brake_force"], 1e-6)

        inputs = veh.DriverInputs()
        inputs.m_steering = float(_clamp(steer_state / max(params["max_steer"], 1e-6), -1.0, 1.0))
        inputs.m_throttle = float(_clamp(thr_state * drive_scale, 0.0, 1.0))
        inputs.m_braking = float(_clamp(brk_state * brake_scale, 0.0, 1.0))

        for _ in range(SUBSTEPS):
            car.Synchronize(t, inputs, terrain); terrain.Synchronize(t)
            car.Advance(INTERNAL); terrain.Advance(INTERNAL); t += INTERNAL

        x, y, psi, vx, vy, wz = read_planar(chassis, d_ref_local)
        ax_body = (vx - prev_vx) / DT
        prev_vx = vx

        ax_tel = axle_telemetry(vehicle, chassis, terrain)
        gear = int(trans.GetCurrentGear())
        T_sp_front = float(sum(dl.GetSpindleTorque(ai, sd) for ai, sd in driven_sides))
        # clean per-axle DRIVE force from spindle torque (front driven, rear=0 in FWD)
        Fdrive_front = T_sp_front / max(r_eff, 1e-6)
        recs.append(dict(
            step=k, vx=vx, vy=vy, wz=wz, ax=ax_body, steer=steer_state,
            thr_in=inputs.m_throttle, brk_in=inputs.m_braking, gear=gear,
            T_spindle_front=T_sp_front, Fdrive_front=Fdrive_front,
            f_fx_body=ax_tel["f_fx_body"], r_fx_body=ax_tel["r_fx_body"],
            f_fy_body=ax_tel["f_fy_body"], r_fy_body=ax_tel["r_fy_body"],
            f_fz=ax_tel["f_fz"], r_fz=ax_tel["r_fz"],
            f_kappa=ax_tel["f_kappa"], r_kappa=ax_tel["r_kappa"],
            f_alpha=ax_tel["f_alpha"], r_alpha=ax_tel["r_alpha"],
            r_eff=r_eff, mu=float(mu),
        ))
    car = None
    return recs


def main():
    d = np.load(AVOID, allow_pickle=True)
    pk = [str(k) for k in d["param_keys"]]
    out = {}
    keys = None
    for ep in EPISODES:
        a = np.asarray(d["actions"][ep])
        init = d["init"][ep]
        mu = float(d["params"][ep][pk.index("mu")])
        mass = float(d["params"][ep][pk.index("mass")])
        print(f"=== ep{ep}: mu={mu:.4f} mass={mass:.0f} ===", flush=True)
        recs = run_episode(a, init, mu, mass)
        if keys is None:
            keys = list(recs[0].keys())
        arr = np.array([[r[k] for k in keys] for r in recs], dtype=np.float64)
        out[f"ep{ep}"] = arr
        ki = {k: i for i, k in enumerate(keys)}
        for k in (5, 15, 30, 50):
            if k < len(recs):
                r = recs[k]
                print("  step%2d vx=%.2f ax=%+.2f thr=%.2f gear=%d | Fdrive_f=%.0f "
                      "Fx_f_body=%.0f Fx_r_body=%.0f Fz_f=%.0f Fz_r=%.0f kap_f=%+.3f"
                      % (k, r["vx"], r["ax"], r["thr_in"], r["gear"], r["Fdrive_front"],
                         r["f_fx_body"], r["r_fx_body"], r["f_fz"], r["r_fz"], r["f_kappa"]),
                      flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez(OUT, keys=np.array(keys), episodes=np.array(EPISODES), **out)
    print(f"\nsaved {OUT}")
    print("keys:", keys)


if __name__ == "__main__":
    main()
