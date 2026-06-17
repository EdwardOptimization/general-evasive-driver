"""AVOID-VX term decomposition — CHRONO side.

Drives the avoid oracle (saved actions) on the REAL isolated veh.Sedan() (mass 1450, FWD,
TMeasy) on avoidance-mu terrain, replicating the ChronoVehicleBackend actuator/teleport path,
and dumps PER-FRONT-WHEEL telemetry each control step so it can be compared TERM BY TERM with
gpu_physics_pwr on the same actions/states:

    per control step, FRONT-LEFT and FRONT-RIGHT wheel:
        longitudinal_slip kappa  (tire.GetLongitudinalSlip)
        slip_angle alpha         (tire.GetSlipAngle)
        Fx drive force [N]       (local-frame ReportTireForce.x)
        Fy lateral   [N]         (local-frame ReportTireForce.y)
        Fz vertical load [N]     (|ReportTireForce.z|)
        wheel omega [rad/s]
    powertrain chain:
        engine motor rpm / motor torque  (eng.GetMotorSpeed/GetMotorTorque)
        current gear                     (trans.GetCurrentGear)
        output driveshaft torque [Nm]    (trans.GetOutputDriveshaftTorque)
        driven (front) spindle torque sum [Nm]  (driveline.GetSpindleTorque)
    body:
        vx, vy, yaw_rate, ax_body (finite diff over the 0.02 control step)

Episodes: the canonical avoid-vx-gap cases 72..77 (mu=0.3625, throttle 0.62 ramp, ~0 brake).

Run inside the pinned chrono env:
    /home/quyaonan/miniforge3/envs/chrono/bin/python \
        scripts/feasibility_audit/avoid_vx_term_decomp_chrono.py
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pychrono as chrono
import pychrono.vehicle as veh

ROOT = Path(__file__).resolve().parents[2]
AVOID = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_avoid_labels.npz"
OUT = ROOT / "runs/feasibility_audit/phase4_f2/avoid_term_decomp_chrono.npz"

EPISODES = [72, 73, 74, 75, 76, 77]
DT = 0.02
INTERNAL = 1e-3
SUBSTEPS = 20
INIT_Z = 0.23
SPINUP_MU = 1.0
SETTLE = 300
SPINUP_MAX = 12000

# AutoDrift base actuator constants (must match ChronoVehicleBackend)
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


def front_wheel_telemetry(vehicle, terrain):
    """Per FRONT wheel (axle 0): kappa, alpha, local Fx/Fy/Fz, omega."""
    rows = {}
    for name, side in (("L", veh.LEFT), ("R", veh.RIGHT)):
        tire = vehicle.GetTire(0, side)
        wheel = vehicle.GetWheel(0, side)
        fr = tire.ReportTireForce(terrain)
        ws = wheel.GetState()
        local = ws.rot.RotateBack(fr.force)
        rows[name] = dict(
            kappa=float(tire.GetLongitudinalSlip()),
            alpha=float(tire.GetSlipAngle()),
            fx=float(local.x),
            fy=float(local.y),
            fz=abs(float(local.z)),
            omega=float(getattr(ws, "omega", float("nan"))),
            radius=float(tire.GetRadius()),
        )
    # also grab rear-axle Fz for the load-transfer check
    fz_rear = 0.0
    for side in (veh.LEFT, veh.RIGHT):
        tire = vehicle.GetTire(1, side)
        wheel = vehicle.GetWheel(1, side)
        fr = tire.ReportTireForce(terrain)
        ws = wheel.GetState()
        local = ws.rot.RotateBack(fr.force)
        fz_rear += abs(float(local.z))
    rows["fz_rear_sum"] = fz_rear
    return rows


def run_episode(ep, actions, init, mu, mass):
    car, vehicle, chassis, non_chassis = build_car(mass)
    ref_pos = vehicle.GetPos(); cog_pos = chassis.GetPos()
    d_ref_local = chassis.GetRot().RotateBack(ref_pos - cog_pos)

    eng = vehicle.GetEngine()
    trans = vehicle.GetTransmission()
    dl = vehicle.GetDriveline()
    driven = list(dl.GetDrivenAxleIndexes())
    driven_sides = [(ai, veh.LEFT) for ai in driven] + [(ai, veh.RIGHT) for ai in driven]

    # spin-up on high-mu terrain to settle suspension/driveline (backend convention)
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

    # actuator state (AutoDrift replica)
    params = dict(max_steer=0.62, max_steer_rate=3.5, max_drive_force=BASE_MAX_DRIVE_FORCE,
                  max_brake_force=BASE_MAX_BRAKE_FORCE, drive_tau=0.08, steer_tau=0.06)
    drive_scale = params["max_drive_force"] / BASE_MAX_DRIVE_FORCE
    brake_scale = params["max_brake_force"] / BASE_MAX_BRAKE_FORCE
    steer_state = 0.0
    drive_force_state = 0.0

    x, y, psi, vx, vy, wz = read_planar(chassis, d_ref_local)
    prev_vx = vx
    recs = []
    T = len(actions)
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

        fw = front_wheel_telemetry(vehicle, terrain)
        rpm = float(eng.GetMotorSpeed()) * 60.0 / (2.0 * np.pi)
        motor_tq = float(eng.GetOutputMotorshaftTorque())
        gear = int(trans.GetCurrentGear())
        T_ds = float(trans.GetOutputDriveshaftTorque())
        T_sp = float(sum(dl.GetSpindleTorque(ai, sd) for ai, sd in driven_sides))
        recs.append(dict(
            step=k, vx=vx, vy=vy, wz=wz, ax=ax_body, steer=steer_state,
            thr_in=inputs.m_throttle, brk_in=inputs.m_braking,
            rpm=rpm, motor_tq=motor_tq, gear=gear, T_driveshaft=T_ds, T_spindle_sum=T_sp,
            fl_kappa=fw["L"]["kappa"], fl_alpha=fw["L"]["alpha"], fl_fx=fw["L"]["fx"],
            fl_fy=fw["L"]["fy"], fl_fz=fw["L"]["fz"], fl_omega=fw["L"]["omega"],
            fr_kappa=fw["R"]["kappa"], fr_alpha=fw["R"]["alpha"], fr_fx=fw["R"]["fx"],
            fr_fy=fw["R"]["fy"], fr_fz=fw["R"]["fz"], fr_omega=fw["R"]["omega"],
            fz_front_sum=fw["L"]["fz"] + fw["R"]["fz"], fz_rear_sum=fw["fz_rear_sum"],
            r_eff=fw["L"]["radius"],
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
        Tcap = min(len(a), 90)  # only need throttle phase + early coast
        print(f"=== ep{ep}: mu={mu:.4f} mass={mass:.0f} T(use)={Tcap} ===")
        recs = run_episode(ep, a[:Tcap], init, mu, mass)
        if keys is None:
            keys = list(recs[0].keys())
        arr = np.array([[r[k] for k in keys] for r in recs], dtype=np.float64)
        out[f"ep{ep}"] = arr
        # quick console: throttle-phase ax + front Fz unload + front Fx
        for k in (0, 5, 10, 20, 30, 40):
            if k < len(recs):
                r = recs[k]
                print("  step%2d vx=%.2f ax=%+.2f thr_in=%.2f gear=%d rpm=%.0f Tds=%.0f Tsp=%.0f "
                      "| Fz_f=%.0f Fz_r=%.0f kap_fl=%+.4f Fx_fl=%.0f Fy_fl=%.0f"
                      % (k, r["vx"], r["ax"], r["thr_in"], r["gear"], r["rpm"], r["T_driveshaft"],
                         r["T_spindle_sum"], r["fz_front_sum"], r["fz_rear_sum"], r["fl_kappa"],
                         r["fl_fx"], r["fl_fy"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez(OUT, keys=np.array(keys), episodes=np.array(EPISODES), **out)
    print(f"\nsaved {OUT}")
    print("keys:", keys)


if __name__ == "__main__":
    main()
